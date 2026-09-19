import json
from pathlib import Path

from app.schemas.orchestration import RiskInferenceRequest
from app.schemas.policy import PolicyEvaluationRequest
from app.schemas.recovery import RecoveryEvaluationRequest

WORKFLOW_PATH = Path("workflows/finmate_journey.json")


def test_validate_request_handles_webhook_body_and_keeps_normalized_output() -> None:
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    validate = next(node for node in workflow["nodes"] if node["name"] == "Validate Request")
    code = validate["parameters"]["jsCode"]

    assert "const request = $json.body ?? $json;" in code
    for field in ("journey_id", "customer_id", "customer_goal"):
        assert field in code
        assert f"{field}: request.{field}" in code
    assert "requested_amount: Number(request.requested_amount)" in code


def test_validate_request_connection_is_unchanged() -> None:
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert workflow["connections"]["Validate Request"]["main"] == [
        [{"node": "Get Simulated CRM Context", "type": "main", "index": 0}]
    ]


def test_risk_inference_node_uses_exact_flat_fastapi_feature_contract() -> None:
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    risk_node = next(node for node in workflow["nodes"] if node["name"] == "Run Risk Inference")
    parameters = risk_node["parameters"]
    body = parameters["jsonBody"]
    schema_fields = set(RiskInferenceRequest.model_fields)

    assert parameters["method"] == "POST"
    assert parameters["contentType"] == "json"
    assert parameters["specifyBody"] == "json"
    assert set(
        field for field in schema_fields
        if f"model_features.{field}" in body
    ) == schema_fields
    assert "$node['Build Model Context'].json.model_features" in body
    assert workflow["connections"]["Build Model Context"]["main"] == [
        [{"node": "Run Risk Inference", "type": "main", "index": 0}]
    ]


def test_policy_node_uses_exact_fastapi_policy_contract() -> None:
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    policy_node = next(node for node in workflow["nodes"] if node["name"] == "Evaluate Policy")
    parameters = policy_node["parameters"]
    body = parameters["jsonBody"]
    required = set(PolicyEvaluationRequest.model_json_schema()["required"])

    assert parameters["method"] == "POST"
    assert parameters["contentType"] == "json"
    assert parameters["specifyBody"] == "json"
    assert all(f"{field}:" in body for field in required)
    assert "risk_signal: { risk_probability:" in body
    assert "required_information: { customer_identity_verified:" in body
    assert workflow["connections"]["Get SHAP Explanation"]["main"] == [
        [{"node": "Evaluate Policy", "type": "main", "index": 0}]
    ]


