/** Split a backend snippet ("...notes on **database** theory...") into plain/hit parts. */
export function parseSnippet(snippet: string): { text: string; hit: boolean }[] {
  const parts: { text: string; hit: boolean }[] = [];
  snippet.split("**").forEach((chunk, i) => {
    if (chunk) parts.push({ text: chunk, hit: i % 2 === 1 });
  });
  return parts;
}

/** Extract highlightable terms from a raw user query (quotes dropped, words split). */
export function queryTerms(query: string): string[] {
  return Array.from(new Set(query.toLowerCase().replace(/"/g, " ").split(/[^\p{L}\p{N}]+/u).filter((t) => t.length > 1)));
}

export function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
