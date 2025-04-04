# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import os
import copy
import uuid
import pytest
import bagit
from zipfile import BadZipFile
from flask import json
from flask_login.utils import login_user
from unittest.mock import MagicMock, patch, PropertyMock
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.datastructures import FileStorage

from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_pidstore.models import PersistentIdentifier
from weko_search_ui.utils import handle_validate_item_import
from weko_workflow.models import Activity, WorkFlow

from weko_swordserver.errors import ErrorType, WekoSwordserverException

from .helpers import json_data


@pytest.fixture()
def admin_tsv_settings(workflow):
    return {
        "default_format": "TSV",
        "data_format": {
            "TSV": {
                "register_format": "Direct"
            },
            "XML": {
                "workflow": str(workflow[0]["workflow"].id),
                "register_format": "Workflow"
            }
        }
    }


@pytest.fixture()
def admin_xml_settings(workflow):
    return {
        "default_format": "XML",
        "data_format": {
            "TSV": {
                "register_format": "Direct"
            },
            "XML": {
                "workflow": str(workflow[0]["workflow"].id),
                "register_format": "Workflow"
            }
        }
    }

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace

# def check_import_items(file, is_change_identifier: bool = False)
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py::test_check_import_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
@pytest.mark.skip(reason="old test")
def test_check_import_items(app, admin_tsv_settings, admin_xml_settings):
    check_tsv_result = {"error": [], "list_record": [{"sample": "Tsv metadata here."}]}
    check_xml_result = {"error": [], "list_record": [{"sample": "Xml metadata here."}]}
    check_tsv_error_result = {"error": ["something tsv error happend"]}
    check_xml_error_result = {"error": ["something xml error happend"]}
    sample_files = "This is sample files data."
    # Case01:  default_format = TSV and import tsv
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_tsv_settings):
        with patch("weko_swordserver.registration.check_tsv_import_items", return_value=check_tsv_result):
            check_result, file_format = check_import_items(sample_files)
            assert check_result == check_tsv_result
            assert file_format == "TSV/CSV"

    # Case02: default_format = TSV but try import xml
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_tsv_settings):
        with patch("weko_swordserver.registration.check_tsv_import_items", return_value=check_tsv_error_result):
            with patch("weko_swordserver.registration.check_xml_import_items", return_value=check_xml_result):
                check_result, file_format = check_import_items(sample_files)
                assert check_result == check_xml_result
                assert file_format == "XML"

    # Case03: default_format = TSV and import error
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_tsv_settings):
        with patch("weko_swordserver.registration.check_tsv_import_items", return_value=check_tsv_error_result):
            with patch("weko_swordserver.registration.check_xml_import_items", return_value=check_xml_error_result):
                check_result, file_format = check_import_items(sample_files)
                assert check_result == check_tsv_error_result
                assert file_format is None

    # Case04:  default_format = XML and import xml
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_xml_settings):
        with patch("weko_swordserver.registration.check_xml_import_items", return_value=check_xml_result):
            check_result, file_format = check_import_items(sample_files)
            assert check_result == check_xml_result
            assert file_format == "XML"

    # Case05: default_format = XML but try import tsv
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_xml_settings):
        with patch("weko_swordserver.registration.check_xml_import_items", return_value=check_xml_error_result):
            with patch("weko_swordserver.registration.check_tsv_import_items", return_value=check_tsv_result):
                check_result, file_format = check_import_items(sample_files)
                assert check_result == check_tsv_result
                assert file_format == "TSV/CSV"

    # Case06: default_format = XML and import error
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_xml_settings):
        with patch("weko_swordserver.registration.check_xml_import_items", return_value=check_xml_error_result):
            with patch("weko_swordserver.registration.check_tsv_import_items", return_value=check_tsv_error_result):
                check_result, file_format = check_import_items(sample_files)
                assert check_result == check_xml_error_result
                assert file_format is None

    # Case07: default_format = <unknown>
    admin_unknown_settings = {"default_format": "anonymous"}
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_unknown_settings):
        check_result, file_format = check_import_items(sample_files)
        assert check_result == {}
        assert file_format is None

    # Case08: workflow not found (TSV)
    admin_unknown_settings = {"default_format": "anonymous"}
    with patch("weko_admin.admin.AdminSettings.get", return_value={
        "default_format": "TSV",
        "data_format": {
            "TSV": {
                "register_format": "Direct"
            },
            "XML": {
                "workflow": "9999",
                "register_format": "Workflow"
            }
        }
    }):
        with patch("weko_swordserver.registration.check_tsv_import_items", return_value=check_tsv_error_result):
            with pytest.raises(WekoSwordserverException) as ex:
                check_result, file_format = check_import_items(sample_files)
                assert ex.value.errorType == ErrorType.ServerError
                assert ex.value.message == "Workflow is not configured for importing xml."

    # Case09: workflow not found (XML)
    admin_unknown_settings = {"default_format": "anonymous"}
    with patch("weko_admin.admin.AdminSettings.get", return_value={
        "default_format": "XML",
        "data_format": {
            "TSV": {
                "register_format": "Direct"
            },
            "XML": {
                "workflow": "9999",
                "register_format": "Workflow"
            }
        }
    }):
        with pytest.raises(WekoSwordserverException) as ex:
            check_result, file_format = check_import_items(sample_files)
            assert ex.errorType == ErrorType.ServerError
            assert ex.message == "Workflow is not configured for importing xml."

    # Case09: workflow has been deleted (TSV)
    workflow = MagicMock(spec=WorkFlow)
    workflow.is_deleted = True
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_tsv_settings):
        with patch("weko_swordserver.registration.check_tsv_import_items", return_value=check_tsv_error_result):
            with patch("sqlalchemy.orm.Query.get", return_value=workflow):
                with pytest.raises(WekoSwordserverException) as ex:
                    check_result, file_format = check_import_items(sample_files)
                    assert ex.value.errorType == ErrorType.ServerError
                    assert ex.value.message == "Workflow is not configured for importing xml."

    # Case10: workflow has been deleted (XML)
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_xml_settings):
        with patch("sqlalchemy.orm.Query.get", return_value=workflow):
            with pytest.raises(WekoSwordserverException) as ex:
                check_result, file_format = check_import_items(sample_files)
                assert ex.value.errorType == ErrorType.ServerError
                assert ex.value.message == "Workflow is not configured for importing xml."


