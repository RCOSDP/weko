import io
from datetime import datetime, timedelta, timezone
from unittest import mock  # python3
from unittest.mock import MagicMock

import mock  # python2, after pip install mock
import pytest
from flask import Flask, json, jsonify, session, url_for, Response
from flask_babelex import get_locale, to_user_timezone, to_utc
from flask_login import current_user
from flask_security import login_user
from flask_security.utils import login_user
from invenio_accounts.models import Role, User
from invenio_accounts.testutils import create_test_user, login_user_via_session
from mock import patch

from weko_records.models import ItemType, ItemTypeName
from weko_admin.models import AdminSettings
from weko_records_ui.permissions import (
    check_created_id,
    check_publish_status,
    check_permission_period,
    check_user_group_permission,
    check_usage_report_in_permission,
    get_permission,
    check_open_restricted_permission,
    check_file_download_permission,
    check_content_clickable,
    check_create_usage_report,
    __get_file_permission,
    check_billing_file_permission,
    get_file_price,
    check_original_pdf_download_permission,
    file_permission_factory,
    page_permission_factory,
    is_open_restricted,
    check_charge,
    create_charge,
    close_charge
)


# def page_permission_factory(record, *args, **kwargs):
#    def can(self):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_get_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_page_permission_factory(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]

    assert page_permission_factory(record).can() == False

    with patch("weko_records_ui.permissions.check_publish_status", return_value=True):
        with patch("weko_records_ui.permissions.check_index_permissions", return_value=True):
            assert page_permission_factory(record).can() == True

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        assert page_permission_factory(record).can() == True


# def file_permission_factory(record, *args, **kwargs):
#    def can(self):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_get_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_file_permission_factory(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    assert file_permission_factory(record).can() == None


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
        assert check_file_download_permission(record, fjson, True) == True
    
    with patch("flask_login.utils._get_user", return_value=users[7]["obj"]):
        assert check_file_download_permission(record, fjson, True) == True

    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        assert check_file_download_permission(record, fjson, True) == True
    
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        with patch("weko_records_ui.permissions.to_utc", return_value=datetime.now()):
            assert check_file_download_permission(record, fjson, False) == False
            
            fjson['date'][0]['dateValue'] = ""
            assert check_file_download_permission(record, fjson, False) == True
            
            fjson['date'][0]['dateValue'] = "2022-09-27"
            fjson['accessrole'] = 'open_date'
            assert check_file_download_permission(record, fjson, True) == True
            assert check_file_download_permission(record, fjson, False) == False

            with patch("weko_records_ui.permissions.to_utc", return_value="test"):
                assert check_file_download_permission(record, fjson, False) == False
            
            fjson['accessrole'] = 'open_login'
            assert check_file_download_permission(record, fjson, True) == True

            with patch("weko_records_ui.permissions.check_user_group_permission", return_value=True):
                fjson['groups'] = True
                assert check_file_download_permission(record, fjson, False) == True
                fjson['groups'] = False
                assert check_file_download_permission(record, fjson, False) == True
                fjson['groupsprice'] = [MagicMock()]
                assert check_file_download_permission(record, fjson, False) == True
    
            fjson['accessrole'] = 'open_no'
            assert check_file_download_permission(record, fjson, True) == False
            assert check_file_download_permission(record, fjson, False) == False

            fjson['accessrole'] = 'open_restricted'
            assert check_file_download_permission(record, fjson, True) == False
            

    itn = ItemTypeName(
        id=1, name="テストアイテムタイプ", has_site_license=False, is_active=True
    )
    obj = ItemType(
        item_type_name=itn
        )
    future_date = datetime(2023,12,31,15,0,0)
    past_date = datetime(2022,11,30,15,0,0)

    with open("tests/data/record_a.json","r") as fa:
        record_a = json.load(fa)

    with open("tests/data/fjson_a.json","r") as ra:
        fjson_a = json.load(ra)

    with open("tests/data/record_b.json","r") as fb:
        record_b = json.load(fb)

    with open("tests/data/fjson_b.json","r") as rb:
        fjson_b = json.load(rb)

    with open("tests/data/record_c.json","r") as fc:
        record_c = json.load(fc)

    with open("tests/data/fjson_c.json","r") as rc:
        fjson_c = json.load(rc)

    with patch("flask_login.utils._get_user", return_value=users[5]["obj"]):

        with patch("weko_records.api.ItemTypes.get_by_id", return_value=obj):

            # 課金ファイルアクセス権あり
            with patch("weko_records_ui.permissions.check_billing_file_permission", return_value=True):
                # 8
                with patch("weko_records_ui.permissions.to_utc", return_value=future_date):
                    assert check_file_download_permission(record_a, fjson_a, check_billing_file=True) == True
                # 10
                with patch("weko_records_ui.permissions.to_utc", return_value=past_date):
                    assert check_file_download_permission(record_b, fjson_b, check_billing_file=True) == True
                # 12
                assert check_file_download_permission(record_c, fjson_c, check_billing_file=True) == True
                # 14
                with patch("weko_records_ui.permissions.to_utc", return_value=future_date):
                    assert check_file_download_permission(record_a, fjson_a, check_billing_file=False) == False
                # 16
                with patch("weko_records_ui.permissions.to_utc", return_value=past_date):
                    assert check_file_download_permission(record_b, fjson_b, check_billing_file=False) == True
                # 18
                assert check_file_download_permission(record_c, fjson_c, check_billing_file=False) == True

            # 課金ファイルアクセス権なし
            with patch("weko_records_ui.permissions.check_billing_file_permission", return_value=False):
                # 9
                with patch("weko_records_ui.permissions.to_utc", return_value=future_date):
                    assert check_file_download_permission(record_a, fjson_a, check_billing_file=True) == False
                # 11
                with patch("weko_records_ui.permissions.to_utc", return_value=past_date):
                    assert check_file_download_permission(record_b, fjson_b, check_billing_file=True) == True
                # 13
                assert check_file_download_permission(record_c, fjson_c, check_billing_file=True) == False
                # 15
                with patch("weko_records_ui.permissions.to_utc", return_value=future_date):
                    assert check_file_download_permission(record_a, fjson_a, check_billing_file=False) == False
                # 17
                with patch("weko_records_ui.permissions.to_utc", return_value=past_date):
                    assert check_file_download_permission(record_b, fjson_b, check_billing_file=False) == True
                # 19
                assert check_file_download_permission(record_c, fjson_c, check_billing_file=False) == True

