from fastapi import APIRouter

from app.recovery.service import evaluate_recovery
from app.schemas.recovery import RecoveryEvaluationRequest, RecoveryEvaluationResponse

router = APIRouter()


@router.post("/evaluate", response_model=RecoveryEvaluationResponse)
def evaluate(payload: RecoveryEvaluationRequest) -> RecoveryEvaluationResponse:
    """Generate governed prototype recovery paths; never financing approvals."""
    return evaluate_recovery(payload)
