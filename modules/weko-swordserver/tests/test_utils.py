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
from weko_accounts.models import ShibbolethUser
from weko_admin.models import AdminSettings
from weko_swordserver.utils import (
    check_import_file_format,
    check_import_items,
    get_shared_id_from_on_behalf_of,
    is_valid_file_hash,
    update_item_ids,
    check_deletion_type,
    delete_item_directly
)
from .helpers import json_data
from weko_swordserver.errors import ErrorType, WekoSwordserverException
from weko_swordserver.models import SwordClientModel
from weko_search_ui.mapper import JsonLdMapper


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace

# def check_import_file_format(file, packaging):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_check_import_file_format -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_check_import_file_format(app):
    # SWORDBagIt; metadata/sword.json
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('metadata/sword.json', '{}')
    file_content.seek(0)
    assert check_import_file_format(file_content, 'SWORDBagIt') == 'JSON'

    # SWORDBagIt; invalid json file
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('metadata/invalid.json', '{}')
    file_content.seek(0)
    with pytest.raises(WekoSwordserverException) as e:
        check_import_file_format(file_content, 'SWORDBagIt')
    assert e.value.errorType == ErrorType.MetadataFormatNotAcceptable
    assert e.value.message == "SWORDBagIt requires metadate/sword.json."

    # SWORDBagIt; mismatch packaging
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('metadata/sword.json', '{}')
    file_content.seek(0)
    with pytest.raises(WekoSwordserverException) as e:
        check_import_file_format(file_content, 'SimpleZip')
    assert e.value.errorType == ErrorType.MetadataFormatNotAcceptable
    assert e.value.message == "packaging format is SimpleZip, but sword.json is found."

    # RO-Crate; ro-crate-metadata.json
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('data/ro-crate-metadata.json', '{}')
    file_content.seek(0)
    assert check_import_file_format(file_content, 'SimpleZip') == 'JSON'

    # RO-Crate; invalid place
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('metadata/ro-crate-metadata.json', '{}')
    file_content.seek(0)
    with pytest.raises(WekoSwordserverException) as e:
        check_import_file_format(file_content, 'SimpleZip')
    assert e.value.errorType == ErrorType.MetadataFormatNotAcceptable
    assert e.value.message == "ro-crate-metadata.json is required in data/ directory."

    # Invalid json file
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('invalid.json', '{}')
    file_content.seek(0)
    with pytest.raises(WekoSwordserverException) as e:
        check_import_file_format(file_content, 'SimpleZip')
    assert e.value.errorType == ErrorType.ContentMalformed
    assert e.value.message == "SimpleZip requires ro-crate-metadata.json or other metadata file."

    # Invalid packaging format
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('metadata/sword.json', '{}')
    file_content.seek(0)
    packaging = 'InvalidPackaging'
    with pytest.raises(WekoSwordserverException) as e:
        check_import_file_format(file_content, packaging)
    assert e.value.errorType == ErrorType.PackagingFormatNotAcceptable
    assert e.value.message == f"Not accept packaging format: {packaging}"

    # TSV
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('data/itemtype（1）.tsv', '')
    file_content.seek(0)
    assert check_import_file_format(file_content, 'SimpleZip') == 'TSV/CSV'

    # CSV
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('data/itemtype（1）.csv', '')
    file_content.seek(0)
    assert check_import_file_format(file_content, 'SimpleZip') == 'TSV/CSV'

    # XML
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('data/itemtype.xml', '')
    file_content.seek(0)
    assert check_import_file_format(file_content, 'SimpleZip') == 'XML'


