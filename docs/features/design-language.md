# Design language (Benrey)

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live (admin theme, login, dashboard greeting, error pages) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | `config/settings.py` (`UNFOLD`), `core/static/core/`, `core/admin.py`, `core/admin_ui.py`, `templates/` |
| **Cost**     | $0 (fonts are SIL OFL 1.1, self-hosted) |
| **Depends on** | [admin-ui.md](admin-ui.md), [../../DESIGN.md](../../DESIGN.md), [../../PRODUCT.md](../../PRODUCT.md) |

## What
The admin wears benrey.io's design language:
- dark only, with one acid-lime accent;
- wide oblique display type for page titles;
- Geist for UI and uppercase Geist Mono for labels;
- the source's conic card edge;
- one signature move: the **lit line**, the glowing lime tick from benrey.io's method timeline. Here it marks the active sidebar item.

The full system is in the root [DESIGN.md](../../DESIGN.md), and the product context in [PRODUCT.md](../../PRODUCT.md). Both are read by the impeccable design skill.

Built 2026-10-15 with three Claude Code design skills:
- **dembrandt:** measured the source tokens, ran a WCAG/button/form/status checklist, and the drift check.
- **impeccable:** Operate-mode rules, the craft floor and the detector.
- **taste-skill:** the redesign audit and the real-browser inspector.

## Why
The project is a take-home for Benrey, so the UI speaks their visual language while staying Django's own generated admin. On a working tool the world may lend only type, palette, density and one signature move (impeccable's Operate rule). The layout, navigation and controls stay standard.

**Rejected:**
- **Overriding Unfold's templates wholesale:** every weekly Unfold release would need a merge. Only two one-block overrides exist (`templates/admin/`).
- **A light-mode variant:** Benrey is dark only.
- **Google Fonts:** replaced by self-hosted files, so there's no third-party request and the Phase 5 CSP is simpler.
- **Page-load entrance animations** (the first version had them): an Operate surface loads into a task. Motion is state only, 120–180 ms.
- **Unfold's model search (`COMMAND.search_models`):** it lists `str(obj)` across every searchable model, which would bypass per-role field hiding once the ticket admins exist.
- **Benrey's own logo, 3D renders and licensed Base Neue font:** they're the brand's assets.

## How it's set up
- **`UNFOLD` in `config/settings.py`:**
  - `THEME="dark"`, `BORDER_RADIUS="8px"`;
  - `COLORS`: base ramp (900 #060606 page, 800 #232523, 700 #3c3c3c) and lime primary ramp (600 #c3ff00 fills, 500 #cbfb2e accents, 400 hover);
  - `STYLES`: `core/theme.css`;
  - `SITE_FAVICONS`: `favicon.svg`;
  - `LOGIN.image`: `login-panel.svg`;
  - `SITE_URL=None` (no dead "Return to site" link);
  - `ENVIRONMENT`: `core.admin_ui.environment_callback` (a "Local" badge when `DEBUG`);
  - `SIDEBAR.show_search`.
- **`core/admin.py`:** `User` and `Group` re-registered with Unfold's admin classes and forms, so their pages get the themed widgets. The user list adds `last_login`.
- **`templates/admin/base.html`:** a skip link. **`templates/admin/index.html`:** the dashboard greeting.
- **`templates/404.html` / `500.html`:** standalone branded error pages.
- **`.impeccable/config.json`:** the lit-line glow is a sanctioned exception for impeccable's `dark-glow` rule, scoped to `theme.css` and `_error.html`.
- **Tests:** `tests/test_admin_theme.py` covers:
  - the dark theme, lime variable, favicon, login art and self-hosted fonts;
  - no "Return to site";
  - the skip link before the sidebar;
  - the greeting;
  - Unfold auth admins;
  - the branded 404;
  - the environment badge only under `DEBUG`.

## Who owns what
No credentials.

## Gotchas
- **`STYLES` load before Unfold's own CSS.** `theme.css` still wins because Unfold's Tailwind rules sit in cascade layers and this file is unlayered. Don't wrap it in `@layer`.
- **Specificity still matters between my own rules.** `.bg-primary-600 .text-white` once hid the action bar's "Run" text. Check computed colours, not just screenshots.
- **Unfold renders checkboxes and switches as `appearance-none` inputs.** Switches are the `.rounded-full` ones; target them that way.
- **Unfold renders hex colours as `rgb()`** in its `--color-*` variables.
- **The impeccable detector can't sign in.** Scan signed-in pages by saving them with their CSS inlined. Its remaining findings there are Unfold internals (filter-sheet nesting, `h1` → `h3` in filters, hidden command-palette `kbd`s).
- **The impeccable plugin's hooks** run its detector after edits to UI files and add `.impeccable/hook.cache.json` (gitignored).

## Open items
- [ ] Phase 1: ticket status and priority badges. Lime for open/active only; red, amber, green and blue keep their single meanings.
- [ ] Phase 1: check the role-restricted pages (Agent) against [DESIGN.md](../../DESIGN.md).
- [ ] Add `latin-ext` font files if customer names need them.
