# API-only image (backend/ as build context). For production with the React SPA on the same Cloud Run
# service, use the repository-root Dockerfile instead (see deploy/SETUP.md).
# translateeIQ API (Django + Gunicorn). Use TRANSCRIPTION_BACKEND=mock on Cloud Run unless you add GPU / large CPU.
FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x docker-entrypoint.sh run-celery-cloud-run.sh

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
