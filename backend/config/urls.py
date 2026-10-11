"""URL configuration for weather-aware truck routing."""

from django.urls import include, path

urlpatterns = [
    path("api/", include("backend.api.urls")),
]
