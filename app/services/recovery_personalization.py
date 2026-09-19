"""Failure-safe Gemini personalization for already-authoritative recovery output."""

from __future__ import annotations

import json
import logging

from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from app.config import get_settings
from app.context.service import ContextService
from app.schemas.recovery_personalization import (
    RecoveryPersonalization,
    RecoveryPersonalizationRequest,
    RecoveryPersonalizationResponse,
)


logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """You write concise customer-facing explanatory copy for FinMate's simulated prototype.
The deterministic Policy Engine and Goal Recovery Engine are authoritative. Never approve or reject, change a
policy decision, invent a recovery path, change an amount, promise approval, override human review, or invent
customer values. Use only supplied evidence. Return JSON only with exactly the requested fields. Do not include a
decision field, amounts, offers, guarantees, or a path code absent from deterministic_recovery_paths."""


class RecoveryPersonalizer:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def personalize(self, request: RecoveryPersonalizationRequest) -> RecoveryPersonalizationResponse:
        """Every provider or validation failure preserves deterministic recovery."""
        if not self.settings.gemini_api_key:
            return self._fallback()
        try:
            verified_context = ContextService(self.db).get_full_context(request.customer_id)
            evidence = {
                "original_goal": request.recovery.original_goal,
                "requested_amount": request.recovery.original_requested_amount,
                "policy_decision": request.recovery.original_policy_decision.value,
                "policy_reason_code": request.policy_reason_code,
                "risk_signal": request.risk_signal.model_dump(),
                "shap_factors": [factor.model_dump() for factor in request.top_risk_factors],
                "crm_context": verified_context["crm"],
                "financial_context": verified_context["financial"],
                "credit_context": verified_context["credit"],
                "deterministic_recovery_paths": [path.model_dump(mode="json") for path in request.recovery.available_paths],
            }
            client = genai.Client(api_key=self.settings.gemini_api_key, http_options=types.HttpOptions(timeout=8_000))
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents={"role": "user", "parts": [{"text": json.dumps(evidence)}]},
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            personalization = RecoveryPersonalization.model_validate_json((getattr(response, "text", None) or "").strip())
            self._validate_paths(personalization, request)
            return RecoveryPersonalizationResponse(personalization=personalization, source="GEMINI")
        except Exception as error:
            logger.warning(
                "Recovery personalization fell back: category=%s model=%s exception=%s",
                self._classify(error), self.settings.gemini_model, type(error).__name__,
            )
            return self._fallback()

    @staticmethod
    def _validate_paths(personalization: RecoveryPersonalization, request: RecoveryPersonalizationRequest) -> None:
        allowed = {path.path for path in request.recovery.available_paths}
        returned = {item.path_code for item in personalization.recovery_path_explanations}
        if returned != allowed or len(returned) != len(personalization.recovery_path_explanations):
            raise ValueError("personalization must explain each deterministic path exactly once")

    @staticmethod
    def _fallback() -> RecoveryPersonalizationResponse:
        return RecoveryPersonalizationResponse(source="DETERMINISTIC_FALLBACK")

    @staticmethod
    def _classify(error: Exception) -> str:
        if isinstance(error, (ValueError, json.JSONDecodeError)):
            return "invalid_response"
        if isinstance(error, TimeoutError):
            return "timeout"
        return "provider_or_context_error"
