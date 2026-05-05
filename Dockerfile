# translateeIQ — React (Vite) + Django API in one image for Google Cloud Run.
# Build context must be the repository root (see deploy/deploy-gcp-cloud-run.sh).

FROM node:20-alpine AS frontend
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html vite.config.js postcss.config.js tailwind.config.js ./
COPY public ./public
COPY src ./src
# Same-origin API on Cloud Run: browser calls /api/... on the service hostname.
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
# Whitenoise serves the Vite bundle under Django's STATIC_URL (static/).
ARG VITE_BASE=/static/
ENV VITE_BASE=$VITE_BASE
RUN npm run build

FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY --from=frontend /web/dist ./spa_dist

RUN chmod +x docker-entrypoint.sh run-celery-cloud-run.sh

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV SERVE_SPA=1

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
