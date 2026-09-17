import json
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.scenario_loader import ScenarioConfig, build_router, load_scenarios


def make_client(scenario: ScenarioConfig) -> TestClient:
    app = FastAPI()
    app.include_router(build_router(scenario))
    return TestClient(app)


def test_schema_drift_across_calls():
    scenario = ScenarioConfig(
        scenario_id="acme-crm",
        path="/accounts",
        responses=[
            {"account_id": 1042, "active": True},
            {"AccountID": "1042", "Active": "Y"},
        ],
    )
    client = make_client(scenario)

    first = client.get("/acme-crm/accounts").json()
    second = client.get("/acme-crm/accounts").json()

    assert first != second
    assert set(first.keys()) != set(second.keys())


def test_missing_auth_header_returns_unhelpful_401():
    scenario = ScenarioConfig(
        scenario_id="acme-crm",
        path="/accounts",
        auth_header="X-Legacy-Auth",
        responses=[{"account_id": 1}],
    )
    client = make_client(scenario)

    response = client.get("/acme-crm/accounts")

    assert response.status_code == 401
    assert "X-Legacy-Auth" not in json.dumps(response.json())


def test_present_auth_header_succeeds():
    scenario = ScenarioConfig(
        scenario_id="acme-crm",
        path="/accounts",
        auth_header="X-Legacy-Auth",
        responses=[{"account_id": 1}],
    )
    client = make_client(scenario)

    response = client.get("/acme-crm/accounts", headers={"X-Legacy-Auth": "token"})

    assert response.status_code == 200


def test_configured_latency_delays_response():
    scenario = ScenarioConfig(
        scenario_id="northwind-erp",
        path="/orders",
        latency_ms=200,
        responses=[{"order_id": 1}],
    )
    client = make_client(scenario)

    start = time.monotonic()
    client.get("/northwind-erp/orders")
    elapsed = time.monotonic() - start

    assert elapsed >= 0.2


def test_empty_responses_list_is_rejected():
    with pytest.raises(ValidationError):
        ScenarioConfig(scenario_id="acme-crm", path="/accounts", responses=[])


def test_load_scenarios_skips_invalid_file_and_loads_the_rest(tmp_path):
    (tmp_path / "broken.json").write_text(json.dumps({"scenario_id": "broken", "path": "/x", "responses": []}))
    (tmp_path / "good.json").write_text(
        json.dumps({"scenario_id": "demo", "path": "/widgets", "responses": [{"id": 1}]})
    )

    scenarios = load_scenarios(tmp_path)

    assert len(scenarios) == 1
    assert scenarios[0].scenario_id == "demo"


def test_load_scenarios_from_directory(tmp_path):
    (tmp_path / "demo.json").write_text(
        json.dumps({"scenario_id": "demo", "path": "/widgets", "responses": [{"id": 1}]})
    )

    scenarios = load_scenarios(tmp_path)

    assert len(scenarios) == 1
    assert scenarios[0].scenario_id == "demo"


def test_app_registers_example_scenarios_and_health():
    from app.main import app

    client = TestClient(app)

    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/acme-crm/accounts", headers={"X-Legacy-Auth": "t"}).status_code == 200
