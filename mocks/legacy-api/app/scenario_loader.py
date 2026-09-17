from __future__ import annotations

import asyncio
import json
import logging
from itertools import count
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import settings

log = logging.getLogger(__name__)


class ScenarioConfig(BaseModel):
    """One legacy-system scenario: an endpoint, its quirks, and its response variants."""

    scenario_id: str
    path: str
    auth_header: str | None = None
    latency_ms: int = 0
    responses: list[dict[str, Any]] = Field(min_length=1)


def load_scenarios(scenario_dir: Path | None = None) -> list[ScenarioConfig]:
    """Load every *.json scenario config from a directory. Add a scenario by
    dropping a new file here — no code change required.

    A malformed scenario file is logged and skipped rather than crashing the
    whole service — one bad config shouldn't take down every other scenario.
    """
    directory = scenario_dir or settings.scenario_dir
    if not directory.exists():
        return []
    scenarios = []
    for path in sorted(directory.glob("*.json")):
        try:
            scenarios.append(ScenarioConfig(**json.loads(path.read_text())))
        except Exception:
            log.exception("Skipping invalid scenario file %s", path)
    return scenarios


def build_router(scenario: ScenarioConfig) -> APIRouter:
    router = APIRouter()
    call_counter = count()

    @router.get(f"/{scenario.scenario_id}{scenario.path}")
    async def endpoint(request: Request) -> JSONResponse:
        if scenario.auth_header is not None:
            if not request.headers.get(scenario.auth_header):
                # Deliberately unhelpful: no mention of which header is missing.
                return JSONResponse(
                    content={"error": "ERR-4471", "message": "request could not be completed"},
                    status_code=401,
                )

        if scenario.latency_ms > 0:
            await asyncio.sleep(scenario.latency_ms / 1000)

        call_number = next(call_counter)
        body = scenario.responses[call_number % len(scenario.responses)]
        return JSONResponse(content=body, status_code=200)

    return router
