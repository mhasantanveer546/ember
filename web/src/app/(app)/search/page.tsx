"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { SearchBox } from "@/components/SearchBox";
import { Snippet } from "@/components/Snippet";
import { Card, EmptyState, ErrorNote, LoadingBlock, PageHeader } from "@/components/ui";
import { useTheme } from "@/context/ThemeContext";
import { useWorkspace } from "@/context/WorkspaceContext";
import { fileExtension } from "@/lib/format";
import { searchService } from "@/services/search";
import type { SearchHistoryItem, SearchResponse } from "@/types/api";

function SearchView() {
  const { current, loading: wsLoading } = useWorkspace();
  const { preferences } = useTheme();
  const router = useRouter();
  const params = useSearchParams();
  const urlQuery = params.get("q") ?? "";

  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const ctrl = useRef<AbortController | null>(null);

  const workspaceId = current?.id ?? null;
  const limit = preferences.resultsPerSearch;

  const runSearch = useCallback(
    async (q: string) => {
      if (!workspaceId || !q) return;
      ctrl.current?.abort();
      const c = new AbortController();
      ctrl.current = c;
      setLoading(true);
      setError(null);
      setTypeFilter(null);
      try {
        const r = await searchService.search(workspaceId, q, limit, c.signal);
        setResponse(r);
        searchService.history(workspaceId, 8).then(setHistory).catch(() => {});
      } catch (e) {
        if ((e as Error).name !== "AbortError") setError((e as Error).message);
      } finally {
        if (ctrl.current === c) setLoading(false);
      }
    },
    [workspaceId, limit],
  );

  // Search whenever the URL's ?q changes (covers deep links, history clicks, back/forward).
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- URL is the source of truth for the query
    if (urlQuery) void runSearch(urlQuery);
    else setResponse(null);
  }, [urlQuery, runSearch]);

  useEffect(() => {
    if (!workspaceId) return;
    searchService.history(workspaceId, 8).then(setHistory).catch(() => setHistory([]));
  }, [workspaceId]);

  const submit = (q: string) => router.push(`/search?q=${encodeURIComponent(q)}`);

  if (wsLoading) return <LoadingBlock />;
  if (!current) {
    return <EmptyState title="Create a workspace first" body="Search works inside a workspace." action={<Link href="/workspaces" className="text-accent hover:underline">Go to workspaces</Link>} />;
  }

  const types = response ? Array.from(new Set(response.results.map((r) => fileExtension(r.filename)).filter(Boolean))) : [];
  const shown = response ? response.results.filter((r) => !typeFilter || fileExtension(r.filename) === typeFilter) : [];

  return (
    <>
      <PageHeader title="Search" subtitle={`Searching in ${current.name}`} />
      <SearchBox key={urlQuery} workspaceId={workspaceId} initialValue={urlQuery} autoFocus onSubmit={submit} loading={loading} />

      {error && (
        <div className="mt-6">
          <ErrorNote message={error} onRetry={() => runSearch(urlQuery)} />
        </div>
      )}

      {loading && !response && <LoadingBlock label="Searching…" />}

      {!urlQuery && !loading && (
        <div className="mt-8">
          {history.length > 0 ? (
            <>
              <h2 className="mb-2 text-sm font-medium text-muted">Recent searches</h2>
              <div className="flex flex-wrap gap-2">
                {history.map((h) => (
                  <button key={h.id} onClick={() => submit(h.query_text)} className="rounded-full border border-line bg-surface px-3 py-1 text-sm hover:bg-surface-2">
                    {h.query_text}
                  </button>
                ))}
              </div>
            </>
          ) : (
            <EmptyState title="Search everything you've saved" body='Type a word or phrase you remember. Use quotes for an exact phrase, like "database normalization".' />
          )}
        </div>
      )}

      {response && !error && (
        <section className={`mt-6 transition-opacity ${loading ? "opacity-60" : ""}`} aria-live="polite">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm text-muted">
              {shown.length} {shown.length === 1 ? "result" : "results"}
              {response.is_phrase_search && " · exact phrase"}
            </p>
            {types.length > 1 && (
              <div className="flex gap-1.5" role="group" aria-label="Filter by file type">
                <button onClick={() => setTypeFilter(null)} className={`rounded-full border px-2.5 py-0.5 text-xs ${!typeFilter ? "border-accent bg-accent-soft text-accent" : "border-line"}`}>All</button>
                {types.map((t) => (
                  <button key={t} onClick={() => setTypeFilter(t)} className={`rounded-full border px-2.5 py-0.5 text-xs uppercase ${typeFilter === t ? "border-accent bg-accent-soft text-accent" : "border-line"}`}>{t}</button>
                ))}
              </div>
            )}
          </div>

          {shown.length === 0 ? (
            <EmptyState title="No matches" body="Try fewer or different words. Only documents that are Ready can be searched." />
          ) : (
            <ul className="space-y-3">
              {shown.map((r) => (
                <li key={r.document_id}>
                  <Link href={`/documents/${r.document_id}?q=${encodeURIComponent(response.query)}`} className="block">
                    <Card className="transition-colors hover:border-accent">
                      <p className="font-medium text-accent">{r.filename}</p>
                      <p className="mt-1.5 text-sm leading-relaxed">
                        <Snippet snippet={r.snippet} />
                      </p>
                    </Card>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<LoadingBlock />}>
      <SearchView />
    </Suspense>
  );
}
