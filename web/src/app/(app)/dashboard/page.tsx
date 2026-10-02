"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { SearchBox } from "@/components/SearchBox";
import { StatusBadge } from "@/components/StatusBadge";
import { Card, EmptyState, ErrorNote, LinkButton, LoadingBlock, PageHeader } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useDocuments } from "@/hooks/useDocuments";
import { formatDate, formatDateTime } from "@/lib/format";
import { searchService } from "@/services/search";
import { workspaceService } from "@/services/workspaces";
import type { IndexMetadata, SearchHistoryItem } from "@/types/api";

function Stat({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <Card>
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 font-serif text-3xl font-semibold">{value}</p>
      {hint && <p className="mt-1 text-xs text-muted">{hint}</p>}
    </Card>
  );
}

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
    searchService.history(current.id, 5).then((h) => !cancelled && setHistory(h)).catch(() => !cancelled && setHistory([]));
    return () => {
      cancelled = true;
    };
  }, [current]);

  if (wsLoading) return <LoadingBlock />;
  if (wsError) return <ErrorNote message={wsError} />;
  if (!current) {
    return (
      <>
        <PageHeader title="Welcome to Ember" subtitle="Find what you forgot you knew." />
        <EmptyState
          title="Create your first workspace"
          body="A workspace holds a collection of documents you can search together, for example “Networking course” or “Research papers”."
          action={<LinkButton href="/workspaces">Create a workspace</LinkButton>}
        />
      </>
    );
  }

  const ready = documents.filter((d) => d.status === "READY").length;
  const inProgress = documents.filter((d) => ["UPLOADING", "PROCESSING", "INDEXING"].includes(d.status)).length;
  const failed = documents.filter((d) => d.status === "FAILED").length;
  const recent = [...documents].sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 5);

  return (
    <>
      <PageHeader title={current.name} subtitle="Find what you forgot you knew." />
      <div className="mb-8">
        <SearchBox workspaceId={current.id} onSubmit={(q) => router.push(`/search?q=${encodeURIComponent(q)}`)} />
      </div>

      <div className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="Documents" value={docsLoading ? "…" : documents.length} hint={failed ? `${failed} failed` : undefined} />
        <Stat label="Ready to search" value={docsLoading ? "…" : ready} hint={inProgress ? `${inProgress} processing` : undefined} />
        <Stat label="Indexed words" value={meta ? meta.vocabulary_size.toLocaleString() : "–"} hint="Distinct terms" />
        <Stat
          label="Index"
          value={meta ? `v${meta.version}` : "–"}
          hint={meta?.last_built_at ? `Rebuilt ${formatDateTime(meta.last_built_at)}` : "Updated as you upload"}
        />
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <section>
          <h2 className="mb-3 font-serif text-lg font-semibold">Recent searches</h2>
          {history.length === 0 ? (
            <p className="text-sm text-muted">Nothing yet. Your searches will show up here.</p>
          ) : (
            <ul className="space-y-1">
              {history.map((h) => (
                <li key={h.id}>
                  <Link href={`/search?q=${encodeURIComponent(h.query_text)}`} className="flex justify-between rounded-lg px-3 py-2 text-sm hover:bg-surface-2">
                    <span className="truncate">{h.query_text}</span>
                    <span className="ml-3 shrink-0 text-muted">{formatDate(h.created_at)}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
        <section>
          <h2 className="mb-3 font-serif text-lg font-semibold">Recent documents</h2>
          {recent.length === 0 ? (
            <p className="text-sm text-muted">
              No documents yet. <Link href="/documents" className="text-accent hover:underline">Upload your first</Link>.
            </p>
          ) : (
            <ul className="space-y-1">
              {recent.map((d) => (
                <li key={d.id}>
                  <Link href={`/documents/${d.id}`} className="flex items-center justify-between gap-3 rounded-lg px-3 py-2 text-sm hover:bg-surface-2">
                    <span className="truncate">{d.filename}</span>
                    <StatusBadge status={d.status} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </>
  );
}