# def get_shared_id_from_on_behalf_of(on_behalf_of):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_get_shared_id_from_on_behalf_of -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_get_shared_id_from_on_behalf_of(app, db, users, personal_token):
    on_behalf_of = None
    assert get_shared_id_from_on_behalf_of(on_behalf_of) == -1

    on_behalf_of = users[3].get("email")
    assert get_shared_id_from_on_behalf_of(on_behalf_of) == users[3]["id"]

    on_behalf_of = personal_token[3]["token"].access_token
    assert get_shared_id_from_on_behalf_of(on_behalf_of) == personal_token[3]["token"].user_id
    assert get_shared_id_from_on_behalf_of(on_behalf_of) == users[3]["id"]

    shib_user = ShibbolethUser(shib_eppn="test@example.ac.jp", shib_user_name="testuser", weko_uid=users[3]["id"])
    db.session.add(shib_user)
    db.session.commit()
    on_behalf_of = shib_user.shib_eppn
    assert get_shared_id_from_on_behalf_of(on_behalf_of) == users[3]["id"]

    on_behalf_of = "invalid"
    with pytest.raises(WekoSwordserverException) as e:
        get_shared_id_from_on_behalf_of(on_behalf_of)
    assert e.value.errorType == ErrorType.BadRequest
    assert e.value.message == "No user found by On-Behalf-Of."

    on_behalf_of = 999
    with pytest.raises(WekoSwordserverException) as e:
        get_shared_id_from_on_behalf_of(on_behalf_of)
    assert e.value.errorType == ErrorType.ServerError
    assert e.value.message == "Failed to get shared ID from On-Behalf-Of."

# def is_valid_file_hash(expected_hash, file):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_is_valid_file_hash -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_is_valid_file_hash():
    # correct hash
    body = b"This is a test file content."
    file_content = BytesIO(body)
    file_content.seek(0)
    expected_hash = sha256(body).hexdigest()
    assert is_valid_file_hash(expected_hash, file_content)

    # incorrect hash
    file_content.seek(0)
    invalid_hash = sha256(b'Invalid content').hexdigest()
    assert not is_valid_file_hash(invalid_hash, file_content)

    # invalid hash algorithm
    file_content = BytesIO(body)
    file_content.seek(0)
    expected_hash = sha512(body).hexdigest()
    assert not is_valid_file_hash(expected_hash, file_content)

    # No 4:
    file_content = BytesIO(body)
    file_content.seek(0)
    expected_hash = sha256(body)
    assert not is_valid_file_hash(expected_hash, file_content)


