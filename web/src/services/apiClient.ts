/**
 * Shared API client (Phase 6). Every network call in the app goes through
 * here, so auth headers, silent token refresh and error translation live in
 * exactly one place. UI components never call fetch() directly.
 */
import { API_BASE_URL } from "@/lib/config";
import { tokenStore } from "@/lib/tokenStore";
import type { TokenResponse } from "@/types/api";

export const LOGOUT_EVENT = "ember:logout";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Turn a status + backend detail into text that is safe to show a user. */
export function friendlyMessage(status: number, detail: unknown): string {
  const fromBackend = typeof detail === "string" ? detail : null;
  switch (status) {
    case 0:
      return "Can't reach the Ember server. Check your connection and try again.";
    case 401:
      return fromBackend ?? "Your session has expired. Please sign in again.";
    case 403:
      return fromBackend ?? "You don't have permission to do that.";
    case 404:
      return "We couldn't find that. It may have been deleted.";
    case 409:
      return fromBackend ?? "That conflicts with something that already exists.";
    case 413:
      return "That file is too large. The maximum size is 25 MB.";
    case 422:
      if (Array.isArray(detail)) {
        const first = detail[0] as { msg?: string } | undefined;
        if (first?.msg) return first.msg;
      }
      return fromBackend ?? "Some of the information you entered isn't valid.";
    case 429:
      return "Too many requests. Please wait a moment and try again.";
    default:
      if (status >= 500) return "Something went wrong on our side. Please try again shortly.";
      return fromBackend ?? "Something went wrong. Please try again.";
  }
}

async function parseError(res: Response): Promise<ApiError> {
  let detail: unknown;
  try {
    detail = (await res.json())?.detail;
  } catch {
    /* non-JSON body (e.g. a proxy error page): never surface it */
  }
  return new ApiError(res.status, friendlyMessage(res.status, detail), detail);
}

let refreshInFlight: Promise<boolean> | null = null;

/** Single-flight refresh: concurrent 401s share one /auth/refresh call. */
async function refreshTokens(): Promise<boolean> {
  const refresh = tokenStore.getRefresh();
  if (!refresh) return false;
  refreshInFlight ??= (async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) return false;
      const data = (await res.json()) as TokenResponse;
      tokenStore.set(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

function forceLogout() {
  tokenStore.clear();
  if (typeof window !== "undefined") window.dispatchEvent(new Event(LOGOUT_EVENT));
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  auth?: boolean;
  signal?: AbortSignal;
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true, signal } = opts;

  const send = () => {
    const headers: Record<string, string> = {};
    if (body !== undefined) headers["Content-Type"] = "application/json";
    const token = tokenStore.getAccess();
    if (auth && token) headers.Authorization = `Bearer ${token}`;
    return fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    });
  };

  let res: Response;
  try {
    res = await send();
    if (res.status === 401 && auth) {
      if (await refreshTokens()) res = await send();
      else forceLogout();
    }
  } catch (err) {
    if ((err as Error).name === "AbortError") throw err;
    throw new ApiError(0, friendlyMessage(0, null));
  }

  if (!res.ok) {
    if (res.status === 401 && auth) forceLogout();
    throw await parseError(res);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** Multipart upload via XHR, because fetch() can't report upload progress. */
export function uploadWithProgress<T>(
  path: string,
  form: FormData,
  onProgress?: (fraction: number) => void,
): Promise<T> {
  const attempt = (): Promise<{ status: number; text: string }> =>
    new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_BASE_URL}${path}`);
      const token = tokenStore.getAccess();
      if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) onProgress?.(e.loaded / e.total);
      };
      xhr.onload = () => resolve({ status: xhr.status, text: xhr.responseText });
      xhr.onerror = () => reject(new ApiError(0, friendlyMessage(0, null)));
      xhr.send(form);
    });

  return (async () => {
    let result = await attempt();
    if (result.status === 401) {
      if (await refreshTokens()) result = await attempt();
      else forceLogout();
    }
    if (result.status < 200 || result.status >= 300) {
      let detail: unknown;
      try {
        detail = JSON.parse(result.text)?.detail;
      } catch {
        /* ignore */
      }
      throw new ApiError(result.status, friendlyMessage(result.status, detail), detail);
    }
    return JSON.parse(result.text) as T;
  })();
}
