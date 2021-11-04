#!/bin/bash
# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

trap "exit" INT

pip install -U pytest && pip install coverage==4.5.4 pytest==5.4.3 pytest-cov==2.10.1 pytest-invenio==1.3.4 mock==3.0.5 urllib3==1.21.1 responses==0.10.3 moto==1.3.5


for module_path in modules/*/; do
  if [[ ${module_path} =~ ^modules/(invenio-|weko-).+$ ]] && [[ -d ${module_path}tests ]]; then
    echo "### Running tests for ${module_path%?} ###"
    (cd ${module_path} && python -m pip install . && python setup.py test)
    echo
  fi
done
