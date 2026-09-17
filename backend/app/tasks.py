from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import ScenarioInstance, ScenarioStatus


@celery_app.task(name="scenario.unlock")
def unlock_scenario_instance(instance_id: str) -> None:
    """AC2: transition to active and notify the student."""
    db = SessionLocal()
    try:
        instance = db.get(ScenarioInstance, uuid.UUID(instance_id))
        if instance is None:
            return
        instance.status = ScenarioStatus.active
        instance.notified_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()


@celery_app.task(name="scenario.close")
def close_scenario_instance(instance_id: str) -> None:
    """AC3: transition to closed, locking further submissions."""
    db = SessionLocal()
    try:
        instance = db.get(ScenarioInstance, uuid.UUID(instance_id))
        if instance is None:
            return
        instance.status = ScenarioStatus.closed
        db.commit()
    finally:
        db.close()


@celery_app.task(name="scenario.pivot")
def apply_scenario_pivot(instance_id: str) -> None:
    """AC4: inject the configured pivot change at the configured time."""
    db = SessionLocal()
    try:
        instance = db.get(ScenarioInstance, uuid.UUID(instance_id))
        if instance is None or not instance.pivot_config:
            return
        instance.config = {**instance.config, **instance.pivot_config}
        instance.pivot_applied_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()
