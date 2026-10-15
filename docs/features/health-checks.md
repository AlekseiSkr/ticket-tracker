# Health checks

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live (local); production once Fly is set up |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | `core/middleware.py`; Fly check in `fly.toml` |
| **Cost**     | $0 |
| **Depends on** | [hosting-fly.md](hosting-fly.md), [database.md](database.md) |

## What
Two endpoints:
- `GET /healthz` is **liveness**: the process is up. It never touches the database.
- `GET /readyz` is **readiness**: it runs `SELECT 1` and returns 503 if the DB is down.

Both are answered by the first middleware, before host validation and the HTTPS redirect.

## Why
- **Fly's checks hit the machine directly over HTTP and do not follow redirects.**
  `SECURE_SSL_REDIRECT` would otherwise return a 301, which Fly treats as unhealthy.
- **Neon scales to zero and the free tier has 100 CU-hours a month.** A health check that
  queried the DB every 30 s would keep it awake around the clock and exhaust the quota. So
  liveness never touches the DB, and readiness is for humans and uptime monitors.

**Rejected:**
- **django-health-check:** a dependency for two endpoints.
- **A URL route:** it would sit behind `ALLOWED_HOSTS` and the HTTPS redirect.

## How it's set up
- `core.middleware.HealthCheckMiddleware` is first in `MIDDLEWARE`.
- `fly.toml` has an `[[http_service.checks]]` entry on `/healthz` (every 30 s, 5 s timeout).
- Covered by `tests/test_health.py`, including "zero queries" for `/healthz` and a
  simulated DB outage for `/readyz`.

## Who owns what
No credentials.

## Gotchas
- Don't point an uptime monitor at `/readyz` every minute. That keeps Neon awake and burns
  CU-hours. Use `/healthz` for frequent checks.

## Open items
- [ ] Point the Sentry uptime monitor at `/healthz` once Sentry is set up.
