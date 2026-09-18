"""Proxies a scenario instance's configured legacy system (FDE-005's mock)
so a student can query it without knowing that service's internal address,
and so its quirks -- schema drift across calls, added latency, an
unhelpful 401 on missing/wrong auth -- reach the student exactly as the
mock produces them, rather than being reinterpreted here.
"""
from __future__ import annotations

import uuid
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import ScenarioInstance

router = APIRouter(prefix="/scenario-instances/{instance_id}/legacy-system", tags=["legacy-system"])


@router.get("")
def call_legacy_system(
    instance_id: uuid.UUID,
    db: Session = Depends(get_db),
    x_legacy_auth: Optional[str] = Header(default=None),
) -> Response:
    instance = db.get(ScenarioInstance, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Scenario instance not found")

    legacy_config = (instance.config or {}).get("legacy_system")
    if not legacy_config:
        raise HTTPException(status_code=404, detail="This scenario has no legacy system configured")

    scenario_id = legacy_config.get("scenario_id", "")
    path = legacy_config.get("path", "")
    url = f"{settings.legacy_api_base_url}/{scenario_id}{path}"

    # The header *name* the mock expects is scenario config (not sensitive --
    # it's just an integration detail); the *value* a caller supplies is
    # whatever the student found (e.g. in a scenario artifact) and typed in
    # themselves, forwarded under that name.
    headers = {}
    auth_header_name = legacy_config.get("auth_header_name")
    if x_legacy_auth and auth_header_name:
        headers[auth_header_name] = x_legacy_auth

    try:
        upstream = httpx.get(url, headers=headers, timeout=15.0)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Legacy system unreachable: {exc}") from exc

    # Pass the mock's response through as-is, status code included -- a 401
    # with its deliberately unhelpful body is exactly what a student should
    # see, not something this proxy smooths over.
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type"),
    )
