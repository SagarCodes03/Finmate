from fastapi.testclient import TestClient

from app.main import app


def payload(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "name": "Priya", "business_type": "artisan_bakery", "customer_goal": "Buy a new oven",
        "requested_amount": 120_000, "monthly_revenue": 50_000, "monthly_obligations": 10_000,
        "fico_n": 720, "emp_length": "5 years", "home_ownership_n": "RENT",
        "business_tenure_years": 3, "purpose": "small_business", "customer_identity_verified": True,
        "required_documents_complete": True, "existing_customer_relationship": False, "recovery_allowed": True,
    }
    value.update(changes)
    return value


def test_custom_customer_is_persisted_with_derived_context() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/custom-customers", json=payload())
        assert response.status_code == 201
        created = response.json()
        context = client.get(f"/api/v1/simulated-context/{created['customer_id']}/financial")

    assert created["customer_id"].startswith("custom-")
    assert created["dti_n"] == 20.0
    assert context.json()["annual_revenue"] == 600_000
    assert context.json()["dti_n"] == 20.0


def test_custom_customer_ids_are_unique_and_fields_are_validated() -> None:
    with TestClient(app) as client:
        first = client.post("/api/v1/custom-customers", json=payload())
        second = client.post("/api/v1/custom-customers", json=payload())
        invalid = client.post("/api/v1/custom-customers", json=payload(monthly_revenue=0, fico_n=200))

    assert first.json()["customer_id"] != second.json()["customer_id"]
    assert invalid.status_code == 422


def test_custom_customer_uses_the_existing_journey_proxy(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    class Response:
        def raise_for_status(self) -> None: pass
        def json(self) -> dict[str, object]:
            return {"journey_id": calls[0]["journey_id"], "customer_goal": "Buy a new oven", "requested_amount": 120_000, "risk_signal": {"risk_probability": .2, "predicted_risk_class": 0, "model_version": "test", "top_risk_factors": [], "top_protective_factors": [], "prototype_only": True, "is_simulated_journey": True}, "policy_decision": {"decision": "ELIGIBLE", "reason_code": "TEST", "reason": "Test", "risk_signal": {"risk_probability": .2, "predicted_risk_class": 0, "model_version": "test"}, "required_actions": [], "human_review_required": False, "policy_version": "test", "triggered_rule_ids": [], "audit_context": {}}, "goal_recovery": None, "next_action": "Test", "audit": {}}

    def post(_: str, *, json: dict[str, object], timeout: float) -> Response:
        calls.append(json); return Response()

    monkeypatch.setattr("app.api.v1.endpoints.journey.httpx.post", post)
    with TestClient(app) as client:
        created = client.post("/api/v1/custom-customers", json=payload(customer_identity_verified=False)).json()
        journey = client.post("/api/v1/journeys", json={"journey_id": "custom-test-journey", "customer_id": created["customer_id"], "customer_goal": created["customer_goal"], "requested_amount": created["requested_amount"]})

    assert journey.status_code == 200
    assert calls[0]["customer_id"] == created["customer_id"]
