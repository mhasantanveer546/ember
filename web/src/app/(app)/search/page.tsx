"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { HighlightedText } from "@/components/HighlightedText";
import { SearchBox } from "@/components/SearchBox";
import { Snippet } from "@/components/Snippet";
import { Card, EmptyState, ErrorNote, FileTag, RowsSkeleton, SectionCard, Skeleton } from "@/components/ui";
import { useTheme } from "@/context/ThemeContext";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useDocumentText } from "@/hooks/useDocumentText";
import { useDocuments } from "@/hooks/useDocuments";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { fileExtension, formatBytes, formatRelative } from "@/lib/format";
import { queryTerms } from "@/lib/highlight";
import { searchService } from "@/services/search";
import type { EmberDocument, SearchHistoryItem, SearchResponse, SearchResultItem } from "@/types/api";

const TYPE_LABEL: Record<string, string> = { pdf: "PDF", md: "Markdown", txt: "Text", docx: "Word" };

/** Right-hand preview: a white "page" showing the document around the first match. */
function PreviewPanel({ workspaceId, result, doc, query }: { workspaceId: string; result: SearchResultItem; doc?: EmberDocument; query: string }) {
  const { text, failed, loading } = useDocumentText(workspaceId, result.document_id);
  const terms = useMemo(() => queryTerms(query), [query]);

  const excerpt = useMemo(() => {
    if (!text) return "";
    const lower = text.toLowerCase();
    const first = terms.map((t) => lower.indexOf(t)).filter((i) => i >= 0).sort((a, b) => a - b)[0] ?? 0;
    const start = Math.max(0, first - 160);
    return (start > 0 ? "…" : "") + text.slice(start, start + 1100);
  }, [text, terms]);

  const title = result.filename.replace(/\.[^.]+$/, "");
  return (
    <Card className="p-4">
      <div className="flex items-center gap-3">
        <FileTag filename={result.filename} size="lg" />
        <div className="min-w-0">
          <p className="truncate font-semibold">{result.filename}</p>
          <p className="text-[13px] text-muted">
            {doc ? `${formatBytes(doc.file_size_bytes)} · Added ${formatRelative(doc.created_at)}` : "\u00a0"}
          </p>
        </div>
      </div>

      <div className="paper relative mt-4 max-h-[430px] overflow-hidden rounded-xl bg-[#f8f9f8] p-5 text-[#1a2330]">
        <p className="mb-2 text-[13px] font-bold">{title}</p>
        {loading ? (
          <div className="space-y-2"><Skeleton className="h-3 w-full !bg-black/10" /><Skeleton className="h-3 w-5/6 !bg-black/10" /><Skeleton className="h-3 w-4/6 !bg-black/10" /></div>
        ) : failed ? (
          <p className="passage text-[13px]"><Snippet snippet={result.snippet} /></p>
        ) : (
          <p className="whitespace-pre-wrap break-words text-[12.5px] leading-[1.7]">
            <HighlightedText text={excerpt} terms={terms} />
          </p>
        )}
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-[#f8f9f8] to-transparent" />
      </div>

      <Link
        href={`/documents/${result.document_id}?q=${encodeURIComponent(query)}`}
        className="mt-4 flex w-full items-center justify-center rounded-xl border border-line bg-sidebar px-4 py-3 text-sm font-semibold text-white hover:bg-sunken"
      >
        Open document
      </Link>
    </Card>
  );
}

function SearchView() {
  const { current, loading: wsLoading } = useWorkspace();
  const { preferences } = useTheme();
  const router = useRouter();
  const params = useSearchParams();
  const urlQuery = params.get("q") ?? "";
  const wide = useMediaQuery("(min-width: 1180px)");

  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const ctrl = useRef<AbortController | null>(null);

  const workspaceId = current?.id ?? null;
  const limit = preferences.resultsPerSearch;
  const { documents } = useDocuments(workspaceId);
  const docById = useMemo(() => new Map(documents.map((d) => [d.id, d])), [documents]);

  const runSearch = useCallback(
    async (q: string) => {
      if (!workspaceId || !q) return;
      ctrl.current?.abort();
      const c = new AbortController();
      ctrl.current = c;
      setLoading(true);
      setError(null);
      setTypeFilter(null);
      setSelectedId(null);
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
    return <EmptyState title="Create a workspace first" body="Search works inside a workspace." action={<Link href="/workspaces" className="font-medium text-web underline underline-offset-4">Go to Workspaces</Link>} />;
  }

  const types = response ? Array.from(new Set(response.results.map((r) => fileExtension(r.filename)).filter(Boolean))) : [];
  const shown = response ? response.results.filter((r) => !typeFilter || fileExtension(r.filename) === typeFilter) : [];
  const selected = shown.find((r) => r.document_id === selectedId) ?? shown[0] ?? null;

  const pill = (active: boolean) =>
    `inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm font-medium ${active ? "border-transparent bg-primary text-primary-fg" : "border-line-soft bg-surface text-muted hover:bg-sunken hover:text-fg"}`;

  return (
    <>
      <div className="max-w-3xl">
        <SearchBox key={urlQuery} workspaceId={workspaceId} initialValue={urlQuery} autoFocus onSubmit={submit} loading={loading} />
      </div>

      {response && types.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2.5" role="group" aria-label="Filter by file type">
          {[null, ...types].map((t) => (
            <button key={t ?? "all"} onClick={() => setTypeFilter(t)} aria-pressed={typeFilter === t} className={pill(typeFilter === t)}>
              {t ? TYPE_LABEL[t] ?? `.${t}` : "All"}
            </button>
          ))}
        </div>
      )}

      {error && <div className="mt-6"><ErrorNote message={error} onRetry={() => runSearch(urlQuery)} /></div>}

      {loading && !response && <div className="mt-6"><RowsSkeleton rows={4} /></div>}

      {!urlQuery && !loading && (
        <div className="mt-8 max-w-3xl">
          {history.length > 0 ? (
            <Card className="p-5">
              <h2 className="mb-2 text-[17px] font-semibold">Recent searches</h2>
              <ul className="divide-y divide-line-soft">
                {history.map((h) => (
                  <li key={h.id}>
                    <button onClick={() => submit(h.query_text)} className="block w-full py-2.5 text-left hover:text-web">{h.query_text}</button>
                  </li>
                ))}
              </ul>
            </Card>
          ) : (
            <EmptyState title="Search everything you’ve saved" body="Type a word or phrase you remember. Put quotes around words to find an exact phrase, like “database normalization”." />
          )}
        </div>
      )}

      {response && !error && (
        <div className={`mt-6 grid items-start gap-6 transition-opacity ${loading ? "opacity-50" : ""} ${wide ? "grid-cols-[minmax(0,1fr)_360px]" : ""}`} aria-live="polite">
          <SectionCard title="Your Knowledge" icon="knowledge" tone="knowledge" count={shown.length}>
            {shown.length === 0 ? (
              <EmptyState title="No matches" body={`Nothing in ${current.name} matches “${response.query}”. Try fewer or different words, or check the spelling. Only documents marked Ready can be searched.`} />
            ) : (
              <ul className="divide-y divide-white/8">
                {shown.map((r) => {
                  const doc = docById.get(r.document_id);
                  const isSel = wide && selected?.document_id === r.document_id;
                  return (
                    <li key={r.document_id}>
                      <Link
                        href={`/documents/${r.document_id}?q=${encodeURIComponent(response.query)}`}
                        onClick={(e) => {
                          if (wide) {
                            e.preventDefault();
                            setSelectedId(r.document_id);
                          }
                        }}
                        aria-current={isSel ? "true" : undefined}
                        className={`-mx-2 flex gap-3.5 rounded-xl px-3 py-3.5 ${isSel ? "bg-white/8" : "hover:bg-white/5"}`}
                      >
                        <FileTag filename={r.filename} />
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-semibold">{r.filename}</p>
                          <p className="passage mt-1 line-clamp-3 text-muted"><Snippet snippet={r.snippet} /></p>
                          {doc && <p className="mt-1.5 text-xs text-faint">Added {formatRelative(doc.created_at)}</p>}
                        </div>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            )}
          </SectionCard>

          {wide && selected && (
            <aside className="sticky top-24" aria-label="Document preview">
              <PreviewPanel workspaceId={current.id} result={selected} doc={docById.get(selected.document_id)} query={response.query} />
            </aside>
          )}
        </div>
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
