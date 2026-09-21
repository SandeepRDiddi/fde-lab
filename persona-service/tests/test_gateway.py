import httpx
import pytest

from app.gateway import GatewayError, PromptOpsGatewayClient


def _client_with_response(json_body):
    client = PromptOpsGatewayClient()
    client._client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=json_body))
    )
    return client


def test_complete_returns_openai_compatible_message_content():
    client = _client_with_response(
        {"choices": [{"message": {"role": "assistant", "content": "hello"}}]}
    )

    reply = client.complete(system_prompt="sys", messages=[])

    assert reply == "hello"


def test_complete_sends_system_prompt_as_first_message():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured["body"] = json.loads(request.content)
        captured["path"] = request.url.path
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    client = PromptOpsGatewayClient()
    client._client = httpx.Client(transport=httpx.MockTransport(handler))

    client.complete(system_prompt="You are Dana.", messages=[{"role": "user", "content": "hi"}])

    assert captured["path"].endswith("/chat/completions")
    assert captured["body"]["messages"][0] == {"role": "system", "content": "You are Dana."}
    assert captured["body"]["messages"][1] == {"role": "user", "content": "hi"}
    assert captured["body"]["stream"] is False


def test_complete_sends_bearer_auth_header_when_api_key_set():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    client = PromptOpsGatewayClient()
    client.api_key = "test-key-123"
    client._client = httpx.Client(transport=httpx.MockTransport(handler))

    client.complete(system_prompt="sys", messages=[])

    assert captured["auth"] == "Bearer test-key-123"


def test_complete_sends_a_generous_max_tokens():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]})

    client = PromptOpsGatewayClient()
    client._client = httpx.Client(transport=httpx.MockTransport(handler))

    client.complete(system_prompt="sys", messages=[])

    assert captured["body"]["max_tokens"] >= 2048


def test_complete_raises_when_reasoning_model_exhausts_tokens_with_no_output():
    # Caught live in the scenario generator (same default model,
    # openai/gpt-oss-20b) -- a reasoning model can spend its whole
    # completion budget on hidden chain-of-thought and return
    # finish_reason "length" with zero characters of actual reply content.
    client = _client_with_response({"choices": [{"message": {"content": ""}, "finish_reason": "length"}]})

    with pytest.raises(GatewayError, match="ran out of tokens"):
        client.complete(system_prompt="sys", messages=[])
