# Deploying Ember (free-tier path, no credit card)

```
Browser ──HTTPS──> Vercel (Next.js web)
                      │  NEXT_PUBLIC_API_URL
                      ▼
                 Render (FastAPI, Docker) ──> Neon (Postgres)
                      │                  ├──> Upstash (Redis: logout denylist, job records)
                      │                  └──> S3-compatible bucket (document files)
```

**Why these choices:** all have a free tier that doesn't need a card at sign-up (confirm on each signup page, plans change).
Google Cloud (the Phase 9 plan) needs a billing account, so it stays an option for later; the code is already portable (Docker image + S3 storage).

## What the free tier means in practice
- Render's free web service **sleeps after ~15 min idle**; the first request after that takes 30-60 s. Fine for a personal tool, not for a launch.
- The free plan has **no background worker**, so `RUN_JOBS_INLINE=true`: uploads are processed inside the upload request (a big PDF makes the upload take a few seconds).
- Render's disk is **wiped on every restart**, which is why files go to an S3 bucket and the search index is rebuilt from it automatically (verified: restart, then search still works).
- One API instance only (the search index is held in memory per process).

## 0. Before you start
Push the repo (already on GitHub) and have: a Neon database (you do), a GitHub login.

## 1. Redis (Upstash)
1. upstash.com -> Create database (Redis), pick the region closest to your Render region.
2. Copy the **TCP** connection URL that starts with `rediss://` (not the REST URL). This is `REDIS_URL`.

## 2. File storage (any S3-compatible bucket)
Example with **Supabase Storage** (free): create a project -> Storage -> New bucket `ember-documents` (private) ->
Project Settings -> Storage -> **S3 Connection**: note the *endpoint* and *region*, then create an *access key pair*.
(Cloudflare R2 and Backblaze B2 work too; check their sign-up requirements.)
You need: `S3_ENDPOINT_URL`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`.

## 3. API on Render
1. Generate a secret locally: `python -c "import secrets; print(secrets.token_urlsafe(48))"` -> `JWT_SECRET`.
2. render.com -> New -> **Blueprint** -> choose the `ember` repo. Render reads `render.yaml`.
3. Fill the prompted variables:
   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | your Neon string (keep `?sslmode=require`; if it has `&channel_binding=require`, delete that part) |
   | `JWT_SECRET` | the generated secret |
   | `REDIS_URL` | the Upstash `rediss://...` URL |
   | `CORS_ORIGINS` | `https://placeholder.vercel.app` for now (fixed in step 5) |
   | `S3_*` | from step 2 |
4. Deploy. When it is live, open `https://<your-service>.onrender.com/health` -> `{"status":"ok"}`.
   The container runs `alembic upgrade head` on every start, so tables are created automatically.

## 4. Web on Vercel
1. vercel.com -> Add New -> Project -> import the `ember` repo.
2. **Root Directory: `web`**. Framework: Next.js (auto-detected).
3. Environment variable: `NEXT_PUBLIC_API_URL` = your Render URL (no trailing slash).
4. Deploy. Note the URL, e.g. `https://ember-xyz.vercel.app`.

## 5. Connect them (CORS)
Render -> ember-api -> Environment -> set `CORS_ORIGINS` to the exact Vercel origin (`https://ember-xyz.vercel.app`, no trailing slash;
comma-separate if you add a custom domain). Save; Render redeploys.

## 6. Verify
```bash
python backend/scripts/smoke_test.py --api https://<your-service>.onrender.com   # expect 16/16 PASS
```
Then open the Vercel URL, register, create a workspace, upload a file, search.
The smoke test creates throwaway `smoke-*@example.com` users; delete them from Neon (`users` table) if you like.

## 7. Lock it down
After your own account exists, set `ALLOW_REGISTRATION=false` on Render. Until Phase 8 (rate limiting) an open sign-up page on a public URL
lets anyone create accounts and use your storage and quotas.

## Troubleshooting
| Symptom | Fix |
|---|---|
| Render deploy fails at startup with a validation error | Read the log line: usually `JWT_SECRET` < 32 chars, `CORS_ORIGINS` still contains `localhost`, or `S3_*` missing |
| Browser console: CORS error | `CORS_ORIGINS` doesn't exactly equal the site origin (scheme + host, no path, no trailing slash) |
| Web says "Can't reach the Ember server" | `NEXT_PUBLIC_API_URL` wrong; it is baked in at build time, so **redeploy Vercel** after changing it |
| First request very slow | Render free tier waking up; wait ~1 min |
| Upload fails with a 5xx | Check Render logs for S3 errors (endpoint, bucket name, keys, region) |
| Documents vanish after redeploy | `STORAGE_BACKEND` isn't `s3`, so files were on the ephemeral disk |
| Logout / token errors | Redis URL wrong (must be `rediss://` TCP URL with the password) |

## Later (Phases 9-10)
Cloud Run + Cloud SQL + Cloud Storage + Secret Manager, GitHub Actions CI/CD, and a real background worker once you move off the free plan
(set `RUN_JOBS_INLINE=false` and run `python backend/scripts/run_worker.py` as a second service).

## No-card alternative: Hugging Face Spaces (backend)

Render now asks for a card. A free Docker Space does not.

1. huggingface.co -> New Space -> SDK **Docker** (Blank), visibility Public or Private. Name it e.g. `ember-api`.
2. Settings -> Variables and secrets: add the same variables as the Render list
   (`ENVIRONMENT=production`, `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `CORS_ORIGINS`,
   `RUN_JOBS_INLINE=true`, `STORAGE_BACKEND=s3`, `S3_*`). Put secrets under *Secrets*.
3. From the repo root: `deploy/huggingface/publish.sh <hf-user>/ember-api`
   (password = a HF access token with write scope).
4. API URL: `https://<hf-user>-ember-api.hf.space` (check `/health`).
   Use it as `NEXT_PUBLIC_API_URL` in Vercel and `--api` in the smoke test.

Free Spaces sleep after ~48h idle and wake on the next request (~1 min).
