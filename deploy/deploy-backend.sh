#!/usr/bin/env bash
# Build backend image (Cloud Build) and deploy meeting-api + meeting-worker as separate Cloud Run services.
#
# Usage from repo root:
#   export GCP_PROJECT_ID="your-project-id"
#   export GCP_REGION="us-central1"
#   export BACKEND_ENV_FILE="deploy/env.backend.yaml"
#   export CLOUDSQL_CONNECTION_NAME="project:region:instance"   # if DATABASE_URL uses /cloudsql/...
#   ./deploy/deploy-backend.sh
#
# Optional overrides:
#   API_SERVICE="meeting-api"         # Cloud Run service name for the API
#   WORKER_SERVICE="meeting-worker"   # Cloud Run service name for the worker
#   CLOUD_RUN_MAX_INSTANCES="1"       # API max instances (default 1 when env file set)
#   WORKER_MAX_INSTANCES="5"
#   WORKER_MEMORY="4Gi"
#   WORKER_CPU="2"
#   IMAGE_TAG="20260101120000"        # default: timestamp
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PROJECT="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
REGION="${GCP_REGION:-us-central1}"
API_SERVICE="${API_SERVICE:-meeting-api}"
WORKER_SERVICE="${WORKER_SERVICE:-meeting-worker}"
REPO="${ARTIFACT_REGISTRY_REPO:-meeting-transcriber}"
TAG="${IMAGE_TAG:-$(date +%Y%m%d%H%M%S)}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/backend:${TAG}"

ENV_FILE="${BACKEND_ENV_FILE:-}"
if [[ -z "$ENV_FILE" ]]; then
  echo "ERROR: BACKEND_ENV_FILE is required (e.g. deploy/env.backend.yaml)" >&2
  exit 1
fi
[[ "$ENV_FILE" != /* ]] && ENV_FILE="${ROOT}/${ENV_FILE#./}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: BACKEND_ENV_FILE not found: $ENV_FILE" >&2
  exit 1
fi

gcloud config set project "$PROJECT"

echo "==> Cloud Build: ${IMAGE}  (context: backend/)"
gcloud builds submit "$ROOT/backend" --tag "$IMAGE"

MAX_API="${CLOUD_RUN_MAX_INSTANCES:-1}"
WORKER_MEM="${WORKER_MEMORY:-4Gi}"
WORKER_CPU="${WORKER_CPU:-2}"
WORKER_MAX="${WORKER_MAX_INSTANCES:-5}"

API_DEPLOY=(gcloud run deploy "$API_SERVICE"
  --image "$IMAGE"
  --region "$REGION"
  --platform managed
  --allow-unauthenticated
  --memory 2Gi
  --cpu 2
  --timeout 3600
  --max-instances "$MAX_API"
  --env-vars-file "$ENV_FILE")

WORKER_DEPLOY=(gcloud run deploy "$WORKER_SERVICE"
  --image "$IMAGE"
  --region "$REGION"
  --platform managed
  --no-allow-unauthenticated
  --no-cpu-throttling
  --memory "$WORKER_MEM"
  --cpu "$WORKER_CPU"
  --timeout 3600
  --max-instances "$WORKER_MAX"
  --command ./run-celery-cloud-run.sh
  --env-vars-file "$ENV_FILE")

if [[ -n "${CLOUDSQL_CONNECTION_NAME:-}" ]]; then
  API_DEPLOY+=(--add-cloudsql-instances "$CLOUDSQL_CONNECTION_NAME")
  WORKER_DEPLOY+=(--add-cloudsql-instances "$CLOUDSQL_CONNECTION_NAME")
fi

echo ""
echo "==> Deploying API: ${API_SERVICE}  (max-instances=${MAX_API})"
"${API_DEPLOY[@]}"

echo ""
echo "==> Deploying Worker: ${WORKER_SERVICE}  (memory=${WORKER_MEM}, max-instances=${WORKER_MAX})"
"${WORKER_DEPLOY[@]}"

API_URL="$(gcloud run services describe "$API_SERVICE" --region "$REGION" --format='value(status.url)')"
WORKER_URL="$(gcloud run services describe "$WORKER_SERVICE" --region "$REGION" --format='value(status.url)')"

echo ""
echo "=== Backend deployed ==="
echo "API URL:      ${API_URL}"
echo "Health check: ${API_URL}/api/health/"
echo "Worker URL:   ${WORKER_URL}  (internal — no public traffic)"
echo "Image:        ${IMAGE}"
echo ""
echo "Next step: deploy frontend with VITE_API_URL=${API_URL}/api"
echo "  export VITE_API_URL=${API_URL}/api"
echo "  ./deploy/deploy-frontend.sh"
