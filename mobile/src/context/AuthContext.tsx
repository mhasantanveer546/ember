import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { onForcedLogout } from "@/services/apiClient";
import { authService } from "@/services/auth";
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      await tokenStore.load();
      if (tokenStore.getAccess() || tokenStore.getRefresh()) {
        try {
          const me = await authService.me();
          if (!cancelled) setUser(me);
        } catch {
          if (!cancelled) setUser(null);
        }
      }
      if (!cancelled) setLoading(false);
    })();
    const off = onForcedLogout(() => setUser(null));
    return () => {
      cancelled = true;
      off();
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
