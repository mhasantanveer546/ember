"use client";

import { useEffect, useRef, useState } from "react";
import { searchService } from "@/services/search";
import { useDebounced } from "@/hooks/useDebounced";
import { Icon } from "./Icon";

interface Props {
  workspaceId: string | null;
  initialValue?: string;
  autoFocus?: boolean;
  onSubmit: (query: string) => void;
  loading?: boolean;
  size?: "md" | "lg";
}

/** Search input with debounced prefix autocomplete on the last word of the query. */
export function SearchBox({ workspaceId, initialValue = "", autoFocus, onSubmit, loading, size = "lg" }: Props) {
  const [value, setValue] = useState(initialValue);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const wrapper = useRef<HTMLDivElement>(null);

  const debounced = useDebounced(value, 180);
  const lastWord = debounced.split(/\s+/).pop() ?? "";

  useEffect(() => {
    if (!workspaceId || lastWord.length < 2 || lastWord.startsWith('"')) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- clear stale suggestions
      setSuggestions([]);
      return;
    }
    const ctrl = new AbortController();
    searchService
      .autocomplete(workspaceId, lastWord, ctrl.signal)
      .then((s) => setSuggestions(s.filter((x) => x !== lastWord.toLowerCase())))
      .catch(() => setSuggestions([])); // best-effort: autocomplete never blocks searching
    return () => ctrl.abort();
  }, [workspaceId, lastWord]);

  useEffect(() => {
    const close = (e: MouseEvent) => {
      if (!wrapper.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const applySuggestion = (s: string) => {
    const words = value.split(/\s+/);
    words[words.length - 1] = s;
    const next = words.join(" ");
    setValue(next);
    setOpen(false);
    setActive(-1);
    onSubmit(next);
  };

  const submit = () => {
    const q = value.trim();
    if (!q) return;
    setOpen(false);
    onSubmit(q);
  };

  const big = size === "lg";

  return (
    <div ref={wrapper} className="relative">
      <div className={`flex items-center gap-2 rounded-2xl border border-line bg-surface pl-4 pr-2 shadow-sm focus-within:border-ember focus-within:ring-4 focus-within:ring-ember/15 ${big ? "py-2" : "py-1"}`}>
        <Icon name="search" className={`shrink-0 text-faint ${big ? "h-5 w-5" : "h-[18px] w-[18px]"}`} />
        <input
          data-search-input
          type="search"
          value={value}
          autoFocus={autoFocus}
          onChange={(e) => {
            setValue(e.target.value);
            setOpen(true);
            setActive(-1);
          }}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown" && suggestions.length) {
              e.preventDefault();
              setActive((a) => (a + 1) % suggestions.length);
            } else if (e.key === "ArrowUp" && suggestions.length) {
              e.preventDefault();
              setActive((a) => (a <= 0 ? suggestions.length - 1 : a - 1));
            } else if (e.key === "Enter") {
              e.preventDefault();
              if (open && active >= 0) applySuggestion(suggestions[active]);
              else submit();
            } else if (e.key === "Escape") setOpen(false);
          }}
          placeholder={big ? "A word, a half-remembered phrase…" : "Search…"}
          aria-label="Search your documents"
          role="combobox"
          aria-expanded={open && suggestions.length > 0}
          aria-autocomplete="list"
          aria-controls="ember-suggestions"
          disabled={!workspaceId}
          className={`min-w-0 flex-1 bg-transparent outline-none placeholder:text-faint disabled:opacity-50 ${big ? "py-2 text-lg" : "py-1.5 text-base"}`}
        />
        <button
          onClick={submit}
          disabled={!workspaceId || !value.trim() || loading}
          className={`shrink-0 rounded-xl bg-ink font-medium text-ink-fg hover:opacity-90 disabled:opacity-40 ${big ? "px-5 py-2.5 text-sm" : "px-4 py-2 text-sm"}`}
        >
          Search
        </button>
      </div>
      {open && suggestions.length > 0 && (
        <ul id="ember-suggestions" role="listbox" className="absolute z-10 mt-2 w-full overflow-hidden rounded-xl border border-line bg-surface p-1 shadow-pop">
          {suggestions.map((s, i) => {
            const prefix = lastWord.toLowerCase();
            const hasPrefix = s.startsWith(prefix);
            return (
              <li key={s} role="option" aria-selected={i === active}>
                <button
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => applySuggestion(s)}
                  className={`block w-full rounded-lg px-3 py-2 text-left text-[15px] ${i === active ? "bg-sunken" : "hover:bg-sunken"}`}
                >
                  {hasPrefix ? (
                    <>
                      <span className="font-semibold">{s.slice(0, prefix.length)}</span>
                      <span className="text-muted">{s.slice(prefix.length)}</span>
                    </>
                  ) : (
                    s
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
