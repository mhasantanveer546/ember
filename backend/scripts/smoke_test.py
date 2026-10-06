"""
Ember — end-to-end smoke test against a RUNNING API (+ worker + Redis).

    python backend/scripts/smoke_test.py [--api http://localhost:8000]

Uses only the standard library. Creates a throwaway user and workspace
(random email), exercises the real pipeline and prints PASS/FAIL per step.
Exit code 0 only if every step passes.
"""

import argparse
import json
import sys
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request

PASSWORD = "correcthorsebattery"
results: list[tuple[str, bool, str]] = []


def call(api, method, path, token=None, body=None, files=None):
    headers = {}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if files:
        boundary = uuid.uuid4().hex
        parts = []
        for name, (filename, content, ctype) in files.items():
            parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                f"Content-Type: {ctype}\r\n\r\n".encode() + content + b"\r\n"
            )
        data = b"".join(parts) + f"--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(api + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            try:
                return r.status, (json.loads(raw) if raw else None)
            except ValueError:  # non-JSON body (e.g. the /docs HTML page)
                return r.status, None
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, None


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not ok else ""))
    return ok


def register_and_login(api, email):
    call(api, "POST", "/auth/register", body={"email": email, "password": PASSWORD})
    _, tok = call(api, "POST", "/auth/login", body={"email": email, "password": PASSWORD})
    return tok["access_token"] if tok else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000")
    api = ap.parse_args().api.rstrip("/")

    try:
        status, _ = call(api, "GET", "/docs")
    except Exception as e:
        print(f"Cannot reach the API at {api}: {e}\nStart it first (see docs/RUNNING.md).")
        return 1
    if not check("API reachable", status == 200, f"HTTP {status}"):
        return 1

    run = uuid.uuid4().hex[:8]
    token = register_and_login(api, f"smoke-{run}@example.com")
    if not check("Register + login", token):
        return 1

    status, ws = call(api, "POST", "/workspaces", token, {"name": f"Smoke {run}"})
    if not check("Create workspace", status in (200, 201) and ws, f"HTTP {status}"):
        return 1
    wid = ws["id"]

    text = (f"TCP congestion control uses slow start and AIMD {run}.\n"
            "Database normalization reduces redundancy.\n").encode()
    status, up = call(api, "POST", f"/workspaces/{wid}/documents", token,
                      files={"file": ("notes.txt", text, "text/plain")})
    if not check("Upload document", status in (200, 201) and up, f"HTTP {status}"):
        return 1
    did = up["document"]["id"]

    final = "?"
    for _ in range(30):  # up to ~30 s for the worker
        _, doc = call(api, "GET", f"/workspaces/{wid}/documents/{did}", token)
        final = doc["status"] if doc else "?"
        if final in ("READY", "FAILED"):
            break
        time.sleep(1)
    if not check("Worker processes document -> READY", final == "READY",
                 f"stuck at {final}: is the worker running (python backend/scripts/run_worker.py)?"):
        return 1

    _, r = call(api, "POST", f"/workspaces/{wid}/search", token, {"query": "congestion control"})
    hit = bool(r and r["results"] and "**congestion**" in r["results"][0]["snippet"])
    check("Search finds it, with highlighted snippet", hit, str(r)[:150])

    _, r = call(api, "POST", f"/workspaces/{wid}/search", token, {"query": '"database normalization"'})
    check("Exact phrase search", bool(r and r["is_phrase_search"] and r["results"]))

    _, r = call(api, "POST", f"/workspaces/{wid}/search", token, {"query": "zzzznotthere"})
    check("Unknown word returns no results", r is not None and r["results"] == [])

    _, r = call(api, "GET", f"/workspaces/{wid}/search/autocomplete?prefix=conge", token)
    check("Autocomplete", bool(r and "congestion" in r["suggestions"]))

    status, r = call(api, "GET", f"/workspaces/{wid}/documents/{did}/text", token)
    check("Text preview", status == 200 and r and "congestion" in r["text"])

    status, dup = call(api, "POST", f"/workspaces/{wid}/documents", token,
                       files={"file": ("again.txt", text, "text/plain")})
    check("Duplicate upload detected", status in (200, 201) and dup and dup["is_duplicate"])

    status, _ = call(api, "POST", f"/workspaces/{wid}/documents", token,
                     files={"file": ("evil.exe", b"MZ\x90\x00not really text", "application/octet-stream")})
    check("Bad file type rejected", status in (400, 415, 422), f"HTTP {status}")

    other = register_and_login(api, f"smoke-other-{run}@example.com")
    s1, _ = call(api, "GET", f"/workspaces/{wid}/documents", other)
    s2, _ = call(api, "POST", f"/workspaces/{wid}/search", other, {"query": "congestion"})
    check("Another user cannot access this workspace", s1 in (403, 404) and s2 in (403, 404), f"{s1}/{s2}")
    s3, _ = call(api, "GET", f"/workspaces/{wid}/documents")
    check("No token -> 401", s3 == 401, f"HTTP {s3}")

    status, _ = call(api, "DELETE", f"/workspaces/{wid}/documents/{did}", token)
    check("Delete document", status == 204, f"HTTP {status}")
    _, r = call(api, "POST", f"/workspaces/{wid}/search", token, {"query": "congestion"})
    check("Deleted document no longer searchable", r is not None and r["results"] == [])

    call(api, "DELETE", f"/workspaces/{wid}", token)  # cleanup

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("Failed:", "; ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
