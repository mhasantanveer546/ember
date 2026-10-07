"use client";

import Link from "next/link";
import { useState } from "react";
import { Button, Card, EmptyState, ErrorNote, Input, PageHeader, RowsSkeleton } from "@/components/ui";
import { Icon } from "@/components/Icon";
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

      <Card className="mb-6 p-5">
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
      </Card>

      {(error || loadError) && <div className="mb-6"><ErrorNote message={(error ?? loadError)!} /></div>}

      {loading ? (
        <RowsSkeleton rows={3} />
      ) : workspaces.length === 0 ? (
        <EmptyState title="No workspaces yet" body="Create one above, then add documents to it." />
      ) : (
        <Card className="overflow-hidden">
          <ul className="divide-y divide-line-soft">
            {workspaces.map((w) => (
              <li key={w.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-5 py-4">
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
                    <input autoFocus value={editing.name} onChange={(e) => setEditing({ id: w.id, name: e.target.value })} aria-label="Workspace name" className="min-w-0 flex-1 rounded-lg border border-line bg-sunken px-3 py-1.5 text-sm focus:border-web" />
                    <Button type="submit" size="sm" disabled={busy || !editing.name.trim()}>Save</Button>
                    <Button type="button" variant="ghost" size="sm" onClick={() => setEditing(null)}>Cancel</Button>
                  </form>
                ) : (
                  <>
                    <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sunken text-web"><Icon name="layers" /></span>
                    <div className="min-w-0 flex-1">
                      <Link href={`/workspaces/${w.id}`} onClick={() => select(w.id)} className="text-[17px] font-semibold hover:text-web">{w.name}</Link>
                      <p className="mt-0.5 flex items-center gap-2 text-sm text-muted">
                        Created {formatDate(w.created_at)}
                        {w.id === current?.id && (
                          <span className="inline-flex items-center gap-1.5 font-medium text-green"><span className="h-1.5 w-1.5 rounded-full bg-green" /> Active</span>
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
        </Card>
      )}
    </>
  );
}
