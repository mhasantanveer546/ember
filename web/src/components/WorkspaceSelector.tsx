"use client";

import { useWorkspace } from "@/context/WorkspaceContext";

export function WorkspaceSelector() {
  const { workspaces, current, select } = useWorkspace();
  if (workspaces.length === 0) return <span className="text-sm text-muted">No workspace yet</span>;
  return (
    <label className="flex items-center gap-2 text-sm">
      <span className="sr-only">Workspace</span>
      <select
        value={current?.id ?? ""}
        onChange={(e) => select(e.target.value)}
        className="max-w-48 rounded-lg border border-line bg-surface px-2.5 py-1.5 text-sm"
      >
        {workspaces.map((w) => (
          <option key={w.id} value={w.id}>
            {w.name}
          </option>
        ))}
      </select>
    </label>
  );
}
