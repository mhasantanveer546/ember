"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { authService } from "@/services/auth";
import { LOGOUT_EVENT } from "@/services/apiClient";
import { tokenStore } from "@/lib/tokenStore";
import type { User } from "@/types/api";

interface AuthCtx {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!tokenStore.getAccess() && !tokenStore.getRefresh()) {
        setLoading(false);
        return;
      }
      try {
        const me = await authService.me();
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    const onForcedLogout = () => setUser(null);
    window.addEventListener(LOGOUT_EVENT, onForcedLogout);
    return () => {
      cancelled = true;
      window.removeEventListener(LOGOUT_EVENT, onForcedLogout);
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    await authService.login(email, password);
    setUser(await authService.me());
  }, []);

  const register = useCallback(
    async (email: string, password: string) => {
      await authService.register(email, password);
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, []);

  return <Ctx.Provider value={{ user, loading, login, register, logout }}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used inside AuthProvider");
  return v;
}
