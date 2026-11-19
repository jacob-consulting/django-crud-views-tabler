"""Settings for the public demo on Render (see render.yaml at the repo root).

Extends the local example settings. Requires the env var SECRET_KEY; RENDER_EXTERNAL_HOSTNAME is set by Render.
"""

import os

from config.settings import *  # noqa: F403
from config.settings import BASE_DIR, MIDDLEWARE

DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]
# The Access check card traces other users' access; on a public demo every visitor can sign in as alex.
CRUD_VIEWS_MANAGE_ACCESS_TRACE = False

# Only the Render host: the local settings' Cloudflare tunnel host does not apply here.
_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
ALLOWED_HOSTS = [_host] if _host else []
CSRF_TRUSTED_ORIGINS = [f"https://{_host}"] if _host else []

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# new list: never mutate the imported base MIDDLEWARE
MIDDLEWARE = [
    MIDDLEWARE[0],  # SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],
    "config.boot.BootIdMiddleware",
    "config.ratelimit.WriteRateLimitMiddleware",
]

STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# single gunicorn worker → a process-local cache is enough for the rate-limit counters
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

ROOT_URLCONF = "config.urls_demo"
DEMO_WRITE_RATES = ("30/m", "300/d")
