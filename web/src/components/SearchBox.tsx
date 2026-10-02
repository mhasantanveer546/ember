"use client";

import { useEffect, useRef, useState } from "react";
import { searchService } from "@/services/search";
import { useDebounced } from "@/hooks/useDebounced";

interface Props {
  workspaceId: string | null;
  initialValue?: string;
  autoFocus?: boolean;
  onSubmit: (query: string) => void;
  loading?: boolean;
}

/** Search input with debounced prefix autocomplete (last word of the query). */
export function SearchBox({ workspaceId, initialValue = "", autoFocus, onSubmit, loading }: Props) {
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
      .catch(() => setSuggestions([])); // autocomplete is best-effort: never block searching
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

  return (
    <div ref={wrapper} className="relative">
      <div className="flex gap-2">
        <input
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
          placeholder='Search your knowledge… try "exact phrase"'
          aria-label="Search"
          role="combobox"
          aria-expanded={open && suggestions.length > 0}
          aria-autocomplete="list"
          aria-controls="ember-suggestions"
          disabled={!workspaceId}
          className="w-full rounded-xl border border-line bg-surface px-4 py-3 text-base shadow-sm placeholder:text-muted focus:border-accent disabled:opacity-50"
        />
        <button
          onClick={submit}
          disabled={!workspaceId || !value.trim() || loading}
          className="rounded-xl bg-accent px-5 text-sm font-medium text-accent-fg hover:bg-accent-hover disabled:opacity-50"
        >
          Search
        </button>
      </div>
      {open && suggestions.length > 0 && (
        <ul id="ember-suggestions" role="listbox" className="absolute z-10 mt-1 w-full overflow-hidden rounded-xl border border-line bg-surface shadow-lg">
          {suggestions.map((s, i) => (
            <li key={s} role="option" aria-selected={i === active}>
              <button
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => applySuggestion(s)}
                className={`block w-full px-4 py-2 text-left text-sm ${i === active ? "bg-accent-soft" : "hover:bg-surface-2"}`}
              >
                {s}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
