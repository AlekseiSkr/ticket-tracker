# templates/: project-level template overrides

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-18 |
| **Where**    | `TEMPLATES["DIRS"]` in `config/settings.py` (searched before app templates) |
| **Cost**     | $0 |
| **Depends on** | [../DESIGN.md](../DESIGN.md), [../docs/features/design-language.md](../docs/features/design-language.md) |

## What
The few templates the project owns: branded error pages and two thin admin overrides (see
[admin/README.md](admin/README.md)).

## Why
Error pages must render without the admin, the database or context processors. The admin
overrides each extend Unfold's template of the same name and add one thing, so Unfold
upgrades keep flowing through.

**Rejected:** copying Unfold's templates wholesale. Every weekly Unfold release would need a merge.

## How it's set up
| File | Role |
|---|---|
| `_error.html` | Standalone base for error pages: self-hosted fonts, inline CSS, a lit line, one link back to the admin. |
| `400.html` / `404.html` / `500.html` | Copy blocks only. Django uses them when `DEBUG` is off. The 400 page mostly means an upload over 11 MB. |
| `admin/` | Admin overrides. |

Tests: `tests/test_admin_theme.py` (404 page, skip link, greeting).

## Who owns what
No credentials.

## Gotchas
- **Locally, with `DEBUG=True`, Django shows its technical 404 page instead.** Check
  `404.html` through the test or with `DEBUG=False`.
- **`500.html` gets no request context.** Keep it free of anything except `{% static %}`.

## Open items
- [ ] None.
