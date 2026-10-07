"use client";

import { useTheme } from "@/context/ThemeContext";
import type { ThemePreference } from "@/services/settings";

const OPTIONS: { value: ThemePreference; label: string }[] = [
  { value: "dark", label: "Dark" },
  { value: "light", label: "Light" },
  { value: "system", label: "Auto" },
];

/** Three-way segmented control. */
export function ThemeToggle() {
  const { preferences, setTheme } = useTheme();
  return (
    <div role="radiogroup" aria-label="Theme" className="inline-flex rounded-lg bg-sunken p-0.5 text-sm font-medium">
      {OPTIONS.map((o) => (
        <button
          key={o.value}
          role="radio"
          aria-checked={preferences.theme === o.value}
          onClick={() => setTheme(o.value)}
          className={`rounded-md px-3.5 py-1.5 ${preferences.theme === o.value ? "bg-primary text-primary-fg" : "text-muted hover:text-fg"}`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
