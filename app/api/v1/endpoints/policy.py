from fastapi import APIRouter

from app.policy.service import evaluate_policy
from app.schemas.policy import PolicyEvaluationRequest, PolicyEvaluationResponse

router = APIRouter()


@router.post("/evaluate", response_model=PolicyEvaluationResponse)
def evaluate(payload: PolicyEvaluationRequest) -> PolicyEvaluationResponse:
    """Evaluate deterministic prototype policy; this is not a real loan decision."""
    return evaluate_policy(payload)
