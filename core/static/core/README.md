# core/static/core/: admin theme assets

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | Served by WhiteNoise at `/static/core/` |
| **Cost**     | $0 |
| **Depends on** | [../../../docs/features/design-language.md](../../../docs/features/design-language.md) |

## What
`theme.css` holds the parts of the Benrey design language that Unfold's colour settings can't express:
- type;
- lime buttons with dark text;
- caption headings;
- card edges;
- focus rings;
- load motion.

`UNFOLD["STYLES"]` in `config/settings.py` loads it on every admin page.

## Why
Static files namespaced under the `core` app need no `STATICFILES_DIRS` entry.

**Rejected:** a project-level `static/` folder, which would mean one more setting for a single file.

## How it's set up
| File | Role |
|---|---|
| `theme.css` | Unlayered overrides on top of Unfold's layered Tailwind CSS. Tokens are listed at the top as custom properties. |

## Who owns what
No credentials.

## Gotchas
- **This folder is public** (`collectstatic` publishes it). Never put anything private here.
- **Don't wrap `theme.css` in `@layer`.** It only wins because it is unlayered.

## Open items
- [ ] None.
