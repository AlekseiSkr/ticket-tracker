# Content Security Policy

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live in code (2026-10-18) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-18 |
| **Updated**  | 2026-10-18 |
| **Where**    | `core/middleware.py` (`CSP`, `ContentSecurityPolicyMiddleware`), listed in `config/settings.py` `MIDDLEWARE` |
| **Cost**     | $0 |
| **Depends on** | [admin-ui.md](admin-ui.md), [ai-form-assistant.md](ai-form-assistant.md) |

## What
Every response carries a `Content-Security-Policy` header:
- scripts, styles, fonts, images and fetches come only from the app's own origin;
- inline scripts, plugins and `<base>` tags are blocked;
- forms post only to the app;
- no other site may frame it.

If an injected `<script>` ever reached a page, the browser would refuse to run it.

## Why
The admin shows text that customers and agents type, so a script injection is the attack
that matters. Django escapes output already; the CSP is the second wall.

**Rejected:**
- **django-csp:** a dependency for one header. Django 6.0 has CSP built in, so drop this
  middleware when upgrading.
- **Nonces for inline scripts:** none of our templates and none of Unfold's use inline
  scripts, so there's nothing to allow.

## How it's set up
The policy is the `CSP` string in `core/middleware.py`; the middleware sets it with
`setdefault`, so a view could still send its own. Checked on 2026-10-18 in a browser against
the dashboard, the ticket list, a ticket page, searchable dropdowns and the assistant: no
violations. A test injected inline script and it was blocked. `tests/test_security.py` pins
the script policy.

## Who owns what
No credentials.

## Gotchas
- **`'unsafe-eval'` stays in `script-src`.** Unfold's Alpine.js build evaluates its `x-data`
  expressions. Alpine's CSP build would remove that need, but Unfold ships the standard one.
- **`'unsafe-inline'` stays in `style-src`.** Unfold's templates use `style=` attributes, and
  so do the error pages' inline CSS.
- **When something stops working after a frontend change,** open the browser console. It
  names the blocked source and the directive.

## Open items
- [ ] Optional: send violation reports to Sentry's security endpoint (`report-uri`).
