import { request } from "./apiClient";
import { tokenStore } from "@/lib/tokenStore";
import type { TokenResponse, User } from "@/types/api";

export const authService = {
  async register(email: string, password: string): Promise<User> {
    return request<User>("/auth/register", { method: "POST", body: { email, password }, auth: false });
  },
  async login(email: string, password: string): Promise<void> {
    const t = await request<TokenResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    });
    tokenStore.set(t.access_token, t.refresh_token);
  },
  async logout(): Promise<void> {
    try {
      await request<void>("/auth/logout", { method: "POST" });
    } catch {
      /* the local session is cleared regardless */
    } finally {
      tokenStore.clear();
    }
  },
  me: () => request<User>("/auth/me"),
};
