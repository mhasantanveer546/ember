/**
 * Settings. The backend has no profile/preferences endpoints yet, so
 * preferences live in this browser's localStorage. They are a convenience,
 * not account data, and won't follow the user to another device.
 */
export type ThemePreference = "light" | "dark" | "system";

export interface Preferences {
  theme: ThemePreference;
  resultsPerSearch: number;
}

const KEY = "ember.preferences";
export const DEFAULT_PREFERENCES: Preferences = { theme: "dark", resultsPerSearch: 20 };

export const settingsService = {
  load(): Preferences {
    if (typeof window === "undefined") return DEFAULT_PREFERENCES;
    try {
      const raw = window.localStorage.getItem(KEY);
      return raw ? { ...DEFAULT_PREFERENCES, ...JSON.parse(raw) } : DEFAULT_PREFERENCES;
    } catch {
      return DEFAULT_PREFERENCES;
    }
  },
  save(prefs: Preferences) {
    window.localStorage.setItem(KEY, JSON.stringify(prefs));
  },
};
