from urllib.parse import parse_qs, urlparse

from config.storage import PrivateMediaStorage

COMMON = {
    "bucket_name": "media",
    "endpoint_url": "http://storage:8333",
    "access_key": "test-key",
    "secret_key": "test-secret",
    "region_name": "us-east-1",
    "addressing_style": "path",
    "signature_version": "s3v4",
    "querystring_auth": True,
    "querystring_expire": 60,
}


def _signed(url: str) -> tuple[str, dict[str, list[str]]]:
    parsed = urlparse(url)
    return parsed.netloc, parse_qs(parsed.query)


def test_urls_are_presigned_against_the_internal_endpoint_by_default():
    storage = PrivateMediaStorage(**COMMON)
    host, query = _signed(storage.url("attachments/report.pdf"))
    assert host == "storage:8333"
    assert "X-Amz-Signature" in query
    assert query["X-Amz-Expires"] == ["60"]


def test_public_endpoint_is_used_for_browser_facing_urls():
    storage = PrivateMediaStorage(public_endpoint_url="http://localhost:8333", **COMMON)
    url = storage.url("attachments/report.pdf")
    host, query = _signed(url)
    assert host == "localhost:8333"
    assert "/media/attachments/report.pdf" in url
    assert "X-Amz-Signature" in query
