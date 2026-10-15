# core/management/: Django management-command package

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | `core/management/` |
| **Cost**     | $0 |
| **Depends on** | [commands/README.md](commands/README.md) |

## What
The package Django scans for `manage.py` commands from the `core` app. The only content is
`commands/`.

## Why
Django requires this two-level layout (`<app>/management/commands/<name>.py`).

**Rejected:** standalone scripts. They'd miss Django settings, the DB connection and storage.

## How it's set up
| Path | Role |
|---|---|
| `__init__.py` | Makes it a package (empty). |
| `commands/` | One file per command (see [commands/README.md](commands/README.md)). |

## Who owns what
No credentials.

## Gotchas
None.

## Open items
None.
