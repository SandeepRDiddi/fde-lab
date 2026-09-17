import json

from generator.storage import S3DatasetStore


def test_upload_writes_ndjson_and_returns_s3_uri(fake_s3_client):
    store = S3DatasetStore(client=fake_s3_client, bucket="test-bucket")
    rows = [{"a": 1}, {"a": 2, "b": None}]

    location = store.upload("datasets/cohort/instance/run.jsonl", rows)

    assert location == "s3://test-bucket/datasets/cohort/instance/run.jsonl"
    stored = fake_s3_client.objects[("test-bucket", "datasets/cohort/instance/run.jsonl")]
    lines = stored["Body"].decode("utf-8").splitlines()
    assert [json.loads(line) for line in lines] == rows
    assert stored["ContentType"] == "application/x-ndjson"


def test_upload_keys_never_collide_across_calls(fake_s3_client):
    store = S3DatasetStore(client=fake_s3_client, bucket="test-bucket")

    store.upload("datasets/cohort/instance/run-1.jsonl", [{"a": 1}])
    store.upload("datasets/cohort/instance/run-2.jsonl", [{"a": 1}])

    assert len(fake_s3_client.objects) == 2
