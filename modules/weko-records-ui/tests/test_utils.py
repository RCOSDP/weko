import re
import pytest
from weko_records_ui.utils import (
    convert_token_into_obj,
    is_onetime_file,
    to_utc_datetime,
    create_download_url,
    create_onetime_url_record,
    create_secret_url_record,
    generate_sha256_hash,
    is_future,
    create_usage_report_for_user,
    get_data_usage_application_data,
    send_secret_url_mail,
    send_usage_report_mail_for_user,
    check_and_send_usage_report,
    get_onetime_download,
    get_license_pdf,
    hide_item_metadata,
    get_pair_value,
    get_min_price_billing_file_download,
    validate_download_record,
    is_private_index,
    get_file_info_list,
    replace_license_free,
    hide_by_itemtype,
    hide_by_email,
    hide_by_file,
    hide_item_metadata_email_only,
    get_workflows,
    get_billing_file_download_permission,
    get_list_licence,
    restore,
    soft_delete,
    is_billing_item,
    get_groups_price,
    get_record_permalink,
    get_google_detaset_meta,
    get_google_scholar_meta,
    get_valid_onetime_download,
    display_oaiset_path,
    get_terms,
    get_roles,
    check_items_settings,
    validate_file_access,
    validate_secret_url_generation_request,
    #RoCrateConverter,
    #create_tsv
    is_secret_url_feature_enabled,
    has_permission_to_manage_secret_url,
    is_secret_file,
    can_manage_secret_url,
    validate_token,
    validate_url_download,
    )
import base64
from unittest.mock import MagicMock
import copy
import pytest
import io
from datetime import date, datetime as dt, time, timezone
from datetime import timedelta
from lxml import etree
from fpdf import FPDF
from invenio_records_files.utils import record_file_factory
from flask import Flask, json, jsonify, session, url_for,current_app
from flask_security.utils import login_user
from invenio_accounts.testutils import login_user_via_session
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from mock import patch
from weko_deposit.api import WekoRecord
from weko_records_ui.models import FileOnetimeDownload, FileSecretDownload
from weko_records.api import ItemTypes,Mapping
from werkzeug.exceptions import NotFound
from weko_admin.models import AdminSettings
from weko_records.serializers.utils import get_mapping
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName
from flask_babelex import gettext as _
from datetime import datetime ,timedelta

from weko_schema_ui.models import PublishStatus

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def is_future(settings=None):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_is_future -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_is_future(app):
    assert is_future(None) == True
    assert is_future('2100-01-01') == True
    assert is_future('2000-01-01T00:00:00') == False
    assert is_future('2000-01-01 00:00:00') == False
    assert is_future(dt(2100, 1, 1)) == True
    assert is_future('2000-01-01 00:00') == True

# def check_items_settings(settings=None):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_check_items_settings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_items_settings(app,db_admin_settings):
    with app.test_request_context():
        assert check_items_settings()==None
    
    settings = AdminSettings(name='items_display_settings',settings={"items_display_email": False, "items_search_author": "name", "item_display_open_date": False})
    setting = settings.get("items_display_settings")
    with app.test_request_context():
        assert check_items_settings(setting)==None

    settings = AdminSettings(name='items_display_settings',settings={"items_display_email": False})
    setting = settings.get("items_display_settings")
    with app.test_request_context():
        assert check_items_settings(setting)==None

    settings = AdminSettings(name='items_display_settings',settings={"items_search_author": "name"})
    setting = settings.get("items_display_settings")
    with app.test_request_context():
        assert check_items_settings(setting)==None
    
    settings = AdminSettings(name='items_display_settings',settings={"item_display_open_date": False})
    setting = settings.get("items_display_settings")
    with app.test_request_context():
        assert check_items_settings(setting)==None

    settings = AdminSettings(name='items_display_settings',settings={"items_display_email": False, "items_search_author": "name"})
    setting = settings.get("items_display_settings")
    with app.test_request_context():
        assert check_items_settings(setting)==None

    settings = AdminSettings(name='items_display_settings',settings={"items_display_email": False, "item_display_open_date": False})
    setting = settings.get("items_display_settings")
    with app.test_request_context():
        assert check_items_settings(setting)==None

    settings = AdminSettings(name='items_display_settings',settings={"items_search_author": "name", "item_display_open_date": False})
    setting = settings.get("items_display_settings")
    with app.test_request_context():
        assert check_items_settings(setting)==None
    
    settings = AdminSettings(name='items_display_settings',settings={})
    setting = settings.get("items_display_settings")
    with app.test_request_context():
        assert check_items_settings(setting)==None
        
    setting = AdminSettings.get(name="items_display_settings")
    assert isinstance(setting,AdminSettings.Dict2Obj)==True
    with app.test_request_context():
        current_app.config["EMAIL_DISPLAY_FLG"]=""
        current_app.config["ITEM_SEARCH_FLG"]=""
        current_app.config["OPEN_DATE_DISPLAY_FLG"]=""
        assert check_items_settings(setting)==None
        assert current_app.config["EMAIL_DISPLAY_FLG"]==setting.items_display_email
        assert current_app.config["ITEM_SEARCH_FLG"]==setting.items_search_author
        assert current_app.config["OPEN_DATE_DISPLAY_FLG"]==setting.item_display_open_date

    setting = AdminSettings.get(name="items_display_settings",dict_to_object=False)
    assert isinstance(setting,dict)==True
    with app.test_request_context():
        current_app.config["EMAIL_DISPLAY_FLG"]=""
        current_app.config["ITEM_SEARCH_FLG"]=""
        current_app.config["OPEN_DATE_DISPLAY_FLG"]=""
        assert setting['items_display_email']==False
        assert setting['items_search_author']=='name'
        assert setting['item_display_open_date']==False
        assert check_items_settings(setting)==None
        assert current_app.config["EMAIL_DISPLAY_FLG"]==setting['items_display_email']
        assert current_app.config["ITEM_SEARCH_FLG"]==setting['items_search_author']
        assert current_app.config["OPEN_DATE_DISPLAY_FLG"]==setting['item_display_open_date']
        current_app.config["EMAIL_DISPLAY_FLG"]=""
        current_app.config["ITEM_SEARCH_FLG"]=""
        current_app.config["OPEN_DATE_DISPLAY_FLG"]=""
        setting['items_display_email']=True
        setting['items_search_author']='id'
        setting['item_display_open_date']=True
        assert check_items_settings(setting)==None
        assert current_app.config["EMAIL_DISPLAY_FLG"]==setting['items_display_email']
        assert current_app.config["ITEM_SEARCH_FLG"]==setting['items_search_author']
        assert current_app.config["OPEN_DATE_DISPLAY_FLG"]==setting['item_display_open_date']


# def get_record_permalink(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_record_permalink -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_record_permalink(app,records):
    indexer, results = records
    record = results[0]["record"]
    assert get_record_permalink(record) == 'https://doi.org/10.xyz/0000000001'

    record = results[1]["record"]
    assert get_record_permalink(record) == None


# def get_groups_price(record: dict) -> list:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_groups_price -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_groups_price(app,records):
    indexer, results = records
    record = results[0]["record"]
    assert get_groups_price(record)==[]


# def get_billing_file_download_permission(groups_price: list) -> dict:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_billing_file_download_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_billing_file_download_permission(users):
    groups_price = [{'file_name': '003.jpg', 'groups_price': [{'group': '1', 'price': '100'}]}]
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert get_billing_file_download_permission(groups_price)=={'003.jpg': False}


# def get_min_price_billing_file_download(groups_price: list,
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_min_price_billing_file_download -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_min_price_billing_file_download(users):
    groups_price = [{'file_name': '003.jpg', 'groups_price': [{'group': '1', 'price': '100'}]}]
    billing_file_permission = {'003.jpg': True}
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        assert get_min_price_billing_file_download(groups_price,billing_file_permission) == {}

        billing_file_permission['003.jpg'] = False
        assert get_min_price_billing_file_download(groups_price,billing_file_permission) == {}

        # Exception coverage
        try:
            billing_file_permission['003.jpg'] = True
            groups_price[0]['groups_price'][0]['price'] = {}
            get_min_price_billing_file_download(groups_price,billing_file_permission)
        except:
            pass
        

# def is_billing_item(item_type_id):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_is_billing_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_is_billing_item(app,itemtypes):
    assert is_billing_item(1)==False

# def soft_delete(recid):
#     def get_cache_data(key: str):
#     def check_an_item_is_locked(item_id=None):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_soft_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_soft_delete(app, records, users):
    indexer, results = records
    record = results[0]["record"]
    recid = results[0]["recid"]
    assert soft_delete(record.pid.pid_value)==None
    assert recid.status == PIDStatus.DELETED

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        assert soft_delete(record.pid.pid_value) == None

        data1 = MagicMock()
        data1.exists = False

        with patch("weko_records_ui.utils.PIDVersioning", return_value=data1):
            assert soft_delete(record.pid.pid_value) == None


# def restore(recid):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_restore -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_restore(app,records):
    indexer, results = records
    record = results[0]["record"]
    recid = results[0]["recid"]
    assert restore(record.pid.pid_value)==None

    soft_delete(record.pid.pid_value)
    assert recid.status == PIDStatus.DELETED
    assert restore(record.pid.pid_value)==None
    assert recid.status == PIDStatus.REGISTERED


