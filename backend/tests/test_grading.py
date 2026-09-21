import io
import json

import pytest

from app.grading import (
    GradingError,
    evaluate_python_script_submission,
    evaluate_sql_submission,
    evaluate_technical_submission,
    run_python_script_preview,
    run_query,
)


class FakeBody:
    def __init__(self, data: bytes):
        self._buf = io.BytesIO(data)

    def read(self):
        return self._buf.read()


class FakeS3Client:
    def __init__(self, objects: dict[str, bytes]):
        self._objects = objects

    def get_object(self, *, Bucket, Key):
        return {"Body": FakeBody(self._objects[f"{Bucket}/{Key}"])}


ROWS = [
    {"order_id": "ORD-1", "customer_email": "a@example.com", "quantity": 1},
    {"order_id": "ORD-1", "customer_email": "a@example.com", "quantity": 1},  # duplicate row
    {"order_id": "ORD-2", "customer_email": "b@example.com", "quantity": 3},
]
DATASET_LOCATION = "s3://fde-lab-datasets/instances/abc/orders.ndjson"

TASK = {
    "task_type": "sql_query",
    "table_name": "orders",
    "reference_query": "SELECT DISTINCT order_id, customer_email, quantity FROM orders",
}


@pytest.fixture
def fake_bucket(monkeypatch):
    body = "\n".join(json.dumps(row) for row in ROWS).encode("utf-8")
    client = FakeS3Client({"fde-lab-datasets/instances/abc/orders.ndjson": body})
    monkeypatch.setattr("app.dataset_store.boto3.client", lambda *a, **kw: client)
    return client


def test_correct_query_passes(fake_bucket):
    passed, failures = evaluate_sql_submission(
        "SELECT DISTINCT order_id, customer_email, quantity FROM orders", DATASET_LOCATION, TASK
    )
    assert passed is True
    assert failures == []


def test_unordered_rows_ignores_row_order(fake_bucket):
    passed, failures = evaluate_sql_submission(
        "SELECT DISTINCT customer_email, quantity, order_id FROM orders ORDER BY customer_email DESC",
        DATASET_LOCATION,
        {**TASK, "reference_query": "SELECT DISTINCT customer_email, quantity, order_id FROM orders"},
    )
    assert passed is True
    assert failures == []


def test_query_missing_dedup_fails_with_mismatch(fake_bucket):
    passed, failures = evaluate_sql_submission("SELECT * FROM orders", DATASET_LOCATION, TASK)
    assert passed is False
    assert failures[0]["rule_id"] == "result_mismatch"


def test_non_select_query_rejected(fake_bucket):
    passed, failures = evaluate_sql_submission(
        "DELETE FROM orders WHERE quantity = 1", DATASET_LOCATION, TASK
    )
    assert passed is False
    assert failures[0]["rule_id"] == "query_must_be_select"


def test_multi_statement_query_rejected(fake_bucket):
    passed, failures = evaluate_sql_submission(
        "SELECT * FROM orders; DROP TABLE orders;", DATASET_LOCATION, TASK
    )
    assert passed is False
    assert failures[0]["rule_id"] == "query_must_be_select"


def test_disallowed_keyword_rejected(fake_bucket):
    passed, failures = evaluate_sql_submission(
        "SELECT * FROM orders WHERE customer_email = 'drop the mic'", DATASET_LOCATION, TASK
    )
    assert passed is False
    assert failures[0]["rule_id"] == "query_disallowed_keyword"


