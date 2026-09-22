import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.models import Engagement, ScenarioInstance, ScenarioStatus
from app.routers.scenario_instances import _to_read_model
from app.schemas import EngagementCreate, EngagementRead, EngagementStageCreate

router = APIRouter(prefix="/engagements", tags=["engagements"])


class GlobalRetailEngagementCreate(BaseModel):
    """FDE-018 AC4: launches an engagement from whatever's currently in
    GLOBAL_RETAIL_STAGES, so an instructor doesn't hand-assemble the stages
    list themselves."""

    cohort_id: uuid.UUID
    student_id: uuid.UUID


def _to_engagement_read(engagement: Engagement, db: Session) -> EngagementRead:
    stages = (
        db.query(ScenarioInstance)
        .filter(ScenarioInstance.engagement_id == engagement.id)
        .order_by(ScenarioInstance.stage_order)
        .all()
    )
    return EngagementRead(
        id=engagement.id,
        cohort_id=engagement.cohort_id,
        student_id=engagement.student_id,
        status=engagement.status,
        context=engagement.context,
        created_at=engagement.created_at,
        completed_at=engagement.completed_at,
        stages=[_to_read_model(stage) for stage in stages],
    )


def _create_engagement(cohort_id: uuid.UUID, student_id: uuid.UUID, stages: list[EngagementStageCreate], db: Session) -> EngagementRead:
    """FDE-017 AC1: persists one Engagement plus one ScenarioInstance per
    stage, ordered, with only the first stage unlocked (active) -- the rest
    stay not_started until the previous stage's submission is approved
    (app/tasks.py's _advance_engagement). Shared by the generic create
    endpoint and the FDE-018 GlobalRetail convenience endpoint below."""
    engagement = Engagement(cohort_id=cohort_id, student_id=student_id)
    db.add(engagement)
    db.flush()

    for order, stage in enumerate(stages):
        instance = ScenarioInstance(
            cohort_id=cohort_id,
            student_id=student_id,
            config=stage.config,
            engagement_id=engagement.id,
            stage_order=order,
        )
        if order == 0:
            instance.status = ScenarioStatus.active
        db.add(instance)

    db.commit()
    db.refresh(engagement)
    return _to_engagement_read(engagement, db)


@router.post("", response_model=EngagementRead, status_code=201)
def create_engagement(payload: EngagementCreate, db: Session = Depends(get_db)) -> EngagementRead:
    return _create_engagement(payload.cohort_id, payload.student_id, payload.stages, db)


@router.post("/global-retail", response_model=EngagementRead, status_code=201)
def create_global_retail_engagement(
    payload: GlobalRetailEngagementCreate, db: Session = Depends(get_db)
) -> EngagementRead:
    """FDE-018 AC4: launches the GlobalRetail worked-example engagement from
    the current GLOBAL_RETAIL_STAGES content (length grows as later
    stage-content stories land)."""
    stages = [EngagementStageCreate(config=config) for config in GLOBAL_RETAIL_STAGES]
    return _create_engagement(payload.cohort_id, payload.student_id, stages, db)


@router.get("/{engagement_id}", response_model=EngagementRead)
def get_engagement(engagement_id: uuid.UUID, db: Session = Depends(get_db)) -> EngagementRead:
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        raise HTTPException(status_code=404, detail="Engagement not found")
    return _to_engagement_read(engagement, db)
