"use client";

import { Select } from "@/components/ui";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useTheme } from "@/context/ThemeContext";

export default function PreferencesSettings() {
  const { preferences, updatePreferences } = useTheme();
  return (
    <div className="max-w-lg divide-y divide-line-soft border-y border-line-soft">
      <section className="py-6">
        <h2 className="display text-lg">Theme</h2>
        <p className="mb-4 mt-1 text-muted">Auto follows your device.</p>
        <ThemeToggle />
      </section>
      <section className="py-6">
        <h2 className="display mb-4 text-lg">Search</h2>
        <div className="max-w-48">
          <Select label="Results per search" value={preferences.resultsPerSearch} onChange={(e) => updatePreferences({ resultsPerSearch: Number(e.target.value) })}>
            {[10, 20, 50].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </Select>
        </div>
      </section>
      <p className="py-4 text-sm text-muted">Preferences are saved in this browser only.</p>
    </div>
  );
}