def test_correct_query_passes_with_mixed_null_and_string_column_values(monkeypatch):
    # Regression: a column holding None in one row and a string in another
    # (real datasets have nulls) used to raise TypeError from plain
    # sorted() when comparing result sets, since Python can't order None
    # against str -- caught live against a real messy dataset.
    rows = [
        {"order_id": "ORD-1", "customer_email": None, "quantity": 1},
        {"order_id": "ORD-2", "customer_email": "b@example.com", "quantity": 3},
        {"order_id": "ORD-3", "customer_email": None, "quantity": 2},
    ]
    body = "\n".join(json.dumps(row) for row in rows).encode("utf-8")
    client = FakeS3Client({"fde-lab-datasets/instances/abc/orders.ndjson": body})
    monkeypatch.setattr("app.dataset_store.boto3.client", lambda *a, **kw: client)

    task = {"task_type": "sql_query", "table_name": "orders", "reference_query": "SELECT * FROM orders"}
    passed, failures = evaluate_sql_submission("SELECT * FROM orders", DATASET_LOCATION, task)

    assert passed is True
    assert failures == []


def test_invalid_sql_returns_execution_error(fake_bucket):
    passed, failures = evaluate_sql_submission("SELECT * FRUM orders", DATASET_LOCATION, TASK)
    assert passed is False
    assert failures[0]["rule_id"] == "query_execution_error"


def test_missing_dataset_location_raises_grading_error(fake_bucket):
    with pytest.raises(GradingError):
        evaluate_sql_submission("SELECT 1", None, TASK)


def test_missing_reference_query_raises_grading_error(fake_bucket):
    with pytest.raises(GradingError):
        evaluate_sql_submission("SELECT 1", DATASET_LOCATION, {"task_type": "sql_query", "table_name": "orders"})


def test_evaluate_technical_submission_dispatches_by_task_type(fake_bucket):
    passed, failures = evaluate_technical_submission(
        "SELECT DISTINCT order_id, customer_email, quantity FROM orders", DATASET_LOCATION, TASK
    )
    assert passed is True
    assert failures == []


def test_evaluate_technical_submission_unknown_task_type_raises(fake_bucket):
    with pytest.raises(GradingError):
        evaluate_technical_submission("anything", DATASET_LOCATION, {"task_type": "python_script"})


def test_run_query_returns_actual_result_ungraded(fake_bucket):
    result = run_query("SELECT * FROM orders", DATASET_LOCATION, TASK)
    assert result["columns"] == ["order_id", "customer_email", "quantity"]
    assert result["row_count"] == 3
    assert result["truncated"] is False
    assert len(result["rows"]) == 3


def test_run_query_truncates_beyond_preview_limit(fake_bucket, monkeypatch):
    import app.grading as grading_module

    monkeypatch.setattr(grading_module, "_RUN_PREVIEW_LIMIT", 2)

    result = run_query("SELECT * FROM orders", DATASET_LOCATION, TASK)

    assert result["row_count"] == 3
    assert len(result["rows"]) == 2
    assert result["truncated"] is True


def test_run_query_rejects_non_select(fake_bucket):
    with pytest.raises(GradingError):
        run_query("DELETE FROM orders", DATASET_LOCATION, TASK)


def test_run_query_rejects_disallowed_keyword(fake_bucket):
    with pytest.raises(GradingError):
        run_query("SELECT * FROM orders WHERE customer_email = 'drop the mic'", DATASET_LOCATION, TASK)


def test_run_query_surfaces_execution_error(fake_bucket):
    with pytest.raises(GradingError):
        run_query("SELECT * FRUM orders", DATASET_LOCATION, TASK)


def test_run_query_without_dataset_raises(fake_bucket):
    with pytest.raises(GradingError):
        run_query("SELECT 1", None, TASK)


DEDUP_REFERENCE_SOLUTION = """
import json

with open("orders.json") as f:
    rows = json.load(f)

seen = {}
for row in rows:
    seen[row["order_id"]] = row

with open("cleaned.json", "w") as f:
    json.dump(list(seen.values()), f)
"""

PYTHON_TASK = {
    "task_type": "python_script",
    "input_filename": "orders.json",
    "output_filename": "cleaned.json",
    "reference_solution": DEDUP_REFERENCE_SOLUTION,
}


