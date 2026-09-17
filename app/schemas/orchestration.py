"""Contracts for n8n-safe orchestration wrappers around existing services."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.policy import ShapFactor


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


def serialize_context(context: dict[str, Any]) -> SimulatedContextResponse:
    return SimulatedContextResponse.model_validate(context)