# def import_items_to_activity(item, data_path, request_info)
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py::test_import_items_to_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
# def test_import_items_to_activity(app, db,index,users,tokens,sword_mapping,sword_client,make_zip,make_crate,mocker,workflow,admin_settings):

#     check_result = {"data_path": "/tmp/weko_import_20250210103204704","list_record": [{"$schema": "/items/jsonschema/2","metadata": {"path": [1623632832836],"publish_status": "public","files_info": [{"key": "item_1617604990215","items": [{"filesize": [{"value": "333"}],"version": "1.0","fileDate": [{"fileDateValue": "2023-01-18","fileDateType": "Created"}],"filename": "sample.rst","url": {"url": "https://example.org/data/sample.rst","objectType": "fulltext","label": "data/sample.rst"},"format": "text/x-rst"}]}]},"publish_status": "public","file_path": ["sample.rst"]}]}
#     item = check_result.get("list_record")[0]
#     data_path = check_result.get("data_path","")
#     item["root_path"] = os.path.join(data_path, "data")
#     owner = 1
#     request_info = {
#         "user_id": owner,
#         "action": "IMPORT",
#         "workflow_id": str(workflow[0]["workflow"].id),
#     }

#     # normal case
#     url = "http://test_server.localdomain/workflow/activity/detail/A-TEST-00002"
#     current_action = "end_action"
#     recid = 200001
#     with patch("weko_workflow.headless.HeadlessActivity.auto", return_value=(url, current_action, recid)) as mock_auto:
#         url, recid, current_action = import_items_to_activity(item, data_path, request_info)
#         mock_auto.assert_called_once()
#         assert url == url
#         assert recid == recid
#         assert current_action == current_action

#     # except case
#     expect_current_action = "item_login"
#     mock_activity = MagicMock()
#     type(mock_activity).current_action = mocker.PropertyMock(return_value=expect_current_action)
#     mocker.patch("weko_swordserver.registration.HeadlessActivity", return_value=mock_activity)
#     with patch("weko_workflow.headless.HeadlessActivity.auto", side_effect=Exception()) as mock_auto:
#         with pytest.raises(WekoSwordserverException) as e:
#             import_items_to_activity(item, data_path, request_info)
#             mock_auto.assert_called_once()
#         assert e.value.errorType == ErrorType.ServerError
#         assert e.value.message == f"An error occurred while {expect_current_action}."

#     # xml case
#     settings1 = {"data_format":{"TSV":{"item_type":"15","register_format":"Direct"},"XML":{"workflow":"1","item_type":"15","register_format":"Workflow"}},"default_format":"TSV"}
#     settings2 = {"data_format":{"TSV":{"item_type":"15","register_format":"Direct"},"XML":{"workflow":"-1","item_type":"15","register_format":"Workflow"}},"default_format":"TSV"}
#     sword_api_setting = admin_settings[9]
#     sword_api_setting.settings = settings1
#     db.session.merge(sword_api_setting)
#     db.session.commit()
#     item = check_result.get("list_record")[0]
#     data_path = check_result.get("data_path","")
#     item["root_path"] = os.path.join(data_path, "data")
#     owner = 1
#     request_info = {
#         "user_id": owner,
#         "action": "IMPORT",
#         "workflow_id": None,
#     }
#     expect_current_action = "item_login"
#     mock_activity = MagicMock()
#     type(mock_activity).current_action = mocker.PropertyMock(return_value=expect_current_action)
#     mocker.patch("weko_swordserver.registration.HeadlessActivity", return_value=mock_activity)
#     with patch("weko_workflow.headless.HeadlessActivity.auto", side_effect=Exception()) as mock_auto:
#         with pytest.raises(WekoSwordserverException) as e:
#             import_items_to_activity(item, data_path, request_info)
#             mock_auto.assert_called_once()
#         assert e.value.errorType == ErrorType.ServerError
#         assert e.value.message == f"An error occurred while {expect_current_action}."
#     sword_api_setting = admin_settings[9]
#     sword_api_setting.settings = settings2
#     db.session.merge(sword_api_setting)
#     db.session.commit()


