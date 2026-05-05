#!/usr/bin/env bash
# Deploy frontend to Vercel (Production).
# Prereq: npm install (repo root). Set VITE_API_URL in Vercel project settings.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v npx >/dev/null 2>&1; then
  echo "npx not found. Install Node.js 18+." >&2
  exit 1
fi

if [[ -n "${VERCEL_TOKEN:-}" ]]; then
  exec npx vercel deploy --prod --yes --token "$VERCEL_TOKEN"
else
  exec npx vercel deploy --prod --yes
fi
