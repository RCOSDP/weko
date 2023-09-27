from unittest import mock
from urllib.parse import parse_qs
import pytest
import uuid
from os.path import dirname, join
from mock import patch
import copy
import datetime
import base64
import flask
from werkzeug.datastructures import MultiDict
from flask import current_app,session
from flask_babelex import gettext as _
from sqlalchemy.orm.exc import NoResultFound
from weko_deposit.pidstore import get_record_without_version
from weko_deposit.api import WekoRecord, WekoDeposit
from invenio_files_rest.models import Bucket
from invenio_cache import current_cache
from invenio_accounts.testutils import login_user_via_session as login
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from flask_login.utils import login_user,logout_user
from tests.helpers import json_data
from invenio_mail.models import MailConfig
from weko_admin.models import SiteInfo
from weko_user_profiles import UserProfile
from weko_records.api import ItemTypes, ItemsMetadata
from weko_user_profiles.config import WEKO_USERPROFILES_POSITION_LIST,WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
from weko_workflow.models import ActivityHistory,GuestActivity
from weko_workflow.config import WEKO_WORKFLOW_FILTER_PARAMS,IDENTIFIER_GRANT_LIST
from weko_workflow.utils import (
    filter_all_condition,
    filter_condition,
    get_application_and_approved_date,
    get_disptype_and_ver_in_metainfo,
    get_record_by_root_ver,
    get_url_root,
    handle_finish_workflow,
    process_send_reminder_mail,
    register_hdl,
    IdentifierHandle,
    get_current_language,
    get_term_and_condition_content,
    get_identifier_setting,
    saving_doi_pidstore,
    item_metadata_validation,merge_doi_error_list,
    MappingData,
    validation_item_property,
    handle_check_required_data,
    get_activity_id_of_record_without_version,
    handle_check_required_pattern_and_either,
    check_required_data,get_sub_item_value,
    get_item_value_in_deep,
    delete_bucket,
    merge_buckets_by_records,
    set_bucket_default_size,
    is_show_autofill_metadata,
    is_hidden_pubdate,
    get_parent_pid_with_type,
    get_actionid,
    convert_record_to_item_metadata,
    prepare_edit_workflow,
    delete_cache_data,
    update_cache_data,
    get_cache_data,
    get_account_info,
    check_existed_doi,
    set_files_display_type,
    get_thumbnails,
    get_allow_multi_thumbnail,
    is_usage_application_item_type,
    is_usage_application,
    send_mail_reminder,
    send_mail_approval_done,
    send_mail_registration_done,
    send_mail_request_approval,
    send_mail,
    email_pattern_registration_done,
    email_pattern_request_approval,
    email_pattern_approval_done,
    get_mail_data,
    get_subject_and_content,
    get_file_path,
    replace_characters,
    get_register_info,
    get_approval_dates,
    get_item_info,
    get_site_info_name,
    get_default_mail_sender,
    set_mail_info,
    process_send_reminder_mail,
    process_send_notification_mail,
    get_workflow_item_type_names,
    create_usage_report,
    create_record_metadata,
    modify_item_metadata,
    replace_title_subitem,
    get_shema_dict,
    create_deposit,
    update_activity_action,
    check_continue,
    auto_fill_title,
    exclude_admin_workflow,
    is_enable_item_name_link,
    save_activity_data,
    send_mail_url_guest_user,
    generate_guest_activity_token_value,
    init_activity_for_guest_user,
    send_usage_application_mail_for_guest_user,
    validate_guest_activity_token,
    validate_guest_activity_expired,
    create_onetime_download_url_to_guest,
    delete_guest_activity,
    get_activity_display_info,
    recursive_get_specified_properties,
    get_approval_keys,
    __init_activity_detail_data_for_guest,
    process_send_mail,
    cancel_expired_usage_reports,
    process_send_approval_mails,
    prepare_data_for_guest_activity,
    get_usage_data,
    get_sub_key_by_system_property_key,
    update_approval_date,
    get_record_first_version,
    get_current_date,
    update_system_data_for_item_metadata,
    update_approval_date_for_deposit,
    update_system_data_for_activity,
    make_activitylog_tsv
)
from weko_workflow.api import GetCommunity, UpdateItem, WorkActivity, WorkActivityHistory, WorkFlow
from weko_workflow.models import Activity

# def get_current_language():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_current_language(app):#c
    with app.test_request_context(
        headers=[("Accept-Language","ja")]
    ):
        assert get_current_language()=="en"
        current_app.config.update(
            WEKO_WORKFLOW_TERM_AND_CONDITION_FILE_LANGUAGES = ["ja","en"],
        )
        assert get_current_language()=="ja"

# def get_term_and_condition_content(item_type_name):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_term_and_condition_content -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_term_and_condition_content(app):#c
    item_type_name="test_item_type"
    result = None
    with open(join(dirname(__file__),"data/test_file/test_item_type_en.txt"),"r") as f:
        result = f.read().splitlines()
    current_app.config.update(
        WEKO_WORKFLOW_TERM_AND_CONDITION_FILE_EXTENSION = ".txt",
        WEKO_WORKFLOW_TERM_AND_CONDITION_FILE_LOCATION = join(dirname(__file__),"data/test_file/")
    )
    with patch("weko_workflow.utils.get_current_language",return_value="en"):
        assert get_term_and_condition_content(item_type_name)==result
    
    with patch("weko_workflow.utils.get_current_language",return_value="wrong"):
        assert get_term_and_condition_content(item_type_name)==""


# def get_identifier_setting(community_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_identifier_setting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_identifier_setting(identifier):#c
    assert get_identifier_setting(identifier.repository)==identifier

# def saving_doi_pidstore(item_id,
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_saving_doi_pidstore(db_records,item_type,mocker):#c
    item_id = db_records[0][3].id
    pid_without_ver = get_record_without_version(db_records[0][0]).object_uuid
    mock_register = mocker.patch("weko_workflow.utils.IdentifierHandle.register_pidstore", return_value=None)
    data = {
        "identifier_grant_jalc_doi_link":"https://doi.org/1000/0000000001",
        "identifier_grant_jalc_cr_doi_link":"https://doi.org/2000/0000000001",
        "identifier_grant_jalc_dc_doi_link":"https://doi.org/3000/0000000001",
        "identifier_grant_ndl_jalc_doi_link":"https://doi.org/4000/0000000001"
    }
    mock_update = mocker.patch("weko_workflow.utils.IdentifierHandle.update_idt_registration_metadata")
    result = saving_doi_pidstore(item_id,pid_without_ver,data,1,False,True)
    assert result == True
    mock_update.assert_has_calls([mocker.call("1000/0000000001","JaLC")])
    
    mock_update = mocker.patch("weko_workflow.utils.IdentifierHandle.update_idt_registration_metadata")
    result = saving_doi_pidstore(item_id,pid_without_ver,data,2,False,False)
    assert result == True
    mock_update.assert_has_calls([mocker.call("2000/0000000001","Crossref")])
    
    with patch("weko_workflow.utils.IdentifierHandle.register_pidstore",return_value=True):
        mock_update = mocker.patch("weko_workflow.utils.IdentifierHandle.update_idt_registration_metadata")
        result = saving_doi_pidstore(item_id,pid_without_ver,data,3,False,False)
        assert result == True
        mock_update.assert_has_calls([mocker.call("3000/0000000001","DataCite"),mocker.call("3000/0000000001","DataCite")])
    
    with patch("weko_workflow.utils.IdentifierHandle.register_pidstore",side_effect=Exception):
        mock_update = mocker.patch("weko_workflow.utils.IdentifierHandle.update_idt_registration_metadata")
        result = saving_doi_pidstore(item_id,pid_without_ver,data,4,True,False)
        assert result == False

    mock_update = mocker.patch("weko_workflow.utils.IdentifierHandle.update_idt_registration_metadata")
    result = saving_doi_pidstore(uuid.uuid4(),pid_without_ver,data,"wrong",False,False)
    assert result == False

# def register_hdl(activity_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_register_hdl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_register_hdl(app,db_records,db_register):#c
    recid, depid, record, item, parent, doi, deposit = db_records[0]
    assert recid.pid_value=="1"
    activity_id='A-00000800-00000'
    act = Activity(
                activity_id=activity_id,
                item_id=record.id,
            )
    with patch("weko_handle.api.Handle.register_handle",return_value="handle:00.000.12345/0000000001"):
        with app.test_request_context():
            register_hdl("8")
            pid = IdentifierHandle(parent.object_uuid).check_pidstore_exist(pid_type='hdl')
            assert pid[0].object_uuid == parent.object_uuid
            pid = IdentifierHandle(recid.object_uuid).check_pidstore_exist(pid_type='hdl')
            assert pid[0].object_uuid == recid.object_uuid
    
    recid, depid, record, item, parent, doi, deposit = db_records[2]
    assert recid.pid_value=="1.1"
    activity_id='A-00000800-00000'
    act = Activity(
                activity_id=activity_id,
                item_id=record.id,
            )
    with patch("weko_handle.api.Handle.register_handle",return_value="handle:00.000.12345/0000000001"):
        with app.test_request_context():
            register_hdl("2")
            pid = IdentifierHandle(parent.object_uuid).check_pidstore_exist(pid_type='hdl')
            assert pid[0].object_uuid == parent.object_uuid
            pid = IdentifierHandle(recid.object_uuid).check_pidstore_exist(pid_type='hdl')
            assert pid == []
    
    recid, depid, record, item, parent, doi,deposit = db_records[1]
    assert recid.pid_value=="1.0"
    activity_id='A-00000800-00000'
    act = Activity(
                activity_id=activity_id,
                item_id=record.id,
            )
    with patch("weko_handle.api.Handle.register_handle",return_value="handle:00.000.12345/0000000001"):
        with app.test_request_context():
            register_hdl("9")
            # register_hdl uses parent object_uuid.
            pid = IdentifierHandle(parent.object_uuid).check_pidstore_exist(pid_type='hdl')
            assert pid[0].object_uuid == parent.object_uuid
            # register_hdl does not use recid object_uuid.
            pid = IdentifierHandle(recid.object_uuid).check_pidstore_exist(pid_type='hdl')
            assert pid==[]
    

                


# def register_hdl_by_item_id(deposit_id, item_uuid, url_root):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# def register_hdl_by_handle(hdl, item_uuid, item_uri):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# def item_metadata_validation(item_id, identifier_type, record=None,
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_item_metadata_validation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_item_metadata_validation(db_records,item_type):
    recid, depid, record, item, parent, doi, deposit = db_records[0]
    #result = item_metadata_validation(recid.id,"hdl")
    result = item_metadata_validation(None,"hdl",record=record)
    assert result == None
    recid, depid, record, item, parent, doi, deposit = db_records[2]
    
    without_ver = get_record_without_version(recid)
    print("tts:{}".format(without_ver))
    # identifiery_type is JaLC, new resource_type in journalarticle_type, old resource_type in elearning_type
    with patch("weko_workflow.utils.MappingData.get_first_data_by_mapping",\
        side_effect=[("item_1617258105262.resourcetype", ['conference paper']),(None,["learning object"])]):
        result = item_metadata_validation(recid.object_uuid,"1",without_ver_id=without_ver.object_uuid)
        assert result == {'required': [], 'required_key': [], 'pattern': [],
                  'either': [],  'either_key': [], 'mapping': [], 'other': 'You cannot change the resource type of items that have been grant a DOI.'}
    print("tt4.1")
    # identifiery_type is JaLC, new resource_type in report_types, old resource_type in thesis_types
    with patch("weko_workflow.utils.MappingData.get_first_data_by_mapping",\
        side_effect=[("item_1617258105262.resourcetype", ['thesis']),(None,["report"])]):
        result = item_metadata_validation(recid.object_uuid,"1",without_ver_id=without_ver.object_uuid)
        assert result == {'required': [], 'required_key': [], 'pattern': [],
                  'either': [],  'either_key': [], 'mapping': [], 'other': 'You cannot change the resource type of items that have been grant a DOI.'}
    # identifiery_type is JaLC, new resource_type in dataset_type, old resource_type in datageneral_types
    with patch("weko_workflow.utils.MappingData.get_first_data_by_mapping",\
        side_effect=[("item_1617258105262.resourcetype", ['software']),(None,["internal report"])]):
        result = item_metadata_validation(recid.object_uuid,"1",without_ver_id=without_ver.object_uuid)
        assert result == {'required': [], 'required_key': [], 'pattern': [],
                  'either': [],  'either_key': [], 'mapping': [], 'other': 'You cannot change the resource type of items that have been grant a DOI.'}
    
    # identifiery_type is JaLC, new resource_type in else, old resource_type in else
    with patch("weko_workflow.utils.MappingData.get_first_data_by_mapping",\
        side_effect=[("item_1617258105262.resourcetype", ['else']),(None,["else"])]):
        result = item_metadata_validation(recid.object_uuid,"1",without_ver_id=without_ver.object_uuid)
        assert result == {'required': ['item_1617605131499.url.url'], 'required_key': ['jpcoar:URI'], 'pattern': [],
                  'either': [],  'either_key': [], 'mapping': [], }

    # identifiery_type is CrossRef, new resource_type in thesis_types, old resource_type in report_types
    with patch("weko_workflow.utils.MappingData.get_first_data_by_mapping",\
        side_effect=[("item_1617258105262.resourcetype", ['thesis']),(None,["report"])]):
        result = item_metadata_validation(recid.object_uuid,"2",without_ver_id=without_ver.object_uuid)
        assert result == {'required': ['item_1617605131499.url.url'], 'required_key': ['jpcoar:URI'], 'pattern': [],
                  'either': [],  'either_key': [], 'mapping': [], }

    # identifiery_type is CrossRef, new resource_type in journalarticle_type, old resource_type in else
    with patch("weko_workflow.utils.MappingData.get_first_data_by_mapping",\
        side_effect=[("item_1617258105262.resourcetype", ['conference paper']),(None,["else"])]):
        result = item_metadata_validation(recid.object_uuid,"2",without_ver_id=without_ver.object_uuid)
        assert result == {'required': [], 'required_key': [], 'pattern': [],
                  'either': [],  'either_key': [], 'mapping': [], 'other': 'You cannot change the resource type of items that have been grant a DOI.'}
    # identifiery_type is DataCite, new resource_type in dataset_type, old resource_type in else
    with patch("weko_workflow.utils.MappingData.get_first_data_by_mapping",\
        side_effect=[("item_1617258105262.resourcetype", ['dataset']),(None,["thesis"])]):
        result = item_metadata_validation(recid.object_uuid,"3",without_ver_id=without_ver.object_uuid)
        assert result == {'required': [], 'required_key': [], 'pattern': [],
                  'either': [],  'either_key': [], 'mapping': [], 'other': 'You cannot change the resource type of items that have been grant a DOI.'}
    
    # identifiery_type is other
    with patch("weko_workflow.utils.MappingData.get_first_data_by_mapping",\
        side_effect=[("item_1617258105262.resourcetype", ['thesis']),(None,["report"])]):
        result = item_metadata_validation(recid.object_uuid,"4",without_ver_id=without_ver.object_uuid)
        assert result == "Cannot register selected DOI for current Item Type of this item."

    
