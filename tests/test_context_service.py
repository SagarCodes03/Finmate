from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models
from app.context.seed import DEMO_CUSTOMERS, seed_demo_customers
from app.context.service import ContextService
from app.database import Base
from app.ml.config import FEATURES
from app.ml.inference import predict_risk
from app.policy.service import evaluate_policy
from app.schemas.policy import PolicyEvaluationRequest


@pytest.fixture()
def db(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'context_test.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    seed_demo_customers(session)
    try:
        yield session
    finally:
        session.close()


def test_seed_is_idempotent_and_includes_all_demo_customers(db: Session) -> None:
    seed_demo_customers(db)
    service = ContextService(db)
    assert {item["customer_id"] for item in DEMO_CUSTOMERS} == {"rahul-demo", "eligible-demo", "recovery-demo", "missing-info-demo"}
    assert service.get_crm_context("rahul-demo")["customer_name"] == "Rahul"


def test_context_sections_have_simulated_metadata_and_expected_values(db: Session) -> None:
    service = ContextService(db)
    crm = service.get_crm_context("rahul-demo")
    financial = service.get_financial_context("rahul-demo")
    credit = service.get_credit_context("rahul-demo")
    assert crm["source"] == "SIMULATED_PROTOTYPE_SQLITE"
    assert crm["is_simulated"] is True
    assert financial["annual_revenue"] == 480_000
    assert financial["purpose"] == "small_business"
    assert credit["fico_n"] == 620.0


def test_unknown_customer_returns_404(db: Session) -> None:
    with pytest.raises(HTTPException) as error:
        ContextService(db).get_full_context("unknown-demo")
    assert error.value.status_code == 404


def test_model_feature_mapping_exactly_matches_model_schema(db: Session) -> None:
    service = ContextService(db)
    for customer in DEMO_CUSTOMERS:
        features = service.get_model_features(customer["customer_id"])
        assert tuple(features) == FEATURES
        assert all(value is not None for value in features.values())


def test_seeded_scenarios_use_actual_inference_and_existing_policy(db: Session) -> None:
    service = ContextService(db)
    expected = {
        "rahul-demo": "COMPLEX_REVIEW",
        "eligible-demo": "ELIGIBLE",
        "recovery-demo": "NOT_SUITABLE",
        "missing-info-demo": "MISSING_INFORMATION",
    }
    for customer_id, decision in expected.items():
        full = service.get_full_context(customer_id)
        risk = predict_risk(full["model_features"])
        customer = next(item for item in DEMO_CUSTOMERS if item["customer_id"] == customer_id)
        request = PolicyEvaluationRequest.model_validate({
            "journey_id": f"test-{customer_id}",
            "goal": customer["default_goal"],
            "requested_loan_amount": customer["default_requested_amount"],
            "risk_signal": {**risk, "model_version": "finmate-default-risk-xgb-v2"},
            "required_information": {
                "customer_identity_verified": full["crm"]["customer_identity_verified"],
                "business_context_verified": full["crm"]["business_context_verified"],
                "required_documents_complete": full["crm"]["required_documents_complete"],
            },
            "top_risk_factors": risk["top_risk_factors"],
            "top_protective_factors": risk["top_protective_factors"],
        })
        assert evaluate_policy(request).decision.value == decision
