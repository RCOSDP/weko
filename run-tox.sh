#!/bin/bash
# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
# :license: BSD, see LICENSE for details.

date --iso-8601="minutes"
pip install tox
pip install tox-setuptools-version
for module_path in modules/*/; do
  if [[ ${module_path} =~ ^modules/(invenio-|weko-).+$ ]] && [[ -d ${module_path}tests ]]; then
    echo "### Running tests for ${module_path%?} ###"
    (cd ${module_path} && tox > tox.result; rm -rf .tox)
    echo
  fi
done
date --iso-8601="minutes"
