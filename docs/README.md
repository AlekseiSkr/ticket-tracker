# Docs

Every feature gets one short doc in [features/](features/), copied from [_template.md](_template.md).
Keep each one short; a doc nobody reads because it's long is worse than no doc.

## Rules

- **No secrets in git.** API keys, tokens and passwords live in the password manager or
  in Fly secrets (`fly secrets set`). Docs say *where* a credential lives, never its value.
- **Absolute dates.** Write `2026-10-15`, never "last week".
- **Record the rejected option.** Half of a decision's value is knowing what it beat.
- **Update `Status` and `Updated` when reality changes.** A doc that says Live about
  something dead is worse than nothing.

## Index

| Feature | Status | Doc |
|---|---|---|
| Local development (Docker) | Live | [local-development.md](features/local-development.md) |
| Configuration and secrets | In progress | [configuration-and-secrets.md](features/configuration-and-secrets.md) |
| Health checks | Live | [health-checks.md](features/health-checks.md) |
| Database (Postgres / Neon) | In progress | [database.md](features/database.md) |
| File storage (SeaweedFS / Cloudflare R2) | In progress | [file-storage.md](features/file-storage.md) |
| Admin UI (Django admin + Unfold) | In progress | [admin-ui.md](features/admin-ui.md) |
| CI/CD (GitHub Actions) | In progress | [ci-cd.md](features/ci-cd.md) |
| Hosting (Fly.io) | Planned | [hosting-fly.md](features/hosting-fly.md) |
| Authentication and roles | Planned | [authentication-and-roles.md](features/authentication-and-roles.md) |
| AI form assistant (Groq) | Planned | [ai-form-assistant.md](features/ai-form-assistant.md) |
| Error monitoring (Sentry) | Planned | [error-monitoring.md](features/error-monitoring.md) |
| Demo data (seed) | Planned | [demo-data.md](features/demo-data.md) |

The overall build plan and its decisions are in [plan.md](plan.md).
