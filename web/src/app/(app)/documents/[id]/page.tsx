"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { StatusBadge } from "@/components/StatusBadge";
import { Button, Card, ErrorNote, LoadingBlock } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { formatBytes, formatDateTime } from "@/lib/format";
import { escapeRegExp, queryTerms } from "@/lib/highlight";
import { documentService } from "@/services/documents";
import type { EmberDocument } from "@/types/api";

const MAX_CHARS = 200_000; // keep the DOM responsive on very large documents

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
  const container = useRef<HTMLDivElement>(null);

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

  // Poll status while the document is still being processed (Phase 6.2).
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
    container.current?.querySelector(`[data-hit="${active}"]`)?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [active, hitCount, terms]);

  if (!workspaceId) return <LoadingBlock />;
  if (error) return <ErrorNote message={error} onRetry={load} />;
  if (!doc) return <LoadingBlock />;

  const step = (delta: number) => hitCount && setActive((a) => (a + delta + hitCount) % hitCount);

  return (
    <>
      <Link href="/documents" className="text-sm text-muted hover:text-fg">← Documents</Link>
      <div className="mb-6 mt-2 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="break-words font-serif text-2xl font-semibold tracking-tight">{doc.filename}</h1>
          <p className="mt-1 text-sm text-muted">
            {formatBytes(doc.file_size_bytes)} · Added {formatDateTime(doc.created_at)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={doc.status} />
          <Button
            variant="secondary"
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
            onClick={async () => {
              if (!confirm(`Delete “${doc.filename}”? This can't be undone.`)) return;
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

      {doc.status === "FAILED" && <ErrorNote message="We couldn't extract text from this file. Try Re-index, or upload a different copy." />}
      {["UPLOADING", "PROCESSING", "INDEXING"].includes(doc.status) && <LoadingBlock label="Ember is reading this document…" />}

      {doc.status === "READY" && (
        <Card className="!p-0">
          <form
            className="flex flex-wrap items-center gap-2 border-b border-line p-3"
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
              className="min-w-40 flex-1 rounded-lg border border-line bg-bg px-3 py-1.5 text-sm"
            />
            <Button type="submit" variant="secondary" className="!py-1.5">Find</Button>
            <span className="text-xs text-muted" aria-live="polite">
              {terms.length ? (hitCount ? `${active + 1} of ${hitCount}` : "No matches") : ""}
            </span>
            <Button type="button" variant="ghost" className="!px-2 !py-1.5" onClick={() => step(-1)} disabled={!hitCount} aria-label="Previous match">↑</Button>
            <Button type="button" variant="ghost" className="!px-2 !py-1.5" onClick={() => step(1)} disabled={!hitCount} aria-label="Next match">↓</Button>
          </form>
          <div ref={container} className="max-h-[70vh] overflow-y-auto whitespace-pre-wrap break-words p-5 text-[15px] leading-7">
            {textError ? (
              <span className="text-danger">{textError}</span>
            ) : text === null ? (
              <LoadingBlock label="Loading text…" />
            ) : (
              parts.map((p, i) =>
                p.hit === null ? (
                  <span key={i}>{p.s}</span>
                ) : (
                  <mark key={i} data-hit={p.hit} className={`hit ${p.hit === active ? "active" : ""}`}>{p.s}</mark>
                ),
              )
            )}
            {truncated && <p className="mt-4 text-xs text-muted">Preview truncated to the first {MAX_CHARS.toLocaleString()} characters.</p>}
          </div>
        </Card>
      )}
    </>
  );
}

export default function DocumentPage() {
  return (
    <Suspense fallback={<LoadingBlock />}>
      <DocumentView />
    </Suspense>
  );
}
