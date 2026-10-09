#!/usr/bin/env bash
# Usage: deploy/huggingface/publish.sh <hf-username>/<space-name>
# Needs: a Docker Space already created on huggingface.co, and `git` logged in
# (use a HF access token with write scope as the password when prompted).
set -euo pipefail
SPACE="${1:?usage: publish.sh <hf-username>/<space-name>}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
git clone "https://huggingface.co/spaces/${SPACE}" "$TMP/space"
cd "$TMP/space"
rm -rf backend search_engine
cp -r "$ROOT/backend" "$ROOT/search_engine" .
rm -rf backend/.venv backend/storage_data backend/__pycache__ backend/.pytest_cache
cp "$ROOT/deploy/huggingface/Dockerfile" "$ROOT/deploy/huggingface/README.md" .
git add -A
git commit -m "Deploy Ember API" || true
git push
echo "Pushed. Watch the build in the Space's Logs tab."
