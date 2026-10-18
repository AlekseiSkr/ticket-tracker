# core/: cross-cutting app infrastructure

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | `core/` (Django app `core`) |
| **Cost**     | $0 |
| **Depends on** | [../config/README.md](../config/README.md), [../docs/features/health-checks.md](../docs/features/health-checks.md) |

## What
Infrastructure that isn't part of the ticket domain: the health/readiness middleware,
operational management commands, the auth admin registrations and the admin theme. It has no models.

## Why
This keeps `tickets/` purely about the domain, so ops code and business rules don't mix.

**Rejected:** putting these in `config/`. Management commands and middleware need a real app.

## How it's set up
| Path | Role |
|---|---|
| `apps.py` | `CoreConfig`. |
| `middleware.py` | `HealthCheckMiddleware` answers `/healthz` (liveness, zero DB queries) and `/readyz` (`SELECT 1`, 503 if the DB is down) before host validation and the HTTPS redirect. |
| `management/` | Operational commands (see [management/README.md](management/README.md)). |
| `admin.py` | `User` and `Group` re-registered with Unfold's admin classes and forms. |
| `admin_ui.py` | Callbacks for `settings.UNFOLD` (the "Local" environment badge). |
| `assistant.py` | The AI form assistant endpoint (`/admin/assistant/`): role-filtered form metadata into the prompt, Groq call, help-text fallback, per-user rate limit (see [../docs/features/ai-form-assistant.md](../docs/features/ai-form-assistant.md)). |
| `static/core/` | Theme assets: `theme.css`, self-hosted fonts, favicon, login art (see [static/core/README.md](static/core/README.md)). |

Tests: `tests/test_health.py` and `tests/test_ensure_bucket.py`.

## Who owns what
No credentials.

## Gotchas
- **`/healthz` must never touch the database.** It's polled every 30 s, and Neon's free
  compute hours would drain. A test asserts zero queries.

## Open items
- [ ] Phase 3: the AI-assistant view may live here or in `tickets/`. Decide when it's built.
