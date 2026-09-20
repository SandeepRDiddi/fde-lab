from fastapi import APIRouter, HTTPException

from app.schemas import ScenarioDraftRequest
from app.scenario_generator import GeneratorError, generate_scenario_config

router = APIRouter(prefix="/scenario-generator", tags=["scenario-generator"])


@router.post("/draft")
def draft_scenario(payload: ScenarioDraftRequest) -> dict:
    """FDE-014: drafts a scenario config from a raw requirement -- returned
    for an instructor to review, not persisted. Creating the actual instance
    is a separate POST /scenario-instances call with this (possibly edited)
    config, same as any other scenario."""
    try:
        return generate_scenario_config(payload.requirement)
    except GeneratorError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
