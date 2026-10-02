import type { DocumentStatus } from "@/types/api";

const styles: Record<DocumentStatus, { label: string; cls: string; pulse?: boolean }> = {
  UPLOADING: { label: "Uploading", cls: "text-warn", pulse: true },
  PROCESSING: { label: "Processing", cls: "text-warn", pulse: true },
  INDEXING: { label: "Indexing", cls: "text-warn", pulse: true },
  READY: { label: "Ready", cls: "text-ok" },
  FAILED: { label: "Failed", cls: "text-danger" },
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  const s = styles[status];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border border-line px-2 py-0.5 text-xs font-medium ${s.cls}`}>
      <span className={`h-1.5 w-1.5 rounded-full bg-current ${s.pulse ? "animate-pulse" : ""}`} />
      {s.label}
    </span>
  );
}
