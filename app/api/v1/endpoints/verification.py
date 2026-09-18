"""Simulated-only verification updates followed by the existing governed journey."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.journey import run_journey
from app.context.service import ContextService
from app.database import get_db
from app.models.demo_context import DemoCustomer
from app.schemas.orchestration import (
    JourneyReassessmentRequest,
    JourneyReassessmentResponse,
    JourneyRequest,
    SimulatedVerificationRequest,
    SimulatedVerificationResponse,
)


router = APIRouter()

_ALLOWED_FIELDS = (
    "customer_identity_verified",
    "required_documents_complete",
)


@router.patch("/simulated-verifications", response_model=SimulatedVerificationResponse)
def confirm_simulated_verification(
    payload: SimulatedVerificationRequest, db: Session = Depends(get_db)
) -> SimulatedVerificationResponse:
    customer = db.get(DemoCustomer, payload.customer_id)
    if customer is None or not customer.is_simulated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulated demo customer not found")
    profile = customer.business_profile
    if getattr(profile, payload.field):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This simulated verification field is not currently missing.",
        )
    setattr(profile, payload.field, True)
    db.commit()
    return SimulatedVerificationResponse(customer_id=customer.customer_id, field=payload.field, value=True)


@router.post("/reassess", response_model=JourneyReassessmentResponse)
def reassess_after_simulated_verification(
    payload: JourneyReassessmentRequest, db: Session = Depends(get_db)
) -> JourneyReassessmentResponse:
    context = ContextService(db).get_crm_context(payload.customer_id)
    still_missing = [field for field in _ALLOWED_FIELDS if not context[field]]
    if still_missing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Confirm all currently missing simulated verification items before reassessment.",
        )
    reassessment = run_journey(JourneyRequest(
        journey_id=payload.journey_id,
        customer_id=payload.customer_id,
        customer_goal=payload.customer_goal,
        requested_amount=payload.requested_amount,
    ))
    return JourneyReassessmentResponse(
        original_journey_id=payload.original_journey_id,
        reassessment=reassessment,
    )
