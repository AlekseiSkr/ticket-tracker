# core/static/core/: admin theme assets

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | Served by WhiteNoise at `/static/core/` |
| **Cost**     | $0 |
| **Depends on** | [../../../DESIGN.md](../../../DESIGN.md), [../../../docs/features/design-language.md](../../../docs/features/design-language.md) |

## What
The admin's design-system assets, loaded through `UNFOLD` settings.

## Why
Static files namespaced under the `core` app need no `STATICFILES_DIRS` entry. The fonts are
self-hosted, which drops the Google Fonts dependency the Phase 5 CSP would otherwise have to
allow.

**Rejected:**
- Google Fonts CSS (a third-party request on every page).
- A project-level `static/` folder (one more setting).

## How it's set up
| Path | Role |
|---|---|
| `theme.css` | Unlayered overrides on top of Unfold's layered Tailwind CSS: fonts, lime controls, captions, the lit-line nav, browser surfaces. Tokens are custom properties at the top. |
| `fonts/` | Geist, Geist Mono and Archivo (latin subset, variable woff2) with their `OFL-*.txt` licences, which must ship with the files. |
| `favicon.svg` | A lime square with a ticket stub (`UNFOLD["SITE_FAVICONS"]`). |
| `assistant.js` | The form assistant panel: tracks the last-focused field, posts the question with `X-CSRFToken`, shows the answer as text. |
| `login-panel.svg` | The login side panel: khaki grid and lit line, decorative (`UNFOLD["LOGIN"]["image"]`). |

## Who owns what
No credentials. The fonts are SIL OFL 1.1.

## Gotchas
- **This folder is public** (`collectstatic` publishes it). Never put anything private here.
- **Don't wrap `theme.css` in `@layer`.** It only wins because it is unlayered.
- **The fonts are the latin subset only.** Add `latin-ext` files if names with other diacritics show up.

## Open items
- [ ] None.
