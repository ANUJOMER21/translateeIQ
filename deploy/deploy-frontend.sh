#!/usr/bin/env bash
# Build the React (Vite/nginx) image via Cloud Build and deploy meeting-frontend on Cloud Run.
# VITE_API_URL is baked into the JS bundle at build time.
#
# Usage from repo root:
#   export GCP_PROJECT_ID="your-project-id"
#   export GCP_REGION="us-central1"
#   export VITE_API_URL="https://meeting-api-xxxxx-uc.a.run.app/api"
#   ./deploy/deploy-frontend.sh
#
# Optional overrides:
#   FRONTEND_SERVICE="meeting-frontend"
#   CLOUD_RUN_MAX_INSTANCES="3"
#   IMAGE_TAG="20260101120000"
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PROJECT="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
REGION="${GCP_REGION:-us-central1}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-meeting-frontend}"
REPO="${ARTIFACT_REGISTRY_REPO:-meeting-transcriber}"
TAG="${IMAGE_TAG:-$(date +%Y%m%d%H%M%S)}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/frontend:${TAG}"
API_URL="${VITE_API_URL:?Set VITE_API_URL to your backend API URL, e.g. https://meeting-api-xxxxx-uc.a.run.app/api}"

gcloud config set project "$PROJECT"

echo "==> Cloud Build: ${IMAGE}"
echo "    VITE_API_URL=${API_URL}"
gcloud builds submit "$ROOT/frontend" \
  --config "$ROOT/frontend/cloudbuild.yaml" \
  --substitutions "_VITE_API_URL=${API_URL},_IMAGE=${IMAGE}"

echo ""
echo "==> Deploying frontend: ${FRONTEND_SERVICE}"
gcloud run deploy "$FRONTEND_SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1 \
  --max-instances "${CLOUD_RUN_MAX_INSTANCES:-3}" \
  --port 8080

FRONTEND_URL="$(gcloud run services describe "$FRONTEND_SERVICE" --region "$REGION" --format='value(status.url)')"

echo ""
echo "=== Frontend deployed ==="
echo "URL: ${FRONTEND_URL}"
echo ""
echo "IMPORTANT: Add ${FRONTEND_URL} to CORS_ALLOWED_ORIGINS in deploy/env.backend.yaml"
echo "           then redeploy backend: ./deploy/deploy-backend.sh"
