# tickets/management/: management-command package

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-18 |
| **Updated**  | 2026-10-18 |
| **Where**    | `tickets/management/` |
| **Cost**     | $0 |
| **Depends on** | [commands/README.md](commands/README.md) |

## What
The package Django needs to discover the `tickets` app's commands. The commands themselves are in [commands/](commands/README.md).

## Why
Django finds commands only at `<app>/management/commands/`.

**Rejected:** putting the seed in `core/`. It builds ticket-domain data and belongs with the domain.

## How it's set up
| File | Role |
|---|---|
| `__init__.py` | Marks the package. |
| `commands/` | `seed_demo`, `seed_users`. |

## Who owns what
No credentials.

## Gotchas
- None.

## Open items
- [ ] None.
