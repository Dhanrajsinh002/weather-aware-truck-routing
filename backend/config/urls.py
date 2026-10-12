"""URL configuration for weather-aware truck routing."""

from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.urls import include, path, re_path

try:
    from backend.api import urls as api_urls
except ModuleNotFoundError:
    from api import urls as api_urls


def spa_index_view(request):
    """Serve the single-page application index.html or a status fallback."""
    dist_index = settings.REPO_ROOT / "frontend" / "dist" / "index.html"
    if dist_index.exists():
        return FileResponse(open(dist_index, "rb"), content_type="text/html")
    return HttpResponse(
        "Weather-Aware Truck Routing API is running. (Build frontend/dist to view the UI)",
        content_type="text/plain",
        status=200,
    )


urlpatterns = [
    path("api/", include(api_urls)),
    re_path(r"^(?!api/).*$", spa_index_view, name="spa-index"),
]
