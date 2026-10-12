# Multi-stage Dockerfile for Weather-Aware Truck Routing (Railway deployment)

# -----------------------------------------------------------------------------
# Stage 1: Build Frontend (Vite + React + TypeScript)
# -----------------------------------------------------------------------------
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

# Install package dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Build production bundle with live API mode
ENV VITE_USE_MOCK=false
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Production Python Backend & Static Server
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS runner

# Optimize Python execution in container
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install curl for Railway health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies (including gunicorn and whitenoise)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend application source
COPY backend/ ./backend/

# Copy compiled frontend distribution from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Collect Django static assets (if any)
RUN python backend/manage.py collectstatic --noinput || true

# Railway injects the PORT environment variable dynamically
EXPOSE 8000

# Run with Gunicorn WSGI server
CMD ["sh", "-c", "gunicorn backend.config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 4 --timeout 120"]
