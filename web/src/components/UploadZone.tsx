"use client";

import { useRef, useState } from "react";
import { documentService } from "@/services/documents";
import { fileExtension, formatBytes } from "@/lib/format";

const ALLOWED = ["pdf", "txt", "md", "docx"];
const MAX_BYTES = 25 * 1024 * 1024;

interface Item {
  id: number;
  name: string;
  progress: number;
  state: "uploading" | "done" | "duplicate" | "error";
  message?: string;
}

/** Client-side checks are for fast feedback only; the backend re-validates everything. */
function precheck(file: File): string | null {
  if (!ALLOWED.includes(fileExtension(file.name))) return "Unsupported type. Use PDF, TXT, MD or DOCX.";
  if (file.size > MAX_BYTES) return `Too large (${formatBytes(file.size)}). Maximum is 25 MB.`;
  if (file.size === 0) return "This file is empty.";
  return null;
}

export function UploadZone({
  workspaceId,
  folderId = null,
  onUploaded,
}: {
  workspaceId: string;
  folderId?: string | null;
  onUploaded: () => void;
}) {
  const [items, setItems] = useState<Item[]>([]);
  const [dragging, setDragging] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const counter = useRef(0);

  const patch = (id: number, p: Partial<Item>) => setItems((prev) => prev.map((i) => (i.id === id ? { ...i, ...p } : i)));

  const handleFiles = async (files: FileList | File[]) => {
    for (const file of Array.from(files)) {
      const id = ++counter.current;
      const problem = precheck(file);
      setItems((prev) => [{ id, name: file.name, progress: 0, state: problem ? "error" : "uploading", message: problem ?? undefined }, ...prev]);
      if (problem) continue;
      try {
        const res = await documentService.upload(workspaceId, file, folderId, (f) => patch(id, { progress: f }));
        patch(id, res.is_duplicate ? { state: "duplicate", progress: 1, message: "Already in this workspace" } : { state: "done", progress: 1 });
        onUploaded();
      } catch (e) {
        patch(id, { state: "error", message: (e as Error).message });
      }
    }
  };

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          void handleFiles(e.dataTransfer.files);
        }}
        className={`rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors ${
          dragging ? "border-accent bg-accent-soft" : "border-line bg-surface"
        }`}
      >
        <p className="font-medium">Drop files here to add them to your knowledge</p>
        <p className="mt-1 text-sm text-muted">PDF, TXT, Markdown or DOCX, up to 25 MB each</p>
        <button
          onClick={() => input.current?.click()}
          className="mt-4 rounded-lg border border-line bg-surface px-4 py-2 text-sm font-medium hover:bg-surface-2"
        >
          Choose files
        </button>
        <input
          ref={input}
          type="file"
          multiple
          accept=".pdf,.txt,.md,.docx"
          className="hidden"
          onChange={(e) => {
            if (e.target.files) void handleFiles(e.target.files);
            e.target.value = "";
          }}
        />
      </div>

      {items.length > 0 && (
        <ul className="mt-3 space-y-2">
          {items.slice(0, 6).map((i) => (
            <li key={i.id} className="rounded-lg border border-line bg-surface px-3 py-2 text-sm">
              <div className="flex items-center justify-between gap-3">
                <span className="truncate">{i.name}</span>
                <span className={i.state === "error" ? "text-danger" : i.state === "done" ? "text-ok" : "text-muted"}>
                  {i.state === "uploading" && `${Math.round(i.progress * 100)}%`}
                  {i.state === "done" && "Uploaded"}
                  {i.state === "duplicate" && "Duplicate"}
                  {i.state === "error" && "Failed"}
                </span>
              </div>
              {i.state === "uploading" && (
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-2">
                  <div className="h-full bg-accent transition-all" style={{ width: `${i.progress * 100}%` }} />
                </div>
              )}
              {i.message && <p className={`mt-1 text-xs ${i.state === "error" ? "text-danger" : "text-muted"}`}>{i.message}</p>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
