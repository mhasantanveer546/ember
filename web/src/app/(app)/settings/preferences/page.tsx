"use client";

import { Card } from "@/components/ui";
import { useTheme } from "@/context/ThemeContext";
import type { ThemePreference } from "@/services/settings";

export default function PreferencesSettings() {
  const { preferences, setTheme, updatePreferences } = useTheme();
  return (
    <Card className="max-w-xl space-y-6">
      <fieldset>
        <legend className="mb-2 text-sm font-medium">Theme</legend>
        <div className="flex gap-2">
          {(["system", "light", "dark"] as ThemePreference[]).map((t) => (
            <label key={t} className={`cursor-pointer rounded-lg border px-4 py-2 text-sm capitalize ${preferences.theme === t ? "border-accent bg-accent-soft text-accent" : "border-line"}`}>
              <input type="radio" name="theme" value={t} checked={preferences.theme === t} onChange={() => setTheme(t)} className="sr-only" />
              {t === "system" ? "Match device" : t}
            </label>
          ))}
        </div>
      </fieldset>
      <label className="block text-sm">
        <span className="mb-2 block font-medium">Results per search</span>
        <select value={preferences.resultsPerSearch} onChange={(e) => updatePreferences({ resultsPerSearch: Number(e.target.value) })} className="rounded-lg border border-line bg-surface px-3 py-2">
          {[10, 20, 50].map((n) => <option key={n} value={n}>{n}</option>)}
        </select>
      </label>
      <p className="text-xs text-muted">Preferences are saved in this browser only.</p>
    </Card>
  );
}
