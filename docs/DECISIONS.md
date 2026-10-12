# Architecture Decisions & Trade-Offs

## Major Technical Choices

| Area | Chosen Solution | Realistic Alternatives | Rationale for Take-Home | Trade-Off & Future Iteration |
|---|---|---|---|---|
| **Routing Engine** | **Valhalla** (Primary, truck profile) + **OSRM** (Fallback) | Google Routes, Mapbox Directions, HERE Fleet API | Free, zero API keys, supports heavy truck costing and polyline alternate routes. | Public demo servers lack SLA and height/tunnel clearances. In production, host self-hosted Valhalla instances via Docker/Kubernetes. |
| **Weather Engine** | **Open-Meteo API** (Hourly) | NOAA GFS/HRRR, Tomorrow.io, WeatherAPI | High-resolution hourly forecasts, free tier with multi-coordinate batch queries. | 10k daily call limit and lack of radar reflectivity. In production, ingest NOAA HRRR GRIB2 grids directly into a spatial database. |
| **Geocoding** | **Photon by Komoot** (OpenStreetMap) | Mapbox Geocoding, Google Places, Nominatim | Free typeahead without credit cards or strict 1 req/sec limits like Nominatim. | Occasional address ambiguity for rural industrial parks. In production, use commercial postal/geocoding provider or self-hosted Pelias. |
| **Logic Placement** | **Pure Python `backend/core/`** | Django ORM models, Celery tasks, client-side JS | 100% framework-independent; enables blazing fast unit tests (<5s for 111 tests). | Requires explicit DTO dataclasses instead of ORM serializers. Would maintain this clean separation regardless of scale. |
| **Checkpoint Sampling** | **Monotonic ETA Interpolation** | Fixed departure-time weather lookup | Trucks travel 15–20 hours; sampling weather at 8 AM for a checkpoint reached at 11 PM produces false safety. | Assumes constant speed between route summary legs without traffic congestion. With more time, integrate dynamic live traffic slowdowns. |
| **Corridor Heatmap** | **Client-side Precomputed 49h GeoJSON** | Server-side raster tiles, on-demand WebSocket scrub | Precomputing 49 hourly risk arrays allows MapLibre to scrub 0–48h at 60fps with zero network calls. | Initial payload is ~40–80KB larger. With more time, encode hourly values into vector protobuf tiles (MVT) for nationwide scaling. |
| **Frontend Stack** | **React 18 + Vite + TypeScript + MapLibre GL JS** | Next.js, Mapbox GL JS (paid token), Leaflet | Fast HMR, strong typing, free open-source vector maps without billing tokens. | MapLibre bundle is ~1MB minified. With more time, implement route-level code splitting and manual Rollup vendor chunking. |
| **Caching Layer** | **Stateless `LocMemCache`** (30m TTL) | Redis, Memcached, Postgres cache table | Zero external service dependencies; deploys anywhere in 1 container. | Cache clears on process restart and is not shared across multi-process workers. With more time, attach an external Redis instance. |
| **Fixture Mode** | **Deterministic Storm Provider** (`WEATHER_MODE=fixture`) | Recorded HTTP mocks via VCR.py / wiremock | Deterministic storm along I-80/I-76 guarantees consistent hazard escalations for live demos without network rate limits. | Only models the Chicago -> Denver corridor. With more time, make storm centroid and velocity parameterizable via query parameters. |
| **Deployment** | **Single Railway Container** (Gunicorn + WhiteNoise) | Split Vercel frontend + Railway backend | Avoids cross-origin CORS latency, cookie issues, and multiple billing services. | Web dyno serves static assets and API workloads concurrently. With more time, put Cloudflare CDN in front of static assets. |

---

## Known Limitations (Ranked by Importance)

1. **Public API Reliability**: Relying on public community demo instances of Valhalla, OSRM, and Photon can occasionally cause latency spikes or temporary 5xx errors (mitigated by our automatic retry and provider fallback layers).
2. **Simplified Truck Profile**: Routing accounts for cargo weight and truck road classifications, but does not check bridge height clearances, axle weight limits, or HAZMAT restrictions.
3. **In-Memory Cache Volatility**: `LocMemCache` does not persist between container restarts or scale across multiple independent Gunicorn workers.
4. **Traffic Congestion Blindness**: Travel duration relies on commercial routing profiles without live real-time congestion or incident delays.

---

## Reviewer FAQ

**1. Why serve React from Django via WhiteNoise instead of two separate services?**  
A single multi-stage container deployment eliminates CORS configuration errors, avoids domain mismatch issues, simplifies environment variable management, and allows the entire application to be hosted on one Railway dyno within the free resource budget.

**2. How are commercial truck blowover risks calculated?**  
The core risk engine evaluates effective wind (`max(sustained, gusts)`). While 55+ mph is an automatic `NO_TRAVEL` hazard for any vehicle, wind between 45–54 mph escalates to `NO_TRAVEL` if cargo weight exceeds 30,000 lbs, and 35–44 mph escalates to `SEVERE` if weight exceeds 40,000 lbs.

**3. Why is domain logic isolated in `backend/core/` rather than Django models or views?**  
Keeping geometry sampling, ETA interpolation, and risk scoring in pure Python free of Django dependencies ensures deterministic behavior, enables sub-second test execution, and makes the core logic trivially portable to CLI tools, AWS Lambda, or background task workers.

**4. What happens if the primary Valhalla routing API fails?**  
`RouteService` catches network timeouts and HTTP errors from `ValhallaProvider` and automatically delegates to `OsrmProvider`, ensuring route generation succeeds without surfacing an error to the user.

**5. How does the weather heatmap slider scrub smoothly at 60fps without lag?**  
The backend delivers a 49-hour array of pre-computed risk levels for each corridor point. On arrival, the frontend derives 49 distinct GeoJSON collections; slider scrubs simply swap the active layer data in MapLibre with zero HTTP queries.

**6. Why is there no database service configured in Railway?**  
The entire trip planning and risk calculation pipeline is stateless. Weather deduplication relies on an in-memory 30-minute cache, meaning no persistent database service or migration step is necessary.

**7. How are API rate limits on Open-Meteo avoided for long-haul routes?**  
Coordinates are spatially deduplicated by rounding to a 0.1° grid (~11 km), cached in memory for 30 minutes, and queried in parallel chunks of $\le 50$ coordinates using a 5-worker thread pool.

**8. What determines which route is marked as "Recommended"?**  
Routes are sorted lexicographically by `(no_travel_miles, severe_miles, high_miles, avg_risk, duration_seconds)`. The route with the lowest hazard exposure is recommended; duration serves strictly as a safety tie-breaker.
