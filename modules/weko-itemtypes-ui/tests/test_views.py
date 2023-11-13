import pytest
import copy
import os
import json
from datetime import datetime

from weko_itemtypes_ui.views import replace_mapping_version

# def itemtype_mapping(ItemTypeID=0):
# def get_itemtypes():
#     def convert(item):

# pytest -v --cov=weko_itemtypes_ui tests/test_views.py::test_replace_mapping_version --cov-branch --cov-report=term --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
# def replace_mapping_version(jp_key):
@pytest.mark.parametrize(
    "jp_key, return_key_value",
    [
        ("publisher_jpcoar", "publisher(jpcoar)"),
        ("publisher", "publisher(dc)"),
        ("date_dcterms", "date(dcterms)"),
        ("date", "date(datacite)"),
        ("versiontype", "version(oaire)"),
        ("version", "version(datacite)"),
        ("test", "test")
    ]
)
def test_replace_mapping_version(app, jp_key, return_key_value):
    if jp_key == "publisher_jpcoar":
        assert replace_mapping_version(jp_key) == return_key_value

    elif jp_key == "publisher":
        assert replace_mapping_version(jp_key) == return_key_value

    elif jp_key == "date_dcterms":
        assert replace_mapping_version(jp_key) == return_key_value

    elif jp_key == "date":
        assert replace_mapping_version(jp_key) == return_key_value

    elif jp_key == "versiontype":
        assert replace_mapping_version(jp_key) == return_key_value

    elif jp_key == "version":
        assert replace_mapping_version(jp_key) == return_key_value

    else:
        assert replace_mapping_version(jp_key) == return_key_value

    
    