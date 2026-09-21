import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dataset_store import DatasetStoreError, preview_dataset
from app.models import ScenarioInstance
from app.schemas import (
    ScenarioInstanceCreate,
    ScenarioInstanceDatasetUpdate,
    ScenarioInstanceRead,
    ScenarioInstanceSchedule,
)
from app.tasks import (
    apply_scenario_pivot,
    close_scenario_instance,
    revoke_task_if_pending,
    unlock_scenario_instance,
)

router = APIRouter(prefix="/scenario-instances", tags=["scenario-instances"])

# Fields inside config["technical_task"] that are the grader's answer key --
# never safe to return over this router's endpoints. Nothing legitimate
# consumes them via the API: grading (app/grading.py) and the run-preview
# endpoint (app/routers/technical_task.py) read them straight off the ORM
# object server-side, and the only place an answer key should ever be
# visible in a response is the generator's own draft-preview
# (POST /scenario-generator/draft, an instructor-authoring step before an
# instance even exists) -- not any endpoint a student's browser calls.
_ANSWER_KEY_FIELDS = ("reference_query", "reference_solution")


def _redact_technical_task(config: dict) -> dict:
    technical_task = config.get("technical_task")
    if not isinstance(technical_task, dict):
        return config
    redacted = {k: v for k, v in technical_task.items() if k not in _ANSWER_KEY_FIELDS}
    return {**config, "technical_task": redacted}


def _to_read_model(instance: ScenarioInstance) -> ScenarioInstanceRead:
    read = ScenarioInstanceRead.model_validate(instance)
    return read.model_copy(update={"config": _redact_technical_task(read.config)})


@router.get("", response_model=list[ScenarioInstanceRead])
def list_scenario_instances(cohort_id: uuid.UUID, db: Session = Depends(get_db)) -> list[ScenarioInstanceRead]:
    """FDE-009 AC2: an instructor console lists every student's instance for
    a cohort to show live status, one row per student."""
    instances = (
        db.query(ScenarioInstance)
        .filter(ScenarioInstance.cohort_id == cohort_id)
        .order_by(ScenarioInstance.created_at)
        .all()
    )
    return [_to_read_model(instance) for instance in instances]


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
    return _to_read_model(instance)


@router.get("/{instance_id}", response_model=ScenarioInstanceRead)
def get_scenario_instance(instance_id: uuid.UUID, db: Session = Depends(get_db)) -> ScenarioInstanceRead:
    instance = db.get(ScenarioInstance, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Scenario instance not found")
    return _to_read_model(instance)


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
    return _to_read_model(instance)


@router.get("/{instance_id}/dataset-preview")
def get_dataset_preview(instance_id: uuid.UUID, limit: int = 20, db: Session = Depends(get_db)) -> dict:
    """FDE-015: lets a student browse the actual dataset before writing a
    query against it -- real FDE work starts with looking at the data, not
    guessing at column names blind."""
    instance = db.get(ScenarioInstance, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Scenario instance not found")
    if not instance.dataset_location:
        raise HTTPException(status_code=404, detail="This scenario has no dataset yet")
    try:
        return preview_dataset(instance.dataset_location, limit=limit)
    except DatasetStoreError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


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
    for old_task_id in (instance.unlock_task_id, instance.close_task_id, instance.pivot_task_id):
        revoke_task_if_pending(old_task_id)

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

    return _to_read_model(instance)
