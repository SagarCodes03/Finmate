import json
from pathlib import Path

from app.schemas.orchestration import RiskInferenceRequest
from app.schemas.policy import PolicyEvaluationRequest

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