# def create_activity_from_jpcoar(check_result, data_path)
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py::test_create_activity_from_jpcoar -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
@pytest.mark.skip(reason="old test")
# def test_create_activity_from_jpcoar(app, users, admin_xml_settings):
#     contributor = users[3]["obj"]

#     mocker_pid = MagicMock(spec=PersistentIdentifier)
#     prop_mock = PropertyMock(return_value=uuid.uuid4())
#     type(mocker_pid).object_uuid = prop_mock
#     dummy_deposit = {"recid": '1'}
#     dummy_files = {
#         "key": "item_file",
#         "items": [
#             {
#                 "filename": "test1.txt",
#                 'subitem_1551255854908': '1.0',
#                 'subitem_1551255750794': 'text/plain',
#                 'subitem_1551255788530': [{'subitem_1570068579439': '18 KB'}],
#                 'subitem_1551255820788': [{'subitem_1551255828320': '2022-10-20', 'subitem_1551255833133': 'Accepted'}],
#                 'url': {
#                     'url': 'https://weko3.example.org/record/1/files/test1.txt',
#                     "objectType": "abstract",
#                     "label": "test1.txt"
#                 },
#             }
#         ]
#     }
#     expected_metadata = {
#         "item_title": [{"title": "sample", "lang": "en"}],
#         "item_creator": [{
#             "creatorNames": [{"creatorName": "sample, creator", "creatorNameLang": "en"}],
#         }],
#         "item_date": [{"keyword": "Issued", "date_val": "2015-10-01"}],
#         "item_lang": [{"lang": "eng"}],
#         "pubdate": "2024-03-06",
#         "title": "title_sample"
#     }

#     with app.test_request_context():
#         login_user(contributor)
#         with patch("weko_admin.admin.AdminSettings.get", return_value=admin_xml_settings):
#             # Case01: create activity without content files
#             activity, recid = create_activity_from_jpcoar({
#                 "error": [],
#                 "list_record": [{
#                     "metadata": {
#                         "$schema": 15,
#                         **expected_metadata
#                     }
#                 }]
#             }, "tests/data/zip_data/data")
#             assert json.loads(activity.temp_data) == {
#                 "metainfo": expected_metadata,
#             }
#             assert recid is None
#             db_activity = Activity.query.filter_by(id=activity.id).one_or_none()
#             assert db_activity is not None

#             # Case02: create activity with content files
#             with patch("weko_swordserver.registration.upload_jpcoar_contents", return_value=(mocker_pid, dummy_files, dummy_deposit)):
#                 activity, recid = create_activity_from_jpcoar({
#                     "error": [],
#                     "list_record": [{
#                         "metadata": {
#                             **expected_metadata,
#                             "files_info": [dummy_files]
#                         }
#                     }]
#                 }, "tests/data/zip_data/data")
#                 assert json.loads(activity.temp_data) == {
#                     "metainfo": expected_metadata,
#                     "files": dummy_files
#                 }
#                 assert recid == "1"
#                 db_activity = Activity.query.filter_by(id=activity.id).one_or_none()
#                 assert db_activity is not None

#             # Case03: exception occured when init activity
#             with patch("weko_swordserver.registration.upload_jpcoar_contents", return_value=(mocker_pid, dummy_files, dummy_deposit)):
#                 with patch("weko_workflow.api.WorkActivity.init_activity", side_effect=Exception()):
#                     with pytest.raises(Exception):
#                         activity, recid = create_activity_from_jpcoar({
#                             "error": [],
#                             "list_record": [{"metadata": expected_metadata}]
#                         }, "tests/data/zip_data/data")
#                         assert json.loads(activity.temp_data) == {
#                             "metainfo": expected_metadata,
#                             "files": dummy_files
#                         }
#                     db_activity_doing = Activity.query.filter(Activity.action_status=='M').all()
#                     db_activity_quit = Activity.query.filter(Activity.action_status=='C').all()
#                     assert len(db_activity_doing) == 2
#                     assert len(db_activity_quit) == 0

#             # Case04: exception occured after init activity
#             with patch("weko_swordserver.registration.upload_jpcoar_contents", return_value=(mocker_pid, dummy_files, dummy_deposit)):
#                 with patch("weko_workflow.api.WorkActivity.update_title", side_effect=Exception()):
#                     with pytest.raises(Exception):
#                         activity, recid = create_activity_from_jpcoar({
#                             "error": [],
#                             "list_record": [{"metadata": expected_metadata}]
#                         }, "tests/data/zip_data/data")
#                         assert json.loads(activity.temp_data) == {
#                             "metainfo": expected_metadata,
#                             "files": dummy_files
#                         }
#                     db_activity_doing = Activity.query.filter(Activity.action_status=='M').all()
#                     db_activity_quit = Activity.query.filter(Activity.action_status=='C').all()
#                     assert len(db_activity_doing) == 2
#                     assert len(db_activity_quit) == 1

