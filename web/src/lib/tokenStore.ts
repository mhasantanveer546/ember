/**
 * Token storage (browser localStorage).
 *
 * Tradeoff: localStorage is readable by any script on the page, so an XSS bug
 * could steal tokens; httpOnly cookies avoid that but need CSRF protection and
 * backend cookie handling. For this phase we keep the backend's Bearer-token
 * design and mitigate with short-lived access tokens + refresh rotation (the
 * backend already denylists used refresh tokens). Revisit in Phase 8.
 */
const ACCESS = "ember.access";
const REFRESH = "ember.refresh";

const isBrowser = () => typeof window !== "undefined";

export const tokenStore = {
  getAccess: () => (isBrowser() ? window.localStorage.getItem(ACCESS) : null),
  getRefresh: () => (isBrowser() ? window.localStorage.getItem(REFRESH) : null),
  set(access: string, refresh: string) {
    if (!isBrowser()) return;
    window.localStorage.setItem(ACCESS, access);
    window.localStorage.setItem(REFRESH, refresh);
  },
  clear() {
    if (!isBrowser()) return;
    window.localStorage.removeItem(ACCESS);
    window.localStorage.removeItem(REFRESH);
  },
};
