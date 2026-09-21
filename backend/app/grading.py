"""Grades a technical-task submission by actually running it, not by scanning
the submitted text for keywords (that's app/compliance.py, a separate gate).
FDE-013's v1 task type is a read-only SQL query, checked against the
scenario's own synthetic dataset (data-gen's output in object storage) by
comparing its result set to a reference query's -- correctness is measured,
not phrasing. FDE-015's run_query (below) executes the same way but doesn't
grade anything -- a non-graded "try it" step so a student can see what their
query actually returns before submitting it for real.
"""
from __future__ import annotations

import re
import sqlite3
from typing import Any

from app.dataset_store import DatasetStoreError, fetch_dataset_rows

# Read-only enforcement: student queries are graded, not executed against
# anything that persists -- a query that could mutate state or reach outside
# the in-memory table (ATTACH, PRAGMA) is rejected before it ever runs.
_DISALLOWED_KEYWORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|vacuum|replace|into)\b",
    re.IGNORECASE,
)

# A dataset's row count is small (data-gen defaults to a few hundred rows
# per instance) so fetching everything and slicing is simpler than a
# streaming/paginated fetch -- this just caps what a "try it" run hands
# back to the browser.
_RUN_PREVIEW_LIMIT = 50


class GradingError(Exception):
    """A setup failure (bad task config, unreachable/malformed dataset,
    broken reference_query) -- distinct from the student's query simply
    being wrong, which is a normal graded failure, not an exception."""


def _fetch_dataset_rows(dataset_location: str) -> list[dict]:
    try:
        return fetch_dataset_rows(dataset_location)
    except DatasetStoreError as exc:
        raise GradingError(str(exc)) from exc


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


def run_query(student_sql: str, dataset_location: str | None, task: dict[str, Any]) -> dict[str, Any]:
    """FDE-015: runs a query and returns its actual result, ungraded --
    lets a student iterate (explore the data, adjust, re-run) before
    deciding what to submit for real. Same read-only enforcement as
    grading, since this still executes against the real dataset; the only
    difference from evaluate_sql_submission is that nothing is compared or
    persisted here."""
    if not dataset_location:
        raise GradingError("Scenario instance has no dataset yet — nothing to run against")

    table_name = task.get("table_name") or "dataset"
    if not _is_single_select(student_sql):
        raise GradingError("Only a single read-only SELECT statement can be run")
    if _DISALLOWED_KEYWORDS.search(student_sql):
        raise GradingError("Only a read-only SELECT query can be run — remove any write/schema keyword")

    rows = _fetch_dataset_rows(dataset_location)
    conn = _load_sqlite(table_name, rows)
    try:
        cursor = conn.execute(student_sql)
        columns = [d[0] for d in cursor.description] if cursor.description else []
        result = cursor.fetchall()
    except sqlite3.Error as exc:
        raise GradingError(f"Query failed to execute: {exc}") from exc
    finally:
        conn.close()

    return {
        "columns": columns,
        "rows": [list(r) for r in result[:_RUN_PREVIEW_LIMIT]],
        "row_count": len(result),
        "truncated": len(result) > _RUN_PREVIEW_LIMIT,
    }
