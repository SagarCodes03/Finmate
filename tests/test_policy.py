from fastapi.testclient import TestClient

from app.main import app
from app.policy.service import evaluate_policy
from app.schemas.policy import PolicyDecision, PolicyEvaluationRequest


def request_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "journey_id": "demo-rahul-001",
        "goal": "Expand a grocery store",
        "requested_loan_amount": 250_000,
        "risk_signal": {"risk_probability": 0.20, "predicted_risk_class": 1, "model_version": "finmate-default-risk-xgb-v2"},
        "required_information": {
            "customer_identity_verified": True,
            "business_context_verified": True,
            "required_documents_complete": True,
        },
    }
    payload.update(overrides)
    return payload


def test_missing_information_has_highest_precedence() -> None:
    payload = request_payload(
        risk_signal={"risk_probability": 0.90, "predicted_risk_class": 1, "model_version": "model-v1"},
        required_information={"customer_identity_verified": True, "business_context_verified": False, "required_documents_complete": False},
    )
    result = evaluate_policy(PolicyEvaluationRequest.model_validate(payload))
    assert result.decision is PolicyDecision.MISSING_INFORMATION
    assert result.reason_code == "REQUIRED_INFORMATION_MISSING"
    assert result.human_review_required is False


def test_high_risk_is_not_suitable_at_boundary() -> None:
    payload = request_payload(risk_signal={"risk_probability": 0.50, "predicted_risk_class": 1, "model_version": "model-v1"})
    result = evaluate_policy(PolicyEvaluationRequest.model_validate(payload))
    assert result.decision is PolicyDecision.NOT_SUITABLE
    assert result.triggered_rule_ids == ["P003_HIGH_RISK_SIGNAL"]


def test_review_band_and_amount_boundary_require_human_review() -> None:
    risk_review = evaluate_policy(PolicyEvaluationRequest.model_validate(request_payload(risk_signal={"risk_probability": 0.35, "predicted_risk_class": 1, "model_version": "model-v1"})))
    amount_review = evaluate_policy(PolicyEvaluationRequest.model_validate(request_payload(requested_loan_amount=500_000)))
    assert risk_review.decision is PolicyDecision.COMPLEX_REVIEW
    assert amount_review.decision is PolicyDecision.COMPLEX_REVIEW
    assert risk_review.human_review_required is True
    assert amount_review.human_review_reason is not None


def test_low_risk_complete_case_is_eligible() -> None:
    result = evaluate_policy(PolicyEvaluationRequest.model_validate(request_payload()))
    assert result.decision is PolicyDecision.ELIGIBLE
    assert result.policy_version == "prototype-v1"
    assert result.human_review_required is False


def test_exception_is_complex_review_before_risk_rules() -> None:
    result = evaluate_policy(PolicyEvaluationRequest.model_validate(request_payload(exceptional_case=True)))
    assert result.decision is PolicyDecision.COMPLEX_REVIEW
    assert result.reason_code == "EXCEPTION_OR_AMBIGUITY_REVIEW"


def test_policy_api_response() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/policy/evaluate", json=request_payload())
    assert response.status_code == 200
    assert response.json()["decision"] == "ELIGIBLE"
    assert response.json()["risk_signal"]["risk_probability"] == 0.2
