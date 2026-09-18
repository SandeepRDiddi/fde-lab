import uuid

import httpx
from fastapi import APIRouter, HTTPException

from app.config import settings

router = APIRouter(prefix="/cohorts", tags=["cohorts"])


@router.post("/{cohort_id}/provision")
def provision_cohort(cohort_id: uuid.UUID) -> dict:
    """FDE-012 AC2, instructor-action trigger: asks the platform-level
    k8s-provisioner service to create (or re-apply) this cohort's isolated
    Kubernetes namespace. Deliberately not implemented in-process here --
    a public, student/instructor-facing API pod holding the cluster
    credentials needed to create namespaces cluster-wide would be a real
    privilege-escalation smell, so that capability lives in a separate,
    narrowly-scoped service instead (see infra/k8s/provisioner/ and
    infra/k8s/README.md).

    No `cohorts` table backs this -- cohort_id is an opaque identifier
    here, same as it already is on ScenarioInstance (app/models.py), and
    namespace existence in the cluster is the source of truth for "has
    this cohort been provisioned," not a Postgres row.
    """
    try:
        response = httpx.post(
            f"{settings.k8s_provisioner_url}/provision/{cohort_id}",
            # The provisioner's own `helm upgrade --install --wait` can run
            # up to its own 5-minute timeout; give this call enough room to
            # not time out first.
            timeout=310.0,
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"k8s provisioner unreachable: {exc}") from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"k8s provisioner returned {response.status_code}: {response.text}",
        )

    return response.json()
