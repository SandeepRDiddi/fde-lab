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
    assert body["dataset_location"] is None
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


def test_set_scenario_instance_dataset_records_location(client):
    create_payload = {
        "cohort_id": str(uuid.uuid4()),
        "student_id": str(uuid.uuid4()),
        "config": {"data_gen": {"domain": "ecommerce_orders", "row_count": 100, "messiness": "medium"}},
    }
    created = client.post("/scenario-instances", json=create_payload).json()

    response = client.patch(
        f"/scenario-instances/{created['id']}/dataset",
        json={"dataset_location": "s3://fde-lab-datasets/datasets/abc/def/xyz.jsonl"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["dataset_location"] == "s3://fde-lab-datasets/datasets/abc/def/xyz.jsonl"

    refetched = client.get(f"/scenario-instances/{created['id']}").json()
    assert refetched["dataset_location"] == "s3://fde-lab-datasets/datasets/abc/def/xyz.jsonl"


def test_set_scenario_instance_dataset_not_found(client):
    response = client.patch(
        f"/scenario-instances/{uuid.uuid4()}/dataset",
        json={"dataset_location": "s3://fde-lab-datasets/datasets/abc/def/xyz.jsonl"},
    )
    assert response.status_code == 404


def test_list_scenario_instances_filters_by_cohort(client):
    cohort_id = str(uuid.uuid4())
    matching = client.post(
        "/scenario-instances",
        json={"cohort_id": cohort_id, "student_id": str(uuid.uuid4()), "config": {}},
    ).json()
    client.post(
        "/scenario-instances",
        json={"cohort_id": str(uuid.uuid4()), "student_id": str(uuid.uuid4()), "config": {}},
    )

    response = client.get("/scenario-instances", params={"cohort_id": cohort_id})

    assert response.status_code == 200
    body = response.json()
    assert [instance["id"] for instance in body] == [matching["id"]]


def test_list_scenario_instances_empty_cohort_returns_empty_list(client):
    response = client.get("/scenario-instances", params={"cohort_id": str(uuid.uuid4())})
    assert response.status_code == 200
    assert response.json() == []
