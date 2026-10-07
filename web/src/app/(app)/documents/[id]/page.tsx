"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { HighlightedText } from "@/components/HighlightedText";
import { Icon } from "@/components/Icon";
import { StatusBadge } from "@/components/StatusBadge";
import { Button, ErrorNote, FileTag, RowsSkeleton } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { formatBytes, formatDateTime } from "@/lib/format";
import { escapeRegExp, queryTerms } from "@/lib/highlight";
import { documentService } from "@/services/documents";
import type { EmberDocument } from "@/types/api";

const MAX_CHARS = 200_000; // keeps the page responsive on very large documents
const MAX_MATCHES = 300;

interface Match {
  before: string;
  hit: string;
  after: string;
}

function DocumentView() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const params = useSearchParams();
  const { current } = useWorkspace();
  const workspaceId = current?.id ?? null;

  const [doc, setDoc] = useState<EmberDocument | null>(null);
  const [text, setText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [textError, setTextError] = useState<string | null>(null);
  const [terms, setTerms] = useState(() => queryTerms(params.get("q") ?? ""));
  const [termInput, setTermInput] = useState(params.get("q") ?? "");
  const [active, setActive] = useState(0);
  const [zoom, setZoom] = useState(100);

  const load = useCallback(async () => {
    if (!workspaceId) return;
    try {
      const d = await documentService.get(workspaceId, id);
      setDoc(d);
      setError(null);
      if (d.status === "READY") {
        documentService.text(workspaceId, id).then((t) => setText(t.text)).catch((e) => setTextError((e as Error).message));
      }
    } catch (e) {
      setError((e as Error).message);
    }
  }, [workspaceId, id]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial fetch for this document
    void load();
  }, [load]);

  // Poll while the document is still being processed (Phase 6.2).
  useEffect(() => {
    if (!doc || !["UPLOADING", "PROCESSING", "INDEXING"].includes(doc.status)) return;
    const t = setTimeout(load, 2000);
    return () => clearTimeout(t);
  }, [doc, load]);

  const body = useMemo(() => (text === null ? null : text.length > MAX_CHARS ? text.slice(0, MAX_CHARS) : text), [text]);
  const truncated = text !== null && text.length > MAX_CHARS;

  const matches = useMemo<Match[]>(() => {
    if (!body || terms.length === 0) return [];
    const re = new RegExp(terms.map(escapeRegExp).join("|"), "gi");
    const out: Match[] = [];
    let m: RegExpExecArray | null;
    while ((m = re.exec(body)) && out.length < MAX_MATCHES) {
      const start = Math.max(0, m.index - 48);
      const end = Math.min(body.length, m.index + m[0].length + 64);
      out.push({
        before: (start > 0 ? "…" : "") + body.slice(start, m.index).replace(/\s+/g, " "),
        hit: m[0],
        after: body.slice(m.index + m[0].length, end).replace(/\s+/g, " ") + (end < body.length ? "…" : ""),
      });
    }
    return out;
  }, [body, terms]);
  const hitCount = matches.length;

  useEffect(() => {
    if (hitCount === 0) return;
    document.querySelector(`[data-hit="${active}"]`)?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [active, hitCount, terms]);

  if (!workspaceId) return <RowsSkeleton rows={2} />;
  if (error) return <ErrorNote message={error} onRetry={load} />;
  if (!doc) return <RowsSkeleton rows={2} />;

  const step = (delta: number) => hitCount && setActive((a) => (a + delta + hitCount) % hitCount);
  const processing = ["UPLOADING", "PROCESSING", "INDEXING"].includes(doc.status);

  return (
    <>
      <div className="mb-5 flex flex-wrap items-center gap-x-4 gap-y-3">
        <Link href="/documents" aria-label="Back to Knowledge" className="flex h-9 w-9 items-center justify-center rounded-lg border border-line-soft text-muted hover:bg-sunken hover:text-fg">
          <Icon name="back" />
        </Link>
        <FileTag filename={doc.filename} size="lg" />
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-xl font-semibold tracking-tight">{doc.filename}</h1>
          <p className="flex flex-wrap items-center gap-x-3 text-[13px] text-muted">
            <span className="tabular-nums">{formatBytes(doc.file_size_bytes)}</span>
            <span>Added {formatDateTime(doc.created_at)}</span>
            <StatusBadge status={doc.status} />
          </p>
        </div>
        <div className="flex gap-1">
          <Button
            variant="secondary"
            size="sm"
            onClick={async () => {
              try {
                setDoc(await documentService.reindex(workspaceId, doc.id));
                setText(null);
              } catch (e) {
                setError((e as Error).message);
              }
            }}
          >
            Re-index
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={async () => {
              if (!confirm(`Delete “${doc.filename}”? This can’t be undone.`)) return;
              try {
                await documentService.remove(workspaceId, doc.id);
                router.replace("/documents");
              } catch (e) {
                setError((e as Error).message);
              }
            }}
          >
            Delete
          </Button>
        </div>
      </div>

      {doc.status === "FAILED" && <ErrorNote message="Ember couldn’t read the text in this file. Try Re-index, or upload a different copy. Scanned PDFs without selectable text can’t be read yet." />}
      {processing && <RowsSkeleton rows={3} />}

      {doc.status === "READY" && (
        <>
          <form
            className="sticky top-16 z-20 mb-5 flex flex-wrap items-center gap-2 rounded-2xl border border-line-soft bg-surface/95 p-2.5 backdrop-blur"
            onSubmit={(e) => {
              e.preventDefault();
              setTerms(queryTerms(termInput));
              setActive(0);
            }}
          >
            <div className="flex min-w-48 flex-1 items-center gap-2 rounded-xl border border-line bg-sunken px-3 focus-within:border-web">
              <Icon name="search" className="h-4 w-4 text-muted" />
              <input
                value={termInput}
                onChange={(e) => setTermInput(e.target.value)}
                placeholder="Find in this document"
                aria-label="Find in this document"
                className="w-full bg-transparent py-2 text-sm outline-none placeholder:text-faint"
              />
            </div>
            <Button type="submit" variant="secondary" size="sm">Find</Button>
            <span className="min-w-20 text-center text-[13px] tabular-nums text-muted" aria-live="polite">
              {terms.length ? (hitCount ? `${active + 1} of ${hitCount}` : "No matches") : ""}
            </span>
            <Button type="button" variant="ghost" size="sm" onClick={() => step(-1)} disabled={!hitCount} aria-label="Previous match"><Icon name="up" className="h-4 w-4" /></Button>
            <Button type="button" variant="ghost" size="sm" onClick={() => step(1)} disabled={!hitCount} aria-label="Next match"><Icon name="down" className="h-4 w-4" /></Button>
            <div className="ml-auto flex items-center gap-1 rounded-xl border border-line bg-sunken px-1" role="group" aria-label="Text size">
              <button type="button" onClick={() => setZoom((z) => Math.max(70, z - 10))} disabled={zoom <= 70} aria-label="Smaller text" className="rounded-lg p-2 text-muted hover:text-fg disabled:opacity-40"><Icon name="minus" className="h-4 w-4" /></button>
              <span className="w-12 text-center text-sm tabular-nums">{zoom}%</span>
              <button type="button" onClick={() => setZoom((z) => Math.min(160, z + 10))} disabled={zoom >= 160} aria-label="Larger text" className="rounded-lg p-2 text-muted hover:text-fg disabled:opacity-40"><Icon name="plus" className="h-4 w-4" /></button>
            </div>
          </form>

          <div className="grid items-start gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
            <aside className="hidden max-h-[calc(100dvh-12rem)] overflow-y-auto rounded-2xl border border-line-soft bg-surface p-3 lg:sticky lg:top-40 lg:block" aria-label="Matches">
              <h2 className="px-1.5 pb-2 text-sm font-semibold">Matches {hitCount > 0 && <span className="font-normal text-muted tabular-nums">{hitCount}</span>}</h2>
              {terms.length === 0 ? (
                <p className="px-1.5 pb-2 text-[13px] leading-relaxed text-muted">Search inside this document and every match is listed here. Click one to jump to it.</p>
              ) : hitCount === 0 ? (
                <p className="px-1.5 pb-2 text-[13px] text-muted">No matches for these words.</p>
              ) : (
                <ul className="space-y-2">
                  {matches.map((m, i) => (
                    <li key={i}>
                      <button
                        onClick={() => setActive(i)}
                        aria-current={i === active ? "true" : undefined}
                        className={`block w-full rounded-xl border px-3 py-2.5 text-left text-[12.5px] leading-snug ${i === active ? "border-web bg-primary-soft" : "border-line-soft bg-sunken hover:border-line"}`}
                      >
                        <span className="mb-1 block text-[11px] tabular-nums text-faint">{i + 1}</span>
                        <span className="text-muted">{m.before}</span>
                        <span className="font-semibold text-ember-text">{m.hit}</span>
                        <span className="text-muted">{m.after}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </aside>

            <div className="rounded-2xl border border-line-soft bg-black/20 p-3 sm:p-6">
              <article
                className="paper mx-auto min-h-[60vh] max-w-[860px] whitespace-pre-wrap break-words rounded-md bg-[#f8f9f8] px-6 py-8 leading-[1.8] text-[#1a2330] shadow-[0_10px_40px_-12px_rgb(0_0_0/0.6)] sm:px-12 sm:py-12"
                style={{ fontSize: `${(15 * zoom) / 100}px` }}
              >
                {textError ? (
                  <span className="text-danger">{textError}</span>
                ) : body === null ? (
                  <RowsSkeleton rows={3} />
                ) : (
                  <HighlightedText text={body} terms={terms} activeHit={active} />
                )}
                {truncated && <p className="mt-6 text-[13px] text-slate-500">Showing the first {MAX_CHARS.toLocaleString()} characters.</p>}
              </article>
            </div>
          </div>
        </>
      )}
    </>
  );
}

export default function DocumentPage() {
  return (
    <Suspense fallback={<RowsSkeleton rows={2} />}>
      <DocumentView />
    </Suspense>
  );
}
