import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.database import get_db
from app.models import ScenarioInstance
from app.schemas import (
    ScenarioInstanceCreate,
    ScenarioInstanceDatasetUpdate,
    ScenarioInstanceRead,
    ScenarioInstanceSchedule,
)
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


@router.patch("/{instance_id}/dataset", response_model=ScenarioInstanceRead)
def set_scenario_instance_dataset(
    instance_id: uuid.UUID,
    payload: ScenarioInstanceDatasetUpdate,
    db: Session = Depends(get_db),
) -> ScenarioInstanceRead:
    instance = db.get(ScenarioInstance, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Scenario instance not found")
    instance.dataset_location = payload.dataset_location
    db.commit()
    db.refresh(instance)
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

    # Revoke any jobs left over from a previous schedule on this instance —
    # otherwise a reschedule leaves the old unlock/close/pivot jobs pending
    # and they still fire at their original times alongside the new ones.
    # Best-effort: an unreachable broker shouldn't block rescheduling, and
    # under eager execution (tests) the old jobs already ran synchronously
    # before this call, so there's nothing left to revoke.
    if not celery_app.conf.task_always_eager:
        for old_task_id in (instance.unlock_task_id, instance.close_task_id, instance.pivot_task_id):
            if old_task_id:
                try:
                    celery_app.control.revoke(old_task_id)
                except Exception:
                    pass

    instance.start_at = payload.start_at
    instance.end_at = payload.end_at
    instance.pivot_at = payload.pivot_at
    instance.pivot_config = payload.pivot_config
    db.commit()
    db.refresh(instance)

    # Enqueued in chronological order so eager-mode tests exercise the same
    # sequence real ETA-scheduled execution would.
    unlock_result = unlock_scenario_instance.apply_async(args=[str(instance.id)], eta=payload.start_at)
    pivot_result = None
    if payload.pivot_at is not None:
        pivot_result = apply_scenario_pivot.apply_async(args=[str(instance.id)], eta=payload.pivot_at)
    close_result = close_scenario_instance.apply_async(args=[str(instance.id)], eta=payload.end_at)

    instance.unlock_task_id = unlock_result.id
    instance.pivot_task_id = pivot_result.id if pivot_result is not None else None
    instance.close_task_id = close_result.id
    db.commit()
    # Tasks run in their own DB session; under eager execution they've
    # already committed status/config changes by the time apply_async
    # returns above, so re-sync this session's copy before returning it.
    db.refresh(instance)

    return instance