# def merge_doi_error_list(current, new):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_merge_doi_error_list():#c
    current = {"required":["value_c1"],"required_key":["key_cr1"],"either":["value_ce1"],"either_key":["key_ce1"],"pattern":["value_cp1"],"mapping":[]}
    new = {"required":["value_n1"],"required_key":["key_nr1"],"either":["value_ne1"],"either_key":["key_ne1"],"pattern":["value_np1"],"mapping":["value_nm1"]}
    merge_doi_error_list(current, new)
    assert current == {"required":["value_c1","value_n1"],"required_key":["key_cr1","key_nr1"],"either":["value_ce1","value_ne1"],"either_key":["key_ce1","key_ne1"],"pattern":["value_cp1","value_np1"],"mapping":["value_nm1"]}

    current = {"required":["value_c1"],"either":["value_ce1"],"pattern":["value_cp1"],"mapping":["value_cm1"]}
    new = {"required":[],"required_key":["key_nr1"],"either":[],"either_key":["key_ne1"],"pattern":[],"mapping":[]}
    merge_doi_error_list(current, new)
    assert current == {"required":["value_c1"],"required_key":["key_nr1"],"either":["value_ce1"],"either_key":["key_ne1"],"pattern":["value_cp1"],"mapping":["value_cm1"]}

    current = {"required":["value_c1"],"either":["value_ce1"],"pattern":["value_cp1"],"mapping":["value_cm1"]}
    new = {"required":[],"either":[],"pattern":[],"mapping":[]}
    merge_doi_error_list(current, new)
    assert current == {"required":["value_c1"],"either":["value_ce1"],"pattern":["value_cp1"],"mapping":["value_cm1"]}

# def validation_item_property(mapping_data, properties):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_validation_item_property(db_records,item_type,mocker):
    mapping_item = MappingData(db_records[0][3].id)
    properties = {
        "required":["item1","item2"],
        "either":["item3","item4"]
    }
    not_error = {"required":[],"either":[],"pattern":[],"mapping":[]}
    with patch("weko_workflow.utils.validattion_item_property_required",return_value=None):
        with patch("weko_workflow.utils.validattion_item_property_either_required",return_value=None):
            result = validation_item_property(mapping_item,properties,"1")
            assert result == None

    required_error = {"required":["error1"],"either":[],"pattern":[],"mapping":[]}
    either_error = {"required":[],"either":["error2"],"pattern":[],"mapping":[]}
    with patch("weko_workflow.utils.validattion_item_property_required",return_value=required_error):
        with patch("weko_workflow.utils.validattion_item_property_either_required",return_value=either_error):
            result = validation_item_property(mapping_item,properties,"1")
            assert result == {"required":["error1"],"required_key":[],"either":["error2"],"either_key":[],"pattern":[],"mapping":[]}

    properties = {}
    result = validation_item_property(mapping_item, properties,"1")
    assert result == None


# def handle_check_required_data(mapping_data, mapping_key):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_handle_check_required_data(db_records, item_type):#c
    mapping_item = MappingData(db_records[0][3].id)
    with patch("weko_workflow.utils.check_required_data",return_value=['item_1617186331708.subitem_1551255647225']):
        req, keys, values = handle_check_required_data(mapping_item,"title.@value")
        assert req == ['item_1617186331708.subitem_1551255647225']
        assert keys == ['item_1617186331708.subitem_1551255647225']
        assert values == [["title"]]

    with patch("weko_workflow.utils.check_required_data",return_value=None):
        req, keys, values = handle_check_required_data(mapping_item,"title.@value")
        assert req == []
        assert keys == ['item_1617186331708.subitem_1551255647225']
        assert values == [["title"]]










# def handle_check_required_pattern_and_either(mapping_data, mapping_keys,
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_handle_check_required_pattern_and_either -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_handle_check_required_pattern_and_either(db,item_type):
    # mapping_data is None, mapping_key is None
    result = handle_check_required_pattern_and_either(None,None,None)
    assert result == None
    
    rec_uuid1 = uuid.uuid4()
    record_data = {
        "path":["1"],"recid":"1","title":["title"],"item_title": "title","item_type_id": "1",
        "item_1617186331708": {"attribute_name": "Title","attribute_value_mlt": [{ "subitem_1551255647225": "title1"}]},
        "item_1617258105262": {"attribute_name": "Resource Type","attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794","resourcetype": "conference paper"}]},
        "item_1617605131499": {"attribute_name": "File","attribute_type": "file","attribute_value_mlt": [{"url": {"url": "https://localhost/record/1/files/test.txt"},"date": [{"dateType": "Available","dateValue": "2022-10-03"}],"format": "text/tab-separated-values","filename": "check_2022-03-10.tsv","filesize": [{"value": "460 B"}],"accessrole": "open_access","version_id": "29dd361d-dc7f-49bc-b471-bdb5752afef5","displaytype": "detail","licensetype": "license_12",}]}
    }
    record = record = WekoRecord.create(record_data, id_=rec_uuid1)
    mapping_data = MappingData(record=record)
    # identifier_type = JaLC, not exist error
    result = handle_check_required_pattern_and_either(mapping_data,["dc:title"],"1")
    assert result == None
    
    
    rec_uuid2 = uuid.uuid4()
    record_data = {
        "path":["1"],"recid":"2","title":["title"],"item_title": "title","item_type_id": "1",
        "item_1617186331708": {"attribute_name": "Title","attribute_value_mlt": [{ "subitem_1551255647225": "title1"}]},
        "item_1617186941041": {"attribute_name": "Source Title","attribute_value_mlt": [{"subitem_1522650091861": "source_title1","subitem_1522650068558":"en"}]},
        "item_1617258105262": {"attribute_name": "Resource Type","attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794","resourcetype": "conference paper"}]},
        "item_1617605131499": {"attribute_name": "File","attribute_type": "file","attribute_value_mlt": [{"url": {"url": "https://localhost/record/1/files/test.txt"},"date": [{"dateType": "Available","dateValue": "2022-10-03"}],"format": "text/tab-separated-values","filename": "check_2022-03-10.tsv","filesize": [{"value": "460 B"}],"accessrole": "open_access","version_id": "29dd361d-dc7f-49bc-b471-bdb5752afef5","displaytype": "detail","licensetype": "license_12",}]}
    }
    record = record = WekoRecord.create(record_data, id_=rec_uuid2)
    mapping_data = MappingData(record=record)
    # current pattern
    result = handle_check_required_pattern_and_either(mapping_data,['jpcoar:sourceTitle'],"1")
    assert result == None
    
    
    rec_uuid3 = uuid.uuid4()
    record_data = {
        "path":["1"],"recid":"3","title":["title"],"item_title": "title","item_type_id": "1",
        "item_1617186331708": {"attribute_name": "Title","attribute_value_mlt": [{ "subitem_1551255647225": "title1"}]},
        "item_1617186941041": {"attribute_name": "Source Title","attribute_value_mlt": [{"subitem_1522650091861": "source_title1","subitem_1522650068558":"ja"}]},
        "item_1617258105262": {"attribute_name": "Resource Type","attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794","resourcetype": "conference paper"}]},
        "item_1617605131499": {"attribute_name": "File","attribute_type": "file","attribute_value_mlt": [{"url": {"url": "https://localhost/record/1/files/test.txt"},"date": [{"dateType": "Available","dateValue": "2022-10-03"}],"format": "text/tab-separated-values","filename": "check_2022-03-10.tsv","filesize": [{"value": "460 B"}],"accessrole": "open_access","version_id": "29dd361d-dc7f-49bc-b471-bdb5752afef5","displaytype": "detail","licensetype": "license_12",}]}
    }
    record = record = WekoRecord.create(record_data, id_=rec_uuid3)
    mapping_data = MappingData(record=record)
    # not current pattern
    result = handle_check_required_pattern_and_either(mapping_data,['jpcoar:sourceTitle'],"1")
    assert result == {'required': [], 'required_key': [], 'pattern': ['item_1617186941041.subitem_1522650068558'], 'either': [], 'either_key': [], 'mapping': []}
    
    # not exist mapping
    with patch("weko_workflow.utils.DOI_VALIDATION_INFO_JALC",{"dc:title":[["not_exist.@value",None]]}):
        result = handle_check_required_pattern_and_either(mapping_data,["dc:title"],"1")
        assert result == {'required': [], 'required_key': [], 'pattern': [], 'either': [], 'either_key': [], 'mapping': ['dc:title']}
        
    # identifier_type = Crossref
    # exist requirements, is_either = False
    result = handle_check_required_pattern_and_either(mapping_data,["dc:title"],"2")
    assert result == {'required': ['item_1617186331708.subitem_1551255648112'], 'required_key': ['dc:title'], 'pattern': [], 'either': [], 'either_key': [], 'mapping': []}
    
    rec_uuid4 = uuid.uuid4()
    record_data = {
        "path":["1"],"recid":"4","title":["title"],"item_title": "title","item_type_id": "1",
        "item_1617258105262": {"attribute_name": "Resource Type","attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794","resourcetype": "conference paper"}]},
        "item_1617605131499": {"attribute_name": "File","attribute_type": "file","attribute_value_mlt": [{"url": {"url": "https://localhost/record/1/files/test.txt"},"date": [{"dateType": "Available","dateValue": "2022-10-03"}],"format": "text/tab-separated-values","filename": "check_2022-03-10.tsv","filesize": [{"value": "460 B"}],"accessrole": "open_access","version_id": "29dd361d-dc7f-49bc-b471-bdb5752afef5","displaytype": "detail","licensetype": "license_12",}]}
    }
    record = record = WekoRecord.create(record_data, id_=rec_uuid4)
    mapping_data = MappingData(record=record)
    # is_either is True, either not in error_list
    result = handle_check_required_pattern_and_either(mapping_data,["dc:title"],"2",is_either=True)
    assert result == {'required': [], 'required_key': [], 'pattern': [], 'either': [['item_1617186331708.subitem_1551255647225', 'item_1617186331708.subitem_1551255648112']], 'either_key': ['dc:title'], 'mapping': []}
    
    # is_either is True, either in error_list
    result = handle_check_required_pattern_and_either(mapping_data,["dc:title"],"2",error_list=result,is_either=True)
    assert result == {'required': [], 'required_key': [], 'pattern': [], 'either': [['item_1617186331708.subitem_1551255647225', 'item_1617186331708.subitem_1551255648112'], [['item_1617186331708.subitem_1551255647225', 'item_1617186331708.subitem_1551255648112']]], 'either_key': ['dc:title', 'dc:title'], 'mapping': []}
# def validattion_item_property_required(
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# def validattion_item_property_either_required(
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# def check_required_data(data, key, repeatable=False):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_required_data():
    data = {True,True,False}
    result = check_required_data(data,"keyx")
    assert result == ["keyx"]

    result = check_required_data(data,"keyx",repeatable=True)
    assert result == ["keyx"]

    data = {True,True}
    result = check_required_data(data,"keyx",repeatable=True)
    assert result == None



# def get_activity_id_of_record_without_version(pid_object=None):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_activity_id_of_record_without_version(db_register,db_records):
    get_activity_id_of_record_without_version()

    pid = db_records[0][0]
    result = get_activity_id_of_record_without_version(pid)
    assert result == "2"


    with patch("weko_workflow.utils.WorkActivity.get_workflow_activity_by_item_id",return_value=None):
        result = get_activity_id_of_record_without_version(pid)
        assert result == None


# def check_suffix_identifier(idt_regis_value, idt_list, idt_type_list):
def test_check_suffix_identifier():
    regis_value = []
    idt_lsit = [1,2,]
    idt_type_list = ["value1","value2","DOI"]




#     def __init__(self, item_id=None, record=None):
#     def get_data_item_type(self):
#     def get_data_by_mapping(self, mapping_key, ignore_empty=False,
#     def get_first_data_by_mapping(self, mapping_key):
#     def get_first_property_by_mapping(self, mapping_key, ignore_empty=False):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# def get_sub_item_value(atr_vm, key):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_sub_item_value():
    atr_vm = {"key1":"value1","key2":"value2","key3":{"key1":"value3_1"}}
    result = get_sub_item_value(atr_vm,"key1")
    data = ["value1","value3_1"]
    for i,r in enumerate(result):
        assert r == data[i]

    atr_vm = [{"key1":"value1"},{"key1":"value2"}]
    data = ["value1","value2"]
    result = get_sub_item_value(atr_vm,"key1")
    for i,r in enumerate(result):
        assert r == data[i]


# def get_item_value_in_deep(data, keys):
def test_get_item_value_in_deep():
    #result = get_item_value_in_deep([],[])
    #assert result == None

    data = {"key1":"value1","key2":"value2","key3":{"key1":"value3_1"}}
    result = get_item_value_in_deep(data,["key1","key2","keyx"])
    test = ["value1","value3_1"]
    for i,r in enumerate(result):
        assert r == test[i]

    data = [{"key1":"value1"},{"key1":"value2"},{"key2":"value3"}]
    test = ["value1","value2"]
    result = get_sub_item_value(data,["key1","key2","keyx"])
    for i,r in enumerate(result):
        assert r == test[i]


#     def __init__(self, item_id):
#     def get_pidstore(self, pid_type='doi', object_uuid=None):
#     def check_pidstore_exist(self, pid_type, chk_value=None):
#     def register_pidstore(self, pid_type, reg_value):
#     def delete_pidstore_doi(self, pid_value=None):
#     def remove_idt_registration_metadata(self):
#     def update_idt_registration_metadata(self, input_value, input_type):
#     def get_idt_registration_data(self):
#     def commit(self, key_id, key_val, key_typ, atr_nam, atr_val, atr_typ):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# def delete_bucket(bucket_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_delete_bucket(db_records, add_file):
    bucket,_ = add_file(db_records[2][2])
    bucket_id = bucket.id
    delete_bucket(bucket_id)
    assert Bucket.get(bucket_id) == None


# def merge_buckets_by_records(main_record_id,
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize("is_delete",[True,False])
def test_merge_buckets_by_records(db_records, add_file,is_delete):
    bucket_11, rbucket_11 = add_file(db_records[1][2])
    bucket_10, rbucket_10 = add_file(db_records[2][2])

    result = merge_buckets_by_records(db_records[1][2].id,db_records[2][2].id,is_delete)
    assert result == rbucket_11.bucket_id

