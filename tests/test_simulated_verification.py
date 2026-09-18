from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.demo_context import DemoCustomer
from app.schemas.orchestration import JourneyResponse


def _governed_result(journey_id: str) -> JourneyResponse:
    return JourneyResponse.model_validate({
        "journey_id": journey_id,
        "customer_goal": "Expand delivery capacity",
        "requested_amount": 75_000,
        "risk_signal": {
            "risk_probability": 0.399,
            "predicted_risk_class": 0,
            "model_version": "finmate-default-risk-xgb-v2",
            "top_risk_factors": [], "top_protective_factors": [],
            "prototype_only": True, "is_simulated_journey": True,
        },
        "policy_decision": {
            "decision": "COMPLEX_REVIEW", "reason_code": "RISK_OR_AMOUNT_REVIEW",
            "reason": "The journey requires human review under prototype controls.",
            "risk_signal": {"risk_probability": 0.399, "predicted_risk_class": 0, "model_version": "finmate-default-risk-xgb-v2"},
            "required_actions": ["Route the journey to a human reviewer."],
            "human_review_required": True, "human_review_reason": "Risk signal falls in the prototype review band.",
            "policy_version": "prototype-v1", "triggered_rule_ids": ["P004_RISK_OR_AMOUNT_REVIEW"],
            "audit_context": {"journey_id": journey_id},
        },
        "goal_recovery": None,
        "next_action": "Route to human review; no automated recovery is generated.",
        "audit": {"policy_version": "prototype-v1", "simulated": True},
    })


def _reset_vikram() -> None:
    with SessionLocal() as db:
        customer = db.get(DemoCustomer, "missing-info-demo")
        assert customer is not None
        customer.business_profile.customer_identity_verified = False
        customer.business_profile.required_documents_complete = False
        db.commit()


def test_simulated_verification_requires_missing_fields_and_reuses_governed_journey(monkeypatch) -> None:
    _reset_vikram()
    calls: list[dict[str, object]] = []

    def fake_run_journey(payload):  # type: ignore[no-untyped-def]
        calls.append(payload.model_dump())
        return _governed_result(payload.journey_id)

    monkeypatch.setattr("app.api.v1.endpoints.verification.run_journey", fake_run_journey)
    request = {
        "original_journey_id": "original-missing-001",
        "journey_id": "reassessment-missing-001",
        "customer_id": "missing-info-demo",
        "customer_goal": "Expand delivery capacity",
        "requested_amount": 75_000,
    }
    try:
        with TestClient(app) as client:
            blocked = client.post("/api/v1/journeys/reassess", json=request)
            identity = client.patch("/api/v1/journeys/simulated-verifications", json={"customer_id": "missing-info-demo", "field": "customer_identity_verified"})
            documents = client.patch("/api/v1/journeys/simulated-verifications", json={"customer_id": "missing-info-demo", "field": "required_documents_complete"})
            reassessment = client.post("/api/v1/journeys/reassess", json=request)

        assert blocked.status_code == 409
        assert identity.json() == {"customer_id": "missing-info-demo", "field": "customer_identity_verified", "value": True, "is_simulated": True}
        assert documents.json()["value"] is True
        assert reassessment.status_code == 200
        body = reassessment.json()
        assert body["original_journey_id"] == "original-missing-001"
        assert body["reassessment"]["journey_id"] == "reassessment-missing-001"
        assert body["reassessment"]["risk_signal"]["model_version"] == "finmate-default-risk-xgb-v2"
        assert body["reassessment"]["policy_decision"]["decision"] == "COMPLEX_REVIEW"
        assert calls == [{key: request[key] for key in ("journey_id", "customer_id", "customer_goal", "requested_amount")}]
    finally:
        _reset_vikram()


def test_simulated_verification_patch_preflight_allows_the_vite_ui() -> None:
    """The browser must be allowed to send the JSON PATCH before it reaches FastAPI."""
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/journeys/simulated-verifications",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "PATCH",
                "Access-Control-Request-Headers": "content-type",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "PATCH" in response.headers["access-control-allow-methods"]
