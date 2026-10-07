"use client";

import { Card, Select } from "@/components/ui";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useTheme } from "@/context/ThemeContext";

export default function PreferencesSettings() {
  const { preferences, updatePreferences } = useTheme();
  return (
    <div className="max-w-xl space-y-4">
      <Card className="p-6">
        <h2 className="text-[17px] font-semibold">Theme</h2>
        <p className="mb-4 mt-1 text-muted">Dark is the default. Auto follows your device.</p>
        <ThemeToggle />
      </Card>
      <Card className="p-6">
        <h2 className="mb-4 text-[17px] font-semibold">Search</h2>
        <div className="max-w-48">
          <Select label="Results per search" value={preferences.resultsPerSearch} onChange={(e) => updatePreferences({ resultsPerSearch: Number(e.target.value) })}>
            {[10, 20, 50].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </Select>
        </div>
      </Card>
      <p className="px-1 text-sm text-muted">Preferences are saved in this browser only.</p>
    </div>
  );
}
