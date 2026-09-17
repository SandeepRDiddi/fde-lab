from __future__ import annotations

import asyncio
import json
from itertools import count
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from app.config import settings


class ScenarioConfig(BaseModel):
    """One legacy-system scenario: an endpoint, its quirks, and its response variants."""

    scenario_id: str
    path: str
    auth_header: str | None = None
    latency_ms: int = 0
    responses: list[dict[str, Any]]


def load_scenarios(scenario_dir: Path | None = None) -> list[ScenarioConfig]:
    """Load every *.json scenario config from a directory. Add a scenario by
    dropping a new file here — no code change required."""
    directory = scenario_dir or settings.scenario_dir
    if not directory.exists():
        return []
    return [
        ScenarioConfig(**json.loads(path.read_text()))
        for path in sorted(directory.glob("*.json"))
    ]


def build_router(scenario: ScenarioConfig) -> APIRouter:
    router = APIRouter()
    call_counter = count()

    @router.get(f"/{scenario.scenario_id}{scenario.path}")
    async def endpoint(request: Request) -> Response:
        if scenario.auth_header is not None:
            if not request.headers.get(scenario.auth_header):
                # Deliberately unhelpful: no mention of which header is missing.
                return Response(
                    content=json.dumps(
                        {"error": "ERR-4471", "message": "request could not be completed"}
                    ),
                    status_code=401,
                    media_type="application/json",
                )

        if scenario.latency_ms > 0:
            await asyncio.sleep(scenario.latency_ms / 1000)

        call_number = next(call_counter)
        body = scenario.responses[call_number % len(scenario.responses)]
        return Response(content=json.dumps(body), status_code=200, media_type="application/json")

    return router
