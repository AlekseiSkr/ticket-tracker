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
| `core/static/core/` | Admin theme: stylesheet, self-hosted fonts, favicon, login art | Live | [core/static/core/README.md](../core/static/core/README.md) |
| `templates/` | Branded 404/500 pages | Live | [templates/README.md](../templates/README.md) |
| `templates/admin/` | Thin Unfold overrides: skip link, dashboard greeting | Live | [templates/admin/README.md](../templates/admin/README.md) |
| `core/management/` | Management-command package | Live | [core/management/README.md](../core/management/README.md) |
| `core/management/commands/` | `ensure_bucket` | Live | [core/management/commands/README.md](../core/management/commands/README.md) |
| `tickets/` | Ticket domain: models, rules, admin, attachment view | Live | [tickets/README.md](../tickets/README.md) |
| `tickets/migrations/` | Generated schema migration, roles data migration | Live | [tickets/migrations/README.md](../tickets/migrations/README.md) |
| `tickets/management/` | Management-command package | Live | [tickets/management/README.md](../tickets/management/README.md) |
| `tickets/management/commands/` | `seed_users`, `seed_demo` | Live | [tickets/management/commands/README.md](../tickets/management/commands/README.md) |
| `tests/` | pytest-django suite | Live | [tests/README.md](../tests/README.md) |
| `docker/` | Config for local compose services | Live | [docker/README.md](../docker/README.md) |
| `docker/seaweedfs/` | Local S3 emulator identities | Live | [docker/seaweedfs/README.md](../docker/seaweedfs/README.md) |
| `.github/` | Dependabot, repo automation | Live | [.github/README.md](../.github/README.md) |
| `.github/workflows/` | CI and deploy pipelines | Live | [.github/workflows/README.md](../.github/workflows/README.md) |

The root is covered by [../README.md](../README.md) (overview, setup and the brief report), [runbook.md](runbook.md) (operations), [../CLAUDE.md](../CLAUDE.md) (working rules),
[../PRODUCT.md](../PRODUCT.md) (product context) and [../DESIGN.md](../DESIGN.md) (the admin's design system).

## Feature index

| Feature | Status | Doc |
|---|---|---|
| Local development (Docker) | Live | [local-development.md](features/local-development.md) |
| Configuration and secrets | Live | [configuration-and-secrets.md](features/configuration-and-secrets.md) |
| Health checks | Live | [health-checks.md](features/health-checks.md) |
| Database (Postgres / Neon Frankfurt) | Live | [database.md](features/database.md) |
| File storage (SeaweedFS / Cloudflare R2 EU) | Live | [file-storage.md](features/file-storage.md) |
| Admin UI (Django admin + Unfold) | In progress | [admin-ui.md](features/admin-ui.md) |
| Design language (Benrey: dark, lime, lit-line nav, self-hosted fonts) | Live | [design-language.md](features/design-language.md) |
| CI/CD (GitHub Actions → Fly) | Live | [ci-cd.md](features/ci-cd.md) |
| Hosting (Fly.io, aleksei-ticket-tracker.fly.dev) | Live | [hosting-fly.md](features/hosting-fly.md) |
| Authentication and roles | Live (roles, reviewer accounts) | [authentication-and-roles.md](features/authentication-and-roles.md) |
| AI form assistant (Groq) | Live | [ai-form-assistant.md](features/ai-form-assistant.md) |
| Error monitoring (Sentry) | Live in code (DSN not set yet) | [error-monitoring.md](features/error-monitoring.md) |
| Content Security Policy | Live in code | [content-security-policy.md](features/content-security-policy.md) |
| Demo data (seed) | Live (commands); reset workflow planned | [demo-data.md](features/demo-data.md) |

The overall build plan and its decisions are in [plan.md](plan.md).
