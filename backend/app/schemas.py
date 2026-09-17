from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import ScenarioStatus


class ScenarioInstanceCreate(BaseModel):
    cohort_id: uuid.UUID
    student_id: uuid.UUID
    config: dict = {}


class ScenarioInstanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cohort_id: uuid.UUID
    student_id: uuid.UUID
    status: ScenarioStatus
    config: dict
    dataset_location: str | None
    start_at: datetime | None
    end_at: datetime | None
    created_at: datetime


class ScenarioInstanceDatasetUpdate(BaseModel):
    dataset_location: str
