import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, friendlyMessage, request } from "./apiClient";
import { tokenStore } from "@/lib/tokenStore";

const json = (status: number, body?: unknown) =>
  new Response(body === undefined ? null : JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

describe("friendlyMessage", () => {
  it.each([
    [0, /reach/i],
    [403, /permission/i],
    [404, /couldn't find/i],
    [413, /25 MB/],
    [429, /too many/i],
    [500, /our side/i],
  ])("maps %i to a readable message", (status, re) => {
    expect(friendlyMessage(status, undefined)).toMatch(re);
  });
  it("shows the first validation message for 422", () => {
    expect(friendlyMessage(422, [{ msg: "value is not a valid email address" }])).toBe("value is not a valid email address");
  });
  it("never leaks a backend body for 5xx", () => {
    expect(friendlyMessage(500, "Traceback (most recent call last): secret")).not.toMatch(/Traceback/);
  });
});

describe("request", () => {
  beforeEach(() => {
    window.localStorage.clear();
    tokenStore.set("old-access", "old-refresh");
  });
  afterEach(() => vi.restoreAllMocks());

  it("sends the bearer token", async () => {
    const f = vi.spyOn(globalThis, "fetch").mockResolvedValue(json(200, { ok: 1 }));
    await request("/x");
    expect((f.mock.calls[0][1]!.headers as Record<string, string>).Authorization).toBe("Bearer old-access");
  });

  it("refreshes once on 401, stores the rotated tokens and retries", async () => {
    const f = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(json(401, { detail: "expired" }))
      .mockResolvedValueOnce(json(200, { access_token: "new-access", refresh_token: "new-refresh", token_type: "bearer" }))
      .mockResolvedValueOnce(json(200, { hello: "world" }));
    await expect(request("/x")).resolves.toEqual({ hello: "world" });
    expect(f).toHaveBeenCalledTimes(3);
    expect(tokenStore.getAccess()).toBe("new-access");
    expect(tokenStore.getRefresh()).toBe("new-refresh");
  });

  it("shares one refresh call between concurrent 401s", async () => {
    let refreshCalls = 0;
    vi.spyOn(globalThis, "fetch").mockImplementation(async (url, init) => {
      if (String(url).endsWith("/auth/refresh")) {
        refreshCalls++;
        return json(200, { access_token: "n", refresh_token: "r", token_type: "bearer" });
      }
      const auth = (init!.headers as Record<string, string>).Authorization;
      return auth === "Bearer n" ? json(200, { ok: true }) : json(401, { detail: "expired" });
    });
    await Promise.all([request("/a"), request("/b"), request("/c")]);
    expect(refreshCalls).toBe(1);
  });

  it("clears tokens and signals logout when refresh fails", async () => {
    const onLogout = vi.fn();
    window.addEventListener("ember:logout", onLogout);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(json(401, { detail: "nope" }));
    await expect(request("/x")).rejects.toBeInstanceOf(ApiError);
    expect(tokenStore.getAccess()).toBeNull();
    expect(onLogout).toHaveBeenCalled();
    window.removeEventListener("ember:logout", onLogout);
  });

  it("turns a network failure into a friendly status-0 error", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(request("/x")).rejects.toMatchObject({ status: 0 });
  });

  it("does not attach a token or refresh for unauthenticated calls (login)", async () => {
    const f = vi.spyOn(globalThis, "fetch").mockResolvedValue(json(401, { detail: "Incorrect email or password" }));
    await expect(request("/auth/login", { method: "POST", body: {}, auth: false })).rejects.toThrow("Incorrect email or password");
    expect(f).toHaveBeenCalledTimes(1);
  });
});
