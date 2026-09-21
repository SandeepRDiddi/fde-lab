"""Grades a technical-task submission by actually running it, not by scanning
the submitted text for keywords (that's app/compliance.py, a separate gate).
FDE-013's v1 task type is a read-only SQL query, checked against the
scenario's own synthetic dataset (data-gen's output in object storage) by
comparing its result set to a reference query's -- correctness is measured,
not phrasing. FDE-015's run_query (below) executes the same way but doesn't
grade anything -- a non-graded "try it" step so a student can see what their
query actually returns before submitting it for real.

FDE-016 adds a second task type, python_script: the student writes an
actual script (not a single query) that reads the dataset and writes a
corrected output, run in app/code_runner.py's sandbox and compared to a
reference solution's own output the same way sql_query compares result
sets -- a query answers one question, a script is closer to the real
"build something that works" shape of FDE work.
"""
from __future__ import annotations

import re
import sqlite3
from typing import Any

from app.code_runner import CodeRunnerError, run_python_script
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
        # key=repr, not plain sorted() -- a nullable column (real datasets
        # have them) can hold None in one row and a string in another, and
        # Python can't order None against str, which plain sorted() would
        # hit the moment an earlier column ties between two rows.
        passed = sorted(map(tuple, expected), key=repr) == sorted(map(tuple, actual), key=repr)

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


def _rows_to_dicts(dataset_location: str) -> list[dict]:
    return _fetch_dataset_rows(dataset_location)


def _normalize_rows(rows: list[dict]) -> list[tuple]:
    # Real datasets have nulls (data-gen's messiness) -- Python can't order
    # None against a str, so the same column holding None in one row and a
    # string in another raises TypeError under plain sorted(). Sort by each
    # tuple's repr (always a string, always comparable) instead; equality
    # between the two normalized lists this feeds into still compares the
    # real values, so correctness doesn't depend on repr being unique, only
    # deterministic (rows with the same values always sort the same way).
    tuples = [tuple(sorted(row.items(), key=lambda kv: kv[0])) for row in rows]
    return sorted(tuples, key=repr)


def evaluate_python_script_submission(
    student_code: str, dataset_location: str | None, task: dict[str, Any]
) -> tuple[bool, list[dict]]:
    if not dataset_location:
        raise GradingError("Scenario instance has no dataset yet — nothing to grade against")

    reference_solution = task.get("reference_solution")
    if not reference_solution:
        raise GradingError("technical_task.reference_solution is not configured")
    input_filename = task.get("input_filename") or "input.json"
    output_filename = task.get("output_filename") or "output.json"
    compare = task.get("compare", "unordered_rows")

    rows = _rows_to_dicts(dataset_location)

    try:
        expected = run_python_script(
            reference_solution, rows, input_filename=input_filename, output_filename=output_filename
        )
    except CodeRunnerError as exc:
        raise GradingError(f"technical_task.reference_solution failed to run: {exc}") from exc
    if not isinstance(expected, list) or not all(isinstance(r, dict) for r in expected):
        raise GradingError("technical_task.reference_solution must write a JSON array of objects")

    try:
        actual = run_python_script(
            student_code, rows, input_filename=input_filename, output_filename=output_filename
        )
    except CodeRunnerError as exc:
        return False, [{"rule_id": "script_execution_error", "description": str(exc)}]

    if not isinstance(actual, list) or not all(isinstance(r, dict) for r in actual):
        return False, [
            {
                "rule_id": "invalid_output_shape",
                "description": f'Output file "{output_filename}" must contain a JSON array of objects.',
            }
        ]

    if compare == "exact":
        passed = expected == actual
    else:
        passed = _normalize_rows(expected) == _normalize_rows(actual)

    if passed:
        return True, []
    return False, [
        {
            "rule_id": "result_mismatch",
            "description": (
                f"Output has {len(actual)} row(s); expected {len(expected)} row(s) "
                "matching the reference solution's output."
            ),
        }
    ]


def evaluate_technical_submission(
    content: str, dataset_location: str | None, task: dict[str, Any]
) -> tuple[bool, list[dict]]:
    task_type = task.get("task_type")
    if task_type == "sql_query":
        return evaluate_sql_submission(content, dataset_location, task)
    if task_type == "python_script":
        return evaluate_python_script_submission(content, dataset_location, task)
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


def run_python_script_preview(
    student_code: str, dataset_location: str | None, task: dict[str, Any]
) -> dict[str, Any]:
    """FDE-016's run_query equivalent for python_script: runs the script
    and returns what it actually wrote, ungraded. Response shape matches
    run_query's (columns/rows/row_count/truncated) so the frontend renders
    both with the same table component."""
    if not dataset_location:
        raise GradingError("Scenario instance has no dataset yet — nothing to run against")

    input_filename = task.get("input_filename") or "input.json"
    output_filename = task.get("output_filename") or "output.json"
    rows = _rows_to_dicts(dataset_location)

    try:
        output = run_python_script(
            student_code, rows, input_filename=input_filename, output_filename=output_filename
        )
    except CodeRunnerError as exc:
        raise GradingError(str(exc)) from exc
    if not isinstance(output, list) or not all(isinstance(r, dict) for r in output):
        raise GradingError(f'Output file "{output_filename}" must contain a JSON array of objects.')

    columns: list[str] = []
    for row in output:
        for col in row:
            if col not in columns:
                columns.append(col)
    preview_rows = output[:_RUN_PREVIEW_LIMIT]

    return {
        "columns": columns,
        "rows": [[row.get(c) for c in columns] for row in preview_rows],
        "row_count": len(output),
        "truncated": len(output) > _RUN_PREVIEW_LIMIT,
    }
