from fastapi.testclient import TestClient

from app import main
from app.provision import ProvisioningError


def test_health():
    client = TestClient(main.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_provision_returns_namespace(monkeypatch):
    monkeypatch.setattr(main, "provision_cohort", lambda cohort_id, values_file=None: "cohort-acme-cs101")

    client = TestClient(main.app)
    response = client.post("/provision/acme-cs101")

    assert response.status_code == 200
    assert response.json() == {"cohort_id": "acme-cs101", "namespace": "cohort-acme-cs101"}


def test_provision_returns_502_on_helm_failure(monkeypatch):
    def failing(cohort_id, values_file=None):
        raise ProvisioningError("helm upgrade --install failed")

    monkeypatch.setattr(main, "provision_cohort", failing)

    client = TestClient(main.app)
    response = client.post("/provision/acme-cs101")

    assert response.status_code == 502
    assert "helm upgrade" in response.json()["detail"]
