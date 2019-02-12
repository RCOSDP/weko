#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# This file is part of Cookiecutter - Invenio Module Template
# Copyright (C) 2017 ETH Zurich, Swiss Data Science Center.
#
# Cookiecutter - Invenio Module Template is free software; you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# Cookiecutter - Invenio Module Template is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cookiecutter - Invenio Module Template; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# 02111-1307, USA.

# quit on errors:
set -o errexit

# quit on unbound symbols:
set -o nounset

WORKDIR=$(mktemp -d)

function finish {
    echo "Cleaning up."
    pip uninstall -y generated_fun
    rm -rf "${WORKDIR}"
}

trap finish EXIT

sphinx-build -qnN docs docs/_build/html
cookiecutter --no-input -o "$WORKDIR" . project_name=Generated-Fun

cd "${WORKDIR}/generated-fun"

git init
git add -A

pip install -e .\[all\] --quiet

mkdir generated_fun/translations
python setup.py extract_messages
python setup.py init_catalog -l en
python setup.py compile_catalog
git add -A

check-manifest -u || true

./run-tests.sh