#             # Case05: exception occured when quit activity
#             with patch("weko_swordserver.registration.upload_jpcoar_contents", return_value=(mocker_pid, dummy_files, dummy_deposit)):
#                 with patch("weko_workflow.api.WorkActivity.update_title", side_effect=Exception()):
#                     with patch("weko_workflow.api.WorkActivity.quit_activity", side_effect=Exception()):
#                         with pytest.raises(Exception):
#                             activity, recid = create_activity_from_jpcoar({
#                                 "error": [],
#                                 "list_record": [{"metadata": expected_metadata}]
#                             }, "tests/data/zip_data/data")
#                             assert json.loads(activity.temp_data) == {
#                                 "metainfo": expected_metadata,
#                                 "files": dummy_files
#                             }
#                         db_activity_doing = Activity.query.filter(Activity.action_status=='M').all()
#                         db_activity_quit = Activity.query.filter(Activity.action_status=='C').all()
#                         assert len(db_activity_doing) == 3
#                         assert len(db_activity_quit) == 1


# def upload_jpcoar_contents(data_path, contents_data)
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py::test_upload_jpcoar_contents -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
# def test_upload_jpcoar_contents(app, location, index, indexer):
#     def dummy_url_for( links, pid_value="", filename="", _external=False):
#         return "https://www.sample.ac.jp/" + pid_value + "/" + filename + "?_external=" + str(_external)

#     data_path="tests/data/zip_data2/data"
#     contents_data = [
#         {
#             "items": [
#                 {"url": {"url": "contents/sample_data.pdf"}},
#                 {"url": {"url": "contents/sample_txt.txt"}},
#                 {"url": {"url": "contents/weko_test_sample.jpg"}},
#             ]
#         }
#     ]
#     with app.test_request_context():
#         with patch("invenio_indexer.api.RecordIndexer.index", return_value=None):
#             with patch("weko_swordserver.registration.url_for", dummy_url_for):
#                 contents_data_copy = copy.deepcopy(contents_data)
#                 pid, activity_files_data, deposit = upload_jpcoar_contents(data_path, contents_data_copy)
#                 assert pid.pid_type == "depid"
#                 assert pid.id == 2
#                 assert len(activity_files_data) == 3
#                 assert deposit['recid'] == "1"
#                 assert deposit['_deposit'] == {"id": "1", "status": "draft", "owners": []}
#                 assert contents_data_copy == [
#                             {
#                                 "items": [
#                                     {"url": {"url": "https://www.sample.ac.jp/1/sample_data.pdf?_external=True"}},
#                                     {"url": {"url": "https://www.sample.ac.jp/1/sample_txt.txt?_external=True"}},
#                                     {"url": {"url": "https://www.sample.ac.jp/1/weko_test_sample.jpg?_external=True"}},
#                                 ]
#                             }
#                         ]

#             # Case02: missing url
#             with pytest.raises(FileNotFoundError):
#                 upload_jpcoar_contents(data_path, [{"items": [{"dummy": "dummy"}]}])

#             # Case03: path is directory
#             with pytest.raises(FileNotFoundError):
#                 upload_jpcoar_contents(data_path, [{"items": [{"url": {"url": "contents"}}]}])

#             # Case04: bucket size exceeded
#             with patch("os.path.getsize", return_value=100*1024*1024*1024*1024):
#                 with pytest.raises(FileSizeError):
#                     upload_jpcoar_contents(data_path, contents_data)

#             bucket = MagicMock(spec=Bucket)
#             location_mock = MagicMock(spec=Location)
#             location_mock.max_file_size = 4096
#             bucket.location = location_mock
#             bucket.size_limit = 2048
#             with patch("os.path.getsize", return_value=100*1024*1024*1024*1024):
#                 with patch("sqlalchemy.orm.Query.get", return_value=bucket):
#                     with pytest.raises(FileSizeError):
#                         upload_jpcoar_contents(data_path, contents_data)

#             # Case05: bucket quota exceeded
#             with patch("weko_swordserver.registration._location_has_quota", return_value=False):
#                 with pytest.raises(FileSizeError):
#                     upload_jpcoar_contents(data_path, contents_data)


# def create_file_info(bucket, file_path, size_limit, content_length)
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py::test_create_file_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
# def test_create_file_info(app, bucket, users, admin_xml_settings):
#     contributor = users[3]["obj"]
#     with app.test_request_context():
#         login_user(contributor)
#         with patch("weko_admin.admin.AdminSettings.get", return_value=admin_xml_settings):
#             actual = create_file_info(bucket, 'tests/data/zip_data/data/index.csv', 2000000, 36742)
#             objectversion = ObjectVersion.query.filter_by(key=actual['key']).one_or_none()
#             assert actual['key'] == "index.csv"
#             assert actual['uri'] == False
#             assert actual['multipart'] == False
#             assert actual['progress'] == 100
#             assert actual['completed'] == True
#             assert actual['version_id'] == str(objectversion.version_id)
#             assert actual['is_head'] == True
#             assert actual["checksum"] == "sha256:9ac67868b3a74fb749502288fe8c97b8e42b45fef519609f54c054cfdb22a780"
#             assert actual['delete_marker'] == False
#             assert actual['size'] == 36742
#             assert actual['tags'] == {}
#             assert actual['is_show'] == False
#             assert actual['is_thumbnail'] == False
#             assert actual['filename'] == "index.csv"
#             assert actual['created_user_id'] == str(contributor.id)
#             assert actual['created_user'] == {
#                 'user_id': str(contributor.id),
#                 'username': '',
#                 'displayname': '',
#                 'email': contributor.email
#             }
#             assert actual['updated_user_id'] == str(contributor.id)
#             assert actual['updated_user'] == {
#                 'user_id': str(contributor.id),
#                 'username': '',
#                 'displayname': '',
#                 'email': contributor.email
#             }
#             assert 'created' in actual
#             assert 'updated' in actual

