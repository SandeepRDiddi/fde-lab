import io
import json
import uuid

from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate


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


_ROWS = [
    {"order_id": "ORD-1", "customer_email": "a@example.com", "quantity": 1},
    {"order_id": "ORD-2", "customer_email": None, "quantity": 3},
    {"order_id": "ORD-3", "customer_email": None, "quantity": 2},
    {"order_id": "ORD-4", "customer_email": "d@example.com", "quantity": 5},
]
_DATASET_LOCATION = "s3://fde-lab-datasets/instances/stage3/orders.ndjson"


def test_stage_3_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[3])


def test_stage_3_has_no_compliance_checklist():
    """FDE-014's documented constraint: a technical_task's submission
    content IS the query, so a prose compliance_checklist in the same
    field could never be jointly satisfiable."""
    assert "compliance_checklist" not in GLOBAL_RETAIL_STAGES[3]


def test_stage_3_data_gen_uses_high_messiness():
    data_gen = GLOBAL_RETAIL_STAGES[3]["data_gen"]
    assert data_gen["domain"] == "ecommerce_orders"
    assert data_gen["messiness"] == "high"


def test_stage_3_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[3]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def _create_stage3_instance(client, monkeypatch, dataset_location=_DATASET_LOCATION):
    payload = {
        "cohort_id": str(uuid.uuid4()),
        "student_id": str(uuid.uuid4()),
        "config": GLOBAL_RETAIL_STAGES[3],
    }
    instance = client.post("/scenario-instances", json=payload).json()
    client.patch(f"/scenario-instances/{instance['id']}/dataset", json={"dataset_location": dataset_location})

    body = "\n".join(json.dumps(row) for row in _ROWS).encode("utf-8")
    fake_client = _FakeS3Client({"fde-lab-datasets/instances/stage3/orders.ndjson": body})
    monkeypatch.setattr("app.dataset_store.boto3.client", lambda *a, **kw: fake_client)
    return instance["id"]


def test_correct_profiling_query_passes_grading(client, monkeypatch):
    instance_id = _create_stage3_instance(client, monkeypatch)

    response = client.post(
        f"/scenario-instances/{instance_id}/submissions",
        json={"content": "SELECT COUNT(*) FROM orders WHERE customer_email IS NULL"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["grading_result"]["passed"] is True


def test_incorrect_profiling_query_fails_grading(client, monkeypatch):
    instance_id = _create_stage3_instance(client, monkeypatch)

    response = client.post(
        f"/scenario-instances/{instance_id}/submissions",
        json={"content": "SELECT COUNT(*) FROM orders"},
    )
    assert response.status_code == 422
