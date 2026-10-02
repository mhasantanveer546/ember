# Ember web (Next.js)

Phases 5 and 6: the web application, wired to the real FastAPI backend.

## Run it

```bash
cd web
cp .env.example .env.local      # set NEXT_PUBLIC_API_URL if the API isn't on :8000
npm install
npm run dev                     # http://localhost:3000
```

The backend must allow this origin: set `CORS_ORIGINS=http://localhost:3000` in `backend/.env` (that is the default).

Scripts: `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`.

## Structure

```
src/
├── app/
│   ├── auth/            login, register, forgot-password
│   └── (app)/           signed-in routes: dashboard, search, documents, workspaces, settings
├── components/          AppShell, SearchBox (autocomplete), UploadZone, StatusBadge, ui primitives
├── context/             Auth, Workspace, Theme providers
├── hooks/               useDocuments (status polling), useDebounced
├── services/            apiClient (auth, refresh, errors) + auth/workspaces/documents/search/settings
├── lib/                 formatting, snippet/query highlighting, token storage
└── types/api.ts         types mirroring the backend schemas
```

## Decisions and known limits

- **No API calls in components.** Everything goes through `services/`, which share one client that attaches the
  token, silently refreshes on 401 (one shared refresh for concurrent requests) and turns 401/403/404/409/413/422/429/5xx
  into friendly messages. Raw backend bodies are never shown.
- **Tokens live in localStorage.** Simple and works with the backend's Bearer design, but readable by injected scripts
  (XSS). Mitigations: short-lived access tokens, rotating refresh tokens, React's escaping (snippets are rendered as
  text, never as HTML). Revisit in Phase 8 (httpOnly cookies + CSRF).
- **Status polling** (Phase 6.2): while any document is UPLOADING / PROCESSING / INDEXING the list re-fetches every 2 s and stops
  on its own at READY / FAILED.
- **Preferences are per-browser** (theme, results per search); there is no preferences endpoint yet.
- **Not available yet (backend has no endpoint):** password reset, password change, profile editing. These pages say so
  rather than pretending to work.
- **Search filters** are client-side (file type), because the search API doesn't filter yet.
