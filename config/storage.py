"""Object storage backend.

All files live in one private bucket and every URL is presigned. `public_endpoint_url`
exists for local development only: the app reaches the S3 emulator as `storage:8333`
inside Docker, but the browser needs `localhost:8333`. A presigned URL signs its host,
so the host can't be rewritten afterwards; instead we sign with a client that points at
the public endpoint. In production both endpoints are the same and this path is unused.
"""

from functools import cached_property
from typing import Any

import boto3
from storages.backends.s3 import S3Storage
from storages.utils import clean_name


class PrivateMediaStorage(S3Storage):
    def __init__(self, public_endpoint_url: str | None = None, **settings: Any) -> None:
        self.public_endpoint_url = public_endpoint_url
        super().__init__(**settings)

    @cached_property
    def _public_client(self) -> Any:
        return boto3.client(
            "s3",
            endpoint_url=self.public_endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name,
            config=self.client_config,
        )

    def url(
        self,
        name: str,
        parameters: dict[str, Any] | None = None,
        expire: int | None = None,
        http_method: str | None = None,
    ) -> str:
        if not self.public_endpoint_url:
            return super().url(name, parameters, expire, http_method)
        params = {"Bucket": self.bucket_name, "Key": self._normalize_name(clean_name(name))}
        params.update(parameters or {})
        return self._public_client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expire if expire is not None else self.querystring_expire,
            HttpMethod=http_method,
        )
