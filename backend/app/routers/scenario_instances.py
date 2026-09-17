import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ScenarioInstance
from app.schemas import (
    ScenarioInstanceCreate,
    ScenarioInstanceDatasetUpdate,
    ScenarioInstanceRead,
)

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
