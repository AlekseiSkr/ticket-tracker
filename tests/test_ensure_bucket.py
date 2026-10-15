from io import StringIO
from unittest import mock

import pytest
from botocore.exceptions import ClientError
from django.core.management import CommandError, call_command


def _error(status: int) -> ClientError:
    return ClientError(
        {"Error": {"Code": str(status)}, "ResponseMetadata": {"HTTPStatusCode": status}},
        "HeadBucket",
    )


@pytest.fixture
def s3_client():
    with mock.patch("core.management.commands.ensure_bucket.default_storage") as storage:
        storage.bucket_name = "media"
        yield storage.connection.meta.client


def test_reports_reachable_bucket(s3_client):
    out = StringIO()
    call_command("ensure_bucket", stdout=out)
    assert "reachable" in out.getvalue()
    s3_client.create_bucket.assert_not_called()


def test_missing_bucket_fails_without_create(s3_client):
    s3_client.head_bucket.side_effect = _error(404)
    with pytest.raises(CommandError):
        call_command("ensure_bucket")


def test_missing_bucket_is_created_with_create(s3_client):
    s3_client.head_bucket.side_effect = _error(404)
    call_command("ensure_bucket", "--create", stdout=StringIO())
    s3_client.create_bucket.assert_called_once_with(Bucket="media")


def test_forbidden_bucket_is_never_created(s3_client):
    s3_client.head_bucket.side_effect = _error(403)
    with pytest.raises(CommandError):
        call_command("ensure_bucket", "--create")
    s3_client.create_bucket.assert_not_called()
