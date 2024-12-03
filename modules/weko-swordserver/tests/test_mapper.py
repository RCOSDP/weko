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


    # def _get_json_metadata_value():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__get_json_metadata_value -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__get_json_metadata_value(self, item_type):
        json = json_data("data/item_type/processed_json_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")
        json_values = json_data("data/item_type/json_values_2.json")

        mapper = WekoSwordMapper(json, itemtype, json_map)

        for json_map_key, json_value in json_values.items():
            assert mapper._get_json_metadata_value(json_map_key) == json_value


    # def _get_type_of_item_type_path():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__get_type_of_item_type_path -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__get_type_of_item_type_path(self, item_type):
        json = json_data("data/item_type/processed_json_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        mapper = WekoSwordMapper(json, itemtype, json_map)

        item_map = mapper._create_item_map()

        # case: ["object"", "value"]
        type_of_item_type_path_1 = mapper._get_type_of_item_type_path(item_map.get("Resource Type.資源タイプ（シンプル）"))
        # case: ["array", "value"]
        type_of_item_type_path_2 = mapper._get_type_of_item_type_path(item_map.get("Title.Title"))
        # case: ["object", "object", "value"]
        # TODO: Implement this test case
        # case: ["array", "array", "value"]
        type_of_item_type_path_4 = mapper._get_type_of_item_type_path(item_map.get("Contributor.寄与者名.名"))

        assert type_of_item_type_path_1 == ["object", "value"]
        assert type_of_item_type_path_2 == ["array", "value"]
        assert type_of_item_type_path_4 == ["array", "array", "value"]


    # def _get_dimensions():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__get_dimensions -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__get_dimensions(self, item_type):
        json = None
        itemtype = item_type[1]["item_type"]
        json_map = None

        mapper = WekoSwordMapper(json, itemtype, json_map)

        # case: Not a list
        list_0 = 1
        # case: 1D list
        list_1 = [1, 2, 3]
        # case: 2D list
        list_2 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        # case: 3D list
        list_3 = [[[1, 2, 3], [4, 5, 6], [7, 8, 9]], [[1, 2, 3], [4, 5, 6], [7, 8, 9]], [[1, 2, 3], [4, 5, 6], [7, 8, 9]]]
        # case: Empty list
        list_e = []

        assert mapper._get_dimensions(list_0) == 0
        assert mapper._get_dimensions(list_1) == 1
        assert mapper._get_dimensions(list_2) == 2
        assert mapper._get_dimensions(list_3) == 3
        assert mapper._get_dimensions(list_e) == 1


    # def _create_child_metadata_of_a_property():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__create_child_metadata_of_a_property -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__create_child_metadata_of_a_property(self, item_type):
        json = json_data("data/item_type/processed_json_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        mapper = WekoSwordMapper(json, itemtype, json_map)

        # case:
        return


    # def _create_metadata_of_a_property():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__create_metadata_of_a_property -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__create_metadata_of_a_property(self, item_type):
        json = json_data("data/item_type/processed_json_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        mapper = WekoSwordMapper(json, itemtype, json_map)

        item_map = mapper._create_item_map()

        # case: Property is in dict, path is in dict
        metadata_dict_dict = {}
        item_map_key = item_map.get("Resource Type.資源タイプ（シンプル）")
        json_map_key = json_map.get("Resource Type.資源タイプ（シンプル）")
        type_of_item_type_path = mapper._get_type_of_item_type_path(item_map_key)
        json_value = mapper._get_json_metadata_value(json_map_key)
        mapper._create_metadata_of_a_property(metadata_dict_dict, item_map_key, type_of_item_type_path, json_value)
        expected_dict_dict = {
            "item_1617258105262": {
                "resourcetype": "other"
            }
        }

        # case: Property is in dict, path is in list
        metadata_dict_list = {}
        item_map_key = item_map.get("Title.Title")
        json_map_key = json_map.get("Title.Title")
        type_of_item_type_path = mapper._get_type_of_item_type_path(item_map_key)
        json_value = mapper._get_json_metadata_value(json_map_key)
        mapper._create_metadata_of_a_property(metadata_dict_list, item_map_key, type_of_item_type_path, json_value)
        expected_dict_list = {
            "item_1617186331708": [
                {
                "subitem_1551255647225": "サンプルアイテム"
                }
            ]
        }

        # case: Property is in list, path is in dict
        # TODO: Implement this test case

        # case: Property is in list, path is in list
        metadata_list_list = {}
        item_map_key = item_map.get("Contributor.寄与者名.名")
        json_map_key = json_map.get("Contributor.寄与者名.名")
        type_of_item_type_path = mapper._get_type_of_item_type_path(item_map_key)
        json_value = mapper._get_json_metadata_value(json_map_key)
        mapper._create_metadata_of_a_property(metadata_list_list, item_map_key, type_of_item_type_path, json_value)
        expected_list_list = {
            "item_1617349709064": [
                {
                    "givenNames": [
                        {
                            "givenName": "Stian"
                        }
                    ]
                }
            ]
        }

        # case: Property is not exist
        # TODO: Implement this test case

        assert metadata_dict_dict == expected_dict_dict
        assert metadata_dict_list == expected_dict_list
        assert metadata_list_list == expected_list_list


    # def _create_metadata():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__create_metadata -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__create_metadata(self, item_type):
        json = json_data("data/item_type/processed_json_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        mapper = WekoSwordMapper(json, itemtype, json_map)

        item_map = mapper._create_item_map()
        metadata = {
            "pubdate": "2024-11-15",
            "path": [
                1623632832836
            ]
        }

        metadata.update(mapper._create_metadata(item_map))
        expected = json_data("data/item_type/mapped_json_2.json")
        expected.pop("item_1732599253716")
        assert metadata == expected


    # def map():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test_map -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_map(self, item_type):
        json = json_data("data/item_type/processed_json_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        mapper = WekoSwordMapper(json, itemtype, json_map)
        result = mapper.map()

        expected = json_data("data/item_type/mapped_json_2.json")
        expected.pop("item_1732599253716")
        assert result == expected
