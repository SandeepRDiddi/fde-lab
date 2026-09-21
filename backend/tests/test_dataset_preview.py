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


def test_dataset_preview_returns_columns_and_rows(client, monkeypatch):
    rows = [
        {"order_id": "ORD-1", "quantity": 1},
        {"order_id": "ORD-2", "quantity": 3, "note": "drifted extra column"},
    ]
    body = "\n".join(json.dumps(row) for row in rows).encode("utf-8")
    fake_client = _FakeS3Client({"fde-lab-datasets/orders.ndjson": body})
    monkeypatch.setattr("app.dataset_store.boto3.client", lambda *a, **kw: fake_client)

    instance = _create_instance(client)
    client.patch(
        f"/scenario-instances/{instance['id']}/dataset",
        json={"dataset_location": "s3://fde-lab-datasets/orders.ndjson"},
    )

    response = client.get(f"/scenario-instances/{instance['id']}/dataset-preview")

    assert response.status_code == 200
    body = response.json()
    assert body["columns"] == ["order_id", "quantity", "note"]
    assert body["total_rows"] == 2
    assert len(body["rows"]) == 2


def test_dataset_preview_respects_limit(client, monkeypatch):
    rows = [{"order_id": f"ORD-{i}"} for i in range(10)]
    body = "\n".join(json.dumps(row) for row in rows).encode("utf-8")
    fake_client = _FakeS3Client({"fde-lab-datasets/orders.ndjson": body})
    monkeypatch.setattr("app.dataset_store.boto3.client", lambda *a, **kw: fake_client)

    instance = _create_instance(client)
    client.patch(
        f"/scenario-instances/{instance['id']}/dataset",
        json={"dataset_location": "s3://fde-lab-datasets/orders.ndjson"},
    )

    response = client.get(f"/scenario-instances/{instance['id']}/dataset-preview?limit=3")

    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 10
    assert len(body["rows"]) == 3


def test_dataset_preview_without_dataset_404s(client):
    instance = _create_instance(client)

    response = client.get(f"/scenario-instances/{instance['id']}/dataset-preview")

    assert response.status_code == 404


def test_dataset_preview_instance_not_found_404s(client):
    response = client.get(f"/scenario-instances/{uuid.uuid4()}/dataset-preview")
    assert response.status_code == 404
