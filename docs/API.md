# API Specification

## Endpoints

### 1. Health Check
- **Path**: `GET /api/health/`
- **Status Code**: `200 OK`
- **Response**: `{"status": "ok"}`

---

### 2. Geocoding Search
- **Path**: `GET /api/geocode/?q={query}`
- **Query Parameters**: `q` (string, required, minimum 2 characters)
- **Status Code**: `200 OK`
- **Response Example (`q=Chicago`)**:
```json
{
  "results": [
    { "label": "Chicago, Illinois, United States", "lat": 41.87556, "lng": -87.62442 },
    { "label": "Chicago Heights, Illinois, United States", "lat": 41.50628, "lng": -87.63571 }
    /* [8 additional matching location results trimmed] */
  ]
}
```

---

### 3. Trip Weather Risk Analysis
- **Path**: `POST /api/analyze/`
- **Headers**: `Content-Type: application/json`
- **Request Body Example**:
```json
{
  "origin": { "lat": 41.8781, "lng": -87.6298, "label": "Chicago, IL" },
  "destination": { "lat": 39.7392, "lng": -104.9903, "label": "Denver, CO" },
  "departure_time": "2026-10-15T08:00:00Z",
  "load_weight_lb": 35000,
  "checkpoint_interval_miles": 50
}
```

- **Status Code**: `200 OK`
- **Response Example (Generated via `WEATHER_MODE=fixture`)**:
```json
{
  "request_id": "c7110fd8-0152-4735-a6e5-22d4f296d194",
  "weather_mode": "fixture",
  "interval_miles": 50,
  "routes": [
    {
      "id": "r3",
      "label": "Alternative 2",
      "distance_miles": 1056.4,
      "duration_seconds": 57800,
      "geometry": {
        "type": "LineString",
        "coordinates": [[-87.62977, 41.8781], [-87.7198, 41.8064] /* [1,420 coordinate pairs trimmed] */]
      },
      "metrics": {
        "no_travel_miles": 200.0,
        "severe_miles": 100.0,
        "high_miles": 300.0,
        "avg_risk": 1.81,
        "max_level": "NO_TRAVEL"
      },
      "checkpoints": [
        {
          "index": 0,
          "mile": 0.0,
          "lat": 41.8781,
          "lng": -87.62977,
          "eta": "2026-10-15T08:00:00Z",
          "weather": { "wind_mph": 14.3, "gust_mph": 18.6, "rain_in_hr": 0.0, "snow_in_hr": 0.0 },
          "risk": { "level": "LOW", "score": 0, "drivers": [] }
        }
        /* [21 intermediate checkpoints trimmed for brevity] */
      ],
      "rank": 1,
      "recommended": true
    }
    /* [2 alternate routes (r1, r2) trimmed for brevity] */
  ],
  "recommendation": {
    "route_id": "r3",
    "reasons": ["Optimal route choice balancing weather risk and transit duration."],
    "warnings": ["All available routes encounter No Travel weather conditions. Delaying departure is strongly recommended."]
  },
  "heatmap": {
    "start_time": "2026-10-15T08:00:00Z",
    "hours": 49,
    "points": [
      { "lat": 41.52, "lng": -88.32, "levels": [0, 0, 1, 1, 2, 3, 2, 1, 0 /* 40 hours trimmed */] }
      /* [213 corridor grid points trimmed for brevity] */
    ]
  }
}
```

---

## Error Responses & Status Codes

- **`400 Bad Request` (Validation Error)**:
```json
{
  "error": {
    "code": "VALIDATION",
    "fields": {
      "origin": { "lat": ["Ensure this value is less than or equal to 90.0."] },
      "destination": ["This field is required."]
    }
  }
}
```

- **`422 Unprocessable Entity` (Routing Failure)**:
```json
{
  "error": { "code": "NO_ROUTE", "message": "No truck route found between origin and destination." }
}
```

- **`502 Bad Gateway` (Upstream Provider Failure)**:
```json
{
  "error": { "code": "UPSTREAM", "provider": "open_meteo", "message": "Weather provider returned status 503." }
}
```

---

## Backend Environment Variables

| Variable | Type | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | string | `django-insecure-spotter...` | Cryptographic signing key in Django. |
| `DEBUG` | boolean | `0` (False) | Toggles verbose error pages (`1`/`true` to enable). |
| `ALLOWED_HOSTS` | string | `*` | Comma-separated allowed hostnames. Auto-binds `RAILWAY_PUBLIC_DOMAIN`. |
| `CSRF_TRUSTED_ORIGINS` | string | `""` | Comma-separated origins. Auto-binds `https://${RAILWAY_PUBLIC_DOMAIN}`. |
| `WEATHER_MODE` | string | `live` | `live` queries Open-Meteo; `fixture` uses deterministic storm. |
| `USER_AGENT_CONTACT` | string | `WeatherTruckRouting/1.0...` | Identifying User-Agent sent to external public APIs. |
| `PORT` | integer | `8000` | Port listened to by Gunicorn (injected by Railway). |
