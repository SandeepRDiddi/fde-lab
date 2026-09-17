import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import tasks
from app.database import Base
from app.models import ScenarioInstance, ScenarioStatus


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
