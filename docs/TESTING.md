# Testing & Quality Assurance

This document outlines the testing strategy, commands, test coverage, and actual verification counts executed against the codebase.

---

## 1. Test Execution Commands & Real Results

### Backend Suite (`pytest`)
- **Fast Unit & Contract Tests (Excludes Live Network Calls)**:
  ```bash
  pytest -m "not live_smoke"
  ```
  **Actual Result**: `110 passed, 1 deselected in 4.76s` (111 collected).
- **Full Suite (Includes Optional Live Provider Smoke Test)**:
  ```bash
  pytest
  ```
  **Actual Result**: `110 passed, 1 skipped in 3.44s` (`test_open_meteo_live_smoke` skipped when live API not required).

### Frontend Suite (`vitest`, `eslint`, `vite build`)
- **Unit & Logic Tests**:
  ```bash
  cd frontend && npm test
  ```
  **Actual Result**: `3 passed test files, 18 passed tests in 42.14s` (`risk.test.ts`, `validation.test.ts`, `slider.test.ts`).
- **Linter**:
  ```bash
  cd frontend && npm run lint
  ```
  **Actual Result**: Clean exit with `0 errors, 0 warnings`.
- **TypeScript & Production Build**:
  ```bash
  cd frontend && npm run build
  ```
  **Actual Result**: Successful compilation (`tsc && vite build`) in `29.09s` outputting static bundle to `frontend/dist/`.

---

## 2. Backend Test Coverage Breakdown

| Test File | Test Count | What It Covers | Mocked vs Live |
|---|---|---|---|
| `test_risk.py` | 50 tests | Wind (0–70 mph), rain (0–2.0 in/hr), and snow (0–4.5 in/hr) boundary conditions; load blowover escalations (1,000–80,000 lb); rule immutability (load never lowers risk). | Pure Unit (No mocks needed) |
| `test_geo_sampling.py` | 6 tests | Haversine distance, Auto interval rules (`<150->10`, `150-500->25`, `>500->50`), coordinate interpolation, and endpoint preservation. | Pure Unit |
| `test_eta.py` | 5 tests | Monotonic arrival time calculations, duration profiles, start/end anchor guarantees, zero-distance handling. | Pure Unit |
| `test_metrics.py` | 3 tests | Hand-computed Voronoi midpoint segment ownership, distance-weighted `avg_risk`, risk mileage aggregation. | Pure Unit |
| `test_recommend.py` | 7 tests | 5-rule lexicographic preference order (`no_travel_miles -> severe_miles -> high_miles -> avg_risk -> duration`), advisory formatting, all-route `No Travel` warning. | Pure Unit |
| `test_heatmap.py` | 3 tests | 10-mile corridor point sampling, spatial deduplication, 49-hour precomputed hazard level generation. | Pure Unit |
| `test_routes_service.py` | 6 tests | Primary-to-fallback failover, route geometry overlap detection (>90% threshold), waypoint perturbation, route indexing. | Mocked via recorded OSRM JSON |
| `test_valhalla.py` | 4 tests | Metric ton cargo conversion, polyline precision-6 decoding, HTTP 422 error translation. | Mocked via recorded Valhalla JSON |
| `test_open_meteo.py` | 4 tests | Coordinate grid rounding (0.1°), response parsing, 30-minute in-memory caching hit, optional live smoke test. | Recorded JSON + `LocMemCache` |
| `test_photon.py` | 3 tests | Label formatting, geocoder result parsing, fallback to offline freight hubs on network error. | Mocked via recorded Photon JSON |
| `test_weather_interp.py` | 6 tests | Hourly forecast linear interpolation, exact hour checks, forecast horizon clamping (<0h and >168h). | Pure Unit |
| `test_api_analyze.py` | 8 tests | DRF `/api/health/`, `/api/geocode/`, and `/api/analyze/` contracts, validation error formatting (`400`), routing error (`422`), upstream failover (`502`). | DRF APIClient in `fixture` mode |
| `test_types.py` & `test_provider_base.py` | 8 tests | IntEnum integrity, dataclass immutability, exception hierarchy. | Pure Unit |

---

## 3. Boundary-Value Testing for Risk Rules

The risk engine in `backend/core/risk.py` is tested using parametrized boundary tests to verify transition behavior:
- **Wind (mph)**: `24.9` (LOW) vs `25.0` (MODERATE); `34.9` (MODERATE) vs `35.0` (HIGH); `44.9` (HIGH) vs `45.0` (SEVERE); `54.9` (SEVERE) vs `55.0` (NO_TRAVEL).
- **Rain (in/hr)**: `0.0999` (LOW) vs `0.10` (MODERATE); `0.25` (MODERATE) vs `0.2501` (HIGH); `0.50` (HIGH) vs `0.5001` (SEVERE); `1.00` (SEVERE) vs `1.0001` (NO_TRAVEL).
- **Snow (in/hr)**: `0.49` (LOW) vs `0.50` (MODERATE); `1.00` (MODERATE) vs `1.0001` (HIGH); `2.00` (HIGH) vs `2.0001` (SEVERE); `3.00` (SEVERE) vs `3.01` (NO_TRAVEL).
- **Cargo Load Blowover**:
  - `wind=45.0, load=30000` -> SEVERE (no escalation).
  - `wind=45.0, load=30001` -> NO_TRAVEL (escalated).
  - `wind=35.0, load=40000` -> HIGH (no escalation).
  - `wind=35.0, load=40001` -> SEVERE (escalated).
  - Low wind (20 mph) with maximum load (80,000 lb) remains LOW (proving load rules never artificially inflate calm conditions).

---

## 4. Fixture Mode & Deterministic Testing

- **Backend Fixture Mode (`WEATHER_MODE=fixture`)**: Replaces live calls to Open-Meteo with `FixtureWeatherProvider` (`backend/providers/fixture_weather.py`). It generates a deterministic synthetic winter storm centered over western Nebraska and eastern Colorado (I-80/I-76 corridor), testing the full spectrum of `LOW`, `MODERATE`, `HIGH`, `SEVERE`, and `NO_TRAVEL` conditions.
- **Frontend Mock Mode (`VITE_USE_MOCK=true`)**: Allows frontend development without a running backend by serving `frontend/src/mocks/analyze.sample.json`.
