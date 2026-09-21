"""Reads a scenario instance's synthetic dataset (data-gen's NDJSON output
in S3-compatible object storage) back out. Shared by app/grading.py (grades
a query against it) and the dataset-preview endpoint (lets a student browse
it before writing anything) -- both need the same rows, fetched the same
way, from the same service, so this lives in one place rather than being
copied twice within backend/.
"""
from __future__ import annotations

import json
from typing import Any

import boto3

from app.config import settings


class DatasetStoreError(Exception):
    """Dataset location missing/malformed, or object storage unreachable."""


def fetch_dataset_rows(dataset_location: str) -> list[dict]:
    if not dataset_location.startswith("s3://"):
        raise DatasetStoreError(f"Unsupported dataset location: {dataset_location!r}")
    _, _, rest = dataset_location.partition("s3://")
    bucket, _, key = rest.partition("/")

    client = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    )
    try:
        body = client.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
    except Exception as exc:  # noqa: BLE001 -- boto3 raises its own botocore exception types
        raise DatasetStoreError(f"Could not fetch dataset {dataset_location!r}: {exc}") from exc

    try:
        return [json.loads(line) for line in body.splitlines() if line.strip()]
    except json.JSONDecodeError as exc:
        raise DatasetStoreError(f"Dataset {dataset_location!r} is not valid NDJSON: {exc}") from exc


def preview_dataset(dataset_location: str, limit: int = 20) -> dict[str, Any]:
    """FDE-015: lets a student see the actual shape of the data before
    writing a query against it -- real FDE work starts with looking at what
    you're dealing with, not guessing at column names blind. Column order
    is the union across all rows (not just the first), since messiness can
    give later rows extra/renamed columns the first row doesn't have."""
    rows = fetch_dataset_rows(dataset_location)
    columns: list[str] = []
    for row in rows:
        for col in row:
            if col not in columns:
                columns.append(col)
    return {"columns": columns, "rows": rows[:limit], "total_rows": len(rows)}
