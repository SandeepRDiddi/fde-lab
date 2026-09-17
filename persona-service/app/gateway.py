"""Client for PromptOps Gateway — the only path to Claude (architecture.md → AI
persona service: "Persona calls route through PromptOps Gateway rather than
hitting the Claude API directly").

The gateway's exact wire contract isn't documented elsewhere in this repo, so this
client assumes it proxies the Anthropic Messages API shape (model / system /
messages in, a text completion out) since that's the most natural fit for "Claude
via PromptOps Gateway". Flagged in the FDE-004 implementation log as an assumption
to confirm once PromptOps Gateway's actual contract is available.
"""
from __future__ import annotations

import httpx

from app.config import settings


class PromptOpsGatewayClient:
    def __init__(self) -> None:
        self.base_url = settings.promptops_gateway_url
        self.api_key = settings.promptops_gateway_api_key
        self.model = settings.promptops_gateway_model

    def complete(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        response = httpx.post(
            f"{self.base_url}/v1/messages",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "system": system_prompt,
                "messages": messages,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["content"]


def get_gateway_client() -> PromptOpsGatewayClient:
    return PromptOpsGatewayClient()
