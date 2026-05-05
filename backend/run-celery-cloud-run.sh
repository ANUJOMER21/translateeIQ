#!/usr/bin/env sh
# Celery worker for Cloud Run: must bind $PORT (HTTP) while the worker runs.
# See deploy/STEP-BY-STEP-GCP.md — deploy with --command ./run-celery-cloud-run.sh
set -e
cd "$(dirname "$0")"
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings}"

python cloud_run_port_health.py &
exec celery -A config.celery_app worker -l "${CELERY_LOG_LEVEL:-INFO}"
