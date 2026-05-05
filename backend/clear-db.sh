#!/usr/bin/env bash
# Wipe local SQLite DB, uploaded meeting files, chunk staging, and Chroma persistence.
# Run from anywhere:  bash clear-db.sh   (or ./clear-db.sh after chmod +x)
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BACKEND_DIR"

echo "Removing SQLite database..."
rm -f db.sqlite3

echo "Resetting Chroma directory..."
rm -rf chroma_db
mkdir -p chroma_db

echo "Clearing media/meetings and media/chunks..."
mkdir -p media/meetings media/chunks
find media/meetings -mindepth 1 -delete 2>/dev/null || true
find media/chunks -mindepth 1 -delete 2>/dev/null || true

if [[ -x .venv/bin/python ]]; then
  PY=.venv/bin/python
elif [[ -x venv/bin/python ]]; then
  PY=venv/bin/python
else
  PY=python3
fi

echo "Running migrations with: $PY"
"$PY" manage.py migrate --noinput

echo "Done. Database and local uploads are empty."
