import { escapeRegExp } from "@/lib/highlight";

/** Renders text with query terms wrapped in <mark>. Never uses innerHTML. */
export function HighlightedText({ text, terms, activeHit }: { text: string; terms: string[]; activeHit?: number }) {
  if (terms.length === 0) return <>{text}</>;
  const re = new RegExp(`(${terms.map(escapeRegExp).join("|")})`, "gi");
  let n = 0;
  return (
    <>
      {text.split(re).map((s, i) =>
        i % 2 === 1 ? (
          <mark key={i} data-hit={n} className={`hit ${n++ === activeHit ? "active" : ""}`}>
            {s}
          </mark>
        ) : (
          <span key={i}>{s}</span>
        ),
      )}
    </>
  );
}