# def check_import_items(file, file_format, is_change_identifier=False, shared_id=-1, **kwargs):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_check_import_items -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_check_import_items(app, admin_settings, item_type, workflow, sword_client, mocker):
    item_type_id = item_type[0]["item_type"].id
    item_type_name = item_type[0]["item_type_name"].name
    AdminSettings.update("sword_api_setting", {"TSV/CSV": {"active": True, "item_type": str(item_type_id), "registration_type": "Direct", "duplicate_check": False}})

    # check tsv, direct registration, shared_id is -1
    file_content = BytesIO()
    mocker_tsv_check = mocker.patch("weko_swordserver.utils.check_tsv_import_items")
    mocker_tsv_check.return_value = {
        "list_record": [{"item_type_id": item_type_id, "item_type_name": item_type_name, "metadata": {"title": "test"}}],
    }
    check_result = check_import_items(file_content, "TSV/CSV")

    mocker_tsv_check.assert_called_once_with(file_content, False, shared_id=-1)
    assert check_result["list_record"][0]["item_type_id"] == item_type_id
    assert check_result["list_record"][0]["item_type_name"] == item_type_name
    assert check_result["list_record"][0]["metadata"]["title"] == "test"
    assert check_result["register_type"] == "Direct"
    assert check_result["duplicate_check"] == False

    # check tsv, workflow registration, shared_id is 3
    AdminSettings.update("sword_api_setting", {"TSV/CSV": {"active": True, "item_type": str(item_type_id), "registration_type": "Workflow", "duplicate_check": True}})
    file_content = BytesIO()
    mocker_tsv_check = mocker.patch("weko_swordserver.utils.check_tsv_import_items")
    mocker_tsv_check.return_value = {
        "list_record": [{"item_type_id": item_type_id, "item_type_name": item_type_name, "metadata": {"title": "test"}}]
    }
    check_result = check_import_items(file_content, "TSV/CSV", True, 3)

    mocker_tsv_check.assert_called_once_with(file_content, True, shared_id=3)
    assert check_result["list_record"][0]["item_type_id"] == item_type_id
    assert check_result["list_record"][0]["item_type_name"] == item_type_name
    assert check_result["list_record"][0]["metadata"]["title"] == "test"
    assert check_result["register_type"] == "Workflow"
    assert check_result["workflow_id"] == workflow[0]["workflow"].id
    assert check_result["duplicate_check"] == True

    # check jsonld, direct registration, shared_id is -1
    client_id = sword_client[0]["sword_client"].client_id
    mapping_id = sword_client[0]["sword_client"].mapping_id
    file_content = BytesIO()
    mocker_jsonld_check = mocker.patch("weko_swordserver.utils.check_jsonld_import_items")
    mocker_jsonld_check.return_value = {
        "list_record": [{"item_type_id": item_type_id, "item_type_name": item_type_name, "metadata": {"title": "test"}}]
    }
    app.config["WEKO_SWORDSERVER_BAGIT_VERIFICATION"] = False
    check_result = check_import_items(file_content, "JSON", False, -1, packaging="SimpleZip", client_id=client_id)

    mocker_jsonld_check.assert_called_once_with(file_content, "SimpleZip", mapping_id, [], -1, validate_bagit=False, is_change_identifier=False)
    assert check_result["list_record"][0]["item_type_id"] == item_type_id
    assert check_result["list_record"][0]["item_type_name"] == item_type_name
    assert check_result["list_record"][0]["metadata"]["title"] == "test"
    assert check_result["register_type"] == "Direct"
    assert check_result["duplicate_check"] == False

    # check jsonld, workflow registration, shared_id is 3
    client_id = sword_client[1]["sword_client"].client_id
    mapping_id = sword_client[1]["sword_client"].mapping_id
    file_content = BytesIO()
    mocker_jsonld_check = mocker.patch("weko_swordserver.utils.check_jsonld_import_items")
    mocker_jsonld_check.return_value = {
        "list_record": [{"item_type_id": item_type_id, "item_type_name": item_type_name, "metadata": {"title": "test"}}]
    }
    app.config["WEKO_SWORDSERVER_BAGIT_VERIFICATION"] = True
    check_result = check_import_items(file_content, "JSON", True, 3, packaging="SimpleZip", client_id=client_id)
    mocker_jsonld_check.assert_called_once_with(file_content, "SimpleZip", mapping_id, [], 3, validate_bagit=True, is_change_identifier=True)
    assert check_result["list_record"][0]["item_type_id"] == item_type_id
    assert check_result["list_record"][0]["item_type_name"] == item_type_name
    assert check_result["list_record"][0]["metadata"]["title"] == "test"
    assert check_result["register_type"] == "Workflow"
    assert check_result["workflow_id"] == sword_client[1]["sword_client"].workflow_id
    assert check_result["duplicate_check"] == True

    # tsv, workflow not found
    file_content = BytesIO()
    mocker_tsv_check = mocker.patch("weko_swordserver.utils.check_tsv_import_items")
    mocker_tsv_check.return_value = {
        "list_record": [{"item_type_id": item_type_id, "item_type_name": item_type_name, "metadata": {"title": "test"}}]
    }
    with patch("weko_swordserver.utils.WorkFlows.get_workflow_by_itemtype_id", return_value=[]):
        check_result = check_import_items(file_content, "TSV/CSV", True, 3)
    assert check_result["error"] == "Workflow not found for item type ID."

    # tsv, registration workflow not found
    file_content = BytesIO()
    mocker_tsv_check = mocker.patch("weko_swordserver.utils.check_tsv_import_items")
    mocker_tsv_check.return_value = {
        "list_record": [{"item_type_id": item_type_id, "item_type_name": item_type_name, "metadata": {"title": "test"}}]
    }
    with patch("weko_swordserver.utils.WorkFlows.reduce_workflows_for_registration", return_value=[]):
        check_result = check_import_items(file_content, "TSV/CSV", True, 3)
    assert check_result["error"] == "No workflow found for item type ID."

    item_type_id = item_type[1]["item_type"].id
    item_type_name = item_type[1]["item_type_name"].name
    # xml, direct registration, not supported
    AdminSettings.update("sword_api_setting", {"XML": {"active": True, "item_type": str(item_type_id), "registration_type": "Direct", "duplicate_check": False}})
    file_content = BytesIO()
    with pytest.raises(WekoSwordserverException) as e:
        check_import_items(file_content, "XML")
    assert e.value.errorType == ErrorType.MetadataFormatNotAcceptable
    assert e.value.message == "Direct registration is not allowed for XML metadata yet."

    # xml, workflow registration, shared_id is 3
    AdminSettings.update("sword_api_setting", {"XML": {"active": True, "item_type": str(item_type_id), "registration_type": "Workflow", "workflow": str(workflow[1]["workflow"].id), "duplicate_check": True}})
    file_content = BytesIO()
    mocker_xml_check = mocker.patch("weko_swordserver.utils.check_xml_import_items")
    mocker_xml_check.return_value = {
        "list_record": [{"item_type_id": item_type_id, "item_type_name": item_type_name, "metadata": {"title": "test"}}]
    }
    check_result = check_import_items(file_content, "XML", True, 3)
    mocker_xml_check.assert_called_once_with(file_content, item_type_id, shared_id=3)
    assert check_result["list_record"][0]["item_type_id"] == item_type_id
    assert check_result["list_record"][0]["item_type_name"] == item_type_name
    assert check_result["list_record"][0]["metadata"]["title"] == "test"
    assert check_result["register_type"] == "Workflow"
    assert check_result["workflow_id"] == workflow[1]["workflow"].id
    assert check_result["duplicate_check"] == True

    # import item format is not active
    AdminSettings.update("sword_api_setting", {"TSV/CSV": {"active": False, "item_type": str(item_type_id), "registration_type": "Workflow", "duplicate_check": True}})
    file_content = BytesIO()
    mocker_tsv_check = mocker.patch("weko_swordserver.utils.check_tsv_import_items")
    with pytest.raises(WekoSwordserverException) as e:
        check_import_items(file_content, "TSV/CSV", True, 3)
    e.value.errorType == ErrorType.MetadataFormatNotAcceptable
    e.value.message == "TSV/CSV metadata import is not enabled."

    AdminSettings.update("sword_api_setting", {})
    file_content = BytesIO()
    mocker_tsv_check = mocker.patch("weko_swordserver.utils.check_tsv_import_items")
    with pytest.raises(WekoSwordserverException) as e:
        check_import_items(file_content, "XML", True, 3)
    e.value.errorType == ErrorType.MetadataFormatNotAcceptable
    e.value.message == "XML metadata import is not enabled."

    # xml, workflow not found
    AdminSettings.update("sword_api_setting", {"XML": {"active": True, "item_type": str(item_type_id), "registration_type": "Workflow", "workflow": str(workflow[1]["workflow"].id), "duplicate_check": False}})
    file_content = BytesIO()
    with patch("weko_swordserver.utils.WorkFlows.get_workflow_by_id", return_value=None):
        with pytest.raises(WekoSwordserverException) as e:
            check_result = check_import_items(file_content, "XML", True, 3)
    assert e.value.errorType == ErrorType.BadRequest
    assert e.value.message == "Workflow not found for registration your item."

    # xml, registration workflow not found
    file_content = BytesIO()
    with patch("weko_swordserver.utils.WorkFlows.reduce_workflows_for_registration", return_value=[]):
        with pytest.raises(WekoSwordserverException) as e:
            check_result = check_import_items(file_content, "XML", True, 3)
    assert e.value.errorType == ErrorType.BadRequest
    assert e.value.message == "Workflow is not for item registration."

    # jsonld, sword_client not found
    client_id = "invalid_client_id"
    file_content = BytesIO()
    with pytest.raises(WekoSwordserverException) as e:
        check_result = check_import_items(file_content, "JSON", True, 3, packaging="SimpleZip", client_id=client_id)
    assert e.value.errorType == ErrorType.BadRequest
    assert e.value.message == "No SWORD API setting found for client ID that you are using."

    # jsonld, workflow not found
    client_id = sword_client[1]["sword_client"].client_id
    mapping_id = sword_client[1]["sword_client"].mapping_id
    file_content = BytesIO()
    with patch("weko_swordserver.utils.WorkFlows.get_workflow_by_id", return_value=None):
        with pytest.raises(WekoSwordserverException) as e:
            check_result = check_import_items(file_content, "JSON", True, 3, packaging="SimpleZip", client_id=client_id)
    assert e.value.errorType == ErrorType.BadRequest
    assert e.value.message == "Workflow not found for registration your item."

    # jsonld, registration workflow not found
    with patch("weko_swordserver.utils.WorkFlows.reduce_workflows_for_registration", return_value=[]):
        with pytest.raises(WekoSwordserverException) as e:
            check_result = check_import_items(file_content, "JSON", True, 3, packaging="SimpleZip", client_id=client_id)
    assert e.value.errorType == ErrorType.BadRequest
    assert e.value.message == "Workflow is not for item registration."

    # invalid file format
    file_content = BytesIO()
    with pytest.raises(WekoSwordserverException) as e:
        check_import_items(file_content, "InvalidFormat")
    assert e.value.errorType == ErrorType.MetadataFormatNotAcceptable
    assert e.value.message == "Unsupported file format: InvalidFormat"


