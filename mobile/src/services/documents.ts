import { request, uploadFile, type PickedFile } from "./apiClient";
import type { DocumentUploadResponse, EmberDocument } from "@/types/api";

export const documentService = {
  list: (workspaceId: string) => request<EmberDocument[]>(`/workspaces/${workspaceId}/documents`),
  get: (workspaceId: string, id: string) => request<EmberDocument>(`/workspaces/${workspaceId}/documents/${id}`),
  text: (workspaceId: string, id: string) => request<{ text: string }>(`/workspaces/${workspaceId}/documents/${id}/text`),
  remove: (workspaceId: string, id: string) => request<void>(`/workspaces/${workspaceId}/documents/${id}`, { method: "DELETE" }),
  reindex: (workspaceId: string, id: string) => request<EmberDocument>(`/workspaces/${workspaceId}/documents/${id}/reindex`, { method: "POST" }),
  upload: (workspaceId: string, file: PickedFile, folderId: string | null, onProgress?: (f: number) => void) =>
    uploadFile<DocumentUploadResponse>(`/workspaces/${workspaceId}/documents`, file, folderId ? { folder_id: folderId } : {}, onProgress),
};