# def get_list_licence():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_list_licence -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_list_licence(app):
    with app.test_request_context():
        assert get_list_licence()==[{'value': 'license_free', 'name': 'write your own license'}, {'value': 'license_12', 'name': 'Creative Commons CC0 1.0 Universal Public Domain Designation'}, {'value': 'license_6', 'name': 'Creative Commons Attribution 3.0 Unported (CC BY 3.0)'}, {'value': 'license_7', 'name': 'Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)'}, {'value': 'license_8', 'name': 'Creative Commons Attribution-NoDerivs 3.0 Unported (CC BY-ND 3.0)'}, {'value': 'license_9', 'name': 'Creative Commons Attribution-NonCommercial 3.0 Unported (CC BY-NC 3.0)'}, {'value': 'license_10', 'name': 'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0)'}, {'value': 'license_11', 'name': 'Creative Commons Attribution-NonCommercial-NoDerivs 3.0 Unported (CC BY-NC-ND 3.0)'}, {'value': 'license_0', 'name': 'Creative Commons Attribution 4.0 International (CC BY 4.0)'}, {'value': 'license_1', 'name': 'Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)'}, {'value': 'license_2', 'name': 'Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0)'}, {'value': 'license_3', 'name': 'Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)'}, {'value': 'license_4', 'name': 'Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)'}, {'value': 'license_5', 'name': 'Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)'}]


# def get_license_pdf(license, item_metadata_json, pdf, file_item_id, footer_w,
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_license_pdf -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_license_pdf(app):
    app.config['WEKO_RECORDS_UI_LICENSE_ICON_PDF_LOCATION'] = "/static/images/creative_commons/"
    lic ='license_12'
    item_metadata_json={'id': '23.1', 'pid': {'type': 'depid', 'value': '23.1', 'revision_id': 0}, 'lang': 'ja', 'owner': '1', 'title': 'test', 'owners': [1], 'status': 'published', '$schema': '/items/jsonschema/15', 'pubdate': '2022-09-28', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}, 'shared_user_id': -1, 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_ddb1', 'resourcetype': 'dataset'}, 'item_1617605131499': [{'url': {'url': 'https://weko3.example.org/record/23.1/files/sample_arial.pdf'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-28'}], 'format': 'application/pdf', 'filename': 'sample_arial.pdf', 'filesize': [{'value': '28 KB'}], 'mimetype': 'application/pdf', 'accessrole': 'open_access', 'version_id': '72b25fac-c471-44af-9971-c608f684f863', 'displaytype': 'preview', 'licensetype': 'license_12'}]}
    file_item_id = 'item_1617605131499'
    footer_w =90
    footer_h = 4
    cc_logo_xposition = 160
    item = {'name': 'Creative Commons CC0 1.0 Universal Public Domain Designation', 'code': 'CC0', 'href_ja': 'https://creativecommons.org/publicdomain/zero/1.0/deed.ja', 'href_default': 'https://creativecommons.org/publicdomain/zero/1.0/', 'value': 'license_12', 'src': '88x31(0).png', 'src_pdf': 'cc-0.png', 'href_pdf': 'https://creativecommons.org/publicdomain/zero/1.0/deed.ja', 'txt': 'This work is licensed under a Public Domain Dedication International License.'}
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(40, 10, 'Hello World!')
    with app.test_request_context():
        get_license_pdf(lic,item_metadata_json,pdf,file_item_id,footer_w,footer_h,cc_logo_xposition,item)
        assert pdf

    with app.test_request_context():
        get_license_pdf("license_free",item_metadata_json,pdf,file_item_id,footer_w,footer_h,cc_logo_xposition,item)


