#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
trap 'rc=$?; echo "Error: ${BASH_COMMAND} (line ${LINENO}) exited with ${rc}" >&2; exit ${rc}' ERR

SETTING_FILE="$1"
ENABLE_FLAG="$2"

declare -A expected=(
  [WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG]=$ENABLE_FLAG
  [WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS]=$ENABLE_FLAG
  [WEKO_RECORDS_UI_RESTRICTED_API]=$ENABLE_FLAG
  [WEKO_ITEMS_UI_PROXY_POSTING]=$ENABLE_FLAG
  [WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED]=$ENABLE_FLAG
  [WEKO_INDEX_TREE_SHOW_MODAL]=$ENABLE_FLAG
  [WEKO_USERPROFILES_CUSTOMIZE_ENABLED]=$ENABLE_FLAG
  [INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED]=$ENABLE_FLAG
)

fail=0

if [ ! -f "$SETTING_FILE" ]; then
  echo "Error: ${SETTING_FILE} not found" >&2
  exit 2
fi

echo "Checking ${SETTING_FILE}"
for key in "${!expected[@]}"; do
  val=${expected[$key]}
  if grep -Eiq "^${key} *= *${val}$" "$SETTING_FILE"; then
    echo "OK: ${key} = ${val} in ${SETTING_FILE}"
  else
    echo "FAIL: ${key} != ${val} in ${SETTING_FILE}" >&2
    fail=1
  fi
done

if [ "${fail}" -ne 0 ]; then
  echo "Verification failed" >&2
  exit 1
fi

echo "All checks passed"
exit 0
