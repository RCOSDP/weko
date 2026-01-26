#!/usr/bin/env bash
set -euo pipefail

VENV_PATH="${VENV_PATH:-/home/invenio/.virtualenvs/invenio}"

if [ ! -d "$VENV_PATH" ]; then
  echo "[ERROR] VENV_PATH not found: $VENV_PATH" >&2
  exit 1
fi

echo "[INFO] Scanning shared object dependencies under: $VENV_PATH" >&2

find "$VENV_PATH" -type f \( -name "*.so" -o -name "uwsgi" \) -print0 \
  | xargs -0 ldd 2>/dev/null \
  | awk '/=>/ {print $1}' \
  | sort -u
