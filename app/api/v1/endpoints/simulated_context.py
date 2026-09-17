from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.context.service import ContextService
from app.database import get_db
from app.schemas.orchestration import SimulatedContextResponse, serialize_context

router = APIRouter()


@router.get("/{customer_id}/crm", response_model=SimulatedContextResponse)
def crm_context(customer_id: str, db: Session = Depends(get_db)) -> SimulatedContextResponse:
    return serialize_context(ContextService(db).get_crm_context(customer_id))


@router.get("/{customer_id}/financial", response_model=SimulatedContextResponse)
def financial_context(customer_id: str, db: Session = Depends(get_db)) -> SimulatedContextResponse:
    return serialize_context(ContextService(db).get_financial_context(customer_id))


@router.get("/{customer_id}/credit", response_model=SimulatedContextResponse)
def credit_context(customer_id: str, db: Session = Depends(get_db)) -> SimulatedContextResponse:
    return serialize_context(ContextService(db).get_credit_context(customer_id))
