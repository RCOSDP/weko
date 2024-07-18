#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Files-REST is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# Usage:
#   ./run-i18n-tests.sh

python -m setup extract_messages --output-file /dev/null
