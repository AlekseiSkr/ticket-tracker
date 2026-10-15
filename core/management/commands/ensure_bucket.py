"""Check that the media bucket is reachable; with --create, create it if missing.

Local development uses --create against the S3 emulator. In production the bucket is
created once in the Cloudflare dashboard, so run it without --create as a smoke test.
"""

from typing import Any

from botocore.exceptions import ClientError
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError, CommandParser


class Command(BaseCommand):
    help = "Verify the media bucket exists (optionally create it)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--create", action="store_true", help="Create the bucket if missing.")

    def handle(self, *args: Any, **options: Any) -> None:
        client = default_storage.connection.meta.client  # type: ignore[attr-defined]
        bucket = default_storage.bucket_name  # type: ignore[attr-defined]
        try:
            client.head_bucket(Bucket=bucket)
        except ClientError as exc:
            status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status != 404 or not options["create"]:
                raise CommandError(f"Bucket {bucket!r} is not reachable: {exc}") from exc
            client.create_bucket(Bucket=bucket)
            self.stdout.write(self.style.SUCCESS(f"Created bucket {bucket!r}"))
            return
        self.stdout.write(self.style.SUCCESS(f"Bucket {bucket!r} is reachable"))
