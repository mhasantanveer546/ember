"use client";

import { useTheme } from "@/context/ThemeContext";
import type { ThemePreference } from "@/services/settings";

const OPTIONS: { value: ThemePreference; label: string }[] = [
  { value: "system", label: "Auto" },
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
];

/** Three-way segmented control (not the usual sun/moon switch). */
export function ThemeToggle() {
  const { preferences, setTheme } = useTheme();
  return (
    <div role="radiogroup" aria-label="Theme" className="inline-flex rounded-lg bg-sunken p-0.5 text-xs font-medium">
      {OPTIONS.map((o) => (
        <button
          key={o.value}
          role="radio"
          aria-checked={preferences.theme === o.value}
          onClick={() => setTheme(o.value)}
          className={`rounded-md px-2.5 py-1 ${preferences.theme === o.value ? "bg-surface text-fg shadow-sm" : "text-muted hover:text-fg"}`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
