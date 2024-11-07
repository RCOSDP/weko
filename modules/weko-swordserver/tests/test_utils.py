# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import pytest

from weko_swordserver.utils import (
    process_json
)
from .helpers import json_data

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace

# def process_json():
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_process_json -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_process_json(app):
    with app.app_context():
        json_ld = json_data("data/item_type/ro-crate-metadata_2.json")
        json = process_json(json_ld)

        assert json == json_data("data/item_type/processed_json_2.json")