# def check_open_restricted_permission(record, fjson):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_check_open_restricted_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_open_restricted_permission(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    fjson = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': 'image/jpeg', 'filename': 'helloworld.pdf', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': 2700000.0, 'mimetype': 'image/jpeg', 'file_order': 0}
    data1 = MagicMock()
    data1.status = 1

    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert check_open_restricted_permission(record, fjson) == False
        
        with patch("weko_records_ui.permissions.__get_file_permission", return_value=data1):
            assert check_open_restricted_permission(record, fjson) == False
            

# def is_open_restricted(file_data):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_get_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_is_open_restricted(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    fjson = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': 'image/jpeg', 'filename': 'helloworld.pdf', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': 2700000.0, 'mimetype': 'image/jpeg', 'file_order': 0}

    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert is_open_restricted(fjson) == False

        fjson['accessrole'] = 'open_restricted'
        assert is_open_restricted(fjson) == True


# def check_content_clickable(record, fjson):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_check_content_clickable -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_content_clickable(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    fjson = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': 'image/jpeg', 'filename': 'helloworld.pdf', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': 2700000.0, 'mimetype': 'image/jpeg', 'file_order': 0}
    data1 = MagicMock()
    data1.status = 0

    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert check_content_clickable(record, fjson) == False

        fjson['accessrole'] = 'open_restricted'
        assert check_content_clickable(record, fjson) == True

        with patch("weko_records_ui.permissions.__get_file_permission", return_value=[data1]):
            assert check_content_clickable(record, fjson) == False

            data1.status = 1
            assert check_content_clickable(record, fjson) == True


# def check_permission_period(permission):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_get_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_permission_period(app):
    data1 = MagicMock()
    data1.status = 1

    assert check_permission_period(data1) == True

    data1.status = 0
    assert check_permission_period(data1) == False


# def get_permission(record, fjson):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_get_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_permission(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    fjson = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': 'image/jpeg', 'filename': 'helloworld.pdf', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': 2700000.0, 'mimetype': 'image/jpeg', 'file_order': 0}
    data1 = MagicMock()
    data1.status = 1
    data1.usage_application_activity_id = 1
    data2 = {'Status': 'action_canceled'}

    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert get_permission(record, fjson) == None

        with patch("weko_records_ui.permissions.__get_file_permission", return_value=[data1]):
            assert get_permission(record, fjson) != None

            data1.status = 0
            with patch("weko_workflow.api.WorkActivity.get_activity_steps", return_value=[data2]):
                assert get_permission(record, fjson) == None
            
            with patch("weko_workflow.api.WorkActivity.get_activity_steps", return_value=""):
                assert get_permission(record, fjson) != None


