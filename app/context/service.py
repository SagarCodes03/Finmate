"""Read SQLite-backed simulated demo profiles into stable context contracts."""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.ml.config import FEATURES
from app.models.demo_context import DemoCustomer


class ContextService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _customer(self, customer_id: str) -> DemoCustomer:
        statement = select(DemoCustomer).options(
            joinedload(DemoCustomer.business_profile),
            joinedload(DemoCustomer.financial_profile),
            joinedload(DemoCustomer.credit_profile),
        ).where(DemoCustomer.customer_id == customer_id)
        customer = self.db.scalar(statement)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulated demo customer not found")
        return customer

    @staticmethod
    def _metadata(customer: DemoCustomer) -> dict[str, Any]:
        return {"customer_id": customer.customer_id, "source": "SIMULATED_PROTOTYPE_SQLITE", "is_simulated": customer.is_simulated}

    def get_crm_context(self, customer_id: str) -> dict[str, Any]:
        customer = self._customer(customer_id)
        business = customer.business_profile
        return self._metadata(customer) | {
            "customer_name": customer.name,
            "customer_identity_verified": business.customer_identity_verified,
            "business_context_verified": business.business_context_verified,
            "required_documents_complete": business.required_documents_complete,
            "business_type": business.business_type,
            "business_tenure_years": business.business_tenure_years,
            "existing_customer_relationship": business.existing_customer_relationship,
            "recovery_allowed": business.recovery_allowed,
        }

    def get_financial_context(self, customer_id: str) -> dict[str, Any]:
        customer = self._customer(customer_id)
        financial = customer.financial_profile
        return self._metadata(customer) | {
            "monthly_revenue": financial.monthly_revenue,
            "annual_revenue": financial.annual_revenue,
            "existing_obligations": financial.existing_obligations,
            "account_activity_summary": financial.account_activity_summary,
            "dti_n": financial.dti_n,
            "purpose": financial.purpose,
        }

    def get_credit_context(self, customer_id: str) -> dict[str, Any]:
        customer = self._customer(customer_id)
        credit = customer.credit_profile
        return self._metadata(customer) | {
            "fico_n": credit.fico_n,
            "credit_summary": credit.credit_summary,
            "emp_length": credit.emp_length,
            "home_ownership_n": credit.home_ownership_n,
        }

    def get_full_context(self, customer_id: str) -> dict[str, Any]:
        crm = self.get_crm_context(customer_id)
        financial = self.get_financial_context(customer_id)
        credit = self.get_credit_context(customer_id)
        return {"crm": crm, "financial": financial, "credit": credit, "model_features": self.get_model_features(customer_id)}

    def get_model_features(self, customer_id: str) -> dict[str, Any]:
        financial = self.get_financial_context(customer_id)
        credit = self.get_credit_context(customer_id)
        features = {
            "revenue": financial["annual_revenue"], "dti_n": financial["dti_n"],
            "loan_amnt": self._customer(customer_id).default_requested_amount,
            "fico_n": credit["fico_n"], "emp_length": credit["emp_length"],
            "purpose": financial["purpose"], "home_ownership_n": credit["home_ownership_n"],
        }
        if tuple(features) != FEATURES:
            raise RuntimeError("Demo context feature mapping does not match the model schema")
        return features
