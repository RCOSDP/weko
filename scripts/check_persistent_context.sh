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

echo "Checking persistent context updates for range: ${base_ref}..${head_ref}"

changed_entries="$(git diff --name-status --diff-filter=ACMR "${base_ref}" "${head_ref}")"

if [ -z "${changed_entries}" ]; then
  echo "No changed files detected."
  exit 0
fi

echo "Changed files:"
printf '%s\n' "${changed_entries}"

needs_progress=0
needs_findings=0
progress_updated=0
findings_updated=0
task_plan_updated=0

is_context_file() {
  case "$1" in
    task_plan.md|findings.md|progress.md)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

is_workflow_or_docs_only_file() {
  case "$1" in
    AGENTS.md|CLAUDE.md|GEMINI.md|CONTRIBUTING.rst|README.rst|README-TEST.md|.github/pull_request_template.md|.github/copilot-instructions.md)
      return 0
      ;;
    *.md|*.rst|docs/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

is_cross_cutting_or_code_file() {
  case "$1" in
    modules/*|invenio/*|scripts/*|tools/*|ui-tests/*|test/*|plugins/*|docker-compose*.yml|docker-compose*.yaml|install.sh|run-tests.sh|requirements*.txt|packages*.txt|tox.ini|scripts/tox.ini|postgresql/*|elasticsearch/*|nginx/*|handle/*|tika/*|kibana/*)
      return 0
      ;;
    *.py|*.js|*.jsx|*.ts|*.tsx|*.json|*.yml|*.yaml|*.ini|*.cfg|*.sh|*.sql)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

while IFS=$'\t' read -r status file _; do
  [ -z "${file}" ] && continue

  if is_context_file "${file}"; then
    case "${file}" in
      progress.md)
        progress_updated=1
        ;;
      findings.md)
        findings_updated=1
        ;;
      task_plan.md)
        task_plan_updated=1
        ;;
    esac
    continue
  fi

  if is_workflow_or_docs_only_file "${file}"; then
    continue
  fi

  needs_progress=1

  if is_cross_cutting_or_code_file "${file}"; then
    needs_findings=1
  fi
done <<EOF
${changed_entries}
EOF

if [ "${needs_progress}" -eq 0 ] && [ "${needs_findings}" -eq 0 ]; then
  echo "Only documentation or workflow guidance changed. Persistent context update not required."
  exit 0
fi

if [ "${needs_progress}" -eq 1 ] && [ "${progress_updated}" -ne 1 ]; then
  echo "Changes that affect code, configuration, or execution were detected, but progress.md was not updated." >&2
  echo "Record actions taken, tests run, and failures in progress.md." >&2
  exit 1
fi

if [ "${needs_findings}" -eq 1 ] && [ "${findings_updated}" -ne 1 ] && [ "${task_plan_updated}" -ne 1 ]; then
  echo "Cross-cutting or code changes were detected, but neither findings.md nor task_plan.md was updated." >&2
  echo "Add reusable discoveries to findings.md, or update task_plan.md for multi-step work." >&2
  exit 1
fi

echo "Persistent context requirements satisfied."
echo "Summary:"
echo "  progress.md updated: ${progress_updated}"
echo "  findings.md updated: ${findings_updated}"
echo "  task_plan.md updated: ${task_plan_updated}"
echo "  progress required: ${needs_progress}"
echo "  findings/task_plan required: ${needs_findings}"
  exit 0
