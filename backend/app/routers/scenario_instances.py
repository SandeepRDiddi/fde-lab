import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ScenarioInstance
from app.schemas import ScenarioInstanceCreate, ScenarioInstanceRead, ScenarioInstanceSchedule
from app.tasks import apply_scenario_pivot, close_scenario_instance, unlock_scenario_instance

router = APIRouter(prefix="/scenario-instances", tags=["scenario-instances"])


@router.post("", response_model=ScenarioInstanceRead, status_code=201)
def create_scenario_instance(
    payload: ScenarioInstanceCreate, db: Session = Depends(get_db)
) -> ScenarioInstanceRead:
    instance = ScenarioInstance(
        cohort_id=payload.cohort_id,
        student_id=payload.student_id,
        config=payload.config,
    )
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


@router.get("/{instance_id}", response_model=ScenarioInstanceRead)
def get_scenario_instance(instance_id: uuid.UUID, db: Session = Depends(get_db)) -> ScenarioInstanceRead:
    instance = db.get(ScenarioInstance, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Scenario instance not found")
    return instance


@router.post("/{instance_id}/schedule", response_model=ScenarioInstanceRead)
def schedule_scenario_instance(
    instance_id: uuid.UUID, payload: ScenarioInstanceSchedule, db: Session = Depends(get_db)
) -> ScenarioInstanceRead:
    """AC1/AC4: set the instance's unlock/close/pivot times and enqueue the
    corresponding Celery jobs for those times."""
    instance = db.get(ScenarioInstance, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Scenario instance not found")

    if payload.end_at <= payload.start_at:
        raise HTTPException(status_code=422, detail="end_at must be after start_at")
    if payload.pivot_at is not None and not (payload.start_at < payload.pivot_at < payload.end_at):
        raise HTTPException(status_code=422, detail="pivot_at must fall between start_at and end_at")

    instance.start_at = payload.start_at
    instance.end_at = payload.end_at
    instance.pivot_at = payload.pivot_at
    instance.pivot_config = payload.pivot_config
    db.commit()
    db.refresh(instance)

    unlock_scenario_instance.apply_async(args=[str(instance.id)], eta=payload.start_at)
    close_scenario_instance.apply_async(args=[str(instance.id)], eta=payload.end_at)
    if payload.pivot_at is not None:
        apply_scenario_pivot.apply_async(args=[str(instance.id)], eta=payload.pivot_at)

    return instance