# def check_original_pdf_download_permission(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_check_original_pdf_download_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_original_pdf_download_permission(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    data1 = MagicMock()
    def can():
        return True
    data1.can = can

    with app.test_request_context():
        with patch("invenio_access.action_factory", return_value=data1):
            with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
                assert check_original_pdf_download_permission(record) == None

                with patch("weko_records_ui.permissions.check_created_id", return_value=False):
                    assert check_original_pdf_download_permission(record) == None


# def check_user_group_permission(group_id):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_get_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_user_group_permission(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]

    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert check_user_group_permission(1) == False


# def check_publish_status(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_get_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
# @pytest.parametrize("",[])
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
        
        
        record["publish_status"] = "1"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "1"
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
        record["publish_status"] = "1"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "1"
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
        record["publish_status"] = "1"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "1"
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
        record["publish_status"] = "1"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "1"
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
        record["publish_status"] = "1"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "1"
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
        record["publish_status"] = "1"
        record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        assert record.get("publish_status") == "1"
        assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
            "%Y-%m-%d"
        )
        assert check_publish_status(record) == False

        # Exception coverage
        record['pubdate']['attribute_value'] = 2
        try:
            assert check_publish_status(record) == False
        except:
            pass



# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_check_publish_status2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize("publish_status,pubdate,expect_result",[
    ("0",datetime.utcnow().strftime("%Y-%m-%d"),True),
    ("1",datetime.utcnow().strftime("%Y-%m-%d"),False),
    ("0",datetime.now(timezone(timedelta(hours=+9), "JST")).strftime("%Y-%m-%d"),True),
    ("1",datetime.now(timezone(timedelta(hours=+9), "JST")).strftime("%Y-%m-%d"),False),
    ("0",(datetime.now(timezone(timedelta(hours=+9), "JST"))+ timedelta(days=1)).strftime("%Y-%m-%d"),False),
    ("0",(datetime.now(timezone(timedelta(hours=+9), "JST"))-timedelta(days=1)).strftime("%Y-%m-%d"),True),
    ("1",(datetime.now(timezone(timedelta(hours=+9), "JST"))-timedelta(days=1)).strftime("%Y-%m-%d"),False),
])
def test_check_publish_status2(app,publish_status,pubdate,expect_result):
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
        record["publish_status"] = publish_status
        record["pubdate"]["attribute_value"] = pubdate
        assert record.get("publish_status") == publish_status
        assert record.get("pubdate", {}).get("attribute_value") == pubdate
        assert check_publish_status(record) == expect_result

        # now = datetime.now(JST) + timedelta(days=1)
        # record["publish_status"] = "0"
        # record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        # assert record.get("publish_status") == "0"
        # assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
        #     "%Y-%m-%d"
        # )
        # assert check_publish_status(record) == False
        # record["publish_status"] = "1"
        # record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        # assert record.get("publish_status") == "1"
        # assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
        #     "%Y-%m-%d"
        # )
        # assert check_publish_status(record) == False

        # now = datetime.now(JST) + timedelta(days=10)
        # record["publish_status"] = "0"
        # record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        # assert record.get("publish_status") == "0"
        # assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
        #     "%Y-%m-%d"
        # )
        # assert check_publish_status(record) == False
        # record["publish_status"] = "1"
        # record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        # assert record.get("publish_status") == "1"
        # assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
        #     "%Y-%m-%d"
        # )
        # assert check_publish_status(record) == False

        # now = datetime.now(JST) - timedelta(days=1)
        # record["publish_status"] = "0"
        # record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        # assert record.get("publish_status") == "0"
        # assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
        #     "%Y-%m-%d"
        # )
        # assert check_publish_status(record) == True
        # record["publish_status"] = "1"
        # record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        # assert record.get("publish_status") == "1"
        # assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
        #     "%Y-%m-%d"
        # )
        # assert check_publish_status(record) == False

        # now = datetime.now(JST) - timedelta(days=10)
        # record["publish_status"] = "0"
        # record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        # assert record.get("publish_status") == "0"
        # assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
        #     "%Y-%m-%d"
        # )
        # assert check_publish_status(record) == True
        # record["publish_status"] = "1"
        # record["pubdate"]["attribute_value"] = now.strftime("%Y-%m-%d")
        # assert record.get("publish_status") == "1"
        # assert record.get("pubdate", {}).get("attribute_value") == now.strftime(
        #     "%Y-%m-%d"
        # )
        # assert check_publish_status(record) == False


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
                # obj = user.get("obj")
                obj = MagicMock()

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
def test_check_usage_report_in_permission(app):
    data1 = MagicMock()
    data1.usage_report_activity_id = 1

    assert check_usage_report_in_permission(data1) == False

    data1.usage_report_activity_id = None
    assert check_usage_report_in_permission(data1) == True


