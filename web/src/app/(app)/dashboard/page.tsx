"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { HeroArt } from "@/components/HeroArt";
import { Icon, type IconName } from "@/components/Icon";
import { EmberMark } from "@/components/Logo";
import { SearchBox } from "@/components/SearchBox";
import { StatusBadge } from "@/components/StatusBadge";
import { Card, ErrorNote, FileTag, LinkButton, RowsSkeleton } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useDocuments } from "@/hooks/useDocuments";
import { formatDateTime, formatRelative } from "@/lib/format";
import { searchService } from "@/services/search";
import { workspaceService } from "@/services/workspaces";
import type { IndexMetadata, SearchHistoryItem } from "@/types/api";

const PILLS: { href: string; label: string; icon: IconName; primary?: boolean }[] = [
  { href: "/search", label: "My Knowledge", icon: "knowledge", primary: true },
  { href: "/documents", label: "Upload", icon: "upload" },
  { href: "/workspaces", label: "Workspaces", icon: "layers" },
  { href: "/history", label: "History", icon: "clock" },
];

const TRIO: { icon: IconName; color: string; title: string; body: string }[] = [
  { icon: "upload", color: "#ff7a4d", title: "Add", body: "PDFs, notes and documents" },
  { icon: "search", color: "#5aa9ff", title: "Search", body: "Across everything you’ve saved" },
  { icon: "spark", color: "#ffc247", title: "Recall", body: "Open the exact passage" },
];

function Stat({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <Card className="p-5">
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 text-[28px] font-semibold tabular-nums leading-tight">{value}</p>
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

  if (wsLoading) return <div className="p-8"><RowsSkeleton rows={3} /></div>;
  if (wsError) return <div className="p-8"><ErrorNote message={wsError} /></div>;

  const ready = documents.filter((d) => d.status === "READY").length;
  const inProgress = documents.filter((d) => ["UPLOADING", "PROCESSING", "INDEXING"].includes(d.status)).length;
  const recent = [...documents].sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 5);

  return (
    <>
      <section className="relative isolate flex min-h-[calc(100dvh-5rem)] flex-col overflow-hidden md:min-h-dvh">
        <HeroArt className="absolute inset-0 -z-10 h-full w-full" />
        <div className="absolute inset-x-0 bottom-0 -z-10 h-40 bg-gradient-to-t from-[#0a1019] to-transparent dark:from-bg" />

        <div className="flex flex-1 flex-col items-center justify-center px-5 pb-6 pt-24 text-center">
          <EmberMark className="h-14 w-14" glow />
          <h1 className="mt-3 text-[56px] font-bold leading-none tracking-tight text-white drop-shadow sm:text-[68px]">Ember</h1>
          <p className="mt-3 text-lg text-white/80 sm:text-xl">Find what you forgot you knew.</p>

          <div className="mt-24 w-full max-w-2xl text-left sm:mt-36">
            {current ? (
              <>
                <SearchBox variant="hero" workspaceId={current.id} onSubmit={(q) => router.push(`/search?q=${encodeURIComponent(q)}`)} />
                <div className="mt-6 flex flex-wrap justify-center gap-3">
                  {PILLS.map((p) => (
                    <Link
                      key={p.label}
                      href={p.href}
                      className={`inline-flex items-center gap-2 rounded-2xl border px-5 py-2.5 text-sm font-medium text-white backdrop-blur-md ${
                        p.primary
                          ? "border-web/60 bg-primary/30 shadow-[0_0_24px_-6px_rgb(90_169_255/0.6)] hover:bg-primary/40"
                          : "border-white/12 bg-[#0b1623]/60 hover:bg-[#0b1623]/80"
                      }`}
                    >
                      <Icon name={p.icon} className="h-[18px] w-[18px]" />
                      {p.label}
                    </Link>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center">
                <p className="mb-4 text-white/80">Create a workspace to start adding documents.</p>
                <LinkButton href="/workspaces">Create your first workspace</LinkButton>
              </div>
            )}
          </div>
        </div>

        <div className="mx-auto mb-6 mt-10 grid w-full max-w-3xl grid-cols-3 divide-x divide-white/10 border-t border-white/10 px-3 pt-8 text-center">
          {TRIO.map((t) => (
            <div key={t.title} className="px-2">
              <span style={{ color: t.color }}><Icon name={t.icon} className="mx-auto h-6 w-6" /></span>
              <p className="mt-2 text-[15px] font-semibold text-white">{t.title}</p>
              <p className="mt-0.5 text-xs text-white/60">{t.body}</p>
            </div>
          ))}
        </div>
      </section>

      {current && (
        <div className="mx-auto w-full max-w-[1180px] px-4 pb-12 pt-4 md:px-8">
          <div className="grid gap-4 sm:grid-cols-3">
            <Stat label="Documents ready" value={docsLoading ? "–" : ready} hint={inProgress ? `${inProgress} still processing` : undefined} />
            <Stat label="Words indexed" value={meta ? meta.vocabulary_size.toLocaleString() : "–"} hint="Distinct terms in this workspace" />
            <Stat label="Index version" value={meta ? `v${meta.version}` : "–"} hint={meta?.last_built_at ? `Rebuilt ${formatDateTime(meta.last_built_at)}` : undefined} />
          </div>

          {!docsLoading && documents.length > 0 && (
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <Card className="p-5">
                <h2 className="mb-2 text-[17px] font-semibold">Recent searches</h2>
                {history.length === 0 ? (
                  <p className="py-2 text-muted">Your searches will appear here.</p>
                ) : (
                  <ul className="divide-y divide-line-soft">
                    {history.map((h) => (
                      <li key={h.id}>
                        <Link href={`/search?q=${encodeURIComponent(h.query_text)}`} className="flex items-center justify-between gap-4 py-2.5 hover:text-web">
                          <span className="flex min-w-0 items-center gap-2.5"><Icon name="clock" className="h-4 w-4 shrink-0 text-faint" /><span className="truncate">{h.query_text}</span></span>
                          <span className="shrink-0 text-xs text-faint">{formatRelative(h.created_at)}</span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
              <Card className="p-5">
                <h2 className="mb-2 text-[17px] font-semibold">Recently added</h2>
                <ul className="divide-y divide-line-soft">
                  {recent.map((d) => (
                    <li key={d.id}>
                      <Link href={`/documents/${d.id}`} className="flex items-center gap-3 py-2.5 hover:text-web">
                        <FileTag filename={d.filename} />
                        <span className="min-w-0 flex-1 truncate">{d.filename}</span>
                        <StatusBadge status={d.status} />
                      </Link>
                    </li>
                  ))}
                </ul>
              </Card>
            </div>
          )}
        </div>
      )}
    </>
  );
}
