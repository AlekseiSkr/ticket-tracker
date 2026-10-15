"""Read configuration from environment variables.

Required values fail loudly at startup. There is deliberately no fallback to SQLite or
local disk: a missing variable in production must stop the app, not degrade it silently.
"""

import os

from django.core.exceptions import ImproperlyConfigured


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"Missing required environment variable: {name}")
    return value


def optional_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} must be a boolean, got {raw!r}")


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ImproperlyConfigured(f"{name} must be an integer, got {raw!r}") from exc


def env_list(name: str, *, required: bool = False) -> list[str]:
    raw = require_env(name) if required else optional_env(name)
    return [item.strip() for item in raw.split(",") if item.strip()]
