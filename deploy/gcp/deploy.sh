#!/usr/bin/env bash
# Build the API image with Cloud Build and deploy it to Cloud Run.
#   PROJECT_ID=my-proj REGION=europe-west1 CORS_ORIGINS=https://ember.vercel.app ./deploy/gcp/deploy.sh
set -euo pipefail
: "${PROJECT_ID:?set PROJECT_ID}"
: "${CORS_ORIGINS:?set CORS_ORIGINS to your exact web origin(s), comma separated}"
REGION="${REGION:-europe-west1}"
BUCKET="${BUCKET:-${PROJECT_ID}-ember-documents}"
SA_EMAIL="ember-api@${PROJECT_ID}.iam.gserviceaccount.com"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/ember/ember-api:$(git rev-parse --short HEAD 2>/dev/null || date +%s)"

# The Dockerfile needs the repo root as build context (it imports search_engine/).
gcloud builds submit --project "$PROJECT_ID" --region "$REGION" \
  --config deploy/gcp/cloudbuild.yaml --substitutions "_IMAGE=${IMAGE}" .

gcloud run deploy ember-api \
  --project "$PROJECT_ID" --region "$REGION" --image "$IMAGE" \
  --service-account "$SA_EMAIL" --allow-unauthenticated \
  --port 8000 --cpu 1 --memory 1Gi --min-instances 0 --max-instances 3 --concurrency 40 --timeout 120 \
  --set-env-vars "ENVIRONMENT=production,STORAGE_BACKEND=gcs,GCS_BUCKET=${BUCKET},RUN_JOBS_INLINE=true,TRUST_PROXY_HEADERS=true,^@^CORS_ORIGINS=${CORS_ORIGINS}" \
  --set-secrets "DATABASE_URL=DATABASE_URL:latest,REDIS_URL=REDIS_URL:latest,JWT_SECRET=JWT_SECRET:latest"

URL="$(gcloud run services describe ember-api --project "$PROJECT_ID" --region "$REGION" --format 'value(status.url)')"
echo "API: $URL"
echo "Smoke test: python backend/scripts/smoke_test.py --api $URL"
