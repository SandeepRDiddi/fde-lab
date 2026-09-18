import uuid
from datetime import datetime, timedelta, timezone


def _create_instance(client, config=None):
    payload = {
        "cohort_id": str(uuid.uuid4()),
        "student_id": str(uuid.uuid4()),
        "config": config or {},
    }
    return client.post("/scenario-instances", json=payload).json()


def test_create_submission_rejects_content_failing_compliance_checklist(client):
    instance = _create_instance(
        client,
        config={
            "compliance_checklist": [
                {"id": "len", "description": "at least 10 chars", "check": "min_length", "value": 10}
            ]
        },
    )

    response = client.post(f"/scenario-instances/{instance['id']}/submissions", json={"content": "short"})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["failures"] == [{"rule_id": "len", "description": "at least 10 chars"}]

    # Rejected submission is never persisted.
    listed = client.get(f"/scenario-instances/{instance['id']}/submissions").json()
    assert listed == []


def test_create_submission_accepts_content_passing_compliance_checklist(client):
    instance = _create_instance(
        client,
        config={
            "compliance_checklist": [
                {"id": "len", "description": "at least 10 chars", "check": "min_length", "value": 10}
            ]
        },
    )

    response = client.post(
        f"/scenario-instances/{instance['id']}/submissions", json={"content": "a sufficiently long report"}
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending_review"


def test_create_submission_moves_to_pending_review(client):
    instance = _create_instance(client)

    response = client.post(f"/scenario-instances/{instance['id']}/submissions", json={"content": "my report"})

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending_review"
    assert body["scenario_instance_id"] == instance["id"]
    assert body["decided_at"] is None


def test_submission_stays_pending_without_review_delay_until_manual_decision(client):
    instance = _create_instance(client)
    submission = client.post(
        f"/scenario-instances/{instance['id']}/submissions", json={"content": "my report"}
    ).json()
    assert submission["status"] == "pending_review"
    assert submission["review_deadline_at"] is None

    response = client.patch(
        f"/scenario-instances/{instance['id']}/submissions/{submission['id']}/decision",
        json={"decision": "approved"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["decided_at"] is not None
    assert body["notified_at"] is not None

    final_instance = client.get(f"/scenario-instances/{instance['id']}").json()
    assert final_instance["approval_outcome"] == "approved"
    assert final_instance["approval_decided_at"] is not None


def test_submission_with_review_delay_auto_decides(client):
    # Celery runs eagerly in tests, so the auto-decide job fires synchronously
    # as soon as it's enqueued, same as the unlock/close jobs in test_scheduler.
    instance = _create_instance(
        client, config={"approval_workflow": {"review_delay_seconds": 60, "auto_decision": "rejected"}}
    )

    response = client.post(f"/scenario-instances/{instance['id']}/submissions", json={"content": "my report"})

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "rejected"
    assert body["auto_decision"] == "rejected"
    assert body["decided_at"] is not None

    final_instance = client.get(f"/scenario-instances/{instance['id']}").json()
    assert final_instance["approval_outcome"] == "rejected"


def test_create_submission_rejects_partial_approval_config(client):
    instance = _create_instance(client, config={"approval_workflow": {"review_delay_seconds": 60}})

    response = client.post(f"/scenario-instances/{instance['id']}/submissions", json={"content": "x"})

    assert response.status_code == 422


def test_create_submission_rejects_non_positive_review_delay(client):
    instance = _create_instance(
        client, config={"approval_workflow": {"review_delay_seconds": 0, "auto_decision": "approved"}}
    )

    response = client.post(f"/scenario-instances/{instance['id']}/submissions", json={"content": "x"})

    assert response.status_code == 422


def test_create_submission_rejects_invalid_auto_decision(client):
    instance = _create_instance(
        client, config={"approval_workflow": {"review_delay_seconds": 60, "auto_decision": "pending_review"}}
    )

    response = client.post(f"/scenario-instances/{instance['id']}/submissions", json={"content": "x"})

    assert response.status_code == 422


def test_create_submission_on_closed_instance_conflicts(client):
    instance = _create_instance(client)
    now = datetime.now(timezone.utc)
    # Eager celery closes the instance synchronously as soon as it's scheduled.
    client.post(
        f"/scenario-instances/{instance['id']}/schedule",
        json={"start_at": (now + timedelta(seconds=1)).isoformat(), "end_at": (now + timedelta(seconds=2)).isoformat()},
    )

    response = client.post(f"/scenario-instances/{instance['id']}/submissions", json={"content": "x"})

    assert response.status_code == 409


def test_decision_on_already_decided_submission_conflicts(client):
    instance = _create_instance(client)
    submission = client.post(
        f"/scenario-instances/{instance['id']}/submissions", json={"content": "x"}
    ).json()
    client.patch(
        f"/scenario-instances/{instance['id']}/submissions/{submission['id']}/decision",
        json={"decision": "approved"},
    )

    response = client.patch(
        f"/scenario-instances/{instance['id']}/submissions/{submission['id']}/decision",
        json={"decision": "rejected"},
    )

    assert response.status_code == 409


def test_list_submissions_returns_instance_submissions(client):
    instance = _create_instance(client)
    created = client.post(f"/scenario-instances/{instance['id']}/submissions", json={"content": "my report"}).json()

    response = client.get(f"/scenario-instances/{instance['id']}/submissions")

    assert response.status_code == 200
    body = response.json()
    assert [submission["id"] for submission in body] == [created["id"]]


def test_list_submissions_instance_not_found(client):
    response = client.get(f"/scenario-instances/{uuid.uuid4()}/submissions")
    assert response.status_code == 404


def test_create_submission_instance_not_found(client):
    response = client.post(f"/scenario-instances/{uuid.uuid4()}/submissions", json={"content": "x"})
    assert response.status_code == 404


def test_get_submission_not_found(client):
    instance = _create_instance(client)
    response = client.get(f"/scenario-instances/{instance['id']}/submissions/{uuid.uuid4()}")
    assert response.status_code == 404


def test_manual_decision_revokes_pending_auto_decide_job(client, monkeypatch):
    from app import tasks as tasks_module
    from app.celery_app import celery_app

    revoked = []
    monkeypatch.setattr(celery_app.control, "revoke", lambda task_id, **kw: revoked.append(task_id))

    class FakeResult:
        def __init__(self, id):
            self.id = id

    monkeypatch.setattr(
        tasks_module.auto_decide_submission, "apply_async", lambda *, args, eta: FakeResult("auto-decide-1")
    )
    # Exercise the real (non-eager) revoke path — apply_async is faked above
    # so this doesn't need a live broker.
    celery_app.conf.task_always_eager = False

    instance = _create_instance(
        client, config={"approval_workflow": {"review_delay_seconds": 3600, "auto_decision": "approved"}}
    )
    submission = client.post(
        f"/scenario-instances/{instance['id']}/submissions", json={"content": "x"}
    ).json()
    assert submission["status"] == "pending_review"

    response = client.patch(
        f"/scenario-instances/{instance['id']}/submissions/{submission['id']}/decision",
        json={"decision": "rejected"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert revoked == ["auto-decide-1"]
