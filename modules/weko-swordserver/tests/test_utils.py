# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import pytest
from io import BytesIO
from hashlib import sha256,sha512
from zipfile import ZipFile
from unittest.mock import MagicMock, patch
from weko_swordserver.utils import (
    check_import_file_format,
    is_valid_file_hash,
    update_item_ids
)
from .helpers import json_data
from weko_swordserver.errors import ErrorType, WekoSwordserverException
from weko_swordserver.models import SwordClientModel
from weko_search_ui.mapper import JsonLdMapper


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace

# def check_import_file_format(file, packaging):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_check_import_file_format -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_check_import_file_format(app):
    # No 1
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('metadata/sword.json', '{}')
    file_content.seek(0)
    assert check_import_file_format(file_content, 'SWORDBagIt') == 'JSON'


    # No 2
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('metadata/invalid.json', '{}')
    file_content.seek(0)
    with pytest.raises(WekoSwordserverException) as e:
        check_import_file_format(file_content, 'SWORDBagIt')
    assert e.value.errorType == ErrorType.MetadataFormatNotAcceptable
    assert e.value.message == "SWORDBagIt requires metadate/sword.json."

    # No 3
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('ro-crate-metadata.json', '{}')
    file_content.seek(0)
    assert check_import_file_format(file_content, 'SimpleZip') == 'JSON'

    # No 4
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('invalid.json', '{}')
    file_content.seek(0)
    assert check_import_file_format(file_content, 'SimpleZip') == 'OTHERS'

    # No 5
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('metadata/sword.json', '{}')
    file_content.seek(0)
    packaging = 'InvalidPackaging'
    with pytest.raises(WekoSwordserverException) as e:
        check_import_file_format(file_content, packaging)
    assert e.value.errorType == ErrorType.PackagingFormatNotAcceptable
    assert e.value.message == f"Not accept packaging format: {packaging}"



# def is_valid_file_hash(expected_hash, file):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_is_valid_file_hash -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_is_valid_file_hash():
    # No 1
    file_content = BytesIO(b'This is a test file content')
    file_content.seek(0)
    expected_hash = sha256(b'This is a test file content').hexdigest()
    result = is_valid_file_hash(expected_hash,file_content)
    assert result is True

    # No 2
    file_content.seek(0)
    invalid_hash = sha256(b'Invalid content').hexdigest()
    result = is_valid_file_hash(invalid_hash ,file_content)
    assert result is False

    # No 3:
    file_content = BytesIO(b'This is a test file content')
    file_content.seek(0)
    expected_hash = sha512(b'This is a test file content').hexdigest()
    result = is_valid_file_hash(expected_hash,file_content )
    assert result is False

    # No 4:
    file_content = BytesIO(b'This is a test file content')
    file_content.seek(0)
    expected_hash = sha256(b'This is a test file content')
    result = is_valid_file_hash(expected_hash,file_content )
    assert result is False


# def update_item_ids(list_record, new_id):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_update_item_ids -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_update_item_ids(app, mocker):
    """
    update_item_ids 関数の動作をテストする。
    すべての条件分岐やエッジケースをカバーする。
    """
    # list_record が空のリストの場合
    assert update_item_ids([], "new_id") == []

    # list_record に dict 以外の要素が含まれている場合
    # list_record_3 = [1, 2, 3]
    # assert update_item_ids(list_record_3, "new_id") == list_record_3

    # list_record の要素に metadata がない場合
    list_record_4 = [{"key": "value"}]
    assert update_item_ids(list_record_4, "new_id") == list_record_4

    # metadata に id がない場合
    list_record_5 = [{"metadata": {}}]
    assert update_item_ids(list_record_5, "new_id") == list_record_5

    # metadata に link_data がない場合
    list_record_6 = [{"metadata": {"id": "123"}}]
    assert update_item_ids(list_record_6, "new_id") == list_record_6

    metadata = {"test": "test"}

    # link_data の要素に item_id と sele_id がない場合
    list_record_9 = [{"metadata": metadata, "id": "123", "link_data": [{"key": "value"}]}]
    assert update_item_ids(list_record_9, "new_id") == list_record_9

    # link_data の要素に item_id があるが、sele_id が "isSupplementedBy" でない場合
    _id = "123"
    link_data = [{"item_id": "456", "sele_id": "isSupplementTo"}]

    list_record = [{"metadata": metadata, "_id": _id, "link_data": link_data}]
    new_id = "new_id"

    result = update_item_ids(list_record, new_id)

    assert result[0]["link_data"][0]["item_id"] == "456"
    assert result[0]["link_data"][0]["sele_id"] == "isSupplementTo"

    # link_data の要素に item_id があり、sele_id が "isSupplementedBy" の場合
    _id = "123"
    link_data = [{"item_id": "123", "sele_id": "isSupplementedBy"}]

    list_record = [{"metadata": metadata, "_id": _id, "link_data": link_data}]
    new_id = "new_id"

    result = update_item_ids(list_record, new_id)


    assert result[0]["link_data"][0]["item_id"] == new_id
    assert link_data == [{"item_id": "new_id", "sele_id": "isSupplementedBy"}]

    # 複数の ITEM が含まれる場合
    _id1 = "123"
    link_data1 = [{"item_id": "789", "sele_id": "isSupplementTo"}]

    _id2 = "789"
    link_data2 = [{"item_id": "123", "sele_id": "isSupplementedBy"}]

    list_record = [
        {"metadata": metadata, "_id": _id1, "link_data": link_data1},
        {"metadata": metadata, "_id": _id2, "link_data": link_data2}
    ]
    new_id = "new_id"

    result = update_item_ids(list_record, new_id)

    assert result[0]["link_data"][0]["item_id"] == "789"
    assert result[1]["link_data"][0]["item_id"] == new_id


# def get_record_by_client_id(client_id):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_get_record_by_client_id -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
# def test_get_record_by_client_id(app,mocker):
#     # No 1
#     client_id = "valid_client_id"
#     expected_client = SwordClientModel(client_id="client_id", mapping_id="mapping_id")
#     expected_mapping = SwordItemTypeMappingModel(id="mapping_id")

#     with patch.object(SwordClient, 'get_client_by_id', return_value=expected_client):
#         with patch.object(SwordItemTypeMapping, 'get_mapping_by_id', return_value=expected_mapping):
#             client, mapping = get_record_by_client_id(client_id)
#             assert client == expected_client
#             assert mapping == expected_mapping

#     # No 2
#     invalid_client_id = "invalid_client_id"

#     with patch.object(SwordClient, 'get_client_by_id', return_value=None):
#         with patch.object(SwordItemTypeMapping, 'get_mapping_by_id', return_value=expected_mapping):
#             client, mapping = get_record_by_client_id(invalid_client_id)
#             assert client == None
#             assert mapping == expected_mapping

#     # No 3
#     valid_client_id = "valid_client_id"
#     expected_client = SwordClientModel(client_id="client_id", mapping_id="invalid_mapping_id")
#     with patch.object(SwordClient, 'get_client_by_id', return_value=expected_client):
#         with patch.object(SwordItemTypeMapping, 'get_mapping_by_id', return_value=None):
#             client, mapping = get_record_by_client_id(valid_client_id)
#             assert client == expected_client
#             assert mapping == None
