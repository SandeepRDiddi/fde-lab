import json
import uuid

import httpx

from generator.run import generate_for_scenario_instance
from generator.storage import S3DatasetStore


def _backend_app(instance, recorded_patches):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == f"/scenario-instances/{instance['id']}":
            return httpx.Response(200, json=instance)
        if request.method == "PATCH" and request.url.path == f"/scenario-instances/{instance['id']}/dataset":
            payload = json.loads(request.content)
            recorded_patches.append(payload)
            instance["dataset_location"] = payload["dataset_location"]
            return httpx.Response(200, json=instance)
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

    return handler


def test_generate_for_scenario_instance_records_location(monkeypatch, fake_s3_client):
    instance_id = str(uuid.uuid4())
    cohort_id = str(uuid.uuid4())
    instance = {
        "id": instance_id,
        "cohort_id": cohort_id,
        "student_id": str(uuid.uuid4()),
        "status": "not_started",
        "config": {"data_gen": {"domain": "hr_employees", "row_count": 30, "messiness": "low"}},
        "dataset_location": None,
        "start_at": None,
        "end_at": None,
        "created_at": "2026-09-17T00:00:00Z",
    }
    recorded_patches = []
    transport = httpx.MockTransport(_backend_app(instance, recorded_patches))

    monkeypatch.setattr(httpx, "Client", lambda base_url: httpx.Client(base_url=base_url, transport=transport))

    store = S3DatasetStore(client=fake_s3_client, bucket="test-bucket")

    location = generate_for_scenario_instance(
        uuid.UUID(instance_id), backend_base_url="http://backend.test", store=store
    )

    assert location.startswith(f"s3://test-bucket/datasets/{cohort_id}/{instance_id}/")
    assert location.endswith(".jsonl")
    assert recorded_patches == [{"dataset_location": location}]

    (bucket, key), obj = next(iter(fake_s3_client.objects.items()))
    rows = [json.loads(line) for line in obj["Body"].decode("utf-8").splitlines()]
    assert len(rows) == 30


def test_two_runs_for_the_same_instance_never_collide(monkeypatch, fake_s3_client):
    instance_id = str(uuid.uuid4())
    cohort_id = str(uuid.uuid4())
    instance = {
        "id": instance_id,
        "cohort_id": cohort_id,
        "student_id": str(uuid.uuid4()),
        "status": "not_started",
        "config": {"data_gen": {"domain": "ecommerce_orders", "row_count": 10, "messiness": "medium"}},
        "dataset_location": None,
        "start_at": None,
        "end_at": None,
        "created_at": "2026-09-17T00:00:00Z",
    }
    recorded_patches = []
    transport = httpx.MockTransport(_backend_app(instance, recorded_patches))
    monkeypatch.setattr(httpx, "Client", lambda base_url: httpx.Client(base_url=base_url, transport=transport))

    store = S3DatasetStore(client=fake_s3_client, bucket="test-bucket")

    first_location = generate_for_scenario_instance(
        uuid.UUID(instance_id), backend_base_url="http://backend.test", store=store
    )
    second_location = generate_for_scenario_instance(
        uuid.UUID(instance_id), backend_base_url="http://backend.test", store=store
    )

    assert first_location != second_location
    assert len(fake_s3_client.objects) == 2
