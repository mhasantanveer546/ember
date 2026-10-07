"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { Card, EmptyState, ErrorNote, PageHeader, RowsSkeleton } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { formatDateTime, formatRelative } from "@/lib/format";
import { searchService } from "@/services/search";
import type { SearchHistoryItem } from "@/types/api";

export default function HistoryPage() {
  const { current, loading: wsLoading } = useWorkspace();
  const [items, setItems] = useState<SearchHistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!current) return;
    let cancelled = false;
    searchService
      .history(current.id, 100)
      .then((h) => !cancelled && (setItems(h), setError(null)))
      .catch((e) => !cancelled && setError((e as Error).message));
    return () => {
      cancelled = true;
    };
  }, [current]);

  if (wsLoading) return <RowsSkeleton rows={4} />;
  if (!current) return <EmptyState title="Create a workspace first" body="Your search history is kept per workspace." action={<Link href="/workspaces" className="font-medium text-web underline underline-offset-4">Go to Workspaces</Link>} />;

  return (
    <>
      <PageHeader title="History" subtitle={`Your recent searches in ${current.name}`} />
      {error && <ErrorNote message={error} />}
      {!error && items === null && <RowsSkeleton rows={5} />}
      {items && items.length === 0 && <EmptyState title="No searches yet" body="Searches you run appear here so you can repeat them with one click." action={<Link href="/search" className="font-medium text-web underline underline-offset-4">Start searching</Link>} />}
      {items && items.length > 0 && (
        <Card className="max-w-3xl overflow-hidden">
          <ul className="divide-y divide-line-soft">
            {items.map((h) => (
              <li key={h.id}>
                <Link href={`/search?q=${encodeURIComponent(h.query_text)}`} className="flex items-center gap-3.5 px-5 py-3.5 hover:bg-sunken/50">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-sunken text-muted"><Icon name="clock" className="h-4 w-4" /></span>
                  <span className="min-w-0 flex-1 truncate font-medium">{h.query_text}</span>
                  <span className="shrink-0 text-[13px] text-faint" title={formatDateTime(h.created_at)}>{formatRelative(h.created_at)}</span>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </>
  );
}
