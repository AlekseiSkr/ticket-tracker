"""Django settings. Everything environment-specific comes from env vars (see .env.example)."""

from pathlib import Path

import dj_database_url
import sentry_sdk
from django.templatetags.static import static

from config.env import env_bool, env_int, env_list, optional_env, require_env

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = require_env("DJANGO_SECRET_KEY")
DEBUG = env_bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", required=True)
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    # Unfold must come before django.contrib.admin so its templates win.
    "unfold",
    "unfold.contrib.filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "tickets",
]

MIDDLEWARE = [
    # Answers /healthz and /readyz before host validation and the HTTPS redirect,
    # because platform health checks hit the machine directly over plain HTTP.
    "core.middleware.HealthCheckMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.ContentSecurityPolicyMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database ---------------------------------------------------------------
# Long-lived app server: keep connections for up to 60 s, below Neon's 300 s idle
# timeout, and health-check them before reuse.
DATABASES = {
    "default": dj_database_url.parse(
        require_env("DATABASE_URL"),
        conn_max_age=env_int("DB_CONN_MAX_AGE", 60),
        conn_health_checks=True,
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Auth -------------------------------------------------------------------
# Django's default hashers (PBKDF2 first). Argon2 takes 100 MB per login attempt, so a few
# parallel anonymous logins would exhaust the 512 MB VM. Old Argon2 hashes are rehashed at login.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
SESSION_COOKIE_AGE = 8 * 60 * 60  # one working day

# --- Files ------------------------------------------------------------------
# Uploads go straight to object storage. Keeping them in memory means nothing is ever written
# to the container's ephemeral disk. Larger requests are refused; 11 MB leaves room for the
# form fields around a 10 MB attachment, so the validator's message covers 10-11 MB.
FILE_UPLOAD_HANDLERS = ["tickets.validators.CappedUploadHandler"]
FILE_UPLOAD_MAX_MEMORY_SIZE = 11 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 11 * 1024 * 1024

STORAGES = {
    "default": {
        "BACKEND": "config.storage.PrivateMediaStorage",
        "OPTIONS": {
            "bucket_name": require_env("S3_BUCKET"),
            "endpoint_url": require_env("S3_ENDPOINT_URL"),
            "public_endpoint_url": optional_env("S3_PUBLIC_ENDPOINT_URL") or None,
            "access_key": require_env("S3_ACCESS_KEY_ID"),
            "secret_key": require_env("S3_SECRET_ACCESS_KEY"),
            "region_name": optional_env("S3_REGION", "auto"),
            "addressing_style": optional_env("S3_ADDRESSING_STYLE", "virtual"),
            "signature_version": "s3v4",
            "default_acl": None,
            "querystring_auth": True,  # private bucket: every URL is presigned
            "querystring_expire": 60,
            "file_overwrite": False,
        },
    },
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- i18n -------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Security (production) ----------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # HSTS preload is impossible for a subdomain of a shared host (fly.dev), so the
    # deploy check that asks for it is silenced on purpose.
    SILENCED_SYSTEM_CHECKS = ["security.W021"]

# --- AI form assistant (core/assistant.py) --------------------------------------
# Any of these blank: the assistant answers with the field's own help text instead.
LLM_BASE_URL = optional_env("LLM_BASE_URL")
LLM_MODEL = optional_env("LLM_MODEL")
GROQ_API_KEY = optional_env("GROQ_API_KEY")

# --- Error monitoring (docs/features/error-monitoring.md) ------------------------
# Off while SENTRY_DSN is blank (local, CI). No personal data: no user, IP, cookies or request
# bodies, so ticket and customer text never leaves for Sentry.
if SENTRY_DSN := optional_env("SENTRY_DSN"):
    sentry_sdk.init(dsn=SENTRY_DSN, send_default_pii=False, max_request_body_size="never")

# --- Logging ------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": optional_env("LOG_LEVEL", "INFO")},
}

# --- Admin theme (Unfold) -----------------------------------------------------
# Benrey design language (docs/features/design-language.md): dark only, one lime accent.
UNFOLD = {
    "SITE_TITLE": "Ticket Tracker",
    "SITE_HEADER": "Ticket Tracker",
    "SITE_SYMBOL": "support_agent",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "THEME": "dark",
    "BORDER_RADIUS": "8px",
    "COLORS": {
        # Dark mode paints the page with 900 and borders with 800/700.
        "base": {
            "50": "#f5f5f4",
            "100": "#ebeceb",
            "200": "#d2d3d1",
            "300": "#b8b9b6",
            "400": "#b1b2b0",
            "500": "#868783",
            "600": "#626561",
            "700": "#3c3c3c",
            "800": "#232523",
            "900": "#060606",
            "950": "#000000",
        },
        # 600 fills buttons (lime signal); 500 is the dark-mode text accent (lime ink).
        "primary": {
            "50": "#fbffef",
            "100": "#f6ffd9",
            "200": "#efffb8",
            "300": "#e6ff8f",
            "400": "#dbff66",
            "500": "#cbfb2e",
            "600": "#c3ff00",
            "700": "#a3d600",
            "800": "#7a9f00",
            "900": "#536c00",
            "950": "#2c362a",
        },
        "font": {
            "subtle-dark": "#a3a4a0",  # 4.5:1+ on the raised greys
            "default-dark": "#b8b9b6",
            "important-dark": "#ebeceb",
        },
    },
    # Fonts are self-hosted from core/static/core/fonts/ (declared in theme.css).
    "STYLES": [lambda request: static("core/theme.css")],
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "any",
            "type": "image/svg+xml",
            "href": lambda request: static("core/favicon.svg"),
        },
    ],
    # "/" only redirects back to the admin, so a "Return to site" link would be a dead loop.
    "SITE_URL": None,
    "LOGIN": {
        "image": lambda request: static("core/login-panel.svg"),
        "form": "core.forms.RateLimitedLoginForm",  # 10 failures per IP, then 15 min
    },
    "ENVIRONMENT": "core.admin_ui.environment_callback",
    # Model search (COMMAND.search_models) stays off: it lists str(obj) for every searchable
    # model, which would bypass per-role field hiding once the ticket admins exist.
    "SIDEBAR": {"show_search": True, "show_all_applications": True},
}
