"use client";

import Link from "next/link";
import { useWorkspace } from "@/context/WorkspaceContext";
import { Icon } from "./Icon";

/** The workspace is the user's current "collection", so it gets a prominent place in the sidebar. */
export function WorkspaceSelector() {
  const { workspaces, current, select } = useWorkspace();
  if (workspaces.length === 0) {
    return (
      <Link href="/workspaces" className="block rounded-lg border border-dashed border-line px-3 py-2 text-sm text-muted hover:bg-sunken">
        Create a workspace
      </Link>
    );
  }
  return (
    <label className="relative block">
      <span className="sr-only">Workspace</span>
      <select
        value={current?.id ?? ""}
        onChange={(e) => select(e.target.value)}
        className="w-full cursor-pointer appearance-none truncate rounded-lg bg-sunken py-2 pl-3 pr-9 text-sm font-semibold hover:bg-line-soft"
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
