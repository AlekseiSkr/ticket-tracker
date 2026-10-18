# Configuration and secrets

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live (production secrets set on Fly 2026-10-15) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-18 |
| **Where**    | `config/env.py`, `config/settings.py`, `.env.example`; production values in Fly secrets |
| **Cost**     | $0 |
| **Depends on** | [hosting-fly.md](hosting-fly.md) |

## What
All environment-specific settings come from environment variables. `require_env()` stops
the app at startup with `ImproperlyConfigured` when a required variable is missing or
blank. There is one settings module; nothing in the code checks "which environment am I
in".

## Why
A missing database URL or bucket name must crash the app, not quietly fall back to SQLite
or local disk. Silent fallbacks are a classic production bug, and the brief calls them out.

**Rejected:**
- **Separate `settings/local.py` / `settings/production.py` files:** more files, and
  production behaviour hides in a file that local development never runs.
- **django-environ:** a dependency for ~40 lines of code we can test ourselves.
- **Vercel's sample settings** (`if DATABASE_URL: … else: sqlite`): exactly the silent
  fallback we refuse.

## How it's set up
- **Required variables:**
  - `DJANGO_SECRET_KEY`
  - `DJANGO_ALLOWED_HOSTS`
  - `DATABASE_URL`
  - `S3_ENDPOINT_URL`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`
- **Optional variables:**
  - `DJANGO_DEBUG` (default **false**)
  - `DJANGO_CSRF_TRUSTED_ORIGINS`
  - `S3_PUBLIC_ENDPOINT_URL`, `S3_REGION` (default `auto`), `S3_ADDRESSING_STYLE` (default `virtual`)
  - `DB_CONN_MAX_AGE` (default 60)
  - `LOG_LEVEL`
  - `LLM_BASE_URL`, `LLM_MODEL` (in `fly.toml [env]`) and `GROQ_API_KEY` (a secret). If any is blank,
    the form assistant answers from the field's help text instead of failing.
- **Command-only variables** (read by `seed_users`, not by the app at startup):
  - `DEMO_LEAD_1_PASSWORD`, `DEMO_AGENT_1_PASSWORD`, `DEMO_LEAD_2_PASSWORD`,
    `DEMO_AGENT_2_PASSWORD` (one per reviewer account). Required when the command runs, and they must
    pass Django's password validators.
- **Local:** `.env`, copied from `.env.example`.
- **CI:** placeholder values in `.github/workflows/ci.yml` (`env:`). They are not secrets.
- **Production:**
  - non-secret values go in `fly.toml [env]`
  - secrets via `fly secrets set NAME=value`
  - to generate a secret key: `python -c "import secrets; print(secrets.token_urlsafe(50))"`
- **When `DJANGO_DEBUG` is false**, the following are switched on: HTTPS redirect, secure
  cookies, HSTS (1 year, include subdomains) and `SECURE_PROXY_SSL_HEADER`.

## Who owns what
| Secret | Lives in | Set by |
|---|---|---|
| `DJANGO_SECRET_KEY` (prod) | Fly secrets + password manager | Aleksei |
| `DATABASE_URL` (prod) | Fly secrets + password manager | Aleksei (from the Neon console) |
| `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` (prod) | Fly secrets + password manager | Aleksei (from the R2 API token page) |
| `DEMO_LEAD_1_PASSWORD`, `DEMO_AGENT_1_PASSWORD`, `DEMO_LEAD_2_PASSWORD`, `DEMO_AGENT_2_PASSWORD` (prod) | Fly secrets + password manager; sent to reviewers privately | Aleksei |
| `GROQ_API_KEY` | Fly secrets + password manager (set 2026-10-18) | Aleksei |
| `SENTRY_DSN` (optional; blank keeps Sentry off) | Fly secrets, once the Sentry project exists | Aleksei |
| `FLY_API_TOKEN` (CI deploys) | GitHub → repo Settings → Secrets → Actions | Aleksei |

## Gotchas
- The `prod` Docker stage runs `collectstatic` with **placeholder** env values written into
  the Dockerfile. They exist only for that build step and are never used at runtime.
- `security.W021` (HSTS preload) is silenced on purpose: a subdomain of `fly.dev` can't be
  preloaded.
- CI's gitleaks job scans every commit, so a pasted key fails the build. Push protection
  must also be enabled on the GitHub repo (Settings → Code security).

## Open items
- [x] Create production secrets (done 2026-10-15). The Django secret key was generated
  locally and never displayed.
- [x] Enable GitHub secret scanning push protection (done 2026-10-15).
