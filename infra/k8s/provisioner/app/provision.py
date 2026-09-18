"""Core cohort-namespace provisioning logic (FDE-012 AC2): shells out to
`helm upgrade --install` against the chart in infra/k8s/chart/ for one
cohort. Kept dependency-light (stdlib + the chart itself) so the same
logic backs both this service's HTTP endpoint and a direct CLI invocation
(infra/k8s/provision_cohort.py) without either needing the other's
runtime.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

# Two different layouts resolve to the same chart, depending on whether
# this runs from a container image (Dockerfile COPYs chart to ./chart
# alongside ./app) or straight out of a repo checkout (infra/k8s/chart/,
# a sibling of infra/k8s/provisioner/).
_CANDIDATE_CHART_DIRS = [
    Path(__file__).resolve().parent.parent / "chart",
    Path(__file__).resolve().parent.parent.parent / "chart",
]


def _default_chart_dir() -> Path:
    for candidate in _CANDIDATE_CHART_DIRS:
        if (candidate / "Chart.yaml").exists():
            return candidate
    return _CANDIDATE_CHART_DIRS[0]


class ProvisioningError(RuntimeError):
    pass


def namespace_for(cohort_id: str) -> str:
    # Truncate before the final strip -- cutting at 53 chars can land right
    # after a dash, and a namespace name can't end in one.
    slug = re.sub(r"[^a-z0-9-]+", "-", cohort_id.strip().lower()).strip("-")[:53].strip("-")
    if not slug:
        raise ProvisioningError(f"cohort_id {cohort_id!r} has no valid namespace characters")
    return f"cohort-{slug}"


def provision_cohort(
    cohort_id: str,
    *,
    values_file: str | None = None,
    chart_dir: Path | None = None,
    kube_context: str | None = None,
    runner=subprocess.run,
) -> str:
    """Idempotent: `helm upgrade --install` rolls an existing release
    forward rather than erroring, so calling this more than once for the
    same cohort_id (instructor retries the same action, both an eventual
    LTI-launch trigger and an instructor-console trigger fire for the same
    cohort, etc.) is safe rather than something callers need to guard
    against themselves."""
    namespace = namespace_for(cohort_id)
    cmd = [
        "helm", "upgrade", namespace, str(chart_dir or _default_chart_dir()),
        "--install",
        "--namespace", namespace,
        "--set", f"cohortId={cohort_id}",
        "--wait",
        "--timeout", "5m",
    ]
    if values_file:
        cmd += ["-f", values_file]
    if kube_context:
        cmd += ["--kube-context", kube_context]

    result = runner(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise ProvisioningError(
            f"helm upgrade --install failed for cohort {cohort_id!r} "
            f"(namespace {namespace}): {result.stderr.strip()}"
        )
    return namespace
