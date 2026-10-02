"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { workspaceService } from "@/services/workspaces";
import { useAuth } from "./AuthContext";
import type { Workspace } from "@/types/api";

const KEY = "ember.workspace";

interface WorkspaceCtx {
  workspaces: Workspace[];
  current: Workspace | null;
  loading: boolean;
  error: string | null;
  select: (id: string) => void;
  refresh: () => Promise<Workspace[]>;
  create: (name: string) => Promise<Workspace>;
}

const Ctx = createContext<WorkspaceCtx | null>(null);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const list = await workspaceService.list();
      setWorkspaces(list);
      setError(null);
      setCurrentId((prev) => {
        const saved = prev ?? window.localStorage.getItem(KEY);
        return list.some((w) => w.id === saved) ? saved : (list[0]?.id ?? null);
      });
      return list;
    } catch (e) {
      setError((e as Error).message);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!user) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data load after sign-in
    void refresh();
  }, [user, refresh]);

  const select = useCallback((id: string) => {
    window.localStorage.setItem(KEY, id);
    setCurrentId(id);
  }, []);

  const create = useCallback(
    async (name: string) => {
      const ws = await workspaceService.create(name);
      await refresh();
      select(ws.id);
      return ws;
    },
    [refresh, select],
  );

  const current = workspaces.find((w) => w.id === currentId) ?? null;

  return (
    <Ctx.Provider value={{ workspaces, current, loading, error, select, refresh, create }}>{children}</Ctx.Provider>
  );
}

export function useWorkspace(): WorkspaceCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error("useWorkspace must be used inside WorkspaceProvider");
  return v;
}
