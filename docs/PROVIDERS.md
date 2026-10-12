# Third-Party Providers & Attributions

This project integrates public open-source and open-data APIs. All network access is managed through resilient provider adapters in `backend/providers/` with explicit caching, timeouts, retries, and fallbacks.

---

## 1. Valhalla Routing (Primary)
- **Purpose**: Primary multi-alternate truck route generation with commercial costing and polyline generation.
- **Endpoint**: `https://valhalla.opentripplanner.org/route`
- **File Reference**: [`backend/providers/valhalla.py`](file:///e:/Projects/self_learning/python/weather-aware-truck-routing/backend/providers/valhalla.py)
- **License**: MIT / GPLv3 (Powered by OpenStreetMap data under ODbL)
- **API Key Required**: No (uses public community instance).
- **Rate Limit / Fair Use**: Community shared server; subject to burst traffic throttling.
- **Resilience**: 15.0s timeout with 1 automatic retry on timeout or network error (`ValhallaProvider.get_routes()`). Converts cargo lbs to metric tons (`lb * 0.000453592`) for the `truck` costing model. Decodes precision-6 polyline geometry.
- **Fallback**: If Valhalla returns 5xx or times out, execution seamlessly delegates to `OsrmProvider`.

---

## 2. OSRM Routing (Fallback & Waypoints)
- **Purpose**: Secondary fallback routing engine and waypoint perturbation engine when generating diverse corridors.
- **Endpoint**: `https://router.project-osrm.org/route/v1/driving`
- **File Reference**: [`backend/providers/osrm.py`](file:///e:/Projects/self_learning/python/weather-aware-truck-routing/backend/providers/osrm.py) and [`backend/services/routes.py`](file:///e:/Projects/self_learning/python/weather-aware-truck-routing/backend/services/routes.py)
- **License**: BSD 2-Clause (OpenStreetMap data under ODbL).
- **API Key Required**: No.
- **Rate Limit / Fair Use**: Public demo server; max 1–2 requests per second fair-use guidance.
- **Resilience**: 12.0s timeout with 1 retry. Converts meters to statute miles (`* 0.000621371`). Used by `RouteService` to perturb mid-corridor waypoints ($\pm 0.75^\circ$ latitude) if fewer than 3 unique routes exist.

---

## 3. Open-Meteo Weather API
- **Purpose**: Hourly numerical weather forecasts: sustained wind (`wind_speed_10m`), gusts (`wind_gusts_10m`), rain (`rain + showers`), and snowfall (`snowfall`).
- **Endpoint**: `https://api.open-meteo.com/v1/forecast`
- **File Reference**: [`backend/providers/open_meteo.py`](file:///e:/Projects/self_learning/python/weather-aware-truck-routing/backend/providers/open_meteo.py)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0).
- **API Key Required**: No (free for non-commercial/fair use up to 10,000 daily queries).
- **Caching & Optimization**:
  - **Spatial Deduplication**: Coordinates rounded to 0.1° grid cells (~11 km) via `_round_coord()`.
  - **In-Memory Cache**: `django.core.cache.backends.locmem.LocMemCache` with 30-minute TTL (1800s) prevents repeated queries for the same spatial cell and date.
  - **Batching & Concurrency**: Uncached coordinates chunked into batches of $\le 50$ and queried in parallel using `ThreadPoolExecutor(max_workers=5)`.
  - **Retries**: Exponential backoff on HTTP 429 (rate-limit) or 5xx server errors (1.0s, 2.0s, 4.0s).
- **Fallback**: Setting `WEATHER_MODE=fixture` routes all calls to [`backend/providers/fixture_weather.py`](file:///e:/Projects/self_learning/python/weather-aware-truck-routing/backend/providers/fixture_weather.py) simulating a reproducible winter storm without network dependencies.

---

## 4. Photon Geocoding
- **Purpose**: Typeahead location autocomplete for origin and destination input fields.
- **Endpoint**: `https://photon.komoot.io/api`
- **File Reference**: [`backend/providers/photon.py`](file:///e:/Projects/self_learning/python/weather-aware-truck-routing/backend/providers/photon.py)
- **License**: Apache 2.0 (OpenStreetMap data under ODbL).
- **API Key Required**: No.
- **Rate Limit / Fair Use**: Public community service.
- **Resilience**: 10.0s timeout with custom `User-Agent`.
- **Fallback**: If network fails, queries match against local `MOCK_GEOCODE_FALLBACK` comprising major freight hubs (Chicago, Denver, Dallas, Omaha, Des Moines, Kansas City, Salt Lake City, etc.).

---

## 5. OpenFreeMap Map Tiles
- **Purpose**: High-performance vector basemap tiles rendered client-side by MapLibre GL JS.
- **Endpoint**: `https://tiles.openfreemap.org/styles/liberty`
- **File Reference**: [`frontend/src/features/map/MapContainer.tsx`](file:///e:/Projects/self_learning/python/weather-aware-truck-routing/frontend/src/features/map/MapContainer.tsx)
- **License**: Open-source / CC BY (OpenStreetMap data under ODbL).
- **API Key Required**: No.

---

## Required Attribution Text (Rendered in UI)

As implemented in [`frontend/src/components/Header.tsx`](file:///e:/Projects/self_learning/python/weather-aware-truck-routing/frontend/src/components/Header.tsx) and the MapLibre control attribution bar:

> *Map data © OpenStreetMap contributors | Tiles by OpenFreeMap | Weather data by Open-Meteo | Routing by Valhalla & OSRM | Search by Photon*
