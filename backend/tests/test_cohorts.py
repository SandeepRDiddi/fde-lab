import uuid

import httpx

from app.routers import cohorts as cohorts_router


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


def test_provision_cohort_calls_k8s_provisioner(client, monkeypatch):
    cohort_id = uuid.uuid4()
    captured = {}

    def fake_post(url, timeout=None):
        captured["url"] = url
        return _FakeResponse(200, {"cohort_id": str(cohort_id), "namespace": f"cohort-{cohort_id}"})

    monkeypatch.setattr(cohorts_router.httpx, "post", fake_post)

    response = client.post(f"/cohorts/{cohort_id}/provision")

    assert response.status_code == 200
    assert response.json() == {"cohort_id": str(cohort_id), "namespace": f"cohort-{cohort_id}"}
    assert str(cohort_id) in captured["url"]


def test_provision_cohort_returns_502_when_provisioner_unreachable(client, monkeypatch):
    def fake_post(url, timeout=None):
        raise httpx.RequestError("connection refused")

    monkeypatch.setattr(cohorts_router.httpx, "post", fake_post)

    response = client.post(f"/cohorts/{uuid.uuid4()}/provision")

    assert response.status_code == 502
    assert "unreachable" in response.json()["detail"]


def test_provision_cohort_returns_502_on_provisioner_error(client, monkeypatch):
    def fake_post(url, timeout=None):
        return _FakeResponse(502, text="helm upgrade --install failed")

    monkeypatch.setattr(cohorts_router.httpx, "post", fake_post)

    response = client.post(f"/cohorts/{uuid.uuid4()}/provision")

    assert response.status_code == 502
    assert "helm upgrade" in response.json()["detail"]
