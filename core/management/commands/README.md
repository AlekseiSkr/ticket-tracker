# core/management/commands/: operational commands

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | `core/management/commands/`; run as `python manage.py <name>` |
| **Cost**     | $0 |
| **Depends on** | [../../../docs/features/file-storage.md](../../../docs/features/file-storage.md) |

## What
`manage.py` commands for operating the app, as opposed to domain commands such as seeding,
which will live in `tickets/`.

## Why
Ops steps (bucket checks) must run the same way locally, in CI and on Fly
(`fly ssh console -C "python manage.py …"`).

**Rejected:** shell scripts calling the AWS CLI. That's an extra tool, and they wouldn't use
the app's own storage configuration.

## How it's set up
| File | Command | What it does |
|---|---|---|
| `ensure_bucket.py` | `ensure_bucket [--create]` | Calls `HeadBucket` through `default_storage`. With `--create`, creates the bucket only on a 404, never on 403 or other errors. Docker compose runs it with `--create`; in production run it without, as a smoke test. |

Tests: `tests/test_ensure_bucket.py` (S3 client mocked).

## Who owns what
No credentials. It uses the storage credentials from settings.

## Gotchas
- **Never use `--create` against production.** The R2 bucket is created in the dashboard with
  EU jurisdiction. A bucket created by the API would default to the wrong jurisdiction.

## Open items
None.
