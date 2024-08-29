#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017-2020 CERN.
# Copyright (C) 2022      TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# Quit on errors
set -o errexit

# Quit on unbound symbols
set -o nounset

# Always bring down docker services
function cleanup() {
    eval "$(docker-services-cli down --env)"
}
trap cleanup EXIT

python -m check_manifest
python -m sphinx.cmd.build -qnNW docs docs/_build/html
eval "$(docker-services-cli up --search ${SEARCH:-opensearch} --mq ${MQ:-rabbitmq} --cache ${CACHE:-redis} --env)"
# Note: expansion of pytest_args looks like below to not cause an unbound
# variable error when 1) "nounset" and 2) the array is empty.
python -m pytest ${pytest_args[@]+"${pytest_args[@]}"}
tests_exit_code=$?
exit "$tests_exit_code"