def test_merge_buckets_by_records_error(db_records, add_file):
    bucket_11, rbucket_11 = add_file(db_records[1][2])
    bucket_10, rbucket_10 = add_file(db_records[2][2])
    with patch("weko_workflow.utils.delete_bucket",side_effect=Exception):
        result = merge_buckets_by_records(db_records[1][2].id,db_records[2][2].id,True)
        assert result == None





# def delete_unregister_buckets(record_uuid):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# def set_bucket_default_size(record_uuid):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_set_bucket_default_size(db_records, add_file):
    bucket_10, rbucket_10 = add_file(db_records[2][2])
    set_bucket_default_size(rbucket_10.id)
    bucket = Bucket.get(bucket_10.id)
    assert bucket.quota_size == 50 * 1024 * 1024 * 1024
    assert bucket.max_file_size == 50 * 1024 * 1024 * 1024

    with patch("weko_workflow.utils.Bucket.get",side_effect=Exception):
        set_bucket_default_size(rbucket_10.id)


# def is_show_autofill_metadata(item_type_name):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_is_show_autofill_metadata(client):
    current_app.config.update(
        WEKO_ITEMS_UI_HIDE_AUTO_FILL_METADATA = ["wrong_itemtype1","itemtype2"]
    )
    result = is_show_autofill_metadata("itemtype2")
    assert result == False

    result = is_show_autofill_metadata(None)
    assert result == True
# def is_hidden_pubdate(item_type_name):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_is_hidden_pubdate(client):
    current_app.config.update(
        WEKO_ITEMS_UI_HIDE_PUBLICATION_DATE = ["hidden_itemtype"]
    )
    result = is_hidden_pubdate("not_hidden_itemtype")
    assert result == False

    result = is_hidden_pubdate("hidden_itemtype")
    assert result == True

# def get_parent_pid_with_type(pid_type, object_uuid):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_parent_pid_with_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_parent_pid_with_type(db_records):
    result = get_parent_pid_with_type("doi",db_records[0][2].id)
    assert result == db_records[0][5]

    result = get_parent_pid_with_type("hdl",db_records[4][2].id)
    assert result == None


# def filter_all_condition(all_args):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_filter_all_condition(app, mocker):
    dic = MultiDict()
    for key in WEKO_WORKFLOW_FILTER_PARAMS:
        dic.add("{}_0".format(key), "{}_0".format(key))
    for key in WEKO_WORKFLOW_FILTER_PARAMS:
        dic.add("{}_1".format(key), "{}_1".format(key))
    dic.add("dummy_0", "dummy2")
    with app.test_request_context():
        # mocker.patch("flask.request.args.get", side_effect=dic)
        assert filter_all_condition(dic) == {
            "createdfrom": ["createdfrom_0", "createdfrom_1"],
            "createdto": ["createdto_0", "createdto_1"],
            "workflow": ["workflow_0", "workflow_1"],
            "user": ["user_0", "user_1"],
            "item": ["item_0", "item_1"],
            "status": ["status_0", "status_1"],
            "tab": ["tab_0", "tab_1"],
            "sizewait": ["sizewait_0", "sizewait_1"],
            "sizetodo": ["sizetodo_0", "sizetodo_1"],
            "sizeall": ["sizeall_0", "sizeall_1"],
            "pagesall": ["pagesall_0", "pagesall_1"],
            "pagestodo": ["pagestodo_0", "pagestodo_1"],
            "pageswait": ["pageswait_0", "pageswait_1"],
        }

        # mocker.patch("flask.request.args.get", side_effect=MultiDict())
        assert filter_all_condition(MultiDict()) == {}


# def filter_condition(json, name, condition):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_filter_condition():
    json = {}
    filter_condition(json, "name", "condition")
    assert json == {"name": ["condition"]}

    json = {"name": ["condition"]}
    filter_condition(json, "name", "condition")
    assert json == {"name": ["condition", "condition"]}


# def get_actionid(endpoint):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_actionid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_actionid(action_data):
    result = get_actionid("begin_action")
    assert result == 1
    
    result = get_actionid("wrong_action")
    assert result == None