# def update_item_ids(list_record, new_id):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_update_item_ids -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_update_item_ids(app, mocker):
    """
    update_item_ids 関数の動作をテストする。
    すべての条件分岐やエッジケースをカバーする。
    """
    # list_record が空のリストの場合
    assert update_item_ids([], "new_id", "old_id") == []

    # list_record の要素に metadata がない場合
    list_record_4 = [{"key": "value"}]
    assert update_item_ids(list_record_4, "new_id", "old_id") == list_record_4

    # metadata に id がない場合
    list_record_5 = [{"metadata": {}}]
    assert update_item_ids(list_record_5, "new_id", "old_id") == list_record_5

    # metadata に link_data がない場合
    list_record_6 = [{"metadata": {"id": "123"}}]
    assert update_item_ids(list_record_6, "new_id", "old_id") == list_record_6

    metadata = {"test": "test"}

    # link_data の要素が 辞書でない場合
    list_record_7 = [{"metadata": metadata, "id": "123", "link_data": ["not_a_dict"]}]
    assert update_item_ids(list_record_7, "new_id", "old_id") == list_record_7

    # link_data の要素に item_id と sele_id がない場合
    list_record_9 = [{"metadata": metadata, "id": "123", "link_data": [{"key": "value"}]}]
    assert update_item_ids(list_record_9, "new_id", "old_id") == list_record_9

    # link_data の要素に item_id があるが、old_idがない場合
    _id = "123"
    link_data = [{"item_id": "456"}]

    list_record = [{"metadata": metadata, "_id": _id, "link_data": link_data}]
    new_id = "new_id"
    old_id = "old_id"

    result = update_item_ids(list_record, new_id, old_id)

    assert result[0]["link_data"][0]["item_id"] == "456"

    # link_data の要素に item_id があり、old_idがある場合
    _id = "123"
    link_data = [{"item_id": "123"}]

    list_record = [{"metadata": metadata, "_id": _id, "link_data": link_data}]
    new_id = "new_id"
    old_id = "123"

    result = update_item_ids(list_record, new_id, old_id)

    assert result[0]["link_data"][0]["item_id"] == new_id

    # 複数の ITEM が含まれる場合
    _id1 = "123"
    link_data1 = [{"item_id": "789"}]

    _id2 = "789"
    link_data2 = [{"item_id": "123"}]

    list_record = [
        {"metadata": metadata, "_id": _id1, "link_data": link_data1},
        {"metadata": metadata, "_id": _id2, "link_data": link_data2}
    ]
    new_id = "new_id"
    old_id = "123"

    result = update_item_ids(list_record, new_id, old_id)

    assert result[0]["link_data"][0]["item_id"] == "789"
    assert result[1]["link_data"][0]["item_id"] == new_id


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_check_deletion_type -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
@pytest.mark.parametrize("register_type, workflow_exists, workflow_deleted, delete_flow_id, expected", [
    # Workflow type, workflow exists, not deleted, has delete_flow_id
    ("Workflow", True, False, 123, {"deletion_type": "Workflow", "workflow_id": 2, "delete_flow_id": 123}),
    # Workflow type, workflow exists, not deleted, no delete_flow_id
    ("Workflow", True, False, None, {"deletion_type": "Direct"}),
    # Workflow type, workflow exists, deleted, has delete_flow_id
    ("Workflow", True, True, 456, None),
    # Workflow type, workflow does not exist
    ("Workflow", False, None, None, None),
    # Direct type
    ("Direct", None, None, None, {"deletion_type": "Direct"}),
])
def test_check_deletion_type(app, mocker, register_type, workflow_exists, workflow_deleted, delete_flow_id, expected):
    mock_sword_client = MagicMock()
    mock_sword_client.registration_type = register_type
    mock_sword_client.workflow_id = 2

    mocker.patch("weko_swordserver.utils.SwordClient.get_client_by_id", return_value=mock_sword_client)

    if register_type == "Workflow":
        if workflow_exists:
            workflow = MagicMock()
            workflow.is_deleted = workflow_deleted
            workflow.delete_flow_id = delete_flow_id
            mocker.patch("weko_swordserver.utils.WorkFlows.get_workflow_by_id", return_value=workflow)
        else:
            mocker.patch("weko_swordserver.utils.WorkFlows.get_workflow_by_id", return_value=None)
    client_id = "test_client_id"
    if register_type == "Workflow" and (not workflow_exists or workflow_deleted):
        with pytest.raises(WekoSwordserverException) as e:
            check_deletion_type(client_id)
        assert e.value.errorType == ErrorType.BadRequest
        assert e.value.message == "Workflow not found for registration your item."
    else:
        result = check_deletion_type(client_id)
        for k, v in expected.items():
            assert result[k] == v


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_check_deletion_type_no_sword_client -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_check_deletion_type_no_sword_client(app, mocker):
    mocker.patch("weko_swordserver.utils.SwordClient.get_client_by_id", return_value=None)
    with pytest.raises(WekoSwordserverException) as e:
        check_deletion_type("notfound")
    assert e.value.errorType == ErrorType.BadRequest
    assert e.value.message == "No SWORD API setting found for client ID that you are using."


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_check_deletion_type_invalid_registration_type -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_check_deletion_type_invalid_registration_type(app, mocker):
    mock_sword_client = MagicMock()
    mock_sword_client.registration_type = "InvalidType"
    mocker.patch("weko_swordserver.utils.SwordClient.get_client_by_id", return_value=mock_sword_client)
    with pytest.raises(WekoSwordserverException) as e:
        check_deletion_type("invalidtype")
    assert e.value.errorType == ErrorType.ServerError
    assert e.value.message == "Invalid registration type: InvalidType"


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_delete_item_directly -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
@pytest.mark.parametrize(
    "recid, resolve_return, locked, being_edited, raises, error_type, message",
    [
        ("recid123", (MagicMock(), MagicMock()), False, False, None, None, None),
        ("recid_not_found", (MagicMock(), None), None, None,
         WekoSwordserverException, ErrorType.NotFound, "Record not found."),
        ("recid_locked", (MagicMock(), MagicMock()), True, None,
         WekoSwordserverException, ErrorType.BadRequest, "Item cannot be deleted because it is in import progress."),
        ("recid_editing", (MagicMock(), MagicMock()), False, True,
         WekoSwordserverException, ErrorType.BadRequest, "Item cannot be deleted because it is being edited."),
    ]
)
def test_delete_item_directly(
    app, mocker, recid, resolve_return, locked, being_edited, raises, error_type, message
):
    resolver_mock = mocker.patch("weko_swordserver.utils.Resolver")
    resolver_instance = resolver_mock.return_value
    resolver_instance.resolve.return_value = resolve_return

    latest_pid = MagicMock()
    latest_pid.object_uuid = "uuid"
    pid_versioning_mock = mocker.patch("weko_swordserver.utils.PIDVersioning")
    pid_versioning_mock.return_value.last_child = latest_pid

    work_activity_mock = mocker.patch("weko_swordserver.utils.WorkActivity")
    work_activity_instance = work_activity_mock.return_value
    work_activity_instance.get_workflow_activity_by_item_id.return_value = "latest_activity"

    mocker.patch("weko_swordserver.utils.check_an_item_is_locked",
                 return_value=locked if locked is not None else False)
    mocker.patch("weko_swordserver.utils.check_item_is_being_edit",
                 return_value=being_edited if being_edited is not None else False)
    soft_delete_mock = mocker.patch("weko_swordserver.utils.soft_delete")

    if raises:
        with pytest.raises(raises) as e:
            delete_item_directly(recid)
        assert e.value.errorType == error_type
        assert e.value.message == message
    else:
        delete_item_directly(recid)
        soft_delete_mock.assert_called_once_with(recid)
