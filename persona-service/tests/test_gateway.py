import httpx

from app.gateway import PromptOpsGatewayClient


def _client_with_response(json_body):
    client = PromptOpsGatewayClient()
    client._client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=json_body))
    )
    return client


def test_complete_handles_plain_string_content():
    client = _client_with_response({"content": "hello"})

    reply = client.complete(system_prompt="sys", messages=[])

    assert reply == "hello"


def test_complete_handles_anthropic_content_block_list():
    client = _client_with_response(
        {"content": [{"type": "text", "text": "hello "}, {"type": "text", "text": "world"}]}
    )

    reply = client.complete(system_prompt="sys", messages=[])

    assert reply == "hello world"
