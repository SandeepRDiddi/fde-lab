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


def _merge_pivot_config(config: dict, pivot_config: dict) -> dict:
    """One-level-deep merge: a dict value in pivot_config merges into the
    matching dict in config instead of replacing it outright. Needed so e.g.
    pivot_config={"persona": {"agenda": "..."}} updates just the agenda
    without dropping sibling keys like persona.system_prompt (FDE-004)."""
    merged = dict(config)
    for key, value in pivot_config.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


@celery_app.task(name="scenario.pivot")
def apply_scenario_pivot(instance_id: str) -> None:
    """AC4: inject the configured pivot change at the configured time."""
    db = SessionLocal()
    try:
        instance = db.get(ScenarioInstance, uuid.UUID(instance_id))
        if instance is None or not instance.pivot_config or instance.pivot_applied_at is not None:
            return
        instance.config = _merge_pivot_config(instance.config, instance.pivot_config)
        instance.pivot_applied_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()
