# docker/: configuration for local Docker services

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | `docker/`; mounted by `../docker-compose.yml` |
| **Cost**     | $0 |
| **Depends on** | [../docs/features/local-development.md](../docs/features/local-development.md) |

## What
Config files mounted into the supporting containers of the local compose stack. The app's
own image is built from `../Dockerfile`, not from here.

## Why
It keeps service config versioned and out of `docker-compose.yml`.

**Rejected:** inline compose `configs:` blocks, which are harder to read and diff.

## How it's set up
| Path | Role |
|---|---|
| `seaweedfs/` | S3 emulator identities (see [seaweedfs/README.md](seaweedfs/README.md)). |

Related root files:
- `../Dockerfile`: `dev` and `prod` stages, uv, non-root `app` user in prod.
- `../docker-compose.yml`: `db`, `storage` and `web` services.

## Who owns what
No real credentials. Everything here is a local-only placeholder.

## Gotchas
None.

## Open items
None.