# def convert_record_to_item_metadata(record_metadata):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_convert_record_to_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_convert_record_to_item_metadata(db_records,item_type):
    record = WekoRecord.get_record(db_records[0][2].id)
    result = convert_record_to_item_metadata(record)
    test = {'id': '1', '$schema': '1', 'pubdate': '2022-08-20', 'title': 'title', 'weko_shared_id': -1, 'item_1617186331708': [{'subitem_1551255647225': 'title', 'subitem_1551255648112': 'ja','subitem_stop/continue': 'Continue'}], 'item_1617186819068': {'subitem_identifier_reg_text': 'test/0000000001', 'subitem_identifier_reg_type': 'JaLC'}, 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'},'item_1617605131499': [{'accessrole': 'open_access','date': [{'dateType': 'Available','dateValue': '2022-10-03'}],'displaytype': 'detail','filename': 'check_2022-03-10.tsv','filesize': [{'value': '460 B'}],'format': 'text/tab-separated-values','is_thumbnail': True,'licensetype': 'license_12','url': {'url': 'https://localhost/record/1/files/test.txt'},'version_id': '29dd361d-dc7f-49bc-b471-bdb5752afef5'}]}
    assert result == test
# def prepare_edit_workflow(post_activity, recid, deposit):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_edit_workflow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_prepare_edit_workflow(app, workflow, db_records,users,mocker):
    #login(client=client, email=users[2]["email"])
    with app.test_request_context():
        login_user(users[2]["obj"])
        mocker.patch("weko_workflow.utils.WekoDeposit.update")
        mocker.patch("weko_workflow.utils.WekoDeposit.commit")
        data = {
            "flow_id":workflow["flow"].id,
            "workflow_id":workflow["workflow"].id,
            "community":1,
            "itemtype_id":1,
            "activity_login_user":1,
            "activity_update_user":1
        }
        recid = db_records[0][0]
        deposit = db_records[0][6]
        result = prepare_edit_workflow(data,recid,deposit)
    
# def handle_finish_workflow(deposit, current_pid, recid):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_handle_finish_workflow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_handle_finish_workflow(workflow, db_records, mocker):
    result = handle_finish_workflow(None, None, None)
    assert result == None
    mocker.patch("weko_deposit.api.WekoDeposit.publish")
    mocker.patch("weko_deposit.api.WekoDeposit.commit")
    mocker.patch("weko_workflow.utils.update_records_sets.delay")
    deposit = db_records[2][6]
    current_pid = db_records[2][0]
    recid = None
    
    handle_finish_workflow(deposit,current_pid,recid)
# def delete_cache_data(key: str):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_delete_cache_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_delete_cache_data(client):
    key = "test_key"
    current_cache.set(key,"test_value")
    delete_cache_data(key)
    assert current_cache.get(key) == None
    
    delete_cache_data(key)
# def update_cache_data(key: str, value: str, timeout=None):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_update_cache_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_update_cache_data(client):
    key = "test_key"
    value = "test_value"
    update_cache_data(key, value, None)
    
    update_cache_data(key, value, 100)
# def get_cache_data(key: str):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_cache_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_cache_data(client):
    key = "test_key"
    value = "test_value"
    current_cache.set(key, value)
    result = get_cache_data(key)
    assert result == value
# def check_an_item_is_locked(item_id=None):
#     def check(workers):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_an_item_is_locked():
    pass
# def get_account_info(user_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_accoutn_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_accoutn_info(users):
    mail, name = get_account_info(users[2]["obj"].id)
    assert mail == users[2]["email"]
    assert name == ""
    
    mail, name = get_account_info(1000)
    assert mail == None
    assert name == None
# def check_existed_doi(doi_link):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_check_existed_doi --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_existed_doi(client,db,db_records):
    url = "https://doi.org/test/0000000001"
    result = check_existed_doi(url)
    test = {
        "isExistDOI":True,
        "isWithdrawnDoi":False,
        "code":0,
        "msg":_('This DOI has been used already for another '
                'item. Please input another DOI.')
    }
    assert result == test
    
    deleted_url = "https//doi.org/deleted"
    doi = PersistentIdentifier(
        pid_type="doi",
        pid_value=deleted_url,
        status=PIDStatus.DELETED
    )
    db.session.add(doi)
    db.session.commit()
    result = check_existed_doi(deleted_url)
    test = {
        "isExistDOI":True,
        "isWithdrawnDoi":True,
        "code":0,
        "msg":_('This DOI was withdrawn. Please input another DOI.')
    }
    assert result == test
    
    result = check_existed_doi("https://doi.org/not_existed_doi")
    test = {
        "isExistDOI":False,
        "isWithdrawnDoi":False,
        "code":0,
        "msg":_("success")
    }
    assert result == test
# def get_url_root():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_url_root --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_url_root(app):
    app.config["THEME_SITEURL"] = "https://weko3.ir.rcos.nii.ac.jp"
    app.config["SERVER_NAME"] = "TEST_SERVER"
    with app.app_context():
        assert get_url_root() == "https://weko3.ir.rcos.nii.ac.jp/"
        app.config["THEME_SITEURL"] = "https://weko3.ir.rcos.nii.ac.jp/"
        assert get_url_root() == "https://weko3.ir.rcos.nii.ac.jp/"

    app.config["THEME_SITEURL"] = "https://weko3.ir.rcos.nii.ac.jp"
    app.config["SERVER_NAME"] = "TEST_SERVER"
    with app.test_request_context():
        assert get_url_root() == "http://TEST_SERVER/"


# def get_record_by_root_ver(pid_value):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_record_by_root_ver -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_record_by_root_ver(app, db_records):
    app.config.update(
        DEPOSIT_DEFAULT_STORAGE_CLASS="S",
    )
    record, files = get_record_by_root_ver("1")

    assert files == []
    assert record == {'_oai': {'id': 'oai:weko3.example.org:00000001', 'sets': ['1']}, 'path': ['1'], 'owner': '1', 'recid': '1', 'title': ['title'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-08-20'}, '_buckets': {'deposit': '3e99cfca-098b-42ed-b8a0-20ddd09b3e02'}, '_deposit': {'id': '1', 'pid': {'type': 'depid', 'value': '1', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'title', 'author_link': [], 'item_type_id': '1', 'publish_date': '2022-08-20', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'title', 'subitem_1551255648112': 'ja','subitem_stop/continue': 'Continue'}]}, "item_1617186819068": {"attribute_name": "Identifier Registration","attribute_value_mlt": [{"subitem_identifier_reg_text" :"test/0000000001","subitem_identifier_reg_type": "JaLC"}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]},'item_1617605131499': {'attribute_name': 'File','attribute_type': 'file','attribute_value_mlt': [{'accessrole': 'open_access','date': [{'dateType': 'Available','dateValue': '2022-10-03'}],'displaytype': 'detail','filename': 'check_2022-03-10.tsv','filesize': [{'value': '460 ''B'}],'format': 'text/tab-separated-values','is_thumbnail': True,'licensetype': 'license_12','url': {'url': 'https://localhost/record/1/files/test.txt'},'version_id': '29dd361d-dc7f-49bc-b471-bdb5752afef5'}]},'item_1664947259584': {'attribute_name': 'サムネイル','attribute_value_mlt': [{'subitem_thumbnail': [{'thumbnail_label': 'test.png','thumbnail_url': '/api/files/29ad484d-4ed1-4caf-8b21-ab348ae7bf28/test.png?versionId=ecd5715e-4ca5-4e45-b93c-5089f52860a0'}]}]}, 'relation_version_is_last': True}


# def get_disptype_and_ver_in_metainfo(metadata):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_disptype_and_ver_in_metainfo -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_disptype_and_ver_in_metainfo(db_records):
    record = WekoRecord.get_record(db_records[0][2].id)
    result = get_disptype_and_ver_in_metainfo(record)
    file = json_data("data/test_records.json")[0]["item_1617605131499"]["attribute_value_mlt"][0]
    version_id = file["version_id"]
    displaytype = file["displaytype"]
    licensetype = file["licensetype"]
    test = {
        version_id:{
            "displaytype":displaytype,
            "licensetype":licensetype
        }
    }
    assert result == test
# def set_files_display_type(record_metadata, files):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_set_files_display_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_set_files_display_type(db_records):
    record = WekoRecord.get_record(db_records[0][2].id)
    file = json_data("data/test_records.json")[0]["item_1617605131499"]["attribute_value_mlt"][0]
    version_id = file["version_id"]
    displaytype = file["displaytype"]
    licensetype = file["licensetype"]
    files = [
        {"version_id":version_id}
    ]
    test = [
        {
            "version_id":version_id,
            "displaytype":displaytype,
            "licensetype":licensetype
        }
    ]
    result = set_files_display_type(record,files)
    assert result == test
# def get_thumbnails(files, allow_multi_thumbnail=True):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_thumbnails -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_thumbnails(db_records):
    record = WekoRecord.get_record(db_records[0][2].id)

    files = [
        {
            "name":"file1",
            "is_thumbnail":True
        },
        {
            "name":"file2",
            "is_thumbnail":True
        },
        {
            "name":"file3",
            "is_thumbnail":False
        }
    ]
    result = get_thumbnails(files,True)
    assert result == files[:2]
    
    result = get_thumbnails(files,False)
    assert result == [files[0]]
# def get_allow_multi_thumbnail(item_type_id, activity_id=None):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_allow_multi_thumbnail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_allow_multi_thumbnail(app, db_register):
    result = get_allow_multi_thumbnail(1,"1")
    assert result == False
    
    result = get_allow_multi_thumbnail(1,None)
    assert result == None
# def is_usage_application_item_type(activity_detail):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_is_usage_application_item_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_is_usage_application_item_type(db_register):
    activity = db_register["activities"][0]
    result = is_usage_application_item_type(activity)
    assert result == False
    
    current_app.config.update(
        WEKO_ITEMS_UI_APPLICATION_ITEM_TYPES_LIST=["テストアイテムタイプ"]
    )
    result = is_usage_application_item_type(activity)
    assert result == True
# def is_usage_application(activity_detail):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_is_usage_application -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_is_usage_application(db_register):
    activity = db_register["activities"][0]
    result = is_usage_application(activity)
    assert result == False
    
    current_app.config.update(
        WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPES_LIST=["テストアイテムタイプ"]
    )
    result = is_usage_application(activity)
    assert result == True
# def send_mail_reminder(mail_info):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_send_mail_reminder -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_send_mail_reminder(client,mocker):
    # nomal
    mocker.patch("weko_workflow.utils.replace_characters",return_value="mail body")
    with patch("weko_workflow.utils.get_mail_data",return_value=(None,"body")):
        with patch("weko_workflow.utils.send_mail",return_value=True):
            send_mail_reminder({})
    
    # can not get body
    with patch("weko_workflow.utils.get_mail_data",return_value=(None,None)):
        with patch("weko_workflow.utils.send_mail",return_value=True):
            with pytest.raises(ValueError) as e:
                send_mail_reminder({})
                assert str(e.value) == 'Cannot get email template'
    
    # can not send mail
    with patch("weko_workflow.utils.get_mail_data",return_value=(None,"body")):
        with patch("weko_workflow.utils.send_mail",return_value=False):
            with pytest.raises(ValueError) as e:
                send_mail_reminder({})
                assert str(e.value) == 'Cannot send mail'
# def send_mail_approval_done(mail_info):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_send_mail_approval_done -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_send_mail_approval_done(mocker):
    mocker.patch("weko_workflow.utils.replace_characters",return_value="body")
    mocker.patch("weko_workflow.utils.send_mail")
    with patch("weko_workflow.utils.email_pattern_approval_done",return_value=("subject","body")):
        send_mail_approval_done({})
    with patch("weko_workflow.utils.email_pattern_approval_done",return_value=(None,None)):
        send_mail_approval_done({})
# def send_mail_registration_done(mail_info):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_send_mail_registration_done -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_send_mail_registration_done(app,users,mocker):
    mocker.patch("weko_workflow.utils.replace_characters",return_value="body")
    mocker.patch("weko_workflow.utils.send_mail")
    mail_info = {
        "item_type_name":"テストアイテムタイプ"
    }
    with app.test_request_context():
        login_user(users[2]["obj"])
        with patch("weko_workflow.utils.email_pattern_registration_done",return_value=("subject","body")):
            send_mail_registration_done(mail_info)
            
        with patch("weko_workflow.utils.email_pattern_registration_done",return_value=(None, None)):
            send_mail_registration_done(mail_info)
# def send_mail_request_approval(mail_info):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_send_mail_request_approval -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_send_mail_request_approval(mocker):
    mocker.patch("weko_workflow.utils.replace_characters",return_value="value")
    mocker.patch("weko_workflow.utils.send_mail")

    with patch("weko_workflow.utils.email_pattern_request_approval",return_value=("subject","value")):
        mail_info = {
            "next_step":"approval_advisor",
            "advisor_mail":"advisor.mail@test.org"
        }
        send_mail_request_approval(mail_info)
        mail_info = {
            "next_step":"approval_guarantor",
            "guarantor_mail":"guarantor.mail@test.org"
        }
        send_mail_request_approval(mail_info)
        mail_info = {
            "next_step":"other step"
        }
        send_mail_request_approval(mail_info)
        
        send_mail_request_approval({})
# def send_mail(subject, recipient, body):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_send_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_send_mail(mocker):
    mocker.patch("weko_workflow.utils.MailSettingView.send_statistic_mail")
    send_mail("subject", "recipient", "body")
    
    send_mail(None, None, None)
# def email_pattern_registration_done(user_role, item_type_name):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_email_pattern_registration_done -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_email_pattern_registration_done(app,users,mocker):
    mock_path = "weko_workflow.utils.get_mail_data"
    with app.test_request_context():
        config = current_app.config
        login_user(users[2]["obj"])
        from weko_items_ui.utils import get_current_user_role
        role = get_current_user_role()
        
        mocker_data = mocker.patch(mock_path)
        subject, body = email_pattern_registration_done(role, "テストアイテムタイプ")
        assert subject == None
        assert body == None
        
        config.update(
            WEKO_ITEMS_UI_OUTPUT_REPORT="テストアイテムタイプ"
        )
        mocker_data = mocker.patch(mock_path)
        email_pattern_registration_done(role, "テストアイテムタイプ")
        mocker_data.assert_called_with(config["WEKO_WORKFLOW_RECEIVE_OUTPUT_REGISTRATION"])
        
        
        config.update(
            WEKO_ITEMS_UI_OUTPUT_REPORT="",
            WEKO_ITEMS_UI_USAGE_REPORT = "テストアイテムタイプ"
        )
        mocker_data = mocker.patch(mock_path)
        email_pattern_registration_done(role, "テストアイテムタイプ")
        mocker_data.assert_called_with(config["WEKO_WORKFLOW_RECEIVE_USAGE_REPORT"])
        
        config.update(
            WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPES_LIST = ["テストアイテムタイプ"]
        )
        logout_user()
        login_user(users[4]["obj"])
        role = get_current_user_role()
        config.update(
            WEKO_ITEMS_UI_OUTPUT_REPORT="",
        )
        mocker_data = mocker.patch(mock_path)
        email_pattern_registration_done(role, "テストアイテムタイプ")
        mocker_data.assert_called_with(config["WEKO_WORKFLOW_RECEIVE_USAGE_APP_BESIDE"
                                                "_PERFECTURE_AND_LOCATION_DATA_OF"
                                                "_GENERAL_USER"])
        config.update(
            WEKO_ITEMS_UI_APPLICATION_FOR_PERFECTURES="テストアイテムタイプ",
        )
        mocker_data = mocker.patch(mock_path)
        email_pattern_registration_done(role, "テストアイテムタイプ")
        mocker_data.assert_called_with(config["WEKO_WORKFLOW_PERFECTURE_OR_LOCATION_DATA"
                                                "_OF_GENERAL_USER"])

        logout_user()
        login_user(users[8]["obj"])
        role = get_current_user_role()
        config.update(
            WEKO_ITEMS_UI_APPLICATION_FOR_PERFECTURES="",
        )
        mocker_data = mocker.patch(mock_path)
        email_pattern_registration_done(role, "テストアイテムタイプ")
        mocker_data.assert_called_with(config["WEKO_WORKFLOW_RECEIVE_USAGE_APP_BESIDE"
                                                "_PERFECTURE_AND_LOCATION_DATA_OF_STUDENT_OR"
                                                "_GRADUATED_STUDENT"])
        
        config.update(
            WEKO_ITEMS_UI_APPLICATION_FOR_PERFECTURES="テストアイテムタイプ",
        )
        mocker_data = mocker.patch(mock_path)
        email_pattern_registration_done(role, "テストアイテムタイプ")
        mocker_data.assert_called_with(config["WEKO_WORKFLOW_PERFECTURE_OR_LOCATION_DATA"
                                   "_OF_STUDENT_OR_GRADUATED_STUDENT"])
        
        logout_user()
        login_user(users[2]["obj"])
        role = get_current_user_role()
        subject, body = email_pattern_registration_done(role, "テストアイテムタイプ")
        assert subject == None
        assert body == None


# def email_pattern_request_approval(item_type_name, next_action):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_email_pattern_request_approval -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_email_pattern_request_approval(app, mocker):
    config = current_app.config
    mock_path = "weko_workflow.utils.get_mail_data"
    item_type_name = "テストアイテムタイプ"
    subject, body = email_pattern_request_approval(item_type_name,"next_action")
    assert subject == None
    assert body == None
    
    config.update(
        WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPES_LIST = ["テストアイテムタイプ"]
    )
    mocker_data = mocker.patch(mock_path)
    email_pattern_request_approval(item_type_name, "approval_guarantor")
    mocker_data.assert_called_with(config["WEKO_WORKFLOW_REQUEST_APPROVAL_TO_GUARANTOR_OF_USAGE_APP"])
    
    mocker_data = mocker.patch(mock_path)
    email_pattern_request_approval(item_type_name, "approval_advisor")
    mocker_data.assert_called_with(config["WEKO_WORKFLOW_REQUEST_APPROVAL_TO_ADVISOR_OF_USAGE_APP"])
    
    email_pattern_request_approval(item_type_name, "next_action")


# def email_pattern_approval_done(item_type_name):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_email_pattern_approval_done -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_email_pattern_approval_done(client,mocker):
    config = current_app.config
    mock_path = "weko_workflow.utils.get_mail_data"
    item_type_name = "テストアイテムタイプ"
    
    subject, body = email_pattern_approval_done(item_type_name)
    assert subject == None
    assert body == None
    
    config.update(
        WEKO_ITEMS_UI_OUTPUT_REPORT="テストアイテムタイプ"
    )
    mocker_data = mocker.patch(mock_path)
    email_pattern_approval_done(item_type_name)
    mocker_data.assert_called_with(config["WEKO_WORKFLOW_APPROVE_OUTPUT_REGISTRATION"])
    
    config.update(
        WEKO_ITEMS_UI_OUTPUT_REPORT="",
        WEKO_ITEMS_UI_USAGE_REPORT="テストアイテムタイプ"
    )
    mocker_data = mocker.patch(mock_path)
    email_pattern_approval_done(item_type_name)
    mocker_data.assert_called_with(config["WEKO_WORKFLOW_APPROVE_USAGE_REPORT"])
    
    config.update(
        WEKO_ITEMS_UI_USAGE_REPORT="",
        WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPES_LIST=["テストアイテムタイプ"]
    )
    mocker_data = mocker.patch(mock_path)
    email_pattern_approval_done(item_type_name)
    mocker_data.assert_called_with(config["WEKO_WORKFLOW_APPROVE_USAGE_APP_BESIDE_LOCATION_DATA"])
    
    config.update(
        WEKO_ITEMS_UI_APPLICATION_FOR_LOCATION_INFORMATION="テストアイテムタイプ"
    )
    mocker_data = mocker.patch(mock_path)
    email_pattern_approval_done(item_type_name)
    mocker_data.assert_called_with(config["WEKO_WORKFLOW_APPROVE_LOCATION_DATA"])


# def get_mail_data(file_name):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_mail_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_mail_data(mocker):
    mocker.patch("weko_workflow.utils.get_file_path")
    mocker.patch("weko_workflow.utils.get_subject_and_content")
    get_mail_data("test_file")
# def get_subject_and_content(file_path):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_subject_and_content -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_subject_and_content():
    filename = join(dirname(__file__),"data/test_mail.txt")
    subject, body=get_subject_and_content(filename)
    assert subject == "this is subject"
    assert body == "body1\nbody2\nbody3"
    
    subject, body = get_subject_and_content("wrong_file_path")
    assert subject == None
    assert body == None
# def get_file_path(file_name):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_file_path -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_file_path(app):
    current_app.config.update(WEKO_WORKFLOW_MAIL_TEMPLATE_FOLDER_PATH="test_dir")
    result = get_file_path("filepath")
    assert result == "test_dir/filepath"
    
    result = get_file_path(None)
    assert result == ""
    
# def replace_characters(data, content):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_replace_characters -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_replace_characters():
    context = "url is [10]. restricted_fullname is [restricted_fullname]. advisor_name is [8]."
    data = {
        "url":"https://test_url.com",
        "restricted_fullname":"test_file.txt"
    }
    test = "url is https://test_url.com. restricted_fullname is test_file.txt. advisor_name is ."
    
    result = replace_characters(data,context)
    assert result == test
# def get_register_info(activity_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_register_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_register_info(app, db, db_register,users,mocker):
    with app.test_request_context():
        login_user(users[2]["obj"])
        activity_id = db_register["activities"][1].activity_id
        # item link
        db_history2 = ActivityHistory(
            activity_id=activity_id,
            action_id=5,
            action_date=datetime.datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        )
        with db.session.begin_nested():
            db.session.add(db_history2)
        db.session.commit()
        email, date = get_register_info(activity_id)
        assert email == users[2]["email"]
        assert date == datetime.datetime.today().strftime("%Y-%m-%d")
        db_history1 = ActivityHistory(
            activity_id=activity_id,
            action_id=3,
            action_user=users[0]["id"],
            action_status="F",
            action_date=datetime.datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        )
        with db.session.begin_nested():
            db.session.add(db_history1)
        db.session.commit()
        email, date = get_register_info(activity_id)
        assert email == users[0]["email"]
        assert date == "2022-04-14"
# def get_approval_dates(mail_info):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_approval_dates -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_approval_dates(app,mocker):
    datetime_mock = mocker.patch("weko_workflow.utils.datetime")
    datetime_mock.today.return_value=datetime.datetime(2022,10,6,1,2,3,4)
    mail_info = {
    }
    test = {
        "approval_date":"2022-10-06",
        'approval_date_after_7_days': '2022-10-13',
        '31_march_corresponding_year': '2023-03-31'
    }
    get_approval_dates(mail_info)
    assert mail_info == test

    
    datetime_mock.today.return_value=datetime.datetime(2022,10,1,1,2,3,4)
    mail_info = {
    }
    test = {
        "approval_date":"2022-10-01",
        'approval_date_after_7_days': '2022-10-08',
        '31_march_corresponding_year': '2022-03-31'
    }
    get_approval_dates(mail_info)
    assert mail_info == test
# def get_item_info(item_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_item_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_item_info(db_records):
    result = get_item_info(db_records[0][3].id)
    assert result == {'type': 'depid', 'value': '1', 'revision_id': 0, 'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': '', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper', 'subitem_thumbnail': [{'thumbnail_url': '/api/files/29ad484d-4ed1-4caf-8b21-ab348ae7bf28/test.png?versionId=ecd5715e-4ca5-4e45-b93c-5089f52860a0', 'thumbnail_label': 'test.png'}]}
    
    with patch("weko_workflow.utils.ItemsMetadata.get_record",side_effect=Exception("test error")):
        result = get_item_info("item_id")
        assert result == {}
    
    result = get_item_info("")
    assert result == {}
# def get_site_info_name():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_site_info_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_site_info_name(db):
    name_en, name_ja = get_site_info_name()
    assert name_en == ""
    assert name_ja == ""
    
    site_info = {
        "site_name":[
            {"index":"test_index","name":"test_site","language":"en"}
        ],
        "notify":[
            {"notify_name":"test_notify","language":"en"}
        ],
        "copy_right":"test_copy_right",
        "description":"this is test site",
        "keyword":"test",
        "favicon":"test_favicon",
        "favicon_name":"test_favicon_name",
        "google_tracking_id_user":"test_google_tracking_user",
        "addthis_user_id":"1",
        "ogp_image":""
    }
    SiteInfo.update(site_info)
    
    name_en, name_ja = get_site_info_name()
    assert name_en == "test_site"
    assert name_ja == "test_site"
    
    site_info["site_name"] = [
        {"index":"test_index","name":"test_site","language":"en"},
        {"index":"test_index","name":"テストサイト","language":"ja"}
    ]
    SiteInfo.update(site_info)
    
    name_en, name_ja = get_site_info_name()
    assert name_en == "test_site"
    assert name_ja == "テストサイト"
    
    site_info["site_name"] = [
        {"index":"test_index","name":"test_site","language":"en"},
        {"index":"test_index","name":"テストサイト","language":"ja"},
        {"index":"test_index","name":"other_test_site","language":"other"}
    ]
    SiteInfo.update(site_info)
    name_en, name_ja = get_site_info_name()
    assert name_en == ""
    assert name_ja == ""
# def get_default_mail_sender():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_default_mail_sender -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_default_mail_sender(db):
    mail_config = MailConfig(mail_default_sender="test_sender")
    db.session.add(mail_config)
    db.session.commit()
    
    result = get_default_mail_sender()
    assert result == "test_sender"
# def set_mail_info(item_info, activity_detail, guest_user=False):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_set_mail_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_set_mail_info(app, db_register, mocker):
    mocker.patch("weko_workflow.utils.get_site_info_name",return_value=("name_en","name_ja"))
    mocker.patch("weko_workflow.utils.get_default_mail_sender",return_value="default_sender")
    mocker.patch("weko_workflow.utils.get_register_info",return_value=("user@test.org","2022-10-10"))
    item_info = {
        "subitem_university/institution":"test_institution",
        "subitem_fullname":"test_fullname",
        "subitem_mail_address":"test@test.org",
        "subitem_research_title":"test_research_title",
        "subitem_dataset_usage":"test_dataset",
        "subitem_advisor_fullname":"test advisor",
        "subitem_guarantor_fullname":"test guarantor",
        "subitem_advisor_affiliation":"test advisor affiliation",
        "subitem_guarantor_affiliation":"test guarantor affiliation",
        "subitem_advisor_mail_address":"advisor@test.org",
        "subitem_guarantor_mail_address":"guarantor@test.org",
        "subitem_title":"test_sub_title",
        "subitem_restricted_access_name":"test access name",
        'subitem_restricted_access_university/institution':"test_restricted_institution",
        "subitem_restricted_access_research_title":"test_restricted_research_title",
        "subitem_restricted_access_dataset_usage":"test_restricted_dataset",
        "subitem_restricted_access_application_date":"test_restricted_date",
        "subitem_restricted_access_mail_address":"restricted@test.org",
    }
    activity_id = db_register["activities"][0].activity_id
    test = {
        "university_institution":"test_institution",
        "fullname":"test_fullname",
        "activity_id":activity_id,
        "mail_address":"test@test.org",
        "research_title":"test_research_title",
        "dataset_requested":"test_dataset",
        "register_date":"",
        "advisor_name":"test advisor",
        "guarantor_name":"test guarantor",
        "url":"http://TEST_SERVER.localdomain/",
        "advisor_affilication":"test advisor affiliation",
        "guarantor_affilication":"test guarantor affiliation",
        "advisor_mail":"advisor@test.org",
        "guarantor_mail":"guarantor@test.org",
        "register_user_mail":"",
        "report_number":activity_id,
        "registration_number":activity_id,
        "output_registration_title":"test_sub_title",
        "restricted_fullname":"test access name",
        'restricted_university_institution':"test_restricted_institution",
        "restricted_activity_id":activity_id,
        "restricted_research_title":"test_restricted_research_title",
        "restricted_data_name":"test_restricted_dataset",
        "restricted_application_date":"test_restricted_date",
        "restricted_mail_address":"restricted@test.org",
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_approver_name":"",
        "restricted_approver_affiliation":"",
        "restricted_site_name_ja":"name_ja",
        "restricted_site_name_en":"name_en",
        "restricted_site_mail":"default_sender",
        "restricted_site_url":"https://localhost",
        "mail_recipient":"restricted@test.org",
        "restricted_supervisor":"",
        "restricted_reference":""
    }
    with app.test_request_context():
        result = set_mail_info(item_info,db_register["activities"][0],True)
        assert result == test
    test = {
        "university_institution":"test_institution",
        "fullname":"test_fullname",
        "activity_id":activity_id,
        "mail_address":"test@test.org",
        "research_title":"test_research_title",
        "dataset_requested":"test_dataset",
        "register_date":"2022-10-10",
        "advisor_name":"test advisor",
        "guarantor_name":"test guarantor",
        "url":"http://TEST_SERVER.localdomain/",
        "advisor_affilication":"test advisor affiliation",
        "guarantor_affilication":"test guarantor affiliation",
        "advisor_mail":"advisor@test.org",
        "guarantor_mail":"guarantor@test.org",
        "register_user_mail":"user@test.org",
        "report_number":activity_id,
        "registration_number":activity_id,
        "output_registration_title":"test_sub_title",
        "restricted_fullname":"test access name",
        'restricted_university_institution':"test_restricted_institution",
        "restricted_activity_id":activity_id,
        "restricted_research_title":"test_restricted_research_title",
        "restricted_data_name":"test_restricted_dataset",
        "restricted_application_date":"test_restricted_date",
        "restricted_mail_address":"restricted@test.org",
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_approver_name":"",
        "restricted_approver_affiliation":"",
        "restricted_site_name_ja":"name_ja",
        "restricted_site_name_en":"name_en",
        "restricted_site_mail":"default_sender",
        "restricted_site_url":"https://localhost",
        "mail_recipient":"restricted@test.org",
        "restricted_supervisor":"",
        "restricted_reference":""
    }
    with app.test_request_context():
        result = set_mail_info(item_info,db_register["activities"][0],False)
        assert result == test
# def process_send_reminder_mail(activity_detail, mail_template):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_process_send_reminder_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_process_send_reminder_mail(db, db_register,mocker):
    mocker.patch("weko_workflow.utils.get_item_info",return_value={})
    mocker.patch("weko_workflow.utils.set_mail_info",return_value={})
    mock_sender = mocker.patch("weko_workflow.utils.send_mail_reminder")
    process_send_reminder_mail(db_register["activities"][1],"template")
    mock_sender.assert_called_with({"mail_address":"comadmin@test.org","template":"template"})
    
    user_profile = UserProfile(
        user_id=db_register["activities"][1].activity_login_user,
        _username="sysadmin",
        fullname="sysadmin user",
        timezone="asia",
        language="japanese",
    )
    db.session.add(user_profile)
    db.session.commit()
    mock_sender = mocker.patch("weko_workflow.utils.send_mail_reminder")
    process_send_reminder_mail(db_register["activities"][1],"template")
    mock_sender.assert_called_with({"mail_address":"comadmin@test.org","template":"template","fullname":"sysadmin user"})

    with patch("weko_items_ui.utils.get_user_information",return_value={"email":""}):
        with pytest.raises(ValueError) as e:
            process_send_reminder_mail(db_register["activities"][1],"template")
            assert str(e.value) == "Cannot get receiver mail address"
    
    with patch("weko_items_ui.utils.get_user_information",return_value={"email":"test@test.org","fullname":""}):
        with patch("weko_workflow.utils.send_mail_reminder",side_effect=ValueError("test error")):
            with pytest.raises(ValueError) as e:
                process_send_reminder_mail(db_register["activities"][1],"template")
                assert str(e.value) == "test error"

# def process_send_notification_mail(
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_process_send_notification_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_process_send_notification_mail(db,db_register, mocker):
    mocker.patch("weko_workflow.utils.get_item_info",return_value={})
    mocker.patch("weko_workflow.utils.set_mail_info",return_value={})
    def mock_approval_date(data):
        data["approval_date"] = "2022-10-10"
        data["approval_date_after_7_days"] = "2022-10-17"
        data["31_march_corresponding_year"] = "2023-03-31"
    activity = db_register["activities"][0]
    mocker.patch("weko_workflow.utils.get_approval_dates",side_effect=mock_approval_date)
    mock_send_registration = mocker.patch("weko_workflow.utils.send_mail_registration_done")
    mock_send_approval_req = mocker.patch("weko_workflow.utils.send_mail_request_approval")
    mock_send_approval_done = mocker.patch("weko_workflow.utils.send_mail_approval_done")
    data = {
        "item_type_name":"テストアイテムタイプ",
        "next_step":"next_step",
        "approval_date":"2022-10-10",
        "approval_date_after_7_days": "2022-10-17",
        "31_march_corresponding_year": "2023-03-31"
    }
    
    process_send_notification_mail(activity,"item_login","next_step")
    mock_send_registration.assert_called_with(data)
    data = {
        "item_type_name":"テストアイテムタイプ",
        "next_step":"approval_",
        "approval_date":"2022-10-10",
        "approval_date_after_7_days": "2022-10-17",
        "31_march_corresponding_year": "2023-03-31"
    }
    process_send_notification_mail(activity,"item_registration","approval_")
    mock_send_approval_req.assert_called_with(data)
    data = {
        "item_type_name":"テストアイテムタイプ",
        "next_step":"next_step",
        "approval_date":"2022-10-10",
        "approval_date_after_7_days": "2022-10-17",
        "31_march_corresponding_year": "2023-03-31"
    }
    process_send_notification_mail(activity,"approval_administrator","next_step")
    mock_send_approval_done.assert_called_with(data)
    process_send_notification_mail(activity,"other_step","next_step")
# def get_application_and_approved_date(activities, columns):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_application_and_approval_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_application_and_approval_date(db,db_register,users):
    activities = db_register["activities"]
    histories = list()
    for activity in activities:
        histories.append(ActivityHistory(
            activity_id=activity.activity_id,
            action_id=3,
            action_user=users[0]["id"],
            action_status="F",
            action_date=datetime.datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        ))
        histories.append(ActivityHistory(
            activity_id=activity.activity_id,
            action_id=4,
            action_user=users[0]["id"],
            action_status="F",
            action_date=datetime.datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        ))
        histories.append(ActivityHistory(
            activity_id=activity.activity_id,
            action_id=2,
            action_user=users[0]["id"],
            action_status="F",
            action_date=datetime.datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        ))
    db.session.add_all(histories)
    db.session.commit()
    get_application_and_approved_date(activities,["approved_date"])
# def get_workflow_item_type_names(activities: list):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_workflow_item_type_names -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_workflow_item_type_names(db_register):
    activities = db_register["activities"]
    get_workflow_item_type_names(activities)

# def create_usage_report(activity_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_create_usage_report -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_create_usage_report(app,db_register, mocker):
    activity = db_register["activities"][1]
    result = create_usage_report(activity.activity_id)
    assert result == None
    
    current_app.config.update(
        WEKO_WORKFLOW_USAGE_REPORT_WORKFLOW_NAME="test workflow1"
    )
    mock_create = mocker.patch("weko_workflow.utils.create_record_metadata",return_value="test_data")
    result = create_usage_report(activity.activity_id)
    assert result == "test_data"
    mock_create.assert_called_with(
        {"workflow_id":activity.workflow_id,"flow_id":activity.flow_id},
        activity.item_id,activity.activity_id,db_register["workflow"],None
    )
# def create_record_metadata(
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_create_record_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_create_record_metadata(app,db,users,db_register,mocker):
    activity = db_register["activities"][1]
    
    item_id = activity.item_id
    activity_id = activity.activity_id
    workflow = db_register["workflow"]
    activity_data = {
        "workflow_id":workflow.id,
        "flow_id":workflow.flow_id
    }
    def mock_modify_item_metadata(item_,item_type_id_,new_activity_id_,activity_id_,data_dict_,schema_,owner_id_,related_title_):
        item_ = {'id': '1.1', 'pid': {'type': 'depid', 'value': '1.1', 'revision_id': 0}, 'lang': 'ja', 'owner': '1', 'title': 'related_title - ja_usage_title - 2 - ', 'owners': [1], 'status': 'published', '$schema': 'items/jsonschema/1', 'pubdate': '2022-08-20', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}, 'shared_user_id': -1, 'item_1617186331708': [{'subitem_1551255647225': 'ff', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}}
    mocker.patch("weko_workflow.utils.modify_item_metadata",side_effect=mock_modify_item_metadata)
    
    class MockDeposit:
        def __init__(self,record_,model):
            pass
        @classmethod
        def get_record(pid_id):
            return "test_record"
        def update(self, status, metadata):
            pass
        def commit(self):
            pass
        def publish(self):
            pass
        def newversion(self, pid):
            return None
        @property
        def id(self):
            return uuid.uuid4()
        def __getitem__(self,key):
            if key == "_deposit":
                return {"id":"test id"}
    mocker.patch("weko_workflow.utils.WekoDeposit",side_effect=MockDeposit)
    def mock_create_deposit(pid_):
        PersistentIdentifier.create(
            pid_type='recid',
            pid_value=str(pid_),
            object_type="rec",
            status=PIDStatus.REGISTERED)
    mocker.patch("weko_workflow.utils.create_deposit",side_effect=mock_create_deposit)
    mocker.patch("weko_workflow.utils.update_activity_action")
    mocker.patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_activity")
    with app.test_request_context():
        login_user(users[2]["obj"])
        result = create_record_metadata(activity_data,item_id,activity_id,workflow,"related_title")
        assert result == "new_activity"

# def modify_item_metadata(
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_modify_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_modify_item_metadata(app,db,db_register,users,mocker):
    activity = db_register["activities"][1]
    item_id = activity.item_id
    item = ItemsMetadata.get_record(id_=item_id).dumps()
    workflow = db_register["workflow"]
    item_type_id = workflow.itemtype_id
    activity_id = activity.activity_id
    data_dict={'subitem_1551255647225': 'title', 'subitem_1551255648112': 'ja', 'subitem_identifier_reg_text': 'test_2/0000000001', 'subitem_identifier_reg_type': 'JaLC'}
    schema = ItemTypes.get_by_id(item_type_id).schema
    owner_id = users[2]["id"]
    related_title = "related_title"

    user_profile = UserProfile(
        user_id=db_register["activities"][1].activity_login_user,
        _username="sysadmin",
        fullname="sysadmin user",
        timezone="asia",
        language="japanese",
        _displayname="display sysadmin"
    )
    db.session.add(user_profile)
    db.session.commit()
    app.config.update(
        WEKO_ITEMS_UI_USAGE_REPORT_TITLE = {"en":"en_usage_title","ja":"ja_usage_title"}
    )
    data_dict = {
        'subitem_1551255647225': 'title',
        'subitem_1551255648112': 'ja',
        'subitem_identifier_reg_text': 'test_2/0000000001',
        'subitem_identifier_reg_type': 'JaLC'
    }
    schema_dict = {
        "subitem_1551255647225":"item_1617186331708",
        "subitem_1551255648112":"item_1617186331708",
        "subitem_identifier_reg_text":"item_1617186819068",
        "subitem_identifier_reg_type":"item_1617186819068"
    }
    
    test = {'id': '1.1', 'pid': {'type': 'depid', 'value': '1.1', 'revision_id': 0}, 'lang': 'ja', 'owner': '1', 'title': 'related_title - ja_usage_title - 2 - ', 'owners': [1], 'status': 'published', '$schema': 'items/jsonschema/1', 'pubdate': '2022-08-20', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}, 'shared_user_id': -1, 'item_1617186331708': [{'subitem_1551255647225': 'ff', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}}
    mocker.patch("weko_workflow.utils.get_shema_dict",return_value=schema_dict)
    result = modify_item_metadata(item,item_type_id,"new activity",activity_id,
                         data_dict,schema,owner_id,related_title)

    assert result == test
    result = modify_item_metadata(None,item_type_id,"new activity",activity_id,
                         data_dict,schema,owner_id,related_title)
    assert result == None
# def replace_title_subitem(subitem_title, subitem_item_title_language):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_replace_title_subitem -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_replace_title_subitem(app):
    current_app.config.update(
        WEKO_ITEMS_UI_USAGE_APPLICATION_TITLE={"en":"usage_app_title"},
        WEKO_ITEMS_UI_USAGE_REPORT_TITLE={"en":"usage_report_title"}
    )
    subitem_title = "this title is usage_app_title"
    result = replace_title_subitem(subitem_title,"en")
    assert result == "this title is usage_report_title"
# def get_shema_dict(properties, data_dict):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_schema_dict -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_schema_dict():
    #data_dict = {
    #    'subitem_1551255647225': 'title',
    #    'subitem_1551255648112': 'ja',
    #    'subitem_identifier_reg_text': 'test_2/0000000001',
    #    'subitem_identifier_reg_type': 'JaLC'
    #}
    
    data_dict={
        "key1":"vlaue1",
        "key2":"value2",
        "key3":"value3"
    }
    properties = {
        "items_1":{
            "items":{
                "name":"test item1"
            }
        },
        "items_2":{
            "items":{
                "name":"test item2",
                "properties":{
                    "key1":"value1",
                    "keyx":"valuex"
                }
            }
        },
        "system":{
            "properties":{
                "key3":"value3"
            }
        }
    }
    test = {"key1":"items_2","key3":"system"}
    result = get_shema_dict(properties,data_dict)
    assert result == test
# def create_deposit(item_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_create_deposit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_create_deposit(mocker):
    item_id = uuid.uuid4()
    mocker.patch("weko_workflow.utils.WekoDeposit.create")
    create_deposit(item_id)

# def update_activity_action(activity_id, owner_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_update_activity_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_update_activity_action(app,users,db_register):
    update_activity_action("1",1)
    
    current_app.config.update(
        WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION_USAGE_APPLICATION = "Start"
    )
    activity = db_register["activities"][1]
    update_activity_action(activity.activity_id,1)
    activity_action = WorkActivity().get_activity_action_comment(
        activity_id=activity.activity_id,
        action_id=1,
        action_order=1)
    assert activity_action.action_status == "M"
# def check_continue(response, activity_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_check_continue -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_continue(app,db_register):
    response = {}
    result = check_continue(response,"1")
    assert result == response
    
    current_app.config.update(
        WEKO_WORKFLOW_CONTINUE_APPROVAL=True
    )
    test = {
        "check_handle":1,
        "check_continue":1
    }
    result = check_continue(response,db_register["activities"][4].activity_id)
    assert result == test
    test = {
        "check_handle":1,
        "check_continue":0
    }
    result = check_continue(response,db_register["activities"][5].activity_id)
    assert result == test
# def auto_fill_title(item_type_name):
#     def _get_title(title_key):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_autofill_title -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_autofill_title(app):
    item_type_name = "テストアイテムタイプ"
    result = auto_fill_title(item_type_name)
    assert result == ""
    
    current_app.config.update(
        WEKO_ITEMS_UI_AUTO_FILL_TITLE_SETTING={
            "usage_application_title_key":["テストアイテムタイプ"],
        },
        WEKO_ITEMS_UI_AUTO_FILL_TITLE={"usage_application_title_key":"usage_application_title"},
        WEKO_ITEMS_UI_USAGE_APPLICATION_TITLE_KEY="usage_application_title_key",
        WEKO_ITEMS_UI_USAGE_REPORT_TITLE_KEY="",
        WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE_KEY=""
    )
    result = auto_fill_title(item_type_name)
    assert result == "usage_application_title"
    current_app.config.update(
        WEKO_ITEMS_UI_AUTO_FILL_TITLE_SETTING={
            "usage_report_title_key":["テストアイテムタイプ"],
        },
        WEKO_ITEMS_UI_AUTO_FILL_TITLE={"usage_report_title_key":"usage_report_title"},
        WEKO_ITEMS_UI_USAGE_APPLICATION_TITLE_KEY="",
        WEKO_ITEMS_UI_USAGE_REPORT_TITLE_KEY="usage_report_title_key",
        WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE_KEY=""
    )
    result = auto_fill_title(item_type_name)
    assert result == "usage_report_title"
    current_app.config.update(
        WEKO_ITEMS_UI_AUTO_FILL_TITLE_SETTING={
            "output_registration_title_key":["テストアイテムタイプ"],
        },
        WEKO_ITEMS_UI_AUTO_FILL_TITLE={"output_registration_title_key":"output_registration_title"},
        WEKO_ITEMS_UI_USAGE_APPLICATION_TITLE_KEY="",
        WEKO_ITEMS_UI_USAGE_REPORT_TITLE_KEY="",
        WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE_KEY="output_registration_title_key"
    )
    result = auto_fill_title(item_type_name)
    assert result == "output_registration_title"
    current_app.config.update(
        WEKO_ITEMS_UI_AUTO_FILL_TITLE_SETTING="not dict",
        WEKO_ITEMS_UI_AUTO_FILL_TITLE={"output_registration_title_key":"output_registration_title"},
        WEKO_ITEMS_UI_USAGE_APPLICATION_TITLE_KEY="",
        WEKO_ITEMS_UI_USAGE_REPORT_TITLE_KEY="",
        WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE_KEY="output_registration_title_key"
    )
    result = auto_fill_title(item_type_name)
    assert result == ""
    current_app.config.update(
        WEKO_ITEMS_UI_AUTO_FILL_TITLE_SETTING={
            "output_registration_title_key":["テストアイテムタイプ"],
        },
        WEKO_ITEMS_UI_AUTO_FILL_TITLE={},
        WEKO_ITEMS_UI_USAGE_APPLICATION_TITLE_KEY="",
        WEKO_ITEMS_UI_USAGE_REPORT_TITLE_KEY="",
        WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE_KEY="output_registration_title_key"
    )
    result = auto_fill_title(item_type_name)
    assert result == ""
# def exclude_admin_workflow(workflow_list):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_exclude_admin_workflow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_exclude_admin_workflow(app, users, workflow):
    with app.test_request_context():
        login_user(users[8]["obj"])

        wf = workflow["workflow"]
        result = exclude_admin_workflow([wf])
        assert result == [wf]
        current_app.config.update(
            WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY=True
        )
        result = exclude_admin_workflow([wf])
        assert result == []
        
        current_app.config.update(
            WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION="not exist action"
        )
        result = exclude_admin_workflow([wf])
        assert result == [wf]
# def is_enable_item_name_link(action_endpoint, item_type_name):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_is_enable_item_name_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_is_enable_item_name_link(app):
    current_app.config.update(
        WEKO_ITEMS_UI_USAGE_REPORT="not enable item type"
    )
    result = is_enable_item_name_link("item_login_application","enable item type")
    assert result == True
    result = is_enable_item_name_link("item_login_application","not enable item type")
    assert result == False
    
# def save_activity_data(data: dict) -> NoReturn:
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_save_activity_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_save_activity_data(mocker):
    mock_update = mocker.patch("weko_workflow.utils.WorkActivity.update_activity")
    save_activity_data({})
    mock_update.assert_not_called()

    data = {
        "activity_id":"test_id",
        "title":"test title",
        "shared_user_id":1,
        "approval1":"test1@test.org",
        "approval2":"test2@test.org"
    }
    mock_update = mocker.patch("weko_workflow.utils.WorkActivity.update_activity")
    save_activity_data(data)
    mock_update.assert_called_with("test_id",{"title":"test title","shared_user_id":1,"approval1":"test1@test.org","approval2":"test2@test.org"})

# def send_mail_url_guest_user(mail_info: dict) -> bool:
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_send_mail_url_guest_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_send_mail_url_guest_user(mocker):
    mocker.patch("weko_workflow.utils.replace_characters",return_value=None)
    with patch("weko_workflow.utils.get_mail_data",return_value=(None,None)):
        result = send_mail_url_guest_user({})
        assert result == False
    with patch("weko_workflow.utils.get_mail_data",return_value=("subject","body")):
        with patch("weko_workflow.utils.send_mail",return_value=True):
            result = send_mail_url_guest_user({})
            assert result == True
        with patch("weko_workflow.utils.send_mail",return_value=False):
            result = send_mail_url_guest_user({})
            assert result == False
# def generate_guest_activity_token_value(
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_generate_guest_activity_token_value -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_generate_guest_activity_token_value(client,mocker):
    activity_id = "A-20221003-00001"
    filename = "test_file.txt"
    activity_date = datetime.datetime(2022,10,1)
    mail = "guest@test.org"
    mocker.patch("weko_workflow.utils.oracle10.hash",return_value="CE06FDFB15823A5C")
    token_value="A-20221003-00001 2022-10-01 guest@test.org CE06FDFB15823A5C"
    token_value = base64.b64encode(token_value.encode()).decode()
    result = generate_guest_activity_token_value(activity_id,filename,activity_date,mail)
    assert result == token_value
# def init_activity_for_guest_user(
#     def _get_guest_activity():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_init_activity_for_guest_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_init_activity_for_guest_user(app,db_register,mocker):
    with app.test_request_context():
        record_id = uuid.uuid4()
        data = {
            "workflow_id":db_register["workflow"].id,
            "flow_id":db_register["flow_define"].id,
            "extra_info":{
                "guest_mail":"guest@test.org",
                "file_name":"test.txt",
                "record_id":str(record_id)
            }
        }
        new_activit_id="A-20221003-00001"
        mocker.patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value=new_activit_id)
        mocker.patch("weko_workflow.utils.generate_guest_activity_token_value",return_value="QS0yMDIyMTAwMy0wMDAwMSAyMDIyLTEwLTAxIGd1ZXN0QHRlc3Qub3JnIENFMDZGREZCMTU4MjNBNUM=")
        activity, tmp_url = init_activity_for_guest_user(data,False)
        assert activity.activity_id == new_activit_id
        assert tmp_url == "http://TEST_SERVER.localdomain/workflow/activity/guest-user/test.txt?token=QS0yMDIyMTAwMy0wMDAwMSAyMDIyLTEwLTAxIGd1ZXN0QHRlc3Qub3JnIENFMDZGREZCMTU4MjNBNUM="
# def send_usage_application_mail_for_guest_user(guest_mail: str, temp_url: str):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_send_usage_application_mail_for_guest_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_send_usage_application_mail_for_guest_user(app,db,mocker):
    mail_config = MailConfig(mail_default_sender="test_sender")
    db.session.add(mail_config)
    db.session.commit()
    mail = "guest@test.org"
    url = "https://test.com"
    mock_sender = mocker.patch("weko_workflow.utils.send_mail_url_guest_user")
    send_usage_application_mail_for_guest_user(mail,url)

    mock_sender.assert_called_with(
        {
            "template":"",
            "mail_address":mail,
            "url_guest_user":url,
            "restricted_site_name_ja": "",
            "restricted_site_name_en": "",
            "restricted_site_mail": "test_sender",
            "restricted_site_url": "https://localhost",
        }
    )
# def validate_guest_activity_token(
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_validate_guest_activity_token -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_validate_guest_activity_token(app):
    filename = "test_file.txt"
    token_value="A-20221003-00001 2022-10-01 guest@test.org CE06FDFB15823A5C"
    token_value = base64.b64encode(token_value.encode()).decode()
    flg,activity_id,mail = validate_guest_activity_token(token_value,filename)
    assert flg == True
    assert activity_id == "A-20221003-00001"
    assert mail == "guest@test.org"
    with patch("weko_workflow.utils.oracle10.verify",side_effect=Exception):
        flg, activity_id, mail = validate_guest_activity_token(token_value,filename)
        assert flg == False
        assert activity_id == None
        assert mail == None
# def validate_guest_activity_expired(activity_id: str) -> str:
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_validate_guest_activity_expired -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_validate_guest_activity_expired(app,workflow,mocker):
    filename = "test_file.txt"
    token_value="A-20221003-00001 2022-10-01 guest@test.org CE06FDFB15823A5C"
    token_value = base64.b64encode(token_value.encode()).decode()
    activity_id = "A-20221003-00000"
    # not exist guest_activity
    result = validate_guest_activity_expired(activity_id)
    assert result == ""
    
    guest_activity = GuestActivity.create(
        user_mail="guest@test.org",
        record_id=str(uuid.uuid4()),
        file_name=filename,
        activity_id=activity_id,
        token=token_value,
        expiration_date=3
    )
    # is_usage_report is False
    result = validate_guest_activity_expired(activity_id)
    assert result == ""
    
    # is_usage_report is True
    activity_id = "A-20221003-00002"
    guest_activity = GuestActivity.create(
        user_mail="guest@test.org",
        record_id=str(uuid.uuid4()),
        file_name=filename,
        activity_id=activity_id,
        token=token_value,
        expiration_date=3,
        is_usage_report=True
    )
    # current_date > expiration_acccess_date
    datetime_mock = mocker.patch("weko_workflow.utils.datetime")
    datetime_mock.utcnow.return_value=datetime.datetime.utcnow()+datetime.timedelta(days=30)
    result = validate_guest_activity_expired(activity_id)
    assert result == _("The specified link has expired.")
    
    # current_date < expiration_acccess_date
    datetime_mock = mocker.patch("weko_workflow.utils.datetime")
    datetime_mock.utcnow.return_value=datetime.datetime.utcnow()
    result = validate_guest_activity_expired(activity_id)
    assert result == ""
    with patch("weko_workflow.utils.timedelta",side_effect=OverflowError):
        result = validate_guest_activity_expired(activity_id)
        assert result == ""
# def create_onetime_download_url_to_guest(activity_id: str,
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_create_onetime_download_url_to_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_create_onetime_download_url_to_guest(app, workflow,mocker):
    with app.test_request_context():
        today = datetime.datetime(2022,10,6,1,2,3,4)
        datetime_mock = mocker.patch("weko_workflow.utils.datetime")
        datetime_mock.today.return_value=today
        datetime_mock.utcnow.return_value=today
        file_name="test_file.txt"
        record_id = str(uuid.uuid4())
        user_mail = "user@test.org"
        extra_info = {
            "file_name":file_name,
            "record_id":record_id,
            "user_mail":user_mail
        }
        token_value="A-20221003-00001 2022-10-01 guest@test.org CE06FDFB15823A5C"
        token_value = base64.b64encode(token_value.encode()).decode()
        activity_id = "A-20221003-00001"
        guest_activity = GuestActivity.create(
            user_mail="guest@test.org",
            record_id=record_id,
            file_name=file_name,
            activity_id=activity_id,
            token=token_value,
            expiration_date=30
        )
        datetime_mock_ui = mocker.patch("weko_records_ui.utils.dt")
        datetime_mock_ui.utcnow.return_value=today
        expiration_date = today + datetime.timedelta(days=30)
        mocker.patch("weko_records_ui.utils.oracle10.hash",return_value="CE06FDFB15823A5C")
        url_token = "{} {} {} {}".format(record_id,user_mail,"2022-10-06","CE06FDFB15823A5C")
        url_token_value = base64.b64encode(url_token.encode()).decode()
        url = 'http://TEST_SERVER.localdomain/record/{}/file/onetime/test_file.txt?token={}'.format(record_id,url_token_value)
        test = {
            "file_url":url,
            "expiration_date":expiration_date.strftime("%Y-%m-%d"),
            "expiration_date_ja":"",
            "expiration_date_en":""
        }
        result = create_onetime_download_url_to_guest(activity_id, extra_info)
        assert result == test
        
        # not exist user_mail
        extra_info = {
            "file_name":file_name,
            "record_id":record_id,
            "guest_mail":user_mail
        }
        result = create_onetime_download_url_to_guest(activity_id, extra_info)
        assert result == test
        
        # raise OverflowError
        with patch("weko_workflow.utils.timedelta",side_effect=OverflowError):
            test = {
                "file_url":url,
                "expiration_date":"",
                "expiration_date_ja":"無制限",
                "expiration_date_en":"Unlimited"
            }
            result = create_onetime_download_url_to_guest(activity_id, extra_info)
            assert result == test
# def delete_guest_activity(activity_id: str) -> bool:
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_delete_guest_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_delete_guest_activity(client,workflow):
    token_value="A-20221003-00001 2022-10-01 guest@test.org CE06FDFB15823A5C"
    token_value = base64.b64encode(token_value.encode()).decode()
    activity_id = "A-20221003-00001"
    guest_activity = GuestActivity.create(
        user_mail="guest@test.org",
        record_id=str(uuid.uuid4()),
        file_name="test.txt",
        activity_id=activity_id,
        token=token_value,
        expiration_date=30
    )
    
    result = delete_guest_activity(activity_id)
    assert result == True
    
    result = delete_guest_activity("not exist activity")
    assert result == False
# def get_activity_display_info(activity_id: str):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_activity_display_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_activity_display_info(app,db, users, db_register,mocker):
    with app.test_request_context():
        activity = db_register["activities"][1]
        activity_id = activity.activity_id
        db_history1 = ActivityHistory(
            activity_id=activity_id,
            action_id=3,
            action_user=users[0]["id"],
            action_status="F",
            action_date=datetime.datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
            action_order=1
        )
        with db.session.begin_nested():
            db.session.add(db_history1)
        test_steps = [
            {"ActivityId":activity_id,"ActionId":1,"ActionName":"Start","ActionVersion":"1.0.0","ActionEndpoint":"begin_action","Author":"contributor@test.org","Status":"action_doing","ActionOrder":1},
            {"ActivityId":activity_id,"ActionId":3,"ActionName":"Item Registration","ActionVersion":"1.0.0","ActionEndpoint":"item_login","Author":"","Status":" ","ActionOrder":2},
            {"ActivityId":activity_id,"ActionId":5,"ActionName":"Item Link","ActionVersion":"1.0.0","ActionEndpoint":"item_link","Author":"","Status":" ","ActionOrder":3}
        ]
        endpoint, action_id, activity_detail, cur_action, histories, item, steps, temporary_comment, workflow_detail = get_activity_display_info(activity_id)
        assert endpoint == "begin_action"
        assert action_id == 1
        assert activity_detail == activity
        assert cur_action == activity.action
        assert histories == [db_history1]
        assert item == ItemsMetadata.get_record(id_=activity.item_id)
        assert steps == test_steps
        assert temporary_comment == None
        assert workflow_detail == db_register["workflow"]
        
        mocker.patch("weko_workflow.utils.ItemsMetadata.get_record",side_effect=NoResultFound)
        activity.activity_status="C"
        db.session.merge(activity)
        db.session.commit()
        mocker.patch("weko_workflow.utils.WorkActivity.get_activity_action_comment",return_value=None)
        endpoint, action_id, activity_detail, cur_action, histories, item, steps, temporary_comment, workflow_detail = get_activity_display_info(activity_id)
        assert endpoint == "begin_action"
        assert action_id == 1
        assert activity_detail == activity
        assert cur_action == activity.action
        assert histories == [db_history1]
        assert item == None
        assert steps == test_steps
        assert temporary_comment == ""
        assert workflow_detail == db_register["workflow"]
        
# def __init_activity_detail_data_for_guest(activity_id: str, community_id: str):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test___init_activity_detail_data_for_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test___init_activity_detail_data_for_guest(app,db,users,db_register,mocker):
    with app.test_request_context():
        
        activity = db_register["activities"][1]
        activity_id = activity.activity_id
        db_history1 = ActivityHistory(
                activity_id=activity_id,
                action_id=3,
                action_user=users[0]["id"],
                action_status="F",
                action_date=datetime.datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                action_order=1
            )
        with db.session.begin_nested():
            db.session.add(db_history1)

        test_steps = [
            {"ActivityId":activity_id,"ActionId":1,"ActionName":"Start","ActionVersion":"1.0.0","ActionEndpoint":"begin_action","Author":"contributor@test.org","Status":"action_doing","ActionOrder":1},
            {"ActivityId":activity_id,"ActionId":3,"ActionName":"Item Registration","ActionVersion":"1.0.0","ActionEndpoint":"item_login","Author":"","Status":" ","ActionOrder":2},
            {"ActivityId":activity_id,"ActionId":5,"ActionName":"Item Link","ActionVersion":"1.0.0","ActionEndpoint":"item_link","Author":"","Status":" ","ActionOrder":3}
        ]
        action_endpoint = "begin_action"
        action_id=1
        activity_detail=activity
        cur_action=activity.action
        histories=[db_history1]
        item=ItemsMetadata.get_record(id_=activity.item_id)
        steps=test_steps,
        temporary_comment=None
        workflow_detail=db_register["workflow"]
        display_info = (action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail)
        mocker.patch("weko_workflow.utils.get_activity_display_info",return_value=display_info)
        mocker.patch("weko_workflow.utils.get_approval_keys",return_value=[])
        community_id=""
        session['user_id'] = 'dummy user'
        session["guest_email"] = "guest@test.org"
        user_profile = {
            "results":{
                'subitem_user_name': "guest",
                'subitem_fullname': "guest",
                'subitem_mail_address': "guest@test.org",
                'subitem_displayname': "guest",
                'subitem_university/institution': '',
                'subitem_affiliated_division/department': '',
                'subitem_position': '',
                'subitem_phone_number': '',
                'subitem_position(other)': '',
                'subitem_affiliated_institution': [],
            }
        }
        test = dict(
            page=None,
            render_widgets=False,
            community_id=community_id,
            temporary_journal='',
            temporary_idf_grant='',
            temporary_idf_grant_suffix='',
            idf_grant_data='',
            idf_grant_input=IDENTIFIER_GRANT_LIST,
            idf_grant_method=0,
            error_type='item_login_error',
            cur_step=action_endpoint,
            approval_record=[],
            recid=None,
            links=None,
            term_and_condition_content='',
            is_auto_set_index_action=True,
            application_item_type=False,
            auto_fill_title="",
            auto_fill_data_type=None,
            is_show_autofill_metadata=True,
            is_hidden_pubdate=False,
            position_list=WEKO_USERPROFILES_POSITION_LIST,
            institute_position_list=WEKO_USERPROFILES_INSTITUTE_POSITION_LIST,
            item_type_name="テストアイテムタイプ",
            res_check=1,
            action_id=action_id,
            activity=activity_detail,
            histories=histories,
            item=item,
            steps=steps,
            temporary_comment=temporary_comment,
            workflow_detail=workflow_detail,
            user_profile=user_profile,
            list_license=[{'value': 'license_free', 'name': 'write your own license'}, {'value': 'license_12', 'name': 'Creative Commons CC0 1.0 Universal Public Domain Designation'}, {'value': 'license_6', 'name': 'Creative Commons Attribution 3.0 Unported (CC BY 3.0)'}, {'value': 'license_7', 'name': 'Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)'}, {'value': 'license_8', 'name': 'Creative Commons Attribution-NoDerivs 3.0 Unported (CC BY-ND 3.0)'}, {'value': 'license_9', 'name': 'Creative Commons Attribution-NonCommercial 3.0 Unported (CC BY-NC 3.0)'}, {'value': 'license_10', 'name': 'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0)'}, {'value': 'license_11', 'name': 'Creative Commons Attribution-NonCommercial-NoDerivs 3.0 Unported (CC BY-NC-ND 3.0)'}, {'value': 'license_0', 'name': 'Creative Commons Attribution 4.0 International (CC BY 4.0)'}, {'value': 'license_1', 'name': 'Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)'}, {'value': 'license_2', 'name': 'Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0)'}, {'value': 'license_3', 'name': 'Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)'}, {'value': 'license_4', 'name': 'Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)'}, {'value': 'license_5', 'name': 'Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)'}],
            cur_action=cur_action,
            activity_id=activity_detail.activity_id,
            is_enable_item_name_link=True,
            enable_feedback_maillist=current_app.config[
                'WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL'],
            enable_contributor=current_app.config[
                'WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'],
            out_put_report_title="",
            action_endpoint_key={},
            approval_email_key=[],
            step_item_login_url="weko_items_ui/iframe/item_edit.html",
            need_file=True,
            need_billing_file=False,
            records={'id': '1.1', 'pid': {'type': 'depid', 'value': '1.1', 'revision_id': 0}, 'lang': 'ja', 'owner': '1', 'title': 'title', 'owners': [1], 'status': 'published', '$schema': '/items/jsonschema/15', 'pubdate': '2022-08-20', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}, 'shared_user_id': -1, 'item_1617186331708': [{'subitem_1551255647225': 'ff', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}},
            record=[],
            jsonschema="/items/jsonschema/1",
            schemaform="/items/schemaform/1",
            item_save_uri="/items/iframe/model/save",
            files=[],
            endpoints={},
            need_thumbnail=False,
            files_thumbnail=[],
            allow_multi_thumbnail=False,
            id=db_register["workflow"].itemtype_id,
        )

        result = __init_activity_detail_data_for_guest(activity_id,community_id)
        assert result == test

# def prepare_data_for_guest_activity(activity_id: str) -> dict:
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_data_for_guest_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_prepare_data_for_guest_activity(app,db,users,db_register,mocker):
    with app.test_request_context():
        mocker.patch("weko_workflow.utils.__init_activity_detail_data_for_guest",return_value={})
        request_mock = mocker.patch.object(flask, "request")
        request_mock.method.return_value="GET"
        request_mock.form.return_value={"checked":True}
        activity = db_register["activities"][1]
        activity_id = activity.activity_id
        db_history1 = ActivityHistory(
                    activity_id=activity_id,
                    action_id=3,
                    action_user=users[0]["id"],
                    action_status="F",
                    action_date=datetime.datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    action_order=1
                )
        with db.session.begin_nested():
            db.session.add(db_history1)

        init_data = dict(
                page=None,
                render_widgets=False,
                community_id="",
                temporary_journal='',
                temporary_idf_grant='',
                temporary_idf_grant_suffix='',
                idf_grant_data='',
                idf_grant_input=IDENTIFIER_GRANT_LIST,
                idf_grant_method=0,
                error_type='item_login_error',
                cur_step="begin_action",
                approval_record=[],
                recid=None,
                links=None,
                term_and_condition_content='',
                is_auto_set_index_action=True,
                application_item_type=False,
                auto_fill_title="",
                auto_fill_data_type=None,
                is_show_autofill_metadata=True,
                is_hidden_pubdate=False,
                position_list=WEKO_USERPROFILES_POSITION_LIST,
                institute_position_list=WEKO_USERPROFILES_INSTITUTE_POSITION_LIST,
                item_type_name="テストアイテムタイプ",
                res_check=1,
                action_id=1,
                activity=activity,
                histories=[db_history1],
                item=ItemsMetadata.get_record(id_=activity.item_id),
                steps=[{"ActivityId":activity_id,"ActionId":1,"ActionName":"Start","ActionVersion":"1.0.0","ActionEndpoint":"begin_action","Author":"contributor@test.org","Status":"action_doing","ActionOrder":1},{"ActivityId":activity_id,"ActionId":3,"ActionName":"Item Registration","ActionVersion":"1.0.0","ActionEndpoint":"item_login","Author":"","Status":" ","ActionOrder":2},{"ActivityId":activity_id,"ActionId":5,"ActionName":"Item Link","ActionVersion":"1.0.0","ActionEndpoint":"item_link","Author":"","Status":" ","ActionOrder":3}],
                temporary_comment=None,
                workflow_detail=db_register["workflow"],
                user_profile={"results":{'subitem_user_name': "guest",'subitem_fullname': "guest",'subitem_mail_address': "guest@test.org",'subitem_displayname': "guest",'subitem_university/institution': '','subitem_affiliated_division/department': '','subitem_position': '','subitem_phone_number': '','subitem_position(other)': '','subitem_affiliated_institution': [],}},
                list_license=[{'value': 'license_free', 'name': 'write your own license'}, {'value': 'license_12', 'name': 'Creative Commons CC0 1.0 Universal Public Domain Designation'}, {'value': 'license_6', 'name': 'Creative Commons Attribution 3.0 Unported (CC BY 3.0)'}, {'value': 'license_7', 'name': 'Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)'}, {'value': 'license_8', 'name': 'Creative Commons Attribution-NoDerivs 3.0 Unported (CC BY-ND 3.0)'}, {'value': 'license_9', 'name': 'Creative Commons Attribution-NonCommercial 3.0 Unported (CC BY-NC 3.0)'}, {'value': 'license_10', 'name': 'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0)'}, {'value': 'license_11', 'name': 'Creative Commons Attribution-NonCommercial-NoDerivs 3.0 Unported (CC BY-NC-ND 3.0)'}, {'value': 'license_0', 'name': 'Creative Commons Attribution 4.0 International (CC BY 4.0)'}, {'value': 'license_1', 'name': 'Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)'}, {'value': 'license_2', 'name': 'Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0)'}, {'value': 'license_3', 'name': 'Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)'}, {'value': 'license_4', 'name': 'Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)'}, {'value': 'license_5', 'name': 'Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)'}],
                cur_action=activity.action,
                activity_id=activity.activity_id,
                is_enable_item_name_link=True,
                enable_feedback_maillist=current_app.config[
                    'WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL'],
                enable_contributor=current_app.config[
                    'WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'],
                out_put_report_title="",
                action_endpoint_key={},
                approval_email_key=[],
                step_item_login_url="weko_items_ui/iframe/item_edit.html",
                need_file=True,
                need_billing_file=False,
                records={'id': '1.1', 'pid': {'type': 'depid', 'value': '1.1', 'revision_id': 0}, 'lang': 'ja', 'owner': '1', 'title': 'title', 'owners': [1], 'status': 'published', '$schema': '/items/jsonschema/15', 'pubdate': '2022-08-20', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}, 'shared_user_id': -1, 'item_1617186331708': [{'subitem_1551255647225': 'ff', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}},
                record=[],
                jsonschema="/items/jsonschema/1",
                schemaform="/items/schemaform/1",
                item_save_uri="/items/iframe/model/save",
                files=[],
                endpoints={},
                need_thumbnail=False,
                files_thumbnail=[],
                allow_multi_thumbnail=False,
                id=db_register["workflow"].itemtype_id,
            )
        mocker.patch("weko_workflow.utils.__init_activity_detail_data_for_guest",return_value=init_data)

        result = prepare_data_for_guest_activity(activity_id)
        init_data["community"]=None
        assert result == init_data
        
        init_data.pop("community")
        init_data["cur_step"] = "item_login"
        mocker.patch("weko_workflow.utils.__init_activity_detail_data_for_guest",return_value=init_data)
        result = prepare_data_for_guest_activity(activity_id)
        init_data["application_item_type"] = False
        init_data["community"]=None
        init_data["res_check"]=0
        assert result == init_data
        
# def recursive_get_specified_properties(properties):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_recursive_get_specified_properties -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_recursive_get_specified_properties():
    pr = {
        "items":[
            {
                "key":"test_key1"
            },
            {
                "approval":"value",
                "key":"test_key2"
            },
        ]
    }
    result = recursive_get_specified_properties(pr)
    assert result == "test_key2"
    pr = {
        "items":[
            {
                "key":"test_key1"
            },
            {
                "items":[
                    {
                        "approval":"value",
                        "key":"test_key2"
                    }
                ]
            }
        ]
    }
    result = recursive_get_specified_properties(pr)
    assert result == "test_key2"
    
    pr = {}
    result = recursive_get_specified_properties(pr)
    assert result == None
# def get_approval_keys():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_approval_keys -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_approval_keys(item_type):
    result = get_approval_keys()
    assert result == ['parentkey.subitem_restricted_access_guarantor_mail_address']
# def process_send_mail(mail_info, mail_pattern_name):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_process_send_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_process_send_mail(app,mocker):
    mocker.patch("weko_workflow.utils.replace_characters",return_value=None)
    mocker.patch("weko_workflow.utils.send_mail")
    mail_info = {}
    mail_pattern_name = ""
    result = process_send_mail(mail_info,mail_pattern_name)
    assert result == None
    
    mail_info = {"mail_recipient":"value"}
    mail_pattern_name = ""
    with patch("weko_workflow.utils.get_mail_data",return_value=(None,None)):
        result = process_send_mail(mail_info,mail_pattern_name)
        
    with patch("weko_workflow.utils.get_mail_data",return_value=("body","subject")):
        result = process_send_mail(mail_info,mail_pattern_name)

# def cancel_expired_usage_reports():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_cancel_expired_usage_reports -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_cancel_expired_usage_reports(db_register,mocker):
    token_value="A-20221003-00001 2022-10-01 guest@test.org CE06FDFB15823A5C"
    token_value = base64.b64encode(token_value.encode()).decode()
    activity_id = "A-20221003-00001"
    guest_activity = GuestActivity.create(
        user_mail="guest@test.org",
        record_id=str(uuid.uuid4()),
        file_name="test.txt",
        activity_id=activity_id,
        token=token_value,
        expiration_date=1,
        is_usage_report=True
    )
    today = datetime.datetime.today()+datetime.timedelta(days=2)
    datetime_mock = mocker.patch("weko_workflow.models.datetime")
    datetime_mock.utcnow.return_value=today
    mocker.patch("weko_workflow.utils.GuestActivity.get_expired_activities",return_value=[guest_activity])
    mocker.patch("weko_workflow.utils.WorkActivity.cancel_usage_report_activities")
    cancel_expired_usage_reports()

# def process_send_approval_mails(activity_detail, actions_mail_setting,
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_process_send_approval_mails -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_process_send_approval_mails(app,db_register,users,mocker):
    mocker.patch("weko_workflow.utils.get_item_info",return_value=None)
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_en":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    activity = db_register["activities"][1]
    next_step_appover_id = users[2]["id"]
    file_data={
                "file_url":"test_url",
                "expiration_date":"",
                "expiration_date_ja":"無制限",
                "expiration_date_en":"Unlimited"
            }
    # approval is True,previous.inform_approval is True
    actions_mail_setting={
        "previous":{"inform_reject":False,"inform_approval":True,"request_approval":False},
        "next": {},
        "approval": True,
        "reject": False}
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_en":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    test_mail_info = {
        "restricted_download_link":"test_url",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"無制限",
        "restricted_expiration_date_en":"Unlimited"
    }
    mock_sender = mocker.patch("weko_workflow.utils.process_send_mail")
    process_send_approval_mails(activity, actions_mail_setting,next_step_appover_id,file_data)
    mock_sender.assert_called_with(test_mail_info,"email_pattern_approval_done.tpl")
    
    # approval is True,next.request_approval is True
    actions_mail_setting={
        "previous":{},
        "next": {"inform_reject":False,"inform_approval":False,"request_approval":True},
        "approval": True,
        "reject": False}
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_en":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    test_mail_info = {
        "restricted_download_link":"test_url",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"無制限",
        "restricted_expiration_date_en":"Unlimited",
        "mail_recipient":users[2]["email"]
    }
    mock_sender = mocker.patch("weko_workflow.utils.process_send_mail")
    process_send_approval_mails(activity, actions_mail_setting,next_step_appover_id,file_data)
    mock_sender.assert_called_with(test_mail_info,"email_pattern_request_approval.tpl")
    
    # approval is True,previous.inform_approval is False,next.request_approval is False
    actions_mail_setting={
        "previous":{},
        "next": {"inform_reject":False,"inform_approval":False,"request_approval":False},
        "approval": True,
        "reject": False}
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_en":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    process_send_approval_mails(activity, actions_mail_setting,next_step_appover_id,file_data)

    # reject is True, previous.inform_reject is True
    actions_mail_setting={
        "previous":{"inform_reject":True,"inform_approval":False,"request_approval":True},
        "next": {},
        "approval": False,
        "reject": True}
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_en":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    test_mail_info = {
        "restricted_download_link":"test_url",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"無制限",
        "restricted_expiration_date_en":"Unlimited"
    }
    mock_sender = mocker.patch("weko_workflow.utils.process_send_mail")
    process_send_approval_mails(activity, actions_mail_setting,next_step_appover_id,file_data)
    mock_sender.assert_called_with(test_mail_info,"email_pattern_approval_rejected.tpl")

    # reject is True, previous.inform_reject is False
    actions_mail_setting={
        "previous":{"inform_reject":False,"inform_approval":False,"request_approval":False},
        "next": {},
        "approval": False,
        "reject": True}
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_en":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    process_send_approval_mails(activity, actions_mail_setting,next_step_appover_id,file_data)

    # approval is False,reject is False
    actions_mail_setting={
        "previous":{},
        "next": {},
        "approval": False,
        "reject": False}
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_en":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    process_send_approval_mails(activity, actions_mail_setting,next_step_appover_id,file_data)

