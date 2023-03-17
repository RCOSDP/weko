import io
from datetime import datetime, timedelta, timezone
from unittest import mock  # python3
from unittest.mock import MagicMock

import mock  # python2, after pip install mock
import pytest
from flask import Flask, json, jsonify, session, url_for
from flask_babelex import get_locale, to_user_timezone, to_utc
from flask_login import current_user
from flask_security import login_user
from flask_security.utils import login_user
from invenio_accounts.models import Role, User
from invenio_accounts.testutils import create_test_user, login_user_via_session
from mock import patch

from weko_records_ui.permissions import (
    check_created_id,
    check_publish_status,
    get_permission,
    check_open_restricted_permission,
    check_file_download_permission,
    check_content_clickable,
    check_create_usage_report,
    __get_file_permission,
    check_original_pdf_download_permission,
    file_permission_factory,
    page_permission_factory,
    is_open_restricted
)


# def page_permission_factory(record, *args, **kwargs):
#    def can(self):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_get_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_page_permission_factory(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    assert page_permission_factory(record)

# def file_permission_factory(record, *args, **kwargs):
#    def can(self):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_get_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_file_permission_factory(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    assert file_permission_factory(record)

# def check_file_download_permission(record, fjson, is_display_file_info=False):
#    def site_license_check():
#    def get_email_list_by_ids(user_id_list):
#    def __check_user_permission(user_id_list):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_check_file_download_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_file_download_permission(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    fjson = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': 'image/jpeg', 'filename': 'helloworld.pdf', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': 2700000.0, 'mimetype': 'image/jpeg', 'file_order': 0}
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert check_file_download_permission(record, fjson,True) == True
    
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert check_file_download_permission(record, fjson,False) == True

# def check_open_restricted_permission(record, fjson):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_check_open_restricted_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_open_restricted_permission(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    fjson = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': 'image/jpeg', 'filename': 'helloworld.pdf', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': 2700000.0, 'mimetype': 'image/jpeg', 'file_order': 0}
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert check_open_restricted_permission(record, fjson) == False

# def is_open_restricted(file_data):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_get_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_is_open_restricted(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    fjson = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': 'image/jpeg', 'filename': 'helloworld.pdf', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': 2700000.0, 'mimetype': 'image/jpeg', 'file_order': 0}
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert is_open_restricted(fjson) == False

# def check_content_clickable(record, fjson):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_check_content_clickable -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_content_clickable(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    fjson = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': 'image/jpeg', 'filename': 'helloworld.pdf', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': 2700000.0, 'mimetype': 'image/jpeg', 'file_order': 0}
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert check_content_clickable(record, fjson) == False

# def check_permission_period(permission):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_get_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def get_permission(record, fjson):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_get_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_permission(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    fjson = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': 'image/jpeg', 'filename': 'helloworld.pdf', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': 2700000.0, 'mimetype': 'image/jpeg', 'file_order': 0}
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert get_permission(record, fjson) == None


# def check_original_pdf_download_permission(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_check_original_pdf_download_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_original_pdf_download_permission(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            assert check_original_pdf_download_permission(record) == None


