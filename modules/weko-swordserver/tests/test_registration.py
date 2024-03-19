import copy
import uuid
import pytest
from flask import json
from flask_login.utils import login_user
from mock import patch, MagicMock
from unittest.mock import PropertyMock

from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_pidstore.models import PersistentIdentifier
from weko_swordserver.errors import ErrorType, WekoSwordserverException
from weko_swordserver.registration import check_import_items, create_activity_from_jpcoar, create_file_info, upload_jpcoar_contents
from weko_workflow.models import Activity, WorkFlow


@pytest.fixture()
def admin_tsv_settings(workflow):
    return {
        "default_format": "TSV",
        "data_format": {
            "TSV": {
                "register_format": "Direct"
            },
            "XML": {
                "workflow": str(workflow.id),
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
                "workflow": str(workflow.id),
                "register_format": "Workflow"
            }
        }
    }


# def check_import_items(file, is_change_identifier: bool = False)
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py::test_check_import_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_check_import_items(app, admin_tsv_settings, admin_xml_settings):
    check_tsv_result = {"error": [], "list_record": [{"sample": "Tsv metadata here."}]}
    check_xml_result = {"error": [], "list_record": [{"sample": "Xml metadata here."}]}
    check_tsv_error_result = {"error": ["something tsv error happend"]}
    check_xml_error_result = {"error": ["something xml error happend"]}
    sample_files = "This is sample files data."
    # Case01:  default_format = TSV and import tsv
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_tsv_settings):
        with patch("weko_swordserver.registration.check_tsv_import_items", return_value=check_tsv_result):
            check_result, register_format = check_import_items(sample_files)
            assert check_result == check_tsv_result
            assert register_format == "Direct"

    # Case02: default_format = TSV but try import xml
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_tsv_settings):
        with patch("weko_swordserver.registration.check_tsv_import_items", return_value=check_tsv_error_result):
            with patch("weko_swordserver.registration.check_xml_import_items", return_value=check_xml_result):
                check_result, register_format = check_import_items(sample_files)
                assert check_result == check_xml_result
                assert register_format == "Workflow"

    # Case03: default_format = TSV and import error
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_tsv_settings):
        with patch("weko_swordserver.registration.check_tsv_import_items", return_value=check_tsv_error_result):
            with patch("weko_swordserver.registration.check_xml_import_items", return_value=check_xml_error_result):
                check_result, register_format = check_import_items(sample_files)
                assert check_result == check_tsv_error_result
                assert register_format is None

    # Case04:  default_format = XML and import xml
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_xml_settings):
        with patch("weko_swordserver.registration.check_xml_import_items", return_value=check_xml_result):
            check_result, register_format = check_import_items(sample_files)
            assert check_result == check_xml_result
            assert register_format == "Workflow"

    # Case05: default_format = XML but try import tsv
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_xml_settings):
        with patch("weko_swordserver.registration.check_xml_import_items", return_value=check_xml_error_result):
            with patch("weko_swordserver.registration.check_tsv_import_items", return_value=check_tsv_result):
                check_result, register_format = check_import_items(sample_files)
                assert check_result == check_tsv_result
                assert register_format == "Direct"

    # Case06: default_format = XML and import error
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_xml_settings):
        with patch("weko_swordserver.registration.check_xml_import_items", return_value=check_xml_error_result):
            with patch("weko_swordserver.registration.check_tsv_import_items", return_value=check_tsv_error_result):
                check_result, register_format = check_import_items(sample_files)
                assert check_result == check_xml_error_result
                assert register_format is None

    # Case07: default_format = <unknown>
    admin_unknown_settings = {"default_format": "anonymous"}
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_unknown_settings):
        check_result, register_format = check_import_items(sample_files)
        assert check_result == {}
        assert register_format is None

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
                check_result, register_format = check_import_items(sample_files)
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
            check_result, register_format = check_import_items(sample_files)
            assert ex.errorType == ErrorType.ServerError
            assert ex.message == "Workflow is not configured for importing xml."

    # Case09: workflow has been deleted (TSV)
    workflow = MagicMock(spec=WorkFlow)
    workflow.is_deleted = True
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_tsv_settings):
        with patch("weko_swordserver.registration.check_tsv_import_items", return_value=check_tsv_error_result):
            with patch("sqlalchemy.orm.Query.get", return_value=workflow):
                with pytest.raises(WekoSwordserverException) as ex:
                    check_result, register_format = check_import_items(sample_files)
                    assert ex.value.errorType == ErrorType.ServerError
                    assert ex.value.message == "Workflow is not configured for importing xml."

    # Case10: workflow has been deleted (XML)
    with patch("weko_admin.admin.AdminSettings.get", return_value=admin_xml_settings):
        with patch("sqlalchemy.orm.Query.get", return_value=workflow):
            with pytest.raises(WekoSwordserverException) as ex:
                check_result, register_format = check_import_items(sample_files)
                assert ex.value.errorType == ErrorType.ServerError
                assert ex.value.message == "Workflow is not configured for importing xml."


