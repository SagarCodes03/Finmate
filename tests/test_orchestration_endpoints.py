from fastapi.testclient import TestClient
import pytest

from app.main import app


def test_simulated_context_endpoints_are_labeled_and_deterministic() -> None:
    with TestClient(app) as client:
        crm = client.get("/api/v1/simulated-context/rahul-demo/crm")
        financial = client.get("/api/v1/simulated-context/rahul-demo/financial")
        credit = client.get("/api/v1/simulated-context/rahul-demo/credit")
    assert crm.status_code == financial.status_code == credit.status_code == 200
    assert crm.json()["is_simulated"] is True
    assert crm.json()["source"] == "SIMULATED_PROTOTYPE_SQLITE"
    assert financial.json()["annual_revenue"] == 480_000
    assert credit.json()["fico_n"] == 620.0


def test_risk_endpoint_wraps_existing_inference(monkeypatch) -> None:
    def fake_predict_risk(_: dict[str, object]) -> dict[str, object]:
        return {
            "risk_probability": 0.6,
            "predicted_risk_class": 1,
            "top_risk_factors": [{"feature": "numeric__dti_n", "shap_value": 0.2}],
            "top_protective_factors": [],
        }

    monkeypatch.setattr("app.api.v1.endpoints.risk.predict_risk", fake_predict_risk)
    payload = {
        "revenue": 48_000,
        "dti_n": 40,
        "loan_amnt": 500_000,
        "fico_n": 620,
        "emp_length": "2 years",
        "purpose": "small_business",
        "home_ownership_n": "RENT",
    }
    with TestClient(app) as client:
        response = client.post("/api/v1/risk/infer", json=payload)
    assert response.status_code == 200
    assert response.json()["risk_probability"] == 0.6
    assert response.json()["prototype_only"] is True


def _journey_result(decision: str, goal_recovery: dict[str, object] | None) -> dict[str, object]:
    return {
        "journey_id": "frontend-demo-001",
        "customer_goal": "Purchase inventory",
        "requested_amount": 200_000,
        "risk_signal": {
            "risk_probability": 0.6,
            "predicted_risk_class": 1,
            "model_version": "finmate-default-risk-xgb-v2",
            "top_risk_factors": [{"feature": "numeric__dti_n", "shap_value": 0.2}],
            "top_protective_factors": [],
            "prototype_only": True,
            "shap_source": "EXISTING_BACKEND_INFERENCE",
            "is_simulated_journey": True,
        },
        "policy_decision": {
            "decision": decision,
            "reason_code": "PROTOTYPE_RESULT",
            "reason": "A deterministic prototype policy result.",
            "risk_signal": {
                "risk_probability": 0.6,
                "predicted_risk_class": 1,
                "model_version": "finmate-default-risk-xgb-v2",
            },
            "required_actions": ["Continue through the governed journey."],
            "human_review_required": decision == "COMPLEX_REVIEW",
            "human_review_reason": "Review is required." if decision == "COMPLEX_REVIEW" else None,
            "policy_version": "prototype-v1",
            "triggered_rule_ids": ["P001"],
            "audit_context": {"journey_id": "frontend-demo-001"},
        },
        "goal_recovery": goal_recovery,
        "next_action": "Continue through the governed journey.",
        "audit": {"policy_version": "prototype-v1", "simulated": True},
    }


@pytest.mark.parametrize(
    ("customer_id", "decision", "recovery_expected"),
    [
        ("eligible-demo", "ELIGIBLE", False),
        ("missing-info-demo", "MISSING_INFORMATION", False),
        ("rahul-demo", "COMPLEX_REVIEW", False),
        ("recovery-demo", "NOT_SUITABLE", True),
    ],
)
def test_frontend_journey_endpoint_proxies_each_governed_n8n_path(
    monkeypatch, customer_id: str, decision: str, recovery_expected: bool
) -> None:
    recovery = None
    if recovery_expected:
        recovery = {
            "recovery_status": "AVAILABLE",
            "original_goal": "Purchase inventory",
            "original_requested_amount": 200_000,
            "original_policy_decision": "NOT_SUITABLE",
            "recovery_reason_code": "HIGH_RISK_PROTOTYPE_RECOVERY",
            "recovery_reason": "Controlled prototype alternatives are available.",
            "available_paths": [],
            "policy_version": "prototype-v1",
            "recovery_version": "prototype-recovery-v1",
            "human_review_required": False,
            "human_review_reason": None,
            "triggered_rule_ids": ["R004_HIGH_RISK_RECOVERY"],
            "audit_context": {"journey_id": "frontend-demo-001"},
        }
    calls: list[dict[str, object]] = []

    class FakeN8nResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return _journey_result(decision, recovery)

    def fake_post(url: str, *, json: dict[str, object], timeout: float) -> FakeN8nResponse:
        calls.append({"url": url, "json": json, "timeout": timeout})
        return FakeN8nResponse()

    monkeypatch.setattr("app.api.v1.endpoints.journey.httpx.post", fake_post)
    request = {
        "journey_id": "frontend-demo-001",
        "customer_id": customer_id,
        "customer_goal": "Purchase inventory",
        "requested_amount": 200_000,
    }
    with TestClient(app) as client:
        response = client.post("/api/v1/journeys", json=request)

    assert response.status_code == 200
    assert response.json()["policy_decision"]["decision"] == decision
    assert (response.json()["goal_recovery"] is not None) is recovery_expected
    assert calls[0]["json"] == request


def test_frontend_journey_endpoint_allows_local_vite_origin() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/journeys",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
