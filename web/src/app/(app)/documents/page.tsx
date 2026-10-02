"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { StatusBadge } from "@/components/StatusBadge";
import { UploadZone } from "@/components/UploadZone";
import { Button, EmptyState, ErrorNote, Input, LoadingBlock, PageHeader } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useDocuments } from "@/hooks/useDocuments";
import { formatBytes, formatDate } from "@/lib/format";
import { documentService } from "@/services/documents";
import type { DocumentStatus } from "@/types/api";

type SortKey = "newest" | "oldest" | "name" | "size";

export default function DocumentsPage() {
  const { current, loading: wsLoading } = useWorkspace();
  const { documents, loading, error, reload } = useDocuments(current?.id ?? null);
  const [filter, setFilter] = useState("");
  const [status, setStatus] = useState<DocumentStatus | "ALL">("ALL");
  const [sort, setSort] = useState<SortKey>("newest");
  const [actionError, setActionError] = useState<string | null>(null);

  const visible = useMemo(() => {
    const q = filter.trim().toLowerCase();
    const list = documents.filter((d) => (status === "ALL" || d.status === status) && (!q || d.filename.toLowerCase().includes(q)));
    const cmp: Record<SortKey, (a: (typeof list)[0], b: (typeof list)[0]) => number> = {
      newest: (a, b) => b.created_at.localeCompare(a.created_at),
      oldest: (a, b) => a.created_at.localeCompare(b.created_at),
      name: (a, b) => a.filename.localeCompare(b.filename),
      size: (a, b) => b.file_size_bytes - a.file_size_bytes,
    };
    return [...list].sort(cmp[sort]);
  }, [documents, filter, status, sort]);

  if (wsLoading) return <LoadingBlock />;
  if (!current) return <EmptyState title="Create a workspace first" body="Documents live inside a workspace." />;

  const act = async (fn: () => Promise<unknown>) => {
    setActionError(null);
    try {
      await fn();
      await reload();
    } catch (e) {
      setActionError((e as Error).message);
    }
  };

  return (
    <>
      <PageHeader title="Documents" subtitle={`In ${current.name}`} />
      <UploadZone workspaceId={current.id} onUploaded={reload} />

      <div className="mt-8 flex flex-wrap items-end gap-3">
        <div className="min-w-48 flex-1">
          <Input label="Filter by name" name="filter" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="e.g. networking" />
        </div>
        <label className="text-sm">
          <span className="mb-1 block font-medium">Status</span>
          <select value={status} onChange={(e) => setStatus(e.target.value as DocumentStatus | "ALL")} className="rounded-lg border border-line bg-surface px-3 py-2 text-sm">
            <option value="ALL">All</option>
            <option value="READY">Ready</option>
            <option value="UPLOADING">Uploading</option>
            <option value="PROCESSING">Processing</option>
            <option value="INDEXING">Indexing</option>
            <option value="FAILED">Failed</option>
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium">Sort</span>
          <select value={sort} onChange={(e) => setSort(e.target.value as SortKey)} className="rounded-lg border border-line bg-surface px-3 py-2 text-sm">
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
            <option value="name">Name</option>
            <option value="size">Largest</option>
          </select>
        </label>
      </div>

      {(error || actionError) && (
        <div className="mt-4">
          <ErrorNote message={(error ?? actionError)!} onRetry={error ? reload : undefined} />
        </div>
      )}

      <div className="mt-4">
        {loading ? (
          <LoadingBlock />
        ) : documents.length === 0 ? (
          <EmptyState title="No documents yet" body="Drop a file above to get started. Ember will extract and index it automatically." />
        ) : visible.length === 0 ? (
          <EmptyState title="Nothing matches those filters" />
        ) : (
          <ul className="divide-y divide-line overflow-hidden rounded-xl border border-line bg-surface">
            {visible.map((d) => (
              <li key={d.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
                <div className="min-w-0 flex-1">
                  <Link href={`/documents/${d.id}`} className="block truncate font-medium hover:text-accent">
                    {d.filename}
                  </Link>
                  <p className="text-xs text-muted">
                    {formatBytes(d.file_size_bytes)} · {formatDate(d.created_at)}
                  </p>
                </div>
                <StatusBadge status={d.status} />
                <div className="flex gap-1">
                  <Button variant="ghost" className="!px-2 !py-1 text-xs" onClick={() => act(() => documentService.reindex(current.id, d.id))}>
                    Re-index
                  </Button>
                  <Button
                    variant="danger"
                    className="!px-2 !py-1 text-xs"
                    onClick={() => {
                      if (confirm(`Delete “${d.filename}”? This can't be undone.`)) void act(() => documentService.remove(current.id, d.id));
                    }}
                  >
                    Delete
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}
