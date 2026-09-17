"""Public API contracts for deterministic policy evaluation."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PolicyDecision(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    MISSING_INFORMATION = "MISSING_INFORMATION"
    NOT_SUITABLE = "NOT_SUITABLE"
    COMPLEX_REVIEW = "COMPLEX_REVIEW"


class ShapFactor(BaseModel):
    feature: str = Field(min_length=1, max_length=200)
    shap_value: float


class RiskSignal(BaseModel):
    """A summarized ML output. This is not a governed lending decision."""

    risk_probability: float = Field(ge=0, le=1)
    predicted_risk_class: int = Field(ge=0, le=1)
    model_version: str = Field(min_length=1, max_length=100)


class RequiredInformationStatus(BaseModel):
    customer_identity_verified: bool = False
    business_context_verified: bool = False
    required_documents_complete: bool = False


class PolicyEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    journey_id: str = Field(min_length=1, max_length=100)
    goal: str = Field(min_length=1, max_length=500)
    requested_loan_amount: int = Field(gt=0)
    risk_signal: RiskSignal
    required_information: RequiredInformationStatus
    top_risk_factors: list[ShapFactor] = Field(default_factory=list, max_length=10)
    top_protective_factors: list[ShapFactor] = Field(default_factory=list, max_length=10)
    customer_context: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    exceptional_case: bool = False
    ambiguity_reason: str | None = Field(default=None, max_length=500)

    @field_validator("requested_loan_amount")
    @classmethod
    def amount_is_reasonable_integer(cls, value: int) -> int:
        return value


class PolicyEvaluationResponse(BaseModel):
    decision: PolicyDecision
    reason_code: str
    reason: str
    risk_signal: RiskSignal
    required_actions: list[str]
    human_review_required: bool
    human_review_reason: str | None = None
    policy_version: str
    triggered_rule_ids: list[str]
    audit_context: dict[str, str | int | float | bool | None]