def test_evaluate_python_script_submission_passes_correct_script(fake_bucket):
    passed, failures = evaluate_python_script_submission(DEDUP_REFERENCE_SOLUTION, DATASET_LOCATION, PYTHON_TASK)
    assert passed is True
    assert failures == []


def test_evaluate_python_script_submission_fails_wrong_script(fake_bucket):
    passthrough = """
import json
with open("orders.json") as f:
    rows = json.load(f)
with open("cleaned.json", "w") as f:
    json.dump(rows, f)
"""
    passed, failures = evaluate_python_script_submission(passthrough, DATASET_LOCATION, PYTHON_TASK)
    assert passed is False
    assert failures[0]["rule_id"] == "result_mismatch"


def test_evaluate_python_script_submission_surfaces_script_error(fake_bucket):
    broken = "raise RuntimeError('nope')"
    passed, failures = evaluate_python_script_submission(broken, DATASET_LOCATION, PYTHON_TASK)
    assert passed is False
    assert failures[0]["rule_id"] == "script_execution_error"


def test_evaluate_python_script_submission_rejects_non_list_output(fake_bucket):
    wrong_shape = """
import json
with open("cleaned.json", "w") as f:
    json.dump({"not": "a list"}, f)
"""
    passed, failures = evaluate_python_script_submission(wrong_shape, DATASET_LOCATION, PYTHON_TASK)
    assert passed is False
    assert failures[0]["rule_id"] == "invalid_output_shape"


def test_evaluate_python_script_submission_missing_reference_raises(fake_bucket):
    with pytest.raises(GradingError):
        evaluate_python_script_submission("x", DATASET_LOCATION, {"task_type": "python_script"})


def test_evaluate_python_script_submission_without_dataset_raises(fake_bucket):
    with pytest.raises(GradingError):
        evaluate_python_script_submission(DEDUP_REFERENCE_SOLUTION, None, PYTHON_TASK)


def test_evaluate_technical_submission_dispatches_python_script(fake_bucket):
    passed, failures = evaluate_technical_submission(DEDUP_REFERENCE_SOLUTION, DATASET_LOCATION, PYTHON_TASK)
    assert passed is True
    assert failures == []


def test_run_python_script_preview_returns_actual_result_ungraded(fake_bucket):
    passthrough = """
import json
with open("orders.json") as f:
    rows = json.load(f)
with open("cleaned.json", "w") as f:
    json.dump(rows, f)
"""
    result = run_python_script_preview(passthrough, DATASET_LOCATION, PYTHON_TASK)
    assert result["row_count"] == 3
    assert set(result["columns"]) == {"order_id", "customer_email", "quantity"}


def test_run_python_script_preview_without_dataset_raises(fake_bucket):
    with pytest.raises(GradingError):
        run_python_script_preview("x", None, PYTHON_TASK)


def test_python_script_submission_passes_with_mixed_null_and_string_output_values(monkeypatch):
    # Same regression as the SQL test above, for the python_script path's
    # own row comparison (_normalize_rows).
    rows = [
        {"order_id": "ORD-1", "customer_email": None},
        {"order_id": "ORD-2", "customer_email": "b@example.com"},
        {"order_id": "ORD-3", "customer_email": None},
    ]
    body = "\n".join(json.dumps(row) for row in rows).encode("utf-8")
    client = FakeS3Client({"fde-lab-datasets/instances/abc/orders.ndjson": body})
    monkeypatch.setattr("app.dataset_store.boto3.client", lambda *a, **kw: client)

    passthrough = """
import json
with open("orders.json") as f:
    rows = json.load(f)
with open("cleaned.json", "w") as f:
    json.dump(rows, f)
"""
    task = {"task_type": "python_script", "input_filename": "orders.json", "output_filename": "cleaned.json", "reference_solution": passthrough}
    passed, failures = evaluate_python_script_submission(passthrough, DATASET_LOCATION, task)

    assert passed is True
    assert failures == []
