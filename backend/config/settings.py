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

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-spotter-weather-truck-routing-secret")
DEBUG = os.environ.get("DEBUG", "1") == "1"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "django.contrib.contenttypes",
    "corsheaders",
    "rest_framework",
    "backend.api",
]

MIDDLEWARE = [
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
if FRONTEND_DIST_DIR.exists():
    WHITENOISE_ROOT = FRONTEND_DIST_DIR
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