# def check_user_group_permission(group_id):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_get_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def check_publish_status(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_get_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_publish_status(app):
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        record = {
            "_oai": {"id": "oai:weko3.example.org:00000001", "sets": ["1658073625012"]},
            "path": ["1658073625012"],
            "owner": "1",
            "recid": "1",
            "title": ["2022-07-18"],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2022-07-18"},
            "_buckets": {"deposit": "e37da0e1-710d-413f-8af8-630e224131bb"},
            "_deposit": {
                "id": "1",
                "pid": {"type": "depid", "value": "1", "revision_id": 0},
                "owner": "1",
                "owners": [1],
                "status": "published",
                "created_by": 1,
                "owners_ext": {
                    "email": "wekosoftware@nii.ac.jp",
                    "username": "",
                    "displayname": "",
                },
            },
            "item_title": "2022-07-18",
            "author_link": [],
            "item_type_id": "15",
            "publish_date": "2022-07-18",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "2022-07-18",
                        "subitem_1551255648112": "ja",
                    }
                ],
            },
            "item_1617258105262": {
                "attribute_name": "Resource Type",
                "attribute_value_mlt": [
                    {
                        "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                        "resourcetype": "conference paper",
                    }
                ],
            },
            "relation_version_is_last": True,
        }
        app.config["BABEL_DEFAULT_TIMEZONE"] = "Asia/Tokyo"
        # offset-naive
        now = datetime.utcnow()
        record["publish_status"] = "0"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "0"
        assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
            "%Y-%m-%d"
        )
        assert check_publish_status(record) == True
        record["publish_status"] = "-1"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "-1"
        assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
            "%Y-%m-%d"
        )
        assert check_publish_status(record) == False

        JST = timezone(timedelta(hours=+9), "JST")
        # aware
        now = datetime.now(JST)
        record["publish_status"] = "0"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "0"
        assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
            "%Y-%m-%d"
        )
        assert check_publish_status(record) == True
        record["publish_status"] = "-1"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "-1"
        assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
            "%Y-%m-%d"
        )
        assert check_publish_status(record) == False

        now = datetime.now(JST) + timedelta(days=1)
        record["publish_status"] = "0"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "0"
        assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
            "%Y-%m-%d"
        )
        assert check_publish_status(record) == False
        record["publish_status"] = "-1"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "-1"
        assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
            "%Y-%m-%d"
        )
        assert check_publish_status(record) == False

        now = datetime.now(JST) + timedelta(days=10)
        record["publish_status"] = "0"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "0"
        assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
            "%Y-%m-%d"
        )
        assert check_publish_status(record) == False
        record["publish_status"] = "-1"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "-1"
        assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
            "%Y-%m-%d"
        )
        assert check_publish_status(record) == False

        now = datetime.now(JST) - timedelta(days=1)
        record["publish_status"] = "0"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "0"
        assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
            "%Y-%m-%d"
        )
        assert check_publish_status(record) == True
        record["publish_status"] = "-1"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "-1"
        assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
            "%Y-%m-%d"
        )
        assert check_publish_status(record) == False

        now = datetime.now(JST) - timedelta(days=10)
        record["publish_status"] = "0"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "0"
        assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
            "%Y-%m-%d"
        )
        assert check_publish_status(record) == True
        record["publish_status"] = "-1"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "-1"
        assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
            "%Y-%m-%d"
        )
        assert check_publish_status(record) == False


# def check_created_id(record):