# def get_usage_data(item_type_id, activity_detail, user_profile=None):
#     def __build_metadata_for_usage_report(record_data: Union[dict, list],
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_usage_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_usage_data(app,db,db_register):
    
    # not exist extra_info activity
    activity = db_register["activities"][1]
    result = get_usage_data(1,activity)
    assert result == {}
    
    activity = db_register["activities"][6]
    result = get_usage_data(1,activity)
    assert result == {}
    
    today = datetime.datetime.now()
    test = dict(
        usage_type='Application',
        dataset_usage="related_guest_activity",
        usage_data_name='',
        mail_address="guest@test.org",
        university_institution='',
        affiliated_division_department='',
        position='',
        position_other='',
        phone_number='',
        usage_report_id='',
        wf_issued_date=today.strftime("%Y-%m-%d"),
        item_title="{}{}{}_".format("利用申請",today.strftime("%Y%m%d"),"related_guest_activity")
    )
    result = get_usage_data(31001,activity)
    assert result == test
    
    test = dict(
        usage_type='Application',
        dataset_usage="related_guest_activity",
        usage_data_name='',
        mail_address="user@test.org",
        university_institution='',
        affiliated_division_department='',
        position='',
        position_other='',
        phone_number='',
        usage_report_id='',
        wf_issued_date=today.strftime("%Y-%m-%d"),
        item_title="{}{}{}_".format("利用申請",today.strftime("%Y%m%d"),"related_guest_activity")
    )
    user_profile = {"results":{'subitem_user_name': "guest",'subitem_fullname': "guest",'subitem_mail_address': "user@test.org",'subitem_displayname': "guest",'subitem_university/institution': '','subitem_affiliated_division/department': '','subitem_position': '','subitem_phone_number': '','subitem_position(other)': '','subitem_affiliated_institution': [],}}
    result = get_usage_data(31001,activity,user_profile)
    assert result == test

    test = dict(
        usage_type='Report',
        dataset_usage='title',
        usage_data_name='',
        mail_address='',
        university_institution='',
        affiliated_division_department='',
        position='',
        position_other='',
        phone_number='',
        usage_report_id=activity.activity_id,
        wf_issued_date=today.strftime("%Y-%m-%d"),
        item_title='{}{}{}'.format(activity.extra_info["usage_activity_id"],"利用報告","")
    )
    result = get_usage_data(31003,activity)
    assert result == test
    