# def check_bagit_import_items(file, packaging):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py::test_check_jsonld_import_items -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
@pytest.mark.skip(reason="old test")
def test_check_jsonld_import_items(app,db,index,users,tokens,sword_mapping,sword_client,make_crate,make_crate2,mocker,workflow):
    client_direct = tokens[0]["client"].client_id
    client_workflow = tokens[1]["client"].client_id

    packaging = "http://purl.org/net/sword/3.0/package/SimpleZip"

    # sucsess for direct. It is required to scope "deposit:write".
    zip, _ = make_crate()
    storage = FileStorage(filename="payload.zip",stream=zip)

    with app.test_request_context():     # for i18n get_current_locale().language
        result = check_jsonld_import_items(storage, packaging, client_id=client_direct)

    assert result.get("data_path").startswith("/var/tmp/weko_import_")
    assert result.get("register_type") == "Direct"
    assert result.get("item_type_id") == 2
    assert result.get("error") is None
    assert result.get("list_record")[0].get("errors") is None
    assert result.get("list_record")[0].get("metadata").id == "./"


    # sucsess for workflow. It is required to scope "deposit:write" and "user:activity"
    zip, _ = make_crate()
    storage = FileStorage(filename="payload.zip",stream=zip)

    with app.test_request_context():
        result = check_jsonld_import_items(storage, packaging, client_id=client_workflow)

    assert result.get("data_path").startswith("/var/tmp/weko_import_")
    assert result.get("register_type") == "Workflow"
    assert result.get("item_type_id") == 2
    assert result.get("error") is None
    assert result.get("list_record")[0].get("errors") is None


    # sucsess for split items.
    zip, _ = make_crate2()
    storage = FileStorage(filename="payload.zip",stream=zip)

    with app.test_request_context():
        result = check_jsonld_import_items(storage, packaging, client_id=client_direct)

    assert result.get("data_path").startswith("/var/tmp/weko_import_")
    assert result.get("register_type") == "Direct"
    assert result.get("item_type_id") == 2
    assert result.get("error") is None
    assert result.get("list_record")[0].get("errors") is None
    assert result.get("list_record")[0].get("metadata").id == "_:JournalPaper1"
    assert result.get("list_record")[1].get("errors") is None
    assert result.get("list_record")[1].get("metadata").id == "_:EvidenceData1"

#     # case # 01 : normal case(workflow)
#     client_id = tokens[0]["client"].client_id
#     user_email = users[2]["email"]
#     sword__mapping = sword_mapping[0]["sword_mapping"]
#     sword__client = sword_client[1]["sword_client"]

#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth

#         mapped_json = json_data("data/item_type/mapped_json_2.json")
#         with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):

#             zip, _ = make_crate()
#             file = FileStorage(filename=file_name, stream=zip)

#             with app.test_request_context(headers=headers):
#                 with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
#                     res = check_bagit_import_items(file, packaging[0])
#                     assert not hasattr(res, "error")
#                     assert res["list_record"][0]["errors"] is None

#         # not match indextree, metadata and setting
#         processed_json = json_data("data/item_type/processed_json_2.json")
#         processed_json.get("record").get("header").update({"indextree": 1234567891011})
#         mocker.patch("weko_swordserver.registration.process_json", return_value=processed_json)
#         mapped_json = json_data("data/item_type/mapped_json_2.json")
#         with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):

#             zip, _ = make_crate()
#             file = FileStorage(filename=file_name, stream=zip)

#             with app.test_request_context(headers=headers):
#                 with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
#                     res = check_bagit_import_items(file, packaging[0])
#                     assert not hasattr(res, "error")
#                     assert res["list_record"][0]["errors"] is None
#                     assert res["list_record"][0]["metadata"]["path"] == [1623632832836]

#     # case # 02 : other error(workflow)
#     client_id = tokens[0]["client"].client_id
#     user_email = users[2]["email"]
#     sword__mapping = sword_mapping[0]["sword_mapping"]
#     sword__client = sword_client[1]["sword_client"]

#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth

#         mapped_json = json_data("data/item_type/mapped_json_2.json")
#         with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):

#             zip, _ = make_crate()
#             file = FileStorage(filename=file_name, stream=zip)

#             with app.test_request_context(headers=headers):
#                 with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
#                     with patch("weko_swordserver.registration.handle_files_info", side_effect=Exception("Test error message.")) as mock_handle_files_info:
#                         res = check_bagit_import_items(file, packaging[0])
#                         assert res["error"] == "Test error message."
#                         mock_handle_files_info.assert_called_once()


#     # case # 03 : mapping error(workflow)
#     client_id = tokens[0]["client"].client_id
#     user_email = users[2]["email"]
#     sword__mapping = sword_mapping[0]["sword_mapping"]
#     sword__client = sword_client[1]["sword_client"]

#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth

#         mapped_json = json_data("data/item_type/mapped_json_2.json")
#         with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):

#             zip, _ = make_crate()
#             file = FileStorage(filename=file_name, stream=zip)

