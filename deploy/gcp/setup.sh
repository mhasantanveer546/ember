#!/usr/bin/env bash
# One-time Google Cloud setup for the Ember API. Run in Cloud Shell or any shell with gcloud logged in.
#   PROJECT_ID=my-proj REGION=europe-west1 ./deploy/gcp/setup.sh
# Idempotent: safe to re-run. Creates no database (see docs/GCP.md: Neon is used by default).
set -euo pipefail
: "${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-europe-west1}"
BUCKET="${BUCKET:-${PROJECT_ID}-ember-documents}"
SA="ember-api"
SA_EMAIL="${SA}@${PROJECT_ID}.iam.gserviceaccount.com"
gcloud config set project "$PROJECT_ID" >/dev/null

echo "== Enabling APIs"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com storage.googleapis.com iam.googleapis.com

echo "== Artifact Registry repo"
gcloud artifacts repositories describe ember --location "$REGION" >/dev/null 2>&1 || \
  gcloud artifacts repositories create ember --repository-format=docker --location "$REGION"

echo "== Runtime service account (least privilege)"
gcloud iam service-accounts describe "$SA_EMAIL" >/dev/null 2>&1 || \
  gcloud iam service-accounts create "$SA" --display-name "Ember API runtime"

echo "== Private bucket (uniform access, public access prevented)"
gcloud storage buckets describe "gs://${BUCKET}" >/dev/null 2>&1 || \
  gcloud storage buckets create "gs://${BUCKET}" --location "$REGION" \
    --uniform-bucket-level-access --public-access-prevention
# The API's identity may read/write objects in THIS bucket only.
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member "serviceAccount:${SA_EMAIL}" --role roles/storage.objectAdmin >/dev/null

echo "== Secrets (you will be prompted; input is hidden and never written to disk)"
for NAME in DATABASE_URL REDIS_URL; do
  if ! gcloud secrets describe "$NAME" >/dev/null 2>&1; then
    gcloud secrets create "$NAME" --replication-policy automatic >/dev/null
    read -r -s -p "Value for ${NAME}: " VALUE; echo
    printf '%s' "$VALUE" | gcloud secrets versions add "$NAME" --data-file=- >/dev/null
  fi
done
if ! gcloud secrets describe JWT_SECRET >/dev/null 2>&1; then
  gcloud secrets create JWT_SECRET --replication-policy automatic >/dev/null
  python3 -c "import secrets;print(secrets.token_urlsafe(48),end='')" | gcloud secrets versions add JWT_SECRET --data-file=- >/dev/null
  echo "JWT_SECRET generated."
fi
for NAME in DATABASE_URL REDIS_URL JWT_SECRET; do
  gcloud secrets add-iam-policy-binding "$NAME" \
    --member "serviceAccount:${SA_EMAIL}" --role roles/secretmanager.secretAccessor >/dev/null
done

cat <<MSG

Done. Next:  PROJECT_ID=$PROJECT_ID REGION=$REGION BUCKET=$BUCKET CORS_ORIGINS=https://<your-web-origin> ./deploy/gcp/deploy.sh
MSG
