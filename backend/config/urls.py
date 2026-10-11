"""URL configuration for weather-aware truck routing."""

from django.urls import include, path

try:
    from backend.api import urls as api_urls
except ModuleNotFoundError:
    from api import urls as api_urls

urlpatterns = [
    path("api/", include(api_urls)),
]
