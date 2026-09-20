import io
import json

import pytest

from app.grading import GradingError, evaluate_sql_submission, evaluate_technical_submission


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
    monkeypatch.setattr("app.grading.boto3.client", lambda *a, **kw: client)
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
