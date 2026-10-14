import { request } from "./apiClient";
import { tokenStore } from "@/lib/tokenStore";
import type { TokenResponse, User } from "@/types/api";

export const authService = {
  register: (email: string, password: string) => request<User>("/auth/register", { method: "POST", body: { email, password }, auth: false }),
  async login(email: string, password: string): Promise<void> {
    const t = await request<TokenResponse>("/auth/login", { method: "POST", body: { email, password }, auth: false });
    await tokenStore.set(t.access_token, t.refresh_token);
  },
  async logout(): Promise<void> {
    try {
      const refresh_token = await tokenStore.getRefresh();
      await request<void>("/auth/logout", { method: "POST", body: refresh_token ? { refresh_token } : undefined });
    } catch {
      /* the local session is cleared regardless */
    } finally {
      await tokenStore.clear();
    }
  },
  me: () => request<User>("/auth/me"),
};
