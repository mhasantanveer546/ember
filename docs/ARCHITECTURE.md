# Ember — Architecture (Phase 0)

## System diagram

```
                         ┌─────────────────────┐
                         │       Web App        │
                         │      Next.js         │
                         └──────────┬───────────┘
                                    │ HTTPS
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI         │
                         │       Backend        │
                         │  (hand-rolled JWT)   │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
          Neon Postgres      Object Storage         Redis (Memurai
       (source of truth)   (local dir → GCS)         locally) + RQ
                                                           │
                                                           ▼
                                                       RQ Workers
                                                           │
              ┌─────────────────────┬────────────────────┘
              ▼                     ▼
                            Ember Search Engine
                                    │
                          ┌─────────┴─────────┐
                          ▼                   ▼
                    Inverted Index           Trie
                          │
                          ▼
                       Ranking (TF-IDF)
```

Mobile (Phase 7) talks to the same FastAPI backend — no separate API.

## Stack decisions and rationale

### Neon vs local Postgres vs other managed Postgres
Chosen: **Neon**. Docker Desktop does not run reliably on this machine
(virtualization/WSL issues), ruling out a local Postgres container.
Neon gives a real Postgres instance with no local daemon, plus branching
for testing schema migrations safely. Tradeoff: network latency on every
query during dev, and an internet dependency to develop at all.

### RQ vs Celery
Chosen: **RQ + Redis**. Celery is more powerful (multiple brokers, complex
routing, scheduled tasks) but has more setup overhead and a steeper
learning curve. RQ is a thin, readable wrapper directly on Redis, which
suits learning the concepts hands-on. Revisit if job complexity grows
significantly (complex retry/backoff chains, multi-queue routing).

### Hand-rolled JWT vs managed auth
Chosen: **hand-rolled JWT**. Managed auth (Clerk/Auth0/Supabase Auth) is
faster and safer for production, but the explicit goal here is to learn
token signing, expiry, refresh flow, and password hashing. Tradeoffs now
owned directly: token revocation, refresh rotation, and secret management
all need to be built correctly rather than provided for free.

### Redis via Memurai (local) vs Docker
Chosen: **Memurai**. Native Windows Redis-compatible server, same protocol
RQ expects, no virtualization required.

## Environment

- Python dependency management: `venv` + `pip` (`requirements.txt`)
- Local `.env` for secrets (Neon connection string, JWT secret, Redis URL) —
  never committed; `.env.example` documents required keys.

## Phase status

- [x] Phase 0 — architecture, repo skeleton
- [ ] Phase 1 — search engine core (tokenizer, inverted index, trie, TF-IDF)
- [ ] Phase 2 — backend + database
- [ ] Phase 3 — document pipeline
- [ ] Phase 4 — search API
- [ ] Phase 5+ — web, mobile, cloud, CI/CD, AI/RAG, hardening
