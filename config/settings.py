"""Django settings. Everything environment-specific comes from env vars (see .env.example)."""

from pathlib import Path

import dj_database_url

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
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
SESSION_COOKIE_AGE = 8 * 60 * 60  # one working day

# --- Files ------------------------------------------------------------------
# Uploads go straight to object storage. Keeping them in memory (max 10 MB) means
# nothing is ever written to the container's ephemeral disk.
FILE_UPLOAD_HANDLERS = ["django.core.files.uploadhandler.MemoryFileUploadHandler"]
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
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

# --- Logging ------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": optional_env("LOG_LEVEL", "INFO")},
}

# --- Admin theme (Unfold) -----------------------------------------------------
UNFOLD = {
    "SITE_TITLE": "Ticket Tracker",
    "SITE_HEADER": "Ticket Tracker",
    "SITE_SYMBOL": "support_agent",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
}
