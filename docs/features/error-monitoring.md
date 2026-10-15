# Error monitoring (Sentry)

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Planned (Phase 5) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | Sentry (Developer plan), project `ticket-tracker`, EU data region |
| **Cost**     | $0 (Developer: 5k errors/mo, 1 uptime monitor, 30-day retention) |
| **Depends on** | [hosting-fly.md](hosting-fly.md), [health-checks.md](health-checks.md) |

## What
Unhandled exceptions from Django are reported to Sentry with request context, but no
personal data. One uptime monitor watches `/healthz`.

## Why
It answers "if the live URL 500s, what's your first debugging step?" with something
concrete: open the Sentry issue and see the stack trace and release. Fly logs are only
useful while you're watching them.

**Rejected:**
- **Logs only:** no alerting, no grouping.
- **Better Stack / Grafana Cloud:** more setup for the same signal.

## How it's set up
1. https://sentry.io/signup/: choose the **EU** data region at sign-up (it can't be changed
   later).
2. Create a Django project and copy the DSN.
3. `fly secrets set SENTRY_DSN=…`. The app enables Sentry only when the DSN is set, with
   `send_default_pii=False`.
4. Uptime → create a monitor for `https://<app>.fly.dev/healthz`.

## Who owns what
- **Sentry account:** Aleksei.
- **DSN:** Fly secrets. It isn't strictly secret, but keep it out of the repo anyway.

## Gotchas
- **Point the uptime monitor at `/healthz`, not `/readyz`**, to avoid waking Neon (see
  [database.md](database.md)).

## Open items
- [ ] Create the Sentry project (Phase 5).
