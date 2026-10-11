"""URL routing for API endpoints."""

from django.urls import path
from .views import analyze_view, geocode_view, health_view

urlpatterns = [
    path("health/", health_view, name="health"),
    path("geocode/", geocode_view, name="geocode"),
    path("analyze/", analyze_view, name="analyze"),
]
