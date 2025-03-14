# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
import pytest
from .helpers import json_data
from weko_swordserver.errors import ErrorType, WekoSwordserverException
from weko_swordserver.mapper import WekoSwordMapper
from unittest.mock import patch

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace

# class WekoSwordMapper:
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
class TestWekoSwordMapper:
    # def __init__(self, json, itemtype, json_map):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__init -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__init(self, item_type):
        json = json_data("data/item_type/processed_json_2.json")
        json_ld = json_data("data/item_type/ro-crate-metadata_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)

        assert mapper.json == json
        assert mapper.itemtype == itemtype
        assert mapper.itemtype_name == item_type[1]["item_type_name"].name
        assert mapper.json_map == json_map
        # assert mapper.json_ld == json_ld

    # def map():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test_map -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_map(self, item_type):

        # with valid data
        json = json_data("data/item_type/processed_json_2.json")
        json_ld = json_data("data/item_type/ro-crate-metadata_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        result = mapper.map()

        expected = json_data("data/item_type/mapped_json_2.json")
        # expected.pop("item_1732599253716")
        assert result == expected

        # with deleted record
        json = {
                    "record": {
                        "header": {
                            "identifier": "example",
                            "datestamp": "2024-12-27",
                            "@status": "deleted"
                        },
                        "metadata": {}
                    }
                }
        json_ld = json_data("data/item_type/ro-crate-metadata_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        result = mapper.map()

        assert result == {}

    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__create_metadata -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__create_metadata(self, item_type):
        json = json_data("data/item_type/processed_json_2.json")
        json_ld = json_data("data/item_type/ro-crate-metadata_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)

        # case: valid metadata creation; contains Extra metadata
        item_map =  mapper._create_item_map()
        metadata = mapper._create_metadata(item_map)

        assert metadata["item_1617604990215"][0]["filesize"][0]["value"] == "333"
        assert metadata["item_1617186331708"][0]["subitem_1551255647225"] == "サンプルアイテム"
        assert metadata["item_1617258105262"]["resourcetype"] == "other"
        assert "'author.@id': 'http://orcid.org/0000-0002-1825-0097'" in metadata["item_1732599253716"]

        # case: valid metadata creation; not contains Extra metadata
        item_map =  mapper._create_item_map()
        item_map.pop("Extra")
        metadata = mapper._create_metadata(item_map)

        assert metadata["item_1617604990215"][0]["filesize"][0]["value"] == "333"
        assert metadata["item_1617186331708"][0]["subitem_1551255647225"] == "サンプルアイテム"
        assert metadata["item_1617258105262"]["resourcetype"] == "other"

    # def _get_json_metadata_value():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__get_json_metadata_value -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__get_json_metadata_value(self, item_type):
        # json = json_data("data/item_type/processed_json_2.json")
        json_ld = json_data("data/item_type/ro-crate-metadata_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        # key dose not exist
        json = {
                "record": {
                    "header": {
                        "identifier": "The Sample",
                        "datestamp": "2024-11-15",
                        "indextree": 1623632832836,
                        "publish_status": "public"
                    },
                    "metadata": {
                        "d2Vrby0uLw==": {
                            "contentSize": "333"
                        }
                    }
                }
            }
        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        assert mapper._get_json_metadata_value("d2Vrby0uLw1==.hasPart.contentSize") == None

        # dict in dict: {"json_key": {}} one KEYs
        json = {
                "record": {
                    "header": {
                        "identifier": "The Sample",
                        "datestamp": "2024-11-15",
                        "indextree": 1623632832836,
                        "publish_status": "public"
                    },
                    "metadata": {
                        "d2Vrby0uLw==": {
                            "hasPart": "333"
                        }
                    }
                }
            }
        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        with pytest.raises(WekoSwordserverException) as excinfo:
            mapper._get_json_metadata_value("d2Vrby0uLw==")
        assert str(excinfo.value.message) == "Value is dict but still need to get more keys. Check the mapping definition."
        assert excinfo.value.errorType == ErrorType.ServerError

        # one KEYs
        json = {
                "record": {
                    "header": {
                        "identifier": "The Sample",
                        "datestamp": "2024-11-15",
                        "indextree": 1623632832836,
                        "publish_status": "public"
                    },
                    "metadata": {
                        "d2Vrby0uLw==": "333"
                    }
                }
            }
        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        assert mapper._get_json_metadata_value("d2Vrby0uLw==") == "333"

        # Two or more KEYs,but value key is not exist in the mapping
        json = {
                "record": {
                    "header": {
                        "identifier": "The Sample",
                        "datestamp": "2024-11-15",
                        "indextree": 1623632832836,
                        "publish_status": "public"
                    },
                    "metadata": {
                        "d2Vrby0uLw==": "333"
                    }
                }
            }
        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        with pytest.raises(WekoSwordserverException) as excinfo:
            mapper._get_json_metadata_value("d2Vrby0uLw==.hasPart.contentSize")
        assert str(excinfo.value.message) == "Value: 333 got from d2Vrby0uLw== but still need to get ['hasPart', 'contentSize']. Check the mapping definition."
        assert excinfo.value.errorType == ErrorType.ServerError

        # value in dict
        json = {
                "record": {
                    "header": {
                        "identifier": "The Sample",
                        "datestamp": "2024-11-15",
                        "indextree": 1623632832836,
                        "publish_status": "public"
                    },
                    "metadata": {
                        "d2Vrby0uLw==": {
                            "hasPart": None
                        }
                    }
                }
            }
        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        assert mapper._get_json_metadata_value("d2Vrby0uLw==.hasPart.contentSize") == None

        # value in dict  not one key
        json = {
                "record": {
                    "header": {
                        "identifier": "The Sample",
                        "datestamp": "2024-11-15",
                        "indextree": 1623632832836,
                        "publish_status": "public"
                    },
                    "metadata": {
                        "d2Vrby0uLw==": {
                            "hasPart":
                                {
                                    "contentSize": "333"
                                }
                        }
                    }
                }
            }
        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        assert mapper._get_json_metadata_value("d2Vrby0uLw==.hasPart.contentSize") == "333"

        # value in dict  one key
        json = {
                "record": {
                    "header": {
                        "identifier": "The Sample",
                        "datestamp": "2024-11-15",
                        "indextree": 1623632832836,
                        "publish_status": "public"
                    },
                    "metadata": {
                        "d2Vrby0uLw==": {
                            "hasPart": {
                                "contentSize": "333"
                            }
                        }
                    }
                }
            }
        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        assert mapper._get_json_metadata_value("d2Vrby0uLw==.hasPart") == {'contentSize': '333'}

        # value in dict  next is list  not one key
        json = {
                "record": {
                    "header": {
                        "identifier": "The Sample",
                        "datestamp": "2024-11-15",
                        "indextree": 1623632832836,
                        "publish_status": "public"
                    },
                    "metadata": {
                        "d2Vrby0uLw==": {
                            "hasPart": [
                                {
                                    "contentSize": "333"
                                },
                                {
                                    "contentSize1": "444"
                                }
                            ]
                        }
                    }
                }
            }
        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        assert mapper._get_json_metadata_value("d2Vrby0uLw==.hasPart.contentSize1") == [None,"444"]

        # value in dict  next is list  one key
        json = {
                "record": {
                    "header": {
                        "identifier": "The Sample",
                        "datestamp": "2024-11-15",
                        "indextree": 1623632832836,
                        "publish_status": "public"
                    },
                    "metadata": {
                        "d2Vrby0uLw==": {
                            "hasPart": [ "333","444"]
                        }
                    }
                }
            }
        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        assert mapper._get_json_metadata_value("d2Vrby0uLw==.hasPart") == ["333","444"]

        # value in dict  next is list  one key
        json = {
                "record": {
                    "header": {
                        "identifier": "The Sample",
                        "datestamp": "2024-11-15",
                        "indextree": 1623632832836,
                        "publish_status": "public"
                    },
                    "metadata": {
                        "d2Vrby0uLw==": {
                            "hasPart": "333"
                        }
                    }
                }
            }
        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        with pytest.raises(WekoSwordserverException) as excinfo:
            mapper._get_json_metadata_value("d2Vrby0uLw==.hasPart.contentSize")
        assert str(excinfo.value.message) == "Value: 333 got from hasPart but still need to get ['contentSize']. Check the mapping definition."
        assert excinfo.value.errorType == ErrorType.ServerError

        # value in list
        json = {
            "record": {
                "header": {
                    "identifier": "The Sample",
                    "datestamp": "2024-11-15",
                    "indextree": 1623632832836,
                    "publish_status": "public"
                },
                "metadata": {
                    "d2Vrby0uLw==": [
                        {
                            "hasPart": {
                                "contentSize": "333"
                            }
                        },
                        {
                            "hasPart": {
                                "contentSize": "444"
                            }
                        }
                    ]
                }
            }
        }
        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        assert mapper._get_json_metadata_value("d2Vrby0uLw==.hasPart.contentSize") == ["333", "444"]

        # value in list
        json = {
            "record": {
                "header": {
                    "identifier": "The Sample",
                    "datestamp": "2024-11-15",
                    "indextree": 1623632832836,
                    "publish_status": "public"
                },
                "metadata": {
                    "d2Vrby0uLw==": [
                        [
                            {
                                "hasPart": {
                                    "contentSize": "333"
                                }
                            }
                        ],
                        [
                            {
                                "hasPart": {
                                    "contentSize": "444"
                                }
                            }
                        ]
                    ]
                }
            }
        }
        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        with pytest.raises(WekoSwordserverException) as excinfo:
            mapper._get_json_metadata_value("d2Vrby0uLw==.hasPart.contentSize")
        assert str(excinfo.value.message) =="List in list not supported. Check your metadata file."
        assert excinfo.value.errorType == ErrorType.ContentMalformed

        # value in list
        json = {
            "record": {
                "header": {
                    "identifier": "The Sample",
                    "datestamp": "2024-11-15",
                    "indextree": 1623632832836,
                    "publish_status": "public"
                },
                "metadata": {
                    "d2Vrby0uLw==": [ "333" , "444"]
                }
            }
        }
        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        with pytest.raises(WekoSwordserverException) as excinfo:
            mapper._get_json_metadata_value("d2Vrby0uLw==")
        assert "Value: 333 got from list but still need to get []. Check the mapping definition." in str(excinfo.value.message)
        assert excinfo.value.errorType == ErrorType.ServerError





        # # no value in list  Todo:
        # json = {
        #     "record": {
        #         "header": {
        #             "identifier": "The Sample",
        #             "datestamp": "2024-11-15",
        #             "indextree": 1623632832836,
        #             "publish_status": "public"
        #         },
        #         "metadata": {
        #             "d2Vrby0uLw==": []
        #         }
        #     }
        # }
        # mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        # assert mapper._get_json_metadata_value("d2Vrby0uLw==") == []

        # # value is None in dict
        # json = {
        #         "record": {
        #             "header": {
        #                 "identifier": "The Sample",
        #                 "datestamp": "2024-11-15",
        #                 "indextree": 1623632832836,
        #                 "publish_status": "public"
        #             },
        #             "metadata": {
        #                 "d2Vrby0uLw==": {
        #                 }
        #             }
        #         }
        #     }
        # mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)
        # assert mapper._get_json_metadata_value("d2Vrby0uLw==.hasPart.contentSize") == None

    # def _get_type_of_item_type_path():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__get_type_of_item_type_path -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__get_type_of_item_type_path(self, item_type):
        json = json_data("data/item_type/processed_json_2.json")
        json_ld = json_data("data/item_type/ro-crate-metadata_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)

        item_map = mapper._create_item_map()

        # case: ["object", "value"]
        type_of_item_type_path_1 = mapper._get_type_of_item_type_path(item_map.get("Resource Type.資源タイプ（シンプル）"))
        assert type_of_item_type_path_1 == ["object", "value"]

        # case: ["array", "value"]
        type_of_item_type_path_2 = mapper._get_type_of_item_type_path(item_map.get("Title.Title"))
        assert type_of_item_type_path_2 == ["array", "value"]

        # case: ["object", "object", "value"]
        type_of_item_type_path_3 = mapper._get_type_of_item_type_path(item_map.get("Bibliographic Information.発行日.日付"))
        assert type_of_item_type_path_3 == ["object", "object", "value"]

        # case: ["array", "array", "value"]
        type_of_item_type_path_4 = mapper._get_type_of_item_type_path(item_map.get("Contributor.寄与者名.名"))
        assert type_of_item_type_path_4 == ["array", "array", "value"]

        # case: invalid mapping, last element not value
        with pytest.raises(WekoSwordserverException) as excinfo:
            mapper._get_type_of_item_type_path("item_1617349709064.givenNames")
        assert str(excinfo.value.message) == "Some error occurred in the server. Can not create metadata."
        assert excinfo.value.errorType == ErrorType.ServerError

    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__create_child_metadata_of_a_property -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__create_child_metadata_of_a_property(self, item_type):
        json = json_data("data/item_type/processed_json_2.json")
        json_ld = json_data("data/item_type/ro-crate-metadata_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)

        # case: value in dict
        # If item_map_keys length is 1, it means that the item_map_keys contains only last key
        # Only if json_value is not None, add json_value to metadata
        child_metadata = {}
        item_map_keys = ["item_1617258105262"]
        type_of_item_type_path = ["value"]
        json_value = "other"
        mapper._create_child_metadata_of_a_property(child_metadata, item_map_keys, type_of_item_type_path, json_value)
        assert child_metadata == {"item_1617258105262": "other"}

        # case: value in dict
        # If item_map_keys length is 1, it means that the item_map_keys contains only last key
        # json_value is None
        child_metadata = {}
        item_map_keys = ["item_1617258105262"]
        type_of_item_type_path = ["value"]
        json_value = None
        mapper._create_child_metadata_of_a_property(child_metadata, item_map_keys, type_of_item_type_path, json_value)
        assert child_metadata == {}

        # case: nested object
        # If _type is "value", add json_value to metadata
        # json_value is not None
        child_metadata = {}
        item_map_keys = ["item_1617186331708"]
        type_of_item_type_path = ["value"]
        json_value = "サンプルアイテム"
        mapper._create_child_metadata_of_a_property(child_metadata, item_map_keys, type_of_item_type_path, json_value)
        assert child_metadata == {'item_1617186331708': 'サンプルアイテム'}

        # case: nested object
        # if not child_metadata.get(_item_map_key):
        child_metadata = {}
        item_map_keys = ["item_1617186476635", "subitem_1600958577026"]
        type_of_item_type_path = ["object", "value"]
        json_value = "サンプルアイテム"
        mapper._create_child_metadata_of_a_property(child_metadata, item_map_keys, type_of_item_type_path, json_value)
        assert child_metadata == {"item_1617186476635": {"subitem_1600958577026": "サンプルアイテム"}}

        # case: nested object
        # if child_metadata.get(_item_map_key):
        child_metadata = {"item_1617186476635" : {"subitem_1600958577026": "XXXXXXXXXXXXXXXXX"}}
        item_map_keys = ["item_1617186476635", "subitem_1600958577026"]
        type_of_item_type_path = ["object", "value"]
        json_value = "サンプルアイテム"
        mapper._create_child_metadata_of_a_property(child_metadata, item_map_keys, type_of_item_type_path, json_value)
        assert child_metadata == {"item_1617186476635": {"subitem_1600958577026": "サンプルアイテム"}}

        # case: nested array
        child_metadata = {}
        item_map_keys = ["item_1617349709064", "givenNames","givenName"]
        type_of_item_type_path = ["array", "array", "value"]
        json_value = ["Stian"]
        mapper._create_child_metadata_of_a_property(child_metadata, item_map_keys, type_of_item_type_path, json_value)
        assert child_metadata == {'item_1617349709064': [{'givenNames': [{'givenName': 'Stian'}]}]}

        # case: nested object in array
        child_metadata = {}
        item_map_keys = ["item_1617349709064", "givenNames", "givenName"]
        type_of_item_type_path = ["array", "object", "value"]
        json_value = [{"givenName": "Stian"}]
        mapper._create_child_metadata_of_a_property(child_metadata, item_map_keys, type_of_item_type_path, json_value)
        assert child_metadata == {'item_1617349709064': [{'givenNames': {'givenName': {'givenName': 'Stian'}}}]}

    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__create_metadata_of_a_property -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__create_metadata_of_a_property(self, item_type):
        json = json_data("data/item_type/processed_json_2.json")
        json_ld = json_data("data/item_type/ro-crate-metadata_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)

        # case: value in dict  If json_value is not list, use json_value
        metadata = {}
        item_map_key = "item_1617258105262"
        type_of_item_type_path = ["value"]
        json_value = "other"
        mapper._create_metadata_of_a_property(metadata, item_map_key, type_of_item_type_path, json_value)
        assert metadata == {"item_1617258105262": "other"}

        # case: value in dict  If json_value is list, use only first element
        metadata = {}
        item_map_key = "item_1617258105262"
        type_of_item_type_path = ["array"]
        json_value = ["Stian"]
        mapper._create_metadata_of_a_property(metadata, item_map_key, type_of_item_type_path, json_value)
        assert metadata == {"item_1617258105262": "Stian"}

        # case: nested object If _type is "object", create nested metadata  if not metadata.get(_item_map_key):
        metadata = {}
        item_map_key = "item_1617258105262.subitem_1551255647225"
        type_of_item_type_path = ["object", "value"]
        json_value = "サンプルアイテム"
        mapper._create_metadata_of_a_property(metadata, item_map_key, type_of_item_type_path, json_value)
        assert metadata == {"item_1617258105262": {"subitem_1551255647225": "サンプルアイテム"}}

        # case: nested array
        # If _type is "array", do the following method # If diff_array is 0, create [{}, {}, ...] in metadata if not metadata.get(_item_map_key):
        metadata = {}
        item_map_key = "item_1617349709064.givenNames"
        type_of_item_type_path = ["array", "value"]
        json_value = ["Stian"]
        mapper._create_metadata_of_a_property(metadata, item_map_key, type_of_item_type_path, json_value)
        assert metadata == {'item_1617349709064': [{'givenNames': 'Stian'}]}

        # case: nested object in array
        metadata = {}
        item_map_key = "item_1617349709064.givenNames.givenName"
        type_of_item_type_path = ["array", "object", "value"]
        json_value = ["Stian"]
        mapper._create_metadata_of_a_property(metadata, item_map_key, type_of_item_type_path, json_value)
        assert metadata == {'item_1617349709064': [{'givenNames': {'givenName': 'Stian'}}]}

        # case: if diff_array > 0
        metadata = {}
        item_map_key = "item_1617186419668.givenNames.givenName"
        type_of_item_type_path = ["array", "array", "value"]
        json_value = ["Stian"]
        mapper._create_metadata_of_a_property(metadata, item_map_key, type_of_item_type_path, json_value)
        assert metadata == {'item_1617186419668': [{'givenNames': [{'givenName': 'Stian'}]}]}

        # case: If dim_json_value is bigger than num_array_type, pick the first element of json_value until dim_json_value equals to num_array_type
        metadata = {}
        item_map_key = "item_1617186419668.givenName"
        type_of_item_type_path = ["array", "value"]
        json_value = [[["Stian","Stian1"],["Stian2","Stian3"]],[["Stian4", "Stian5"], ["Stian6", "Stian7"]]]
        mapper._create_metadata_of_a_property(metadata, item_map_key, type_of_item_type_path, json_value)
        assert metadata == {'item_1617186419668': [{'givenName': 'Stian'}, {'givenName': 'Stian1'}]}

        # case: nested object　not if not metadata.get(_item_map_key):
        metadata = {"item_1617186476635": {"subitem_1600958577026": "existing_value"}}
        item_map_key = "item_1617186476635.subitem_1600958577026"
        type_of_item_type_path = ["object", "value"]
        json_value = "サンプルアイテム"
        mapper._create_metadata_of_a_property(metadata, item_map_key, type_of_item_type_path, json_value)
        assert metadata == {"item_1617186476635": {"subitem_1600958577026": "サンプルアイテム"}}







        # case: not if not metadata.get(_item_map_key):
        # metadata =  {"item_1617349709064" : [{"givenNames": {"givenName":"XXXXXXXXXXXXXXXXX"}},{"givenNames1": {"givenName":"YYYYYYYYYYYYYYYYY"}}]}
        # item_map_key = "item_1617349709064.givenNames1.givenName"
        # type_of_item_type_path = ["array","object","value"]
        # json_value = ["Stian"]
        # mapper._create_metadata_of_a_property(metadata, item_map_key, type_of_item_type_path, json_value)
        # print(metadata)
        # {'item_1617349709064': [{'givenNames': {'givenName': 'XXXXXXXXXXXXXXXXX'}, 'givenNames1': {'givenName': 'Stian'}}, {'givenNames1': {'givenName': 'YYYYYYYYYYYYYYYYY'}}]}
        # {"item_1617349709064" : [{"givenNames": {"givenName":"XXXXXXXXXXXXXXXXX"}},{"givenNames1": {"givenName":"Stian"}}]}



        # assert metadata == {'item_1617349709064': [{'givenNames': ['Stian', 'John']}, {'givenNames1': {'givenName': 'YYYYYYYYYYYYYYYYY'}}]}



        # case: not if not metadata.get(_item_map_key):
        # metadata =  {"item_1617349709064" : [{"givenNames": {"givenName":"XXXXXXXXXXXXXXXXX"}},{"givenNames1": {"givenName":"YYYYYYYYYYYYYYYYY"}}]}
        # item_map_key = "item_1617349709064.givenNames1.givenName"
        # type_of_item_type_path = ["array","object","value"]
        # json_value = ["Stian"]
        # mapper._create_metadata_of_a_property(metadata, item_map_key, type_of_item_type_path, json_value)
        # print(metadata)
        # assert metadata == {'item_1617349709064': [{'givenNames': {'givenName': 'XXXXXXXXXXXXXXXXX'}}, {'givenNames1': {'givenName': 'Stian'}}]}

    # def _get_dimensions():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__get_dimensions -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__get_dimensions(self, item_type):
        json = None
        json_ld = json_data("data/item_type/ro-crate-metadata_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = None

        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)

        # case: Not a list
        list_0 = 1
        assert mapper._get_dimensions(list_0) == 0

        # case: 1D list
        list_1 = [1, 2, 3]
        assert mapper._get_dimensions(list_1) == 1

        # case: 2D list
        list_2 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        assert mapper._get_dimensions(list_2) == 2

        # case: 3D list
        list_3 = [[[1, 2, 3], [4, 5, 6], [7, 8, 9]], [[1, 2, 3], [4, 5, 6], [7, 8, 9]], [[1, 2, 3], [4, 5, 6], [7, 8, 9]]]
        assert mapper._get_dimensions(list_3) == 3

        # case: Empty list
        list_e = []
        assert mapper._get_dimensions(list_e) == 1

    # def _get_extra_dict():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test__get_extra_dict -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test__get_extra_dict(self, item_type):
        json = None
        json_ld = json_data("data/item_type/ro-crate-metadata_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = None

        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)

        path_and_value ={
            "hasPart.contentSize": [
                "333"
            ],
            "hasPart.version": [
                "1.0"
            ],
            "hasPart.datetime.date": [
                "2023-01-18"
            ],
            "hasPart.datetime.type": [
                "Created"
            ],
            "hasPart.name": [
                "sample.rst"
            ],
            "hasPart.identifier.@id": [
                "https://example.org/data/sample.rst"
            ],
            "hasPart.identifier.type": [
                "fulltext"
            ],
            "hasPart.@id": [
                "data/sample.rst"
            ],
            "hasPart.encodingFormat": [
                "text/x-rst"
            ],
            "#title.name": "サンプルアイテム",
            "#title.language": "ja",
            "author.name": "Egon Willighagen",
            "Resource Type.uri": "",
            "Resource Type.type": "other",
            "contributor.givenName.name": [
                "Stian"
            ],
            "contributor.givenName.language": [
                "en"
            ],
            "contributor.familyName.name": [
                "Soiland-Reyes"
            ],
            "contributor.familyName.language": [
                "en"
            ],
            "contributor.@type": [
                "DataCurator"
            ],
            "contributor.identifier.@id": [
                "https://orcid.org/0000-0002-1234-5679"
            ],
            "contributor.identifier.uri": [
                "https://orcid.org/0000-0002-1234-5679"
            ],
            "contributor.identifier.scheme": [
                "https://orcid.org"
            ],
            "contributor.email": [
                "contributor@example.org"
            ],
            "contributor.language": [
                "en"
            ],
            "contributor.fullname": [
                "Stian Soiland-Reyes"
            ],
            "contributor.affiliation.name": [
                "University of Manchester"
            ],
            "contributor.affiliation.language": [
                "en"
            ],
            "contributor.affiliation.identifier.uri": [
                "https://example.org/affiliation"
            ],
            "contributor.affiliation.identifier.scheme": [
                "GRID"
            ],
            "contributor.affiliation.identifier.@id": [
                "https://example.org/affiliation"
            ],
            "contributor.alternateName.name": [
                "Stian S.R."
            ],
            "contributor.alternateName.language": [
                "en"
            ],
            "#subtitle.name": "試しに作ってみた",
            "#subtitle.language": "ja"
        }
        all_properties = {
            "@id": "./",
            "author.@id": "http://orcid.org/0000-0002-1825-0097",
            "author.identifier.@id": "https://orcid.org/0000-0002-1234-5678",
            "author.identifier.scheme": "https://orcid.org",
            "author.identifier.uri": "https://orcid.org/0000-0002-1234-5678",
            "author.name": "Egon Willighagen",
            "contributor[0].@id": "http://orcid.org/0000-0002-1825-0085",
            "contributor[0].affiliation.@id": "#affiliation",
            "contributor[0].affiliation.identifier.@id": "https://example.org/affiliation",
            "contributor[0].affiliation.identifier.scheme": "GRID",
            "contributor[0].affiliation.identifier.uri": "https://example.org/affiliation",
            "contributor[0].affiliation.language": "en",
            "contributor[0].affiliation.name": "University of Manchester",
            "contributor[0].alternateName.@id": "#alternateName",
            "contributor[0].alternateName.language": "en",
            "contributor[0].alternateName.name": "Stian S.R.",
            "contributor[0].contributorType": "Researcher",
            "contributor[0].email": "contributor@example.org",
            "contributor[0].familyName.@id": "#familyName",
            "contributor[0].familyName.language": "en",
            "contributor[0].familyName.name": "Soiland-Reyes",
            "contributor[0].fullname": "Stian Soiland-Reyes",
            "contributor[0].givenName.@id": "#givenName",
            "contributor[0].givenName.language": "en",
            "contributor[0].givenName.name": "Stian",
            "contributor[0].identifier.@id": "https://orcid.org/0000-0002-1234-5679",
            "contributor[0].identifier.scheme": "https://orcid.org",
            "contributor[0].identifier.uri": "https://orcid.org/0000-0002-1234-5679",
            "contributor[0].language": "en",
            "contributor[0].nametype": "Personal",
            "creator.@id": "http://orcid.org/0000-0002-1825-0097",
            "creator.identifier.@id": "https://orcid.org/0000-0002-1234-5678",
            "creator.identifier.scheme": "https://orcid.org",
            "creator.identifier.uri": "https://orcid.org/0000-0002-1234-5678",
            "creator.name": "Egon Willighagen",
            "datePublished": "2024/11/15T01:59:48Z",
            "accessMode": "public",
            "description": "A simple example for swordserver.",
            "isPartOf.@id": "https://example.org/project/123",
            "isPartOf.name": "Project XYZ",
            "isPartOf.sameAs": "https://192.168.56.101/tree/index/1623632832836",
            "hasPart[0].@id": "data/sample.rst",
            "hasPart[0].contentSize": "333",
            "hasPart[0].datetime.@id": "#datetime",
            "hasPart[0].datetime.date": "2023-01-18",
            "hasPart[0].datetime.type": "Created",
            "hasPart[0].encodingFormat": "text/x-rst",
            "hasPart[0].identifier.@id": "https://example.org/data/sample.rst",
            "hasPart[0].identifier.label": "sample.rst",
            "hasPart[0].identifier.type": "fulltext",
            "hasPart[0].name": "sample.rst",
            "hasPart[0].version": "1.0",
            "hasPart[1].version": "1.0",
            "name": "The Sample",
            "Resource Type.@id": "#resourcetype",
            "Resource Type.type": "other",
            "Resource Type.uri": ""
        }

        extra_dict = mapper._get_extra_dict(path_and_value, all_properties)

        assert extra_dict["@id"] == "./"
        assert extra_dict["author.identifier.@id"] == "https://orcid.org/0000-0002-1234-5678"
        assert extra_dict["contributor[0].@id"] == "http://orcid.org/0000-0002-1825-0085"
        assert extra_dict["creator.name"] == "Egon Willighagen"
        assert extra_dict["datePublished"] == "2024/11/15T01:59:48Z"

    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_mapper.py::TestWekoSwordMapper::test_is_valid_mapping -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_is_valid_mapping(self, item_type):
        json = json_data("data/item_type/processed_json_2.json")
        json_ld = json_data("data/item_type/ro-crate-metadata_2.json")
        itemtype = item_type[1]["item_type"]
        json_map = json_data("data/item_type/sword_mapping_2.json")

        mapper = WekoSwordMapper(json, json_ld, itemtype, json_map)

        # case: valid mapping
        assert mapper.is_valid_mapping() is True

        # case: invalid mapping
        json_map_invalid = {
            "Invalid Key 1": "invalid_key",
            "Invalid Key 2": "invalid_key",
            "Invalid Key 3": "invalid_key"
        }
        mapper_invalid = WekoSwordMapper(json, json_ld, itemtype, json_map_invalid)
        assert mapper_invalid.is_valid_mapping() is False

