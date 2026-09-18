from fastapi import FastAPI, HTTPException

from .config import settings
from .provision import ProvisioningError, provision_cohort

app = FastAPI(title="FDE Lab — Kubernetes cohort provisioner")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/provision/{cohort_id}")
def provision(cohort_id: str) -> dict:
    """AC2: creates (or re-applies) the isolated namespace + full stack for
    one cohort. The only intended caller is the backend's
    `POST /cohorts/{cohort_id}/provision` (instructor-action trigger); see
    infra/k8s/README.md for why the LTI-launch trigger isn't wired to call
    this yet.

    This is the one component in the platform holding cluster-level
    namespace-create credentials, deliberately kept separate from the
    student/instructor-facing backend API (see infra/k8s/README.md's RBAC
    note) -- so it's a small standalone service rather than a route folded
    into backend/, the same shape this repo already uses for lti-service
    and the enterprise mocks.
    """
    try:
        namespace = provision_cohort(cohort_id, values_file=settings.chart_values_file)
    except ProvisioningError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"cohort_id": cohort_id, "namespace": namespace}
