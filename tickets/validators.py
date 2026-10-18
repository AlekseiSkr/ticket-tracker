"""Attachment rules: allow-listed types checked by content (magic bytes), 10 MB cap, random keys."""

import codecs
import uuid
from pathlib import PurePath
from typing import Any

from django.core.exceptions import ValidationError
from django.core.files import File

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
# Extension -> the bytes a real file of that type starts with. "" means checked as text below.
SIGNATURES = {
    ".png": b"\x89PNG\r\n\x1a\n",
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
    ".pdf": b"%PDF-",
    ".txt": b"",
}


def validate_attachment(file: File) -> None:
    ext = PurePath(file.name or "").suffix.lower()
    if ext not in SIGNATURES:
        raise ValidationError("Attach a PNG, JPG, PDF or TXT file.")
    if file.size is not None and file.size > MAX_ATTACHMENT_BYTES:
        raise ValidationError("Attachments can be at most 10 MB.")
    file.seek(0)
    head = file.read(2048)
    file.seek(0)
    if ext == ".txt":
        try:
            # final=False: a multi-byte character cut off at the 2 KB boundary is fine.
            text = codecs.getincrementaldecoder("utf-8")().decode(head, final=False)
        except UnicodeDecodeError:
            raise ValidationError("This .txt file isn't UTF-8 text.") from None
        if "\0" in text:
            raise ValidationError("This .txt file isn't plain text.")
    elif not head.startswith(SIGNATURES[ext]):
        raise ValidationError(f"This file's contents don't match its {ext} extension.")


def attachment_upload_to(instance: Any, filename: str) -> str:
    """A random key, so names never collide or leak what the customer called the file."""
    return f"attachments/{uuid.uuid4().hex}{PurePath(filename).suffix.lower()}"
