"""Idempotent seed data for local FinMate prototype journeys."""

from sqlalchemy.orm import Session

from app.models.demo_context import BusinessProfile, CreditProfile, DemoCustomer, FinancialProfile


DEMO_CUSTOMERS = (
    {
        "customer_id": "rahul-demo", "name": "Rahul", "default_goal": "Expand grocery store", "default_requested_amount": 500_000,
        "business": {"business_type": "grocery_store", "business_tenure_years": 4, "customer_identity_verified": True, "business_context_verified": True, "required_documents_complete": True, "existing_customer_relationship": True},
        "financial": {"monthly_revenue": 40_000, "annual_revenue": 480_000, "existing_obligations": 16_000, "dti_n": 40.0, "purpose": "small_business", "account_activity_summary": "SIMULATED_ACTIVE_ACCOUNT"},
        "credit": {"fico_n": 620.0, "emp_length": "2 years", "home_ownership_n": "RENT", "credit_summary": "SIMULATED_SUMMARIZED_CREDIT_CONTEXT"},
    },
    {
        "customer_id": "eligible-demo", "name": "Ananya", "default_goal": "Upgrade business equipment", "default_requested_amount": 50_000,
        "business": {"business_type": "retail_shop", "business_tenure_years": 10, "customer_identity_verified": True, "business_context_verified": True, "required_documents_complete": True, "existing_customer_relationship": True},
        "financial": {"monthly_revenue": 12_500, "annual_revenue": 150_000, "existing_obligations": 2_000, "dti_n": 5.0, "purpose": "home_improvement", "account_activity_summary": "SIMULATED_STABLE_ACCOUNT"},
        "credit": {"fico_n": 800.0, "emp_length": "10+ years", "home_ownership_n": "OWN", "credit_summary": "SIMULATED_STRONG_CREDIT_CONTEXT"},
    },
    {
        "customer_id": "recovery-demo", "name": "Meera", "default_goal": "Purchase inventory", "default_requested_amount": 200_000,
        "business": {"business_type": "small_retail", "business_tenure_years": 2, "customer_identity_verified": True, "business_context_verified": True, "required_documents_complete": True, "existing_customer_relationship": False},
        "financial": {"monthly_revenue": 1_667, "annual_revenue": 20_000, "existing_obligations": 8_000, "dti_n": 40.0, "purpose": "small_business", "account_activity_summary": "SIMULATED_LIMITED_ACCOUNT_ACTIVITY"},
        "credit": {"fico_n": 620.0, "emp_length": "2 years", "home_ownership_n": "RENT", "credit_summary": "SIMULATED_HIGHER_RISK_CREDIT_CONTEXT"},
    },
    {
        "customer_id": "missing-info-demo", "name": "Vikram", "default_goal": "Expand delivery capacity", "default_requested_amount": 75_000,
        "business": {"business_type": "delivery_service", "business_tenure_years": 3, "customer_identity_verified": False, "business_context_verified": True, "required_documents_complete": False, "existing_customer_relationship": False},
        "financial": {"monthly_revenue": 8_000, "annual_revenue": 96_000, "existing_obligations": 4_000, "dti_n": 15.0, "purpose": "small_business", "account_activity_summary": "SIMULATED_ACCOUNT_PENDING_DOCUMENTS"},
        "credit": {"fico_n": 700.0, "emp_length": "5 years", "home_ownership_n": "MORTGAGE", "credit_summary": "SIMULATED_CREDIT_CONTEXT"},
    },
)


def seed_demo_customers(db: Session) -> None:
    """Create missing demo records without overwriting existing profile data."""
    for item in DEMO_CUSTOMERS:
        if db.get(DemoCustomer, item["customer_id"]):
            continue
        customer = DemoCustomer(
            customer_id=item["customer_id"], name=item["name"], is_simulated=True,
            default_goal=item["default_goal"], default_requested_amount=item["default_requested_amount"],
        )
        customer.business_profile = BusinessProfile(**item["business"])
        customer.financial_profile = FinancialProfile(**item["financial"])
        customer.credit_profile = CreditProfile(**item["credit"])
        db.add(customer)
    db.commit()
