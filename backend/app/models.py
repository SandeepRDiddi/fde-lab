from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class ScenarioStatus(str, enum.Enum):
    not_started = "not_started"
    active = "active"
    closed = "closed"


class ApprovalStatus(str, enum.Enum):
    submitted = "submitted"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"


class ScenarioInstance(Base):
    """A scenario configured for one student within one cohort."""

    __tablename__ = "scenario_instances"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # cohort_id / student_id are opaque identifiers for now — no FK, since the
    # cohorts/students tables don't exist yet (later story).
    cohort_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    status: Mapped[ScenarioStatus] = mapped_column(
        Enum(ScenarioStatus, name="scenario_status"),
        nullable=False,
        default=ScenarioStatus.not_started,
    )
    # Structured injects config: documents, data, mocks, persona (FDE-001 AC4).
    # config["data_gen"] carries the synthetic data generator's domain/row_count/
    # messiness knobs (FDE-003 AC1-2).
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # Object storage location of the generated dataset, set by the data generator
    # once it has produced and uploaded this instance's dataset (FDE-003 AC3).
    dataset_location: Mapped[str | None] = mapped_column(String, nullable=True)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Mid-scenario pivot (FDE-002 AC4): when set, a Celery job fires at pivot_at and
    # merges pivot_config into config (the "client changes their mind" moment).
    pivot_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pivot_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pivot_applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Set when the unlock job notifies the student (FDE-002 AC2).
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Celery task ids for the currently-scheduled jobs, so a reschedule can
    # revoke the previous schedule's still-pending jobs instead of leaving
    # them to fire at their old times alongside the new ones.
    unlock_task_id: Mapped[str | None] = mapped_column(nullable=True)
    close_task_id: Mapped[str | None] = mapped_column(nullable=True)
    pivot_task_id: Mapped[str | None] = mapped_column(nullable=True)
    # Outcome of this instance's approval workflow, recorded once a
    # submission is approved or rejected (FDE-007 AC3).
    approval_outcome: Mapped[ApprovalStatus | None] = mapped_column(
        Enum(ApprovalStatus, name="approval_status"), nullable=True
    )
    approval_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Submission(Base):
    """A student's deliverable submission for a scenario instance. Only ever
    created after passing the compliance checklist -- app/compliance.py
    evaluates it server-side in create_submission and rejects a failing one
    (422) before a row is ever written here. Progresses through the
    approval workflow state machine: submitted -> pending_review ->
    approved/rejected (FDE-007)."""

    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    scenario_instance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("scenario_instances.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approval_status"),
        nullable=False,
        default=ApprovalStatus.submitted,
    )
    # Set from config["approval_workflow"] at submission time when a scenario
    # configures a review delay (FDE-007 AC2): the auto-decide job's eta, and
    # the outcome it applies once it fires.
    review_deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_decision: Mapped[ApprovalStatus | None] = mapped_column(
        Enum(ApprovalStatus, name="approval_status"), nullable=True
    )
    # Celery task id for the scheduled auto-decide job, so a manual decision
    # made before the deadline can revoke it (mirrors *_task_id on
    # ScenarioInstance).
    auto_decide_task_id: Mapped[str | None] = mapped_column(nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
