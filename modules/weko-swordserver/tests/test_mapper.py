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
    # def __init__(self, json, itemtype, json_map):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__init -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__init(self, item_type):
        json = json_data("data/item_type/processed_json_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        mapper = WekoSwordMapper(json, itemtype, json_map)

        assert mapper.json == json
        assert mapper.itemtype == itemtype
        assert mapper.itemtype_name == item_type[1]["item_type_name"].name
        assert mapper.json_map == json_map


    # def __create_item_map():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__create_item_map -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__create_item_map(self, item_type):
        json = None
        itemtype = item_type[1]["item_type"]
        json_map = None

        mapper = WekoSwordMapper(json, itemtype, json_map)

        item_map =  mapper._create_item_map()
        assert item_map == json_data("data/item_type/item_map_2.json")


    # def map():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test_map -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_map(self, item_type):
        json = json_data("data/item_type/processed_json_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        mapper = WekoSwordMapper(json, itemtype, json_map)
        result = mapper.map()

        assert result == json_data("data/item_type/mapped_json_2.json")
