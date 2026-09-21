"""Client for the persona service's model backend (architecture.md → AI
persona service calls this "PromptOps Gateway").

No PromptOps Gateway exists to point at yet, and a hosted frontier-model API
(Claude, GPT) costs real money per call for a training lab, so this talks to
an open-weight model instead via the OpenAI-compatible chat/completions
contract -- the shape Groq, Together, DeepInfra, OpenRouter, and Ollama's own
/v1 endpoint all speak, so switching provider later is a URL/key/model swap,
not a rewrite. Defaults to Groq (generous free tier, far faster than a local
CPU-bound Ollama instance -- see FDE_PROMPTOPS_GATEWAY_URL/_API_KEY/_MODEL in
.env); point FDE_PROMPTOPS_GATEWAY_URL at a local Ollama's /v1 path instead
to go back to fully local/free with no API key.
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
        # OpenAI chat-completions convention: the system prompt is just the
        # first message in the list (role "system"), not a separate field.
        full_messages = [{"role": "system", "content": system_prompt}, *messages]
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            response = self._client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": full_messages,
                    "stream": False,
                    # The default model (openai/gpt-oss-20b) is a reasoning
                    # model -- it spends completion tokens on hidden
                    # chain-of-thought before writing the actual reply.
                    # Without a generous budget a longer conversation or a
                    # persona system prompt that invites more deliberation
                    # risks finish_reason "length" with truncated/empty
                    # content (see backend/app/scenario_generator.py's own
                    # comment on this same failure mode, caught live there).
                    "max_tokens": 4096,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            # Network failure, timeout, or a non-2xx from the model backend --
            # surface as a clean error instead of an unhandled 500. A common
            # everyday case: no/invalid FDE_PROMPTOPS_GATEWAY_API_KEY, or the
            # model in FDE_PROMPTOPS_GATEWAY_MODEL isn't available there.
            raise GatewayError(f"Model backend request failed: {exc}") from exc
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        finish_reason = data["choices"][0].get("finish_reason")
        if finish_reason == "length" and not content.strip():
            raise GatewayError(
                "Model ran out of tokens (finish_reason=length) before writing any reply -- "
                "it likely spent the whole budget on internal reasoning for this turn"
            )
        return content


@lru_cache
def get_gateway_client() -> PromptOpsGatewayClient:
    return PromptOpsGatewayClient()
