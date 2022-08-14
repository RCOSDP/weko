import pytest
from tests.helpers import json_data

from weko_records.serializers.utils import get_mapping, get_full_mapping,\
                                            get_mapping_inactive_show_list

def test_get_mapping():
    mapping = json_data("data/item_type_mapping.json")
    result = get_mapping(mapping, 'jpcoar_mapping')
    data = json_data("data/get_mapping.json")
    assert result == data


def test_get_full_mapping():
    mapping = json_data("data/item_type_mapping.json")
    result = get_full_mapping(mapping, 'jpcoar_mapping')
    data = json_data("data/get_fll_mapping.json")
    assert result == data


def test_get_mapping_inactive_show_list():
    mapping = json_data("data/item_type_mapping.json")
    result = get_mapping_inactive_show_list(mapping, 'jpcoar_mapping')
    data = json_data("data/get_mapping_inactive_show_list.json")
    assert result == data