def test_check_created_id(app, users):
    datastore = app.extensions["invenio-accounts"].datastore
    login_manager = app.login_manager

    @login_manager.user_loader
    def load_user(user_id):
        user = datastore.find_user(id=user_id)
        return user

    @app.route("/foo_login/<username>")
    def login(username):
        user = datastore.find_user(email=username)
        login_user(user)
        return "Logged In"

    record = {
        "_oai": {"id": "oai:weko3.example.org:00000001", "sets": ["1657555088462"]},
        "path": ["1657555088462"],
        "owner": "1",
        "recid": "1",
        "title": ["a"],
        "pubdate": {"attribute_name": "PubDate", "attribute_value": "2022-07-12"},
        "_buckets": {"deposit": "35004d51-8938-4e77-87d7-0c9e176b8e7b"},
        "_deposit": {
            "id": "1",
            "pid": {"type": "depid", "value": "1", "revision_id": 0},
            "owner": "1",
            "owners": [1],
            "status": "published",
            "created_by": 1,
            "owners_ext": {
                "email": "wekosoftware@nii.ac.jp",
                "username": "",
                "displayname": "",
            },
        },
        "item_title": "a",
        "author_link": [],
        "item_type_id": "15",
        "publish_date": "2022-07-12",
        "publish_status": "0",
        "weko_shared_id": -1,
        "item_1617186331708": {
            "attribute_name": "Title",
            "attribute_value_mlt": [
                {"subitem_1551255647225": "a", "subitem_1551255648112": "ja"}
            ],
        },
        "item_1617258105262": {
            "attribute_name": "Resource Type",
            "attribute_value_mlt": [
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                    "resourcetype": "conference paper",
                }
            ],
        },
        "relation_version_is_last": True,
    }
    assert record.get("_deposit", {}).get("created_by") == 1
    assert record.get("item_type_id") == "15"
    assert record.get("weko_shared_id") == -1

    supers = app.config["WEKO_PERMISSION_SUPER_ROLE_USER"]
    user_roles = app.config["WEKO_PERMISSION_ROLE_USER"]

    with app.test_request_context(headers=[("Accept-Language", "en")]):
        with app.test_client() as client:
            # guest user
            assert current_user.is_authenticated == False
            assert record.get("_deposit", {}).get("created_by") == 1
            assert record.get("item_type_id") == "15"
            assert record.get("weko_shared_id") == -1
            assert check_created_id(record) == False
            ## no item type
            record["item_type_id"] = ""
            assert record.get("_deposit", {}).get("created_by") == 1
            assert record.get("item_type_id") == ""
            assert record.get("weko_shared_id") == -1
            assert check_created_id(record) == False
            record["item_type_id"] = "15"

    data_registration = app.config.get("WEKO_ITEMS_UI_DATA_REGISTRATION")
    application_item_type_list = app.config.get(
        "WEKO_ITEMS_UI_APPLICATION_ITEM_TYPES_LIST"
    )

    with app.test_request_context(headers=[("Accept-Language", "en")]):
        with app.test_client() as client:
            for user in users:
                obj = user.get("obj")

                client.get("/foo_login/{}".format(obj.email), follow_redirects=True)
                assert current_user.is_authenticated == True
                assert current_user.id == obj.id
                assert current_user.roles == obj.roles
                super_flg = False
                for s in supers:
                    if s in obj.roles:
                        super_flg = True
                print("email:{}".format(obj.email))
                print("id:{}".format(obj.id))
                print("roles:{}".format(obj.roles))
                print("super_flg:{}".format(super_flg))

                # no item_type_id
                record["item_type_id"] = ""
                assert record.get("item_type_id") == ""
                record["_deposit"]["created_by"] = obj.id
                record["weko_shared_id"] = -1
                assert record.get("_deposit", {}).get("created_by") == obj.id
                assert record.get("weko_shared_id") == -1
                assert check_created_id(record) == True

                record["_deposit"]["created_by"] = -1
                record["weko_shared_id"] = obj.id
                assert record.get("_deposit", {}).get("created_by") == -1
                assert record.get("weko_shared_id") == obj.id
                assert check_created_id(record) == True

                record["_deposit"]["created_by"] = -1
                record["weko_shared_id"] = -1
                assert record.get("_deposit", {}).get("created_by") == -1
                assert record.get("weko_shared_id") == -1
                if super_flg:
                    assert check_created_id(record) == True
                else:
                    assert check_created_id(record) == False

                record["item_type_id"] = "15"
                assert record.get("item_type_id") == "15"

                # created_by
                record["_deposit"]["created_by"] = obj.id
                record["weko_shared_id"] = -1
                assert record.get("_deposit", {}).get("created_by") == obj.id
                assert record.get("weko_shared_id") == -1
                assert check_created_id(record) == True

                # weko_shared_id
                record["_deposit"]["created_by"] = -1
                record["weko_shared_id"] = obj.id
                assert record.get("_deposit", {}).get("created_by") == -1
                assert record.get("weko_shared_id") == obj.id
                assert check_created_id(record) == True

                # created_id and weko_shared_id
                record["_deposit"]["created_by"] = obj.id
                record["weko_shared_id"] = obj.id
                assert record.get("_deposit", {}).get("created_by") == obj.id
                assert record.get("weko_shared_id") == obj.id
                assert check_created_id(record) == True

                # no created_id and weko_shared_id
                record["_deposit"]["created_by"] = -1
                record["weko_shared_id"] = -1
                assert record.get("_deposit", {}).get("created_by") == -1
                assert record.get("weko_shared_id") == -1
                if super_flg:
                    assert check_created_id(record) == True
                else:
                    assert check_created_id(record) == False


# def check_usage_report_in_permission(permission):


# def check_create_usage_report(record, file_json):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_check_create_usage_report -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_create_usage_report(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    fjson = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': 'image/jpeg', 'filename': 'helloworld.pdf', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': 2700000.0, 'mimetype': 'image/jpeg', 'file_order': 0}
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert check_create_usage_report(record, fjson) == None

# def __get_file_permission(record_id, file_name):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test___get_file_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test___get_file_permission(app, records, users,db_file_permission):
    indexer, results = records
    recid = results[0]["recid"]
    filename =results[0]["filename"]
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert __get_file_permission(recid.pid_value, filename) == []