# def get_pair_value(name_keys, lang_keys, datas):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_pair_value -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_pair_value(app):
    name_keys = ['subitem_1551255647225']
    lang_keys = ['subitem_1551255648112']
    datas = [{'subitem_1551255647225': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000001(public_open_access_simple)', 'subitem_1551255648112': 'en'}]
    with app.test_request_context():
        name,lang =  get_pair_value(name_keys,lang_keys,datas)
        assert name== ('ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'ja')
        assert lang== ('en_conference paperITEM00000001(public_open_access_simple)', 'en')


# def hide_item_metadata(record, settings=None, item_type_mapping=None,
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_hide_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_hide_item_metadata(app,records,users):
    indexer, results = records
    record = results[0]["record"]
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert hide_item_metadata(record)==False

    record['_deposit'] = {"owners_ext": {"email": "email"}}
    app.config['EMAIL_DISPLAY_FLG'] = False
    with patch("weko_items_ui.utils.hide_meta_data_for_role", return_value=True):
        assert hide_item_metadata(record)==True


# def hide_item_metadata_email_only(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_hide_item_metadata_email_only -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_hide_item_metadata_email_only(app,records,users):
    indexer, results = records
    record = results[0]["record"]
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert hide_item_metadata_email_only(record)==False

        record['_deposit'] = {"owners_ext": {"email": "email"}}
        app.config['EMAIL_DISPLAY_FLG'] = False
        with patch("weko_items_ui.utils.hide_meta_data_for_role", return_value=True):
            assert hide_item_metadata_email_only(record)==True


# def hide_by_file(item_metadata):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_hide_by_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_hide_by_file(app,records):
    indexer, results = records
    record = results[0]["item"]
    assert hide_by_file(copy.deepcopy(record))==record

    data1 = {"data1":
        {
            "attribute_type": "file",
            "attribute_value_mlt": [
                {
                    "accessrole": "open_no"
                }
            ]
        }
    }
    assert hide_by_file(data1)


# def hide_by_email(item_metadata):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_hide_by_email -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_hide_by_email(app,records):
    indexer, results = records
    record = results[0]["record"]
    test_record = copy.deepcopy(record)
    record['item_1617186419668']['attribute_value_mlt'][0].pop('creatorMails')
    record['item_1617186419668']['attribute_value_mlt'][1].pop('creatorMails')
    record['item_1617186419668']['attribute_value_mlt'][2].pop('creatorMails')
    record['item_1617349709064']['attribute_value_mlt'][0].pop('contributorMails')
    assert hide_by_email(test_record)==record

    record = {
        "item_type_id": "1",
        "_deposit": {
            "owners": [1],
            "owners_ext": {
                "username": "test username",
                "displayname": "test displayname",
                "email": "test@test.com"
            }
        },
        "publish_date": "2021-08-06",
        "publish_status": "0",
        "item_1617186331708": {
            "attribute_name": "Title",
            "attribute_value_mlt": [
                {
                    "subitem_1551255647225": "test title ja",
                    "subitem_1551255648112": "ja",
                },
                {
                    "subitem_1551255647225": "test title en",
                    "subitem_1551255648112": "en",
                },
            ],
        }
    }
    record['_deposit'].pop("owners_ext")
    test_record = copy.deepcopy(record)
    assert hide_by_email(test_record)==record

    record = {
        "item_type_id": None,
        "_deposit": {
            "owners": [1],
            "owners_ext": {
                "username": "test username",
                "displayname": "test displayname",
                "email": "test@test.com"
            }
        },
        "publish_date": "2021-08-06",
        "publish_status": "0",
        "item_1617186331708": {
            "attribute_name": "Title",
            "attribute_value_mlt": [
                {
                    "subitem_1551255647225": "test title ja",
                    "subitem_1551255648112": "ja",
                },
                {
                    "subitem_1551255647225": "test title en",
                    "subitem_1551255648112": "en",
                },
            ],
        }
    }
    test_record = copy.deepcopy(record)
    assert hide_by_email(test_record)==record


# def hide_by_itemtype(item_metadata, hidden_items):
#     def del_hide_sub_metadata(keys, metadata):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_hide_by_itemtype -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_hide_by_itemtype(app, records):
    indexer, results = records
    record = results[0]["item"]
    hidden_items1 = ["test"]
    hidden_items2 = [["test", "test", "test"]]
    hidden_items3 = [["test", "test"]]
    test1 = {"test": {"attribute_value_mlt": {"test": "test"}}}
    test2 = {"test": {"attribute_value_mlt": {"test": "test"}}}
    test3 = {"test": {"attribute_value_mlt": [{"test": "test"}]}}

    assert hide_by_itemtype(test1, hidden_items1) != None
    assert hide_by_itemtype(test2, hidden_items2) != None
    assert hide_by_itemtype(test3, hidden_items3) != None

    # assert hide_by_itemtype(copy.deepcopy(record),[])=={'id': '1', 'pid': {'type': 'recid', 'value': '1', 'revision_id': 0}, 'path': ['2'], 'owner': '1', 'title': 'ja_conference paperITEM00000009(public_open_access_open_access_simple)', 'owners': [1], 'status': 'draft', '$schema': 'https://localhost:8443/items/jsonschema/1', 'pubdate': '2021-08-06', 'feedback_mail_list': [{'email': 'wekosoftware@nii.ac.jp', 'author_id': ''}], 'item_1617186331708': [{'subitem_1551255647225': 'ja_conference paperITEM00000009(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000009(public_open_access_simple)', 'subitem_1551255648112': 'en'}], 'item_1617186385884': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}], 'item_1617186419668': [{'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '4', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'creatorAffiliations': [{'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}], 'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI'}]}]}, {'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}]}, {'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}]}], 'item_1617186476635': {'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}, 'item_1617186499011': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}], 'item_1617186609386': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}], 'item_1617186626617': [{'subitem_description': 'Description\nDescription<br/>Description', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'en'}, {'subitem_description': '概要\n概要\n概要\n概要', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'ja'}], 'item_1617186643794': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}], 'item_1617186660861': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}], 'item_1617186702042': [{'subitem_1551255818386': 'jpn'}], 'item_1617186783814': [{'subitem_identifier_uri': 'http://localhost', 'subitem_identifier_type': 'URI'}], 'item_1617186859717': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}], 'item_1617186882738': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}], 'item_1617186901218': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}], 'item_1617186920753': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}], 'item_1617186941041': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}], 'item_1617186959569': {'subitem_1551256328147': '1'}, 'item_1617186981471': {'subitem_1551256294723': '111'}, 'item_1617186994930': {'subitem_1551256248092': '12'}, 'item_1617187024783': {'subitem_1551256198917': '1'}, 'item_1617187045071': {'subitem_1551256185532': '3'}, 'item_1617187112279': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}], 'item_1617187136212': {'subitem_1551256096004': '2021-06-30'}, 'item_1617187187528': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}, 'item_1617265215918': {'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}, 'item_1617349709064': [{'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'contributorType': 'ContactPerson', 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'lang': 'ja', 'contributorName': '情報, 太郎'}, {'lang': 'ja-Kana', 'contributorName': 'ジョウホ, タロウ'}, {'lang': 'en', 'contributorName': 'Joho, Taro'}]}], 'item_1617349808926': {'subitem_1523263171732': 'Version'}, 'item_1617351524846': {'subitem_1523260933860': 'Unknown'}, 'item_1617353299429': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}], 'item_1617605131499': [{'url': {'url': 'https://weko3.example.org/record/1/files/helloworld.pdf'}, 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'format': 'application/pdf', 'filename': 'helloworld.pdf', 'filesize': [{'value': '1 KB'}], 'mimetype': 'application/pdf', 'accessrole': 'open_access', 'version_id': 'c1502853-c2f9-455d-8bec-f6e630e54b21', 'displaytype': 'simple'}], 'item_1617610673286': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}], 'rightHolderNames': [{'rightHolderName': 'Right Holder Name', 'rightHolderLanguage': 'ja'}]}], 'item_1617620223087': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}], 'item_1617944105607': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}]}


# def replace_license_free(record_metadata, is_change_label=True):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_replace_license_free -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_replace_license_free(app,records):
    # indexer, results = records
    # record = results[0]["record"]
    # assert replace_license_free(copy.deepcopy(record))==None

    data1 = {"key": {
        "attribute_type": "file",
        "attribute_value_mlt": [{
            "licensetype": "license_free",
            "licensefree": "True"
        }]
    }}
    replace_license_free(data1)

# def get_file_info_list(record):
#     def get_file_size(p_file):
#     def set_message_for_file(p_file):
#     def get_data_by_key_array_json(key, array_json, get_key):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_file_info_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_file_info_list(app,records):
    indexer, results = records
    record = results[0]["record"]
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        ret =  get_file_info_list(record)
        assert len(ret)==2

# def create_usage_report_for_user(onetime_download_extra_info: dict):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
#def test_create_usage_report_for_user():
#    assert False


# def get_data_usage_application_data(record_metadata, data_result: dict):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_data_usage_application_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_data_usage_application_data(app, db, workflows, records, users, db_file_permission):
    _onetime_download_extra_info = {
        'usage_application_activity_id': 'usage_application_activity_id_dummy1',
        'is_guest': False
    }
    app.config['WEKO_WORKFLOW_USAGE_REPORT_WORKFLOW_NAME'] = 'Data Usage Report'
    app.config['WEKO_WORKFLOW_ENABLE_SHOWING_TERM_OF_USE'] = False
    app.config['WEKO_WORKFLOW_ACTIVITY_ID_FORMAT'] = 'A-{}-{}'
    app.config['WEKO_WORKFLOW_RESTRICTED_ACCESS_USAGE_REPORT_ID'] = 'subitem_restricted_access_usage_report_id'
    assert create_usage_report_for_user(_onetime_download_extra_info)

    _onetime_download_extra_info['is_guest'] = True
    with app.test_request_context():
        assert create_usage_report_for_user(_onetime_download_extra_info)==None


# def send_usage_report_mail_for_user(guest_mail: str, temp_url: str):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_send_usage_report_mail_for_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_send_usage_report_mail_for_user(app):
    with patch("weko_workflow.utils.send_mail_url_guest_user", return_value=True):
        res = send_usage_report_mail_for_user('guest@nii.co.jp', 'guest_url')
        assert res


# def check_and_send_usage_report(extra_info, user_mail):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_check_and_send_usage_report -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_and_send_usage_report(app, db, users, db_file_permission):
    _record = {
        'recid': db_file_permission[0].record_id
    }
    _file_obj = {
        'accessrole': 'open_restricted',
        'filename': db_file_permission[0].file_name
    }
    app.config['WEKO_WORKFLOW_USAGE_REPORT_WORKFLOW_NAME'] = 'Data Usage Report'
    
    #56
    assert not check_and_send_usage_report({"is_guest": False, "send_usage_report": False, "usage_application_activity_id": "A-20230101-00001"},users[7]['email'],_record, _file_obj)
    
    data1 = MagicMock()
    data2 = MagicMock()
    data3 = MagicMock()

    def send_reminder_mail(x, y, z):
        return False
    
    def send_reminder_mail_2(x, y, z):
        return True

    data1.activity_id = 'A-20230301-00001'
    data3.send_reminder_mail = send_reminder_mail

    with patch("flask_login.utils._get_user", return_value=users[2]['obj']):

        with patch("weko_records_ui.utils.create_usage_report_for_user", return_value=False):
            assert _("Unexpected error occurred.") == check_and_send_usage_report({"is_guest": False, "send_usage_report": True, "usage_application_activity_id": "A-20230101-00001"},users[7]['email'],data1, data2)

        with patch("weko_records_ui.utils.create_usage_report_for_user", return_value=data1):
            with patch("weko_records_ui.utils.UsageReport", return_value=data3):
                assert _("Failed to send mail.") == check_and_send_usage_report({"is_guest": False, "send_usage_report": True, "usage_application_activity_id": "A-20230101-00001"},users[7]['email'],data1, data2)
    
        with patch("weko_records_ui.utils.create_usage_report_for_user", return_value=data1):
            data3.send_reminder_mail = send_reminder_mail_2
            with patch("weko_records_ui.utils.UsageReport", return_value=data3):
                with patch("weko_records_ui.utils.check_create_usage_report" ,return_value={}):
                    with patch("weko_records_ui.models.FilePermission.update_usage_report_activity_id",return_value=""):
                        check_and_send_usage_report({"is_guest": False, "send_usage_report": True, "usage_application_activity_id": "A-20230101-00001"},users[7]['email'],_record, _file_obj)
    data1.activity_id = ""
    with patch("weko_records_ui.utils.create_usage_report_for_user", return_value=data1):
        with patch("flask_login.utils._get_user", return_value=users[7]['obj']):
            with patch("weko_records_ui.utils.UsageReport", return_value=data3):
                with patch("weko_records_ui.utils.check_create_usage_report",return_value=None):
                    check_and_send_usage_report({"is_guest": False, "send_usage_report": True, "usage_application_activity_id": "A-20230101-00001"},users[7]['email'],data1, data2)


# def is_private_index(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_is_private_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_is_private_index(app,records):
    indexer, results = records
    record = results[0]["record"]
    assert is_private_index(record)==False

    data1 = [
        [0, 1, 2, 3, 4, 5, 6],
        [0, 1, 2, 3, 4, 5, 6],
        [0, 1, 2, 3, 4, 5, 6],
        [0, 1, 2, 3, 4, 5, 6],
        [0, 1, 2, 3, 4, 5, 6],
        [0, 1, 2, 3, 4, 5, 6],
        [0, 1, 2, 3, 4, 5, 6],
    ]

    with patch("weko_index_tree.api.Indexes.get_path_list", return_value=data1):
        assert is_private_index(record) == False
    
    data1 = [
        [0, 1, 2, 3, 4, 5, False],
    ]

    with patch("weko_index_tree.api.Indexes.get_path_list", return_value=data1):
        assert is_private_index(record) == True


# def validate_download_record(record: dict):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_validate_download_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
def test_validate_download_record():
    record = {'publish_status': PublishStatus.PUBLIC.value}
    with patch('weko_records_ui.utils.is_private_index', return_value=False):
        assert validate_download_record(record) is True
        record['publish_status'] = None
        assert validate_download_record(record) is False
        record['publish_status'] = PublishStatus.PUBLIC.value
    with patch('weko_records_ui.utils.is_private_index', return_value=True):
        assert validate_download_record(record) is False
        record['publish_status'] = None
        assert validate_download_record(record) is False


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_is_secret_url_feature_enabled -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
def test_is_secret_url_feature_enabled(app):
    with app.app_context():
        # Case 1: secret_enableがTrueを返す
        with patch('weko_records_ui.utils.AdminSettings.get') as mock_get:
            mock_get.return_value = {
                'secret_URL_file_download': {
                    'secret_enable': True,
                }
            }
            assert is_secret_url_feature_enabled() is True

        # Case 2: secret_enableがFalseを返す
        with patch('weko_records_ui.utils.AdminSettings.get') as mock_get:
            mock_get.return_value = {
                'secret_URL_file_download': {
                    'secret_enable': False,
                }
            }
            assert is_secret_url_feature_enabled() is False

        # Case 3: AdminSettingsがNoneでcurrent_app.configが存在し、期待するデフォルト設定がある場合
        with patch('weko_records_ui.utils.AdminSettings.get', return_value=None):
            with patch('weko_records_ui.utils.current_app.config', {
                'WEKO_ADMIN_RESTRICTED_ACCESS_SETTINGS': {
                    'secret_URL_file_download': {}
                }
            }):
                # secret_enable は存在しないのでデフォルト値の False を返すことを検証
                assert is_secret_url_feature_enabled() is False

        # Case 4: AdminSettingsがNoneでcurrent_app.configが存在しない場合
        with patch('weko_records_ui.utils.AdminSettings.get', return_value=None):
            with patch('weko_records_ui.utils.current_app.config', {'WEKO_ADMIN_RESTRICTED_ACCESS_SETTINGS': {}}):
                # 設定がない場合も False を返すことを検証
                assert is_secret_url_feature_enabled() is False

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_has_permission_to_manage_secret_url -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
@pytest.mark.parametrize(
    "user_id, expected",
    [
        (0, True),  # Owner
        (4, True),  # Shared user
        (1, True),  # Superuser
        (2, True),  # Superuser
        (3, False), # No permission
        (5, False), # No superuser role
    ],
)
def test_has_permission_to_manage_secret_url(user_id, expected, app, users):
    # レコードに必要なデータを設定
    # 'owner'と'weko_shared_id'は、usersリストから取り出した値を使用
    record = {'owner': str(users[0]["id"]), 'weko_shared_id': users[4]["id"]}

    # アプリケーションコンテキスト内でテスト実行
    with app.app_context():
        # has_permission_to_manage_secret_url関数を実行し、
        # 結果が期待される値 (expected) と一致するかを検証
        assert has_permission_to_manage_secret_url(record, users[user_id]["id"]) == expected

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_is_secret_file -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
@pytest.mark.parametrize(
    "file_data, filename, expected",
    [
        # ケース1: accessroleが 'open_no' の場合
        ([{'filename': 'testfile.txt', 'accessrole': 'open_no', 'date': [{'dateValue': '2999-12-31'}]}], 'testfile.txt', True),
        # ケース2: accessroleが 'open_date' で公開日が未来の場合
        ([{'filename': 'testfile.txt', 'accessrole': 'open_date', 'date': [{'dateValue': '2999-12-31'}]}], 'testfile.txt', True),
        # ケース3: accessroleが 'open_date' で公開日が過去の場合
        ([{'filename': 'testfile.txt', 'accessrole': 'open_date', 'date': [{'dateValue': '2000-01-01'}]}], 'testfile.txt', False),
        # ケース4: accessroleが 'open_no' や 'open_date' でない場合
        ([{'filename': 'testfile.txt', 'accessrole': 'open_test', 'date': [{'dateValue': '2999-12-31'}]}], 'testfile.txt', False),
        # ケース5: ファイル名が一致しない場合
        ([{'filename': 'otherfile.txt', 'accessrole': 'open_no', 'date': [{'dateValue': '2999-12-31'}]}], 'testfile.txt', False),
        # ケース6: file_dataが空の場合
        ([], 'testfile.txt', False),
    ],
)
def test_is_secret_file(file_data, filename, expected):
    # WekoRecordのモックを作成し、get_file_dataメソッドをファイルデータでモックする
    mock_record = MagicMock(spec=WekoRecord)
    mock_record.get_file_data.return_value = file_data  # モックのget_file_dataメソッドが返す値を設定

    # dt（日時関連）をモックして、現在の日付や日付文字列の変換を制御する
    with patch('weko_records_ui.utils.dt') as mock_dt:
        mock_dt.now.return_value = dt(2024, 1, 1)  # 現在の日付を2024年1月1日に設定
        mock_dt.strptime.side_effect = lambda *args, **kwargs: dt.strptime(*args, **kwargs)  # strptimeの動作をモック

        # is_secret_file関数を実行して、結果が期待される値と一致するかを確認
        result = is_secret_file(mock_record, filename)

        # 実際の結果が期待値と一致することを確認
        assert result == expected

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_can_manage_secret_url -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
@pytest.mark.parametrize(
    "is_authenticated, feature_enabled, has_permission, is_secret, expected",
    [
        # Case 1: ユーザーが認証されていない場合
        (False, True, True, True, False),
        # Case 2: 機能が有効でない場合
        (True, False, True, True, False),
        # Case 3: ユーザーに権限がない場合
        (True, True, False, True, False),
        # Case 4: ファイルが秘密でない場合
        (True, True, True, False, False),
        # Case 5: すべての条件を満たす場合
        (True, True, True, True, True),
    ],
)
def test_can_manage_secret_url(is_authenticated, feature_enabled, has_permission, is_secret, expected):
    # WekoRecordのモックを作成
    mock_record = MagicMock(spec=WekoRecord)
    
    # ユーザーのモックを作成
    mock_user = MagicMock()
    mock_user.is_authenticated = is_authenticated  # ユーザーが認証されているかどうかを設定

    # current_userのモックを作成して、`mock_user`を返すように設定
    with patch('weko_records_ui.utils.current_user', mock_user):
        # is_secret_url_feature_enabledのモックを作成して、`feature_enabled`を返すように設定
        with patch('weko_records_ui.utils.is_secret_url_feature_enabled', return_value=feature_enabled):
            # has_permission_to_manage_secret_urlのモックを作成して、`has_permission`を返すように設定
            with patch('weko_records_ui.utils.has_permission_to_manage_secret_url', return_value=has_permission):
                # is_secret_fileのモックを作成して、`is_secret`を返すように設定
                with patch('weko_records_ui.utils.is_secret_file', return_value=is_secret):
                    # can_manage_secret_url関数を実行し、結果が期待される値と一致するかを確認
                    assert can_manage_secret_url(mock_record, 'testfile.txt') == expected


# def get_onetime_download(file_name: str, record_id: str,
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_onetime_download -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_onetime_download(app, db_fileonetimedownload):
    with app.test_request_context():
        ret = get_onetime_download('helloworld.pdf','1','wekosoftware@nii.ac.jp')
        assert ret.file_name=='helloworld.pdf'

        with patch("weko_records_ui.models.FileOnetimeDownload.find", return_value=False):
            assert get_onetime_download('helloworld.pdf','1','wekosoftware@nii.ac.jp') == None

# def def get_valid_onetime_download(file_name: str, record_id: str,user_mail: str) -> Optional[FileOnetimeDownload]:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_valid_onetime_download -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_valid_onetime_download():
    with patch("weko_records_ui.models.FileOnetimeDownload.find_downloadable_only",return_value=[]):
        assert get_valid_onetime_download(file_name= "str", record_id= "str",user_mail= "str") is None
    with patch("weko_records_ui.models.FileOnetimeDownload.find_downloadable_only",return_value=[{}]):
        assert {} == get_valid_onetime_download(file_name= "str", record_id= "str",user_mail= "str")
    with patch("weko_records_ui.models.FileOnetimeDownload.find_downloadable_only",return_value=["a","b"]):
        assert "a" == get_valid_onetime_download(file_name= "str", record_id= "str",user_mail= "str")


# def get_workflows():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_workflows -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_workflows(app,users):
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            assert get_workflows()==[]
        
        data1 = MagicMock()

        def get_workflow_list():
            return [data1]
        
        data1.get_workflow_list = get_workflow_list
        data1.open_restricted = True
        data1.id = True
        data1.flows_name = True

        with patch("weko_records_ui.utils.WorkFlow", return_value=data1):
            assert get_workflows() != []


# def get_roles():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_roles -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_roles(app,users):
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert get_roles()==[{'id': 'none_loggin', 'name': 'Guest'}, {'id': 1, 'name': 'System Administrator'}, {'id': 2, 'name': 'Repository Administrator'}, {'id': 3, 'name': 'Contributor'}, {'id': 4, 'name': 'Community Administrator'}, {'id': 5, 'name': 'General'}, {'id': 6, 'name': 'Original Role'}]


# def get_terms():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_terms -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_terms(app):
    with app.test_request_context():
        assert get_terms()== [{'id': 'term_free', 'name': 'Free Input'}]


# def display_oaiset_path(record_metadata):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_display_oaiset_path -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_display_oaiset_path(app,records,itemtypes,oaischema,users):
    indexer, results = records
    record = results[0]["record_data"]
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert display_oaiset_path(record)==None

        data1 = MagicMock()
        data1.public_state = True
        data1.harvest_public_state = True

        with patch("weko_index_tree.api.Indexes.get_path_name", return_value=[data1]):
            assert display_oaiset_path(record) == None


# def get_google_scholar_meta(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_google_scholar_meta -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_google_scholar_meta(app,records,itemtypes,oaischema,oaiidentify):
    _data = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2022-10-07T06:11:40Z</responseDate><request identifier="oai:repository.dl.itc.u-tokyo.ac.jp:02005680" verb="getrecord" metadataPrefix="jpcoar_1.0">https://repository.dl.itc.u-tokyo.ac.jp/oai</request><getrecord><record><header><identifier>oai:repository.dl.itc.u-tokyo.ac.jp:02005680</identifier><datestamp>2022-09-27T06:40:27Z</datestamp></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">『史料編纂掛備用写真画像図画類目録』画像の部：新旧架番号対照表</dc:title><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/123" nameIdentifierScheme="ORCID">123</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="en">creator name</jpcoar:creatorName><jpcoar:familyName xml:lang="en">creator family name</jpcoar:familyName><jpcoar:givenName xml:lang="en">creator given name</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="en">creator alternative name</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="test uri" nameIdentifierScheme="ISNI">affi name id</jpcoar:nameIdentifier><jpcoar:affiliationName xml:lang="en">affi name</jpcoar:affiliationName></jpcoar:affiliation></jpcoar:creator><dc:rights>CC BY</dc:rights><datacite:description xml:lang="ja" descriptionType="Other">『史料編纂掛備用寫眞畫像圖畫類目録』（1905年）の「画像」（肖像画模本）の部に著録する資料の架番号の新旧対照表。史料編纂所所蔵肖像画模本データベースおよび『目録』版面画像へのリンク付き。『画像史料解析センター通信』98（2022年10月）に解説記事あり。</datacite:description><dc:publisher xml:lang="ja">東京大学史料編纂所附属画像史料解析センター</dc:publisher><dc:publisher xml:lang="en">Center for the Study of Visual Sources, Historiographical Institute, The University of Tokyo</dc:publisher><datacite:date dateType="Issued">2022-09-30</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_ddb1">dataset</dc:type><jpcoar:identifier identifierType="HDL">http://hdl.handle.net/2261/0002005680</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://repository.dl.itc.u-tokyo.ac.jp/records/2005680</jpcoar:identifier><jpcoar:relation relationType="references"><jpcoar:relatedIdentifier identifierType="URI">https://clioimg.hi.u-tokyo.ac.jp/viewer/list/idata/850/8500/20/%28a%29/?m=limit</jpcoar:relatedIdentifier></jpcoar:relation><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>point longitude test</datacite:pointLongitude><datacite:pointLatitude>point latitude test</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>1</datacite:westBoundLongitude><datacite:eastBoundLongitude>2</datacite:eastBoundLongitude><datacite:southBoundLatitude>3</datacite:southBoundLatitude><datacite:northBoundLatitude>4</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>geo location place test</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:file><jpcoar:URI objectType="dataset">https://repository.dl.itc.u-tokyo.ac.jp/record/2005680/files/comparison_table_of_preparation_image_catalog.xlsx</jpcoar:URI><jpcoar:mimeType>application/vnd.openxmlformats-officedocument.spreadsheetml.sheet</jpcoar:mimeType><jpcoar:extent>121.7KB</jpcoar:extent><datacite:date dateType="Available">2022-09-27</datacite:date></jpcoar:file></jpcoar:jpcoar></metadata></record></getrecord></OAI-PMH>'
    _rv = etree.fromstring(_data)
    with patch("weko_records_ui.utils.getrecord", return_value=_rv):
        with app.test_request_context():
            indexer, results = records
            record = results[0]["record"]
            assert get_google_scholar_meta(record)==[{'data': '『史料編纂掛備用写真画像図画類目録』画像の部：新旧架番号対照表', 'name': 'citation_title'}, {'data': '東京大学史料編纂所附属画像史料解析センター', 'name': 'citation_publisher'}, {'data': '2022-09-30', 'name': 'citation_publication_date'}, {'data': 'creator name', 'name': 'citation_author'}, {'data': 'https://repository.dl.itc.u-tokyo.ac.jp/record/2005680/files/comparison_table_of_preparation_image_catalog.xlsx',  'name': 'citation_pdf_url'}, {'data': '', 'name': 'citation_dissertation_institution'}, {'data': 'http://TEST_SERVER/records/1', 'name': 'citation_abstract_html_url'}]


# def get_google_detaset_meta(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_google_detaset_meta -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_google_detaset_meta(app, records, itemtypes, oaischema, oaiidentify):
    _data = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2022-10-07T06:11:40Z</responseDate><request identifier="oai:repository.dl.itc.u-tokyo.ac.jp:02005680" verb="getrecord" metadataPrefix="jpcoar_1.0">https://repository.dl.itc.u-tokyo.ac.jp/oai</request><getrecord><record><header><identifier>oai:repository.dl.itc.u-tokyo.ac.jp:02005680</identifier><datestamp>2022-09-27T06:40:27Z</datestamp></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">『史料編纂掛備用写真画像図画類目録』画像の部：新旧架番号対照表</dc:title><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/123" nameIdentifierScheme="ORCID">123</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="en">creator name</jpcoar:creatorName><jpcoar:familyName xml:lang="en">creator family name</jpcoar:familyName><jpcoar:givenName xml:lang="en">creator given name</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="en">creator alternative name</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="test uri" nameIdentifierScheme="ISNI">affi name id</jpcoar:nameIdentifier><jpcoar:affiliationName xml:lang="en">affi name</jpcoar:affiliationName></jpcoar:affiliation></jpcoar:creator><dc:rights>CC BY</dc:rights><datacite:description xml:lang="ja" descriptionType="Other">『史料編纂掛備用寫眞畫像圖畫類目録』（1905年）の「画像」（肖像画模本）の部に著録する資料の架番号の新旧対照表。史料編纂所所蔵肖像画模本データベースおよび『目録』版面画像へのリンク付き。『画像史料解析センター通信』98（2022年10月）に解説記事あり。</datacite:description><dc:publisher xml:lang="ja">東京大学史料編纂所附属画像史料解析センター</dc:publisher><dc:publisher xml:lang="en">Center for the Study of Visual Sources, Historiographical Institute, The University of Tokyo</dc:publisher><datacite:date dateType="Issued">2022-09-30</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_ddb1">dataset</dc:type><jpcoar:identifier identifierType="HDL">http://hdl.handle.net/2261/0002005680</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://repository.dl.itc.u-tokyo.ac.jp/records/2005680</jpcoar:identifier><jpcoar:relation relationType="references"><jpcoar:relatedIdentifier identifierType="URI">https://clioimg.hi.u-tokyo.ac.jp/viewer/list/idata/850/8500/20/%28a%29/?m=limit</jpcoar:relatedIdentifier></jpcoar:relation><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>point longitude test</datacite:pointLongitude><datacite:pointLatitude>point latitude test</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>1</datacite:westBoundLongitude><datacite:eastBoundLongitude>2</datacite:eastBoundLongitude><datacite:southBoundLatitude>3</datacite:southBoundLatitude><datacite:northBoundLatitude>4</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>geo location place test</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:file><jpcoar:URI objectType="dataset">https://repository.dl.itc.u-tokyo.ac.jp/record/2005680/files/comparison_table_of_preparation_image_catalog.xlsx</jpcoar:URI><jpcoar:mimeType>application/vnd.openxmlformats-officedocument.spreadsheetml.sheet</jpcoar:mimeType><jpcoar:extent>121.7KB</jpcoar:extent><datacite:date dateType="Available">2022-09-27</datacite:date></jpcoar:file></jpcoar:jpcoar></metadata></record></getrecord></OAI-PMH>'
    _rv = etree.fromstring(_data)
    with patch("weko_records_ui.utils.getrecord", return_value=_rv):
        indexer, results = records
        record = results[0]["record"]
        assert get_google_detaset_meta(record)=='{"@context": "https://schema.org/", "@type": "Dataset", "citation": ["http://hdl.handle.net/2261/0002005680", "https://repository.dl.itc.u-tokyo.ac.jp/records/2005680"], "creator": [{"@type": "Person", "alternateName": "creator alternative name", "familyName": "creator family name", "givenName": "creator given name", "identifier": "123", "name": "creator name"}], "description": "『史料編纂掛備用寫眞畫像圖畫類目録』（1905年）の「画像」（肖像画模本）の部に著録する資料の架番号の新旧対照表。史料編纂所所蔵肖像画模本データベースおよび『目録』版面画像へのリンク付き。『画像史料解析センター通信』98（2022年10月）に解説記事あり。", "distribution": [{"@type": "DataDownload", "contentUrl": "https://repository.dl.itc.u-tokyo.ac.jp/record/2005680/files/comparison_table_of_preparation_image_catalog.xlsx", "encodingFormat": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}, {"@type": "DataDownload", "contentUrl": "https://raw.githubusercontent.com/RCOSDP/JDCat-base/main/apt.txt", "encodingFormat": "text/plain"}, {"@type": "DataDownload", "contentUrl": "https://raw.githubusercontent.com/RCOSDP/JDCat-base/main/environment.yml", "encodingFormat": "application/x-yaml"}, {"@type": "DataDownload", "contentUrl": "https://raw.githubusercontent.com/RCOSDP/JDCat-base/main/postBuild", "encodingFormat": "text/x-shellscript"}], "includedInDataCatalog": {"@type": "DataCatalog", "name": "https://localhost"}, "license": ["CC BY"], "name": "『史料編纂掛備用写真画像図画類目録』画像の部：新旧架番号対照表", "spatialCoverage": [{"@type": "Place", "geo": {"@type": "GeoCoordinates", "latitude": "point latitude test", "longitude": "point longitude test"}}, {"@type": "Place", "geo": {"@type": "GeoShape", "box": "1 3 2 4"}}, "geo location place test"]}'
        
        app.config['WEKO_RECORDS_UI_GOOGLE_SCHOLAR_OUTPUT_RESOURCE_TYPE'] = None
        assert get_google_detaset_meta(record) == None

        data1 = MagicMock()

        with patch("lxml.etree", return_value=data1):
            assert get_google_detaset_meta(record) == None


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_to_utc_datetime -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
def test_to_utc_datetime(app):
    assert to_utc_datetime('2025-1-1') == datetime(
        2025, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert to_utc_datetime('2025-01-01') == datetime(
        2025, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert to_utc_datetime('2025-1-1', 720) == datetime(
        2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert to_utc_datetime('2025-1-1', -720) == datetime(
        2024, 12, 31, 12, 0, tzinfo=timezone.utc)
    assert to_utc_datetime('2025-1-1', -540) == datetime(
        2024, 12, 31, 15, 0, tzinfo=timezone.utc)
    assert to_utc_datetime('2025/01/01') is None


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_validate_secret_url_generation_request -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
def test_validate_secret_url_generation_request(app):
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(1)).strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(1)).strftime("%Y-%m-%d")
    base_case = {'link_name'              : '',
                 'expiration_date'        : '',
                 'download_limit'         : None,
                 'send_email'             : False,
                 'timezone_offset_minutes': 0}
    test_cases = [
        (None,
         False),
        # Base case is valid
        (base_case,
         True),
        # When all fields are valid
        ({'link_name'              : '123',
          'expiration_date'        : tomorrow,
          'download_limit'         : 1,
          'send_email'             : False,
          'timezone_offset_minutes': 0},
          True),
        # When all fields are invalid
        ({'link_name'              : 123,
          'expiration_date'        : yesterday,
          'download_limit'         : 0,
          'send_email'             : None,
          'timezone_offset_minutes': '0'},
          False),
        # When each keys do not exist
        ({key: value for key, value in base_case.items()
          if key != 'link_name'}, False),
        ({key: value for key, value in base_case.items()
          if key != 'expiration_date'}, False),
        ({key: value for key, value in base_case.items()
          if key != 'download_limit'}, False),
        ({key: value for key, value in base_case.items()
          if key != 'send_email'}, False),
        ({key: value for key, value in base_case.items()
          if key != 'timezone_offset_minutes'}, False),
        # For link_name
        ({**base_case, 'link_name': '123'    }, True),
        ({**base_case, 'link_name': 123      }, False),
        ({**base_case, 'link_name': 'a' * 256}, False),
        # For expiration_date
        ({**base_case, 'expiration_date': today    }, True),
        ({**base_case, 'expiration_date': tomorrow }, True),
        ({**base_case, 'expiration_date': yesterday}, False),
        ({**base_case, 'expiration_date': 'abc'    }, False),
        ({**base_case, 'expiration_date': 20250101 }, False),
        # For download_limit
        ({**base_case, 'download_limit': 1    }, True),
        ({**base_case, 'download_limit': 0    }, False),
        ({**base_case, 'download_limit': -1   }, False),
        ({**base_case, 'download_limit': 1.1  }, False),
        ({**base_case, 'download_limit': 'abc'}, False),
        # For send_email
        ({**base_case, 'send_email': False}, True),
        ({**base_case, 'send_email': True }, True),
        ({**base_case, 'send_email': None }, False),
        # For timezone_offset_minutes
        ({**base_case, 'timezone_offset_minutes': 0   }, True),
        ({**base_case, 'timezone_offset_minutes': 720 }, True),
        ({**base_case, 'timezone_offset_minutes': -720}, True),
        ({**base_case, 'timezone_offset_minutes': 800 }, False),
    ]

    for request_data, expected in test_cases:
        assert validate_secret_url_generation_request(request_data) is expected


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_create_secret_url_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings -p no:warnings
@patch('weko_records_ui.utils.get_restricted_access')
@patch('weko_records_ui.utils.current_user')
def test_create_secret_url_record(mock_user, mock_settings, users):
    mock_settings.return_value = {'expiration_date': 30, 'download_limit': 10}
    mock_user.id = 1
    record_id = 1
    file_name = 'test.txt'

    # Test request data
    request = {'link_name': '', 'expiration_date': '', 'download_limit': None,
               'timezone_offset_minutes': 0}
    url_obj = create_secret_url_record(record_id, file_name, request)
    assert isinstance(url_obj, FileSecretDownload)
    assert url_obj.creator_id == 1
    assert url_obj.record_id == str(record_id)
    assert url_obj.file_name == file_name
    expected_name = 'test.txt_' + datetime.now(timezone.utc).strftime('%Y-%m-%d')
    assert url_obj.label_name == expected_name
    expected_date = datetime.combine((datetime.now(timezone.utc).date()+timedelta(days=31)), time(0, 0, 0))
    assert url_obj.expiration_date == expected_date
    assert url_obj.download_limit == 10

    # If request is valid
    request = {
        'link_name': 'test',
        'expiration_date': (datetime.now(timezone.utc).date()).strftime('%Y-%m-%d'),
        'download_limit': 5,
        'timezone_offset_minutes': 720
    }
    url_obj2 = create_secret_url_record(record_id, file_name, request)
    assert url_obj2.creator_id == 1
    assert url_obj2.record_id == str(record_id)
    assert url_obj2.file_name == file_name
    assert url_obj2.label_name == 'test'
    expected_date2 = datetime.combine((datetime.now(timezone.utc).date()+timedelta(days=1)), time(12,0,0))
    assert url_obj2.expiration_date == expected_date2
    assert url_obj2.download_limit == 5
    request = {'link_name': '',
               'expiration_date': '2022-10-10',
               'download_limit': '',
               'timezone_offset_minutes': 0}
    with pytest.raises(ValueError):
        create_secret_url_record(record_id, file_name, request)
    request = {'link_name': '',
               'expiration_date': '',
               'download_limit': 0,
               'timezone_offset_minutes': 0}
    with pytest.raises(ValueError):
        create_secret_url_record(record_id, file_name, request)

    # If settings is invalid
    mock_settings.return_value = {}
    assert create_secret_url_record(record_id, file_name, request) is None
    mock_settings.return_value = 'invalid data'
    assert create_secret_url_record(record_id, file_name, request) is None


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_create_onetime_download_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
@patch('weko_records_ui.utils.get_restricted_access')
@patch('weko_records_ui.utils.current_user')
def test_create_onetime_download_record(mock_user, mock_get, users):
    mock_get.return_value = {'expiration_date': 30}
    mock_user.id = 1
    activity_id = 1
    record_id = 1
    file_name = 'test.txt'
    user_mail = 'test@example.org'

    assert FileOnetimeDownload.query.count() == 0
    url_obj = create_onetime_url_record(
        activity_id, record_id, file_name, user_mail)
    assert FileOnetimeDownload.query.count() == 1
    assert isinstance(url_obj, FileOnetimeDownload)
    assert url_obj.approver_id == 1
    assert url_obj.record_id == str(record_id)
    assert url_obj.file_name == file_name
    now = (dt.now(timezone.utc) + timedelta(days=31)).replace(tzinfo=None)
    tolerance = timedelta(seconds=1)
    assert now - url_obj.expiration_date <= tolerance
    assert url_obj.download_limit == 10
    assert url_obj.user_mail == user_mail
    assert url_obj.is_guest is False

    mock_get.return_value = {}
    assert create_onetime_url_record(
        activity_id, record_id, file_name, user_mail) is None
    mock_get.return_value = 'invalid data'
    assert create_onetime_url_record(
        activity_id, record_id, file_name, user_mail) is None


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_create_download_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
def test_create_download_url(app):
    with patch('weko_records_ui.utils.base64.urlsafe_b64encode') as encoded:
        encoded.return_value = b'test'
        with app.test_request_context():
            secret_obj = FileSecretDownload(
                creator_id=1,
                record_id=1,
                file_name='test.txt',
                label_name='test_url',
                expiration_date=dt.now() + timedelta(days=30),
                download_limit=10)
            url = create_download_url(secret_obj)
            assert url == (f'http://TEST_SERVER/record/1/file/secret/test.txt'
                           f'?token={b"test".decode()}')
        with app.test_request_context():
            onetime_obj = FileOnetimeDownload(
                approver_id=1,
                record_id=1,
                file_name='test.txt',
                expiration_date=dt.now() + timedelta(days=30),
                download_limit=10,
                user_mail='test@example.org',
                is_guest=False,
                extra_info={'activity_id': 1})
            url = create_download_url(onetime_obj)
            assert url == (f'http://TEST_SERVER/record/1/file/onetime/test.txt'
                           f'?token={b"test".decode()}')
        with app.test_request_context():
            invalid_obj = MagicMock()
            url = create_download_url(invalid_obj)
            assert url is None


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_generate_sha256_hash -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
def test_generate_sha256_hash(app):
    app.config['WEKO_RECORDS_UI_SECRET_KEY'] = 'secret'
    secret_ubj = FileSecretDownload(
        creator_id=1,
        record_id=1,
        file_name='test.txt',
        label_name='test_url',
        expiration_date=dt.now().date() + timedelta(days=30),
        download_limit=10)
    secret_url = generate_sha256_hash(secret_ubj)
    assert len(secret_url) == 32
    secret_obj2 = FileSecretDownload(
        creator_id=2,
        record_id=2,
        file_name='test2.txt',
        label_name='test_url2',
        expiration_date=dt.now().date() + timedelta(days=10),
        download_limit=5)
    secret_url2 = generate_sha256_hash(secret_obj2)
    assert len(secret_url2) == 32
    assert secret_url != secret_url2
    same_url = generate_sha256_hash(secret_ubj)
    assert secret_url == same_url

    onetime_obj = FileOnetimeDownload(
        approver_id=1,
        record_id=1,
        file_name='test.txt',
        expiration_date=dt.now().date() + timedelta(days=30),
        download_limit=10,
        user_mail='test@example.org',
        is_guest=False,
        extra_info={'activity_id': 1})
    onetime_url = generate_sha256_hash(onetime_obj)
    assert len(onetime_url) == 32
    onetime_obj2 = FileOnetimeDownload(
        approver_id=2,
        record_id=2,
        file_name='test2.txt',
        expiration_date=dt.now().date() + timedelta(days=10),
        download_limit=5,
        user_mail='test2@example.org',
        is_guest=True,
        extra_info={'activity_id': 2})
    onetime_url2 = generate_sha256_hash(onetime_obj2)
    assert len(onetime_url2) == 32
    assert onetime_url != onetime_url2
    same_url = generate_sha256_hash(onetime_obj)
    assert onetime_url == same_url


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_send_secret_url_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
@patch('weko_records_ui.utils.UserProfile.get_by_userid')
@patch('weko_records_ui.utils.current_user')
@patch('weko_records_ui.utils.set_mail_info', return_value={})
@patch('weko_records_ui.utils.process_send_mail', return_value=True)
def test_send_secret_url_mail(mock_send, mock_set_info, mock_user,
                              mock_profile, app):
    app.config['WEKO_RECORDS_UI_MAIL_TEMPLATE_SECRET_URL'] = 'test_template'
    mock_profile_obj = MagicMock()
    mock_profile_obj._displayname = 'test_user'
    mock_profile.return_value = mock_profile_obj
    mock_user.id = 1
    mock_user.email = 'test@example.org'

    uuid = 'test_uuid'
    url_obj = FileSecretDownload(
        creator_id=1,
        record_id=1,
        file_name='test.txt',
        label_name='test_url',
        expiration_date=datetime(2125, 1, 1, 0, 0),
        download_limit=10)
    item_title = 'test_title'
    mock_user.id = 1
    expected_info = {
        'restricted_download_link'  : create_download_url(url_obj),
        'mail_recipient'            : 'test@example.org',
        'file_name'                 : url_obj.file_name,
        'restricted_expiration_date': '2125-01-01 23:59:59(JST)',
        'restricted_download_count' : str(url_obj.download_limit),
        'restricted_fullname'       : 'test_user',
        'restricted_data_name'      : item_title,
    }
    expected_pattern = 'test_template'
    with app.test_request_context():
        assert send_secret_url_mail(uuid, url_obj, item_title) is True
    mock_send.assert_called_once_with(expected_info, expected_pattern)
    mock_send.reset_mock()

    mock_profile.return_value = None
    with app.test_request_context():
        assert send_secret_url_mail(uuid, url_obj, item_title) is True
    expected_info['restricted_fullname'] = ''
    mock_send.assert_called_once_with(expected_info, expected_pattern)

    mock_send.return_value = False
    with app.test_request_context():
        assert send_secret_url_mail(uuid, url_obj, item_title) is False


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_validate_token -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
def test_validate_token(app, users):
    with app.test_request_context():
        secret_obj = FileSecretDownload.create(
            creator_id=1,
            record_id=1,
            file_name='test.txt',
            label_name='test_url',
            expiration_date=dt.now(timezone.utc) + timedelta(days=30),
            download_limit=10)
        url = create_download_url(secret_obj)
        match = re.search(r'[?&]token=([^&]+)', url)
        secret_token = match.group(1)
        assert validate_token(secret_token, is_secret_url=True) is True
    with app.test_request_context():
        onetime_obj = FileOnetimeDownload.create(
            approver_id=1,
            record_id=1,
            file_name='test.txt',
            expiration_date=dt.now(timezone.utc) + timedelta(days=30),
            download_limit=10,
            user_mail='test@example.org',
            is_guest=False,
            extra_info={'activity_id': 1})
        url = create_download_url(onetime_obj)
        match = re.search(r'[?&]token=([^&]+)', url)
        onetime_token = match.group(1)
        assert validate_token(onetime_token, is_secret_url=False) is True
    invalid_bytes = b'\xb2q\xff\x19\xaf\xfc\xc6T\x8bt\xd6\xf6\xc6 \
                            \x08D\xe7\xf3G;cN\x1bn|\xa2\x88\x01v\xed\x1cA_1'
    with app.test_request_context():
        secret_token = base64.urlsafe_b64decode(secret_token.encode())
        assert secret_token.split(b'_')[-1] == invalid_bytes.split(b'_')[-1]
        invalid_token = base64.urlsafe_b64encode(invalid_bytes).decode()
        assert validate_token(invalid_token, is_secret_url=True) is False
    with app.test_request_context():
        onetime_token = base64.urlsafe_b64decode(onetime_token.encode())
        assert onetime_token.split(b'_')[-1] == invalid_bytes.split(b'_')[-1]
        invalid_token = base64.urlsafe_b64encode(invalid_bytes).decode()
        assert validate_token(invalid_token, is_secret_url=False) is False
    with app.test_request_context():
        assert validate_token('', is_secret_url=True) is False
        assert validate_token(123, is_secret_url=True) is False


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_convert_token_into_obj -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
@patch('weko_records_ui.utils.validate_token')
def test_convert_token_into_obj(vldt_token, app, users):
    vldt_token.return_value = True
    created_at = dt.now(timezone.utc)
    with app.test_request_context():
        secret_obj = FileSecretDownload.create(
            creator_id=1,
            record_id=1,
            file_name='test.txt',
            label_name='test_url',
            expiration_date=created_at + timedelta(days=30),
            download_limit=10)
        assert FileSecretDownload.query.count() == 1
        url = create_download_url(secret_obj)
        match = re.search(r'[?&]token=([^&]+)', url)
        secret_token = match.group(1)
        secret_obj = convert_token_into_obj(secret_token, is_secret_url=True)
        assert isinstance(secret_obj, FileSecretDownload)
        assert secret_obj.id == 1
        assert secret_obj.creator_id == 1
        assert secret_obj.record_id == '1'
        assert secret_obj.file_name == 'test.txt'
        assert secret_obj.label_name == 'test_url'
        expected_date = (created_at + timedelta(days=30)).replace(tzinfo=None)
        assert secret_obj.expiration_date == expected_date
        assert secret_obj.download_limit == 10
        vldt_token.assert_called_once_with(secret_token, True)
        vldt_token.reset_mock()
    with app.test_request_context():
        onetime_obj = FileOnetimeDownload.create(
            approver_id=1,
            record_id=1,
            file_name='test.txt',
            expiration_date=created_at + timedelta(days=30),
            download_limit=10,
            user_mail='test@example.org',
            is_guest=False,
            extra_info={'activity_id': 1})
        assert FileOnetimeDownload.query.count() == 1
        url = create_download_url(onetime_obj)
        match = re.search(r'[?&]token=([^&]+)', url)
        onetime_token = match.group(1)
        onetime_obj = convert_token_into_obj(onetime_token, is_secret_url=False)
        assert isinstance(onetime_obj, FileOnetimeDownload)
        assert onetime_obj.id == 1
        assert onetime_obj.approver_id == 1
        assert onetime_obj.record_id == '1'
        assert onetime_obj.file_name == 'test.txt'
        expected_date = (created_at + timedelta(days=30)).replace(tzinfo=None)
        assert onetime_obj.expiration_date == expected_date
        assert onetime_obj.download_limit == 10
        assert onetime_obj.is_guest == False
        assert onetime_obj.extra_info == {'activity_id': 1}
        vldt_token.assert_called_once_with(onetime_token, False)
    vldt_token.return_value = False
    with app.test_request_context():
        assert convert_token_into_obj(secret_token, True) is None
        assert convert_token_into_obj(onetime_token, False) is None

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_validate_url_download -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
@patch('weko_records_ui.utils.validate_token')
@patch('weko_records_ui.utils.is_secret_url_feature_enabled')
@patch('weko_records_ui.utils.validate_file_access')
@patch('weko_records_ui.utils.validate_download_record')
def test_validate_url_download(vldt_record, vldt_file, is_enabled, vldt_token,
                               app, db, users):
    with app.test_request_context():
        secret_obj = FileSecretDownload.create(
            creator_id=1,
            record_id=1,
            file_name='test.txt',
            label_name='test_url',
            expiration_date=dt.now(timezone.utc) + timedelta(days=30),
            download_limit=10)
    db.session.flush()
    match = re.search(r'[?&]token=([^&]+)', create_download_url(secret_obj))
    secret_token = match.group(1)
    vldt_token.return_value  = True
    is_enabled.return_value  = True
    vldt_file.return_value   = True
    vldt_record.return_value = True
    assert validate_url_download('', '', secret_token, True) == (True, '')

    with app.test_request_context():
        onetime_obj = FileOnetimeDownload.create(
            approver_id=1,
            record_id=1,
            file_name='test.txt',
            expiration_date=dt.now(timezone.utc) + timedelta(days=30),
            download_limit=10,
            user_mail='test@example.org',
            is_guest=False,
            extra_info={'activity_id': 1})
    db.session.flush()
    match = re.search(r'[?&]token=([^&]+)', create_download_url(onetime_obj))
    onetime_token = match.group(1)
    assert validate_url_download('', '', onetime_token, False) == (True, '')

    with patch('weko_records_ui.utils.validate_token',
               return_value=False):
        assert validate_url_download('', '', secret_token, True) == (
            False, 'The provided token is invalid.')
    with patch('weko_records_ui.utils.is_secret_url_feature_enabled',
               return_value=False):
        assert validate_url_download('', '', secret_token, True) == (
                    False, 'This feature is currently disabled.')
    with patch('weko_records_ui.utils.validate_file_access',
               return_value=False):
        assert validate_url_download('', '', secret_token, True) == (
            False, 'This file is currently not available for this feature.')
    with patch('weko_records_ui.utils.validate_download_record',
               return_value=False):
        assert validate_url_download('', '', secret_token, True) == (
            False, 'This file is currently not available for this feature.')

    secret_obj.is_deleted = True
    db.session.commit()
    assert validate_url_download('', '', secret_token, True) == (
        False, 'This URL has been deactivated.')
    secret_obj.is_deleted = False
    secret_obj.download_count = 10
    db.session.commit()
    assert validate_url_download('', '', secret_token, True) == (
        False, 'The download limit has been exceeded.')
    secret_obj.download_count = 0
    db.session.commit()
    with patch('weko_records_ui.utils.dt') as mock_dt:
        mock_dt.now.return_value = dt.now(timezone.utc) + timedelta(days=31)
        assert validate_url_download('', '', secret_token, True) == (
            False, 'The expiration date for download has been exceeded.')

    onetime_obj.is_deleted = True
    db.session.commit()
    assert validate_url_download('', '', onetime_token, False) == (
        False, 'This URL has been deactivated.')
    onetime_obj.is_deleted = False
    onetime_obj.download_count = 10
    db.session.commit()
    assert validate_url_download('', '', onetime_token, False) == (
        False, 'The download limit has been exceeded.')
    onetime_obj.download_count = 0
    db.session.commit()
    with patch('weko_records_ui.utils.dt') as mock_dt:
        mock_dt.now.return_value = dt.now(timezone.utc) + timedelta(days=31)
        assert validate_url_download('', '', onetime_token, False) == (
            False, 'The expiration date for download has been exceeded.')


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_validate_file_access -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
def test_validate_file_access():
    with patch('weko_records_ui.utils.is_secret_file', return_value=True):
        assert validate_file_access('', '', is_secret_url=True) is True
    with patch('weko_records_ui.utils.is_secret_file', return_value=False):
        assert validate_file_access('', '', is_secret_url=True) is False
    with patch('weko_records_ui.utils.is_onetime_file', return_value=True):
        assert validate_file_access('', '', is_secret_url=False) is True
    with patch('weko_records_ui.utils.is_onetime_file', return_value=False):
        assert validate_file_access('', '', is_secret_url=False) is False


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_is_onetime_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
def test_is_onetime_file():
    mock_record = MagicMock()
    mock_record.get_file_data.return_value = [
        {"filename": "file1.txt", "accessrole": "open_restricted"},
        {"filename": "file2.txt", "accessrole": "public"}
    ]
    assert is_onetime_file(mock_record, "file1.txt") is True
    assert is_onetime_file(mock_record, "file2.txt") is False
    assert is_onetime_file(mock_record, "file3.txt") is False


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_RoCrateConverter_convert -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_RoCrateConverter_convert(app, db):
    with open('tests/data/rocrate/rocrate_mapping.json', 'r') as f:
        mapping = json.load(f)
    with open('tests/data/rocrate/records_metadata.json', 'r') as f:
        record_data = json.load(f)
    converter = RoCrateConverter()
    rocrate = converter.convert(record_data, mapping)
    assert rocrate
    assert type(rocrate) == dict

    with open('tests/data/rocrate/test_mapping_rocrate_mapping.json', 'r') as f:
        mapping = json.load(f)
    with open('tests/data/rocrate/test_mapping_records_metadata.json', 'r') as f:
        record_data = json.load(f)
    rocrate = converter.convert(record_data, mapping)
    assert rocrate['@graph'][0]['prop1'] == 'value1'
    assert rocrate['@graph'][0]['prop2'] == ['value2']
    assert rocrate['@graph'][0]['prop3'] == ['value3_1', 'value3_2']
    assert rocrate['@graph'][0]['prop4_1'] == 'value4_1'
    assert rocrate['@graph'][0]['prop4_2'] == 'value4_2'
    assert 'prop4_3' not in rocrate['@graph'][0]
    assert rocrate['@graph'][0]['prop5'] == ['value5_1', 'value5_2', 'value5_3']
    assert rocrate['@graph'][0]['prop6'] == ['value6_2']
    assert rocrate['@graph'][0]['prop7'] == ['value7_1']
    assert 'prop8' not in rocrate['@graph'][0]
    assert 'prop9' not in rocrate['@graph'][0]
    assert rocrate['@graph'][0]['prop10'] == ['value10_1_en', 'value10_2_1_en']
    assert rocrate['@graph'][0]['prop_static'] == 'value_static'
    assert 'prop_none' not in rocrate['@graph'][0]
    assert 'prop_none_lang' not in rocrate['@graph'][0]

    assert rocrate['@graph'][5]['name'] == 'name_en'
    assert rocrate['@graph'][5]['additionalType'] == 'tab'
    assert rocrate['@graph'][2]['fileprop1'] == 'filevalue1_1'
    assert rocrate['@graph'][2]['fileprop2'] == 'filevalue2_1'
    assert rocrate['@graph'][2]['fileprop3'] == ['filevalue3_1_1', 'filevalue3_2_1_1_1', 'filevalue3_2_1_1_2']
    assert rocrate['@graph'][2]['fileprop_static'] == 'filevalue_static'
    assert rocrate['@graph'][3]['fileprop1'] == 'filevalue1_2'
    assert rocrate['@graph'][3]['fileprop2'] == 'filevalue2_2'
    assert rocrate['@graph'][3]['fileprop3'] == ['filevalue3_1_2', 'filevalue3_2_1_2_1', 'filevalue3_2_1_2_2']
    assert rocrate['@graph'][3]['fileprop_static'] == 'filevalue_static'
    assert rocrate['@graph'][4]['fileprop1'] == 'filevalue1_3'
    assert rocrate['@graph'][4]['fileprop2'] == 'filevalue2_3'
    assert rocrate['@graph'][4]['fileprop3'] == ['filevalue3_1_3', 'filevalue3_2_1_3_1', 'filevalue3_2_1_3_2']
    assert rocrate['@graph'][4]['fileprop_static'] == 'filevalue_static'

    rocrate = converter.convert(record_data, mapping, 'ja')
    assert rocrate['@graph'][0]['prop6'] == ['value6_3']
    assert rocrate['@graph'][0]['prop7'] == ['value7_2']
    assert rocrate['@graph'][0]['prop10'] == ['value10_1_ja', 'value10_2_1_ja']
    assert rocrate['@graph'][5]['name'] == 'name_ja'

    rocrate = converter.convert(record_data, mapping, 'other')
    assert rocrate['@graph'][0]['prop6'] == ['value6_2']
    assert rocrate['@graph'][0]['prop7'] == ['value7_1']
    assert rocrate['@graph'][0]['prop10'] == ['value10_1_en', 'value10_2_1_en']
    assert rocrate['@graph'][5]['name'] == 'name'


# def create_tsv(files, language='en'):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_create_tsv -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_create_tsv(app, records):
    from weko_records_ui.config import (
        WEKO_RECORDS_UI_TSV_FIELD_NAMES_DEFAULT,
        WEKO_RECORDS_UI_TSV_FIELD_NAMES_EN,
        WEKO_RECORDS_UI_TSV_FIELD_NAMES_JA,
    )
    indexer, results = records
    record = results[0]["record"]

    # 16 set language en
    res_tsv = create_tsv(record.files, 'en')
    for field in WEKO_RECORDS_UI_TSV_FIELD_NAMES_EN:
        assert field in res_tsv.getvalue()

    # 17 set language ja
    res_tsv = create_tsv(record.files, 'ja')
    for field in WEKO_RECORDS_UI_TSV_FIELD_NAMES_JA:
        assert field in res_tsv.getvalue()

    # 18 shortage of fieldnames
    fieldnames = ['名前', 'サイズ', 'ライセンス']
    with patch("weko_records_ui.config.WEKO_RECORDS_UI_TSV_FIELD_NAMES_EN", fieldnames):
        res_tsv = create_tsv(record.files)
        for field in fieldnames:
            assert field in res_tsv.getvalue()
        assert WEKO_RECORDS_UI_TSV_FIELD_NAMES_DEFAULT[3] in res_tsv.getvalue()
        assert WEKO_RECORDS_UI_TSV_FIELD_NAMES_DEFAULT[4] in res_tsv.getvalue()

    # 19 not exist fieldnames
    with patch("weko_records_ui.config.WEKO_RECORDS_UI_TSV_FIELD_NAMES_EN", None):
        res_tsv = create_tsv(record.files)
        for field in WEKO_RECORDS_UI_TSV_FIELD_NAMES_DEFAULT:
            assert field in res_tsv.getvalue()

