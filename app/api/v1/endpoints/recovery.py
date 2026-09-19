from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.recovery.service import evaluate_recovery
from app.schemas.recovery import RecoveryEvaluationRequest, RecoveryEvaluationResponse
from app.schemas.recovery_personalization import RecoveryPersonalizationRequest, RecoveryPersonalizationResponse
from app.services.recovery_personalization import RecoveryPersonalizer

router = APIRouter()


@router.post("/evaluate", response_model=RecoveryEvaluationResponse)
def evaluate(payload: RecoveryEvaluationRequest) -> RecoveryEvaluationResponse:
    """Generate governed prototype recovery paths; never financing approvals."""
    return evaluate_recovery(payload)


@router.post("/personalize", response_model=RecoveryPersonalizationResponse)
def personalize(payload: RecoveryPersonalizationRequest, db: Session = Depends(get_db)) -> RecoveryPersonalizationResponse:
    """Add optional explanatory copy without changing governed recovery output."""
    return RecoveryPersonalizer(db).personalize(payload)
