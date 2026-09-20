import httpx

from app.gateway import PromptOpsGatewayClient


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
