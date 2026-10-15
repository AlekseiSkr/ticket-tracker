"""Health endpoints, answered before host validation and the HTTPS redirect.

/healthz  liveness: the process is up. Never touches the database, so frequent platform
          checks don't keep the serverless Postgres awake or burn its compute hours.
/readyz   readiness: the database answers a trivial query.
"""

import logging
from collections.abc import Callable

from django.db import connection
from django.http import HttpRequest, HttpResponse, JsonResponse

logger = logging.getLogger(__name__)


class HealthCheckMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path == "/healthz":
            return JsonResponse({"status": "ok"})
        if request.path == "/readyz":
            return self._readiness()
        return self.get_response(request)

    @staticmethod
    def _readiness() -> JsonResponse:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            logger.exception("Readiness check failed: database unreachable")
            return JsonResponse({"status": "unavailable", "database": "down"}, status=503)
        return JsonResponse({"status": "ok", "database": "up"})
