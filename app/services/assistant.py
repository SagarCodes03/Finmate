"""Gemini orchestration for FinMate explanations, constrained to governed tools."""

from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any

import httpx
from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from app.config import get_settings
from app.context.service import ContextService
from app.ml.config import MODEL_VERSION
from app.ml.inference import predict_risk
from app.models.demo_context import DemoCustomer
from app.policy.service import evaluate_policy
from app.recovery.service import evaluate_recovery
from app.schemas.orchestration import AssistantChatRequest, AssistantChatResponse, AssistantDiagnosticResponse
from app.schemas.policy import PolicyEvaluationRequest
from app.schemas.recovery import RecoveryEvaluationRequest


logger = logging.getLogger(__name__)


GOVERNANCE_NOTE = (
    "FinMate is a simulated prototype. XGBoost supplies a risk signal, while the "
    "deterministic Policy Engine owns the journey decision. This assistant cannot "
    "approve, reject, alter, or override governed outcomes."
)

SYSTEM_INSTRUCTION = """You are FinMate's customer-facing prototype assistant. You explain only
structured evidence returned by the approved server-side tools or the current governed
journey supplied by the application. You are not a lender and you are not the decision maker.

Non-negotiable governance rules:
- Never approve or reject a loan, financing request, or customer.
- Never modify, estimate, reinterpret, or substitute an XGBoost probability.
- Never override, second-guess, or replace the deterministic Policy Engine output.
- Never invent eligibility.
- Never invent recovery options.
- Never invent loan amounts, rates, products, offers, guarantees, external integrations,
  Paytm integrations, or customer data.
- All customer data and outcomes are simulated prototype data. Say so when relevant.
- SHAP explains the model signal only; it does not make a journey decision.
- Policy Engine output is authoritative for the prototype journey decision; Goal Recovery output
  is authoritative for available recovery paths; human review remains human-controlled.
- If information is unavailable, state that it is unavailable. If asked to bypass policy or to
  make a decision, refuse and explain that the governed process must be followed.
- When no current governed journey evidence is provided, retrieve relevant context with approved
  tools before discussing a customer-specific result. Explain only the returned values.

Be concise, clear, and avoid financial advice. Do not claim tool use that did not occur."""


class AssistantConfigurationError(RuntimeError):
    pass


class AssistantProviderError(RuntimeError):
    """A safe public failure when Gemini cannot complete a request."""

    def __init__(self, category: str) -> None:
        super().__init__("The Gemini service could not complete this request.")
        self.category = category


class AssistantResponseError(RuntimeError):
    """Gemini completed a request but did not return a usable final response."""

class AssistantToolExecutionError(RuntimeError):
    """An approved server-side tool could not produce a safe response."""



