# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


from .helpers import json_data

from weko_swordserver.mapper import WekoSwordMapper

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace

# class WekoSwordMapper:
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
class TestWekoSwordMapper:
    # def test__process_json_map():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__create_item_map -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__create_item_map(self, item_type):
        json = None
        itemtype_name = item_type[1]["item_type_name"].name
        json_map = None

        mapper = WekoSwordMapper(json, itemtype_name, json_map)
        mapper.map_itemtype("")

        item_map =  mapper._create_item_map()
        assert item_map == json_data("data/item_type/item_map_2.json")