# def update_approval_date(activity):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_update_approval_date(app,db_register,mocker):
    mocker.patch("weko_workflow.utils.update_approval_date_for_deposit")
    mocker.patch("weko_workflow.utils.update_system_data_for_item_metadata")
    mocker.patch("weko_workflow.utils.update_system_data_for_activity")
    
    activity = db_register["activities"][1]
    
    # item_type_id not in list
    result = update_approval_date(activity)
    assert result == None
    
    current_app.config.update(
        WEKO_WORKFLOW_USAGE_APPLICATION_ITEM_TYPES_LIST=[1]
    )
    # not exist sub_approval_date_key
    update_approval_date(activity)
    
    
    with patch("weko_workflow.utils.get_sub_key_by_system_property_key",return_value=("approval_date_key","approval_date_value")):
        update_approval_date(activity)
# def create_record_metadata_for_user(usage_application_activity, usage_report):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_create_record_metadata_for_user(app,db_register,mocker):
    mock_update_deposit = mocker.patch("weko_workflow.utils.update_system_data_for_item_metadata")
    mock_update_metadata = mocker.patch("weko_workflow.utils.update_approval_date_for_deposit")
    mock_update_system = mocker.patch("weko_workflow.utils.update_system_data_for_activity")
    
    activitiy = db_register["activities"][0]
