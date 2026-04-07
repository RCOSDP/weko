#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <base-ref> <head-ref>" >&2
  exit 2
fi

base_ref="$1"
head_ref="$2"
empty_tree="4b825dc642cb6eb9a060e54bf8d69288fbee4904"

normalize_ref() {
  local ref="$1"

  if [ -z "${ref}" ] || [ "${ref}" = "0000000000000000000000000000000000000000" ]; then
    printf '%s\n' "${empty_tree}"
    return
  fi

  if git rev-parse --verify "${ref}^{commit}" >/dev/null 2>&1; then
    printf '%s\n' "${ref}"
    return
  fi

  printf '%s\n' "${empty_tree}"
}

base_ref="$(normalize_ref "${base_ref}")"
head_ref="$(normalize_ref "${head_ref}")"

echo "Checking for newly added legacy SQL files in range: ${base_ref}..${head_ref}"

new_legacy_sql="$(
  git diff --name-status --diff-filter=A "${base_ref}" "${head_ref}" \
    | awk '$1 == "A" {print $2}' \
    | rg '^postgresql/(ddl|update)/.*\.sql$' || true
)"

if [ -z "${new_legacy_sql}" ]; then
  echo "No new legacy SQL files detected."
  exit 0
fi

echo "New legacy SQL files are not allowed:" >&2
printf '%s\n' "${new_legacy_sql}" >&2
echo "Add schema changes via module Alembic migrations instead of creating new files under postgresql/ddl or postgresql/update." >&2
exit 1
