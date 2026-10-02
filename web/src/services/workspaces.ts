import { request } from "./apiClient";
import type { Folder, IndexMetadata, Workspace } from "@/types/api";

export const workspaceService = {
  list: () => request<Workspace[]>("/workspaces"),
  create: (name: string) => request<Workspace>("/workspaces", { method: "POST", body: { name } }),
  rename: (id: string, name: string) =>
    request<Workspace>(`/workspaces/${id}`, { method: "PATCH", body: { name } }),
  remove: (id: string) => request<void>(`/workspaces/${id}`, { method: "DELETE" }),

  folders: (workspaceId: string) => request<Folder[]>(`/workspaces/${workspaceId}/folders`),
  createFolder: (workspaceId: string, name: string, parentFolderId: string | null = null) =>
    request<Folder>(`/workspaces/${workspaceId}/folders`, {
      method: "POST",
      body: { name, parent_folder_id: parentFolderId },
    }),
  renameFolder: (workspaceId: string, folderId: string, name: string) =>
    request<Folder>(`/workspaces/${workspaceId}/folders/${folderId}`, { method: "PATCH", body: { name } }),
  removeFolder: (workspaceId: string, folderId: string) =>
    request<void>(`/workspaces/${workspaceId}/folders/${folderId}`, { method: "DELETE" }),

  indexMetadata: (workspaceId: string) => request<IndexMetadata>(`/workspaces/${workspaceId}/index`),
  rebuildIndex: (workspaceId: string) =>
    request<{ document_count: number; vocabulary_size: number; failed_document_count: number }>(
      `/workspaces/${workspaceId}/index/rebuild`,
      { method: "POST" },
    ),
};
