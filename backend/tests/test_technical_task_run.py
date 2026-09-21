import io
import json
import uuid


class _FakeBody:
    def __init__(self, data: bytes):
        self._buf = io.BytesIO(data)

    def read(self):
        return self._buf.read()


class _FakeS3Client:
    def __init__(self, objects: dict[str, bytes]):
        self._objects = objects

    def get_object(self, *, Bucket, Key):
        return {"Body": _FakeBody(self._objects[f"{Bucket}/{Key}"])}


def _create_instance(client, config=None):
    payload = {
        "cohort_id": str(uuid.uuid4()),
        "student_id": str(uuid.uuid4()),
        "config": config or {},
    }
    return client.post("/scenario-instances", json=payload).json()


def _seed_dataset(client, monkeypatch, instance_id, rows):
    body = "\n".join(json.dumps(row) for row in rows).encode("utf-8")
    fake_client = _FakeS3Client({"fde-lab-datasets/orders.ndjson": body})
    monkeypatch.setattr("app.dataset_store.boto3.client", lambda *a, **kw: fake_client)
    client.patch(
        f"/scenario-instances/{instance_id}/dataset",
        json={"dataset_location": "s3://fde-lab-datasets/orders.ndjson"},
    )


def test_run_query_returns_actual_result_not_a_grade(client, monkeypatch):
    instance = _create_instance(
        client,
        config={
            "technical_task": {
                "task_type": "sql_query",
                "table_name": "orders",
                "reference_query": "SELECT DISTINCT order_id FROM orders",
            }
        },
    )
    _seed_dataset(
        client, monkeypatch, instance["id"],
        [{"order_id": "ORD-1"}, {"order_id": "ORD-1"}, {"order_id": "ORD-2"}],
    )

    response = client.post(
        f"/scenario-instances/{instance['id']}/technical-task/run", json={"content": "SELECT * FROM orders"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["row_count"] == 3
    assert body["columns"] == ["order_id"]

    # Running a query -- even a "wrong" one relative to reference_query --
    # doesn't create a submission or fail anything; it's just a preview.
    assert client.get(f"/scenario-instances/{instance['id']}/submissions").json() == []


def test_run_query_without_technical_task_404s(client):
    instance = _create_instance(client)

    response = client.post(
        f"/scenario-instances/{instance['id']}/technical-task/run", json={"content": "SELECT 1"}
    )

    assert response.status_code == 404


def test_run_query_rejects_non_select_as_422(client, monkeypatch):
    instance = _create_instance(
        client,
        config={"technical_task": {"task_type": "sql_query", "table_name": "orders", "reference_query": "SELECT 1"}},
    )
    _seed_dataset(client, monkeypatch, instance["id"], [{"order_id": "ORD-1"}])

    response = client.post(
        f"/scenario-instances/{instance['id']}/technical-task/run", json={"content": "DELETE FROM orders"}
    )

    assert response.status_code == 422


def test_run_query_instance_not_found_404s(client):
    response = client.post(
        f"/scenario-instances/{uuid.uuid4()}/technical-task/run", json={"content": "SELECT 1"}
    )
    assert response.status_code == 404


def test_run_python_script_returns_actual_result_not_a_grade(client, monkeypatch):
    instance = _create_instance(
        client,
        config={
            "technical_task": {
                "task_type": "python_script",
                "input_filename": "orders.json",
                "output_filename": "cleaned.json",
                "reference_solution": "import json\nwith open('orders.json') as f: rows = json.load(f)\nwith open('cleaned.json', 'w') as f: json.dump(rows, f)",
            }
        },
    )
    _seed_dataset(client, monkeypatch, instance["id"], [{"order_id": "ORD-1"}, {"order_id": "ORD-2"}])

    script = (
        "import json\n"
        "with open('orders.json') as f:\n    rows = json.load(f)\n"
        "with open('cleaned.json', 'w') as f:\n    json.dump(rows, f)\n"
    )
    response = client.post(
        f"/scenario-instances/{instance['id']}/technical-task/run", json={"content": script}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["row_count"] == 2
    assert client.get(f"/scenario-instances/{instance['id']}/submissions").json() == []


def test_run_python_script_with_syntax_error_returns_422(client, monkeypatch):
    instance = _create_instance(
        client,
        config={
            "technical_task": {
                "task_type": "python_script",
                "input_filename": "orders.json",
                "output_filename": "cleaned.json",
                "reference_solution": "import json\nwith open('cleaned.json', 'w') as f: json.dump([], f)",
            }
        },
    )
    _seed_dataset(client, monkeypatch, instance["id"], [{"order_id": "ORD-1"}])

    response = client.post(
        f"/scenario-instances/{instance['id']}/technical-task/run",
        json={"content": "this is not python("},
    )

    assert response.status_code == 422
