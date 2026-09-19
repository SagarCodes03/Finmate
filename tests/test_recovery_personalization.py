import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.recovery.service import evaluate_recovery
from app.schemas.recovery import RecoveryEvaluationRequest


def recovery_payload() -> dict[str, object]:
    deterministic = evaluate_recovery(RecoveryEvaluationRequest.model_validate({
        "journey_id": "personalization-001", "customer_goal": "Purchase inventory", "requested_amount": 200_000,
        "original_policy_decision": "NOT_SUITABLE", "policy_reason_code": "RISK_SIGNAL_ABOVE_PROTOTYPE_LIMIT",
        "policy_version": "prototype-v1", "risk_signal": {"risk_probability": .6, "predicted_risk_class": 1, "model_version": "test"},
        "top_risk_factors": [{"feature": "numeric__dti_n", "shap_value": .2}], "customer_context": {"simulated": True},
    }))
    return {"customer_id": "recovery-demo", "policy_reason_code": "RISK_SIGNAL_ABOVE_PROTOTYPE_LIMIT", "risk_signal": {"risk_probability": .6, "predicted_risk_class": 1, "model_version": "test"}, "top_risk_factors": [{"feature": "numeric__dti_n", "shap_value": .2}], "recovery": deterministic.model_dump(mode="json")}


def valid_llm_response() -> str:
    return json.dumps({
        "headline": "A structured recovery plan is available.", "goal_summary": "Keep the inventory goal in view.",
        "why_current_path_failed": "The current governed path needs a different approach.", "recommended_next_steps": ["Review the available paths."],
        "personalized_90_day_plan": [{"period": "Days 1-30", "actions": ["Organize records."]}, {"period": "Days 31-60", "actions": ["Maintain consistent activity."]}, {"period": "Days 61-90", "actions": ["Prepare for reassessment."]}],
        "recovery_path_explanations": [
            {"path_code": "RIGHT_SIZED_FINANCING", "explanation": "Consider the deterministic smaller amount."},
            {"path_code": "PHASED_FINANCING", "explanation": "Consider the deterministic first phase."},
            {"path_code": "IMPROVE_ELIGIBILITY", "explanation": "Use the structured preparation period."},
        ],
    })


def test_personalization_uses_verified_context_and_returns_validated_copy(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test-key")
    captured: list[object] = []

    class FakeModels:
        def generate_content(self, **kwargs: object) -> object:
            captured.append(kwargs["contents"])
            return SimpleNamespace(text=valid_llm_response())

    monkeypatch.setattr("app.services.recovery_personalization.genai.Client", lambda **_: SimpleNamespace(models=FakeModels()))
    with TestClient(app) as client:
        response = client.post("/api/v1/recovery/personalize", json=recovery_payload())
    assert response.status_code == 200
    assert response.json()["source"] == "GEMINI"
    evidence = json.loads(captured[0]["parts"][0]["text"])
    assert evidence["financial_context"]["annual_revenue"] == 20_000.0
    assert "customer_context" not in evidence
    assert {item["path_code"] for item in response.json()["personalization"]["recovery_path_explanations"]} == {"RIGHT_SIZED_FINANCING", "PHASED_FINANCING", "IMPROVE_ELIGIBILITY"}


def test_malformed_or_provider_failure_falls_back_without_failing_journey(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test-key")

    class InvalidModels:
        def generate_content(self, **_: object) -> object:
            return SimpleNamespace(text="not json")

    monkeypatch.setattr("app.services.recovery_personalization.genai.Client", lambda **_: SimpleNamespace(models=InvalidModels()))
    with TestClient(app) as client:
        invalid = client.post("/api/v1/recovery/personalize", json=recovery_payload())
    assert invalid.status_code == 200
    assert invalid.json() == {"personalization": None, "source": "DETERMINISTIC_FALLBACK"}

    monkeypatch.setattr("app.services.recovery_personalization.genai.Client", lambda **_: (_ for _ in ()).throw(RuntimeError("provider down")))
    with TestClient(app) as client:
        failed = client.post("/api/v1/recovery/personalize", json=recovery_payload())
    assert failed.status_code == 200
    assert failed.json()["source"] == "DETERMINISTIC_FALLBACK"


def test_llm_cannot_add_paths_or_change_governed_decision(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test-key")
    bad = json.loads(valid_llm_response())
    bad["decision"] = "ELIGIBLE"
    bad["recovery_path_explanations"][0]["path_code"] = "IMPROVE_ELIGIBILITY"

    class FakeModels:
        def generate_content(self, **_: object) -> object:
            return SimpleNamespace(text=json.dumps(bad))

    monkeypatch.setattr("app.services.recovery_personalization.genai.Client", lambda **_: SimpleNamespace(models=FakeModels()))
    request = recovery_payload()
    original_paths = request["recovery"]["available_paths"]
    with TestClient(app) as client:
        response = client.post("/api/v1/recovery/personalize", json=request)
    assert response.status_code == 200
    assert response.json()["source"] == "DETERMINISTIC_FALLBACK"
    assert request["recovery"]["available_paths"] == original_paths
