#!/bin/bash
# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
# :license: BSD, see LICENSE for details.

trap "exit" INT

python -m venv venv
. venv/bin/activate
python -m pip install -U 'setuptools==57.5.0' wheel 'pip==20.2.4' coveralls PyYAML
pip install -r packages.txt
pip install --no-deps -r packages-invenio.txt
sed -E 's/\/code\///g' requirements-weko-modules.txt | xargs pip install --no-deps
python -m pip uninstall -y 'coverage' 'pytest' 'pytest-cov' 'pytest-invenio' 'mock' 'urllib3' 'responses' 'moto'
python -m pip install 'coverage==4.5.4' 'pytest==5.4.3' 'pytest-cov==2.10.1' 'pytest-invenio==1.3.4' 'mock==3.0.5' 'urllib3==1.21.1' 'responses==0.10.3' 'moto==1.3.5'

for module_path in modules/*/; do
  if [[ ${module_path} =~ ^modules/(invenio-|weko-).+$ ]] && [[ -d ${module_path}tests ]]; then
    echo "### Running tests for ${module_path%?} ###"
    (cd ${module_path} && python -m pip install . && python setup.py test)
    echo
  fi
done
