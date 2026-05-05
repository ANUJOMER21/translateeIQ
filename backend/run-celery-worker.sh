#!/usr/bin/env bash
# Process meeting uploads (transcribe, agents, Chroma). Requires Redis (see docker-compose.yml).
set -euo pipefail
cd "$(dirname "$0")"
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings}"
exec celery -A config.celery_app worker -l info
