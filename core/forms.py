"""Admin login form with a limit on failed attempts per client IP."""

from typing import Any

from django.core.exceptions import ValidationError
from unfold.forms import AuthenticationForm

from core import ratelimit

MAX_FAILURES = 10
WINDOW = 15 * 60  # seconds, counted from the first failure


class RateLimitedLoginForm(AuthenticationForm):
    """Ten failed logins from one IP block it for 15 minutes. The check runs before the
    password is hashed, so a blocked client costs no CPU."""

    def clean(self) -> dict[str, Any]:
        # Fly's proxy sets Fly-Client-IP; behind it, REMOTE_ADDR is the proxy itself.
        meta = self.request.META if self.request else {}
        key = f"login-failures:{meta.get('HTTP_FLY_CLIENT_IP') or meta.get('REMOTE_ADDR')}"
        if ratelimit.count(key) >= MAX_FAILURES:
            raise ValidationError(
                "Too many failed logins from your network. Try again in 15 minutes.",
                code="rate_limited",
            )
        try:
            return super().clean()
        except ValidationError:
            ratelimit.hit(key, WINDOW)
            raise
