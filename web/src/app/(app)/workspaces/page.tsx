"use client";

import Link from "next/link";
import { useState } from "react";
import { Button, EmptyState, ErrorNote, Input, PageHeader, RowsSkeleton } from "@/components/ui";
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
      <PageHeader title="Workspaces" subtitle="Each workspace is a separate collection you search together." />

      <form
        className="flex flex-wrap items-end gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          if (!name.trim()) return;
          void run(async () => {
            await create(name.trim());
            setName("");
          });
        }}
      >
        <div className="min-w-56 flex-1">
          <Input label="New workspace" name="name" value={name} maxLength={255} onChange={(e) => setName(e.target.value)} placeholder="Networking course" />
        </div>
        <Button type="submit" disabled={busy || !name.trim()}>Create workspace</Button>
      </form>

      {(error || loadError) && <div className="mt-6"><ErrorNote message={(error ?? loadError)!} /></div>}

      <div className="mt-10">
        {loading ? (
          <RowsSkeleton rows={3} />
        ) : workspaces.length === 0 ? (
          <EmptyState title="No workspaces yet" body="Create one above, then add documents to it." />
        ) : (
          <ul className="border-t border-line">
            {workspaces.map((w) => (
              <li key={w.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-line-soft py-4">
                {editing?.id === w.id ? (
                  <form
                    className="flex min-w-0 flex-1 gap-2"
                    onSubmit={(e) => {
                      e.preventDefault();
                      void run(async () => {
                        await workspaceService.rename(w.id, editing.name.trim());
                        setEditing(null);
                        await refresh();
                      });
                    }}
                  >
                    <input autoFocus value={editing.name} onChange={(e) => setEditing({ id: w.id, name: e.target.value })} aria-label="Workspace name" className="min-w-0 flex-1 rounded-lg border border-line bg-surface px-3 py-1.5 text-sm focus:border-ink" />
                    <Button type="submit" size="sm" disabled={busy || !editing.name.trim()}>Save</Button>
                    <Button type="button" variant="ghost" size="sm" onClick={() => setEditing(null)}>Cancel</Button>
                  </form>
                ) : (
                  <>
                    <div className="min-w-0 flex-1">
                      <Link href={`/workspaces/${w.id}`} onClick={() => select(w.id)} className="display text-xl hover:text-ember-text">
                        {w.name}
                      </Link>
                      <p className="mt-0.5 flex items-center gap-2 text-sm text-muted">
                        Created {formatDate(w.created_at)}
                        {w.id === current?.id && (
                          <span className="inline-flex items-center gap-1.5 font-medium text-ember-text">
                            <span className="h-1.5 w-1.5 rounded-full bg-ember" /> Active
                          </span>
                        )}
                      </p>
                    </div>
                    <div className="flex gap-1">
                      {w.id !== current?.id && <Button variant="secondary" size="sm" onClick={() => select(w.id)}>Make active</Button>}
                      <Button variant="ghost" size="sm" onClick={() => setEditing({ id: w.id, name: w.name })}>Rename</Button>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => {
                          if (confirm(`Delete the workspace “${w.name}” and all of its documents? This can’t be undone.`)) {
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
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}
