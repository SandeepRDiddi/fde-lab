"""Grades a technical-task submission by actually running it, not by scanning
the submitted text for keywords (that's app/compliance.py, a separate gate).
FDE-013's v1 task type is a read-only SQL query, checked against the
scenario's own synthetic dataset (data-gen's output in object storage) by
comparing its result set to a reference query's -- correctness is measured,
not phrasing.
"""
from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

import boto3

from app.config import settings

# Read-only enforcement: student queries are graded, not executed against
# anything that persists -- a query that could mutate state or reach outside
# the in-memory table (ATTACH, PRAGMA) is rejected before it ever runs.
_DISALLOWED_KEYWORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|vacuum|replace|into)\b",
    re.IGNORECASE,
)


class GradingError(Exception):
    """A setup failure (bad task config, unreachable/malformed dataset,
    broken reference_query) -- distinct from the student's query simply
    being wrong, which is a normal graded failure, not an exception."""


def _fetch_dataset_rows(dataset_location: str) -> list[dict]:
    if not dataset_location.startswith("s3://"):
        raise GradingError(f"Unsupported dataset location: {dataset_location!r}")
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
        raise GradingError(f"Could not fetch dataset {dataset_location!r}: {exc}") from exc

    try:
        return [json.loads(line) for line in body.splitlines() if line.strip()]
    except json.JSONDecodeError as exc:
        raise GradingError(f"Dataset {dataset_location!r} is not valid NDJSON: {exc}") from exc


def _load_sqlite(table_name: str, rows: list[dict]) -> sqlite3.Connection:
    """Builds an in-memory table from the dataset's rows. Column set is the
    union across all rows (not just the first), since messiness-injected
    schema drift means later rows can carry extra columns the first row
    doesn't have -- a missing value on a given row becomes NULL."""
    conn = sqlite3.connect(":memory:")
    columns: list[str] = []
    for row in rows:
        for col in row:
            if col not in columns:
                columns.append(col)

    if not columns:
        raise GradingError("Dataset has no rows to grade against")

    quoted_cols = ", ".join(f'"{c}"' for c in columns)
    conn.execute(f'CREATE TABLE "{table_name}" ({quoted_cols})')
    placeholders = ", ".join("?" for _ in columns)
    conn.executemany(
        f'INSERT INTO "{table_name}" VALUES ({placeholders})',
        [[row.get(c) for c in columns] for row in rows],
    )
    conn.commit()
    return conn


def _is_single_select(sql: str) -> bool:
    statements = [s.strip() for s in sql.strip().rstrip(";").split(";") if s.strip()]
    return len(statements) == 1 and statements[0].lower().startswith("select")


def evaluate_sql_submission(
    student_sql: str, dataset_location: str | None, task: dict[str, Any]
) -> tuple[bool, list[dict]]:
    if not dataset_location:
        raise GradingError("Scenario instance has no dataset yet — nothing to grade against")

    table_name = task.get("table_name") or "dataset"
    reference_query = task.get("reference_query")
    if not reference_query:
        raise GradingError("technical_task.reference_query is not configured")
    compare = task.get("compare", "unordered_rows")

    if not _is_single_select(student_sql):
        return False, [
            {
                "rule_id": "query_must_be_select",
                "description": "Submission must be a single SELECT statement.",
            }
        ]
    if _DISALLOWED_KEYWORDS.search(student_sql):
        return False, [
            {
                "rule_id": "query_disallowed_keyword",
                "description": "Only a read-only SELECT query is graded — remove any write/schema keyword.",
            }
        ]

    rows = _fetch_dataset_rows(dataset_location)
    conn = _load_sqlite(table_name, rows)
    try:
        try:
            expected = conn.execute(reference_query).fetchall()
        except sqlite3.Error as exc:
            raise GradingError(f"technical_task.reference_query failed to run: {exc}") from exc

        try:
            actual = conn.execute(student_sql).fetchall()
        except sqlite3.Error as exc:
            return False, [
                {
                    "rule_id": "query_execution_error",
                    "description": f"Query failed to execute: {exc}",
                }
            ]
    finally:
        conn.close()

    if compare == "ordered_rows":
        passed = expected == actual
    else:
        passed = sorted(map(tuple, expected)) == sorted(map(tuple, actual))

    if passed:
        return True, []
    return False, [
        {
            "rule_id": "result_mismatch",
            "description": (
                f"Query returned {len(actual)} row(s); expected {len(expected)} row(s) "
                "matching the task's reference result."
            ),
        }
    ]


def evaluate_technical_submission(
    content: str, dataset_location: str | None, task: dict[str, Any]
) -> tuple[bool, list[dict]]:
    task_type = task.get("task_type")
    if task_type == "sql_query":
        return evaluate_sql_submission(content, dataset_location, task)
    raise GradingError(f"Unsupported technical_task.task_type: {task_type!r}")
