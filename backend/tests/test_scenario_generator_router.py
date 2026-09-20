import json

from app import scenario_generator as gen
from tests.test_scenario_generator import VALID_DRAFT, _canned


def test_draft_endpoint_returns_generated_config(client, monkeypatch):
    monkeypatch.setattr(gen, "_call_model_backend", _canned(json.dumps(VALID_DRAFT)))

    response = client.post("/scenario-generator/draft", json={"requirement": "orders keep duplicating"})

    assert response.status_code == 200
    body = response.json()
    assert body["technical_task"]["task_type"] == "sql_query"
    assert body["data_gen"]["domain"] == "ecommerce_orders"


def test_draft_endpoint_502_on_generator_failure(client, monkeypatch):
    monkeypatch.setattr(gen, "_call_model_backend", _canned("garbage", "still garbage"))

    response = client.post("/scenario-generator/draft", json={"requirement": "anything"})

    assert response.status_code == 502


def test_generated_config_is_accepted_by_scenario_instance_creation(client, monkeypatch):
    """The whole point of the generator is that its output is a real,
    usable scenario config -- prove it by actually creating an instance
    with it and confirming the rest of the app (compliance/grading) reads
    it correctly."""
    import uuid

    monkeypatch.setattr(gen, "_call_model_backend", _canned(json.dumps(VALID_DRAFT)))
    draft = client.post("/scenario-generator/draft", json={"requirement": "orders keep duplicating"}).json()

    response = client.post(
        "/scenario-instances",
        json={"cohort_id": str(uuid.uuid4()), "student_id": str(uuid.uuid4()), "config": draft},
    )

    assert response.status_code == 201
    assert response.json()["config"]["technical_task"]["reference_query"] == draft["technical_task"]["reference_query"]
