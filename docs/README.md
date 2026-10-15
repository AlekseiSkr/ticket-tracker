# Docs

Two kinds of doc, both copied from [_template.md](_template.md) and kept short (a doc
nobody reads because it's long is worse than no doc):

- **Directory docs:** a `README.md` in **every directory that holds code or config**. It
  says what the directory does, why it's built that way, how its files fit together, and
  what to watch out for, so any person or agent can get up to speed on that folder alone.
- **Feature docs:** one per feature or external service in [features/](features/), covering
  accounts, setup steps and cross-cutting decisions.

## Rules

- **No secrets in git.** API keys, tokens and passwords live in the password manager or
  in Fly secrets (`fly secrets set`). Docs say *where* a credential lives, never its value.
- **Absolute dates.** Write `2026-10-15`, never "last week".
- **Record the rejected option.** Half of a decision's value is knowing what it beat.
- **Update `Status` and `Updated` when reality changes.** A doc that says Live about
  something dead is worse than nothing.

## Directory index

| Directory | What's there | Status | Doc |
|---|---|---|---|
| `config/` | Settings, env helpers, S3 storage backend, URLs, WSGI/ASGI | Live | [config/README.md](../config/README.md) |
| `core/` | Health/readiness middleware, ops infrastructure | Live | [core/README.md](../core/README.md) |
| `core/management/` | Management-command package | Live | [core/management/README.md](../core/management/README.md) |
| `core/management/commands/` | `ensure_bucket` | Live | [core/management/commands/README.md](../core/management/commands/README.md) |
| `tickets/` | Ticket domain: models, rules, admin | Planned (Phase 1) | [tickets/README.md](../tickets/README.md) |
| `tickets/migrations/` | Generated migrations, roles data migration | Planned (Phase 1) | [tickets/migrations/README.md](../tickets/migrations/README.md) |
| `tests/` | pytest-django suite | Live | [tests/README.md](../tests/README.md) |
| `docker/` | Config for local compose services | Live | [docker/README.md](../docker/README.md) |
| `docker/seaweedfs/` | Local S3 emulator identities | Live | [docker/seaweedfs/README.md](../docker/seaweedfs/README.md) |
| `.github/` | Dependabot, repo automation | Live | [.github/README.md](../.github/README.md) |
| `.github/workflows/` | CI and deploy pipelines | CI Live, deploy Planned | [.github/workflows/README.md](../.github/workflows/README.md) |

The root is covered by [../README.md](../README.md) (run it) and [../CLAUDE.md](../CLAUDE.md) (working rules).

## Feature index

| Feature | Status | Doc |
|---|---|---|
| Local development (Docker) | Live | [local-development.md](features/local-development.md) |
| Configuration and secrets | Live | [configuration-and-secrets.md](features/configuration-and-secrets.md) |
| Health checks | Live | [health-checks.md](features/health-checks.md) |
| Database (Postgres / Neon Frankfurt) | Live | [database.md](features/database.md) |
| File storage (SeaweedFS / Cloudflare R2 EU) | Live | [file-storage.md](features/file-storage.md) |
| Admin UI (Django admin + Unfold) | In progress | [admin-ui.md](features/admin-ui.md) |
| CI/CD (GitHub Actions) | In progress (CI Live) | [ci-cd.md](features/ci-cd.md) |
| Hosting (Fly.io, aleksei-ticket-tracker.fly.dev) | Live | [hosting-fly.md](features/hosting-fly.md) |
| Authentication and roles | Planned | [authentication-and-roles.md](features/authentication-and-roles.md) |
| AI form assistant (Groq) | Planned | [ai-form-assistant.md](features/ai-form-assistant.md) |
| Error monitoring (Sentry) | Planned | [error-monitoring.md](features/error-monitoring.md) |
| Demo data (seed) | Planned | [demo-data.md](features/demo-data.md) |

The overall build plan and its decisions are in [plan.md](plan.md).
