from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class ScenarioStatus(str, enum.Enum):
    not_started = "not_started"
    active = "active"
    closed = "closed"


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
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