#             with app.test_request_context(headers=headers):
#                 with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
#                     def mock_handle(*args, **kwargs):
#                         list_record = args[0]
#                         list_record[0]["id"] = "１"
#                         modified_args = (list_record,) + args[1:]
#                         return handle_validate_item_import(*modified_args, **kwargs)
#                     with patch("weko_swordserver.registration.handle_validate_item_import", side_effect=mock_handle) as mock_handle_validate_item_import:
#                         res = check_bagit_import_items(file, packaging[0])
#                         errors = res["list_record"][0]["errors"]
#                         assert 'Please specify item ID by half-width number.' in errors
#                         assert 'Specified URI and system URI do not match.' in errors
#                         mock_handle_validate_item_import.assert_called_once()


#     # case # 04 : json.load error(workflow)
#     client_id = tokens[0]["client"].client_id
#     user_email = users[2]["email"]
#     sword__mapping = sword_mapping[0]["sword_mapping"]
#     sword__client = sword_client[1]["sword_client"]

#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth

#         zip, _ = make_crate()
#         file = FileStorage(filename=file_name, stream=zip)

#         with app.test_request_context(headers=headers):
#             with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
#                 with patch("weko_swordserver.registration.json.load", side_effect=UnicodeDecodeError("utf-8",b"test",0,1,"mock UnicodeDecodeError")) as mock_json_load:
#                     res = check_bagit_import_items(file, packaging[0])
#                     assert res["error"] == "mock UnicodeDecodeError"
#                     mock_json_load.assert_called_once()


#     # case # 05 : item type not found(workflow)
#     client_id = tokens[0]["client"].client_id
#     user_email = users[2]["email"]
#     sword__mapping = sword_mapping[0]["sword_mapping"]
#     sword__client = sword_client[1]["sword_client"]

#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth

#         zip, _ = make_crate()
#         file = FileStorage(filename=file_name, stream=zip)

#         with app.test_request_context(headers=headers):
#             with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
#                 with patch("weko_swordserver.registration.ItemTypes.get_by_id", return_value=None) as mock_get_by_id:
#                     res = check_bagit_import_items(file, packaging[0])
#                     assert res["error"] == "Item type not found for registration your item."
#                     mock_get_by_id.assert_called_once()


#     # case # 06 : item type and workflow do not match(workflow)
#     client_id = tokens[0]["client"].client_id
#     user_email = users[2]["email"]
#     sword__mapping = sword_mapping[0]["sword_mapping"]
#     sword__mapping.item_type_id = 1
#     sword__client = sword_client[1]["sword_client"]
#     workflow_ = workflow[0]["workflow"]
#     original_itemtype_id = workflow_.itemtype_id
#     workflow_.itemtype_id = 1
#     db.session.commit()

#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth

#         zip, _ = make_crate()
#         file = FileStorage(filename=file_name, stream=zip)

#         with app.test_request_context(headers=headers):
#             with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)) as mock_get_record_by_client_id:
#                 res = check_bagit_import_items(file, packaging[0])
#                 assert res["error"] == "Item type and workflow do not match."
#                 mock_get_record_by_client_id.assert_called_once()
#     workflow_.itemtype_id = original_itemtype_id
#     db.session.commit()


#     # case # 07 : workflow not found(workflow)
#     client_id = tokens[0]["client"].client_id
#     user_email = users[2]["email"]
#     sword__mapping = sword_mapping[0]["sword_mapping"]
#     sword__client = sword_client[1]["sword_client"]

#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth

#         zip, _ = make_crate()
#         file = FileStorage(filename=file_name, stream=zip)

#         with app.test_request_context(headers=headers):
#             with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
#                 with patch("weko_workflow.api.WorkFlow.get_workflow_by_id", return_value=None) as mock_get_workflow_by_id:
#                     res = check_bagit_import_items(file, packaging[0])
#                     assert res["error"] == "Workflow not found for registration your item."
#                     mock_get_workflow_by_id.assert_called_once()


#     # case # 08 : normal case(direct)
#     client_id = tokens[0]["client"].client_id
#     user_email = users[2]["email"]
#     sword__mapping = sword_mapping[0]["sword_mapping"]
#     sword__client = sword_client[0]["sword_client"]

#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth

#         mapped_json = json_data("data/item_type/mapped_json_2.json")
#         with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):

#             zip, _ = make_crate()
#             file = FileStorage(filename=file_name, stream=zip)

#             with app.test_request_context(headers=headers):
#                 res = check_bagit_import_items(file, packaging[0])
#                 assert not hasattr(res, "error")
#                 assert res["list_record"][0]["errors"] is None


#     # case # 08-1 : normal case(direct)
#     client_id = tokens[2]["client"].client_id
#     user_email = users[2]["email"]
#     sword__mapping = sword_mapping[0]["sword_mapping"]
#     sword__client = sword_client[0]["sword_client"]

#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[2]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[2]["scope"].split(" ")
#         mock_request.oauth = mock_oauth
#         mock_request.headers = headers

#         mapped_json = json_data("data/item_type/mapped_json_2.json")
#         with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):

#             zip, _ = make_crate()
#             file = FileStorage(filename=file_name, stream=zip)

#             with app.test_request_context(headers=headers):
#                 res = check_bagit_import_items(file, packaging[0])
#                 assert res["error"].startswith("403 Forbidden:")


