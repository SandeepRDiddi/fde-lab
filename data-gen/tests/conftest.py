import pytest


class FakeS3Client:
    """In-memory stand-in for boto3's S3 client, so tests never touch real
    object storage."""

    def __init__(self):
        self.objects: dict[str, dict] = {}

    def put_object(self, *, Bucket, Key, Body, ContentType):
        self.objects[(Bucket, Key)] = {"Body": Body, "ContentType": ContentType}


@pytest.fixture()
def fake_s3_client():
    return FakeS3Client()
