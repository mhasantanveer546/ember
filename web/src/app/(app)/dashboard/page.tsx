"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FileTag, EmptyState, ErrorNote, LinkButton, RowsSkeleton } from "@/components/ui";
import { SearchBox } from "@/components/SearchBox";
import { StatusBadge } from "@/components/StatusBadge";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useDocuments } from "@/hooks/useDocuments";
import { formatDate, formatDateTime } from "@/lib/format";
import { searchService } from "@/services/search";
import { workspaceService } from "@/services/workspaces";
import type { IndexMetadata, SearchHistoryItem } from "@/types/api";

function Figure({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="px-6 first:pl-0">
      <dd className="text-[22px] font-semibold tabular-nums leading-none">{value}</dd>
      <dt className="mt-1.5 text-[13px] text-muted">{label}</dt>
    </div>
  );
}

const STEPS = [
  { title: "Create a workspace", body: "A workspace is one collection you search together, like “Networking course” or “Thesis papers”." },
  { title: "Add your documents", body: "PDF, text, Markdown or Word files up to 25 MB. Ember reads and indexes each one." },
  { title: "Search for anything you half remember", body: "A single word is enough. Ember shows the passage, not just the file." },
];

export default function DashboardPage() {
  const { current, loading: wsLoading, error: wsError } = useWorkspace();
  const router = useRouter();
  const { documents, loading: docsLoading } = useDocuments(current?.id ?? null);
  const [meta, setMeta] = useState<IndexMetadata | null>(null);
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);

  useEffect(() => {
    if (!current) return;
    let cancelled = false;
    workspaceService.indexMetadata(current.id).then((m) => !cancelled && setMeta(m)).catch(() => !cancelled && setMeta(null));
    searchService.history(current.id, 6).then((h) => !cancelled && setHistory(h)).catch(() => !cancelled && setHistory([]));
    return () => {
      cancelled = true;
    };
  }, [current]);

  if (wsLoading) return <RowsSkeleton rows={3} />;
  if (wsError) return <ErrorNote message={wsError} />;

  if (!current) {
    return (
      <>
        <h1 className="display max-w-xl text-[40px]">Find what you forgot you knew.</h1>
        <p className="mt-3 max-w-lg text-lg text-muted">Three steps to a searchable library of everything you’ve written down.</p>
        <ol className="mt-12 max-w-xl divide-y divide-line-soft">
          {STEPS.map((s, i) => (
            <li key={s.title} className={`flex gap-6 py-6 ${i > 0 ? "opacity-55" : ""}`}>
              <span className="display w-8 shrink-0 text-3xl text-faint">{i + 1}</span>
              <div>
                <h2 className="text-lg font-semibold">{s.title}</h2>
                <p className="mt-1 text-muted">{s.body}</p>
                {i === 0 && (
                  <div className="mt-4">
                    <LinkButton href="/workspaces">Create a workspace</LinkButton>
                  </div>
                )}
              </div>
            </li>
          ))}
        </ol>
      </>
    );
  }

  const ready = documents.filter((d) => d.status === "READY").length;
  const inProgress = documents.filter((d) => ["UPLOADING", "PROCESSING", "INDEXING"].includes(d.status)).length;
  const recent = [...documents].sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 5);

  return (
    <>
      <h1 className="display max-w-2xl text-[40px] sm:text-[48px]">What are you trying to remember?</h1>
      <div className="mt-8">
        <SearchBox workspaceId={current.id} onSubmit={(q) => router.push(`/search?q=${encodeURIComponent(q)}`)} />
        <p className="mt-3 text-sm text-muted">
          Searching {current.name}. Put quotes around words to find an exact phrase.
        </p>
      </div>

      <dl className="mt-12 flex flex-wrap gap-y-4 divide-x divide-line">
        <Figure value={docsLoading ? "–" : ready} label={inProgress ? `documents ready, ${inProgress} still processing` : "documents ready"} />
        <Figure value={meta ? meta.vocabulary_size.toLocaleString() : "–"} label="distinct words indexed" />
        <Figure value={meta ? `v${meta.version}` : "–"} label={meta?.last_built_at ? `index, rebuilt ${formatDateTime(meta.last_built_at)}` : "index version"} />
      </dl>

      {!docsLoading && documents.length === 0 ? (
        <div className="mt-12 border-t border-line-soft">
          <EmptyState
            title="Nothing to search yet"
            body="Add your first document and it becomes searchable within seconds."
            action={<LinkButton href="/documents">Add documents</LinkButton>}
          />
        </div>
      ) : (
        <div className="mt-14 grid gap-12 md:grid-cols-2">
          <section aria-labelledby="recent-searches">
            <h2 id="recent-searches" className="display mb-3 text-lg">Pick up where you left off</h2>
            {history.length === 0 ? (
              <p className="text-muted">Your searches will appear here.</p>
            ) : (
              <ul className="divide-y divide-line-soft border-y border-line-soft">
                {history.map((h) => (
                  <li key={h.id}>
                    <Link href={`/search?q=${encodeURIComponent(h.query_text)}`} className="group flex items-baseline justify-between gap-4 py-2.5 hover:text-ember-text">
                      <span className="truncate">{h.query_text}</span>
                      <span className="shrink-0 text-[13px] text-faint">{formatDate(h.created_at)}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
          <section aria-labelledby="recent-docs">
            <h2 id="recent-docs" className="display mb-3 text-lg">Recently added</h2>
            <ul className="divide-y divide-line-soft border-y border-line-soft">
              {recent.map((d) => (
                <li key={d.id}>
                  <Link href={`/documents/${d.id}`} className="flex items-center gap-3 py-2.5 hover:text-ember-text">
                    <FileTag filename={d.filename} />
                    <span className="min-w-0 flex-1 truncate">{d.filename}</span>
                    <StatusBadge status={d.status} />
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </>
  );
}
