"""Callbacks referenced from settings.UNFOLD."""

from django.conf import settings
from django.http import HttpRequest


def environment_callback(request: HttpRequest) -> list[str] | None:
    """Header badge so a local instance is never mistaken for production."""
    return ["Local", "info"] if settings.DEBUG else None
