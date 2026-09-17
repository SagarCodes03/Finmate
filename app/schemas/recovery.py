"""API contracts for deterministic Goal Recovery evaluation."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.policy import PolicyDecision, RiskSignal, ShapFactor


class RecoveryStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    NO_APPLICABLE_PATH = "NO_APPLICABLE_PATH"


class RecoveryPath(str, Enum):
    RIGHT_SIZED_FINANCING = "RIGHT_SIZED_FINANCING"
    PHASED_FINANCING = "PHASED_FINANCING"
    IMPROVE_ELIGIBILITY = "IMPROVE_ELIGIBILITY"


class RecoveryOption(BaseModel):
    path: RecoveryPath
    title: str
    description: str
    reason: str
    requested_amount: int = Field(gt=0)
    alternative_amount: int | None = Field(default=None, gt=0)
    next_actions: list[str]
    prototype_only: bool = True


class RecoveryEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    journey_id: str = Field(min_length=1, max_length=100)
    customer_goal: str = Field(min_length=1, max_length=500)
    requested_amount: int = Field(gt=0)
    original_policy_decision: PolicyDecision
    policy_reason_code: str = Field(min_length=1, max_length=100)
    policy_version: str = Field(min_length=1, max_length=100)
    risk_signal: RiskSignal
    top_risk_factors: list[ShapFactor] = Field(default_factory=list, max_length=10)
    customer_context: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    human_review_required: bool = False
    human_review_reason: str | None = Field(default=None, max_length=500)


class RecoveryEvaluationResponse(BaseModel):
    recovery_status: RecoveryStatus
    original_goal: str
    original_requested_amount: int
    original_policy_decision: PolicyDecision
    recovery_reason_code: str
    recovery_reason: str
    available_paths: list[RecoveryOption]
    policy_version: str
    recovery_version: str
    human_review_required: bool
    human_review_reason: str | None = None
    triggered_rule_ids: list[str]
    audit_context: dict[str, str | int | float | bool | None]
