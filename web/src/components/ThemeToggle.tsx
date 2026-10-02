"use client";

import { useTheme } from "@/context/ThemeContext";
import type { ThemePreference } from "@/services/settings";

const order: ThemePreference[] = ["system", "light", "dark"];
const labels: Record<ThemePreference, string> = { system: "Auto", light: "Light", dark: "Dark" };

export function ThemeToggle() {
  const { preferences, setTheme } = useTheme();
  const next = order[(order.indexOf(preferences.theme) + 1) % order.length];
  return (
    <button
      onClick={() => setTheme(next)}
      className="rounded-lg border border-line px-2.5 py-1.5 text-xs font-medium hover:bg-surface-2"
      aria-label={`Theme: ${labels[preferences.theme]}. Switch to ${labels[next]}`}
      title="Switch theme"
    >
      {labels[preferences.theme]}
    </button>
  );
}
