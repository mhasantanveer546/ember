#!/usr/bin/env python3
"""Fail if tracked files contain things that look like real credentials.
Usage: python scripts/scan_secrets.py   (run from the repo root; also used by CI in Phase 10)"""
import re
import subprocess
import sys

PATTERNS = {
    "GitHub token": r"(github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{30,})",
    "AWS access key": r"AKIA[0-9A-Z]{16}",
    "Google API key": r"AIza[0-9A-Za-z_\-]{30,}",
    "Private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "DB URL with password": r"postgres(?:ql)?(?:\+\w+)?://[^:@/\s]+:(?!password|p@|\*|\$|<)[^@\s]{6,}@(?!host\b|h/)[\w.-]+",
}
files = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
bad = []
for f in files:
    if f.endswith((".lock", ".png", ".jpg", ".ico", ".patch", "package-lock.json")):
        continue
    try:
        text = open(f, encoding="utf-8").read()
    except (UnicodeDecodeError, FileNotFoundError):
        continue
    for name, pat in PATTERNS.items():
        if re.search(pat, text):
            bad.append(f"{f}: looks like a {name}")
tracked_env = [f for f in files if re.search(r"(^|/)\.env($|\.local)|\.pem$", f)]
bad += [f"{f}: env/key file must not be tracked" for f in tracked_env]
print("\n".join(bad) or "No secrets found.")
sys.exit(1 if bad else 0)
