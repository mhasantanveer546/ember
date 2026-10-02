import { request, uploadWithProgress } from "./apiClient";
import type { DocumentUploadResponse, EmberDocument } from "@/types/api";

export const documentService = {
  list: (workspaceId: string) => request<EmberDocument[]>(`/workspaces/${workspaceId}/documents`),
  get: (workspaceId: string, id: string) =>
    request<EmberDocument>(`/workspaces/${workspaceId}/documents/${id}`),
  text: (workspaceId: string, id: string) =>
    request<{ text: string }>(`/workspaces/${workspaceId}/documents/${id}/text`),
  remove: (workspaceId: string, id: string) =>
    request<void>(`/workspaces/${workspaceId}/documents/${id}`, { method: "DELETE" }),
  reindex: (workspaceId: string, id: string) =>
    request<EmberDocument>(`/workspaces/${workspaceId}/documents/${id}/reindex`, { method: "POST" }),
  move: (workspaceId: string, id: string, folderId: string | null) =>
    request<EmberDocument>(`/workspaces/${workspaceId}/documents/${id}`, {
      method: "PATCH",
      body: { folder_id: folderId },
    }),
  upload(
    workspaceId: string,
    file: File,
    folderId: string | null,
    onProgress?: (fraction: number) => void,
  ): Promise<DocumentUploadResponse> {
    const form = new FormData();
    form.append("file", file);
    if (folderId) form.append("folder_id", folderId);
    return uploadWithProgress<DocumentUploadResponse>(`/workspaces/${workspaceId}/documents`, form, onProgress);
  },
};
