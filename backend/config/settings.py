"""Django settings for weather-aware truck routing backend."""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent

# Ensure both repo root and backend dir are in sys.path
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# --- Core Security and Environment Configuration ---
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-spotter-weather-truck-routing-secret"
)

# DEBUG: False unless explicitly set to 1/true
DEBUG = os.environ.get("DEBUG", "0").lower() in ("1", "true", "yes")

# ALLOWED_HOSTS: comma-separated list of hosts, default "*"
raw_allowed_hosts = os.environ.get("ALLOWED_HOSTS", "*")
ALLOWED_HOSTS = [h.strip() for h in raw_allowed_hosts.split(",") if h.strip()]

# CSRF_TRUSTED_ORIGINS: comma-separated list of origins (e.g. https://*.up.railway.app)
raw_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in raw_csrf.split(",") if o.strip()]

# Automatically include Railway public domain if provided by Railway environment
railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
if railway_domain:
    if railway_domain not in ALLOWED_HOSTS and "*" not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(railway_domain)
    railway_origin = f"https://{railway_domain}"
    if railway_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(railway_origin)

# Trust the X-Forwarded-Proto header set by Railway reverse proxy for HTTPS termination
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "django.contrib.contenttypes",
    "corsheaders",
    "rest_framework",
    "backend.api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

# Enable WhiteNoise static asset serving if installed
try:
    import whitenoise  # noqa: F401
    MIDDLEWARE.append("whitenoise.middleware.WhiteNoiseMiddleware")
except ImportError:
    pass

MIDDLEWARE.append("django.middleware.common.CommonMiddleware")

ROOT_URLCONF = "backend.config.urls"
WSGI_APPLICATION = "backend.config.wsgi.application"

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise configuration to serve built React frontend from root URL
FRONTEND_DIST_DIR = REPO_ROOT / "frontend" / "dist"
WHITENOISE_ROOT = str(FRONTEND_DIST_DIR)
WHITENOISE_INDEX_FILE = True

# Stateless in-memory cache for weather deduplication
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "weather-truck-routing-cache",
        "TIMEOUT": 1800,  # 30 minutes
    }
}

REST_FRAMEWORK = {
    "UNAUTHENTICATED_USER": None,
}

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