# def create_activity_from_jpcoar(check_result, data_path)
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py::test_create_activity_from_jpcoar -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_create_activity_from_jpcoar(app, users, admin_xml_settings):
    contributor = users[3]["obj"]

    mocker_pid = MagicMock(spec=PersistentIdentifier)
    prop_mock = PropertyMock(return_value=uuid.uuid4())
    type(mocker_pid).object_uuid = prop_mock
    dummy_deposit = {"recid": '1'}
    dummy_files = {
        "key": "item_file",
        "items": [
            {
                "filename": "test1.txt",
                'subitem_1551255854908': '1.0',
                'subitem_1551255750794': 'text/plain',
                'subitem_1551255788530': [{'subitem_1570068579439': '18 KB'}],
                'subitem_1551255820788': [{'subitem_1551255828320': '2022-10-20', 'subitem_1551255833133': 'Accepted'}],
                'url': {
                    'url': 'https://weko3.example.org/record/1/files/test1.txt',
                    "objectType": "abstract",
                    "label": "test1.txt"
                },
            }
        ]
    }
    expected_metadata = {
        "item_title": [{"title": "sample", "lang": "en"}],
        "item_creator": [{
            "creatorNames": [{"creatorName": "sample, creator", "creatorNameLang": "en"}],
        }],
        "item_date": [{"keyword": "Issued", "date_val": "2015-10-01"}],
        "item_lang": [{"lang": "eng"}],
        "pubdate": "2024-03-06",
        "title": "title_sample"
    }

    with app.test_request_context():
        login_user(contributor)
        with patch("weko_admin.admin.AdminSettings.get", return_value=admin_xml_settings):
            # Case01: create activity without content files
            activity, recid = create_activity_from_jpcoar({
                "error": [],
                "list_record": [{
                    "metadata": {
                        "$schema": 15,
                        **expected_metadata
                    }
                }]
            }, "tests/data/zip_data/data")
            assert json.loads(activity.temp_data) == {
                "metainfo": expected_metadata,
            }
            assert recid is None
            db_activity = Activity.query.filter_by(id=activity.id).one_or_none()
            assert db_activity is not None

            # Case02: create activity with content files
            with patch("weko_swordserver.registration.upload_jpcoar_contents", return_value=(mocker_pid, dummy_files, dummy_deposit)):
                activity, recid = create_activity_from_jpcoar({
                    "error": [],
                    "list_record": [{
                        "metadata": {
                            **expected_metadata,
                            "files_info": [dummy_files]
                        }
                    }]
                }, "tests/data/zip_data/data")
                assert json.loads(activity.temp_data) == {
                    "metainfo": expected_metadata,
                    "files": dummy_files
                }
                assert recid == "1"
                db_activity = Activity.query.filter_by(id=activity.id).one_or_none()
                assert db_activity is not None

            # Case03: exception occured when init activity
            with patch("weko_swordserver.registration.upload_jpcoar_contents", return_value=(mocker_pid, dummy_files, dummy_deposit)):
                with patch("weko_workflow.api.WorkActivity.init_activity", side_effect=Exception()):
                    with pytest.raises(Exception):
                        activity, recid = create_activity_from_jpcoar({
                            "error": [],
                            "list_record": [{"metadata": expected_metadata}]
                        }, "tests/data/zip_data/data")
                        assert json.loads(activity.temp_data) == {
                            "metainfo": expected_metadata,
                            "files": dummy_files
                        }
                    db_activity_doing = Activity.query.filter(Activity.action_status=='M').all()
                    db_activity_quit = Activity.query.filter(Activity.action_status=='C').all()
                    assert len(db_activity_doing) == 2
                    assert len(db_activity_quit) == 0

            # Case04: exception occured after init activity
            with patch("weko_swordserver.registration.upload_jpcoar_contents", return_value=(mocker_pid, dummy_files, dummy_deposit)):
                with patch("weko_workflow.api.WorkActivity.update_title", side_effect=Exception()):
                    with pytest.raises(Exception):
                        activity, recid = create_activity_from_jpcoar({
                            "error": [],
                            "list_record": [{"metadata": expected_metadata}]
                        }, "tests/data/zip_data/data")
                        assert json.loads(activity.temp_data) == {
                            "metainfo": expected_metadata,
                            "files": dummy_files
                        }
                    db_activity_doing = Activity.query.filter(Activity.action_status=='M').all()
                    db_activity_quit = Activity.query.filter(Activity.action_status=='C').all()
                    assert len(db_activity_doing) == 2
                    assert len(db_activity_quit) == 1


