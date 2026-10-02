import { request } from "./apiClient";
import type { SearchHistoryItem, SearchResponse } from "@/types/api";

export const searchService = {
  search: (workspaceId: string, query: string, limit = 20, signal?: AbortSignal) =>
    request<SearchResponse>(`/workspaces/${workspaceId}/search`, {
      method: "POST",
      body: { query, limit },
      signal,
    }),
  async autocomplete(workspaceId: string, prefix: string, signal?: AbortSignal): Promise<string[]> {
    const q = new URLSearchParams({ prefix, limit: "6" });
    const r = await request<{ suggestions: string[] }>(
      `/workspaces/${workspaceId}/search/autocomplete?${q}`,
      { signal },
    );
    return r.suggestions;
  },
  async history(workspaceId: string, limit = 20): Promise<SearchHistoryItem[]> {
    const r = await request<{ history: SearchHistoryItem[] }>(
      `/workspaces/${workspaceId}/search/history?limit=${limit}`,
    );
    return r.history;
  },
};
