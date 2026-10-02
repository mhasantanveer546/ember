# Running and testing Ember locally (Windows / Git Bash)

Run every command from the **repo root** (the folder containing `backend/`, `web/`, `search_engine/`) unless a step says `cd`.

## 0. One-time prerequisites
- Python 3.11+ and Node.js 20+ (`python --version`, `node --version`)
- Memurai (Redis for Windows) installed and running (`memurai-cli ping` should print PONG; or check the Memurai service in Services)
- A Neon Postgres connection string

## 1. Install
```bash
git pull
python -m venv .venv
source .venv/Scripts/activate          # Git Bash on Windows
pip install -r backend/requirements.txt
cd web && npm install && cd ..
```

## 2. Configure
```bash
cp .env.example .env                   # repo root
cp web/.env.example web/.env.local
python -c "import secrets; print(secrets.token_urlsafe(48))"   # paste the output as JWT_SECRET
```
Edit `.env`: set `DATABASE_URL` (Neon string, keep `?sslmode=require`) and `JWT_SECRET`. Leave `LOCAL_STORAGE_PATH=./backend/storage_data`.

## 3. Create the tables
```bash
python -m alembic -c backend/alembic.ini upgrade head
```

## 4. Start three terminals (each at the repo root, venv active in 1 and 2)
```bash
# Terminal 1: API
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
# Terminal 2: worker (extracts + indexes uploads)
python backend/scripts/run_worker.py
# Terminal 3: web
cd web && npm run dev
```
Open http://localhost:3000. API docs: http://localhost:8000/docs.

**If the worker misbehaves on Windows**, skip Terminal 2: add `RUN_JOBS_INLINE=true` to `.env`, restart the API. Uploads then process inside the API (slower upload request, dev only).

## 5. Manual test checklist (browser)
1. Register -> you land on the dashboard. Sign out, sign in again.
2. Workspaces -> create "Test".
3. Documents -> drop a .txt/.md/.pdf/.docx. Status goes UPLOADING -> PROCESSING -> INDEXING -> READY without refreshing.
4. Upload the same file again -> "Duplicate". Upload a .exe or a >25 MB file -> clear error.
5. Search a word from the file: highlighted snippet appears. Type 2+ letters -> autocomplete. Try a "quoted phrase".
6. Click a result -> document page shows the text with highlights; use the up/down arrows to jump between matches.
7. Workspace page -> create a folder, move the document into it, rebuild the index.
8. Delete the document -> searching for its words returns nothing.
9. Settings -> switch theme; refresh, it persists.
10. Isolation: register a second user in a private window; they must not see the first user's workspaces.

## 6. Automated tests
```bash
python -m pytest backend -q            # backend (uses in-memory SQLite + fake Redis, no Neon needed)
cd web && npm run lint && npm run typecheck && npm test && npm run build
```
If pytest can't import `search_engine`, run it as `PYTHONPATH=. python -m pytest backend -q` (Git Bash).

## 7. Troubleshooting
| Symptom | Cause / fix |
|---|---|
| Web shows "Can't reach the Ember server" | API not running, or `NEXT_PUBLIC_API_URL` wrong. Restart `npm run dev` after editing `.env.local`. |
| Browser console CORS error | Add your web origin to `CORS_ORIGINS` in `.env`, restart API. |
| Document stuck on UPLOADING | Worker not running (Terminal 2) or Redis/Memurai down. Check the worker output; use `RUN_JOBS_INLINE=true` as a fallback. |
| Document FAILED | Unreadable/scanned PDF or corrupt file. Open the document page and Re-index, or check the worker log. |
| `connection refused` on Redis | Start the Memurai service. |
| Neon error `SSL` / `password authentication failed` | Re-copy the connection string; keep `?sslmode=require`. |
| Search finds nothing right after READY | Wait a second and search again; the API rebuilds its index when it notices new documents. |
