"use client";

import Link from "next/link";
import { useWorkspace } from "@/context/WorkspaceContext";
import { Icon } from "./Icon";

/** The current workspace, switchable from the top bar. */
export function WorkspaceSelector() {
  const { workspaces, current, select } = useWorkspace();
  if (workspaces.length === 0) {
    return (
      <Link href="/workspaces" className="block truncate rounded-full border border-dashed border-line px-3.5 py-1.5 text-sm text-muted hover:bg-sunken">
        Create a workspace
      </Link>
    );
  }
  return (
    <label className="relative block">
      <span className="sr-only">Workspace</span>
      <Icon name="layers" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
      <select
        value={current?.id ?? ""}
        onChange={(e) => select(e.target.value)}
        className="w-full cursor-pointer appearance-none truncate rounded-full border border-line-soft bg-surface/80 py-1.5 pl-9 pr-8 text-sm font-medium backdrop-blur hover:bg-sunken"
      >
        {workspaces.map((w) => (
          <option key={w.id} value={w.id}>
            {w.name}
          </option>
        ))}
      </select>
      <Icon name="chevron" className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
    </label>
  );
}
