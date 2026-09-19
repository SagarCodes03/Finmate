from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.recovery.service import evaluate_recovery
from app.schemas.recovery import RecoveryEvaluationRequest, RecoveryPath, RecoveryStatus


def payload(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "journey_id": "rahul-demo-001",
        "customer_goal": "Expand grocery store",
        "requested_amount": 500_000,
        "original_policy_decision": "NOT_SUITABLE",
        "policy_reason_code": "RISK_SIGNAL_ABOVE_PROTOTYPE_LIMIT",
        "policy_version": "prototype-v1",
        "risk_signal": {"risk_probability": 0.60, "predicted_risk_class": 1, "model_version": "finmate-default-risk-xgb-v2"},
        "top_risk_factors": [{"feature": "numeric__dti_n", "shap_value": 0.2}],
    }
    data.update(overrides)
    return data


def test_not_suitable_generates_recovery_and_preserves_goal() -> None:
    result = evaluate_recovery(RecoveryEvaluationRequest.model_validate(payload()))
    assert result.recovery_status is RecoveryStatus.AVAILABLE
    assert result.original_goal == "Expand grocery store"
    assert {option.path for option in result.available_paths} == {
        RecoveryPath.RIGHT_SIZED_FINANCING, RecoveryPath.PHASED_FINANCING, RecoveryPath.IMPROVE_ELIGIBILITY,
    }


def test_high_risk_recovery_explains_risk_and_right_sizes_amount() -> None:
    result = evaluate_recovery(RecoveryEvaluationRequest.model_validate(payload()))
    right_sized = next(option for option in result.available_paths if option.path is RecoveryPath.RIGHT_SIZED_FINANCING)
    assert right_sized.alternative_amount == 250_000
    assert "dti_n" in right_sized.reason
    assert "approval" in right_sized.next_actions[1].lower()


def test_high_amount_produces_right_sized_and_phased_options() -> None:
    result = evaluate_recovery(RecoveryEvaluationRequest.model_validate(payload(requested_amount=600_000)))
    paths = {option.path for option in result.available_paths}
    assert RecoveryPath.RIGHT_SIZED_FINANCING in paths
    assert RecoveryPath.PHASED_FINANCING in paths


def test_90_day_preparation_path_has_concrete_actions_without_a_guarantee() -> None:
    result = evaluate_recovery(RecoveryEvaluationRequest.model_validate(payload()))
    plan = next(option for option in result.available_paths if option.path is RecoveryPath.IMPROVE_ELIGIBILITY)
    assert plan.timeline_days == 90
    assert plan.title == "Improve eligibility and reassess in 90 days"
    assert len(plan.next_actions) == 7
    assert any("identity and business documentation" in action.lower() for action in plan.next_actions)
    assert any("bank statements" in action.lower() for action in plan.next_actions)
    assert all("guarantee" not in action.lower() and "approval" not in action.lower() for action in plan.next_actions)


def test_eligible_and_missing_information_do_not_generate_recovery() -> None:
    eligible = evaluate_recovery(RecoveryEvaluationRequest.model_validate(payload(original_policy_decision="ELIGIBLE")))
    missing = evaluate_recovery(RecoveryEvaluationRequest.model_validate(payload(original_policy_decision="MISSING_INFORMATION")))
    assert eligible.recovery_status is RecoveryStatus.NOT_APPLICABLE
    assert missing.recovery_reason_code == "GATHER_INFORMATION_FIRST"
    assert not eligible.available_paths and not missing.available_paths


def test_complex_review_keeps_human_pathway() -> None:
    result = evaluate_recovery(RecoveryEvaluationRequest.model_validate(payload(original_policy_decision="COMPLEX_REVIEW", human_review_required=True)))
    assert result.recovery_status is RecoveryStatus.HUMAN_REVIEW_REQUIRED
    assert result.human_review_required is True


def test_no_configured_path_is_controlled_empty_response() -> None:
    result = evaluate_recovery(RecoveryEvaluationRequest.model_validate(payload(customer_context={"recovery_allowed": False})))
    assert result.recovery_status is RecoveryStatus.NO_APPLICABLE_PATH
    assert result.available_paths == []


def test_boundary_and_invalid_input() -> None:
    result = evaluate_recovery(RecoveryEvaluationRequest.model_validate(payload(requested_amount=100_000)))
    assert any(option.path is RecoveryPath.PHASED_FINANCING for option in result.available_paths)
    try:
        RecoveryEvaluationRequest.model_validate(payload(requested_amount=0))
    except ValidationError:
        pass
    else:
        raise AssertionError("zero requested amount must be rejected")


def test_recovery_api() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/recovery/evaluate", json=payload())
    assert response.status_code == 200
    assert response.json()["recovery_status"] == "AVAILABLE"
