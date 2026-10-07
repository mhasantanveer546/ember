"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { Icon } from "@/components/Icon";
import { StatusBadge } from "@/components/StatusBadge";
import { Button, ErrorNote, FileTag, RowsSkeleton } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { formatBytes, formatDateTime } from "@/lib/format";
import { escapeRegExp, queryTerms } from "@/lib/highlight";
import { documentService } from "@/services/documents";
import type { EmberDocument } from "@/types/api";

const MAX_CHARS = 200_000; // keeps the page responsive on very large documents

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

  const { parts, hitCount, truncated } = useMemo(() => {
    if (text === null) return { parts: [] as { s: string; hit: number | null }[], hitCount: 0, truncated: false };
    const body = text.length > MAX_CHARS ? text.slice(0, MAX_CHARS) : text;
    if (terms.length === 0) return { parts: [{ s: body, hit: null }], hitCount: 0, truncated: text.length > MAX_CHARS };
    const re = new RegExp(`(${terms.map(escapeRegExp).join("|")})`, "gi");
    let n = 0;
    const out = body.split(re).map((s, i) => (i % 2 === 1 ? { s, hit: n++ } : { s, hit: null }));
    return { parts: out, hitCount: n, truncated: text.length > MAX_CHARS };
  }, [text, terms]);

  useEffect(() => {
    if (hitCount === 0) return;
    document.querySelector(`[data-hit="${active}"]`)?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [active, hitCount, terms]);

  if (!workspaceId) return <RowsSkeleton rows={2} />;
  if (error) return <ErrorNote message={error} onRetry={load} />;
  if (!doc) return <RowsSkeleton rows={2} />;

  const step = (delta: number) => hitCount && setActive((a) => (a + delta + hitCount) % hitCount);

  return (
    <>
      <Link href="/documents" className="-ml-1 inline-flex items-center gap-1 text-sm text-muted hover:text-fg">
        <Icon name="back" className="h-4 w-4" /> Documents
      </Link>
      <header className="mb-8 mt-4 flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="mb-2"><FileTag filename={doc.filename} /></div>
          <h1 className="display break-words text-[30px]">{doc.filename}</h1>
          <p className="mt-2 flex flex-wrap items-center gap-x-3 text-sm text-muted">
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
      </header>

      {doc.status === "FAILED" && <ErrorNote message="Ember couldn’t read the text in this file. Try Re-index, or upload a different copy. Scanned PDFs without selectable text can’t be read yet." />}
      {["UPLOADING", "PROCESSING", "INDEXING"].includes(doc.status) && <RowsSkeleton rows={3} />}

      {doc.status === "READY" && (
        <>
          <form
            className="sticky top-14 z-10 -mx-5 flex flex-wrap items-center gap-2 border-y border-line-soft bg-bg/95 px-5 py-2.5 backdrop-blur md:top-0 md:-mx-12 md:px-12"
            onSubmit={(e) => {
              e.preventDefault();
              setTerms(queryTerms(termInput));
              setActive(0);
            }}
          >
            <input
              value={termInput}
              onChange={(e) => setTermInput(e.target.value)}
              placeholder="Find in this document"
              aria-label="Find in this document"
              className="min-w-40 flex-1 rounded-lg border border-line bg-surface px-3 py-1.5 text-sm placeholder:text-faint focus:border-ink"
            />
            <Button type="submit" variant="secondary" size="sm">Find</Button>
            <span className="min-w-16 text-center text-[13px] tabular-nums text-muted" aria-live="polite">
              {terms.length ? (hitCount ? `${active + 1} of ${hitCount}` : "No matches") : ""}
            </span>
            <Button type="button" variant="ghost" size="sm" onClick={() => step(-1)} disabled={!hitCount} aria-label="Previous match"><Icon name="up" className="h-4 w-4" /></Button>
            <Button type="button" variant="ghost" size="sm" onClick={() => step(1)} disabled={!hitCount} aria-label="Next match"><Icon name="down" className="h-4 w-4" /></Button>
          </form>

          <article className="passage mt-10 max-w-[68ch] whitespace-pre-wrap break-words pb-24 !text-[1.125rem] !leading-[1.8]">
            {textError ? (
              <span className="font-sans text-[15px] text-danger">{textError}</span>
            ) : text === null ? (
              <RowsSkeleton rows={3} />
            ) : (
              parts.map((p, i) =>
                p.hit === null ? (
                  <span key={i}>{p.s}</span>
                ) : (
                  <mark key={i} data-hit={p.hit} className={`hit ${p.hit === active ? "active" : ""}`}>
                    {p.s}
                  </mark>
                ),
              )
            )}
            {truncated && <p className="mt-6 font-sans text-[13px] text-muted">Showing the first {MAX_CHARS.toLocaleString()} characters.</p>}
          </article>
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
