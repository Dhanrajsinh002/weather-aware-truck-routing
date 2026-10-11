"""Route retrieval orchestration with provider fallback and diversity enhancement."""

from __future__ import annotations

import logging
from typing import List, Sequence, Tuple
from backend.core.geo import haversine_distance_miles
from backend.core.types import LatLng, Route
from backend.providers.base import NoRouteFoundError, RoutingError, RoutingProvider
from backend.providers.osrm import OsrmProvider
from backend.providers.valhalla import ValhallaProvider

logger = logging.getLogger(__name__)


def compute_geometry_overlap(coords_a: Sequence[Sequence[float]], coords_b: Sequence[Sequence[float]]) -> float:
    """Calculate approximate fractional overlap between two route geometries.

    Takes sampled points from coords_a and tests proximity to any point in coords_b.
    """
    if not coords_a or not coords_b:
        return 0.0

    # Subsample up to 50 points from coords_a
    step_a = max(1, len(coords_a) // 50)
    samples_a = [coords_a[i] for i in range(0, len(coords_a), step_a)]

    close_count = 0
    proximity_threshold_miles = 5.0

    for pt_a in samples_a:
        lon_a, lat_a = pt_a[0], pt_a[1]
        # Check against coords_b points (subsampled)
        step_b = max(1, len(coords_b) // 50)
        found_close = False
        for j in range(0, len(coords_b), step_b):
            lon_b, lat_b = coords_b[j][0], coords_b[j][1]
            if haversine_distance_miles(lat_a, lon_a, lat_b, lon_b) <= proximity_threshold_miles:
                found_close = True
                break
        if found_close:
            close_count += 1

    return close_count / len(samples_a) if samples_a else 0.0


def deduplicate_routes(routes: Sequence[Route], max_overlap: float = 0.90) -> List[Route]:
    """Filter out routes that have greater than max_overlap with any earlier route."""
    unique: List[Route] = []
    for r in routes:
        is_duplicate = False
        for kept in unique:
            overlap = compute_geometry_overlap(r.geometry, kept.geometry)
            if overlap > max_overlap:
                is_duplicate = True
                break
        if not is_duplicate:
            unique.append(r)
    return unique


def relabel_and_index_routes(routes: Sequence[Route]) -> List[Route]:
    """Sort by duration and assign clean IDs and standard labels."""
    sorted_routes = sorted(routes, key=lambda r: r.duration_seconds)
    result: List[Route] = []
    for idx, r in enumerate(sorted_routes[:3]):
        label = "Fastest" if idx == 0 else f"Alternative {idx}"
        r.id = f"r{idx + 1}"
        r.label = label
        result.append(r)
    return result


class RouteService:
    """Service orchestrating routing across primary and fallback providers."""

    def __init__(
        self,
        primary_provider: RoutingProvider | None = None,
        fallback_provider: RoutingProvider | None = None,
    ):
        self.primary = primary_provider or ValhallaProvider()
        self.fallback = fallback_provider or OsrmProvider()

    def get_diverse_routes(
        self,
        origin: LatLng,
        destination: LatLng,
        weight_lb: float,
    ) -> List[Route]:
        """Fetch up to 3 distinct routes, falling back to OSRM and waypoint perturbation if needed."""
        routes: List[Route] = []

        # 1. Try primary provider (Valhalla)
        try:
            routes = self.primary.get_routes(origin, destination, weight_lb)
        except Exception as e:
            logger.warning("Primary routing provider failed, attempting fallback: %s", e)
            try:
                routes = self.fallback.get_routes(origin, destination, weight_lb)
            except NoRouteFoundError as nr_err:
                logger.warning("Fallback routing found no route: %s", nr_err)
                raise NoRouteFoundError(
                    "No viable driving route could be found between the selected locations. Please check your origin and destination."
                ) from nr_err
            except Exception as fb_err:
                logger.error("Fallback routing provider also failed: %s", fb_err)
                if isinstance(e, NoRouteFoundError):
                    raise NoRouteFoundError(
                        "No viable driving route could be found between the selected locations. Please check your origin and destination."
                    ) from e

                combined_msg = f"{e} {fb_err}".lower()
                if any(k in combined_msg for k in ["noroute", "no route", "unroutable", "impossible route"]):
                    raise NoRouteFoundError(
                        "No viable driving route could be found between the selected locations. Please check your origin and destination."
                    ) from fb_err

                raise RoutingError(
                    "Routing services are temporarily unavailable. Please try again shortly."
                ) from fb_err

        if not routes:
            raise NoRouteFoundError(
                "No viable driving route could be found between the selected locations. Please check your origin and destination."
            )

        # De-duplicate
        unique_routes = deduplicate_routes(routes)

        # 2. If fewer than 3 routes and fallback is OSRM, try via-waypoint perturbation
        if len(unique_routes) < 3 and isinstance(self.fallback, OsrmProvider):
            mid_lat = (origin.lat + destination.lat) / 2.0
            mid_lng = (origin.lng + destination.lng) / 2.0

            perturbations = [
                LatLng(lat=mid_lat + 0.75, lng=mid_lng),
                LatLng(lat=mid_lat - 0.75, lng=mid_lng),
            ]

            for via_pt in perturbations:
                if len(unique_routes) >= 3:
                    break
                try:
                    extra_routes = self.fallback.get_routes(
                        origin=origin,
                        destination=destination,
                        weight_lb=weight_lb,
                        via_waypoints=[via_pt],
                    )
                    for extra in extra_routes:
                        overlap = any(
                            compute_geometry_overlap(extra.geometry, kept.geometry) > 0.85
                            for kept in unique_routes
                        )
                        if not overlap:
                            unique_routes.append(extra)
                            if len(unique_routes) >= 3:
                                break
                except Exception as extra_err:
                    logger.debug("Diversity waypoint routing failed: %s", extra_err)

        return relabel_and_index_routes(unique_routes)
