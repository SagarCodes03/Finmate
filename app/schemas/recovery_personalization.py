"""Validated, non-decisional Gemini copy for deterministic recovery paths."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.policy import RiskSignal, ShapFactor
from app.schemas.recovery import RecoveryEvaluationResponse, RecoveryPath


class RecoveryPlanPeriod(BaseModel):
    model_config = ConfigDict(extra="forbid")
    period: Literal["Days 1-30", "Days 31-60", "Days 61-90"]
    actions: list[str] = Field(min_length=1, max_length=4)


class RecoveryPathExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path_code: RecoveryPath
    explanation: str = Field(min_length=1, max_length=600)


class RecoveryPersonalization(BaseModel):
    """Presentation-only copy. It deliberately contains no decision or amount."""

    model_config = ConfigDict(extra="forbid")
    headline: str = Field(min_length=1, max_length=160)
    goal_summary: str = Field(min_length=1, max_length=500)
    why_current_path_failed: str = Field(min_length=1, max_length=700)
    recommended_next_steps: list[str] = Field(min_length=1, max_length=5)
    personalized_90_day_plan: list[RecoveryPlanPeriod] = Field(min_length=3, max_length=3)
    recovery_path_explanations: list[RecoveryPathExplanation] = Field(default_factory=list, max_length=3)

    @field_validator("personalized_90_day_plan")
    @classmethod
    def require_ordered_periods(cls, value: list[RecoveryPlanPeriod]) -> list[RecoveryPlanPeriod]:
        if [period.period for period in value] != ["Days 1-30", "Days 31-60", "Days 61-90"]:
            raise ValueError("the 90-day plan must contain each required period in order")
        return value


class RecoveryPersonalizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: str = Field(min_length=1, max_length=100)
    policy_reason_code: str = Field(min_length=1, max_length=100)
    risk_signal: RiskSignal
    top_risk_factors: list[ShapFactor] = Field(default_factory=list, max_length=10)
    recovery: RecoveryEvaluationResponse


class RecoveryPersonalizationResponse(BaseModel):
    personalization: RecoveryPersonalization | None = None
    source: Literal["GEMINI", "DETERMINISTIC_FALLBACK"]
