# Ember — Security (Phase 8)

Audit of the whole system against the Phase 8 checklist: what was found, what changed, and what is a
deliberate trade-off. Tests live in `backend/tests/test_security_hardening.py` (33) plus the existing
auth / authorization / upload suites.

## Findings fixed in this phase

| # | Finding | Severity | Fix |
|---|---------|----------|-----|
| 1 | Rate limiter and security-headers middleware existed but were **never wired in** — no brute-force protection, no body-size guard | High | Middleware registered; limits on register, login (per account + per IP), refresh, upload, search |
| 2 | Login timing leaked which emails exist (unknown email skipped bcrypt) | Medium | Dummy bcrypt check on the unknown-email path |
| 3 | Passwords > 72 bytes made bcrypt raise → HTTP 500 (and bcrypt silently ignores bytes past 72) | Medium | Reject at registration (422), treat as non-matching at login |
| 4 | Email was case-sensitive (`A@x.com` ≠ `a@x.com`): duplicate accounts, confusing login failures | Low | Normalised to lower case; lookups are case-insensitive so existing rows still work |
| 5 | Token with a non-UUID `sub` → 500 instead of 401 | Low | `sub` validated in `decode_token` |
| 6 | JWTs accepted without `exp`/`iat`/`jti` | Medium | Required claims enforced; `alg=none` test added |
| 7 | Logout revoked only the access token; a stolen refresh token kept working for 7 days | High | Logout also revokes the refresh token (web + mobile now send it) |
| 8 | Weak passwords (`aaaaaaaa`, blanks) accepted | Low | Blank / ≤3 distinct characters rejected |
| 9 | Upload read the whole body before the size check; no limit without `Content-Length` | Medium | Read capped at limit+1 byte |
| 10 | DOCX zip bombs (tiny file → GBs on extraction) and traversal entries | High | Entry count, inflated size, ratio and path checks before extraction |
| 11 | Client filename stored/echoed unsanitised (control chars, bidi override, directories) | Low | `sanitize_filename`; storage keys were already UUID-based |
| 12 | `/docs` and `/openapi.json` public in production | Low | Off in production unless `ENABLE_DOCS=true` |
| 13 | Web app sent no security headers | Low | nosniff, frame-deny, referrer, permissions, HSTS, base CSP via `next.config.ts` |

## Checklist status

**Authentication** — bcrypt with per-hash salt; HS256 JWT, 30 min access / 7 day refresh; refresh rotation with Redis
denylist keyed by `jti`; logout revokes both tokens; identical error for unknown email vs wrong password.

**Authorization** — every workspace/folder/document route goes through `get_owned_*`, which returns the same 404 for
"missing" and "someone else's" (no existence leak) and checks the URL's workspace matches the object's.
Covered by `test_authorization.py`. The search index is per workspace, so results cannot cross users.

**Uploads** — extension allow-list (pdf, txt, md, docx), 25 MB cap, magic bytes, DOCX structure + bomb checks,
UTF-8/NUL checks for text, UUID storage keys, local-storage path-traversal guard, 25 MB+overhead body guard.

**API** — Pydantic validation everywhere, explicit CORS origin list (never `*`), HSTS in production, rate limits:

| Bucket | Limit |
|---|---|
| register | 10 / hour / IP |
| login | 8 / 5 min per (IP, email) and 40 / 5 min per IP |
| refresh | 60 / min / IP |
| upload | 60 / min / IP |
| search | 240 / min / IP |

Limits fail **open** if Redis is down (availability over lockout). Behind a proxy set `TRUST_PROXY_HEADERS=true`
or every user shares the proxy's IP and the per-IP buckets trip for everyone; never set it without a proxy.

**Secrets** — `.env` is git-ignored; history scanned: only placeholders. Run `python scripts/scan_secrets.py`
(CI will run it in Phase 10). Production boot fails if `JWT_SECRET` is short or placeholder-like, or CORS lists localhost.
Rotate any token ever pasted into a chat or ticket. Use Secret Manager on GCP in Phase 9.

## Accepted trade-offs / known gaps

- **Web tokens live in `localStorage`** — readable by any script on the page, so an XSS bug would leak them. We ship
  no third-party scripts and React escapes output, but the stronger design is an httpOnly refresh cookie; revisit with
  a cookie-based session if the web app ever hosts untrusted content. Mobile uses Keychain/Keystore (`expo-secure-store`).
- **No account lockout / email verification / password reset** — rate limiting only. Registration can be closed with
  `ALLOW_REGISTRATION=false`.
- **Access tokens can't be revoked server-side except by logout** (30 min lifetime bounds it).
- **No antivirus scan** of uploads; files are never executed and are served only to their owner.
- **No nonce-based script CSP yet** (needs middleware for the inline theme bootstrap).
- Existing mixed-case emails keep working; two legacy rows differing only by case would both match — not expected in practice.
