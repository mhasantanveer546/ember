import { Platform } from "react-native";

/**
 * Base URL of the Ember API.
 *
 * Set EXPO_PUBLIC_API_URL (see mobile/.env.example). Defaults for local dev:
 *  - Android emulator reaches your computer at 10.0.2.2 (not localhost).
 *  - iOS simulator can use localhost.
 *  - A PHYSICAL phone needs your computer's LAN IP, e.g. http://192.168.1.20:8000,
 *    and the API must listen on 0.0.0.0 (uvicorn --host 0.0.0.0).
 * Production builds must use https.
 */
const fallback = Platform.OS === "android" ? "http://10.0.2.2:8000" : "http://localhost:8000";
export const API_BASE_URL = (process.env.EXPO_PUBLIC_API_URL ?? fallback).replace(/\/$/, "");
