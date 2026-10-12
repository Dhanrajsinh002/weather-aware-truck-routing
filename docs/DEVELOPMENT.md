# Local Development Guide

## 1. Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Node.js 18+ or 20+

---

## 2. Backend Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate       # On Linux/macOS
.\.venv\Scripts\Activate.ps1    # On Windows PowerShell

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Run development server (defaults to port 8000)
python backend/manage.py runserver 8000
```

### Backend Environment Variables
Set these via shell export, PowerShell `$env:VAR`, or `.env`:
- `WEATHER_MODE=fixture`: Bypasses Open-Meteo and serves the deterministic Chicago -> Denver storm scenario.
- `DEBUG=1`: Enables verbose Django traceback pages during local development.
- `ALLOWED_HOSTS=*`: Accepts requests from any host.
- `PORT=8000`: Port for production Gunicorn runner.

---

## 3. Frontend Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Configure local environment
cp .env.example .env
# Set VITE_USE_MOCK=false to talk to your local backend

# 4. Start Vite dev server
npm run dev
```
The frontend starts at `http://localhost:5173`.

### Vite Development Proxy
In `frontend/vite.config.ts`, Vite automatically proxies `/api` calls:
```typescript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```
All frontend calls (`fetch('/api/geocode/...')`, `fetch('/api/analyze/...')`) are automatically forwarded to `http://localhost:8000` without triggering CORS issues.

---

## 4. Mock & Fixture Modes

### Frontend Mock Mode (`VITE_USE_MOCK=true`)
In `frontend/.env`, set `VITE_USE_MOCK=true`. The frontend will operate completely offline without a running Django backend, sourcing all route, checkpoint, and heatmap data from `src/mocks/analyze.sample.json` with realistic network latency simulation.

### Backend Fixture Mode (`WEATHER_MODE=fixture`)
Run the backend with `WEATHER_MODE=fixture`. The backend continues querying real routing from Valhalla/OSRM and real typeahead geocoding from Photon, but injects deterministic winter storm weather data along the I-80/I-76 corridor. Ideal for demos and reproducible evaluation without hitting Open-Meteo fair-use limits.

---

## 5. Testing the Production Build Locally

Django serves the compiled React single-page application using WhiteNoise:

```bash
# 1. Build frontend bundle
cd frontend
npm run build

# 2. Return to root and run with Gunicorn (or manage.py runserver)
cd ..
python backend/manage.py runserver 8000
```
- WhiteNoise intercepts `GET /` and serves `frontend/dist/index.html` (`WHITENOISE_INDEX_FILE = True`).
- WhiteNoise serves static assets (`/assets/*`) from `frontend/dist/` (`WHITENOISE_ROOT = str(REPO_ROOT / 'frontend' / 'dist')`).
- `/api/*` requests route directly to Django DRF views.
- Deep links and client-side refreshes fall back to `spa_index_view` in `backend/config/urls.py`.
