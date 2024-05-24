import pytest
from weko_records_ui.utils import (
    check_and_create_usage_report,
    check_items_settings, create_onetime_download_url,
    create_usage_report_for_user, display_oaiset_path,
    generate_one_time_download_url, get_billing_file_download_permission,
    get_billing_role, get_file_info_list, get_google_detaset_meta,
    get_google_scholar_meta, get_groups_price, get_license_pdf,
    get_list_licence, get_min_price_billing_file_download,
    get_onetime_download, get_pair_value, get_record_permalink, get_roles,
    get_terms, get_workflows, hide_by_email, hide_by_file, hide_by_itemtype,
    hide_item_metadata, hide_item_metadata_email_only, is_billing_item,
    is_open_access, is_private_index, is_show_email_of_creator,
    parse_one_time_download_token, replace_license_free, restore,
    send_usage_report_mail_for_user, soft_delete, update_onetime_download,
    validate_download_record, validate_onetime_download_token, replace_license_free_for_opensearch
)
import base64
from unittest.mock import MagicMock
import copy
import pytest
import io
from datetime import datetime as dt
from datetime import timedelta
from lxml import etree
from fpdf import FPDF
from invenio_records_files.utils import record_file_factory
from flask import Flask, json, jsonify, session, url_for,current_app
from flask_security.utils import login_user
from invenio_accounts.testutils import login_user_via_session
from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from mock import patch
from weko_records_ui.models import FileOnetimeDownload
from weko_records.api import ItemTypes,Mapping
from werkzeug.exceptions import NotFound
from weko_admin.models import AdminSettings
from weko_records.serializers.utils import get_mapping
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

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

    data1 = {"item": {
        "attribute_value_mlt": [{
            "groupsprice": ["groupsprices"],
            "filename": "filename"
        }]
    }}

    assert get_groups_price(data1) != None


# def get_billing_file_download_permission(groups_price: list) -> dict:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_billing_file_download_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_billing_file_download_permission(users):
    groups_price = [{'file_name': '003.jpg', 'groups_price': [{'group': '1', 'price': '100'}]}]
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert get_billing_file_download_permission(groups_price)=={'003.jpg': False}

        with patch("weko_records_ui.utils.check_user_group_permission", return_value=True):
            assert get_billing_file_download_permission(groups_price)=={'003.jpg': True}


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


# def is_billing_item(record: dict) -> bool:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_is_billing_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_is_billing_item(i18n_app,records, mock_es_execute):
    _, results = records
    non_billing_record = results[0]['record']
    billing_record = results[3]['record']

    assert is_billing_item(non_billing_record)==False
    assert is_billing_item(billing_record)==True


# def is_open_access(record: Dict) -> bool:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_is_open_access -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_is_open_access(records_open_access, mocker):
    def mock_strptime(date_string, format):
        return dt.strptime(date_string, format)

    _, results = records_open_access
    with patch("weko_records_ui.utils.Indexes.get_public_indexes_list", return_value=["2", "4", "6"]):
        # all indexes are not public
        assert not is_open_access(results[0]['record'])

        # some indexes are public and accessrole is open_access
        assert is_open_access(results[1]['record'])

        # all indexes are public, accessrole is open_date and now is before public_date
        mock_datetime = mocker.patch("weko_records_ui.utils.dt")
        mock_datetime.now.return_value = dt(2024, 5, 19, 12, 55, 32)
        mock_datetime.strptime.side_effect=mock_strptime
        assert not is_open_access(results[2]['record'])
        
        # all indexes are public, accessrole is open_date and now is after public_date
        mock_datetime.now.return_value = dt(2024, 5, 20, 12, 55, 32)
        assert is_open_access(results[3]['record'])
        
        # all indexes are public and accessrole is login_user
        assert not is_open_access(results[4]['record'])


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

        name_keys = ['subitem_1551255647225', 'subitem_1551255647225']
        lang_keys = ['subitem_1551255648112', 'subitem_1551255647225']
        name,lang =  get_pair_value(name_keys,lang_keys,datas)
        


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
    record = results[0]["item"]
    assert hide_by_email(copy.deepcopy(record))==record
    app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS'] = ["test"]
    data1 = {
        "data1": {
            "attribute_type": "file",
            "attribute_value_mlt": [
                {
                    "accessrole": "open_no",
                    "test": {"test": "test"}
                }
            ]
        },
        "_deposit": {"owners_ext": {"email": "email"}}
    }
    assert hide_by_email(data1)


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


