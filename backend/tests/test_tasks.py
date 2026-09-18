import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import tasks
from app.database import Base
from app.models import ApprovalStatus, ScenarioInstance, ScenarioStatus, Submission


@pytest.fixture()
def session_factory(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(tasks, "SessionLocal", factory)
    yield factory
    Base.metadata.drop_all(bind=engine)


def _make_instance(session_factory, **kwargs) -> uuid.UUID:
    db = session_factory()
    instance = ScenarioInstance(cohort_id=uuid.uuid4(), student_id=uuid.uuid4(), **kwargs)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    instance_id = instance.id
    db.close()
    return instance_id


def test_unlock_task_activates_and_notifies(session_factory):
    instance_id = _make_instance(session_factory)

    tasks.unlock_scenario_instance(str(instance_id))

    db = session_factory()
    instance = db.get(ScenarioInstance, instance_id)
    assert instance.status == ScenarioStatus.active
    assert instance.notified_at is not None
    db.close()


def test_close_task_closes_instance(session_factory):
    instance_id = _make_instance(session_factory, status=ScenarioStatus.active)

    tasks.close_scenario_instance(str(instance_id))

    db = session_factory()
    instance = db.get(ScenarioInstance, instance_id)
    assert instance.status == ScenarioStatus.closed
    db.close()


def test_pivot_task_merges_config(session_factory):
    instance_id = _make_instance(
        session_factory, config={"base": "value"}, pivot_config={"twist": "budget cut"}
    )

    tasks.apply_scenario_pivot(str(instance_id))

    db = session_factory()
    instance = db.get(ScenarioInstance, instance_id)
    assert instance.config == {"base": "value", "twist": "budget cut"}
    assert instance.pivot_applied_at is not None
    db.close()


def test_pivot_task_deep_merges_nested_dict_without_dropping_sibling_keys(session_factory):
    instance_id = _make_instance(
        session_factory,
        config={"persona": {"system_prompt": "You are Dana.", "agenda": "Old agenda"}},
        pivot_config={"persona": {"agenda": "New agenda"}},
    )

    tasks.apply_scenario_pivot(str(instance_id))

    db = session_factory()
    instance = db.get(ScenarioInstance, instance_id)
    assert instance.config == {
        "persona": {"system_prompt": "You are Dana.", "agenda": "New agenda"}
    }
    db.close()


def test_pivot_task_noop_without_pivot_config(session_factory):
    instance_id = _make_instance(session_factory, config={"base": "value"})

    tasks.apply_scenario_pivot(str(instance_id))

    db = session_factory()
    instance = db.get(ScenarioInstance, instance_id)
    assert instance.config == {"base": "value"}
    assert instance.pivot_applied_at is None
    db.close()


def test_unlock_task_missing_instance_is_noop(session_factory):
    tasks.unlock_scenario_instance(str(uuid.uuid4()))


def _make_submission(session_factory, instance_id, **kwargs) -> uuid.UUID:
    db = session_factory()
    submission = Submission(scenario_instance_id=instance_id, content="my report", **kwargs)
    db.add(submission)
    db.commit()
    db.refresh(submission)
    submission_id = submission.id
    db.close()
    return submission_id


def test_auto_decide_submission_applies_configured_outcome(session_factory):
    instance_id = _make_instance(session_factory)
    submission_id = _make_submission(
        session_factory,
        instance_id,
        status=ApprovalStatus.pending_review,
        auto_decision=ApprovalStatus.approved,
    )

    tasks.auto_decide_submission(str(submission_id))

    db = session_factory()
    submission = db.get(Submission, submission_id)
    instance = db.get(ScenarioInstance, instance_id)
    assert submission.status == ApprovalStatus.approved
    assert submission.decided_at is not None
    assert submission.notified_at is not None
    assert instance.approval_outcome == ApprovalStatus.approved
    assert instance.approval_decided_at is not None
    db.close()


def test_auto_decide_submission_noop_if_already_decided(session_factory):
    instance_id = _make_instance(session_factory)
    submission_id = _make_submission(
        session_factory,
        instance_id,
        status=ApprovalStatus.approved,
        auto_decision=ApprovalStatus.rejected,
    )

    tasks.auto_decide_submission(str(submission_id))

    db = session_factory()
    submission = db.get(Submission, submission_id)
    # Already approved manually before the deadline — must not be flipped.
    assert submission.status == ApprovalStatus.approved
    db.close()


def test_auto_decide_submission_missing_submission_is_noop(session_factory):
    tasks.auto_decide_submission(str(uuid.uuid4()))


def test_apply_submission_decision_second_call_loses_the_race(session_factory):
    """Simulates a manual decision and the auto-decide task both reaching
    apply_submission_decision for the same submission -- only the first
    should actually apply; the second must not silently overwrite it."""
    instance_id = _make_instance(session_factory)
    submission_id = _make_submission(session_factory, instance_id, status=ApprovalStatus.pending_review)

    db = session_factory()
    submission = db.get(Submission, submission_id)
    first_applied = tasks.apply_submission_decision(db, submission, ApprovalStatus.approved)
    second_applied = tasks.apply_submission_decision(db, submission, ApprovalStatus.rejected)
    db.close()

    assert first_applied is True
    assert second_applied is False

    db = session_factory()
    submission = db.get(Submission, submission_id)
    assert submission.status == ApprovalStatus.approved
    db.close()


def test_pivot_task_is_idempotent(session_factory):
    instance_id = _make_instance(
        session_factory, config={"base": "value"}, pivot_config={"twist": "budget cut"}
    )

    tasks.apply_scenario_pivot(str(instance_id))

    db = session_factory()
    instance = db.get(ScenarioInstance, instance_id)
    first_applied_at = instance.pivot_applied_at
    # A redelivered/duplicate task run can see a pivot_config that changed
    # since the first run applied (e.g. a reschedule) — it must not re-merge.
    instance.pivot_config = {"twist": "a different change"}
    db.commit()
    db.close()

    tasks.apply_scenario_pivot(str(instance_id))

    db = session_factory()
    instance = db.get(ScenarioInstance, instance_id)
    assert instance.config == {"base": "value", "twist": "budget cut"}
    assert instance.pivot_applied_at == first_applied_at
    db.close()
