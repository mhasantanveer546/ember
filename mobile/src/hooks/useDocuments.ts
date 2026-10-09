import { useCallback, useEffect, useRef, useState } from "react";
import { documentService } from "@/services/documents";
import type { EmberDocument } from "@/types/api";

const IN_PROGRESS = new Set(["UPLOADING", "PROCESSING", "INDEXING"]);

/**
 * Loads a workspace's documents and polls every 2 s while any is still
 * UPLOADING / PROCESSING / INDEXING. Stops by itself at READY / FAILED.
 */
export function useDocuments(workspaceId: string | null) {
  const [documents, setDocuments] = useState<EmberDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const loadRef = useRef<() => Promise<void>>(async () => {});

  const load = useCallback(async () => {
    if (!workspaceId) return;
    try {
      const docs = await documentService.list(workspaceId);
      setDocuments(docs);
      setError(null);
      if (timer.current) clearTimeout(timer.current);
      if (docs.some((d) => IN_PROGRESS.has(d.status))) timer.current = setTimeout(() => void loadRef.current(), 2000);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    loadRef.current = load;
  }, [load]);

  useEffect(() => {
    setLoading(true);
    void load();
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [load]);

  return { documents, loading, error, reload: load };
}
