# Search performance (Phase 4.2)

Benchmark: `backend/scripts/benchmark_search.py` (run: `cd backend && PYTHONPATH=..:. python scripts/benchmark_search.py`).
Measures the real backend path: index lookup -> candidates -> ranking -> Top-K -> DB fetch -> snippets from stored files.

## Assumptions
- Synthetic Zipf-distributed corpus: 5,000-word vocabulary, 300 words/doc, `.txt` files, Top-K = 10.
- Single process/thread, warm cache, local disk, in-memory SQLite (NOT Neon: network round trips per result are not included).
- Sandbox hardware: 1 CPU, Python 3.12, Linux. Re-run on your machine for your own numbers.

## Results (P50 / P95 ms)
| Query shape | 1,000 docs | 10,000 docs |
|---|---|---|
| 1 rare term | 4.9 / 8.5 | 6.1 / 8.3 |
| 1 common term (largest posting list) | 7.9 / 13.6 | 36.4 / 68.5 |
| 2 mid-frequency terms | 5.8 / 8.8 | 11.7 / 17.1 |
| 3 terms (common + mid) | 10.2 / 12.6 | 61.2 / 88.3 |
| exact phrase (2 words) | 11.2 / 33.2 | 73.3 / 222.4 |

Full index rebuild: 0.72 s (1k docs), 8.3 s (10k docs), about 1,200-1,400 docs/s.
Target P95 < 500 ms: met for every shape at both sizes.

## No full-collection scan
Only documents in the query terms' posting lists are scored
(`tests/test_search_performance.py`: 1 of 501 documents scored for a rare term).

## Known limits / next optimizations
- Common-term and phrase queries grow with posting-list size (10k docs: up to ~220 ms P95). Beyond ~50k docs, consider
  scoring only the best candidates first or caching.
- Rebuild is linear in corpus size and re-extracts every file. Persist tokenized postings if it gets slow.
- Re-run against Neon to include real network latency.