def test_goal_recovery_node_uses_exact_fastapi_recovery_contract() -> None:
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    recovery_node = next(node for node in workflow["nodes"] if node["name"] == "Goal Recovery")
    parameters = recovery_node["parameters"]
    body_expression = parameters["jsonBody"]
    schema_fields = set(RecoveryEvaluationRequest.model_fields)
    required_fields = set(RecoveryEvaluationRequest.model_json_schema()["required"])
    mapped_fields = {
        "journey_id",
        "customer_goal",
        "requested_amount",
        "original_policy_decision",
        "policy_reason_code",
        "policy_version",
        "risk_signal",
        "top_risk_factors",
        "customer_context",
        "human_review_required",
        "human_review_reason",
    }

    assert parameters["method"] == "POST"
    assert parameters["contentType"] == "json"
    assert parameters["specifyBody"] == "json"
    assert required_fields <= mapped_fields <= schema_fields
    assert body_expression.startswith("={{ JSON.stringify({ ")
    assert body_expression.endswith(" }) }}")
    for mapping in (
        "journey_id: $node['Build Model Context'].json.journey_id",
        "customer_goal: $node['Build Model Context'].json.customer_goal",
        "requested_amount: Math.trunc(Number($node['Build Model Context'].json.requested_amount))",
        "original_policy_decision: $json.decision",
        "policy_reason_code: $json.reason_code",
        "policy_version: $json.policy_version",
        "risk_probability: Number($json.risk_signal.risk_probability)",
        "predicted_risk_class: Math.trunc(Number($json.risk_signal.predicted_risk_class))",
        "model_version: $json.risk_signal.model_version",
        "top_risk_factors: $node['Get SHAP Explanation'].json.top_risk_factors",
        "customer_context: { simulated: true, recovery_allowed: $node['Build Model Context'].json.crm.recovery_allowed }",
        "human_review_required: Boolean($json.human_review_required)",
    ):
        assert mapping in body_expression

    # JSON.stringify returns valid JSON text, which n8n's JSON Body mode parses into this typed object.
    body = json.loads(json.dumps({
        "journey_id": "recovery-demo-001",
        "customer_goal": "Purchase inventory",
        "requested_amount": 200_000,
        "original_policy_decision": "NOT_SUITABLE",
        "policy_reason_code": "RISK_SIGNAL_ABOVE_PROTOTYPE_LIMIT",
        "policy_version": "prototype-v1",
        "risk_signal": {
            "risk_probability": 0.6,
            "predicted_risk_class": 1,
            "model_version": "finmate-default-risk-xgb-v2",
        },
        "top_risk_factors": [{"feature": "numeric__dti_n", "shap_value": 0.2}],
        "customer_context": {"simulated": True, "recovery_allowed": True},
        "human_review_required": False,
        "human_review_reason": None,
    }))

    assert set(body) == mapped_fields
    RecoveryEvaluationRequest.model_validate(body)
    assert isinstance(body["requested_amount"], int)
    assert body["original_policy_decision"] == "NOT_SUITABLE"
    assert isinstance(body["risk_signal"]["risk_probability"], float)
    assert isinstance(body["risk_signal"]["predicted_risk_class"], int)
    assert isinstance(body["top_risk_factors"], list)
    assert isinstance(body["top_risk_factors"][0]["shap_value"], float)
    assert body["customer_context"] == {"simulated": True, "recovery_allowed": True}
    assert workflow["connections"]["Decision Router"]["main"][0] == [
        {"node": "Goal Recovery", "type": "main", "index": 0}
    ]


def test_decision_router_explicitly_routes_each_governed_policy_decision() -> None:
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    router = next(node for node in workflow["nodes"] if node["name"] == "Decision Router")
    rules = router["parameters"]["rules"]["values"]

    assert [
        rule["conditions"]["conditions"][0]["rightValue"] for rule in rules
    ] == [
        "NOT_SUITABLE",
        "COMPLEX_REVIEW",
        "MISSING_INFORMATION",
        "ELIGIBLE",
    ]
    assert all(
        rule["conditions"]["conditions"][0]["leftValue"] == "={{ $json.decision }}"
        for rule in rules
    )
    assert workflow["connections"]["Decision Router"]["main"] == [
        [{"node": "Goal Recovery", "type": "main", "index": 0}],
        [{"node": "Human Review Path", "type": "main", "index": 0}],
        [{"node": "Missing Information Path", "type": "main", "index": 0}],
        [{"node": "Eligible Path", "type": "main", "index": 0}],
    ]


def test_decision_router_fallback_is_a_non_eligible_safe_stop() -> None:
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    router = next(node for node in workflow["nodes"] if node["name"] == "Decision Router")
    options = router["parameters"]["rules"]["options"]

    assert options["fallbackOutput"] == "extra"
    assert options["renameFallbackOutput"] == "Unhandled Decision (Safe Stop)"
    assert "ELIGIBLE" in [
        rule["conditions"]["conditions"][0]["rightValue"]
        for rule in router["parameters"]["rules"]["values"]
    ]
    router_outputs = workflow["connections"]["Decision Router"]["main"]
    assert len(router_outputs) == 4
    assert router_outputs[3] == [{"node": "Eligible Path", "type": "main", "index": 0}]
    # The Switch fallback is output 4 after the four explicit rules; it is intentionally unconnected.
