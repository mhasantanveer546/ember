# Ember

**Find what you forgot you knew.**

A personal knowledge search platform. Upload documents (PDF, TXT, MD, DOCX),
search across all of them with a classical information-retrieval engine,
and later ask grounded questions over your own knowledge base via RAG.

## Repo layout (monorepo)

```
ember/
├── backend/         FastAPI application (auth, workspaces, documents, search API)
├── search_engine/   Standalone Python search engine (tokenizer, inverted index,
│                    trie, TF-IDF ranking) — no FastAPI dependency, testable alone
├── web/             Next.js web application
├── mobile/          React Native / Expo mobile application
├── docs/            Architecture, API, database, deployment, security docs
└── .github/         CI/CD workflows
```

## Status

Phases 0–7 complete (search engine, backend, document pipeline, search API, web app, mobile app). Next: Phase 8 security hardening; deployment guide ready. To run and test everything locally, see `docs/RUNNING.md`.

## Stack decisions

| Concern            | Choice                | Why (short)                                   |
|--------------------|------------------------|-----------------------------------------------|
| Database           | Neon (Postgres)        | No local Docker needed; branching for dev     |
| Queue / jobs       | Redis (Memurai locally) + RQ | Simple, readable, no card required for local |
| Auth               | Hand-rolled JWT         | Learning the mechanics deliberately           |
| Backend            | FastAPI                 | Async support, typed, auto docs               |
| Search engine      | Hand-rolled (Python)    | Core learning goal of the project             |

Full rationale in `docs/ARCHITECTURE.md`.

Deploying: see `docs/DEPLOYMENT.md` (free-tier path: Vercel + Render + Neon + Upstash + S3-compatible storage).
