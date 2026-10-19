"""Fixed-window counters in the default cache, shared by the login form and the AI assistant.

shortcut: the default cache is per process (2 gunicorn workers), so real limits are up to 2x
and a deploy resets them; point CACHES at a shared cache if that matters.
"""

from django.core.cache import cache


def count(key: str) -> int:
    return int(cache.get(key, 0))


def hit(key: str, window: int) -> int:
    """Add one to the key's counter and return it. The window starts at the first hit."""
    if cache.add(key, 1, window):
        return 1
    try:
        return int(cache.incr(key))
    except ValueError:  # the window expired between add() and incr()
        cache.add(key, 1, window)
        return 1