class FinMateAssistant:
    """A stateless Gemini turn with a narrow, server-owned tool surface."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.tools_used: list[str] = []
        self.context_used: list[str] = []

    def chat(self, request: AssistantChatRequest) -> AssistantChatResponse:
        if not self.settings.gemini_api_key:
            raise AssistantConfigurationError("GEMINI_API_KEY is not configured")

        current_status = self._journey_status(request.current_journey)
        # Existing governed evidence is always preferred. Without it, provide Gemini
        # a verified starting context; it may request additional approved tools.
        initial_evidence: dict[str, Any] = {}
        if request.current_journey is not None:
            initial_evidence["current_journey"] = request.current_journey
            self.context_used.append("current_governed_journey")
        else:
            initial_evidence["customer_context"] = self.get_customer_context(request.customer_id)

        try:
            client = genai.Client(
                api_key=self.settings.gemini_api_key,
                http_options=types.HttpOptions(
                    timeout=30_000,
                    retry_options=types.HttpRetryOptions(
                        attempts=3,
                        initial_delay=1,
                        max_delay=4,
                        http_status_codes=[429, 500, 502, 503, 504],
                    ),
                ),
            )
            contents = self._contents(request, initial_evidence)
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=contents,
                config=self._generation_config(),
            )
            # Execute only whitelisted calls. A small bounded loop prevents a model
            # from turning one user message into uncontrolled tool activity.
            for _ in range(3):
                calls = list(getattr(response, "function_calls", None) or [])
                if not calls:
                    break
                contents.append(self._model_content(response))
                responses: list[dict[str, Any]] = []
                for call in calls:
                    name = getattr(call, "name", "")
                    arguments = dict(getattr(call, "args", None) or {})
                    result = self._execute_tool(name, request.customer_id, arguments)
                    responses.append({"function_response": {"name": name, "response": result}})
                # Only this server creates function-response parts. Browser history
                # remains text-only and can never replay or forge tool results.
                contents.append({"role": "user", "parts": responses})
                response = client.models.generate_content(
                    model=self.settings.gemini_model,
                    contents=contents,
                    config=self._generation_config(),
                )
            if getattr(response, "function_calls", None):
                raise AssistantResponseError("Gemini exceeded the permitted tool-call rounds.")
            text = (getattr(response, "text", None) or "").strip()
            if not text:
                raise AssistantResponseError("Gemini response did not contain text.")
        except Exception as error:
            category = self._classify_provider_error(error)
            logger.warning(
                "Gemini assistant request failed: category=%s model=%s exception=%s status_code=%s",
                category,
                self.settings.gemini_model,
                type(error).__name__,
                getattr(error, "code", None),
            )
            raise AssistantProviderError(category) from error

        return AssistantChatResponse(
            response=text,
            tools_used=self.tools_used,
            journey_status=current_status or self._last_policy_status(),
            context_used=self.context_used,
            governance_note=GOVERNANCE_NOTE,
        )

    def diagnose_provider(self) -> AssistantDiagnosticResponse:
        """Perform a minimal Gemini request without returning provider content or secrets."""
        if not self.settings.gemini_api_key:
            return AssistantDiagnosticResponse(configured=False, request_status="NOT_CONFIGURED")
        try:
            client = genai.Client(api_key=self.settings.gemini_api_key)
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents="Return exactly READY.",
                config=types.GenerateContentConfig(temperature=0, max_output_tokens=8),
            )
            if not (getattr(response, "text", None) or "").strip():
                raise AssistantResponseError("Gemini diagnostic returned no text.")
        except Exception as error:
            logger.warning(
                "Gemini diagnostic failed: category=%s model=%s exception=%s status_code=%s",
                self._classify_provider_error(error), self.settings.gemini_model,
                type(error).__name__, getattr(error, "code", None),
            )
            return AssistantDiagnosticResponse(configured=True, model=self.settings.gemini_model, request_status="FAILED")
        return AssistantDiagnosticResponse(configured=True, model=self.settings.gemini_model, request_status="SUCCESS")

    def get_customer_context(self, customer_id: str) -> dict[str, Any]:
        self._record("get_customer_context", "customer_context")
        return ContextService(self.db).get_crm_context(customer_id)

    def get_financial_context(self, customer_id: str) -> dict[str, Any]:
        self._record("get_financial_context", "financial_context")
        return ContextService(self.db).get_financial_context(customer_id)

    def get_credit_context(self, customer_id: str) -> dict[str, Any]:
        self._record("get_credit_context", "credit_context")
        return ContextService(self.db).get_credit_context(customer_id)

    def run_risk_assessment(self, customer_id: str) -> dict[str, Any]:
        self._record("run_risk_assessment", "risk_signal_and_shap")
        return {**predict_risk(ContextService(self.db).get_model_features(customer_id)), "model_version": MODEL_VERSION, "prototype_only": True}

    def evaluate_policy_for_customer(self, customer_id: str) -> dict[str, Any]:
        self._record("evaluate_policy", "policy_decision")
        context = ContextService(self.db).get_full_context(customer_id)
        customer = self.db.get(DemoCustomer, customer_id)
        if customer is None:  # ContextService normally raises first; retain a safe guard.
            return {"error": "Simulated demo customer is unavailable."}
        risk = predict_risk(context["model_features"])
        result = evaluate_policy(PolicyEvaluationRequest.model_validate({
            "journey_id": f"assistant-{customer_id}", "goal": customer.default_goal,
            "requested_loan_amount": customer.default_requested_amount,
            "risk_signal": {**risk, "model_version": MODEL_VERSION},
            "required_information": {key: context["crm"][key] for key in ("customer_identity_verified", "business_context_verified", "required_documents_complete")},
            "top_risk_factors": risk["top_risk_factors"], "top_protective_factors": risk["top_protective_factors"],
            "customer_context": {"simulated": True},
        }))
        payload = result.model_dump(mode="json")
        self._policy_result = payload
        return payload

    def evaluate_goal_recovery_for_customer(self, customer_id: str) -> dict[str, Any]:
        self._record("evaluate_goal_recovery", "goal_recovery")
        policy = getattr(self, "_policy_result", None) or self.evaluate_policy_for_customer(customer_id)
        context = ContextService(self.db).get_full_context(customer_id)
        customer = self.db.get(DemoCustomer, customer_id)
        if customer is None:
            return {"error": "Simulated demo customer is unavailable."}
        recovery = evaluate_recovery(RecoveryEvaluationRequest.model_validate({
            "journey_id": f"assistant-{customer_id}", "customer_goal": customer.default_goal,
            "requested_amount": customer.default_requested_amount,
            "original_policy_decision": policy["decision"], "policy_reason_code": policy["reason_code"],
            "policy_version": policy["policy_version"], "risk_signal": policy["risk_signal"],
            "top_risk_factors": predict_risk(context["model_features"])["top_risk_factors"],
            "customer_context": {"simulated": True}, "human_review_required": policy["human_review_required"],
            "human_review_reason": policy.get("human_review_reason"),
        }))
        return recovery.model_dump(mode="json")

    def _execute_tool(self, name: str, customer_id: str, _: dict[str, Any]) -> dict[str, Any]:
        tools: dict[str, Callable[[str], dict[str, Any]]] = {
            "get_customer_context": self.get_customer_context,
            "get_financial_context": self.get_financial_context,
            "get_credit_context": self.get_credit_context,
            "run_risk_assessment": self.run_risk_assessment,
            "evaluate_policy": self.evaluate_policy_for_customer,
            "evaluate_goal_recovery": self.evaluate_goal_recovery_for_customer,
        }
        if name not in tools:
            raise AssistantToolExecutionError("Gemini requested an unapproved tool.")
        try:
            return tools[name](customer_id)
        except Exception as error:
            logger.warning("Gemini tool failed: tool=%s exception=%s", name, type(error).__name__)
            raise AssistantToolExecutionError("An approved tool could not complete.") from error

    def _tool_declarations(self) -> types.Tool:
        names = ("get_customer_context", "get_financial_context", "get_credit_context", "run_risk_assessment", "evaluate_policy", "evaluate_goal_recovery")
        return types.Tool(function_declarations=[
            types.FunctionDeclaration(name=name, description=f"Retrieve structured, simulated prototype evidence via {name}. The server fixes the customer identity; do not supply financial values.", parameters={"type": "object", "properties": {}})
            for name in names
        ])

    def _generation_config(self) -> types.GenerateContentConfig:
        """Keep the governed tool surface available on every model turn."""
        return types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[self._tool_declarations()],
            temperature=0.1,
        )

    def _contents(self, request: AssistantChatRequest, evidence: dict[str, Any]) -> list[Any]:
        # The API receives only validated display text from prior turns. In
        # particular, browser-provided history cannot include Gemini tool parts.
        history: list[Any] = [
            types.Content(
                role="model" if item.role == "assistant" else "user",
                parts=[types.Part.from_text(text=item.content)],
            )
            for item in request.conversation_history
        ]
        history.append({"role": "user", "parts": [{"text": f"Customer ID: {request.customer_id}\\nVerified application evidence: {evidence}\\n\\nCustomer message: {request.message}"}]})
        return history

    @staticmethod
    def _model_content(response: Any) -> Any:
        candidates = getattr(response, "candidates", None) or []
        return getattr(candidates[0], "content", {"role": "model", "parts": []}) if candidates else {"role": "model", "parts": []}

    def _record(self, tool: str, context: str) -> None:
        if tool not in self.tools_used:
            self.tools_used.append(tool)
        if context not in self.context_used:
            self.context_used.append(context)

    @staticmethod
    def _journey_status(journey: dict[str, Any] | None) -> str | None:
        if not journey:
            return None
        policy = journey.get("policy_decision")
        return policy.get("decision") if isinstance(policy, dict) and isinstance(policy.get("decision"), str) else None

    def _last_policy_status(self) -> str | None:
        result = getattr(self, "_policy_result", None)
        return result.get("decision") if isinstance(result, dict) else None

    @staticmethod
    def _classify_provider_error(error: Exception) -> str:
        """Classify failures for server logs without recording provider payloads."""
        if isinstance(error, AssistantResponseError):
            return "response_parsing"
        if isinstance(error, AssistantToolExecutionError):
            return "tool_execution"
        name = type(error).__name__.lower()
        if "function" in name or "tool" in name:
            return "invalid_tool_function_response"
        status_code = getattr(error, "code", None)
        if status_code in (401, 403):
            return "authentication"
        if status_code == 404:
            return "model_api"
        if status_code == 429:
            return "model_api_rate_limit"
        if status_code in (500, 502, 503, 504):
            return "model_api"
        if isinstance(error, (TypeError, ValueError)):
            return "request_format"
        if isinstance(error, httpx.TimeoutException):
            return "timeout_connectivity"
        if isinstance(error, (httpx.NetworkError, OSError)):
            return "timeout_connectivity"
        return "other_provider_error"
