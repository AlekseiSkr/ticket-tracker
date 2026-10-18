# config/: Django project configuration

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-18 |
| **Where**    | `config/` (the Django project package; `DJANGO_SETTINGS_MODULE=config.settings`) |
| **Cost**     | $0 |
| **Depends on** | [../docs/features/configuration-and-secrets.md](../docs/features/configuration-and-secrets.md), [../docs/features/file-storage.md](../docs/features/file-storage.md) |

## What
The Django project itself: settings, URL routing, the WSGI/ASGI entry points, the
env-variable helpers and the object-storage backend. No business logic lives here.

## Why
- **One settings module driven entirely by environment variables**, so local, CI and
  production run the same code. Only the values differ.
- **Required variables fail at startup**, with no silent SQLite or local-disk fallback.

**Rejected:**
- Split `settings/{base,local,production}.py` files
- django-environ (see the configuration doc)

## How it's set up
| File | Role |
|---|---|
| `settings.py` | All settings. Reads env through `env.py`. Sections: database, auth (Django's default PBKDF2), files (memory-only uploads capped at 11 MB, S3 `STORAGES`), static (WhiteNoise), security (switched on when `DJANGO_DEBUG` is false), logging, `UNFOLD` (dark theme, Benrey colour ramps, fonts and `core/theme.css`; see [design-language.md](../docs/features/design-language.md)). |
| `env.py` | `require_env`, `optional_env`, `env_bool`, `env_int`, `env_list`. Raise `ImproperlyConfigured` on missing or invalid values. |
| `storage.py` | `PrivateMediaStorage` (django-storages `S3Storage`). Every URL is presigned, 60 s. `public_endpoint_url` signs URLs for the browser-facing host in local Docker. |
| `urls.py` | `/admin/` plus a `/` redirect to it. Health endpoints are **not** here; they're middleware in `core/`. |
| `wsgi.py` / `asgi.py` | Entry points. Production runs gunicorn on `config.wsgi:application`. |

**Adding a setting:**
1. Read it via `env.py`.
2. Add it to `.env.example` and `.github/workflows/ci.yml` (`env:`).
3. If it's secret, document where it lives in the configuration doc.

## Who owns what
No credentials in this folder. Values come from `.env` (local), CI placeholders, or Fly
secrets (production).

## Gotchas
- **`unfold` must stay above `django.contrib.admin`** in `INSTALLED_APPS`.
- **`HealthCheckMiddleware` must stay first** in `MIDDLEWARE`. Fly health checks are plain
  HTTP and don't follow redirects.
- **Tests run with `DEBUG=False`.** `tests/conftest.py` swaps the static storage, and HTTP
  requests in tests need `secure=True`.
- **`storage.py` relies on two django-storages internals** (`_normalize_name`,
  `client_config`). Re-run `tests/test_storage.py` after upgrading django-storages.

## Open items
- [x] Phase 3: `LLM_BASE_URL`, `LLM_MODEL`, `GROQ_API_KEY` (2026-10-18).
- [ ] Phase 5: CSP, Sentry, admin login rate limit. (Phase 4 OAuth was dropped on 2026-10-18.)
