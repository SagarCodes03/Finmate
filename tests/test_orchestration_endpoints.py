from fastapi.testclient import TestClient

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
