import { parseSnippet } from "@/lib/highlight";

export function Snippet({ snippet }: { snippet: string }) {
  if (!snippet) return <span className="italic text-muted">No preview available</span>;
  return (
    <>
      {parseSnippet(snippet).map((p, i) =>
        p.hit ? (
          <mark key={i} className="hit">
            {p.text}
          </mark>
        ) : (
          <span key={i}>{p.text}</span>
        ),
      )}
    </>
  );
}
