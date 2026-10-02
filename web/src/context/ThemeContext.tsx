"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { DEFAULT_PREFERENCES, settingsService, type Preferences, type ThemePreference } from "@/services/settings";

interface ThemeCtx {
  preferences: Preferences;
  setTheme: (t: ThemePreference) => void;
  updatePreferences: (p: Partial<Preferences>) => void;
}

const Ctx = createContext<ThemeCtx | null>(null);

function applyTheme(t: ThemePreference) {
  const dark = t === "dark" || (t === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.classList.toggle("dark", dark);
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [preferences, setPreferences] = useState<Preferences>(DEFAULT_PREFERENCES);

  useEffect(() => {
    const loaded = settingsService.load();
    // eslint-disable-next-line react-hooks/set-state-in-effect -- hydrate from localStorage after mount
    setPreferences(loaded);
    applyTheme(loaded.theme);
  }, []);

  useEffect(() => {
    if (preferences.theme !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => applyTheme("system");
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [preferences.theme]);

  const updatePreferences = useCallback((patch: Partial<Preferences>) => {
    setPreferences((prev) => {
      const next = { ...prev, ...patch };
      settingsService.save(next);
      if (patch.theme) applyTheme(next.theme);
      return next;
    });
  }, []);

  const setTheme = useCallback((t: ThemePreference) => updatePreferences({ theme: t }), [updatePreferences]);

  return <Ctx.Provider value={{ preferences, setTheme, updatePreferences }}>{children}</Ctx.Provider>;
}

export function useTheme(): ThemeCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error("useTheme must be used inside ThemeProvider");
  return v;
}
