"""Contracts for n8n-safe orchestration wrappers around existing services."""

from typing import Any, Literal
import logging

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.policy import PolicyEvaluationResponse, ShapFactor
from app.schemas.recovery import RecoveryEvaluationResponse


logger = logging.getLogger(__name__)


class SimulatedContextResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    customer_id: str
    source: str
    is_simulated: bool


class RiskInferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revenue: float | None = None
    dti_n: float | None = None
    loan_amnt: float | None = Field(default=None, gt=0)
    fico_n: float | None = None
    emp_length: str | None = None
    purpose: str | None = None
    home_ownership_n: str | None = None


class RiskInferenceResponse(BaseModel):
    risk_probability: float = Field(ge=0, le=1)
    predicted_risk_class: int = Field(ge=0, le=1)
    model_version: str
    top_risk_factors: list[ShapFactor]
    top_protective_factors: list[ShapFactor]
    prototype_only: bool = True


class JourneyRequest(BaseModel):
    """Frontend request forwarded unchanged to the existing n8n journey webhook."""

    model_config = ConfigDict(extra="forbid")

    journey_id: str = Field(min_length=1, max_length=100)
    customer_id: str = Field(min_length=1, max_length=100)
    customer_goal: str = Field(min_length=1, max_length=500)
    requested_amount: int = Field(gt=0)


class JourneyRiskSignal(RiskInferenceResponse):
    """Existing risk/SHAP output retained in the n8n journey response."""

    shap_source: str | None = None
    is_simulated_journey: bool = True


class JourneyResponse(BaseModel):
    """Structured final result from the existing governed n8n journey."""

    journey_id: str
    customer_goal: str
    requested_amount: int
    risk_signal: JourneyRiskSignal
    policy_decision: PolicyEvaluationResponse
    goal_recovery: RecoveryEvaluationResponse | None = None
    next_action: str
    audit: dict[str, str | int | float | bool | None]


class CustomCustomerCreate(BaseModel):
    """Validated, simulated-only intake for a customer using the normal journey pipeline."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    business_type: str = Field(min_length=1, max_length=100)
    customer_goal: str = Field(min_length=1, max_length=500)
    requested_amount: int = Field(gt=0)
    monthly_revenue: float = Field(gt=0)
    monthly_obligations: float = Field(ge=0)
    fico_n: float = Field(ge=300, le=850)
    emp_length: str = Field(min_length=1, max_length=40)
    home_ownership_n: Literal["RENT", "OWN", "MORTGAGE", "OTHER"]
    business_tenure_years: int = Field(gt=0, le=100)
    purpose: str = Field(min_length=1, max_length=100)
    customer_identity_verified: bool = False
    required_documents_complete: bool = False
    existing_customer_relationship: bool = False
    recovery_allowed: bool = True

    @model_validator(mode="after")
    def validate_reasonable_obligations(self) -> "CustomCustomerCreate":
        if self.monthly_obligations > self.monthly_revenue * 100:
            raise ValueError("monthly_obligations is outside the supported prototype range")
        return self


class CustomCustomerResponse(BaseModel):
    customer_id: str
    name: str
    business_type: str
    customer_goal: str
    requested_amount: int
    dti_n: float
    is_simulated: bool = True


SimulatedVerificationField = Literal[
    "customer_identity_verified",
    "required_documents_complete",
]


class SimulatedVerificationRequest(BaseModel):
    """Explicitly simulated context confirmation; it does not verify real documents."""

    model_config = ConfigDict(extra="forbid")

    customer_id: str = Field(min_length=1, max_length=100)
    field: SimulatedVerificationField


class SimulatedVerificationResponse(BaseModel):
    customer_id: str
    field: SimulatedVerificationField
    value: bool
    is_simulated: bool = True


class JourneyReassessmentRequest(JourneyRequest):
    """A new journey ID is required so the original assessment remains distinct."""

    original_journey_id: str = Field(min_length=1, max_length=100)


class JourneyReassessmentResponse(BaseModel):
    original_journey_id: str
    reassessment: JourneyResponse
    is_simulated: bool = True


def serialize_context(context: dict[str, Any]) -> SimulatedContextResponse:
    return SimulatedContextResponse.model_validate(context)


class AssistantMessage(BaseModel):
    """A client-managed, text-only turn for the prototype assistant."""

    model_config = ConfigDict(extra="forbid")

    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=4_000)


class AssistantChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=4_000)
    conversation_history: list[AssistantMessage] = Field(default_factory=list, max_length=12)
    current_journey: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_text_only_history(self) -> "AssistantChatRequest":
        """Accept only the bounded, alternating text turns emitted by the UI."""
        if sum(len(item.content) for item in self.conversation_history) > 24_000:
            logger.warning("Assistant request rejected: category=malformed_conversation_history reason=text_budget")
            raise ValueError("conversation_history exceeds the allowed text budget")
        for index, item in enumerate(self.conversation_history):
            expected_role = "user" if index % 2 == 0 else "assistant"
            if item.role != expected_role:
                logger.warning("Assistant request rejected: category=malformed_conversation_history reason=turn_order")
                raise ValueError("conversation_history must alternate user and assistant text turns")
        return self


class AssistantChatResponse(BaseModel):
    response: str
    tools_used: list[str] = Field(default_factory=list)
    journey_status: str | None = None
    context_used: list[str] = Field(default_factory=list)
    governance_note: str


class AssistantDiagnosticResponse(BaseModel):
    configured: bool
    model: str | None = None
    request_status: Literal["SUCCESS", "FAILED", "NOT_CONFIGURED"]
