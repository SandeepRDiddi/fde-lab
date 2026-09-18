import uuid

import httpx


def _create_instance(client, config=None):
    payload = {
        "cohort_id": str(uuid.uuid4()),
        "student_id": str(uuid.uuid4()),
        "config": config or {},
    }
    return client.post("/scenario-instances", json=payload).json()


def test_no_legacy_system_configured_404s(client):
    instance = _create_instance(client)

    response = client.get(f"/scenario-instances/{instance['id']}/legacy-system")

    assert response.status_code == 404


def test_instance_not_found_404s(client):
    response = client.get(f"/scenario-instances/{uuid.uuid4()}/legacy-system")
    assert response.status_code == 404


def test_proxies_successful_response(client, monkeypatch):
    instance = _create_instance(
        client, config={"legacy_system": {"scenario_id": "acme-crm", "path": "/accounts"}}
    )
    captured = {}

    def fake_get(url, headers=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        return httpx.Response(200, json={"account_id": 1042, "active": True})

    monkeypatch.setattr("app.routers.legacy_system.httpx.get", fake_get)

    response = client.get(f"/scenario-instances/{instance['id']}/legacy-system")

    assert response.status_code == 200
    assert response.json() == {"account_id": 1042, "active": True}
    assert captured["url"].endswith("/acme-crm/accounts")


def test_proxies_401_body_unchanged(client, monkeypatch):
    """The mock's deliberately unhelpful 401 must reach the student as-is,
    not get reinterpreted or swallowed by the proxy."""
    instance = _create_instance(
        client,
        config={"legacy_system": {"scenario_id": "acme-crm", "path": "/accounts", "auth_header_name": "X-Legacy-Auth"}},
    )

    def fake_get(url, headers=None, timeout=None):
        return httpx.Response(401, json={"error": "ERR-4471", "message": "request could not be completed"})

    monkeypatch.setattr("app.routers.legacy_system.httpx.get", fake_get)

    response = client.get(f"/scenario-instances/{instance['id']}/legacy-system")

    assert response.status_code == 401
    assert response.json() == {"error": "ERR-4471", "message": "request could not be completed"}


def test_forwards_supplied_auth_value_under_configured_header_name(client, monkeypatch):
    instance = _create_instance(
        client,
        config={"legacy_system": {"scenario_id": "acme-crm", "path": "/accounts", "auth_header_name": "X-Legacy-Auth"}},
    )
    captured = {}

    def fake_get(url, headers=None, timeout=None):
        captured["headers"] = headers
        return httpx.Response(200, json={"account_id": 1042})

    monkeypatch.setattr("app.routers.legacy_system.httpx.get", fake_get)

    response = client.get(
        f"/scenario-instances/{instance['id']}/legacy-system", headers={"X-Legacy-Auth": "legacy-demo-token"}
    )

    assert response.status_code == 200
    assert captured["headers"] == {"X-Legacy-Auth": "legacy-demo-token"}


def test_unreachable_legacy_system_returns_502(client, monkeypatch):
    instance = _create_instance(
        client, config={"legacy_system": {"scenario_id": "acme-crm", "path": "/accounts"}}
    )

    def fake_get(url, headers=None, timeout=None):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr("app.routers.legacy_system.httpx.get", fake_get)

    response = client.get(f"/scenario-instances/{instance['id']}/legacy-system")

    assert response.status_code == 502
