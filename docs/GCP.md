# Ember on Google Cloud (Phase 9) + CI/CD (Phase 10)

Everything here is scripted but **not yet run against a real project** — it needs a GCP account with
billing enabled (Cloud Run, Cloud Build and Artifact Registry require a billing account; usage for a
personal app normally stays inside the free tier, but set a budget alert). First run: expect to fix small things.

## Architecture

```
Browser / Expo app ──HTTPS──▶ Cloud Run (ember-api, FastAPI)
                                 ├─ Secret Manager  → DATABASE_URL, REDIS_URL, JWT_SECRET
                                 ├─ Cloud Storage   → uploaded files (private bucket)
                                 ├─ Neon Postgres   → documents, users, index source of truth
                                 └─ Upstash Redis   → token denylist, rate limits
Web (Next.js) ──▶ Vercel (root dir `web`, NEXT_PUBLIC_API_URL = Cloud Run URL)
```

Cloud SQL / Memorystore are deliberately not used by default: the smallest Cloud SQL instance and any Memorystore
tier cost money every hour even when idle, while Neon and Upstash have free tiers. See "Using Cloud SQL" to switch.

## 9.1 Cloud Run
- A **container** is the app plus its dependencies in one image (`backend/Dockerfile`); Cloud Run runs copies of it.
- The service is **stateless**: no local disk is trusted (files go to Cloud Storage, state to Postgres/Redis), so any
  instance can serve any request and instances can be created/destroyed freely. The in-memory search index is rebuilt
  from Postgres on demand and refreshed when its ready-document count changes (`ensure_index_fresh`), so several
  instances stay correct.
- **Scaling**: 0 → 3 instances, 40 concurrent requests each (`--min-instances 0` = free when idle, ~cold start of a few s).
- **Env vars** are plain config; **secrets** are mounted from Secret Manager (`--set-secrets`).
- The **service account** `ember-api@PROJECT` is the app's identity. It can only read secrets it was granted and
  manage objects in the one bucket.
- Uploads are processed inline (`RUN_JOBS_INLINE=true`). For heavier use, deploy the same image a second time as a
  worker (`python backend/scripts/run_worker.py`, `--no-cpu-throttling`, min 1) and set `RUN_JOBS_INLINE=false`.

## 9.2 Database
Default: keep **Neon** (set `DATABASE_URL` in Secret Manager; `postgresql://…` or `postgresql+psycopg://…` both work).
Migrations run at container start (`alembic upgrade head` in the Dockerfile CMD) — fine for one service; with several
deploy pipelines run them as a separate step instead. Neon keeps point-in-time history on the free tier (short window);
for real data, take regular `pg_dump` backups.

**Using Cloud SQL instead:** create a PostgreSQL instance, add `--add-cloudsql-instances PROJECT:REGION:INSTANCE` to
`deploy.sh`, and use `postgresql+psycopg://USER:PASS@/DB?host=/cloudsql/PROJECT:REGION:INSTANCE`. Unix-socket (private)
connectivity avoids exposing the database to the internet; enable automated backups and PITR; budget ≈ $10+/month.

## 9.3 Cloud Storage
- A **bucket** is a flat namespace of **objects**; our keys `workspaces/<ws>/documents/<doc>/original.<ext>` just contain
  slashes. The database stores only the key.
- The bucket is created private with *public access prevention* and uniform IAM; only the API's service account has access.
- Files are served only through the API after an ownership check. If direct downloads are ever needed, hand out
  short-lived **V4 signed URLs** from the API instead of opening the bucket.
- Backend code: `app/services/storage/gcs_storage.py` (`STORAGE_BACKEND=gcs`, `GCS_BUCKET`), credentials via ADC — no key file.

## 9.4 Secret Manager
`setup.sh` stores `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET` (auto-generated) in Secret Manager and grants only the runtime
account `secretAccessor`. Nothing secret is in GitHub, the Dockerfile, source, or any `NEXT_PUBLIC_*` variable (those are
public in the browser bundle by design). Rotate by adding a new secret version and redeploying.

## 9.5 Web deployment
Vercel (free, no card), root directory `web`, one variable `NEXT_PUBLIC_API_URL=<Cloud Run URL>`. It is baked in at build
time, so changing the API URL needs a redeploy. Then set Cloud Run's `CORS_ORIGINS` to the exact Vercel origin and redeploy
the API (`CORS_ORIGINS=https://… ./deploy/gcp/deploy.sh`). Production boot refuses `localhost` CORS.

## Steps
```bash
gcloud auth login
PROJECT_ID=<your-project> REGION=europe-west1 ./deploy/gcp/setup.sh       # once
PROJECT_ID=<your-project> REGION=europe-west1 CORS_ORIGINS=https://<vercel-origin> ./deploy/gcp/deploy.sh
python backend/scripts/smoke_test.py --api <printed Cloud Run URL>
```
After you have created your account: redeploy with `ALLOW_REGISTRATION=false` (add it to `--set-env-vars`).

## Phase 10 — CI/CD (`.github/workflows`)
- **ci.yml** (every push and PR): backend `pytest` + Docker image build; web lint → typecheck → test → build;
  mobile typecheck; secret scan.
- **deploy-api.yml** (after CI passes on `main`, or manually): authenticates to Google with **Workload Identity
  Federation** (no JSON key in GitHub), runs `deploy.sh`, then a `/health` check. It is inert until you set these repository
  *variables* (Settings → Secrets and variables → Actions → Variables): `GCP_PROJECT_ID`, `GCP_REGION`, `CORS_ORIGINS`,
  `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_DEPLOYER_SERVICE_ACCOUNT`.
- Web deploys automatically from Vercel's own GitHub integration on every push to `main` (previews on PRs).

One-time WIF setup (replace the placeholders):
```bash
gcloud iam service-accounts create ember-deployer
gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:ember-deployer@$PROJECT_ID.iam.gserviceaccount.com --role roles/run.admin
gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:ember-deployer@$PROJECT_ID.iam.gserviceaccount.com --role roles/cloudbuild.builds.editor
gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:ember-deployer@$PROJECT_ID.iam.gserviceaccount.com --role roles/artifactregistry.writer
gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:ember-deployer@$PROJECT_ID.iam.gserviceaccount.com --role roles/storage.admin
gcloud iam service-accounts add-iam-policy-binding ember-api@$PROJECT_ID.iam.gserviceaccount.com --member serviceAccount:ember-deployer@$PROJECT_ID.iam.gserviceaccount.com --role roles/iam.serviceAccountUser
gcloud iam workload-identity-pools create github --location global
gcloud iam workload-identity-pools providers create-oidc github --location global --workload-identity-pool github \
  --issuer-uri https://token.actions.githubusercontent.com \
  --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition "assertion.repository=='mhasantanveer546/ember'"
gcloud iam service-accounts add-iam-policy-binding ember-deployer@$PROJECT_ID.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/$(gcloud projects describe $PROJECT_ID --format 'value(projectNumber)')/locations/global/workloadIdentityPools/github/attribute.repository/mhasantanveer546/ember"
```
The provider resource name for `GCP_WORKLOAD_IDENTITY_PROVIDER` is
`projects/<project-number>/locations/global/workloadIdentityPools/github/providers/github`.
