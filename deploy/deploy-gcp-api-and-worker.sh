#!/usr/bin/env bash
# Build one image (Cloud Build) and deploy BOTH meeting-api and meeting-worker with the same tag.
#
# From repo root:
#   export GCP_PROJECT_ID="your-project-id"
#   export GCP_REGION="us-central1"
#   export GCP_ENV_FILE="deploy/gcp-run.env.yaml"
#   export CLOUDSQL_CONNECTION_NAME="project:region:instance"   # if DATABASE_URL uses /cloudsql/...
#   ./deploy/deploy-gcp-api-and-worker.sh
#
# Optional overrides:
#   IMAGE_TAG="20260101120000"     # default: timestamp
#   CLOUD_RUN_MAX_INSTANCES="1"    # API only; default 1 when GCP_ENV_FILE is set
#   WORKER_MAX_INSTANCES="5"
#   WORKER_MEMORY="4Gi"
#   WORKER_CPU="2"
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PROJECT="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
REGION="${GCP_REGION:-us-central1}"
API_SERVICE="${CLOUD_RUN_SERVICE:-meeting-api}"
WORKER_SERVICE="${CLOUD_RUN_WORKER_SERVICE:-meeting-worker}"
REPO="${ARTIFACT_REGISTRY_REPO:-meeting-transcriber}"
TAG="${IMAGE_TAG:-$(date +%Y%m%d%H%M%S)}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/${API_SERVICE}:${TAG}"

gcloud config set project "$PROJECT"

echo "==> Cloud Build: ${IMAGE}"
gcloud builds submit "$ROOT" --tag "$IMAGE"

MAX_INSTANCES="${CLOUD_RUN_MAX_INSTANCES:-}"
if [[ -n "${GCP_ENV_FILE:-}" ]]; then
  MAX_INSTANCES="${MAX_INSTANCES:-1}"
else
  MAX_INSTANCES="${MAX_INSTANCES:-10}"
fi

ENV_PATH=""
if [[ -n "${GCP_ENV_FILE:-}" ]]; then
  if [[ ! -f "$GCP_ENV_FILE" ]]; then
    echo "GCP_ENV_FILE not found: $GCP_ENV_FILE (run from repo root or pass a path relative to it)" >&2
    exit 1
  fi
  ENV_PATH="$GCP_ENV_FILE"
  [[ "$GCP_ENV_FILE" != /* ]] && ENV_PATH="${ROOT}/${GCP_ENV_FILE#./}"
else
  echo "ERROR: GCP_ENV_FILE is required for this script (use deploy/gcp-run.env.yaml)." >&2
  exit 1
fi

API_DEPLOY=(gcloud run deploy "$API_SERVICE"
  --image "$IMAGE"
  --region "$REGION"
  --platform managed
  --allow-unauthenticated
  --memory 2Gi
  --cpu 2
  --timeout 3600
  --max-instances "$MAX_INSTANCES"
  --env-vars-file "$ENV_PATH")

if [[ -n "${CLOUDSQL_CONNECTION_NAME:-}" ]]; then
  API_DEPLOY+=(--add-cloudsql-instances "$CLOUDSQL_CONNECTION_NAME")
fi

WORKER_MEM="${WORKER_MEMORY:-4Gi}"
WORKER_CPU="${WORKER_CPU:-2}"
WORKER_MAX="${WORKER_MAX_INSTANCES:-5}"

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
  --env-vars-file "$ENV_PATH")

if [[ -n "${CLOUDSQL_CONNECTION_NAME:-}" ]]; then
  WORKER_DEPLOY+=(--add-cloudsql-instances "$CLOUDSQL_CONNECTION_NAME")
fi

echo "==> Cloud Run deploy: ${API_SERVICE} (max-instances=${MAX_INSTANCES})"
[[ -n "${CLOUDSQL_CONNECTION_NAME:-}" ]] && echo "    (--add-cloudsql-instances ${CLOUDSQL_CONNECTION_NAME})"
"${API_DEPLOY[@]}"

echo "==> Cloud Run deploy: ${WORKER_SERVICE} (max-instances=${WORKER_MAX}, memory=${WORKER_MEM})"
[[ -n "${CLOUDSQL_CONNECTION_NAME:-}" ]] && echo "    (--add-cloudsql-instances ${CLOUDSQL_CONNECTION_NAME})"
"${WORKER_DEPLOY[@]}"

API_URL="$(gcloud run services describe "$API_SERVICE" --region "$REGION" --format='value(status.url)')"
WORKER_URL="$(gcloud run services describe "$WORKER_SERVICE" --region "$REGION" --format='value(status.url)')"

echo ""
echo "=== ${API_SERVICE} ==="
echo "URL:    ${API_URL}"
echo "UI:     ${API_URL}"
echo "Health: ${API_URL}/api/health/"
echo ""
echo "=== ${WORKER_SERVICE} ==="
echo "URL (internal / logs only): ${WORKER_URL}"
echo ""
echo "Image (both services): ${IMAGE}"
echo "Split hosting: set VITE_API_URL to ${API_URL}/api"
