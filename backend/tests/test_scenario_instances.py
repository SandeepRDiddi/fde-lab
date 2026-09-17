import uuid


def test_create_scenario_instance(client):
    payload = {
        "cohort_id": str(uuid.uuid4()),
        "student_id": str(uuid.uuid4()),
        "config": {"persona": "cfo-persona-v1", "documents": ["q3-report.pdf"]},
    }

    response = client.post("/scenario-instances", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["cohort_id"] == payload["cohort_id"]
    assert body["student_id"] == payload["student_id"]
    assert body["config"] == payload["config"]
    assert body["status"] == "not_started"
    assert body["start_at"] is None
    assert body["end_at"] is None
    assert "id" in body


def test_get_scenario_instance_returns_status_and_timestamps(client):
    create_payload = {
        "cohort_id": str(uuid.uuid4()),
        "student_id": str(uuid.uuid4()),
        "config": {},
    }
    created = client.post("/scenario-instances", json=create_payload).json()

    response = client.get(f"/scenario-instances/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["status"] == "not_started"
    assert "start_at" in body
    assert "end_at" in body


def test_get_scenario_instance_not_found(client):
    response = client.get(f"/scenario-instances/{uuid.uuid4()}")
    assert response.status_code == 404