# def check_create_usage_report(record, file_json):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_check_create_usage_report -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_create_usage_report(app, records, users,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    fjson = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': 'image/jpeg', 'filename': 'helloworld.pdf', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': 2700000.0, 'mimetype': 'image/jpeg', 'file_order': 0}
    data1 = MagicMock()

    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert check_create_usage_report(record, fjson) == None

        with patch("weko_records_ui.permissions.__get_file_permission", return_value=[data1]):
            with patch("weko_records_ui.permissions.check_usage_report_in_permission", return_value=True):
                assert check_create_usage_report(record, fjson) != None

            with patch("weko_records_ui.permissions.check_usage_report_in_permission", return_value=False):
                assert check_create_usage_report(record, fjson) == None


# def __get_file_permission(record_id, file_name):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test___get_file_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test___get_file_permission(app, records, users,db_file_permission):
    indexer, results = records
    recid = results[0]["recid"]
    filename =results[0]["filename"]
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert __get_file_permission(recid.pid_value, filename) == []

# def check_billing_file_permission(item_id, file_name):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_check_billing_file_permission -vv -s --cov-branch --cov-report=term --basetemp=.tox/c1/tmp
def test_check_billing_file_permission(users, db_item_billing):
    # 20
    assert check_billing_file_permission('1', '課金ファイル.txt') == False

    with patch("flask_login.utils._get_user", return_value=users[7]["obj"]):
        # 21
        with patch("weko_records_ui.permissions.check_charge", return_value='already'):
            assert check_billing_file_permission('1', '課金ファイル.txt') == True
        # 22
        with patch("weko_records_ui.permissions.check_charge", return_value='not_billed'):
            assert check_billing_file_permission('99', '課金ファイル.txt') == False
        # 23
        with patch("weko_records_ui.permissions.check_charge", return_value='not_billed'):
            assert check_billing_file_permission('1', '課金ファイル.txt') == False
    # 24
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        with patch("weko_records_ui.permissions.check_charge", return_value='not_billed'):
            assert check_billing_file_permission('1', '課金ファイル.txt') == True
    # 25 
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        with patch("weko_records_ui.permissions.check_charge", return_value='not_billed'):
            assert check_billing_file_permission('1', '課金ファイル.txt') == False

# def get_file_price(item_id):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_get_file_price -vv -s --cov-branch --cov-report=term --basetemp=.tox/c1/tmp
def test_get_file_price(users, db_item_billing, db_admin_settings):
    # 26
    assert get_file_price('99') == (None, None)
    # 27
    with patch("flask_login.utils._get_user", return_value=users[7]["obj"]):
        assert get_file_price('2') == (None, None)
    # 28
    with patch("flask_login.utils._get_user", return_value=users[8]["obj"]):
        result = get_file_price('2')
        assert result[0] == 110

# def check_charge(user_id, item_id, file_name):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_check_charge -vv -s --cov-branch --cov-report=term --basetemp=.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
        (8, True),
    ],
)
def test_check_charge(db_admin_settings, users, id, result):

    res = mock.Mock(spec=Response)
    settings = {"host": "host", "port": "port", "user": "user", "password": "pass", "use_proxy": True}

    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        # 29
        with patch('weko_records_ui.permissions.requests.get') as requests_get:
            requests_get.side_effect = Exception
            assert check_charge('1','1','課金ファイル.txt') == 'api_error'
        # 30
        res.json.return_value = {'message':'unknown_user_id'}
        with patch('weko_records_ui.permissions.requests.get', return_value=res):
            assert check_charge('1','1','課金ファイル.txt') == 'unknown_user'
        # 31
        res.json.return_value = {'message':'this_user_is_not_permit_to_use_credit_card'}
        with patch('weko_records_ui.permissions.requests.get', return_value=res):
            assert check_charge('1','1','課金ファイル.txt') == 'shared'
        # 32
        res.json.return_value = {'location':'location'}
        with patch('weko_records_ui.permissions.requests.get', return_value=res):
            assert check_charge('1','1','課金ファイル.txt') == 'credit_error'
        # 33
        res.json.return_value = ['element1','element2']
        with patch('weko_records_ui.permissions.requests.get', return_value=res):
            assert check_charge('1','1','課金ファイル.txt') == "already"
        # 34
        res.json.return_value = ['']
        with patch('weko_records_ui.permissions.requests.get', return_value=res):
            assert check_charge('1','1','課金ファイル.txt') == 'not_billed'
        # 35
        res.json.return_value = ['']
        AdminSettings.update('proxy_settings', settings)
        with patch('weko_records_ui.permissions.requests.get', return_value=res):
            assert check_charge('1','1','課金ファイル.txt') == 'not_billed'

