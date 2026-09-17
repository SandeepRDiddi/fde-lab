from __future__ import annotations

import json
from typing import Any, Protocol

from generator.config import settings


class PutObjectClient(Protocol):
    """The slice of the boto3 S3 client interface this module needs — lets
    tests inject a fake without standing up real object storage."""

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, ContentType: str) -> Any: ...


class S3DatasetStore:
    """Writes a generated dataset to S3-compatible object storage (S3/R2/MinIO
    per architecture.md's data layer) as newline-delimited JSON, since
    messiness (schema drift) can give rows differing column sets that a flat
    CSV can't represent cleanly."""

    def __init__(self, client: PutObjectClient | None = None, bucket: str | None = None):
        self._client = client or self._build_default_client()
        self._bucket = bucket or settings.s3_bucket

    @staticmethod
    def _build_default_client() -> PutObjectClient:
        import boto3

        return boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )

    def upload(self, key: str, rows: list[dict]) -> str:
        body = "\n".join(json.dumps(row) for row in rows).encode("utf-8")
        self._client.put_object(
            Bucket=self._bucket, Key=key, Body=body, ContentType="application/x-ndjson"
        )
        return f"s3://{self._bucket}/{key}"
