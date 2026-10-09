/** Types mirroring the FastAPI response schemas (backend/app/schemas). */

export type DocumentStatus = "UPLOADING" | "PROCESSING" | "INDEXING" | "READY" | "FAILED";

export interface User {
  id: string;
  email: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Workspace {
  id: string;
  owner_id: string;
  name: string;
  created_at: string;
}

export interface Folder {
  id: string;
  workspace_id: string;
  parent_folder_id: string | null;
  name: string;
  created_at: string;
}

export interface EmberDocument {
  id: string;
  workspace_id: string;
  folder_id: string | null;
  owner_id: string;
  filename: string;
  mime_type: string;
  file_size_bytes: number;
  status: DocumentStatus;
  created_at: string;
}

export interface DocumentUploadResponse {
  document: EmberDocument;
  is_duplicate: boolean;
}

export interface SearchResultItem {
  document_id: string;
  filename: string;
  score: number;
  snippet: string;
}

export interface SearchResponse {
  query: string;
  is_phrase_search: boolean;
  results: SearchResultItem[];
}

export interface SearchHistoryItem {
  id: string;
  query_text: string;
  created_at: string;
}

export interface IndexMetadata {
  version: number;
  document_count: number;
  vocabulary_size: number;
  last_built_at: string | null;
}
