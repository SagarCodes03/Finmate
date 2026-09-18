"""Simulated custom-customer intake backed by the same context tables as demos."""

from uuid import uuid4

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.demo_context import BusinessProfile, CreditProfile, DemoCustomer, FinancialProfile
from app.schemas.orchestration import CustomCustomerCreate, CustomCustomerResponse

router = APIRouter()


@router.post("", response_model=CustomCustomerResponse, status_code=status.HTTP_201_CREATED)
def create_custom_customer(payload: CustomCustomerCreate, db: Session = Depends(get_db)) -> CustomCustomerResponse:
    """Persist a simulated profile that n8n retrieves through ContextService."""
    customer_id = f"custom-{uuid4().hex}"
    dti_n = (payload.monthly_obligations / payload.monthly_revenue) * 100
    customer = DemoCustomer(
        customer_id=customer_id,
        name=payload.name.strip(),
        is_simulated=True,
        default_goal=payload.customer_goal.strip(),
        default_requested_amount=payload.requested_amount,
    )
    customer.business_profile = BusinessProfile(
        business_type=payload.business_type.strip(),
        business_tenure_years=payload.business_tenure_years,
        customer_identity_verified=payload.customer_identity_verified,
        business_context_verified=True,
        required_documents_complete=payload.required_documents_complete,
        existing_customer_relationship=payload.existing_customer_relationship,
        recovery_allowed=payload.recovery_allowed,
    )
    customer.financial_profile = FinancialProfile(
        monthly_revenue=payload.monthly_revenue,
        annual_revenue=payload.monthly_revenue * 12,
        existing_obligations=payload.monthly_obligations,
        dti_n=dti_n,
        purpose=payload.purpose.strip(),
        account_activity_summary="SIMULATED_CUSTOMER_PROVIDED_CONTEXT",
    )
    customer.credit_profile = CreditProfile(
        fico_n=payload.fico_n,
        emp_length=payload.emp_length.strip(),
        home_ownership_n=payload.home_ownership_n,
        credit_summary="SIMULATED_CUSTOMER_PROVIDED_CREDIT_CONTEXT",
    )
    db.add(customer)
    db.commit()
    return CustomCustomerResponse(
        customer_id=customer_id, name=customer.name, business_type=customer.business_profile.business_type,
        customer_goal=customer.default_goal, requested_amount=customer.default_requested_amount, dti_n=dti_n,
    )
