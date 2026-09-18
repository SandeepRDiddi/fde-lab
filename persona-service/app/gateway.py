"""Client for the persona service's model backend (architecture.md → AI
persona service calls this "PromptOps Gateway").

No PromptOps Gateway exists to point at yet, and a hosted Claude API costs
real money per call for a training lab, so this defaults to a local Ollama
instance (free, open-source models, runs on the training infrastructure
itself) via Ollama's native /api/chat endpoint. Swap
FDE_PROMPTOPS_GATEWAY_URL to a real gateway's URL later -- everything above
this client (routers/conversations.py) is unaffected either way.
"""
from __future__ import annotations

from functools import lru_cache

import httpx

from app.config import settings


class GatewayError(RuntimeError):
    """PromptOps Gateway was unreachable or returned an error response."""


class PromptOpsGatewayClient:
    def __init__(self) -> None:
        self.base_url = settings.promptops_gateway_url
        self.api_key = settings.promptops_gateway_api_key
        self.model = settings.promptops_gateway_model
        # Reused across calls so requests on the hot chat-turn path share a
        # pooled connection instead of paying a fresh TCP/TLS handshake each
        # time. Generous timeout: local CPU inference (no dedicated GPU, or
        # one shared with everything else on the machine) can take well over
        # 30s for a single turn on anything past a small (~3B) model.
        self._client = httpx.Client(timeout=90.0)

    def complete(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        # Ollama's chat API takes the system prompt as just another message
        # in the list (role "system"), rather than a separate top-level field.
        ollama_messages = [{"role": "system", "content": system_prompt}, *messages]
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            response = self._client.post(
                f"{self.base_url}/api/chat",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": ollama_messages,
                    "stream": False,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            # Network failure, timeout, or a non-2xx from the model backend --
            # surface as a clean error instead of an unhandled 500. A common
            # everyday case: Ollama isn't running, or the model in
            # FDE_PROMPTOPS_GATEWAY_MODEL hasn't been pulled yet.
            raise GatewayError(f"Model backend request failed: {exc}") from exc
        data = response.json()
        return data["message"]["content"]


@lru_cache
def get_gateway_client() -> PromptOpsGatewayClient:
    return PromptOpsGatewayClient()
