import uuid
from datetime import datetime, timedelta, timezone


def _create_instance(client):
    payload = {
        "cohort_id": str(uuid.uuid4()),
        "student_id": str(uuid.uuid4()),
        "config": {"base": "value"},
    }
    return client.post("/scenario-instances", json=payload).json()


def test_schedule_enqueues_unlock_and_close_jobs(client):
    instance = _create_instance(client)
    now = datetime.now(timezone.utc)
    start_at = now + timedelta(seconds=1)
    end_at = now + timedelta(seconds=2)

    response = client.post(
        f"/scenario-instances/{instance['id']}/schedule",
        json={"start_at": start_at.isoformat(), "end_at": end_at.isoformat()},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["start_at"] is not None
    assert body["end_at"] is not None

    # Celery runs eagerly in tests (compressed timings, no live broker needed) —
    # both jobs fire synchronously as soon as they're enqueued.
    final = client.get(f"/scenario-instances/{instance['id']}").json()
    assert final["status"] == "closed"
    assert final["notified_at"] is not None


def test_schedule_with_pivot_injects_config_change(client):
    instance = _create_instance(client)
    now = datetime.now(timezone.utc)
    start_at = now + timedelta(seconds=1)
    pivot_at = now + timedelta(seconds=2)
    end_at = now + timedelta(seconds=3)

    response = client.post(
        f"/scenario-instances/{instance['id']}/schedule",
        json={
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "pivot_at": pivot_at.isoformat(),
            "pivot_config": {"twist": "budget cut 20%"},
        },
    )

    assert response.status_code == 200
    final = client.get(f"/scenario-instances/{instance['id']}").json()
    assert final["status"] == "closed"
    assert final["config"] == {"base": "value", "twist": "budget cut 20%"}
    assert final["pivot_applied_at"] is not None


def test_schedule_without_pivot_leaves_config_untouched(client):
    instance = _create_instance(client)
    now = datetime.now(timezone.utc)

    client.post(
        f"/scenario-instances/{instance['id']}/schedule",
        json={
            "start_at": (now + timedelta(seconds=1)).isoformat(),
            "end_at": (now + timedelta(seconds=2)).isoformat(),
        },
    )

    final = client.get(f"/scenario-instances/{instance['id']}").json()
    assert final["config"] == {"base": "value"}
    assert final["pivot_applied_at"] is None


def test_schedule_rejects_end_before_start(client):
    instance = _create_instance(client)
    now = datetime.now(timezone.utc)

    response = client.post(
        f"/scenario-instances/{instance['id']}/schedule",
        json={
            "start_at": (now + timedelta(hours=1)).isoformat(),
            "end_at": now.isoformat(),
        },
    )

    assert response.status_code == 422


def test_schedule_rejects_pivot_outside_window(client):
    instance = _create_instance(client)
    now = datetime.now(timezone.utc)

    response = client.post(
        f"/scenario-instances/{instance['id']}/schedule",
        json={
            "start_at": now.isoformat(),
            "end_at": (now + timedelta(hours=1)).isoformat(),
            "pivot_at": (now + timedelta(hours=2)).isoformat(),
            "pivot_config": {"twist": "x"},
        },
    )

    assert response.status_code == 422


def test_schedule_rejects_naive_datetime(client):
    instance = _create_instance(client)
    now = datetime.now(timezone.utc)

    response = client.post(
        f"/scenario-instances/{instance['id']}/schedule",
        json={
            "start_at": now.replace(tzinfo=None).isoformat(),
            "end_at": (now + timedelta(hours=1)).isoformat(),
        },
    )

    assert response.status_code == 422


def test_reschedule_revokes_previous_jobs(client, monkeypatch):
    from app import tasks as tasks_module
    from app.celery_app import celery_app

    revoked = []
    monkeypatch.setattr(celery_app.control, "revoke", lambda task_id, **kw: revoked.append(task_id))

    counter = {"n": 0}

    class FakeResult:
        def __init__(self, id):
            self.id = id

    def fake_apply_async(*, args, eta):
        counter["n"] += 1
        return FakeResult(f"task-{counter['n']}")

    monkeypatch.setattr(tasks_module.unlock_scenario_instance, "apply_async", fake_apply_async)
    monkeypatch.setattr(tasks_module.close_scenario_instance, "apply_async", fake_apply_async)
    monkeypatch.setattr(tasks_module.apply_scenario_pivot, "apply_async", fake_apply_async)
    # Exercise the real (non-eager) revoke path — apply_async is faked above
    # so this doesn't need a live broker.
    celery_app.conf.task_always_eager = False

    instance = _create_instance(client)
    now = datetime.now(timezone.utc)

    first = client.post(
        f"/scenario-instances/{instance['id']}/schedule",
        json={
            "start_at": (now + timedelta(hours=1)).isoformat(),
            "end_at": (now + timedelta(hours=2)).isoformat(),
        },
    )
    assert first.status_code == 200
    assert revoked == []

    second = client.post(
        f"/scenario-instances/{instance['id']}/schedule",
        json={
            "start_at": (now + timedelta(hours=3)).isoformat(),
            "end_at": (now + timedelta(hours=4)).isoformat(),
        },
    )
    assert second.status_code == 200
    assert set(revoked) == {"task-1", "task-2"}


def test_schedule_not_found(client):
    now = datetime.now(timezone.utc)

    response = client.post(
        f"/scenario-instances/{uuid.uuid4()}/schedule",
        json={
            "start_at": now.isoformat(),
            "end_at": (now + timedelta(hours=1)).isoformat(),
        },
    )

    assert response.status_code == 404
