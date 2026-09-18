from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import update

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import ApprovalStatus, ScenarioInstance, ScenarioStatus, Submission


def revoke_task_if_pending(task_id: str | None) -> None:
    """Best-effort: revoke (and terminate if a worker already picked it up)
    a scheduled Celery task. An unreachable broker shouldn't block whatever
    the caller is doing, and under eager execution the task already ran
    synchronously before this is ever called, so there's nothing to revoke.
    Shared by the reschedule path (scenario_instances.py) and the manual
    approval decision path (submissions.py)."""
    if not task_id or celery_app.conf.task_always_eager:
        return
    try:
        celery_app.control.revoke(task_id, terminate=True)
    except Exception:
        pass


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


def apply_submission_decision(db, submission: Submission, decision: ApprovalStatus) -> bool:
    """AC3: record the outcome and notify the student. Shared by the manual
    decision route and the auto-decide task below so both paths land in the
    same place.

    The update is conditioned on status == pending_review in the same SQL
    statement (not a separate read-then-write) so a manual decision and the
    auto-decide task racing each other can't both apply -- whichever's
    UPDATE runs first wins, the second matches zero rows. Returns whether
    this call actually applied the decision.
    """
    now = datetime.now(timezone.utc)
    result = db.execute(
        update(Submission)
        .where(Submission.id == submission.id, Submission.status == ApprovalStatus.pending_review)
        .values(status=decision, decided_at=now, notified_at=now)
    )
    if result.rowcount == 0:
        db.rollback()
        return False

    instance = db.get(ScenarioInstance, submission.scenario_instance_id)
    if instance is not None:
        instance.approval_outcome = decision
        instance.approval_decided_at = now

    db.commit()
    db.refresh(submission)
    return True


@celery_app.task(name="approval.auto_decide")
def auto_decide_submission(submission_id: str) -> None:
    """AC2: apply the scenario-configured auto-decision once the review
    delay elapses. A no-op if the submission was already decided manually
    before the deadline (idempotency guard, same shape as
    apply_scenario_pivot's)."""
    db = SessionLocal()
    try:
        submission = db.get(Submission, uuid.UUID(submission_id))
        if submission is None or submission.auto_decision is None:
            return
        # apply_submission_decision's own WHERE clause is the real guard
        # against a race with a manual decision; this check is just a
        # cheap early-out to skip the UPDATE attempt in the common case.
        if submission.status != ApprovalStatus.pending_review:
            return
        apply_submission_decision(db, submission, submission.auto_decision)
    finally:
        db.close()
