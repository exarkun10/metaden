# ── Stage 1: Build Vue frontend (native platform only) ────────────────────────
FROM --platform=$BUILDPLATFORM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json .
RUN npm install
COPY frontend/ .
RUN npm run build

# ── Stage 2: Final single-container image ─────────────────────────────────────
FROM python:3.12-slim

# Install nginx, supervisor, curl, ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend
COPY backend/ /app/backend/

# Copy built frontend
COPY --from=frontend-build /build/dist /app/frontend/dist

# Copy configs
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/supervisord.conf /etc/supervisor/conf.d/metaden.conf
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Remove default nginx site
RUN rm -f /etc/nginx/sites-enabled/default

# Config and media mount points
RUN mkdir -p /config /media

EXPOSE 8265

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
    CMD curl -f http://localhost:8265/api/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
