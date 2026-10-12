# Weather-Aware Truck Routing

An intelligent, full-stack logistics and routing platform designed for commercial freight operations. The system computes multiple diverse highway corridors between origin and destination, samples checkpoints based on trip ETAs, evaluates real-time weather hazards (wind speed, gusts, heavy rain, snowfall, and truck blowover risks adjusted for cargo load weight), and ranks routes using a safety-first recommendation engine. It also provides an interactive MapLibre map and a 0–48 hour weather risk corridor heatmap slider.

---

## 🛠️ Tech Stack

### Backend
- **Framework**: Python 3.12, Django 5.x, Django REST Framework (DRF)
- **Production Server**: Gunicorn, WhiteNoise (serving frontend static assets)
- **External Providers & Fallbacks**:
  - **Routing**: Primary: [Valhalla](https://valhalla.opentripplanner.org/) (truck costing profile, metric ton load parameter, precision-6 polylines); Fallback: [OSRM](https://project-osrm.org/)
  - **Weather**: [Open-Meteo](https://open-meteo.com/) (hourly multi-coordinate batch queries, 0.1° spatial grid deduplication, 30-minute in-memory caching)
  - **Geocoding**: [Photon by Komoot](https://photon.komoot.io/) (OpenStreetMap typeahead with local freight hub fallback)
- **Testing**: `pytest`, `pytest-django`, `httpx`

### Frontend
- **Framework & Tooling**: React 18, TypeScript, Vite
- **Mapping & Visualization**: [MapLibre GL JS](https://maplibre.org/)
- **State & Data Fetching**: TanStack React Query, React Context
- **Icons & Styling**: Lucide React, Modern responsive CSS
- **Testing**: Vitest, React Testing Library, ESLint

### Deployment & Infrastructure
- **Containerization**: Multi-stage `Dockerfile` (Node 20 build stage + Python 3.12 runtime)
- **Hosting**: Railway single-service deployment (no external database service required; stateless application)

---

## ⚙️ Environment Variables

### Backend (`backend/`)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(django-insecure default)* | Django cryptographic signing key. Must be set in production. |
| `DEBUG` | `0` (or `False`) | Set `1` or `true` for local development debug pages. |
| `ALLOWED_HOSTS` | `*` | Comma-separated list of allowed hostnames. Auto-detects `RAILWAY_PUBLIC_DOMAIN`. |
| `CSRF_TRUSTED_ORIGINS` | *(empty)* | Comma-separated list of origins (e.g., `https://my-app.up.railway.app`). Auto-detects Railway domain. |
| `WEATHER_MODE` | `live` | `live` to fetch real-time forecasts from Open-Meteo; `fixture` to use the deterministic Chicago → Denver winter storm simulation. |
| `USER_AGENT_CONTACT` | `WeatherTruckRouting/1.0...` | Contact identifier sent in headers to Open-Meteo and Photon APIs. |
| `PORT` | `8000` | HTTP port used by Gunicorn (injected automatically on Railway). |

### Frontend (`frontend/`)

| Variable | Default | Description |
|---|---|---|
| `VITE_USE_MOCK` | `false` | When `true`, frontend bypasses network API requests and uses local mock data (`src/mocks/analyze.sample.json`). Set to `false` in production. |
| `VITE_API_BASE_URL` | *(empty)* | Optional base URL prefix for API calls. If empty, uses relative paths (`/api/...`) compatible with the Vite dev proxy and WhiteNoise. |

---

## 🚀 How to Run Locally

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Node.js 18+ or 20+
- Git

### 1. Backend Setup

```bash
# From project root:
# 1. Create and activate a virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Start the Django development server
python backend/manage.py runserver 8000
```
Backend API will be live at `http://127.0.0.1:8000/`.

---

### 2. Frontend Setup

In a separate terminal:

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Create or configure local environment
cp .env.example .env
# Ensure VITE_USE_MOCK=false if testing against your local backend

# 4. Start the Vite dev server
npm run dev
```
The application will open at `http://localhost:5173/`. Vite automatically proxies `/api` calls to `http://localhost:8000`.

---

### 3. Running via Docker

You can test the production multi-stage build locally in a single container:

```bash
# Build the production Docker image
docker build -t weather-truck-routing .

# Run the container
docker run -p 8000:8000 -e PORT=8000 -e WEATHER_MODE=live weather-truck-routing
```
Visit `http://localhost:8000` to interact with both the React UI and Django API.

---

## 🧪 How to Run Tests

### Backend Tests
The backend test suite covers boundary values, wind load blowover rules, ETA interpolation, route diversity, and DRF endpoint contracts:

```bash
# Run all unit and integration tests (excluding live external API smoke tests)
pytest -m "not live_smoke"

# Run the complete test suite including live provider network calls
pytest

# Run tests with verbose output
pytest -v
```

### Frontend Tests
The frontend test suite verifies form validation, risk utility helpers, and component states:

```bash
cd frontend

# Run unit tests
npm test

# Run tests in watch mode
npm run test:watch

# Run linter
npm run lint
```

---

## ❄️ How to Use Fixture Mode

Fixture mode provides a reproducible, zero-network scenario modeling a severe winter storm traversing Interstate 80 / Interstate 76 from Chicago, IL to Denver, CO (peaking across western Nebraska and eastern Colorado). This enables testing hazard escalations (`NO_TRAVEL`, `SEVERE`, `HIGH`) and demonstrations without hitting public API rate limits.

### Option A: Backend Fixture Mode (Live Frontend + Simulated Backend)
1. Set the environment variable `WEATHER_MODE=fixture`:
   ```bash
   # Linux/macOS
   export WEATHER_MODE=fixture
   python backend/manage.py runserver 8000

   # Windows (PowerShell)
   $env:WEATHER_MODE="fixture"
   python backend/manage.py runserver 8000
   ```
2. Open the frontend and search for a trip from **Chicago, IL** to **Denver, CO**.
3. All routing and checkpoint calculations will run normally, while the weather service serves deterministic storm data displaying varied risk levels along the corridor.

### Option B: Frontend Mock Mode (Zero-Backend Offline Mode)
If you wish to demo or test the React UI without running the Django backend:
1. In `frontend/.env`:
   ```env
   VITE_USE_MOCK=true
   ```
2. Run `npm run dev`.
3. Geocoding and route calculation will instantly resolve from `frontend/src/mocks/analyze.sample.json` with realistic latency simulation.

---

## 📡 API Summary

### 1. Health Check
- **Endpoint**: `GET /api/health/`
- **Description**: Verifies service availability (used by Railway deployment health checks).
- **Response**: `200 OK`
  ```json
  {
    "status": "ok"
  }
  ```

---

### 2. Location Geocoding
- **Endpoint**: `GET /api/geocode/?q={query}`
- **Description**: Typeahead search for US cities and freight hubs.
- **Query Parameters**:
  - `q` (string, required): Search query (minimum 2 characters).
- **Response**: `200 OK`
  ```json
  {
    "results": [
      {
        "label": "Chicago, Illinois, United States",
        "lat": 41.8781,
        "lng": -87.6298
      }
    ]
  }
  ```

---

### 3. Trip Risk Analysis
- **Endpoint**: `POST /api/analyze/`
- **Description**: Computes up to 3 alternate truck routes, checkpoint ETAs, weather hazard metrics, blowover risk escalations, route ranking, and a 49-hour corridor heatmap.
- **Request Body**:
  ```json
  {
    "origin": {
      "lat": 41.8781,
      "lng": -87.6298,
      "label": "Chicago, IL"
    },
    "destination": {
      "lat": 39.7392,
      "lng": -104.9903,
      "label": "Denver, CO"
    },
    "departure_time": "2026-10-15T08:00:00Z",
    "load_weight_lb": 35000,
    "checkpoint_interval_miles": 25
  }
  ```
  - `checkpoint_interval_miles` accepts: `"auto"`, `10`, `25`, `50`.
  - `load_weight_lb`: Cargo weight between `1` and `100,000` lbs.
- **Response Summary (`200 OK`)**:
  ```json
  {
    "request_id": "c1f7b0e1-7447-49d7-84bc-2d1f421e411b",
    "weather_mode": "live",
    "interval_miles": 25,
    "routes": [
      {
        "id": "r1",
        "label": "I-80 / I-76 (Fastest)",
        "distance_miles": 1003.2,
        "duration_seconds": 54000,
        "geometry": {
          "type": "LineString",
          "coordinates": [[-87.6298, 41.8781], [-87.6748, 41.8422]]
        },
        "metrics": {
          "no_travel_miles": 0.0,
          "severe_miles": 45.2,
          "high_miles": 120.0,
          "avg_risk": 1.45,
          "max_level": "SEVERE"
        },
        "checkpoints": [
          {
            "index": 0,
            "mile": 0.0,
            "lat": 41.8781,
            "lng": -87.6298,
            "eta": "2026-10-15T08:00:00Z",
            "weather": {
              "wind_mph": 18.2,
              "gust_mph": 24.5,
              "rain_in_hr": 0.0,
              "snow_in_hr": 0.0
            },
            "risk": {
              "level": "LOW",
              "score": 0,
              "drivers": []
            }
          }
        ],
        "rank": 1,
        "recommended": true
      }
    ],
    "recommendation": {
      "route_id": "r1",
      "reasons": [
        "Avoids all No-Travel weather hazards.",
        "Shortest overall transit duration."
      ],
      "warnings": []
    },
    "heatmap": {
      "start_time": "2026-10-15T08:00:00Z",
      "hours": 49,
      "points": [
        {
          "lat": 41.52,
          "lng": -88.32,
          "levels": [0, 0, 1, 1, 2, 3, 2, 1]
        }
      ]
    }
  }
  ```

---

## 📜 Business Rules & Risk Scoring

1. **Risk Thresholds**:
   - **Wind (mph)**: `<25` LOW; `[25, 35)` MODERATE; `[35, 45)` HIGH; `[45, 55)` SEVERE; `≥55` NO_TRAVEL.
   - **Rain (in/hr)**: `<0.10` LOW; `[0.10, 0.25]` MODERATE; `(0.25, 0.50]` HIGH; `(0.50, 1.00]` SEVERE; `>1.00` NO_TRAVEL.
   - **Snow (in/hr)**: `<0.5` LOW; `[0.5, 1.0]` MODERATE; `(1.0, 2.0]` HIGH; `(2.0, 3.0]` SEVERE; `>3.0` NO_TRAVEL.
2. **Commercial Load Weight Blowover Escalation**:
   - `Wind ≥ 55 mph`: `NO_TRAVEL` regardless of weight.
   - `Wind 45–54 mph` and `load > 30,000 lb`: Escalates to `NO_TRAVEL`.
   - `Wind 35–44 mph` and `load > 40,000 lb`: Escalates to `SEVERE`.
3. **Route Ranking Criteria**:
   - Evaluated lexicographically by: `(no_travel_miles, severe_miles, high_miles, avg_risk, duration_seconds)`.

---

## 📚 Documentation

For in-depth technical specifications and architectural rationale, refer to the documents in [`docs/`](docs/):

- [Architecture & Request Flow](docs/ARCHITECTURE.md): System mermaid diagram, architectural layers, end-to-end `POST /api/analyze/` flow, and directory tree.
- [Business Assumptions & Rules](docs/ASSUMPTIONS.md): Implemented threshold boundaries, cargo blowover rules, segment ownership, and verifying tests.
- [API Specification](docs/API.md): Endpoint contracts, request/response examples generated via fixture mode, error structures, and environment variables.
- [Third-Party Providers & Attributions](docs/PROVIDERS.md): APIs used (Valhalla, OSRM, Open-Meteo, Photon), licenses, caching, retries, fallbacks, and UI attributions.
- [Architecture Decisions & Trade-Offs](docs/DECISIONS.md): Technical choices, alternatives considered, known limitations, and reviewer FAQ.
- [Testing & Quality Assurance](docs/TESTING.md): Real test pass counts, suite coverage, boundary tests, and fixture mode verification.
- [Local Development Guide](docs/DEVELOPMENT.md): Prerequisites, local backend/frontend setup, Vite proxy, mock mode, and production serving.
