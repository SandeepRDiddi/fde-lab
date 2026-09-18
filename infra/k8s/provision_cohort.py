#!/usr/bin/env python3
"""Direct CLI entry point for cohort namespace provisioning (FDE-012 AC2),
for ops/CI use straight out of a repo checkout -- no cluster network hop
to the provisioner service needed. Shares its logic with
infra/k8s/provisioner/app/provision.py (imported below), which is what the
backend's `POST /cohorts/{cohort_id}/provision` instructor-action endpoint
calls over HTTP instead.

Usage:
    python infra/k8s/provision_cohort.py <cohort-id> [--values values-prod.yaml] [--kube-context prod-cluster]

Idempotent -- see provision_cohort()'s docstring in provisioner/app/provision.py.
Requires `helm` (and a working kubeconfig) on PATH; this script does not
install either.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "provisioner"))

from app.provision import ProvisioningError, provision_cohort  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cohort_id")
    parser.add_argument("--values", help="extra Helm values file, applied on top of chart/values.yaml")
    parser.add_argument("--kube-context", help="kubectl context to target (defaults to the current one)")
    args = parser.parse_args()

    try:
        namespace = provision_cohort(
            args.cohort_id,
            values_file=args.values,
            kube_context=args.kube_context,
        )
    except ProvisioningError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Provisioned namespace {namespace!r} for cohort {args.cohort_id!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
