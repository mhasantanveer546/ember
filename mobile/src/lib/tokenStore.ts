/**
 * Token storage in the platform's secure store (iOS Keychain / Android Keystore
 * via expo-secure-store). Unlike AsyncStorage, values are encrypted at rest.
 * Tokens are cached in memory after load() so the API client can read them synchronously.
 * (On web, used only for the dev preview, it falls back to localStorage.)
 */
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

const ACCESS = "ember.access";
const REFRESH = "ember.refresh";

let access: string | null = null;
let refresh: string | null = null;

const read = async (k: string) => (Platform.OS === "web" ? window.localStorage.getItem(k) : SecureStore.getItemAsync(k));
const write = async (k: string, v: string) => (Platform.OS === "web" ? void window.localStorage.setItem(k, v) : SecureStore.setItemAsync(k, v));
const remove = async (k: string) => (Platform.OS === "web" ? void window.localStorage.removeItem(k) : SecureStore.deleteItemAsync(k));

export const tokenStore = {
  async load() {
    [access, refresh] = await Promise.all([read(ACCESS), read(REFRESH)]);
  },
  getAccess: () => access,
  getRefresh: () => refresh,
  async set(a: string, r: string) {
    access = a;
    refresh = r;
    await Promise.all([write(ACCESS, a), write(REFRESH, r)]);
  },
  async clear() {
    access = null;
    refresh = null;
    await Promise.all([remove(ACCESS), remove(REFRESH)]);
  },
};