#     # case # 08-2 : normal case(direct)
#     client_id = tokens[0]["client"].client_id
#     user_email = users[2]["email"]
#     sword__mapping = sword_mapping[0]["sword_mapping"]
#     sword__client = sword_client[0]["sword_client"]

#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth
#         mock_request.headers = headers

#         mapped_json = json_data("data/item_type/mapped_json_2.json")
#         with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):

#             zip, _ = make_crate()
#             file = FileStorage(filename=file_name, stream=zip)

#             with app.test_request_context(headers=headers):
#                 with patch.dict("flask.current_app.config", {"WEKO_SWORDSERVER_DEPOSIT_DATASET": True}):
#                     res = check_bagit_import_items(file, packaging[0])
#                     assert not hasattr(res, "error")
#                     assert res["list_record"][0]["errors"] is None


#     # case # 08-3 : normal case(direct)
#     # isinstance
#     file__name = "payload.zip"
#     zip, _ = make_crate()
#     storage = FileStorage(filename=file__name,stream=zip)
#     data__path, files__list = unpack_zip(storage)

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth
#         mock_request.headers = headers

#         mapped__json = json_data("data/item_type/mapped_json_2.json")
#         with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped__json):
#             with app.test_request_context(headers=headers):
#                 with patch.dict("flask.current_app.config", {"WEKO_SWORDSERVER_DEPOSIT_DATASET": True}):
#                     with patch("weko_swordserver.registration.unpack_zip") as mock_unpack_zip:
#                         mock_unpack_zip.return_value = data__path, files__list
#                         with patch("shutil.copy", side_effect=Exception({"error_msg":"test_error"})):
#                             res = check_bagit_import_items(f"{data__path}/{file_name}", packaging[0])
#                             assert res["error"] == "test_error"


#     # case # 09 : other error(direct)
#     client_id = tokens[0]["client"].client_id
#     user_email = users[2]["email"]
#     sword__mapping = sword_mapping[0]["sword_mapping"]
#     sword__client = sword_client[0]["sword_client"]

#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth

#         mapped_json = json_data("data/item_type/mapped_json_2.json")
#         with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):

#             zip, _ = make_crate()
#             file = FileStorage(filename=file_name, stream=zip)

#             with app.test_request_context(headers=headers):
#                 with patch("weko_swordserver.registration.handle_files_info", side_effect=Exception("Test error message.")) as mock_handle_files_info:
#                     res = check_bagit_import_items(file, packaging[0])
#                     assert res["error"] == "Test error message."
#                     mock_handle_files_info.assert_called_once()


#     # case # 10 : mapping error(direct)
#     client_id = tokens[0]["client"].client_id
#     user_email = users[2]["email"]
#     sword__mapping = sword_mapping[0]["sword_mapping"]
#     sword__client = sword_client[0]["sword_client"]

#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth

#         mapped_json = json_data("data/item_type/mapped_json_2.json")
#         with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):

#             zip, _ = make_crate()
#             file = FileStorage(filename=file_name, stream=zip)

#             with app.test_request_context(headers=headers):
#                 def mock_handle(*args, **kwargs):
#                     list_record = args[0]
#                     list_record[0]["id"] = "１"
#                     modified_args = (list_record,) + args[1:]
#                     return handle_validate_item_import(*modified_args, **kwargs)
#                 with patch("weko_swordserver.registration.handle_validate_item_import", side_effect=mock_handle) as mock_handle_validate_item_import:
#                     res = check_bagit_import_items(file, packaging[0])
#                     errors = res["list_record"][0]["errors"]
#                     assert 'Please specify item ID by half-width number.' in errors
#                     assert 'Specified URI and system URI do not match.' in errors
#                     mock_handle_validate_item_import.assert_called_once()


#     # case # 11 : json.load error(direct)
#     client_id = tokens[0]["client"].client_id
#     user_email = users[2]["email"]
#     sword__mapping = sword_mapping[0]["sword_mapping"]
#     sword__client = sword_client[0]["sword_client"]

#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth

#         zip, _ = make_crate()
#         file = FileStorage(filename=file_name, stream=zip)

#         with app.test_request_context(headers=headers):
#             with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
#                 with patch("weko_swordserver.registration.json.load", side_effect=UnicodeDecodeError) as mock_json_load:
#                     res = check_bagit_import_items(file, packaging[0])
#                     assert res["error"] == "function takes exactly 5 arguments (0 given)"
#                     mock_json_load.assert_called_once()


#     # case # 12 : item type not found(direct)
#     client_id = tokens[0]["client"].client_id
#     user_email = users[2]["email"]
#     sword__mapping = sword_mapping[0]["sword_mapping"]
#     sword__client = sword_client[0]["sword_client"]

#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth

#         zip, _ = make_crate()
#         file = FileStorage(filename=file_name, stream=zip)

#         with app.test_request_context(headers=headers):
#             with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
#                 with patch("weko_swordserver.registration.ItemTypes.get_by_id", return_value=None) as mock_get_by_id:
#                     res = check_bagit_import_items(file, packaging[0])
#                     assert res["error"] == "Item type not found for registration your item."
#                     mock_get_by_id.assert_called_once()


#     # case # 13 : no mapping
#     client_id = tokens[0]["client"].client_id
#     user_email = users[2]["email"]

#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }

#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth

#         zip, _ = make_crate()
#         file = FileStorage(filename=file_name, stream=zip)

