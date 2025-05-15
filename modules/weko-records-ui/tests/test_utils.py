import pytest
from weko_records_ui.utils import (
    is_future,
    create_usage_report_for_user,
    get_data_usage_application_data,
    send_usage_report_mail_for_user,
    check_and_send_usage_report,
    update_onetime_download,
    create_onetime_download_url,
    get_onetime_download,
    validate_onetime_download_token,
    get_license_pdf,
    hide_item_metadata,
    get_pair_value,
    get_min_price_billing_file_download,
    parse_one_time_download_token,
    generate_one_time_download_url,
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
    delete_version,
    soft_delete,
    is_billing_item,
    get_groups_price,
    get_record_permalink,
    get_google_detaset_meta,
    get_google_scholar_meta,
    create_secret_url,
    parse_secret_download_token,
    validate_secret_download_token,
    get_secret_download,
    update_secret_download,
    get_valid_onetime_download,
    display_oaiset_path,
    get_terms,
    get_roles,
    check_items_settings,
    get_data_by_key_array_json,
    get_values_by_selected_lang,
    export_preprocess,
    #RoCrateConverter,
    #create_tsv
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
from flask_babelex import to_utc 
from invenio_accounts.testutils import login_user_via_session
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from mock import patch
from weko_deposit.api import WekoRecord, WekoDeposit
from weko_records_ui.models import FileOnetimeDownload, FileSecretDownload
from weko_records.api import ItemTypes,Mapping
from werkzeug.exceptions import NotFound
from weko_admin.models import AdminSettings
from weko_records.serializers.utils import get_mapping
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName
from flask_babelex import gettext as _
import datetime
from datetime import datetime as dt ,timedelta
from werkzeug.exceptions import Gone, NotFound

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


# def delete_version(recid):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_delete_version -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_delete_version(app, records, users):
    indexer, results = records
    record = results[0]["record"]
    recid = results[0]["recid"]

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        delete_version(record.pid.pid_value + '.1')
        pid = PersistentIdentifier.query.filter_by(
            pid_type='recid', pid_value=record.pid.pid_value + '.1').first()
        assert pid.status == PIDStatus.DELETED

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
    item_metadata_json={'id': '23.1', 'pid': {'type': 'depid', 'value': '23.1', 'revision_id': 0}, 'lang': 'ja', 'owner': 1, 'title': 'test', 'owners': [1], 'status': 'published', '$schema': '/items/jsonschema/15', 'pubdate': '2022-09-28', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}, 'shared_user_ids': [], 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_ddb1', 'resourcetype': 'dataset'}, 'item_1617605131499': [{'url': {'url': 'https://weko3.example.org/record/23.1/files/sample_arial.pdf'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-28'}], 'format': 'application/pdf', 'filename': 'sample_arial.pdf', 'filesize': [{'value': '28 KB'}], 'mimetype': 'application/pdf', 'accessrole': 'open_access', 'version_id': '72b25fac-c471-44af-9971-c608f684f863', 'displaytype': 'preview', 'licensetype': 'license_12'}]}
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

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_values_by_selected_lang -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_values_by_selected_lang(app):
    # cur_lang
    cur_lang = "ja"
    source_title = [('ja',''),('','test0'),('ja','テスト1'), ('en','test'), ('ja','テスト2')]
    test = ['テスト1', 'テスト2']
    result = get_values_by_selected_lang(source_title, cur_lang)
    assert result == test
    
    # not cur_lang, none language is first
    source_title = [('None Language', 'test1'), ('en', 'test2'), ('None Language', 'test3'), ('fr', 'test4')]
    test = ['test1', 'test3']
    result = get_values_by_selected_lang(source_title, cur_lang)
    assert result == test
    
    # not cur_lang, none language is not first, exist ja-Latn
    source_title = [('en', 'test1'), ('en', 'test2'), ('ja-Latn', 'test3'), ('ja-Latn', 'test4')]
    test = ['test3', 'test4']
    result = get_values_by_selected_lang(source_title, cur_lang)
    assert result == test
    
    # not cur_lang, none language is not first, not exist ja-Latn, exist en
    source_title = [('en', 'test1'), ('en', 'test2'), ('None Language', 'test3'), ('None Language', 'test4')]
    test = ['test1', 'test2']
    result = get_values_by_selected_lang(source_title, cur_lang)
    assert result == test
    
    # cur_lang=en, exist title_data_langs
    cur_lang = 'en'
    source_title = [('fr','test1'),('ch','test2'),('ch','test3'),('fr','test4')]
    test = ['test1', 'test4']
    result = get_values_by_selected_lang(source_title, cur_lang)
    assert result == test
    
    # cur_lang !=en, exist title_data_langs
    cur_lang = "ja"
    source_title = [('fr','test1'),('ch','test2'),('ch','test3'),('fr','test4')]
    test = ['test1', 'test4']
    result = get_values_by_selected_lang(source_title, cur_lang)
    assert result == test
    
    # return title_data_langs_none
    app.config["WEKO_RECORDS_UI_LANG_DISP_FLG"] = True
    cur_lang = "en"
    source_title = [('ja','test0'),('None Language', 'test1'),('None Language', 'test2')]
    test = ['test1', 'test2']
    result = get_values_by_selected_lang(source_title, cur_lang)
    assert result == test
    
    # enとja-latnがない、noneがない、
    cur_lang = 'en'
    source_title = []
    test = None
    result = get_values_by_selected_lang(source_title, cur_lang)
    assert result == test

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
def test_hide_by_email(app,records, itemtypes):
    indexer, results = records
    record = results[0]["record"]
    test_record = copy.deepcopy(record)
    record['item_1617186419668']['attribute_value_mlt'][0].pop('creatorMails')
    record['item_1617186419668']['attribute_value_mlt'][1].pop('creatorMails')
    record['item_1617186419668']['attribute_value_mlt'][2].pop('creatorMails')
    record['item_1617349709064']['attribute_value_mlt'][0].pop('contributorMails')
    assert hide_by_email(test_record)==record
    assert hide_by_email(test_record, item_type=itemtypes["item_type"])==record

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
def test_get_file_info_list(app,records, itemtypes):
    indexer, results = records
    record = results[0]["record"]
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        ret =  get_file_info_list(record)
        assert len(ret)==2

        ret =  get_file_info_list(record, item_type=itemtypes["item_type"])
        assert len(ret)==2

    # 異常系
    # 不正な数値を指定する
    record['item_1617605131499']['attribute_value_mlt'][0]['filesize'][0]['value'] = '1.7976931348623157e+308/0 kb'
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        ret =  get_file_info_list(record)
        assert ret[1][0]['size'] == -1
    record['item_1617605131499']['attribute_value_mlt'][0]['filesize'][0]['value'] = '5 kb'

    # access == "open_login"
    record['item_1617605131499']['attribute_value_mlt'][0]['accessrole'] = 'open_login'
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        ret =  get_file_info_list(record)
        assert ret[1][0]['future_date_message'] == 'Restricted Access'

    # access == "open_date"
    record['item_1617605131499']['attribute_value_mlt'][0]['accessrole'] = 'open_date'
    # dateValue == None
    record['item_1617605131499']['attribute_value_mlt'][0]['date'] = [{'dateType':'Available'}]
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        ret =  get_file_info_list(record)
        adt = str(datetime.date.max)
        pdt = to_utc(dt.strptime(adt, '%Y-%m-%d')) 
        assert ret[1][0]['future_date_message'] == "Download is available from {}/{}/{}.".format(pdt.year, pdt.month, pdt.day)
        assert ret[1][0]['download_preview_message'] == "Download / Preview is available from {}/{}/{}.".format(pdt.year, pdt.month, pdt.day)
    
    # dateValue == 過去
    past_time = dt.now() - timedelta(days=3)
    past_time_str = str(past_time).split(' ')[0]
    past_time_str = str(dt.strptime(past_time_str, '%Y-%m-%d')).split(' ')[0]
    record['item_1617605131499']['attribute_value_mlt'][0]['date'][0]['dateValue'] = past_time_str
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        ret =  get_file_info_list(record)
        pdt = to_utc(past_time) 
        assert ret[1][0]['future_date_message'] == ""
        assert ret[1][0]['download_preview_message'] == ""

    # dateValue == 未来
    future_time = dt.now() + timedelta(days=3)
    future_time_str = str(future_time).split(' ')[0]
    future_time_str = str(dt.strptime(future_time_str, '%Y-%m-%d')).split(' ')[0]
    record['item_1617605131499']['attribute_value_mlt'][0]['date'][0]['dateValue'] = future_time_str
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        ret =  get_file_info_list(record)
        pdt = to_utc(future_time) 
        assert ret[1][0]['future_date_message'] == "Download is available from {}/{}/{}.".format(pdt.year, pdt.month, pdt.day)
        assert ret[1][0]['download_preview_message'] == "Download / Preview is available from {}/{}/{}.".format(pdt.year, pdt.month, pdt.day)

# def get_file_info_list(record):
#     def get_file_size(p_file):
#     def set_message_for_file(p_file):
#     def get_data_by_key_array_json(key, array_json, get_key):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_file_info_list_1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_file_info_list_1(app, make_record_need_restricted_access):
    # roles = [{"role":1},{"role":2}]
    record_1 = WekoRecord.get_record_by_pid(11)
    record_1['item_1689228169922']['attribute_value_mlt'][0]['roles'] = [{"role":1},{"role":2}]
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        is_display_file_preview, files =  get_file_info_list(record_1)
        assert is_display_file_preview == True
        assert len(files) == 1
    
    # 'provide': [{'role': '2', 'workflow': '3'}, {'role': 'none_loggin', 'workflow': '3'}, {'role': '1', 'workflow': '99'}, {'role': '3', 'workflow': '3'}]
    # terms='term_free' termsDescription='利用規約本文'
    record_2 = WekoRecord.get_record_by_pid(12)
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        is_display_file_preview, files =  get_file_info_list(record_2)
        assert is_display_file_preview == True
        assert len(files) == 1

    record_2['item_1689228169922']['attribute_value_mlt'][0]['terms'] = '100'
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        is_display_file_preview, files =  get_file_info_list(record_2)
        assert is_display_file_preview == True
        assert len(files) == 1
    
# def get_data_by_key_array_json(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_data_by_key_array_json -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_data_by_key_array_json(app):
    array_json = [{'id': 'test1', 'value':'value1'}, {'id': 'test2', 'value':'value2'}, {'hoge': 1}]
    key = 'test2'
    get_key = 'value'
    assert 'value2' == get_data_by_key_array_json(key, array_json, get_key)
    none_key = 'abc'
    assert None == get_data_by_key_array_json(none_key, array_json, get_key)
    assert None == get_data_by_key_array_json(key, [], get_key)

# def create_usage_report_for_user(onetime_download_extra_info: dict):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
#def test_create_usage_report_for_user():
#    assert False

# def create_usage_report_for_user(onetime_download_extra_info: dict):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_create_usage_report_for_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_create_usage_report_for_user(app, db, workflows, records, users, db_file_permission):
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

# def def get_valid_onetime_download(file_name: str, record_id: str,user_mail: str) -> Optional[FileOnetimeDownload]:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_valid_onetime_download -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_valid_onetime_download():
    with patch("weko_records_ui.models.FileOnetimeDownload.find_downloadable_only",return_value=[]):
        assert get_valid_onetime_download(file_name= "str", record_id= "str",user_mail= "str") is None
    with patch("weko_records_ui.models.FileOnetimeDownload.find_downloadable_only",return_value=[{}]):
        assert {} == get_valid_onetime_download(file_name= "str", record_id= "str",user_mail= "str")
    with patch("weko_records_ui.models.FileOnetimeDownload.find_downloadable_only",return_value=["a","b"]):
        assert "a" == get_valid_onetime_download(file_name= "str", record_id= "str",user_mail= "str")

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
        assert get_google_detaset_meta(record)=='{"@context": "https://schema.org/", "@type": "Dataset", "citation": ["http://hdl.handle.net/2261/0002005680", "https://repository.dl.itc.u-tokyo.ac.jp/records/2005680"], "creator": [{"@type": "Person", "alternateName": "creator alternative name", "familyName": "creator family name", "givenName": "creator given name", "identifier": "123", "name": "creator name"}], "description": "『史料編纂掛備用寫眞畫像圖畫類目録』（1905年）の「画像」（肖像画模本）の部に著録する資料の架番号の新旧対照表。史料編纂所所蔵肖像画模本データベースおよび『目録』版面画像へのリンク付き。『画像史料解析センター通信』98（2022年10月）に解説記事あり。", "distribution": [{"@type": "DataDownload", "contentUrl": "https://repository.dl.itc.u-tokyo.ac.jp/record/2005680/files/comparison_table_of_preparation_image_catalog.xlsx", "encodingFormat": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}, {"@type": "DataDownload", "contentUrl": "https://raw.githubusercontent.com/RCOSDP/JDCat-base/main/apt.txt", "encodingFormat": "text/plain"}, {"@type": "DataDownload", "contentUrl": "https://raw.githubusercontent.com/RCOSDP/JDCat-base/main/environment.yml", "encodingFormat": "application/x-yaml"}, {"@type": "DataDownload", "contentUrl": "https://raw.githubusercontent.com/RCOSDP/JDCat-base/main/postBuild", "encodingFormat": "text/x-shellscript"}], "includedInDataCatalog": {"@type": "DataCatalog", "name": "https://localhost"}, "license": ["CC BY"], "name": "『史料編纂掛備用写真画像図画類目録』画像の部：新旧架番号対照表", "spatialCoverage": [{"@type": "Place", "geo": {"@type": "GeoCoordinates", "latitude": "point latitude test", "longitude": "point longitude test"}}, {"@type": "Place", "geo": {"@type": "GeoShape", "box": "1 3 2 4"}}, "geo location place test"]}'
        
        app.config['WEKO_RECORDS_UI_GOOGLE_SCHOLAR_OUTPUT_RESOURCE_TYPE'] = None
        assert get_google_detaset_meta(record) == None

        data1 = MagicMock()

        with patch("lxml.etree", return_value=data1):
            assert get_google_detaset_meta(record) == None

#def create_secret_url(record_id:str ,file_name:str ,user_mail:str ,restricted_fullname='',restricted_data_name='') -> dict:
# def _generate_secret_download_url(file_name: str, record_id: str, id: str ,created :dt) -> str:
# _create_secret_download_url(file_name: str, record_id: str, user_mail: str)
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_create_secret_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_create_secret_url(app,db,users,records):
    url , results = records
    file_name= results[1]["filename"]
    record_id=results[1]["recid"].pid_value
    user_mail = users[0]["email"]
    
    db.session.add(AdminSettings(id=6,name='restricted_access',settings={"secret_URL_file_download": 
            {"secret_enable": True, 
            "secret_download_limit": 1, 
            "secret_expiration_date": 9999999, 
            "secret_download_limit_unlimited_chk": False,
            "secret_expiration_date_unlimited_chk": False}}))
    
    with app.test_request_context():

        #60
        #76
        # with db.session.begin_nested():
        return_dict = create_secret_url(file_name= file_name, record_id=record_id, user_mail=user_mail)
            
        assert return_dict["restricted_download_count"] == '1'
        assert return_dict["restricted_download_count_ja"] == ""
        assert return_dict["restricted_download_count_en"] == ""
        assert return_dict['restricted_expiration_date'] == ""
        assert return_dict['restricted_expiration_date_ja'] == "無制限"
        assert return_dict['restricted_expiration_date_en'] == "Unlimited"
        
        #61
        # with db.session.begin_nested():
        db.session.merge(AdminSettings(id=6,name='restricted_access',settings={"secret_URL_file_download": 
                {"secret_enable": True, 
                "secret_download_limit": 9999999, 
                "secret_expiration_date": 1, 
                "secret_download_limit_unlimited_chk": False,
                "secret_expiration_date_unlimited_chk": False}}))
        return_dict = create_secret_url(file_name= file_name
                    , record_id=record_id
                    , user_mail=user_mail)
        assert return_dict["restricted_download_count"] == ""
        assert return_dict["restricted_download_count_ja"] == "無制限"
        assert return_dict["restricted_download_count_en"] == "Unlimited"
        assert return_dict['restricted_expiration_date'] == (datetime.date.today() + timedelta(1)).strftime("%Y-%m-%d") 
        assert return_dict['restricted_expiration_date_ja'] == ""
        assert return_dict['restricted_expiration_date_en'] == ""

        #62
        #63
        #test No.4(W2023-22 2)
        from re import match
        assert match("^.+record\/" + record_id + "\/file\/secret\/"+file_name+"\?token=.+=$",return_dict["secret_url"])
        assert return_dict["secret_url"] != ""
        assert return_dict["mail_recipient"] == user_mail
    

# def parse_secret_download_token(token: str) -> Tuple[str, Tuple]:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_parse_secret_download_token -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_parse_secret_download_token(app ,db):
    #64
    assert parse_secret_download_token(None) == (_("Token is invalid."),())
    assert parse_secret_download_token("") == (_("Token is invalid."),())
    #65
    assert parse_secret_download_token("random_string sajfosijdfasodfjv") == (_("Token is invalid."),())


    # 66
    # onetime_download pattern
    assert parse_secret_download_token("MSB1c2VyQGV4YW1wbGUub3JnIDIwMjItMDktMjcgNDBDRkNGODFGM0FFRUI0Ng==") == (_("Token is invalid."),())

    # 67
    # secret_download pattern
    error , res = parse_secret_download_token("MSA1IDIwMjMtMDMtMDggMDA6NTI6MTkuNjI0NTUyIDZGQTdEMzIxQTk0OTU1MEQ=")
    assert not error
    assert res == ('1', '5', '2023-03-08 00:52:19.624552', '6FA7D321A949550D')

# def validate_secret_download_token(
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_validate_secret_download_token -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_validate_secret_download_token(app):

    with app.test_request_context():
        secret_download=FileSecretDownload(
            file_name= "eee.txt", record_id= '1',user_mail="repoadmin@example.org",expiration_date=999999,download_count=10
        )
        secret_download.created = dt(2023,3,8,0,52,19,624552)
        secret_download.id = 5
        # 68
        res = validate_secret_download_token(secret_download=None , file_name= "eee.txt", record_id= '1', id= '5', date= '2023-03-08 00:52:19.624552', token= '6FA7D321A949550D')
        assert res == (False , _("Token is invalid."))

        #69
        res = validate_secret_download_token(secret_download=secret_download , file_name= "aaa.txt", record_id= '1', id= '5', date= '2023-03-08 00:52:19.624552', token= '6FA7D321A949550D')
        assert res == (False , _("Token is invalid."))
        res = validate_secret_download_token(secret_download=secret_download , file_name= "eee.txt", record_id= '5', id= '5', date= '2023-03-08 00:52:19.624552', token= '6FA7D321A949550D')
        assert res == (False , _("Token is invalid."))
        res = validate_secret_download_token(secret_download=secret_download , file_name= "eee.txt", record_id= '1', id= '1', date= '2023-03-08 00:52:19.624552', token= '6FA7D321A949550D')
        assert res == (False , _("Token is invalid."))
        res = validate_secret_download_token(secret_download=secret_download , file_name= "eee.txt", record_id= '1', id= '5', date= '2099-03-08 00:52:19.624552', token= '6FA7D321A949550D')
        assert res == (False , _("Token is invalid."))
        res = validate_secret_download_token(secret_download=secret_download , file_name= "eee.txt", record_id= '1', id= '5', date= '2023-03-08 00:52:19.624552', token= '7FA7D321A949550D')
        assert res == (False , _("Token is invalid."))

        # 70
        secret_download2=FileSecretDownload(
            file_name= "eee.txt", record_id= '5',user_mail="repoadmin@example.org",expiration_date=-1,download_count=10
        )
        secret_download2.created = dt(2023,3,8,0,52,19,624552)
        secret_download2.id = 5
        res = validate_secret_download_token(secret_download=secret_download2 , file_name= "eee.txt", record_id= '1', id= '5', date= '2023-03-08 00:52:19.624552', token= '6FA7D321A949550D')
        assert res == (False , _("The expiration date for download has been exceeded."))
        
        #71
        secret_download2.expiration_date = 99999999
        res = validate_secret_download_token(secret_download=secret_download2 , file_name= "eee.txt", record_id= '1', id= '5', date= '2023-03-08 00:52:19.624552', token= '6FA7D321A949550D')
        assert res == (True ,"")
        
        # 72
        secret_download2.expiration_date = 9999999
        secret_download2.download_count = 0
        res = validate_secret_download_token(secret_download=secret_download2 , file_name= "eee.txt", record_id= '1', id= '5', date= '2023-03-08 00:52:19.624552', token= '6FA7D321A949550D')
        assert res == (False , _("The download limit has been exceeded."))

        # 73
        res = validate_secret_download_token(secret_download=secret_download , file_name= "eee.txt", record_id= '1', id= '5', date= '2023-03-08 00:52:19.624552', token= '6FA7D321A949550D')
        assert res == (True ,"")

        secret_download2.expiration_date = "hoge"
        res = validate_secret_download_token(secret_download=secret_download2 , file_name= "eee.txt", record_id= '1', id= '5', date= '2023-03-08 00:52:19.624552', token= '6FA7D321A949550D')
        assert res == (False , _("Token is invalid."))

# def get_secret_download(file_name: str, record_id: str,
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_secret_download -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_secret_download(app ,db ):
    with app.test_request_context():
        with db.session.begin_nested():
            secret_download=FileSecretDownload(
                file_name= "eee.txt", record_id= '1',user_mail="repoadmin@example.org",expiration_date=999999,download_count=10
            )
            db.session.add(secret_download)
        

        
        assert get_secret_download(file_name= secret_download.file_name
                            , record_id= secret_download.record_id
                            , id= secret_download.id 
                            , created =secret_download.created)
        
        assert not get_secret_download(file_name= secret_download.file_name
                            , record_id= secret_download.record_id
                            , id= secret_download.id + 1
                            , created =secret_download.created)

# def update_secret_download(**kwargs) -> Optional[List[FileSecretDownload]]:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_data_usage_application_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_data_usage_application_data(app ,db):
    with app.test_request_context():
        with db.session.begin_nested():
            secret_download=FileSecretDownload(
                file_name= "eee.txt", record_id= '1',user_mail="repoadmin@example.org",expiration_date=999999,download_count=10
            )
            db.session.add(secret_download)
        update_data = dict(
            file_name   = secret_download.file_name
            , record_id = secret_download.record_id
            , download_count = 100
            , created  = secret_download.created
            , id = secret_download.id
        )
        res = update_secret_download(**update_data)
        assert len(res) == 1
        assert res[0].download_count == 100


# def update_secret_download(**kwargs) -> Optional[List[FileSecretDownload]]:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_export_preprocess -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_export_preprocess(app, records, esindex):
    indexer, results = records
    record = results[0]["record"]
    recid = results[0]["recid"]

    with app.test_request_context():
        schema_type = 'json'
        # export json
        res = export_preprocess(recid, record, schema_type)
        res_dict = json.loads(res)
        assert 'created' in res_dict
        assert res_dict['id'] == 1
        assert res_dict['links'] == {}
        assert res_dict['metadata'] == record
        assert 'updated' in res_dict

        # export BibTeX
        export_preprocess(recid, record, 'bibtex')

        # record update '@export_schema_type'
        export_preprocess(recid, record, 'jpcoar_2.0')

        # fmt is False
        mock_config = {'RECORDS_UI_EXPORT_FORMATS': {recid.pid_type: {schema_type: False}}}
        with patch('flask.current_app.config', mock_config), \
                pytest.raises(Gone):
            export_preprocess(recid, record, schema_type)

        # fmt is None
        mock_config = {}
        with patch('flask.current_app.config', mock_config), \
                pytest.raises(NotFound):
            export_preprocess(recid, record, schema_type)
