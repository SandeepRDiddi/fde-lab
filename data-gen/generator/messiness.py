"""Messiness knobs: nulls, duplicates, schema drift, parameterized by level.

Resolves the architecture.md open question "exact parameterization schema for
the data generator" — v1 exposes three named levels (low/medium/high) rather
than raw per-field knobs, since scenario authors think in terms of "how messy"
not individual rates.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class MessinessProfile:
    null_rate: float  # fraction of (row, non-id field) cells blanked out
    duplicate_rate: float  # fraction of rows appended again verbatim
    schema_drift: bool  # whether a subset of rows gets renamed/extra columns


MESSINESS_PROFILES: dict[str, MessinessProfile] = {
    "low": MessinessProfile(null_rate=0.02, duplicate_rate=0.01, schema_drift=False),
    "medium": MessinessProfile(null_rate=0.08, duplicate_rate=0.05, schema_drift=True),
    "high": MessinessProfile(null_rate=0.20, duplicate_rate=0.12, schema_drift=True),
}


def apply_messiness(
    rows: list[dict],
    fieldnames: list[str],
    id_field: str,
    profile: MessinessProfile,
    rng: random.Random,
) -> list[dict]:
    rows = [dict(row) for row in rows]
    _inject_nulls(rows, fieldnames, id_field, profile.null_rate, rng)
    rows = _inject_duplicates(rows, profile.duplicate_rate, rng)
    if profile.schema_drift:
        _inject_schema_drift(rows, fieldnames, id_field, rng)
    return rows


def _inject_nulls(
    rows: list[dict], fieldnames: list[str], id_field: str, null_rate: float, rng: random.Random
) -> None:
    nullable_fields = [f for f in fieldnames if f != id_field]
    for row in rows:
        for field in nullable_fields:
            if rng.random() < null_rate:
                row[field] = None


def _inject_duplicates(rows: list[dict], duplicate_rate: float, rng: random.Random) -> list[dict]:
    duplicate_count = round(len(rows) * duplicate_rate)
    duplicates = [dict(rng.choice(rows)) for _ in range(duplicate_count)] if rows else []
    return rows + duplicates


def _inject_schema_drift(
    rows: list[dict], fieldnames: list[str], id_field: str, rng: random.Random
) -> None:
    """Simulate an inconsistent export: some rows use a renamed column, and
    some rows carry an extra field the canonical schema doesn't define."""
    drift_field = rng.choice([f for f in fieldnames if f != id_field])
    renamed_field = f"{drift_field}_legacy"
    for row in rows:
        if drift_field in row and rng.random() < 0.15:
            row[renamed_field] = row.pop(drift_field)
        if rng.random() < 0.10:
            row["source_system"] = rng.choice(["legacy_crm", "warehouse_export", "manual_upload"])
