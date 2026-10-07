"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Icon } from "@/components/Icon";
import { StatusBadge } from "@/components/StatusBadge";
import { UploadZone } from "@/components/UploadZone";
import { Button, Card, EmptyState, ErrorNote, FileTag, Input, PageHeader, RowsSkeleton } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useDocuments } from "@/hooks/useDocuments";
import { formatBytes, formatDateTime } from "@/lib/format";
import { documentService } from "@/services/documents";
import { workspaceService } from "@/services/workspaces";
import type { Folder, IndexMetadata } from "@/types/api";

const ALL = "__all__";
const UNFILED = "__unfiled__";

function folderPath(folder: Folder, byId: Map<string, Folder>): string {
  const names = [folder.name];
  let parent = folder.parent_folder_id ? byId.get(folder.parent_folder_id) : undefined;
  for (let guard = 0; parent && guard < 20; guard++) {
    names.unshift(parent.name);
    parent = parent.parent_folder_id ? byId.get(parent.parent_folder_id) : undefined;
  }
  return names.join(" / ");
}

export default function WorkspaceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { workspaces, loading: wsLoading, select } = useWorkspace();
  const workspace = workspaces.find((w) => w.id === id) ?? null;
  const { documents, loading, error, reload } = useDocuments(workspace ? id : null);

  const [folders, setFolders] = useState<Folder[]>([]);
  const [meta, setMeta] = useState<IndexMetadata | null>(null);
  const [selected, setSelected] = useState<string>(ALL);
  const [newFolder, setNewFolder] = useState("");
  const [parent, setParent] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const [rebuilding, setRebuilding] = useState(false);

  const loadSide = useCallback(async () => {
    try {
      setFolders(await workspaceService.folders(id));
      setMeta(await workspaceService.indexMetadata(id).catch(() => null));
    } catch (e) {
      setActionError((e as Error).message);
    }
  }, [id]);

  useEffect(() => {
    if (!workspace) return;
    select(id); // opening a workspace makes it the active one for Search
    // eslint-disable-next-line react-hooks/set-state-in-effect -- load folders + index info for this workspace
    void loadSide();
  }, [workspace, id, select, loadSide]);

  const byId = useMemo(() => new Map(folders.map((f) => [f.id, f])), [folders]);
  const sortedFolders = useMemo(
    () => folders.map((f) => ({ f, path: folderPath(f, byId) })).sort((a, b) => a.path.localeCompare(b.path)),
    [folders, byId],
  );
  const visible = documents.filter((d) => (selected === ALL ? true : selected === UNFILED ? d.folder_id === null : d.folder_id === selected));

  const act = async (fn: () => Promise<unknown>) => {
    setActionError(null);
    try {
      await fn();
      await Promise.all([loadSide(), reload()]);
    } catch (e) {
      setActionError((e as Error).message);
    }
  };

  if (wsLoading) return <RowsSkeleton rows={3} />;
  if (!workspace) return <EmptyState title="Workspace not found" action={<Link href="/workspaces" className="font-medium text-web underline underline-offset-4">Back to Workspaces</Link>} />;

  return (
    <>
      <Link href="/workspaces" className="-ml-1 mb-3 inline-flex items-center gap-1 text-sm text-muted hover:text-fg"><Icon name="back" className="h-4 w-4" /> Workspaces</Link>
      <div className="mt-2">
        <PageHeader
          title={workspace.name}
          subtitle={meta ? `${meta.document_count} indexed ${meta.document_count === 1 ? "document" : "documents"}, ${meta.vocabulary_size.toLocaleString()} distinct words. Index v${meta.version}${meta.last_built_at ? `, rebuilt ${formatDateTime(meta.last_built_at)}` : ""}.` : undefined}
          action={
            <div className="flex gap-2">
              <Button
                variant="secondary"
                disabled={rebuilding}
                onClick={async () => {
                  setRebuilding(true);
                  await act(() => workspaceService.rebuildIndex(id));
                  setRebuilding(false);
                }}
              >
                {rebuilding ? "Rebuilding…" : "Rebuild index"}
              </Button>
              <Link href="/search" className="inline-flex items-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-fg hover:opacity-90">Search this workspace</Link>
            </div>
          }
        />
      </div>

      {(actionError || error) && <div className="mb-4"><ErrorNote message={(actionError ?? error)!} /></div>}

      <div className="grid gap-6 lg:grid-cols-[16rem_1fr]">
        <aside className="rounded-2xl border border-line-soft bg-surface p-4">
          <h2 className="mb-3 text-[17px] font-semibold">Folders</h2>
          <nav aria-label="Folders" className="space-y-0.5">
            {[{ key: ALL, label: "All documents" }, { key: UNFILED, label: "Unfiled" }].map((o) => (
              <button key={o.key} onClick={() => setSelected(o.key)} className={`block w-full rounded-lg px-3 py-1.5 text-left text-sm ${selected === o.key ? "bg-primary-soft font-semibold text-web" : "text-muted hover:bg-sunken/70 hover:text-fg"}`}>
                {o.label}
              </button>
            ))}
            {sortedFolders.map(({ f, path }) => (
              <div key={f.id} className={`group flex items-center rounded-lg ${selected === f.id ? "bg-primary-soft" : "hover:bg-sunken/70"}`}>
                <button onClick={() => setSelected(f.id)} className={`min-w-0 flex-1 truncate px-3 py-1.5 text-left text-sm ${selected === f.id ? "font-semibold text-web" : "text-muted"}`} title={path}>
                  {path}
                </button>
                <button
                  className="px-1.5 text-xs text-faint hover:text-fg"
                  aria-label={`Rename ${f.name}`}
                  onClick={() => {
                    const n = prompt("Rename folder", f.name)?.trim();
                    if (n && n !== f.name) void act(() => workspaceService.renameFolder(id, f.id, n));
                  }}
                >
                  ✎
                </button>
                <button
                  className="px-1.5 text-xs text-danger"
                  aria-label={`Delete ${f.name}`}
                  onClick={() => {
                    if (confirm(`Delete folder “${f.name}”? Its documents stay in the workspace.`)) {
                      if (selected === f.id) setSelected(ALL);
                      void act(() => workspaceService.removeFolder(id, f.id));
                    }
                  }}
                >
                  ✕
                </button>
              </div>
            ))}
          </nav>

          <form
            className="mt-4 space-y-2"
            onSubmit={(e) => {
              e.preventDefault();
              const name = newFolder.trim();
              if (!name) return;
              void act(async () => {
                await workspaceService.createFolder(id, name, parent || null);
                setNewFolder("");
              });
            }}
          >
            <Input label="New folder" name="folder" value={newFolder} onChange={(e) => setNewFolder(e.target.value)} placeholder="Folder name" maxLength={255} />
            <select value={parent} onChange={(e) => setParent(e.target.value)} aria-label="Parent folder" className="w-full rounded-lg border border-line bg-sunken px-2 py-1.5 text-sm focus:border-web">
              <option value="">Top level</option>
              {sortedFolders.map(({ f, path }) => <option key={f.id} value={f.id}>Inside: {path}</option>)}
            </select>
            <Button type="submit" variant="secondary" disabled={!newFolder.trim()} className="w-full">Add folder</Button>
          </form>
        </aside>

        <section className="min-w-0">
          <UploadZone workspaceId={id} folderId={selected !== ALL && selected !== UNFILED ? selected : null} onUploaded={() => { void reload(); void loadSide(); }} />
          <div className="mt-6">
            {loading ? (
              <RowsSkeleton rows={3} />
            ) : visible.length === 0 ? (
              <EmptyState title="No documents here" body="Upload files above, or pick another folder." />
            ) : (
              <Card className="overflow-hidden"><ul className="divide-y divide-line-soft">
                  {visible.map((d) => (
                    <li key={d.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
                      <div className="flex min-w-0 flex-1 items-center gap-3">
                        <FileTag filename={d.filename} />
                        <div className="min-w-0">
                          <Link href={`/documents/${d.id}`} className="block truncate font-medium hover:text-web">{d.filename}</Link>
                          <p className="text-xs tabular-nums text-muted">{formatBytes(d.file_size_bytes)}</p>
                        </div>
                      </div>
                      <select
                        value={d.folder_id ?? ""}
                        aria-label={`Folder for ${d.filename}`}
                        onChange={(e) => void act(() => documentService.move(id, d.id, e.target.value || null))}
                        className="max-w-44 rounded-lg border border-line bg-sunken px-2 py-1 text-xs focus:border-web"
                      >
                        <option value="">Unfiled</option>
                        {sortedFolders.map(({ f, path }) => <option key={f.id} value={f.id}>{path}</option>)}
                      </select>
                      <StatusBadge status={d.status} />
                    </li>
                  ))}
                </ul></Card>
            )}
          </div>
        </section>
      </div>
    </>
  );
}