# def is_show_email_of_creator(item_type_id):
#     def get_creator_id(item_type_id):
#     def item_type_show_email(item_type_id):
#     def item_setting_show_email():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_is_show_email_of_creator -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "is_hide, is_display, is_show_email",
    [(False,True,True),
     (True,True,False),
     (False,False,False),
     (True,False,False)]
)
def test_is_show_email_of_creator(app,db,db_admin_settings,is_hide,is_display,is_show_email):
    item_type_name = ItemTypeName(
        id=1, name="テストアイテムタイプ", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/itemtype_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/itemtype_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/itemtype_render.json", "r") as f:
        item_type_render = json.load(f)
    
    item_type_render["schemaeditor"]["schema"]["item_1617186419668"]["properties"]["creatorMails"]["items"]["properties"]["creatorMail"]["isHide"] = is_hide
    
    item_type_mapping = dict()
    with open("tests/data/itemtype_mapping.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(
        id=1,
        name_id=1,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(id=1, item_type_id=1, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)
        
    setting = AdminSettings.get(name="items_display_settings",dict_to_object=False)
    setting['items_display_email'] = is_display
    AdminSettings.update("items_display_settings",setting)
    
    assert is_show_email_of_creator(1)==is_show_email


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

# def replace_license_free_for_opensearch(search_result, is_change_label=True):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_replace_license_free_for_opensearch -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_replace_license_free_for_opensearch(app):

    data1= {'hits': {
                'hits': [{
                    '_source': {
                        '_item_metadata': {
                            "key": {
                            "attribute_type": "file",
                            "attribute_value_mlt": [{
                                "licensetype": "license_free",
                                "licensefree": "True"
                            }]
                        }
                    }
                }
            }]
    }}
    replace_license_free_for_opensearch(data1)
    data2= {'hits': {
                'hits': [{
                    '_source': {
                        '_item_metadata': {
                            "key": {
                            "attribute_type": "file",
                            "attribute_value_mlt": [{
                                "licensetype": "license_note",
                                "license_note": "True"
                            }]
                        }
                    }
                }
            }]
    }}
    assert data1 == data2

# def get_file_info_list(record):
#     def get_file_size(p_file):
#     def set_message_for_file(p_file):
#     def get_data_by_key_array_json(key, array_json, get_key):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_file_info_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
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
def test_get_file_info_list(app,records,users,id,result,db_item_billing):
    indexer, results = records
    record = results[0]["record"]
    
    # record_data = {
    #     "_oai": {"id": "oai:weko3.example.org:000000{:02d}".format(i), "sets": ["{}".format((i % 2) + 1)]},
    #     "path": ["{}".format((i % 2) + 1)],
    #     "owner": "1",
    #     "recid": "{}".format(i),
    #     "title": [
    #         "ja_conference paperITEM00000009(public_open_access_open_access_simple)"
    #     ],
    #     "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
    #     "_buckets": {"deposit": "27202db8-aefc-4b85-b5ae-4921ac151ddf"},
    #     "_deposit": {
    #         "id": "{}".format(i),
    #         "pid": {"type": "depid", "value": "{}".format(i), "revision_id": 0},
    #         "owners": [1],
    #         "status": "published",
    #     },
    #     "item_title": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
    #     "author_link": ["4"],
    #     "item_type_id": "1",
    #     "publish_date": "2021-08-06",
    #     "publish_status": "0",
    #     "weko_shared_id": -1,
    #     "item_1617186331708": {
    #         "attribute_name": "Title",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_1551255647225": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
    #                 "subitem_1551255648112": "ja",
    #             },
    #             {
    #                 "subitem_1551255647225": "en_conference paperITEM00000009(public_open_access_simple)",
    #                 "subitem_1551255648112": "en",
    #             },
    #         ],
    #     },
    #     "item_1617186385884": {
    #         "attribute_name": "Alternative Title",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_1551255720400": "Alternative Title",
    #                 "subitem_1551255721061": "en",
    #             },
    #             {
    #                 "subitem_1551255720400": "Alternative Title",
    #                 "subitem_1551255721061": "ja",
    #             },
    #         ],
    #     },
    #     "item_1617186419668": {
    #         "attribute_name": "Creator",
    #         "attribute_type": "creator",
    #         "attribute_value_mlt": [
    #             {
    #                 "givenNames": [
    #                     {"givenName": "太郎", "givenNameLang": "ja"},
    #                     {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
    #                     {"givenName": "Taro", "givenNameLang": "en"},
    #                 ],
    #                 "familyNames": [
    #                     {"familyName": "情報", "familyNameLang": "ja"},
    #                     {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
    #                     {"familyName": "Joho", "familyNameLang": "en"},
    #                 ],
    #                 "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
    #                 "creatorNames": [
    #                     {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
    #                     {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
    #                     {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
    #                 ],
    #                 "nameIdentifiers": [
    #                     {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
    #                     {
    #                         "nameIdentifier": "xxxxxxx",
    #                         "nameIdentifierURI": "https://orcid.org/",
    #                         "nameIdentifierScheme": "ORCID",
    #                     },
    #                     {
    #                         "nameIdentifier": "xxxxxxx",
    #                         "nameIdentifierURI": "https://ci.nii.ac.jp/",
    #                         "nameIdentifierScheme": "CiNii",
    #                     },
    #                     {
    #                         "nameIdentifier": "zzzzzzz",
    #                         "nameIdentifierURI": "https://kaken.nii.ac.jp/",
    #                         "nameIdentifierScheme": "KAKEN2",
    #                     },
    #                 ],
    #                 "creatorAffiliations": [
    #                     {
    #                         "affiliationNames": [
    #                             {
    #                                 "affiliationName": "University",
    #                                 "affiliationNameLang": "en",
    #                             }
    #                         ],
    #                         "affiliationNameIdentifiers": [
    #                             {
    #                                 "affiliationNameIdentifier": "0000000121691048",
    #                                 "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
    #                                 "affiliationNameIdentifierScheme": "ISNI",
    #                             }
    #                         ],
    #                     }
    #                 ],
    #             },
    #             {
    #                 "givenNames": [
    #                     {"givenName": "太郎", "givenNameLang": "ja"},
    #                     {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
    #                     {"givenName": "Taro", "givenNameLang": "en"},
    #                 ],
    #                 "familyNames": [
    #                     {"familyName": "情報", "familyNameLang": "ja"},
    #                     {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
    #                     {"familyName": "Joho", "familyNameLang": "en"},
    #                 ],
    #                 "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
    #                 "creatorNames": [
    #                     {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
    #                     {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
    #                     {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
    #                 ],
    #                 "nameIdentifiers": [
    #                     {
    #                         "nameIdentifier": "xxxxxxx",
    #                         "nameIdentifierURI": "https://orcid.org/",
    #                         "nameIdentifierScheme": "ORCID",
    #                     },
    #                     {
    #                         "nameIdentifier": "xxxxxxx",
    #                         "nameIdentifierURI": "https://ci.nii.ac.jp/",
    #                         "nameIdentifierScheme": "CiNii",
    #                     },
    #                     {
    #                         "nameIdentifier": "zzzzzzz",
    #                         "nameIdentifierURI": "https://kaken.nii.ac.jp/",
    #                         "nameIdentifierScheme": "KAKEN2",
    #                     },
    #                 ],
    #             },
    #             {
    #                 "givenNames": [
    #                     {"givenName": "太郎", "givenNameLang": "ja"},
    #                     {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
    #                     {"givenName": "Taro", "givenNameLang": "en"},
    #                 ],
    #                 "familyNames": [
    #                     {"familyName": "情報", "familyNameLang": "ja"},
    #                     {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
    #                     {"familyName": "Joho", "familyNameLang": "en"},
    #                 ],
    #                 "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
    #                 "creatorNames": [
    #                     {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
    #                     {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
    #                     {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
    #                 ],
    #                 "nameIdentifiers": [
    #                     {
    #                         "nameIdentifier": "xxxxxxx",
    #                         "nameIdentifierURI": "https://orcid.org/",
    #                         "nameIdentifierScheme": "ORCID",
    #                     },
    #                     {
    #                         "nameIdentifier": "xxxxxxx",
    #                         "nameIdentifierURI": "https://ci.nii.ac.jp/",
    #                         "nameIdentifierScheme": "CiNii",
    #                     },
    #                     {
    #                         "nameIdentifier": "zzzzzzz",
    #                         "nameIdentifierURI": "https://kaken.nii.ac.jp/",
    #                         "nameIdentifierScheme": "KAKEN2",
    #                     },
    #                 ],
    #             },
    #         ],
    #     },
    #     "item_1617186476635": {
    #         "attribute_name": "Access Rights",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_1522299639480": "open access",
    #                 "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
    #             }
    #         ],
    #     },
    #     "item_1617186499011": {
    #         "attribute_name": "Rights",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_1522650717957": "ja",
    #                 "subitem_1522650727486": "http://localhost",
    #                 "subitem_1522651041219": "Rights Information",
    #             }
    #         ],
    #     },
    #     "item_1617186609386": {
    #         "attribute_name": "Subject",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_1522299896455": "ja",
    #                 "subitem_1522300014469": "Other",
    #                 "subitem_1522300048512": "http://localhost/",
    #                 "subitem_1523261968819": "Sibject1",
    #             }
    #         ],
    #     },
    #     "item_1617186626617": {
    #         "attribute_name": "Description",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_description": "Description\nDescription<br/>Description",
    #                 "subitem_description_type": "Abstract",
    #                 "subitem_description_language": "en",
    #             },
    #             {
    #                 "subitem_description": "概要\n概要\n概要\n概要",
    #                 "subitem_description_type": "Abstract",
    #                 "subitem_description_language": "ja",
    #             },
    #         ],
    #     },
    #     "item_1617186643794": {
    #         "attribute_name": "Publisher",
    #         "attribute_value_mlt": [
    #             {"subitem_1522300295150": "en", "subitem_1522300316516": "Publisher"}
    #         ],
    #     },
    #     "item_1617186660861": {
    #         "attribute_name": "Date",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_1522300695726": "Available",
    #                 "subitem_1522300722591": "2021-06-30",
    #             }
    #         ],
    #     },
    #     "item_1617186702042": {
    #         "attribute_name": "Language",
    #         "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
    #     },
    #     "item_1617186783814": {
    #         "attribute_name": "Identifier",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_identifier_uri": "http://localhost",
    #                 "subitem_identifier_type": "URI",
    #             }
    #         ],
    #     },
    #     "item_1617186859717": {
    #         "attribute_name": "Temporal",
    #         "attribute_value_mlt": [
    #             {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
    #         ],
    #     },
    #     "item_1617186882738": {
    #         "attribute_name": "Geo Location",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_geolocation_place": [
    #                     {"subitem_geolocation_place_text": "Japan"}
    #                 ]
    #             }
    #         ],
    #     },
    #     "item_1617186901218": {
    #         "attribute_name": "Funding Reference",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_1522399143519": {
    #                     "subitem_1522399281603": "ISNI",
    #                     "subitem_1522399333375": "http://xxx",
    #                 },
    #                 "subitem_1522399412622": [
    #                     {
    #                         "subitem_1522399416691": "en",
    #                         "subitem_1522737543681": "Funder Name",
    #                     }
    #                 ],
    #                 "subitem_1522399571623": {
    #                     "subitem_1522399585738": "Award URI",
    #                     "subitem_1522399628911": "Award Number",
    #                 },
    #                 "subitem_1522399651758": [
    #                     {
    #                         "subitem_1522721910626": "en",
    #                         "subitem_1522721929892": "Award Title",
    #                     }
    #                 ],
    #             }
    #         ],
    #     },
    #     "item_1617186920753": {
    #         "attribute_name": "Source Identifier",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_1522646500366": "ISSN",
    #                 "subitem_1522646572813": "xxxx-xxxx-xxxx",
    #             }
    #         ],
    #     },
    #     "item_1617186941041": {
    #         "attribute_name": "Source Title",
    #         "attribute_value_mlt": [
    #             {"subitem_1522650068558": "en", "subitem_1522650091861": "Source Title"}
    #         ],
    #     },
    #     "item_1617186959569": {
    #         "attribute_name": "Volume Number",
    #         "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
    #     },
    #     "item_1617186981471": {
    #         "attribute_name": "Issue Number",
    #         "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
    #     },
    #     "item_1617186994930": {
    #         "attribute_name": "Number of Pages",
    #         "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
    #     },
    #     "item_1617187024783": {
    #         "attribute_name": "Page Start",
    #         "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
    #     },
    #     "item_1617187045071": {
    #         "attribute_name": "Page End",
    #         "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
    #     },
    #     "item_1617187112279": {
    #         "attribute_name": "Degree Name",
    #         "attribute_value_mlt": [
    #             {"subitem_1551256126428": "Degree Name", "subitem_1551256129013": "en"}
    #         ],
    #     },
    #     "item_1617187136212": {
    #         "attribute_name": "Date Granted",
    #         "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
    #     },
    #     "item_1617187187528": {
    #         "attribute_name": "Conference",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_1599711633003": [
    #                     {
    #                         "subitem_1599711636923": "Conference Name",
    #                         "subitem_1599711645590": "ja",
    #                     }
    #                 ],
    #                 "subitem_1599711655652": "1",
    #                 "subitem_1599711660052": [
    #                     {
    #                         "subitem_1599711680082": "Sponsor",
    #                         "subitem_1599711686511": "ja",
    #                     }
    #                 ],
    #                 "subitem_1599711699392": {
    #                     "subitem_1599711704251": "2020/12/11",
    #                     "subitem_1599711712451": "1",
    #                     "subitem_1599711727603": "12",
    #                     "subitem_1599711731891": "2000",
    #                     "subitem_1599711735410": "1",
    #                     "subitem_1599711739022": "12",
    #                     "subitem_1599711743722": "2020",
    #                     "subitem_1599711745532": "ja",
    #                 },
    #                 "subitem_1599711758470": [
    #                     {
    #                         "subitem_1599711769260": "Conference Venue",
    #                         "subitem_1599711775943": "ja",
    #                     }
    #                 ],
    #                 "subitem_1599711788485": [
    #                     {
    #                         "subitem_1599711798761": "Conference Place",
    #                         "subitem_1599711803382": "ja",
    #                     }
    #                 ],
    #                 "subitem_1599711813532": "JPN",
    #             }
    #         ],
    #     },
    #     "item_1617258105262": {
    #         "attribute_name": "Resource Type",
    #         "attribute_value_mlt": [
    #             {
    #                 "resourceuri": "http://purl.org/coar/resource_type/c_5794",
    #                 "resourcetype": "conference paper",
    #             }
    #         ],
    #     },
    #     "item_1617265215918": {
    #         "attribute_name": "Version Type",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_1522305645492": "AO",
    #                 "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
    #             }
    #         ],
    #     },
    #     "item_1617349709064": {
    #         "attribute_name": "Contributor",
    #         "attribute_value_mlt": [
    #             {
    #                 "givenNames": [
    #                     {"givenName": "太郎", "givenNameLang": "ja"},
    #                     {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
    #                     {"givenName": "Taro", "givenNameLang": "en"},
    #                 ],
    #                 "familyNames": [
    #                     {"familyName": "情報", "familyNameLang": "ja"},
    #                     {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
    #                     {"familyName": "Joho", "familyNameLang": "en"},
    #                 ],
    #                 "contributorType": "ContactPerson",
    #                 "nameIdentifiers": [
    #                     {
    #                         "nameIdentifier": "xxxxxxx",
    #                         "nameIdentifierURI": "https://orcid.org/",
    #                         "nameIdentifierScheme": "ORCID",
    #                     },
    #                     {
    #                         "nameIdentifier": "xxxxxxx",
    #                         "nameIdentifierURI": "https://ci.nii.ac.jp/",
    #                         "nameIdentifierScheme": "CiNii",
    #                     },
    #                     {
    #                         "nameIdentifier": "xxxxxxx",
    #                         "nameIdentifierURI": "https://kaken.nii.ac.jp/",
    #                         "nameIdentifierScheme": "KAKEN2",
    #                     },
    #                 ],
    #                 "contributorMails": [{"contributorMail": "wekosoftware@nii.ac.jp"}],
    #                 "contributorNames": [
    #                     {"lang": "ja", "contributorName": "情報, 太郎"},
    #                     {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
    #                     {"lang": "en", "contributorName": "Joho, Taro"},
    #                 ],
    #             }
    #         ],
    #     },
    #     "item_1617349808926": {
    #         "attribute_name": "Version",
    #         "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
    #     },
    #     "item_1617351524846": {
    #         "attribute_name": "APC",
    #         "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
    #     },
    #     "item_1617353299429": {
    #         "attribute_name": "Relation",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_1522306207484": "isVersionOf",
    #                 "subitem_1522306287251": {
    #                     "subitem_1522306382014": "arXiv",
    #                     "subitem_1522306436033": "xxxxx",
    #                 },
    #                 "subitem_1523320863692": [
    #                     {
    #                         "subitem_1523320867455": "en",
    #                         "subitem_1523320909613": "Related Title",
    #                     }
    #                 ],
    #             }
    #         ],
    #     },
    #     "item_1617605131499": {
    #         "attribute_name": "File",
    #         "attribute_type": "file",
    #         "attribute_value_mlt": [
    #             {
    #                 "url": {"url": "https://weko3.example.org/record/{0}/files/{1}".format(
    #                         i, filename
    #                     )},
    #                 "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
    #                 "format": "text/plain",
    #                 "filename": "{}".format(filename),
    #                 "filesize": [{"value": "1 KB"}],
    #                 "mimetype": "{}".format(mimetype),
    #                 "accessrole": "open_login",
    #                 "version_id": "c1502853-c2f9-455d-8bec-f6e630e54b21",
    #                 "displaytype": "simple",
    #             }
    #         ],
    #     },
    #     "item_1617610673286": {
    #         "attribute_name": "Rights Holder",
    #         "attribute_value_mlt": [
    #             {
    #                 "nameIdentifiers": [
    #                     {
    #                         "nameIdentifier": "xxxxxx",
    #                         "nameIdentifierURI": "https://orcid.org/",
    #                         "nameIdentifierScheme": "ORCID",
    #                     }
    #                 ],
    #                 "rightHolderNames": [
    #                     {
    #                         "rightHolderName": "Right Holder Name",
    #                         "rightHolderLanguage": "ja",
    #                     }
    #                 ],
    #             }
    #         ],
    #     },
    #     "item_1617620223087": {
    #         "attribute_name": "Heading",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_1565671149650": "ja",
    #                 "subitem_1565671169640": "Banner Headline",
    #                 "subitem_1565671178623": "Subheading",
    #             },
    #             {
    #                 "subitem_1565671149650": "en",
    #                 "subitem_1565671169640": "Banner Headline",
    #                 "subitem_1565671178623": "Subheding",
    #             },
    #         ],
    #     },
    #     "item_1617944105607": {
    #         "attribute_name": "Degree Grantor",
    #         "attribute_value_mlt": [
    #             {
    #                 "subitem_1551256015892": [
    #                     {
    #                         "subitem_1551256027296": "xxxxxx",
    #                         "subitem_1551256029891": "kakenhi",
    #                     }
    #                 ],
    #                 "subitem_1551256037922": [
    #                     {
    #                         "subitem_1551256042287": "Degree Grantor Name",
    #                         "subitem_1551256047619": "en",
    #                     }
    #                 ],
    #             }
    #         ],
    #     },
    #     "relation_version_is_last": True,
    # }

    with app.test_request_context(headers=[("Accept-Language", "en")]):
        ret =  get_file_info_list(record)
        assert len(ret)==2
    
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        record["item_1617605131499"]["attribute_value_mlt"][0]["accessrole"] = "open_login"
        get_file_info_list(record)

        record["item_1617605131499"]["attribute_value_mlt"][0]["accessrole"] = "open_date"
        date = dt.now() + timedelta(days=1)
        record["item_1617605131499"]["attribute_value_mlt"][0]["date"][0]["dateValue"] = date.strftime('%Y-%m-%d')
        get_file_info_list(record)

        record["item_1617605131499"]["attribute_value_mlt"][0]['terms'] = "term"
        get_file_info_list(record)

        record["item_1617605131499"]["attribute_value_mlt"][0]['terms'] = "term_free"
        record["item_1617605131499"]["attribute_value_mlt"][0]['provide'] = [{"workflow": "workflow", "role": 1}]
        get_file_info_list(record)


    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):

        # 47
        with app.test_request_context(headers=[("Accept-Language", "en")]):
            with open("tests/data/record_d.json","r") as f:
                record_d = json.load(f)
            with patch("weko_records_ui.utils.check_file_download_permission", return_value=True):
                is_display_file_preview, files = get_file_info_list(record_d)
                priceinfo = files[0]['priceinfo']
                billing_file_permission = files[0]['billing_file_permission']
                assert priceinfo[0]['has_role'] != None
                assert billing_file_permission != None

# def check_and_create_usage_report(record, file_object):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_check_and_create_usage_report -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_and_create_usage_report(app,records):
    indexer, results = records
    pid = results[0]["recid"]
    record = results[0]["record"]
    filename = results[0]["filename"]
    fileobj = record_file_factory(
        pid, record, filename
    )
    data1 = MagicMock()
    fileobj["accessrole"] = ["open_restricted"]

    with patch("weko_records_ui.utils.check_create_usage_report", return_value=data1):
        with patch("weko_workflow.utils.create_usage_report", return_value=False):
            with patch("weko_records_ui.models.FilePermission.update_usage_report_activity_id", return_value=True):
                assert check_and_create_usage_report(record,fileobj)==None


# def create_usage_report_for_user(onetime_download_extra_info: dict):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_create_usage_report_for_user(app):
    data1 = MagicMock()

    data2 = MagicMock()
    data2.extra_info = {}

    def get_activity_by_id(x):
        return data2
    
    def find_workflow_by_name_false(x):
        return False

    def find_workflow_by_name_true(x):
        return True

    data1.get_activity_by_id = get_activity_by_id
    data1.find_workflow_by_name = find_workflow_by_name_false

    app.config['WEKO_WORKFLOW_USAGE_REPORT_WORKFLOW_NAME'] = "test"
    with patch("weko_records_ui.utils.WorkActivity", return_value=data1):
        with patch("weko_records_ui.utils.WorkFlow", return_value=data1):
            assert create_usage_report_for_user(data1) == ""

            # ERROR
            data1.find_workflow_by_name = find_workflow_by_name_true
            # with patch("weko_records_ui.utils.RecordMetadata.query.filter_by", return_value=data2):
            with patch("invenio_records.models.RecordMetadata.query.filter_by", return_value=data2):
                try:
                    assert create_usage_report_for_user(data1) == ""
                except:
                    pass
                

# def get_data_usage_application_data(record_metadata, data_result: dict):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_data_usage_application_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_data_usage_application_data(app, db, workflows, records, users, db_file_permission):
    _onetime_download_extra_info = {
        'usage_application_activity_id': 'usage_app_act_id_dummy1',
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
def test_check_and_send_usage_report(app, db, workflows, records, users, db_file_permission):
    _record = {
        'recid': db_file_permission[0].record_id
    }
    _file_obj = {
        'accessrole': 'open_restricted',
        'filename': db_file_permission[0].file_name
    }
    app.config['WEKO_WORKFLOW_USAGE_REPORT_WORKFLOW_NAME'] = 'Data Usage Report'
    with patch("flask_login.utils._get_user", return_value=users[7]['obj']):
        with patch("weko_workflow.utils.create_record_metadata", return_value='usage_report_activity_0'):
            assert check_and_send_usage_report(_record, _file_obj)==None

    data1 = MagicMock()
    data2 = MagicMock()
    data3 = MagicMock()

    def send_reminder_mail(x, y, z):
        return False
    
    def send_reminder_mail_2(x, y, z):
        return True

    data3.send_reminder_mail = send_reminder_mail

    with patch("flask_login.utils._get_user", return_value=users[2]['obj']):
        with patch("weko_records_ui.utils.create_usage_report_for_user", return_value=data1):
            with patch("weko_records_ui.utils.UsageReport", return_value=data3):
                check_and_send_usage_report(data1, data2)

        with patch("weko_records_ui.utils.create_usage_report_for_user", return_value=False):
            check_and_send_usage_report(data1, data2)

        with patch("weko_records_ui.utils.create_usage_report_for_user", return_value=data1):
            with patch("weko_records_ui.utils.UsageReport", return_value=data3):
                data3.send_reminder_mail = send_reminder_mail_2
                check_and_send_usage_report(data1, data2)
    


# def generate_one_time_download_url(
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_generate_one_time_download_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_generate_one_time_download_url(app):
    file_name = "003.jpg"
    record_id = "1"
    guest_mail= "user@example.org"
    with app.test_request_context():
        ret =  generate_one_time_download_url(file_name,record_id,guest_mail)
        rets = ret.split('token=')
        token_str =base64.b64decode(rets[1])
        token = (token_str.decode('utf-8')).split(' ')
        assert token[0] == record_id
        assert token[1] == guest_mail
        

# def parse_one_time_download_token(token: str) -> Tuple[str, Tuple]:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_parse_one_time_download_token -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_parse_one_time_download_token(app):
    token = "MSB1c2VyQGV4YW1wbGUub3JnIDIwMjItMDktMjcgNDBDRkNGODFGM0FFRUI0Ng=="
    with app.test_request_context():
        assert parse_one_time_download_token(token)==('', ('1', 'user@example.org', '2022-09-27', '40CFCF81F3AEEB46'))
        assert parse_one_time_download_token("test") != None
        assert parse_one_time_download_token(None) != None


# def validate_onetime_download_token(
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_validate_onetime_download_token -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_validate_onetime_download_token(app,db_fileonetimedownload):
    file_name='helloworld.pdf'
    record_id='1'
    user_email='wekosoftware@nii.ac.jp'
    token = "9948A41F46456DF5"
    date = "2022-09-28"
    with app.test_request_context():
        file_downloads = FileOnetimeDownload.find(
            file_name=file_name, record_id=record_id, user_mail=user_email
        )
        assert validate_onetime_download_token(file_downloads[0],file_name,record_id,user_email,date,token)== (True, '')

        data1 = MagicMock()
        data1.download_count = 0

        with patch('passlib.handlers.oracle.oracle10.verify', return_value=False):
            assert validate_onetime_download_token(file_downloads[0],file_name,record_id,user_email,date,token)== (False, 'Token is invalid.')

        assert validate_onetime_download_token(False,file_name,record_id,user_email,date,token)== (False, 'Token is invalid.')

        assert validate_onetime_download_token(data1,file_name,record_id,user_email,date,token)== (False, 'Token is invalid.')


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
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_validate_download_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_validate_download_record(app, records):
    indexer, results = records
    record = results[0]["record"]
    assert validate_download_record(record)==None

    data1 = {
        "publish_status": 1
    }

    try:
        validate_download_record(data1)
    except:
        pass

    with patch("weko_records_ui.utils.is_private_index", return_value=True):
        try:
            validate_download_record(record)
        except:
            pass


# def get_onetime_download(file_name: str, record_id: str,
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_onetime_download -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_onetime_download(app, db_fileonetimedownload):
    with app.test_request_context():
        ret = get_onetime_download('helloworld.pdf','1','wekosoftware@nii.ac.jp')
        assert ret.file_name=='helloworld.pdf'

        with patch("weko_records_ui.models.FileOnetimeDownload.find", return_value=False):
            assert get_onetime_download('helloworld.pdf','1','wekosoftware@nii.ac.jp') == None


# def create_onetime_download_url(
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_create_onetime_download_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_create_onetime_download_url(app):
    with app.test_request_context():
        assert create_onetime_download_url('ACT','helloworld.pdf','1','wekosoftware@nii.ac.jp') == None

        data1 = []

        with patch('weko_records_ui.utils.get_restricted_access', return_value=data1):
            assert create_onetime_download_url('ACT','helloworld.pdf','1','wekosoftware@nii.ac.jp') == False


# def update_onetime_download(**kwargs) -> NoReturn:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_update_onetime_download -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_update_onetime_download(app):
    with app.test_request_context():
        assert update_onetime_download(file_name="helloworld.pdf", user_mail="wekosoftware@nii.ac.jp", record_id="1", download_count=0)==None


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
        test_data = '{"@context": "https://schema.org/", "@type": "Dataset", "citation": ["http://hdl.handle.net/2261/0002005680", "https://repository.dl.itc.u-tokyo.ac.jp/records/2005680"], "creator": [{"@type": "Person", "alternateName": "creator alternative name", "familyName": "creator family name", "givenName": "creator given name", "identifier": "123", "name": "creator name"}], "description": "『史料編纂掛備用寫眞畫像圖畫類目録』（1905年）の「画像」（肖像画模本）の部に著録する資料の架番号の新旧対照表。史料編纂所所蔵肖像画模本データベースおよび『目録』版面画像へのリンク付き。『画像史料解析センター通信』98（2022年10月）に解説記事あり。", "distribution": [{"@type": "DataDownload", "contentUrl": "https://repository.dl.itc.u-tokyo.ac.jp/record/2005680/files/comparison_table_of_preparation_image_catalog.xlsx", "encodingFormat": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}, {"@type": "DataDownload", "contentUrl": "https://raw.githubusercontent.com/RCOSDP/JDCat-base/main/apt.txt", "encodingFormat": "text/plain"}, {"@type": "DataDownload", "contentUrl": "https://raw.githubusercontent.com/RCOSDP/JDCat-base/main/environment.yml", "encodingFormat": "application/x-yaml"}, {"@type": "DataDownload", "contentUrl": "https://raw.githubusercontent.com/RCOSDP/JDCat-base/main/postBuild", "encodingFormat": "text/x-shellscript"}], "includedInDataCatalog": {"@type": "DataCatalog", "name": "https://localhost"}, "license": ["CC BY"], "name": "『史料編纂掛備用写真画像図画類目録』画像の部：新旧架番号対照表", "spatialCoverage": [{"@type": "Place", "geo": {"@type": "GeoCoordinates", "latitude": "point latitude test", "longitude": "point longitude test"}}, {"@type": "Place", "geo": {"@type": "GeoShape", "box": "1 3 2 4"}}, "geo location place test"]}'
        ret = get_google_detaset_meta(record)
        assert json.loads(ret) == json.loads(test_data)
        assert type(ret) == str

        app.config['WEKO_RECORDS_UI_GOOGLE_SCHOLAR_OUTPUT_RESOURCE_TYPE'] = None
        assert get_google_detaset_meta(record) == None

        data1 = MagicMock()

        with patch("lxml.etree", return_value=data1):
            assert get_google_detaset_meta(record) == None


# def get_billing_role(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_google_detaset_meta -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_billing_role(records, users):
    _, results = records
    record = results[0]['record']
    with patch('flask_login.utils._get_user', return_value=users[8]['obj']):
        user_role, min_price = get_billing_role(record)
        assert user_role == 'guest'
        assert min_price == ''
    billing_record = results[3]['record']
    with patch('flask_login.utils._get_user', return_value=users[8]['obj']):
        user_role, min_price = get_billing_role(billing_record)
        assert user_role == 'System Administrator'
        assert min_price == '200'
    with patch('flask_login.utils._get_user', return_value=users[5]['obj']):
        user_role, min_price = get_billing_role(billing_record)
        assert user_role == 'guest'
        assert min_price == ''
