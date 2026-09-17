from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

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
    pivot_at: datetime | None
    pivot_config: dict | None
    pivot_applied_at: datetime | None
    notified_at: datetime | None
    created_at: datetime


class ScenarioInstanceDatasetUpdate(BaseModel):
    dataset_location: str


class ScenarioInstanceSchedule(BaseModel):
    """Instructor-set schedule for a scenario instance (FDE-002 AC1, AC4)."""

    start_at: datetime
    end_at: datetime
    pivot_at: datetime | None = None
    pivot_config: dict | None = None

    @field_validator("start_at", "end_at", "pivot_at")
    @classmethod
    def _require_timezone(cls, value: datetime | None) -> datetime | None:
        # Comparing a naive and an aware datetime raises TypeError, not a
        # clean validation error — reject naive input here so a dropped
        # offset on one field fails with 422, not an unhandled 500.
        if value is not None and value.tzinfo is None:
            raise ValueError("must include a timezone offset")
        return value
