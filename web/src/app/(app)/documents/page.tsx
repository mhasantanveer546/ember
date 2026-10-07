"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { StatusBadge } from "@/components/StatusBadge";
import { UploadZone } from "@/components/UploadZone";
import { Button, Card, EmptyState, ErrorNote, FileTag, Input, PageHeader, RowsSkeleton, Select } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useDocuments } from "@/hooks/useDocuments";
import { formatBytes, formatRelative } from "@/lib/format";
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

  if (wsLoading) return <RowsSkeleton rows={3} />;
  if (!current) return <EmptyState title="Create a workspace first" body="Your knowledge lives inside a workspace." action={<Link href="/workspaces" className="font-medium text-web underline underline-offset-4">Go to Workspaces</Link>} />;

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
      <PageHeader title="Knowledge" subtitle={`Everything you’ve added to ${current.name}`} />
      <UploadZone workspaceId={current.id} onUploaded={reload} />

      {documents.length > 0 && (
        <div className="mt-8 grid gap-4 sm:grid-cols-[1fr_10rem_10rem]">
          <Input label="Filter by name" name="filter" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="networking" />
          <Select label="Status" value={status} onChange={(e) => setStatus(e.target.value as DocumentStatus | "ALL")}>
            <option value="ALL">All</option>
            <option value="READY">Ready</option>
            <option value="UPLOADING">Uploading</option>
            <option value="PROCESSING">Reading</option>
            <option value="INDEXING">Indexing</option>
            <option value="FAILED">Failed</option>
          </Select>
          <Select label="Sort by" value={sort} onChange={(e) => setSort(e.target.value as SortKey)}>
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
            <option value="name">Name</option>
            <option value="size">Largest</option>
          </Select>
        </div>
      )}

      {(error || actionError) && <div className="mt-6"><ErrorNote message={(error ?? actionError)!} onRetry={error ? reload : undefined} /></div>}

      <div className="mt-6">
        {loading ? (
          <RowsSkeleton rows={4} />
        ) : documents.length === 0 ? (
          <EmptyState title="No documents yet" body="Drop a file above. Ember reads it and makes it searchable, usually within a few seconds." />
        ) : visible.length === 0 ? (
          <EmptyState title="Nothing matches those filters" body="Clear the filter or choose a different status." />
        ) : (
          <Card className="overflow-hidden">
            <ul className="divide-y divide-line-soft">
              {visible.map((d) => (
                <li key={d.id} className="grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-1 px-4 py-3 hover:bg-sunken/50 sm:grid-cols-[1fr_5rem_8rem_7rem_auto]">
                  <div className="flex min-w-0 items-center gap-3">
                    <FileTag filename={d.filename} />
                    <Link href={`/documents/${d.id}`} className="truncate font-medium hover:text-web">{d.filename}</Link>
                  </div>
                  <span className="hidden text-right text-sm tabular-nums text-muted sm:block">{formatBytes(d.file_size_bytes)}</span>
                  <span className="hidden text-sm text-muted sm:block">{formatRelative(d.created_at)}</span>
                  <StatusBadge status={d.status} />
                  <div className="col-span-2 flex gap-1 sm:col-span-1">
                    <Button variant="ghost" size="sm" onClick={() => act(() => documentService.reindex(current.id, d.id))}>Re-index</Button>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => {
                        if (confirm(`Delete “${d.filename}”? This can’t be undone.`)) void act(() => documentService.remove(current.id, d.id));
                      }}
                    >
                      Delete
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>
    </>
  );
}
