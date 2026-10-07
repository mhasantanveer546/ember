import { useEffect, useRef, useState } from "react";
import { documentService } from "@/services/documents";

/** Fetches a document's extracted text, caching per document for the lifetime of the page. */
export function useDocumentText(workspaceId: string | null, documentId: string | null) {
  const cache = useRef(new Map<string, string>());
  const [state, setState] = useState<{ id: string; text: string | null; failed: boolean } | null>(null);

  useEffect(() => {
    if (!workspaceId || !documentId) return;
    const hit = cache.current.get(documentId);
    if (hit !== undefined) {
      setState({ id: documentId, text: hit, failed: false });
      return;
    }
    let cancelled = false;
    documentService
      .text(workspaceId, documentId)
      .then((r) => {
        cache.current.set(documentId, r.text);
        if (!cancelled) setState({ id: documentId, text: r.text, failed: false });
      })
      .catch(() => !cancelled && setState({ id: documentId, text: null, failed: true }));
    return () => {
      cancelled = true;
    };
  }, [workspaceId, documentId]);

  const ready = state && state.id === documentId;
  return { text: ready ? state.text : null, failed: ready ? state.failed : false, loading: !ready };
}
