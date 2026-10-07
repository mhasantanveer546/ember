"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { SearchBox } from "@/components/SearchBox";
import { Snippet } from "@/components/Snippet";
import { EmptyState, ErrorNote, FileTag, PageHeader, RowsSkeleton } from "@/components/ui";
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

  // The URL's ?q is the source of truth, so deep links, history clicks and back/forward all work.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- run the search for the URL's query
    if (urlQuery) void runSearch(urlQuery);
    else setResponse(null);
  }, [urlQuery, runSearch]);

  useEffect(() => {
    if (!workspaceId) return;
    searchService.history(workspaceId, 8).then(setHistory).catch(() => setHistory([]));
  }, [workspaceId]);

  const submit = (q: string) => router.push(`/search?q=${encodeURIComponent(q)}`);

  if (wsLoading) return <RowsSkeleton rows={3} />;
  if (!current) {
    return <EmptyState title="Create a workspace first" body="Search works inside a workspace." action={<Link href="/workspaces" className="font-medium underline decoration-ember decoration-2 underline-offset-4">Go to Workspaces</Link>} />;
  }

  const types = response ? Array.from(new Set(response.results.map((r) => fileExtension(r.filename)).filter(Boolean))) : [];
  const shown = response ? response.results.filter((r) => !typeFilter || fileExtension(r.filename) === typeFilter) : [];

  return (
    <>
      <PageHeader title="Search" subtitle={`In ${current.name}`} />
      <SearchBox key={urlQuery} workspaceId={workspaceId} initialValue={urlQuery} autoFocus onSubmit={submit} loading={loading} />

      {error && (
        <div className="mt-8">
          <ErrorNote message={error} onRetry={() => runSearch(urlQuery)} />
        </div>
      )}

      {loading && !response && (
        <div className="mt-8">
          <RowsSkeleton rows={4} />
        </div>
      )}

      {!urlQuery && !loading && (
        <div className="mt-10">
          {history.length > 0 ? (
            <section aria-labelledby="recent">
              <h2 id="recent" className="display mb-3 text-lg">Recent searches</h2>
              <ul className="divide-y divide-line-soft border-y border-line-soft">
                {history.map((h) => (
                  <li key={h.id}>
                    <button onClick={() => submit(h.query_text)} className="block w-full py-2.5 text-left hover:text-ember-text">
                      {h.query_text}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : (
            <EmptyState title="Search everything you’ve saved" body="Type a word or phrase you remember. Put quotes around words to find an exact phrase, like “database normalization”." />
          )}
        </div>
      )}

      {response && !error && (
        <section className={`mt-10 transition-opacity ${loading ? "opacity-50" : ""}`} aria-live="polite">
          <div className="flex flex-wrap items-baseline justify-between gap-3 border-b border-line pb-3">
            <h2 className="text-[15px]">
              <span className="font-semibold tabular-nums">{shown.length}</span> {shown.length === 1 ? "result" : "results"} for{" "}
              <span className="font-semibold">{response.query}</span>
              {response.is_phrase_search && <span className="text-muted"> (exact phrase)</span>}
            </h2>
            {types.length > 1 && (
              <div className="flex gap-4 text-sm" role="group" aria-label="Filter by file type">
                {[null, ...types].map((t) => (
                  <button
                    key={t ?? "all"}
                    onClick={() => setTypeFilter(t)}
                    aria-pressed={typeFilter === t}
                    className={`-mb-[13px] border-b-2 pb-3 ${typeFilter === t ? "border-ember font-semibold text-fg" : "border-transparent text-muted hover:text-fg"}`}
                  >
                    {t ? `.${t}` : "All"}
                  </button>
                ))}
              </div>
            )}
          </div>

          {shown.length === 0 ? (
            <EmptyState title="No matches" body="Try fewer or different words, or check the spelling. Only documents marked Ready can be searched." />
          ) : (
            <ul>
              {shown.map((r) => (
                <li key={r.document_id} className="border-b border-line-soft">
                  <Link href={`/documents/${r.document_id}?q=${encodeURIComponent(response.query)}`} className="group -mx-4 block rounded-xl px-4 py-5 hover:bg-sunken/60">
                    <p className="mb-2 flex items-center gap-2 text-sm font-medium text-muted group-hover:text-fg">
                      <FileTag filename={r.filename} />
                      <span className="truncate">{r.filename}</span>
                    </p>
                    <p className="passage max-w-[68ch]">
                      <Snippet snippet={r.snippet} />
                    </p>
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
    <Suspense fallback={<RowsSkeleton rows={3} />}>
      <SearchView />
    </Suspense>
  );
}