# def upload_jpcoar_contents(data_path, contents_data)
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py::test_upload_jpcoar_contents -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_upload_jpcoar_contents(app, location, index, indexer):
    def dummy_url_for( links, pid_value="", filename="", _external=False):
        return "https://www.sample.ac.jp/" + pid_value + "/" + filename + "?_external=" + str(_external)

    data_path="tests/data/zip_data2/data"
    contents_data = [
        {
            "items": [
                {"url": {"url": "contents/sample_data.pdf"}},
                {"url": {"url": "contents/sample_txt.txt"}},
                {"url": {"url": "contents/weko_test_sample.jpg"}},
            ]
        }
    ]
    with app.test_request_context():
        with patch("invenio_indexer.api.RecordIndexer.index", return_value=None):
            with patch("weko_swordserver.registration.url_for", dummy_url_for):
                contents_data_copy = copy.deepcopy(contents_data)
                pid, activity_files_data, deposit = upload_jpcoar_contents(data_path, contents_data_copy)
                print(pid)
                print(activity_files_data)
                print(deposit)
                assert pid.pid_type == "depid"
                assert pid.id == 2
                assert len(activity_files_data) == 3
                assert deposit['recid'] == "1"
                assert deposit['_deposit'] == {"id": "1", "status": "draft", "owners": []}
                assert contents_data_copy == [
                            {
                                "items": [
                                    {"url": {"url": "https://www.sample.ac.jp/1/sample_data.pdf?_external=True"}},
                                    {"url": {"url": "https://www.sample.ac.jp/1/sample_txt.txt?_external=True"}},
                                    {"url": {"url": "https://www.sample.ac.jp/1/weko_test_sample.jpg?_external=True"}},
                                ]
                            }
                        ]

            # Case02: missing url
            with pytest.raises(FileNotFoundError):
                upload_jpcoar_contents(data_path, [{"items": [{"dummy": "dummy"}]}])

            # Case03: path is directory
            with pytest.raises(FileNotFoundError):
                upload_jpcoar_contents(data_path, [{"items": [{"url": {"url": "contents"}}]}])

            # Case04: bucket size exceeded
            with patch("os.path.getsize", return_value=100*1024*1024*1024*1024):
                with pytest.raises(FileSizeError):
                    upload_jpcoar_contents(data_path, contents_data)

            bucket = MagicMock(spec=Bucket)
            location_mock = MagicMock(spec=Location)
            location_mock.max_file_size = 4096
            bucket.location = location_mock
            bucket.size_limit = 2048
            with patch("os.path.getsize", return_value=100*1024*1024*1024*1024):
                with patch("sqlalchemy.orm.Query.get", return_value=bucket):
                    with pytest.raises(FileSizeError):
                        upload_jpcoar_contents(data_path, contents_data)

            # Case05: bucket quota exceeded
            with patch("weko_swordserver.registration._location_has_quota", return_value=False):
                with pytest.raises(FileSizeError):
                    upload_jpcoar_contents(data_path, contents_data)


# def create_file_info(bucket, file_path, size_limit, content_length)
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py::test_create_file_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_create_file_info(app, bucket, users, admin_xml_settings):
    contributor = users[3]["obj"]
    with app.test_request_context():
        login_user(contributor)
        with patch("weko_admin.admin.AdminSettings.get", return_value=admin_xml_settings):
            actual = create_file_info(bucket, 'tests/data/zip_data/data/index.csv', 2000000, 36742)
            objectversion = ObjectVersion.query.filter_by(key=actual['key']).one_or_none()
            assert actual['key'] == "index.csv"
            assert actual['uri'] == False
            assert actual['multipart'] == False
            assert actual['progress'] == 100
            assert actual['completed'] == True
            assert actual['version_id'] == str(objectversion.version_id)
            assert actual['is_head'] == True
            assert actual["checksum"] == "sha256:9ac67868b3a74fb749502288fe8c97b8e42b45fef519609f54c054cfdb22a780"
            assert actual['delete_marker'] == False
            assert actual['size'] == 36742
            assert actual['tags'] == {}
            assert actual['is_show'] == False
            assert actual['is_thumbnail'] == False
            assert actual['filename'] == "index.csv"
            assert actual['created_user_id'] == str(contributor.id)
            assert actual['created_user'] == {
                'user_id': str(contributor.id),
                'username': '',
                'displayname': '',
                'email': contributor.email
            }
            assert actual['updated_user_id'] == str(contributor.id)
            assert actual['updated_user'] == {
                'user_id': str(contributor.id),
                'username': '',
                'displayname': '',
                'email': contributor.email
            }
            assert 'created' in actual
            assert 'updated' in actual