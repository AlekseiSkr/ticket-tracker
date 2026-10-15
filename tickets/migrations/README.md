# tickets/migrations/: database migrations

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Planned (no migrations until Phase 1 models exist) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | `tickets/migrations/` |
| **Cost**     | $0 |
| **Depends on** | [../README.md](../README.md), [../../docs/features/database.md](../../docs/features/database.md) |

## What
Django migrations for the `tickets` app: schema, constraints, indexes, and a data migration
that creates the role groups and permissions.

## Why
- **Migrations are generated, never hand-edited.** The exception is the data migration that
  creates groups.
- **CI fails if a model change has no migration** (`makemigrations --check`).
- **Production applies them via Fly's `release_command`**, so a failing migration aborts the
  deploy.

**Rejected:**
- Running migrations at container start: races between machines, and it can't abort a bad
  release.

## How it's set up
- **Create:** `docker compose exec web python manage.py makemigrations tickets`
- **Apply locally:** automatic when the `web` container starts.
- **Apply in production:** automatic on `fly deploy`.

## Who owns what
No credentials.

## Gotchas
- **Use expand/contract when changing columns.** Migrations run before the new code is live,
  so the old code must survive the new schema.
- **Constraints are real Postgres `CHECK`/`UNIQUE` constraints.** Seed data must already
  satisfy them.

## Open items
- [ ] Phase 1: initial schema + groups/permissions data migration.
