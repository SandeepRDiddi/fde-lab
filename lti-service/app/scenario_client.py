"""Maps an LMS course/cohort onto a scenario instance in the scenario engine
(FDE-001), satisfying acceptance criterion 2.

The scenario engine doesn't exist in this branch yet (FDE-001 landed on its
own feature branch, not merged here) -- this client calls the contract this
service expects at SCENARIO_ENGINE_BASE_URL. See lti-service/README.md for
the deviation this implies and what integration work is still needed once
both branches merge.
"""
from dataclasses import dataclass
from typing import Optional

import httpx
from fastapi import HTTPException

from .config import settings
from .launch import LtiLaunch


@dataclass
class ScenarioInstance:
    scenario_instance_id: str
    launch_path: str  # path within the frontend app, e.g. "/scenario/abc123"


def resolve_scenario_instance(launch: LtiLaunch) -> ScenarioInstance:
    if launch.context_id is None:
        raise HTTPException(status_code=400, detail="Launch is missing an LMS context (course) id")

    try:
        response = httpx.get(
            f"{settings.scenario_engine_base_url}/internal/lti-mappings",
            params={
                "platform_issuer": launch.issuer,
                "deployment_id": launch.deployment_id,
                "context_id": launch.context_id,
            },
            headers={"Authorization": f"Bearer {settings.scenario_engine_internal_token}"},
            timeout=10.0,
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Scenario engine unreachable: {exc}") from exc

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No scenario instance is mapped to LMS context {launch.context_id!r} "
                f"(deployment {launch.deployment_id!r}). An instructor needs to link "
                "this course to a cohort/scenario before students can launch into it."
            ),
        )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Scenario engine returned {response.status_code}")

    data = response.json()
    return ScenarioInstance(
        scenario_instance_id=data["scenario_instance_id"],
        launch_path=data["launch_path"],
    )
