#!/bin/bash
# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
# :license: BSD, see LICENSE for details.

trap "exit" INT

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${WEKO_TEST_VENV_DIR:-/tmp/weko-test-venv}"
PYTEST_TMP_ROOT="${WEKO_TEST_TMPDIR:-/tmp/weko-pytest}"
TEST_MODULES="${WEKO_TEST_MODULES:-}"
VENV_CACHE_KEY_FILE="${VENV_DIR}/.weko-test-cache-key"
VENV_CACHE_INPUTS=(
  "packages.txt"
  "packages-invenio.txt"
  "requirements-weko-modules.txt"
)
TEST_TOOL_PINS=(
  "coverage==4.5.4"
  "pytest==5.4.3"
  "pytest-cov==2.10.1"
  "pytest-invenio==1.3.4"
  "pytest-mock==3.2.0"
  "mock==3.0.5"
  "urllib3==1.21.1"
  "responses==0.10.3"
  "moto==1.3.5"
  "tox==3.28.0"
  "tox-setuptools-version==0.0.0.3"
  "pytest-timeout==1.4.2"
)

should_run_module() {
  local module_name="$1"
  local selected_module

  if [[ -z "${TEST_MODULES}" ]]; then
    return 0
  fi

  for selected_module in ${TEST_MODULES}; do
    case "${selected_module}" in
      "${module_name}"|"modules/${module_name}"|"modules/${module_name}/")
        return 0
        ;;
    esac
  done

  return 1
}

venv_cache_key() {
  (
    printf '%s\n' 'setuptools==57.5.0' 'wheel' 'pip==20.2.4' 'coveralls' 'PyYAML'
    printf '%s\n' "${TEST_TOOL_PINS[@]}"
    sha256sum "${VENV_CACHE_INPUTS[@]}"
  ) | sha256sum | cut -d' ' -f1
}

cd "${ROOT_DIR}"
mkdir -p "${PYTEST_TMP_ROOT}"
current_cache_key="$(venv_cache_key)"

if [[ ! -x "${VENV_DIR}/bin/python" ]] || [[ ! -f "${VENV_CACHE_KEY_FILE}" ]] || [[ "$(cat "${VENV_CACHE_KEY_FILE}")" != "${current_cache_key}" ]]; then
  rm -rf "${VENV_DIR}"
  python -m venv "$VENV_DIR"
  . "$VENV_DIR/bin/activate"
  python -m pip install -U 'setuptools==57.5.0' wheel 'pip==20.2.4' coveralls PyYAML
  pip install -r packages.txt
  pip install --no-deps -r packages-invenio.txt
  sed -E 's/\/code\///g' requirements-weko-modules.txt | xargs pip install --no-deps
  python -m pip uninstall -y 'coverage' 'pytest' 'pytest-cov' 'pytest-invenio' 'pytest-mock' 'mock' 'urllib3' 'responses' 'moto' 'tox' 'tox-setuptools-version' 'pytest-timeout'
  python -m pip install "${TEST_TOOL_PINS[@]}"
  printf '%s\n' "${current_cache_key}" > "${VENV_CACHE_KEY_FILE}"
else
  . "$VENV_DIR/bin/activate"
  echo "Reusing cached test virtualenv: ${VENV_DIR}"
fi

total_modules=0
passed_modules=0
failed_modules=0
failed_module_names=()

for module_path in modules/*/; do
  if [[ ${module_path} =~ ^modules/(invenio-|weko-).+$ ]] && [[ -d ${module_path}tests ]]; then
    module_name="${module_path#modules/}"
    module_name="${module_name%/}"
    if ! should_run_module "${module_name}"; then
      continue
    fi
    module_tmp_dir="${PYTEST_TMP_ROOT}/${module_name}"
    echo "### Running tests for ${module_path%?} ###"
    mkdir -p "${module_tmp_dir}"
    total_modules=$((total_modules + 1))
    if (
      cd "${module_path}" && \
      python -m pip install . && \
      pytest tests \
        --basetemp="${module_tmp_dir}/basetemp" \
        -o cache_dir="${module_tmp_dir}/cache"
    ); then
      passed_modules=$((passed_modules + 1))
    else
      failed_modules=$((failed_modules + 1))
      failed_module_names+=("${module_name}")
    fi
    echo
  fi
done

echo "### Test summary ###"
echo "Selected modules: ${total_modules}"
echo "Passed modules: ${passed_modules}"
echo "Failed modules: ${failed_modules}"

if [[ ${total_modules} -eq 0 ]]; then
  echo "No modules matched WEKO_TEST_MODULES='${TEST_MODULES}'."
  exit 1
fi

if [[ ${failed_modules} -ne 0 ]]; then
  echo "Failed module list: ${failed_module_names[*]}"
  exit 1
fi
