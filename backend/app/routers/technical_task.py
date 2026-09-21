"""FDE-015: a non-graded way to run a technical-task query, separate from
submitting it for real (app/routers/submissions.py). Lets a student iterate
-- explore, run, adjust, run again -- before committing to a graded
submission, instead of the first query they write being the only one that's
ever executed.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.grading import GradingError, run_query
from app.models import ScenarioInstance
from app.schemas import TechnicalTaskRunRequest

router = APIRouter(prefix="/scenario-instances/{instance_id}/technical-task", tags=["technical-task"])


@router.post("/run")
def run_technical_task_query(
    instance_id: uuid.UUID, payload: TechnicalTaskRunRequest, db: Session = Depends(get_db)
) -> dict:
    instance = db.get(ScenarioInstance, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Scenario instance not found")

    technical_task = instance.config.get("technical_task")
    if not technical_task:
        raise HTTPException(status_code=404, detail="This scenario has no technical task configured")

    try:
        return run_query(payload.content, instance.dataset_location, technical_task)
    except GradingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