# def get_current_date():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_current_date(mocker):
    today = datetime.datetime(2022,10,6,0,0,0,0)
    datetime_mock = mocker.patch("weko_workflow.utils.datetime")
    datetime_mock.today.return_value=today
    
    result = get_current_date()
    assert result == today.strftime("%Y-%m-%d")

# def get_sub_key_by_system_property_key(system_property_key, item_type_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_sub_key_by_system_property_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_sub_key_by_system_property_key(item_type):
    # not item_type_id
    sub_key,attribute_name = get_sub_key_by_system_property_key(None,None)
    assert sub_key == None
    assert attribute_name == None
    
    # not exist item_type
    sub_key,attribute_name = get_sub_key_by_system_property_key(None,1000)
    assert sub_key == ""
    assert attribute_name == ""
    
    # nomal
    sub_key,attribute_name = get_sub_key_by_system_property_key("subitem_1522299639480",1)
    assert sub_key == "item_1617186476635"
    assert attribute_name == "Access Rights"
# def update_system_data_for_item_metadata(item_id, sub_system_data_key,
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_update_system_data_for_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_update_system_data_for_item_metadata(db_records):
    item_id = db_records[0][3].id
    data_key = "item_new"
    data = {"key1":"value1"}
    update_system_data_for_item_metadata(item_id,data_key,data)
    item_meta = ItemsMetadata.get_record(id_=item_id)
    assert item_meta.get(data_key) is not None
    assert item_meta[data_key] == data
