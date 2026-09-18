from types import SimpleNamespace

from fastapi.testclient import TestClient
from google.genai.errors import ClientError

from app.config import get_settings
from app.main import app
from app.services.assistant import AssistantResponseError, AssistantToolExecutionError, FinMateAssistant, SYSTEM_INSTRUCTION


def payload(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "customer_id": "rahul-demo",
        "message": "Why is my journey under review?",
        "conversation_history": [],
        "current_journey": None,
    }
    request.update(overrides)
    return request


def test_assistant_requires_configured_gemini_key(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "gemini_api_key", "")
    with TestClient(app) as client:
        response = client.post("/api/v1/assistant/chat", json=payload())
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()


def test_assistant_calls_only_governed_tool_and_returns_mocked_gemini_text(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test-key")
    configs: list[object] = []
    calls = [
        SimpleNamespace(function_calls=[SimpleNamespace(name="evaluate_policy", args={})], candidates=[]),
        SimpleNamespace(function_calls=[], candidates=[], text="The governed policy requires human review."),
    ]

    class FakeModels:
        def generate_content(self, **kwargs: object) -> object:
            configs.append(kwargs["config"])
            return calls.pop(0)

    monkeypatch.setattr("app.services.assistant.genai.Client", lambda **_: SimpleNamespace(models=FakeModels()))
    with TestClient(app) as client:
        response = client.post("/api/v1/assistant/chat", json=payload())

    assert response.status_code == 200
    body = response.json()
    assert body["response"] == "The governed policy requires human review."
    assert "get_customer_context" in body["tools_used"]
    assert "evaluate_policy" in body["tools_used"]
    assert body["journey_status"] == "COMPLEX_REVIEW"
    assert "cannot" in body["governance_note"].lower()
    assert all(getattr(config, "tools", None) for config in configs)


def test_current_governed_evidence_is_preferred_without_recomputing(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test-key")

    class FakeModels:
        def generate_content(self, **_: object) -> object:
            return SimpleNamespace(function_calls=[], candidates=[], text="The returned policy result is not suitable.")

    monkeypatch.setattr("app.services.assistant.genai.Client", lambda **_: SimpleNamespace(models=FakeModels()))
    journey = {"policy_decision": {"decision": "NOT_SUITABLE", "reason": "Governed result."}}
    with TestClient(app) as client:
        response = client.post("/api/v1/assistant/chat", json=payload(current_journey=journey))

    assert response.status_code == 200
    assert response.json()["journey_status"] == "NOT_SUITABLE"
    assert response.json()["tools_used"] == []
    assert response.json()["context_used"] == ["current_governed_journey"]


def test_assistant_returns_safe_gemini_provider_error(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test-key")

    def unavailable_client(**_: object) -> object:
        raise RuntimeError("sensitive provider failure")

    monkeypatch.setattr("app.services.assistant.genai.Client", unavailable_client)
    with TestClient(app) as client:
        response = client.post("/api/v1/assistant/chat", json=payload())

    assert response.status_code == 502
    assert response.json()["detail"] == "The Gemini service could not complete this request."


def test_assistant_classifies_provider_failures_without_exposing_details() -> None:
    assert FinMateAssistant._classify_provider_error(AssistantResponseError("empty")) == "response_parsing"
    assert FinMateAssistant._classify_provider_error(AssistantToolExecutionError("failed")) == "tool_execution"
    assert FinMateAssistant._classify_provider_error(ValueError("bad request")) == "request_format"
    assert FinMateAssistant._classify_provider_error(ClientError(429, {"error": {"code": 429}})) == "model_api_rate_limit"


def test_assistant_rejects_non_alternating_or_oversized_text_history() -> None:
    with TestClient(app) as client:
        invalid_order = client.post(
            "/api/v1/assistant/chat",
            json=payload(conversation_history=[{"role": "assistant", "content": "Untrusted first turn"}]),
        )
        too_large = client.post(
            "/api/v1/assistant/chat",
            json=payload(conversation_history=[{"role": "user", "content": "x" * 4_000}] * 7),
        )
    assert invalid_order.status_code == 422
    assert too_large.status_code == 422


def test_assistant_accepts_five_consecutive_text_only_turns(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test-key")

    class FakeModels:
        def generate_content(self, **_: object) -> object:
            return SimpleNamespace(function_calls=[], candidates=[], text="Governed prototype explanation.")

    monkeypatch.setattr("app.services.assistant.genai.Client", lambda **_: SimpleNamespace(models=FakeModels()))
    history: list[dict[str, str]] = []
    with TestClient(app) as client:
        for index in range(5):
            response = client.post(
                "/api/v1/assistant/chat",
                json=payload(
                    message=f"Follow-up {index}",
                    conversation_history=history,
                    current_journey={"policy_decision": {"decision": "COMPLEX_REVIEW"}},
                ),
            )
            assert response.status_code == 200
            history.extend([
                {"role": "user", "content": f"Follow-up {index}"},
                {"role": "assistant", "content": response.json()["response"]},
            ])


def test_system_instruction_forbids_invented_or_bypassed_decisions() -> None:
    for required_rule in (
        "Never approve or reject",
        "Never override",
        "Never invent eligibility",
        "Never invent recovery options",
        "asked to bypass policy",
        "simulated prototype data",
    ):
        assert required_rule in SYSTEM_INSTRUCTION


def test_existing_health_api_remains_available() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
