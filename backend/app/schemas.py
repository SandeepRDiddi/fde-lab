from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models import ApprovalStatus, ScenarioStatus


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
    approval_outcome: ApprovalStatus | None
    approval_decided_at: datetime | None
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


class SubmissionCreate(BaseModel):
    content: str


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scenario_instance_id: uuid.UUID
    content: str
    status: ApprovalStatus
    review_deadline_at: datetime | None
    auto_decision: ApprovalStatus | None
    decided_at: datetime | None
    notified_at: datetime | None
    created_at: datetime


class SubmissionDecision(BaseModel):
    """Manual approve/reject (FDE-007 AC3) — used when a scenario has no
    configured review delay, or an instructor decides before the
    auto-decision fires."""

    decision: ApprovalStatus

    @field_validator("decision")
    @classmethod
    def _must_be_terminal(cls, value: ApprovalStatus) -> ApprovalStatus:
        if value not in (ApprovalStatus.approved, ApprovalStatus.rejected):
            raise ValueError("decision must be 'approved' or 'rejected'")
        return value
