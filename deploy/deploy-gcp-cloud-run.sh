#!/usr/bin/env bash
# Build backend image (Cloud Build) and deploy Cloud Run.
# Required: GCP_PROJECT_ID, gcloud authenticated, Artifact Registry repo (see deploy/SETUP.md).
#
# Recommended: create deploy/gcp-run.env.yaml from gcp-run.env.yaml.example and run:
#   GCP_ENV_FILE=deploy/gcp-run.env.yaml ./deploy/deploy-gcp-cloud-run.sh
#
# Without GCP_ENV_FILE, deploy uses SQLite inside the container (ephemeral) and a random
# DJANGO_SECRET_KEY — fine for a smoke test, not for real data.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

PROJECT="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
REGION="${GCP_REGION:-us-central1}"
SERVICE="${CLOUD_RUN_SERVICE:-meeting-api}"
REPO="${ARTIFACT_REGISTRY_REPO:-meeting-transcriber}"
TAG="${IMAGE_TAG:-$(date +%Y%m%d%H%M%S)}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/${SERVICE}:${TAG}"

gcloud config set project "$PROJECT"

echo "==> Cloud Build (repo root: Vite + Django): ${IMAGE}"
gcloud builds submit "$ROOT" --tag "$IMAGE"

# Chunk uploads are written to instance-local disk; prod env defaults to max 1 API instance unless overridden.
MAX_INSTANCES="${CLOUD_RUN_MAX_INSTANCES:-}"
if [[ -n "${GCP_ENV_FILE:-}" ]]; then
  MAX_INSTANCES="${MAX_INSTANCES:-1}"
else
  MAX_INSTANCES="${MAX_INSTANCES:-10}"
fi

DEPLOY=(gcloud run deploy "$SERVICE"
  --image "$IMAGE"
  --region "$REGION"
  --platform managed
  --allow-unauthenticated
  --memory 2Gi
  --cpu 2
  --timeout 3600
  --max-instances "$MAX_INSTANCES")

if [[ -n "${CLOUDSQL_CONNECTION_NAME:-}" ]]; then
  DEPLOY+=(--add-cloudsql-instances "$CLOUDSQL_CONNECTION_NAME")
fi

if [[ -n "${GCP_ENV_FILE:-}" ]]; then
  if [[ ! -f "$GCP_ENV_FILE" ]]; then
    echo "GCP_ENV_FILE not found: $GCP_ENV_FILE" >&2
    exit 1
  fi
  ROOT_PATH="$(cd "$(dirname "$0")/.." && pwd)"
  ENV_PATH="$GCP_ENV_FILE"
  [[ "$GCP_ENV_FILE" != /* ]] && ENV_PATH="${ROOT_PATH}/${GCP_ENV_FILE#./}"
  DEPLOY+=(--env-vars-file "$ENV_PATH")
else
  SECRET="${DJANGO_SECRET_KEY:-$(openssl rand -hex 32)}"
  echo "==> No GCP_ENV_FILE — using ephemeral SQLite + random DJANGO_SECRET_KEY (smoke test only)"
  # --set-env-vars splits on commas; CORS_ALLOWED_ORIGINS values often contain commas — use YAML.
  SMOKE_ENV="$(mktemp)"
  cleanup_smoke_env() { rm -f "$SMOKE_ENV"; }
  trap cleanup_smoke_env EXIT
  cat > "$SMOKE_ENV" <<EOF
DJANGO_DEBUG: 'False'
TRANSCRIPTION_BACKEND: 'mock'
SERVE_SPA: '1'
ALLOWED_HOSTS: '*'
DJANGO_SECRET_KEY: '${SECRET}'
CORS_ALLOWED_ORIGINS: 'http://localhost:5173,http://127.0.0.1:5173'
EOF
  DEPLOY+=(--env-vars-file "$SMOKE_ENV")
fi

echo "==> Cloud Run deploy: ${SERVICE} (max-instances=${MAX_INSTANCES})"
if [[ -n "${CLOUDSQL_CONNECTION_NAME:-}" ]]; then
  echo "    (--add-cloudsql-instances ${CLOUDSQL_CONNECTION_NAME})"
fi
"${DEPLOY[@]}"

URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
echo ""
echo "Service URL: $URL"
echo "SPA + API:   open $URL (UI) — API health: $URL/api/health/"
echo "Split hosting (Vercel): set VITE_API_URL to ${URL}/api"
echo "Image:       $IMAGE"