# def create_charge(user_id, item_id, file_name, price, title, file_url):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_create_charge -vv -s --cov-branch --cov-report=term --basetemp=.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
        (8, True),
    ],
)
def test_create_charge(db_admin_settings, users, id, result):

    trade_id = 1
    res = mock.Mock(spec=Response)
    res.json.return_value = {'trade_id':1}
    settings = {"host": "host", "port": "port", "user": "user", "password": "pass", "use_proxy": True}

    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        # 36
        with patch('weko_records_ui.permissions.requests.get') as requests_get:
            requests_get.side_effect = Exception
            assert create_charge(1, 1, 'filename', 110, 'title', 'fileurl') == 'api_error'
        # 37
        res.headers = {'WEKO_CHARGE_STATUS':-128}
        with patch('weko_records_ui.permissions.requests.get', return_value=res):
            assert create_charge(1, 1, 'filename', 110, 'title', 'fileurl') == 'credit_error'
        # 38
        res.headers = {'WEKO_CHARGE_STATUS':-64}
        with patch('weko_records_ui.permissions.requests.get', return_value=res):
            assert create_charge(1, 1, 'filename', 110, 'title', 'fileurl') == 'connection_error'
        # 39
        res.headers = {'WEKO_CHARGE_STATUS':0}
        res.json.return_value = {'trade_id':1, 'charge_status':'1'}
        with patch('weko_records_ui.permissions.requests.get', return_value=res):
            assert create_charge(1, 1, 'filename', 110, 'title', 'fileurl') == 'already'
        # 40
        res.json.return_value = {'trade_id':trade_id, 'charge_status':'0'}
        with patch('weko_records_ui.permissions.requests.get', return_value=res):
            assert create_charge(1, 1, 'filename', 110, 'title', 'fileurl') == str(trade_id)
        # 41
        res.json.return_value = 'str'
        with patch('weko_records_ui.permissions.requests.get', return_value=res):
            assert create_charge(1, 1, 'filename', 110, 'title', 'fileurl') == 'api_error'
        # 42
        res.json.return_value = {'trade_id':trade_id, 'charge_status':'0'}
        AdminSettings.update('proxy_settings', settings)
        with patch('weko_records_ui.permissions.requests.get', return_value=res):
            assert create_charge(1, 1, 'filename', 110, 'title', 'fileurl') == str(trade_id)

# def close_charge(user_id: int, trade_id: int):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_close_charge -vv -s --cov-branch --cov-report=term --basetemp=.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
        (8, True),
    ],
)
def test_close_charge(db_admin_settings, users, id, result):

    res = mock.Mock(spec=Response)
    res.json.return_value = {'json':'json'}
    settings = {"host": "host", "port": "port", "user": "user", "password": "pass", "use_proxy": True}

    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        # 43
        with patch('weko_records_ui.permissions.requests.get') as requests_get:
            requests_get.side_effect = Exception
            assert close_charge(1, 1) == False
        # 44
        res.json.return_value = {'charge_status':'1'}
        with patch('weko_records_ui.permissions.requests.get', return_value=res):
            close_charge(1, 1) == True
        # 45
        res.json.return_value = {'charge_status':'2'}
        with patch('weko_records_ui.permissions.requests.get', return_value=res):
            close_charge(1, 1) == False
        # 46
        AdminSettings.update('proxy_settings', settings)
        res.json.return_value = {'charge_status':'1'}
        with patch('weko_records_ui.permissions.requests.get', return_value=res):
            close_charge(1, 1) == True