#         with app.test_request_context(headers=headers):
#             with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword_client, None)) as mock_get_record_by_client_id:
#                 res = check_bagit_import_items(file, packaging[0])
#                 assert res["error"] == "Metadata mapping not defined for registration your item."
#                 mock_get_record_by_client_id.assert_called_once()

#     # case # 14 : bagit error
#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     data_path = "test_data_path"
#     zip, _ = make_crate()
#     file = FileStorage(filename=file_name, stream=zip)
#     user_email = users[0]["email"]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }
#     with app.test_request_context(headers=headers):
#         with patch("weko_swordserver.registration.unpack_zip") as mock_unpack_zip:
#             mock_unpack_zip.return_value = data_path, []
#             with patch("bagit.Bag", side_effect=bagit.BagValidationError("mock bagit.BagValidationError")) as mock_bag:
#                 res = check_bagit_import_items(file, packaging[0])
#                 assert res["error"] == "mock bagit.BagValidationError"
#                 mock_bag.assert_called_once()


#     # case # 15 : BadZipFile
#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     zip, _ = make_crate()
#     file = f"test_file/{file_name}"
#     user_email = users[0]["email"]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }
#     with app.test_request_context(headers=headers):
#         with patch("weko_swordserver.registration.unpack_zip", side_effect=BadZipFile) as mock_unpack_zip:
#             res = check_bagit_import_items(file, packaging[0])
#             assert res == {
#                 "error": f"The format of the specified file {file_name} dose not "
#                 + "support import. Please specify a zip file."
#             }
#             mock_unpack_zip.assert_called_once()


#     # case # 16 : other error
#     # Mock User.query.filter_by
#     file_name = "mockfile.zip"
#     packaging = [
#         "http://purl.org/net/sword/3.0/package/SimpleZip",
#         "http://purl.org/net/sword/3.0/package/SWORDBagIt",
#     ]
#     zip, _ = make_crate()
#     file = FileStorage(filename=file_name, stream=zip)
#     user_email = users[0]["email"]
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": user_email,
#     }
#     with app.test_request_context(headers=headers):
#         with patch("weko_swordserver.registration.User.query", new_callable=MagicMock) as mock_user_query:
#             mock_filter_by = MagicMock()
#             mock_filter_by.one_or_none.side_effect = SQLAlchemyError
#             mock_user_query.filter_by.return_value = mock_filter_by
#             with pytest.raises(WekoSwordserverException) as e:
#                 check_bagit_import_items(file, packaging[0])
#                 mock_user_query.filter_by.assert_called_once_with(email=user_email)
#             assert e.value.errorType == ErrorType.ServerError
#             assert e.value.message == "An error occurred while searching user by On-Behalf-Of."

#     # Mock Token.query.filter_by
#     access_token = tokens[0]["token"].access_token
#     headers["On-Behalf-Of"] = access_token
#     with app.test_request_context(headers=headers):
#         with patch("weko_swordserver.registration.Token.query", new_callable=MagicMock) as mock_token_query:
#             mock_filter_by = MagicMock()
#             mock_filter_by.one_or_none.side_effect = SQLAlchemyError
#             mock_token_query.filter_by.return_value = mock_filter_by
#             with pytest.raises(WekoSwordserverException) as e:
#                 check_bagit_import_items(file, packaging[0])
#                 mock_token_query.filter_by.assert_called_once_with(access_token=access_token)
#             assert e.value.errorType == ErrorType.ServerError
#             assert e.value.message == "An error occurred while searching user by On-Behalf-Of."

#     # Mock ShibbolethUser.query.filter_by
#     shib_eppn = "test_shib_eppn"
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": shib_eppn,
#     }
#     with app.test_request_context(headers=headers):
#         with patch("weko_swordserver.registration.ShibbolethUser.query", new_callable=MagicMock) as mock_shib_query:
#             mock_filter_by = MagicMock()
#             mock_filter_by.one_or_none.side_effect = SQLAlchemyError
#             mock_shib_query.filter_by.return_value = mock_filter_by
#             with pytest.raises(WekoSwordserverException) as e:
#                 check_bagit_import_items(file, packaging[0])
#                 mock_shib_query.filter_by.assert_called_once_with(shib_eppn=shib_eppn)
#             assert e.value.errorType == ErrorType.ServerError
#             assert e.value.message == "An error occurred while searching user by On-Behalf-Of."

#     # Mock no query.filter_by
#     shib_eppn = "test_shib_eppn"
#     headers = {
#         "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
#         "Content-Disposition": f"attachment;filename={file_name}",
#         "Packaging": packaging[0],
#         "On-Behalf-Of": shib_eppn,
#     }
#     with patch("weko_swordserver.registration.request") as mock_request:
#         mock_oauth = MagicMock()
#         mock_oauth.client.client_id = client_id
#         mock_oauth.access_token.scopes = tokens[0]["scope"].split(" ")
#         mock_request.oauth = mock_oauth
#         mock_request.headers = headers
#         mapped_json = json_data("data/item_type/mapped_json_2.json")
#         with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
#             with app.test_request_context(headers=headers):
#                 res = check_bagit_import_items(file, packaging[0])
#                 assert not hasattr(res, "error")
#                 assert res["list_record"][0]["errors"] is None