# def update_approval_date_for_deposit(deposit, sub_approval_date_key,
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_update_approval_date_for_deposit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_update_approval_date_for_deposit(db_records):
    deposit = db_records[0][6]
    date_key = "sub_approval_date_key"
    approval_date = {"title":"approval","value":"2022-10-06"}
    attribute_name = "approval_date"
    update_approval_date_for_deposit(deposit,date_key,approval_date,attribute_name)
    assert deposit[date_key] is not None
    assert deposit[date_key] == {"attribute_name":attribute_name,"attribute_value_mlt":[approval_date]}
# def update_system_data_for_activity(activity, sub_system_data_key,
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_update_system_data_for_activity(db_register):
    update_system_data_for_activity(None,None,None)
    
    key = "temp_key"
    value = {"data_key":"data_value"}
    activity = db_register["activities"][1]
    update_system_data_for_activity(activity,key,value)
    assert activity.temp_data == {"metainfo":{key:value}}
    
    activity = db_register["activities"][2]
    update_system_data_for_activity(activity,key,value)
    assert activity.temp_data == {"description":"this is temp_data","metainfo":{key:value}}
# def check_authority_by_admin(activity):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# def get_record_first_version(deposit):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_record_first_version -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_record_first_version(db_register,db_records):
    activity = db_register["activities"][1]
    record = WekoRecord.get_record(activity.item_id)
    deposit = WekoDeposit(record, record.model)
    

    result_deposit, pid = get_record_first_version(deposit)
    assert result_deposit == db_records[0][6]
    assert pid == db_records[0][0].object_uuid
# def get_files_and_thumbnail(activity_id, item):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# def get_pid_and_record(item_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# def get_items_metadata_by_activity_detail(activity_detail):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# def get_main_record_detail(activity_id,
#     def check_record(record):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# def prepare_doi_link_workflow(item_id, doi_input):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# def get_pid_value_by_activity_detail(activity_detail):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# def check_doi_validation_not_pass(item_id, activity_id,
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp


def test_get_index_id():
    """Get index ID base on activity id"""
    # from weko_workflow.api import WorkActivity, WorkFlow

    # activity = WorkActivity()
    # activity_detail = activity.get_activity_detail(activity_id)

    # workflow = WorkFlow()
    # workflow_detail = workflow.get_workflow_by_id(
    #     activity_detail.workflow_id)

    # index_tree_id = workflow_detail.index_tree_id

    # if index_tree_id:
    #     from .api import Indexes
    #     index_result = Indexes.get_index(index_tree_id)
    #     if not index_result:
    #         index_tree_id = None
    # else:
    #     index_tree_id = None
    raise BaseException

def test_make_activitylog_tsv(db_register,db_records):
    """test make_activitylog_tsv"""
    activity = Activity()
    activities = []
    activities.append(activity.query.filter_by(activity_id='2'))
    activities.append(activity.query.filter_by(activity_id='3'))
    

    output_tsv = make_activitylog_tsv(activities)
    assert isinstance(output_tsv,str)
    assert len(output_tsv.splitlines()) == 3