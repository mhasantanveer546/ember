"use client";

import Link from "next/link";
import { useState } from "react";
import { Button, Card, EmptyState, ErrorNote, Input, LoadingBlock, PageHeader } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { formatDate } from "@/lib/format";
import { workspaceService } from "@/services/workspaces";

export default function WorkspacesPage() {
  const { workspaces, current, loading, error: loadError, select, refresh, create } = useWorkspace();
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<{ id: string; name: string } | null>(null);

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeader title="Workspaces" subtitle="Separate collections of documents you search together." />

      <form
        className="mb-6 flex items-end gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          if (!name.trim()) return;
          void run(async () => {
            await create(name.trim());
            setName("");
          });
        }}
      >
        <div className="flex-1">
          <Input label="New workspace" name="name" value={name} maxLength={255} onChange={(e) => setName(e.target.value)} placeholder="e.g. Networking course" />
        </div>
        <Button type="submit" disabled={busy || !name.trim()}>Create</Button>
      </form>

      {(error || loadError) && <div className="mb-4"><ErrorNote message={(error ?? loadError)!} /></div>}

      {loading ? (
        <LoadingBlock />
      ) : workspaces.length === 0 ? (
        <EmptyState title="No workspaces yet" body="Create one above to start adding documents." />
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2">
          {workspaces.map((w) => (
            <li key={w.id}>
              <Card className={w.id === current?.id ? "border-accent" : ""}>
                {editing?.id === w.id ? (
                  <form
                    className="flex gap-2"
                    onSubmit={(e) => {
                      e.preventDefault();
                      void run(async () => {
                        await workspaceService.rename(w.id, editing.name.trim());
                        setEditing(null);
                        await refresh();
                      });
                    }}
                  >
                    <input autoFocus value={editing.name} onChange={(e) => setEditing({ id: w.id, name: e.target.value })} aria-label="Workspace name" className="min-w-0 flex-1 rounded-lg border border-line bg-bg px-3 py-1.5 text-sm" />
                    <Button type="submit" disabled={busy || !editing.name.trim()} className="!py-1.5">Save</Button>
                    <Button type="button" variant="ghost" onClick={() => setEditing(null)} className="!py-1.5">Cancel</Button>
                  </form>
                ) : (
                  <>
                    <Link href={`/workspaces/${w.id}`} onClick={() => select(w.id)} className="font-serif text-lg font-semibold hover:text-accent">
                      {w.name}
                    </Link>
                    <p className="mt-1 text-xs text-muted">Created {formatDate(w.created_at)}{w.id === current?.id && " · Active"}</p>
                    <div className="mt-4 flex gap-1">
                      {w.id !== current?.id && <Button variant="secondary" className="!px-3 !py-1 text-xs" onClick={() => select(w.id)}>Make active</Button>}
                      <Button variant="ghost" className="!px-3 !py-1 text-xs" onClick={() => setEditing({ id: w.id, name: w.name })}>Rename</Button>
                      <Button
                        variant="danger"
                        className="!px-3 !py-1 text-xs"
                        onClick={() => {
                          if (confirm(`Delete workspace “${w.name}” and ALL its documents? This can't be undone.`)) {
                            void run(async () => {
                              await workspaceService.remove(w.id);
                              await refresh();
                            });
                          }
                        }}
                      >
                        Delete
                      </Button>
                    </div>
                  </>
                )}
              </Card>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
