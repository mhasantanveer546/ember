/**
 * Non-secret preferences (e.g. last active workspace id). Tiny values, kept in
 * the same secure store for simplicity; falls back to localStorage on web.
 */
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

export default {
  async get(key: string): Promise<string | null> {
    try {
      return Platform.OS === "web" ? window.localStorage.getItem(key) : await SecureStore.getItemAsync(key);
    } catch {
      return null;
    }
  },
  async set(key: string, value: string): Promise<void> {
    try {
      if (Platform.OS === "web") window.localStorage.setItem(key, value);
      else await SecureStore.setItemAsync(key, value);
    } catch {
      /* preference only: ignore storage failures */
    }
  },
};
