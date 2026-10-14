# Ember — Observability (Phase 11)

Three pillars, all built in, no extra services required:

1. **Logs** — one JSON object per line (`LOG_JSON`, default on in production), every line stamped with a `request_id`.
2. **Metrics** — `GET /metrics` (Prometheus text; `?format=json` for humans/scripts).
3. **Error tracking** — unhandled exceptions are logged with full traceback and answered with a JSON 500 carrying the
   `request_id`; set `SENTRY_DSN` (+ `pip install sentry-sdk`) to also ship them to Sentry. PII sending is off.

## Request IDs
Every response has `X-Request-ID`. If the caller sends a sane one (8–64 chars of `[A-Za-z0-9._-]`) it is reused, so a
trace can span web → API; otherwise one is generated. A user who reports "it failed" can give you the id from the
error body or header; `jq 'select(.request_id=="…")'` over the logs shows everything that request did.

## Reading the logs
```json
{"ts":"2026-10-14T04:11:02.311+00:00","level":"INFO","logger":"ember.request","msg":"request",
 "request_id":"9f1c…","method":"POST","route":"/workspaces/{workspace_id}/search","status":200,"duration_ms":4.2}
```
`/health` and `/metrics` are not logged or counted (probes would drown real traffic). 5xx logs at ERROR, 429 at WARNING.
Locally (`LOG_JSON=false`) the same fields print as `key=value` after the message.

## Metrics catalogue
Latency metrics are histograms: Prometheus `_bucket/_sum/_count` plus `_recent{quantile=…}` (P50/P95/P99 over the last
2048 samples of that process). **P50** is the typical request; **P95** is what 1 in 20 users feels; **P99** is the tail —
the number to alert on, because averages hide it.

| Metric | Type | Labels | What it tells you / when to worry |
|---|---|---|---|
| `ember_http_request_seconds` | histogram | method, route | End-to-end API latency per route *template*. Alert if P95 of any route stays > 1 s. |
| `ember_http_requests_total` | counter | method, route, status (2xx/4xx/5xx) | Traffic and error mix. A rise in 4xx on login = guessing; 429 = rate limiter firing. |
| `ember_http_errors_total` | counter | method, route | 5xx only. **Alert on any sustained increase** — these are our bugs. |
| `ember_search_seconds` | histogram | kind (keyword/phrase) | The product's core promise. Engine target: P95 well under 100 ms at 10k docs (`docs/SEARCH_PERFORMANCE.md`). |
| `ember_searches_total` | counter | kind, outcome (hit/empty) | Share of empty results — high means missing documents or poor query handling. |
| `ember_autocomplete_seconds` | histogram | – | Trie lookups as the user types; must feel instant (P99 < 50 ms). |
| `ember_uploads_total` | counter | outcome (accepted/duplicate) | Upload volume and how often users re-upload the same file. |
| `ember_upload_failures_total` | counter | reason (validation/storage) | `validation` = users sending bad files (fine, watch spikes); `storage` = bucket/permissions outage (**page someone**). |
| `ember_extraction_seconds` | histogram | kind | Time to pull text from pdf/docx/txt. Large PDFs dominate; informs worker sizing. |
| `ember_extraction_failures_total` | counter | kind | Unreadable/scanned/corrupt files. Persistent rise for one kind = parser regression. |
| `ember_indexing_seconds` | histogram | – | Upload-to-searchable time inside the worker (read + extract + tokenize + index). What "w8 for it to get ready" feels like. |
| `ember_documents_processed_total` | counter | outcome (ready/failed) | Pipeline success rate = ready / (ready+failed). |
| `ember_worker_failures_total` | counter | stage (read/extract/index) | *Where* the pipeline broke: `read` = storage, `extract` = parser, `index` = our engine. |
| `ember_index_rebuild_seconds` | histogram | – | Cost of rebuilding a workspace index from Postgres (cold start, staleness refresh). Grows with corpus size. |
| `ember_index_rebuilds_total` | counter | outcome (ok/failed) | A `failed` rebuild leaves the old index serving (atomic swap) but needs investigation. |

Failed jobs also log at ERROR (`document processing failed`, with `document_id`, `stage`, truncated error, traceback).

## Securing and scraping
`/metrics` is **404 in production unless `METRICS_TOKEN` is set**, and then requires `Authorization: Bearer <token>`
(constant-time compared). Prometheus scrape config:
```yaml
scrape_configs:
  - job_name: ember-api
    scheme: https
    metrics_path: /metrics
    authorization: { credentials: "<METRICS_TOKEN>" }
    static_configs: [{ targets: ["<api-host>"] }]
```
Quick look without Prometheus: `curl -H "Authorization: Bearer $T" "$API/metrics?format=json" | jq '.histograms[] | select(.name=="ember_search_seconds")'`.

## Caveats
- Metrics are **per process and in memory**: they reset on restart and each Cloud Run/Space instance reports separately.
  A separate worker process (`RUN_JOBS_INLINE=false`) has no HTTP port, so its failures are visible in **logs**
  (`ember.worker`) and via the API-side `ember_documents_processed_total` only when jobs run inline. For a separate
  worker, alert on log lines or use Sentry.
- Google Cloud Logging parses JSON lines from stdout automatically (`severity` is read from `level` only if you add a
  field mapping; `request_id` becomes a searchable `jsonPayload` field).
- Quantiles come from a 2048-sample window: accurate for recent behaviour, not a long-term SLO record — use the
  Prometheus buckets for that.
