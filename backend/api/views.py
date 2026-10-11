"""DRF views for geocoding, route analysis, and healthcheck."""

from __future__ import annotations

import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from backend.api.serializers import AnalyzeRequestSerializer
from backend.core.types import LatLng
from backend.providers.base import NoRouteFoundError, ProviderError, WeatherServiceError
from backend.providers.photon import PhotonProvider
from backend.services.analyze import AnalyzeService

logger = logging.getLogger(__name__)

geocode_provider = PhotonProvider()
analyze_service = AnalyzeService()


@api_view(["GET"])
def health_view(request):
    """Health check endpoint."""
    return Response({"status": "ok"})


@api_view(["GET"])
def geocode_view(request):
    """Typeahead geocoding endpoint via Photon."""
    q = request.query_params.get("q", "").strip()
    if not q or len(q) < 2:
        return Response({"results": []})

    try:
        results = geocode_provider.search(q)
        return Response({
            "results": [
                {
                    "label": res.label,
                    "lat": res.lat,
                    "lng": res.lng,
                }
                for res in results
            ]
        })
    except ProviderError as e:
        logger.error("Geocoding failed: %s", e)
        return Response(
            {"error": {"code": e.code, "message": e.message}},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    except Exception as e:
        logger.exception("Unexpected error during geocoding")
        return Response(
            {"error": {"code": "GEOCODE_ERROR", "message": str(e)}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def analyze_view(request):
    """Trip weather-risk routing analysis endpoint."""
    serializer = AnalyzeRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                "error": {
                    "code": "VALIDATION",
                    "fields": serializer.errors,
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    val = serializer.validated_data
    origin = LatLng(lat=val["origin"]["lat"], lng=val["origin"]["lng"])
    destination = LatLng(lat=val["destination"]["lat"], lng=val["destination"]["lng"])
    departure_time = val["departure_time"]
    load_weight_lb = val["load_weight_lb"]
    interval = val["checkpoint_interval_miles"]

    try:
        result = analyze_service.analyze_trip(
            origin=origin,
            destination=destination,
            departure_time=departure_time,
            load_weight_lb=load_weight_lb,
            checkpoint_interval_miles=interval,
        )
        return Response(result, status=status.HTTP_200_OK)

    except NoRouteFoundError as e:
        return Response(
            {"error": {"code": "NO_ROUTE", "message": e.message}},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    except WeatherServiceError as e:
        return Response(
            {
                "error": {
                    "code": "UPSTREAM",
                    "provider": e.provider,
                    "message": e.message,
                }
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )
    except ProviderError as e:
        return Response(
            {"error": {"code": e.code, "message": e.message}},
            status=e.status_code,
        )
    except Exception as e:
        logger.exception("Unexpected error in trip analysis")
        return Response(
            {"error": {"code": "INTERNAL_ERROR", "message": str(e)}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
