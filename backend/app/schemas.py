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
    start_at: datetime | None
    end_at: datetime | None
    pivot_at: datetime | None
    pivot_config: dict | None
    pivot_applied_at: datetime | None
    notified_at: datetime | None
    created_at: datetime


class ScenarioInstanceSchedule(BaseModel):
    """Instructor-set schedule for a scenario instance (FDE-002 AC1, AC4)."""

    start_at: datetime
    end_at: datetime
    pivot_at: datetime | None = None
    pivot_config: dict | None = None
