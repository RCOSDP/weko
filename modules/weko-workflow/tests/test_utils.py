import copy
import pytest
import uuid
import json
from os.path import dirname, join
from unittest.mock import patch, MagicMock

import datetime
import base64
import flask
import pytz
from werkzeug.datastructures import MultiDict
from flask import current_app,session
from flask_babelex import gettext as _
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from redis.exceptions import ResponseError
from weko_deposit.pidstore import get_record_without_version
from weko_deposit.api import WekoRecord, WekoDeposit
from invenio_accounts.models import User
from invenio_records_files.models import RecordsBuckets
from invenio_files_rest.models import Bucket
from invenio_cache import current_cache
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, RecordIdentifier, PIDDoesNotExistError
from flask_login.utils import login_user
from .helpers import json_data, create_activity
from invenio_mail.models import MailConfig, MailTemplateUsers
from weko_admin.models import SiteInfo, Identifier
from weko_records.models import FeedbackMailList, ItemApplication, ItemType, RequestMailList
from weko_records_ui.models import FilePermission,FileOnetimeDownload
from weko_records_ui.utils import get_list_licence
from weko_user_profiles import UserProfile
from weko_records.api import ItemTypes, ItemsMetadata, Mapping
from weko_user_profiles.config import WEKO_USERPROFILES_POSITION_LIST,WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
from weko_workflow.models import Activity, ActivityHistory, GuestActivity
from weko_workflow.config import WEKO_WORKFLOW_FILTER_PARAMS,IDENTIFIER_GRANT_LIST
from weko_workflow.errors import InvalidParameterValueError
from weko_workflow.utils import (
    filter_all_condition,
    filter_condition,
    get_application_and_approved_date,
    get_contributors,
    get_disptype_and_ver_in_metainfo,
    get_record_by_root_ver,
    get_url_root,
    handle_finish_workflow,
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
    prepare_delete_workflow,
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
    send_mail_registration_done,
    send_mail_approval_done,
    send_mail_registration_done,
    send_mail_request_approval,
    send_mail,
    #email_pattern_registration_done,
    email_pattern_request_approval,
    email_pattern_approval_done,
    get_mail_data,
    get_mail_data_tpl,
    get_subject_and_content,
    get_file_path,
    replace_characters,
    get_register_info,
    get_approval_dates,
    get_item_info,
    get_site_info_name,
    get_default_mail_sender,
    set_mail_info,
    extract_term_description,
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
    __init_activity_detail_data_for_guest,
    recursive_get_specified_properties,
    get_approval_keys,
    process_send_mail,
    process_send_mail_tpl,
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
    prepare_doi_link_workflow,
    make_activitylog_tsv,
    check_authority_by_admin,
    validate_action_role_user,
    is_terms_of_use_only,
    grant_access_rights_to_all_open_restricted_files,
    delete_lock_activity_cache,
    delete_user_lock_activity_cache,
    check_an_item_is_locked,
    bulk_check_an_item_is_locked,
    create_conditions_dict,
    check_role,
    check_etag,
    check_pretty,
    convert_to_timezone,
    load_template,
    fill_template,
    get_non_extract_files_by_recid,
    check_activity_settings
)
from weko_workflow.api import GetCommunity, UpdateItem, WorkActivity, WorkActivityHistory, WorkFlow
from weko_workflow.models import Activity,ActionIdentifier
from datetime import timedelta

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
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_saving_doi_pidstore -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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
    # jalc doi, tmp save
    mock_update = mocker.patch("weko_workflow.utils.IdentifierHandle.update_idt_registration_metadata")
    result = saving_doi_pidstore(item_id,pid_without_ver,data,1,True)
    assert result == True
    mock_update.assert_has_calls([mocker.call("1000/0000000001","JaLC")])

    # jalc crossref doi
    mock_update = mocker.patch("weko_workflow.utils.IdentifierHandle.update_idt_registration_metadata")
    result = saving_doi_pidstore(item_id,pid_without_ver,data,2,False)
    assert result == True
    mock_update.assert_has_calls([mocker.call("2000/0000000001","Crossref")])

    # jalc datacite doi
    with patch("weko_workflow.utils.IdentifierHandle.register_pidstore",return_value=True):
        mock_update = mocker.patch("weko_workflow.utils.IdentifierHandle.update_idt_registration_metadata")
        result = saving_doi_pidstore(item_id,pid_without_ver,data,3,False)
        assert result == True
        mock_update.assert_has_calls([mocker.call("3000/0000000001","DataCite"),mocker.call("3000/0000000001","DataCite")])

    with patch("weko_workflow.utils.IdentifierHandle.register_pidstore",return_value=False):
        mock_update = mocker.patch("weko_workflow.utils.IdentifierHandle.update_idt_registration_metadata")
        result = saving_doi_pidstore(item_id,pid_without_ver,data,4,False)
        mock_update.assert_has_calls([mocker.call("4000/0000000001","JaLC")])
        assert result == True

    # ndl jalc doi, raise exception
    with patch("weko_workflow.utils.IdentifierHandle.register_pidstore",side_effect=Exception):
        mock_update = mocker.patch("weko_workflow.utils.IdentifierHandle.update_idt_registration_metadata")
        result = saving_doi_pidstore(item_id,pid_without_ver,data,4,False)
        assert result == False

    # other doi
    mock_update = mocker.patch("weko_workflow.utils.IdentifierHandle.update_idt_registration_metadata")
    result = saving_doi_pidstore(uuid.uuid4(),pid_without_ver,data,"wrong",False)
    assert result == False

# def register_hdl(activity_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_register_hdl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_register_hdl(app,db_records,db_register_full_action):#c
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

# def register_hdl_by_handle(hdl, item_uuid, item_uri):

# def item_metadata_validation(item_id, identifier_type, record=None,
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_item_metadata_validation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_item_metadata_validation(db_records,item_type):
    recid, depid, record, item, parent, doi, deposit = db_records[0]
    #result = item_metadata_validation(recid.id,"hdl")
    result = item_metadata_validation(None,"hdl",record=record)
    assert result == None
    recid, depid, record, item, parent, doi, deposit = db_records[2]

    without_ver = get_record_without_version(recid)

    # identifiery_type is JaLC, new resource_type in journalarticle_type, old resource_type in elearning_type
    with patch("weko_workflow.utils.MappingData.get_first_data_by_mapping",\
        side_effect=[("item_1617258105262.resourcetype", ['conference paper']),(None,["learning object"])]):
        result = item_metadata_validation(recid.object_uuid,"1",without_ver_id=without_ver.object_uuid)
        assert result == {'required': [], 'required_key': [], 'pattern': [],
                  'either': [],  'either_key': [], 'mapping': [], 'other': 'You cannot change the resource type of items that have been grant a DOI.'}

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

    # identifiery_type is NDL, resource_type is not doctoral thesis
    with patch("weko_workflow.utils.MappingData.get_first_data_by_mapping",\
        side_effect=[("item_1617258105262.resourcetype", ['thesis']),(None,["report"])]):
        result = item_metadata_validation(recid.object_uuid,"4",without_ver_id=without_ver.object_uuid)
        assert result == {'required': [], 'required_key': [], 'pattern': [],
                  'either': [],  'either_key': [], 'mapping': [], 'other': "When assigning a JaLC DOI through NDL, the resource type must be 'doctor thesis'."}

    # identifier_type is NDL, resource_type is doctoral thesis
    with patch("weko_workflow.utils.MappingData.get_first_data_by_mapping",return_value=("item_1617258105262.resourcetype",["doctoral thesis"])):
        result = item_metadata_validation(recid.object_uuid,"4")
        assert result == {'required': ['item_1617605131499.url.url'], 'required_key': ['jpcoar:URI'], 'pattern': [],
                  'either': [],  'either_key': [], 'mapping': [], }

    with patch("weko_workflow.utils.MappingData.get_first_data_by_mapping",\
        side_effect=[("item_1617258105262.resourcetype", ['thesis']),(None,["report"])]):
        result = item_metadata_validation(None,"5",without_ver_id=without_ver.object_uuid,record=record,file_path="test_file_path")
        assert result['other'] == 'Cannot register selected DOI for current Item Type of this item.'


#* THIS IS FOR JPCOAR2.0 DOI VALIDATION TEST
#* This test is for the following as well:
#*     def validation_item_property
#*     def handle_check_required_pattern_and_either
#*     def validattion_item_property_required
# def item_metadata_validation(item_id, identifier_type, record=None,
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_item_metadata_validation_2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_item_metadata_validation_2(db_records_for_doi_validation_test, item_type):
    #* 別表2-1 JaLC DOI
    recid0, depid0, record0, item0, parent0, doi0, deposit0 = db_records_for_doi_validation_test[0]
    result_0: dict = item_metadata_validation(
        item_id=recid0.object_uuid,
        identifier_type="1",
        record=record0,
    )
    result_0_keys: list = list(result_0.keys())
    result_0_check_list_1: list = [
        "jpcoar:URI",
        "dc:publisher",
        "dcndl:dateGranted",
        "datacite:date",
        "jpcoar:pageStart",
        "jpcoar:publisher_jpcoar"
    ]
    result_0_check_list_2: list = []
    for result_0_check_item_1 in result_0_check_list_1:
        for result_0_key in result_0_keys:
            if result_0_check_item_1 in result_0.get(result_0_key):
                result_0_check_list_2.append(result_0_check_item_1)
    assert len(result_0_check_list_2) == 2

    #* 別表2-2 JaLC DOI
    recid1, depid1, record1, item1, parent1, doi1, deposit1 = db_records_for_doi_validation_test[1]
    result_1: dict = item_metadata_validation(
        item_id=recid1.object_uuid,
        identifier_type="1",
        record=record1,
    )
    result_1_keys: list = list(result_1.keys())
    result_1_check_list_1: list = [
        "jpcoar:URI",
        "dc:publisher",
        "dcndl:dateGranted",
        "jpcoar:degreeGrantor",
        "jpcoar:publisher_jpcoar"
    ]
    result_1_check_list_2: list = []
    for result_1_check_item_1 in result_1_check_list_1:
        for result_1_key in result_1_keys:
            if result_1_check_item_1 in result_1.get(result_1_key):
                result_1_check_list_2.append(result_1_check_item_1)
    assert len(result_1_check_list_2) == 1
    # issue 45809
    assert not "jpcoar:pageStart" in result_1.get("either_key")

    #* 別表2-3 JaLC DOI
    recid2, depid2, record2, item2, parent2, doi2, deposit2 = db_records_for_doi_validation_test[2]
    result_2: dict = item_metadata_validation(
        item_id=recid2.object_uuid,
        identifier_type="1",
        record=record2,
    )
    result_2_keys: list = list(result_2.keys())
    result_2_check_list_1: list = [
        "jpcoar:URI",
        "dc:publisher",
        "dcndl:dateGranted",
        "datacite:date",
        "jpcoar:publisher_jpcoar"
    ]
    result_2_check_list_2: list = []
    for result_2_check_item_1 in result_2_check_list_1:
        for result_2_key in result_2_keys:
            if result_2_check_item_1 in result_2.get(result_2_key):
                result_2_check_list_2.append(result_2_check_item_1)
    assert len(result_2_check_list_2) == 1

    #* 別表2-4 JaLC DOI
    recid3, depid3, record3, item3, parent3, doi3, deposit3 = db_records_for_doi_validation_test[3]
    result_3: dict = item_metadata_validation(
        item_id=recid3.object_uuid,
        identifier_type="1",
        record=record3,
    )
    result_3_keys: list = list(result_3.keys())
    result_3_check_list_1: list = [
        "jpcoar:URI",
        "dc:publisher",
        "dcndl:dateGranted",
        "datacite:date",
        "jpcoar:publisher_jpcoar"
    ]
    result_3_check_list_2: list = []
    for result_3_check_item_1 in result_3_check_list_1:
        for result_3_key in result_3_keys:
            if result_3_check_item_1 in result_3.get(result_3_key):
                result_3_check_list_2.append(result_3_check_item_1)
    assert len(result_3_check_list_2) == 1

    #* 別表2-5 JaLC DOI
    recid4, depid4, record4, item4, parent4, doi4, deposit4 = db_records_for_doi_validation_test[4]
    result_4: dict = item_metadata_validation(
        item_id=recid4.object_uuid,
        identifier_type="1",
        record=record4,
    )
    result_4_keys: list = list(result_4.keys())
    result_4_check_list_1: list = [
        "jpcoar:URI",
        "jpcoar:givenName",
        "dc:publisher",
        "dcndl:dateGranted",
        "jpcoar:creatorName",
        "datacite:date",
        "jpcoar:publisher_jpcoar"
    ]
    result_4_check_list_2: list = []
    for result_4_check_item_1 in result_4_check_list_1:
        for result_4_key in result_4_keys:
            if result_4_check_item_1 in result_4.get(result_4_key):
                result_4_check_list_2.append(result_4_check_item_1)
    assert len(result_4_check_list_2) == 1

    #* 別表2-6 JaLC DOI
    recid5, depid5, record5, item5, parent5, doi5, deposit5 = db_records_for_doi_validation_test[5]
    result_5: dict = item_metadata_validation(
        item_id=recid5.object_uuid,
        identifier_type="1",
        record=record5,
    )
    result_5_keys: list = list(result_5.keys())
    result_5_check_list_1: list = [
        "jpcoar:URI",
        "dc:publisher",
        "dcndl:dateGranted",
        "datacite:date",
        "jpcoar:publisher_jpcoar"
    ]
    result_5_check_list_2: list = []
    for result_5_check_item_1 in result_5_check_list_1:
        for result_5_key in result_5_keys:
            if result_5_check_item_1 in result_5.get(result_5_key):
                result_5_check_list_2.append(result_5_check_item_1)
    assert len(result_5_check_list_2) == 1

    #* 別表3-1 Crossref DOI
    recid6, depid6, record6, item6, parent6, doi6, deposit6 = db_records_for_doi_validation_test[6]
    result_6: dict = item_metadata_validation(
        item_id=recid6.object_uuid,
        identifier_type="2",
        record=record6,
    )
    result_6_keys: list = list(result_6.keys())
    result_6_check_list_1: list = [
        "jpcoar:URI",
        "jpcoar:sourceIdentifier",
        "dc:publisher",
        "dcndl:dateGranted",
        "jpcoar:sourceTitle",
        "datacite:date",
        "jpcoar:publisher_jpcoar"
    ]
    result_6_check_list_2: list = []
    for result_6_check_item_1 in result_6_check_list_1:
        for result_6_key in result_6_keys:
            if result_6_check_item_1 in result_6.get(result_6_key):
                result_6_check_list_2.append(result_6_check_item_1)
    assert len(set(result_6_check_list_2)) == 3

    #* 別表3-2 Crossref DOI
    recid7, depid7, record7, item7, parent7, doi7, deposit7 = db_records_for_doi_validation_test[7]
    result_7: dict = item_metadata_validation(
        item_id=recid7.object_uuid,
        identifier_type="2",
        record=record7,
    )
    result_7_keys: list = list(result_7.keys())
    result_7_check_list_1: list = [
        "jpcoar:URI",
        "dc:publisher",
        "dcndl:dateGranted",
        "datacite:date",
        "jpcoar:publisher_jpcoar"
    ]
    result_7_check_list_2: list = []
    for result_7_check_item_1 in result_7_check_list_1:
        for result_7_key in result_7_keys:
            if result_7_check_item_1 in result_7.get(result_7_key):
                result_7_check_list_2.append(result_7_check_item_1)
    assert len(result_7_check_list_2) == 1

    #* 別表4-1 DataCite DOI
    recid8, depid8, record8, item8, parent8, doi8, deposit8 = db_records_for_doi_validation_test[8]
    result_8: dict = item_metadata_validation(
        item_id=recid8.object_uuid,
        identifier_type="3",
        record=record8,
    )
    result_8_keys: list = list(result_8.keys())
    result_8_check_list_1: list = [
        "jpcoar:URI",
        "jpcoar:givenName",
        "dc:publisher",
        "dcndl:dateGranted",
        "jpcoar:creatorName",
        "datacite:date",
        "jpcoar:publisher_jpcoar"
    ]
    result_8_check_list_2: list = []
    for result_8_check_item_1 in result_8_check_list_1:
        for result_8_key in result_8_keys:
            if result_8_check_item_1 in result_8.get(result_8_key):
                result_8_check_list_2.append(result_8_check_item_1)
    assert len(result_8_check_list_2) == 1

    #* 別表4-1 DataCite DOI ~ Testing jpcoar:givenName, jpcoar:creatorName, dc:publisher, jpcoar:publisherName for "en" value
    recid8, depid8, record8, item8, parent8, doi8, deposit8 = db_records_for_doi_validation_test[8]
    result_8: dict = item_metadata_validation(
        item_id=recid8.object_uuid,
        identifier_type="3",
        record=record8,
    )
    result_8_keys: list = list(result_8.keys())
    result_8_check_list_1: list = [
        "jpcoar:URI",
        "jpcoar:givenName",
        "dc:publisher",
        "dcndl:dateGranted",
        "jpcoar:creatorName",
        "datacite:date",
        "jpcoar:publisher_jpcoar"
    ]
    result_8_check_list_2: list = []
    for result_8_check_item_1 in result_8_check_list_1:
        for result_8_key in result_8_keys:
            if result_8_check_item_1 in result_8.get(result_8_key):
                result_8_check_list_2.append(result_8_check_item_1)
    assert len(result_8_check_list_2) == 1


# def merge_doi_error_list(current, new):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_merge_doi_error_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_merge_doi_error_list():
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
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_validation_item_property -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_handle_check_required_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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
    result = handle_check_required_pattern_and_either(mapping_data,["dc:title"],identifier_type="1")
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
    result = handle_check_required_pattern_and_either(mapping_data,['jpcoar:sourceTitle'],identifier_type="1")
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
    result = handle_check_required_pattern_and_either(mapping_data,['jpcoar:sourceTitle'],identifier_type="1")
    assert result == None

    # identifier_type = Crossref
    # exist requirements, is_either = False
    result = handle_check_required_pattern_and_either(mapping_data,["dc:title"],identifier_type="2")
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
    result = handle_check_required_pattern_and_either(mapping_data,["dc:title"],identifier_type="2",is_either=True)
    assert result == {'required': [], 'required_key': [], 'pattern': [], 'either': [['item_1617186331708.subitem_1551255647225', 'item_1617186331708.subitem_1551255648112']], 'either_key': ['dc:title'], 'mapping': []}

    # is_either is True, either in error_list
    result = handle_check_required_pattern_and_either(mapping_data,["dc:title"],identifier_type="2",error_list=result,is_either=True)
    assert result == {'required': [], 'required_key': [], 'pattern': [], 'either': [['item_1617186331708.subitem_1551255647225', 'item_1617186331708.subitem_1551255648112'], [['item_1617186331708.subitem_1551255647225', 'item_1617186331708.subitem_1551255648112']]], 'either_key': ['dc:title', 'dc:title'], 'mapping': []}
# def validattion_item_property_required(

# def validattion_item_property_either_required(

# def check_required_data(data, key, repeatable=False):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_check_required_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_required_data():
    #test No.12(W2023-22 2)
    data = {True,True,False}
    result = check_required_data(data,"keyx")
    assert result == ["keyx"]
    #test No.13(W2023-22 2)
    result = check_required_data(data,"keyx",repeatable=True)
    assert result == ["keyx"]
    #test No.14(W2023-22 2)
    data = {True,True}
    result = check_required_data(data,"keyx",repeatable=True)
    assert result == None



# def get_activity_id_of_record_without_version(pid_object=None):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_activity_id_of_record_without_version -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_activity_id_of_record_without_version(db_register_full_action,db_records):
    get_activity_id_of_record_without_version()

    pid = db_records[0][0]
    result = get_activity_id_of_record_without_version(pid)
    assert result == "2"


    with patch("weko_workflow.utils.WorkActivity.get_workflow_activity_by_item_id",return_value=None):
        result = get_activity_id_of_record_without_version(pid)
        assert result == None


# def check_suffix_identifier(idt_regis_value, idt_list, idt_type_list):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_check_suffix_identifier -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_suffix_identifier():
    regis_value = []
    idt_lsit = [1,2,]
    idt_type_list = ["value1","value2","DOI"]


#     def __init__(self, item_id=None, record=None):
#     def get_data_item_type(self):
#     def get_data_by_mapping(self, mapping_key, ignore_empty=False,
#     def get_first_data_by_mapping(self, mapping_key):
#     def get_first_property_by_mapping(self, mapping_key, ignore_empty=False):

# def get_sub_item_value(atr_vm, key):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_sub_item_value -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_item_value_in_deep -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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


# class IdentifierHandle(object):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::TestIdentifierHandle::test___init__ -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
class TestIdentifierHandle:
    # def __init__(self, item_id):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::TestIdentifierHandle::test___init__ -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test___init__(self, app):
        obj = IdentifierHandle()
        assert obj

        item_uuid = uuid.uuid4()
        with patch("weko_workflow.utils.WekoRecord.get_record", return_value=MagicMock(spec=WekoRecord)) as mock_get_record, \
                patch("weko_workflow.utils.ItemTypes.get_by_id", return_value=MagicMock(spec=ItemType, id=1)) as mock_get_by_id, \
                patch("weko_workflow.utils.Mapping.get_record", return_value=MagicMock(spec=Mapping)) as mock_get_mapping, \
                patch("weko_workflow.utils.ItemsMetadata.get_record", return_value=MagicMock(spec=ItemsMetadata)) as mock_get_metadata, \
                patch("weko_workflow.utils.get_full_mapping", return_value={"mapping": "mapping"}) as mock_mapping_data:
            obj = IdentifierHandle(item_uuid)
        assert obj.item_uuid == item_uuid
        assert obj.item_record is not None
        mock_get_record.assert_called_once_with(item_uuid)
        mock_get_by_id.assert_called()
        mock_get_mapping.assert_called_once_with(1)
        mock_mapping_data.assert_called_once()
        mock_get_metadata.assert_called_once_with(item_uuid)

#     def get_pidstore(self, pid_type='doi', object_uuid=None):

    # def check_pidstore_exist(self, pid_type, chk_value=None):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::TestIdentifierHandle::test_check_pidstore_exist -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_check_pidstore_exist(self, db, mocker):
        mock_persistent_identifier = mocker.patch("weko_workflow.utils.PersistentIdentifier")
        mock_query = MagicMock()
        mock_query.filter_by.return_value = mock_query
        mock_query.all.return_value = [MagicMock(pid_value="10.1234/abcd")]
        mock_persistent_identifier.query = mock_query

        records = IdentifierHandle().check_pidstore_exist("doi", "10.1234/abcd")
        assert records[0].pid_value == "10.1234/abcd"

#     def register_pidstore(self, pid_type, reg_value):
#     def delete_pidstore_doi(self, pid_value=None):
#     def remove_idt_registration_metadata(self):
#     def update_idt_registration_metadata(self, input_value, input_type):
#     def get_idt_registration_data(self):
#     def commit(self, key_id, key_val, key_typ, atr_nam, atr_val, atr_typ):

# def delete_bucket(bucket_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_delete_bucket -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_delete_bucket(db_records, add_file):
    bucket,_ = add_file(db_records[2][2])
    bucket_id = bucket.id
    assert Bucket.get(bucket_id) != None
    RecordsBuckets.query.filter(RecordsBuckets.bucket_id==bucket_id).delete()
    delete_bucket(bucket_id)
    assert Bucket.get(bucket_id) == None


# def merge_buckets_by_records(main_record_id,
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_merge_buckets_by_records -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize("is_delete",[True,False])
def test_merge_buckets_by_records(db_records, add_file,is_delete):
    bucket_11, rbucket_11 = add_file(db_records[1][2])
    bucket_10, rbucket_10 = add_file(db_records[2][2])

    result = merge_buckets_by_records(db_records[1][2].id,db_records[2][2].id,is_delete)
    assert result == rbucket_11.bucket_id

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_merge_buckets_by_records_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_merge_buckets_by_records_error(db_records, add_file):
    bucket_11, rbucket_11 = add_file(db_records[1][2])
    bucket_10, rbucket_10 = add_file(db_records[2][2])
    with patch("weko_workflow.utils.delete_bucket",side_effect=Exception):
        result = merge_buckets_by_records(db_records[1][2].id,db_records[2][2].id,True)
        assert result == None


# def delete_unregister_buckets(record_uuid):

# def set_bucket_default_size(record_uuid):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_set_bucket_default_size -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_set_bucket_default_size(db, db_records, add_file):
    bucket_10, rbucket_10 = add_file(db_records[2][2])
    record_id = rbucket_10.record_id
    bucket_id = bucket_10.id
    set_bucket_default_size(record_id)
    db.session.commit()
    bucket = Bucket.get(bucket_id)
    assert bucket.quota_size == 50 * 1024 * 1024 * 1024
    assert bucket.max_file_size == 50 * 1024 * 1024 * 1024


# def is_show_autofill_metadata(item_type_name):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_is_show_autofill_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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

    result = get_parent_pid_with_type("hdl",db_records[0][2].id)
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
def test_convert_record_to_item_metadata(db_records, db_itemtype):
    record = WekoRecord.get_record(db_records[0][2].id)
    result = convert_record_to_item_metadata(record)
    test = {'id': '1', '$schema': '1', 'created_by': 1, 'pubdate': '2022-08-20', 'title': 'title',
            'shared_user_ids': [],
            'item_1617186331708': [{'subitem_1551255647225': 'title', 'subitem_1551255648112': 'ja','subitem_stop/continue': 'Continue'}],
            'item_1617186819068': {'subitem_identifier_reg_text': 'test/0000000001', 'subitem_identifier_reg_type': 'JaLC'},
            'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'},
            'item_1617605131499': [{'accessrole': 'open_access','date': [{'dateType': 'Available','dateValue': '2022-10-03'}],
            'displaytype': 'detail','filename': 'check_2022-03-10.tsv','filesize': [{'value': '460 B'}],
            'format': 'text/tab-separated-values','is_thumbnail': True,'licensetype': 'license_12',
            'url': {'url': 'https://localhost/record/1/files/test.txt'},
            'version_id': '29dd361d-dc7f-49bc-b471-bdb5752afef5'}],
            'owner': 1, 'owners': [1], 'pid': {'revision_id': 0, 'type': 'depid','value': '1'}}
    assert result == test

    # record_metadataのjsonに"weko_shared_ids": []を設定する。
    record = WekoRecord.get_record(db_records[7][2].id)
    result = convert_record_to_item_metadata(record)
    excepted = {'id': '194',
                '$schema': '1',
                'owner': 1,
                'owners': [1],
                'created_by': 1,
                'pid': {'revision_id': 0, 'type': 'depid','value': '194'},
                'pubdate': '2023-04-25',
                'title': 'テスト タイトル1',
                'shared_user_ids': [],
                'item_1617186331708': [{'subitem_1551255647225': 'テスト タイトル1', 'subitem_1551255648112': 'en'}]
                }
    assert result == excepted

    # record_metadataのjsonに"weko_shared_ids": [6]を設定する。
    record = WekoRecord.get_record(db_records[8][2].id)
    result = convert_record_to_item_metadata(record)
    excepted = {'id': '195',
                '$schema': '1',
                'owner': 1,
                'owners': [1],
                'created_by': 1,
                'pid': {'revision_id': 0, 'type': 'depid','value': '195'},
                'pubdate': '2023-04-25',
                'title': 'テスト タイトル2',
                'shared_user_ids': [6],
                'item_1617186331708': [{'subitem_1551255647225': 'テスト タイトル2', 'subitem_1551255648112': 'en'}]
                }
    assert result == excepted

# def prepare_edit_workflow(post_activity, recid, deposit):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_edit_workflow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize("order_if",[0, 1, 2, 3])
def test_prepare_edit_workflow(app, workflow, db_records,users,mocker, order_if):
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
        recid = db_records[6][0]
        deposit = db_records[6][6]
        mocker.patch("weko_workflow.utils.FeedbackMailList.get_mail_list_by_item_id", return_value = [{"email":"exam@exam.com","author_id":""}])
        request_mail_mock = mocker.patch("weko_workflow.utils.RequestMailList.get_mail_list_by_item_id", return_value = [{"email":"exam@exam.com","author_id":""}])
        item_application_mock = mocker.patch("weko_workflow.utils.ItemApplication.get_item_application_by_item_id", return_value = {"workflow":1, "terms":"term_free", "termsDescription":"test"})

        if order_if == 0:
            result = prepare_edit_workflow(data,recid,deposit)
            request_mail_mock.assert_called()
            item_application_mock.assert_called()
        if order_if == 1:
            with patch("weko_workflow.utils.IdentifierHandle.get_pidstore", return_value = None):
                result = prepare_edit_workflow(data,recid,deposit)
            with patch("weko_workflow.utils.IdentifierHandle.get_pidstore", return_value = PersistentIdentifier(status= PIDStatus.DELETED)) as idh:
                result = prepare_edit_workflow(data,recid,deposit)
        if order_if == 2:
            with patch("weko_workflow.utils.Bucket.get", return_value=None):
                with pytest.raises(SQLAlchemyError):
                    result = prepare_edit_workflow(data,recid,deposit)
        if order_if == 3:
            with patch("weko_workflow.utils.PersistentIdentifier") as pi:
                type(pi).query = pi
                pi.filter_by = MagicMock(return_value = pi)
                pi.one_or_none = MagicMock(return_value = None)
                recid = db_records[7][0]
                deposit = db_records[7][6]
                result = prepare_edit_workflow(data,recid,deposit)
                assert result.activity_id != None

        recid = db_records[6][0]
        deposit = db_records[6][6]
        res = prepare_edit_workflow(data,recid,deposit)
        assert res.activity_id != None

        mocker.patch("weko_workflow.utils.IdentifierHandle.get_pidstore")
        with patch("weko_deposit.api.WekoRecord.get_record_by_pid", return_value=None):
            recid = db_records[4][0]
            deposit = db_records[4][6]
            res = prepare_edit_workflow(data,recid,deposit)
            assert res.activity_id != None

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_edit_workflow_existing_draft_pid_and_bucket -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_prepare_edit_workflow_existing_draft_pid_and_bucket(app, workflow, db_records, users, mocker):
    with app.test_request_context():
        login_user(users[2]["obj"])
        mocker.patch("weko_workflow.utils.WekoDeposit.update")
        mocker.patch("weko_workflow.utils.WekoDeposit.commit")
        mocker.patch("weko_workflow.utils.WekoDeposit.publish")

        data = {
            "flow_id": workflow["flow"].id,
            "workflow_id": workflow["workflow"].id,
            "community": 1,
            "itemtype_id": 1,
            "activity_login_user": 1,
            "activity_update_user": 1
        }
        recid = db_records[3][0]
        deposit = db_records[3][6]

        # 52716-2 existing draft pid and bucket
        res = prepare_edit_workflow(data, recid, deposit)
        assert res.item_id != None

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_edit_workflow_existing_draft_pid_no_bucket -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_prepare_edit_workflow_existing_draft_pid_no_bucket(app, workflow, db_records, users, mocker):
    with app.test_request_context():
        login_user(users[2]["obj"])
        draft_pid = db_records[12][0]
        deposit = db_records[12][6]

        before_count_bucket = Bucket.query.count()
        before_count_records_buckets = RecordsBuckets.query.count()

        mocker.patch("weko_workflow.utils.WekoDeposit.update")
        mocker.patch("weko_workflow.utils.WekoDeposit.commit")
        mocker.patch("weko_workflow.utils.WekoDeposit.publish")

        mocker.patch("invenio_deposit.api.Deposit.files")
        create_bucket_mock = mocker.patch("invenio_files_rest.models.Bucket.create")
        data = {
            "flow_id": workflow["flow"].id,
            "workflow_id": workflow["workflow"].id,
            "community": 1,
            "itemtype_id": 1,
            "activity_login_user": 1,
            "activity_update_user": 1
        }
        mocker.patch("invenio_files_rest.models.Bucket.get" , return_value=None)

        # 52716-3 existing draft pid but no bucket
        with patch("invenio_records_files.models.RecordsBuckets.create", side_effect=SQLAlchemyError("Test Exception")) as create_records_buckets_mock:
            with pytest.raises(SQLAlchemyError) as excinfo:
                prepare_edit_workflow(data, draft_pid, deposit)

                assert create_bucket_mock.called
                assert create_records_buckets_mock.called
                assert str(ex) == "Test Exception"

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_edit_workflow_check_doi -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_prepare_edit_workflow_check_doi(app, workflow, db_records, users, mocker):
    with app.test_request_context():
        login_user(users[2]["obj"])
        mocker.patch("weko_workflow.utils.WekoDeposit.update")
        mocker.patch("weko_workflow.utils.WekoDeposit.commit")
        mocker.patch("weko_workflow.utils.WekoDeposit.publish")
        draft_pid = db_records[3][0]
        deposit = db_records[3][6]
        data = {
            "flow_id": workflow["flow"].id,
            "workflow_id": workflow["workflow"].id,
            "community": 1,
            "itemtype_id": 1,
            "activity_login_user": 1,
            "activity_update_user": 1
        }
        mock_pid_doi = MagicMock()
        # 52716-4 pid_doi.status == PIDStatus.DELETED
        mock_pid_doi.status = PIDStatus.DELETED
        with patch("weko_workflow.utils.IdentifierHandle.get_pidstore", return_value=mock_pid_doi):
            rtn = prepare_edit_workflow(data, draft_pid, deposit)

            action_identifier = ActionIdentifier.query.filter_by(activity_id=rtn.activity_id).first()
            assert action_identifier.action_identifier_select == -3

        # 52716-5 pid_doi.status is not PIDStatus.DELETED
        mock_pid_doi.status = PIDStatus.REGISTERED
        with patch("weko_workflow.utils.IdentifierHandle.get_pidstore", return_value=mock_pid_doi):
            rtn = prepare_edit_workflow(data, draft_pid, deposit)

            action_identifier = ActionIdentifier.query.filter_by(activity_id=rtn.activity_id).first()
            assert action_identifier.action_identifier_select == -1

        # 52716-6 pid_doi is None
        mock_pid_doi = None
        with patch("weko_workflow.utils.IdentifierHandle.get_pidstore", return_value=mock_pid_doi):
            rtn = prepare_edit_workflow(data, draft_pid, deposit)

            action_identifier = ActionIdentifier.query.filter_by(activity_id=rtn.activity_id).first()
            assert action_identifier.action_identifier_select == 0

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_edit_workflow_existing_feedbackmail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_prepare_edit_workflow_existing_feedbackmail(app, workflow, db_records, users, mocker):
    with app.test_request_context():
        login_user(users[2]["obj"])
        mocker.patch("weko_workflow.utils.WekoDeposit.update")
        mocker.patch("weko_workflow.utils.WekoDeposit.commit")
        mocker.patch("weko_workflow.utils.WekoDeposit.publish")

        data = {
            "flow_id": workflow["flow"].id,
            "workflow_id": workflow["workflow"].id,
            "community": 1,
            "itemtype_id": 1,
            "activity_login_user": 1,
            "activity_update_user": 1
        }
        recid = db_records[3][0]
        deposit = db_records[3][6]

        # 52716-7 feedbackmail exists
        with patch("weko_workflow.utils.FeedbackMailList.get_mail_list_by_item_id", return_value=["test@example.com"]):
            mock_create_or_update_action_feedbackmail = mocker.patch("weko_workflow.api.WorkActivity.create_or_update_action_feedbackmail")
            res = prepare_edit_workflow(data, recid, deposit)

            assert mock_create_or_update_action_feedbackmail.called

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_edit_workflow_rtn_none -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_prepare_edit_workflow_rtn_none(app, workflow, db_records, users, mocker):
    with app.test_request_context():
        login_user(users[2]["obj"])
        mocker.patch("weko_workflow.utils.WekoDeposit.update")
        mocker.patch("weko_workflow.utils.WekoDeposit.commit")
        mocker.patch("weko_workflow.utils.WekoDeposit.publish")

        data = {
            "flow_id": workflow["flow"].id,
            "workflow_id": workflow["workflow"].id,
            "community": 1,
            "itemtype_id": 1,
            "activity_login_user": 1,
            "activity_update_user": 1
        }
        recid = db_records[3][0]
        deposit = db_records[3][6]

        # 52716-9 failed init_activity
        with patch("weko_workflow.api.WorkActivity.init_activity", return_value=None):
            res = prepare_edit_workflow(data, recid, deposit)

            assert res is None

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_edit_workflow_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_prepare_edit_workflow_exception(app, workflow, db_records, users, mocker):
    with app.test_request_context():
        login_user(users[2]["obj"])
        draft_pid = db_records[3][0]
        deposit = db_records[3][6]
        data = {
            "flow_id": workflow["flow"].id,
            "workflow_id": workflow["workflow"].id,
            "community": 1,
            "itemtype_id": 1,
            "activity_login_user": 1,
            "activity_update_user": 1
        }
        mocker.patch("weko_workflow.utils.WekoDeposit.update")
        mocker.patch("weko_workflow.utils.WekoDeposit.publish")
        # 52716-10 raises SQLAlchemyError
        with patch("weko_workflow.utils.WekoDeposit.commit", side_effect=SQLAlchemyError("Test Exception")):
            with pytest.raises(SQLAlchemyError) as excinfo:
                prepare_edit_workflow(data, draft_pid, deposit)
            assert str(excinfo.value) == "Test Exception"

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_edit_workflow_draft_item_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_prepare_edit_workflow_draft_item_exception(app, workflow, db_records, users, mocker):
    with app.test_request_context():
        login_user(users[2]["obj"])
        mocker.patch("weko_workflow.utils.WekoDeposit.update")
        mocker.patch("weko_workflow.utils.WekoDeposit.commit")
        mocker.patch("weko_workflow.utils.WekoDeposit.publish")
        draft_pid = db_records[2][0]
        deposit = db_records[2][6]
        data = {
            "flow_id": workflow["flow"].id,
            "workflow_id": workflow["workflow"].id,
            "community": 1,
            "itemtype_id": 1,
            "activity_login_user": 1,
            "activity_update_user": 1
        }
        # 52716-11 failed prepare_draft_item
        mocker.patch("weko_deposit.api.WekoDeposit.prepare_draft_item", return_value=None)
        with pytest.raises(AttributeError) as excinfo:
            prepare_edit_workflow(data, draft_pid, deposit)
        assert "object has no attribute" in str(excinfo.value)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_edit_workflow_get_record_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_prepare_edit_workflow_get_record_exception(app, workflow, db_records, users, mocker):
    with app.test_request_context():
        login_user(users[2]["obj"])
        mocker.patch("weko_workflow.utils.WekoDeposit.update")
        mocker.patch("weko_workflow.utils.WekoDeposit.commit")
        mocker.patch("weko_workflow.utils.WekoDeposit.publish")
        draft_pid = db_records[3][0]
        deposit = db_records[3][6]
        data = {
            "flow_id": workflow["flow"].id,
            "workflow_id": workflow["workflow"].id,
            "community": 1,
            "itemtype_id": 1,
            "activity_login_user": 1,
            "activity_update_user": 1
        }
        # 52716-12 failed get_record
        mocker.patch("weko_deposit.api.WekoDeposit.get_record", return_value=None)
        with pytest.raises(AttributeError) as excinfo:
            prepare_edit_workflow(data, draft_pid, deposit)
        assert "object has no attribute" in str(excinfo.value)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_edit_workflow_convert_item_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_prepare_edit_workflow_convert_item_exception(app, workflow, db_records, users, mocker):
    with app.test_request_context():
        login_user(users[2]["obj"])
        mocker.patch("weko_workflow.utils.WekoDeposit.update")
        mocker.patch("weko_workflow.utils.WekoDeposit.commit")
        mocker.patch("weko_workflow.utils.WekoDeposit.publish")
        draft_pid = db_records[12][0]
        deposit = db_records[12][6]
        data = {
            "flow_id": workflow["flow"].id,
            "workflow_id": workflow["workflow"].id,
            "community": 1,
            "itemtype_id": 1,
            "activity_login_user": 1,
            "activity_update_user": 1
        }
        # 52716-13 failed convert_record_to_item_metadata
        with pytest.raises(KeyError) as excinfo:
            prepare_edit_workflow(data, draft_pid, deposit)
        assert isinstance(excinfo.value, KeyError)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_edit_workflow_pidstore_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_prepare_edit_workflow_pidstore_exception(app, workflow, db_records, users, mocker):
    with app.test_request_context():
        login_user(users[2]["obj"])
        mocker.patch("weko_workflow.utils.WekoDeposit.update")
        mocker.patch("weko_workflow.utils.WekoDeposit.commit")
        mocker.patch("weko_workflow.utils.WekoDeposit.publish")
        draft_pid = db_records[3][0]
        deposit = db_records[3][6]
        data = {
            "flow_id": workflow["flow"].id,
            "workflow_id": workflow["workflow"].id,
            "community": 1,
            "itemtype_id": 1,
            "activity_login_user": 1,
            "activity_update_user": 1
        }
        # 52716-14 failed get_pidstore
        with patch("weko_workflow.utils.get_parent_pid_with_type", side_effect=PIDDoesNotExistError("recid", draft_pid.pid_value)):
            with pytest.raises(PIDDoesNotExistError):
                rtn = prepare_edit_workflow(data, draft_pid, deposit)

                action_identifier = ActionIdentifier.query.filter_by(activity_id=rtn.activity_id).first()
                assert action_identifier.action_identifier_select == 0



# def prepare_edit_workflow(post_activity, recid, deposit):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_edit_workflow2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize("order_if",[0, 1])
def test_prepare_edit_workflow2(app, workflow, db_records,users,mocker, order_if):
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
        recid = db_records[6][0]
        deposit = db_records[6][6]

        if order_if == 0:
            mocker.patch("weko_workflow.utils.FeedbackMailList.get_mail_list_by_item_id", return_value = [{"email":"exam@exam.com","author_id":""}])
            mocker.patch("weko_workflow.utils.RequestMailList.get_mail_list_by_item_id", return_value = [{"email":"exam@exam.com","author_id":""}])
            request_mail_mock = mocker.patch("weko_workflow.utils.WorkActivity.create_or_update_activity_request_mail")
            assert prepare_edit_workflow(data,recid,deposit)
            request_mail_mock.assert_called()

        if order_if == 1:
            mocker.patch("weko_workflow.utils.FeedbackMailList.get_mail_list_by_item_id", return_value = [])
            mocker.patch("weko_workflow.utils.RequestMailList.get_mail_list_by_item_id", return_value = [])
            request_mail_mock = mocker.patch("weko_workflow.utils.WorkActivity.create_or_update_activity_request_mail")
            assert prepare_edit_workflow(data,recid,deposit)
            request_mail_mock.assert_not_called()

# def prepare_delete_workflow(deposit, current_pid, recid):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_delete_workflow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_prepare_delete_workflow(app, db_records,users,db_register,mocker):
    # delete flow item
    del_recid, _, _, _, _, _, del_deposit = db_records[7]
    del_workflow_id = db_register["activities"][7].workflow_id
    del_flow_id = db_register["activities"][7].flow_id
    del_title = db_register["activities"][7].title
    del_post_activity = {
        'pid_value': del_recid, 'itemtype_id': '1',
        'community': None, 'workflow_id': del_workflow_id,
        'title': del_title, 'flow_id': del_flow_id, 'shared_user_id': '-1'
    }

    # not delete flow item
    recid_1,  _, _, _, _, _, deposit_1 = db_records[2]
    workflow_id_1 = db_register["activities"][0].workflow_id
    flow_id_1 = db_register["activities"][0].flow_id
    title_1 = db_register["activities"][0].title
    post_activity_1 = {
        'pid_value': recid_1, 'itemtype_id': '1',
        'community': None, 'workflow_id': workflow_id_1,
        'title': title_1, 'flow_id': flow_id_1, 'shared_user_id': '-1'
    }

    # approval delete flow item
    app_recid, _, _, _, _, _, app_deposit = db_records[7]
    app_workflow_id = db_register["activities"][8].workflow_id
    app_flow_id = db_register["activities"][8].flow_id
    app_title = db_register["activities"][8].title
    app_post_activity = {
        'pid_value': app_recid, 'itemtype_id': '1',
        'community': None, 'workflow_id': app_workflow_id,
        'title': app_title, 'flow_id': app_flow_id, 'shared_user_id': '-1'
    }

    current_app.config.update(
        WEKO_NOTIFICATIONS=False
    )
    with app.test_request_context(), \
            patch("flask_login.utils._get_user", return_value=users[0]['obj']), \
            patch("weko_records_ui.views.check_created_id_by_recid", return_value=True), \
            patch("weko_records_ui.views.soft_delete", return_value=True):
        result = prepare_delete_workflow(del_post_activity, del_recid, del_deposit)
        assert result.workflow_id

        result = prepare_delete_workflow(post_activity_1, recid_1, deposit_1)
        assert result.workflow_id

        result = prepare_delete_workflow(app_post_activity, app_recid, app_deposit)
        assert result.workflow_id

# def handle_finish_workflow(deposit, current_pid, recid):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_handle_finish_workflow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_handle_finish_workflow(workflow, db_records, mocker, db_itemtype2):
    result = handle_finish_workflow(None, None, None)
    assert result == None
    mocker.patch("weko_deposit.api.WekoDeposit.publish")
    mocker.patch("weko_deposit.api.WekoDeposit.commit")
    mocker.patch("invenio_oaiserver.tasks.update_records_sets.delay")

    deposit = db_records[2][6]
    current_pid = db_records[2][0]
    recid = MagicMock(spec=RecordIdentifier, recid=current_pid.pid_value)
    with patch('weko_deposit.api.WekoIndexer.update_es_data'):
        result = handle_finish_workflow(deposit,current_pid,recid)
    assert result

    with patch('weko_deposit.api.WekoIndexer.update_es_data'):
        with patch("weko_workflow.utils.RequestMailList.update") as update_request:
            result = handle_finish_workflow(deposit,current_pid,recid)
            assert result
            update_request.assert_not_called()
        with patch("weko_workflow.utils.RequestMailList.update") as update_request:
            result = handle_finish_workflow(deposit,current_pid,None)
            assert result
            update_request.assert_not_called()

        mocker.patch("weko_workflow.utils.FeedbackMailList.get_mail_list_by_item_id", return_value = [{"email":"exam@exam.com","author_id":""}])
        mocker.patch("weko_workflow.utils.RequestMailList.get_mail_list_by_item_id", return_value = [{"email":"exam@exam.com","author_id":""}])
        with patch("weko_workflow.utils.RequestMailList.update") as update_request:
            result = handle_finish_workflow(deposit,current_pid,recid)
            assert result
            update_request.assert_called()
        with patch("weko_workflow.utils.RequestMailList.update") as update_request:
            result = handle_finish_workflow(deposit,current_pid,None)
            assert result
            update_request.assert_not_called()


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_handle_finish_workflow2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_handle_finish_workflow2(workflow, db_records, item_type, mocker):
    result = handle_finish_workflow(None, None, None)
    assert result == None
    mocker.patch("weko_deposit.api.WekoDeposit.publish")
    mocker.patch("weko_deposit.api.WekoDeposit.commit")
    mocker.patch("invenio_oaiserver.tasks.update_records_sets.delay")

    deposit = db_records[2][6]
    current_pid = db_records[2][0]
    recid = db_records[2][2]
    feedback_mail_list = FeedbackMailList()
    request_mail_list = RequestMailList()
    mock_deposit = mocker.patch('weko_workflow.utils.WekoDeposit.newversion', return_value=deposit)
    mocker.patch('weko_workflow.utils.WekoDeposit.update_request_mail')
    mocker.patch('weko_workflow.utils.FeedbackMailList.get_mail_list_by_item_id', return_value=[feedback_mail_list])
    mock_feedback_mail = mocker.patch('weko_workflow.utils.FeedbackMailList.update')
    mocker.patch('weko_workflow.utils.RequestMailList.get_mail_list_by_item_id', return_value=[request_mail_list])
    mock_request_mail = mocker.patch('weko_workflow.utils.RequestMailList.update')
    mock_update_item = mocker.patch('weko_workflow.utils.UpdateItem.publish')
    result = handle_finish_workflow(deposit,current_pid,recid)
    assert result == deposit.model.id
    mock_deposit.assert_called_once()
    mock_feedback_mail.assert_called_once()
    mock_request_mail.assert_called_once()
    assert mock_update_item.call_count == 2

    result = handle_finish_workflow(deposit,current_pid,None)
    assert result == current_pid.object_uuid

    deposit = db_records[1][6]
    current_pid = db_records[1][0]
    recid = db_records[1][2]
    result = handle_finish_workflow(deposit,current_pid,None)
    assert result == current_pid.object_uuid

    with patch('weko_deposit.pidstore.get_record_without_version', side_effect=Exception):
        result = handle_finish_workflow(deposit,current_pid,recid)
        assert result == None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_handle_finish_workflow_external_system -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_handle_finish_workflow_external_system(workflow, db_records, mocker):
    record = WekoRecord.get_record_by_pid("1")
    deposit = WekoDeposit(record, record.model)
    mocker.patch("weko_deposit.api.WekoDeposit.publish")
    mocker.patch("weko_workflow.utils.UpdateItem.publish")
    mocker.patch("invenio_oaiserver.tasks.update_records_sets.delay")
    mocker.patch("weko_workflow.utils.WekoRecord.get_record_by_pid", return_value=record)
    mocker.patch("weko_deposit.api.WekoDeposit.newversion", MagicMock())
    mocker.patch("weko_workflow.utils.ItemReference.get_src_references", return_value=MagicMock())

    current_pid = PersistentIdentifier.get("recid", "1")
    recid = MagicMock(spec=RecordIdentifier, recid=current_pid.pid_value)
    with patch('weko_workflow.utils.call_external_system') as mock_external:
        handle_finish_workflow(deposit, current_pid, recid)
        mock_external.assert_called()
        assert mock_external.call_args[1]["old_record"] is None
        assert mock_external.call_args[1]["new_record"] is not None

    current_pid = PersistentIdentifier.get("recid", "1.0")
    with patch('weko_workflow.utils.call_external_system') as mock_external:
        handle_finish_workflow(deposit, current_pid, None)
        mock_external.assert_called()
        assert mock_external.call_args[1]["old_record"] is not None
        assert mock_external.call_args[1]["new_record"] is not None

    current_pid = PersistentIdentifier.get("recid", "1.1")
    with patch('weko_workflow.utils.call_external_system') as mock_external:
        handle_finish_workflow(deposit, record.pid, None)
        mock_external.assert_called()
        assert mock_external.call_args[1]["old_record"] is not None
        assert mock_external.call_args[1]["new_record"] is not None

    current_pid = PersistentIdentifier.get("recid", "1")
    with patch("weko_deposit.pidstore.get_record_without_version",
               return_value=None):
        with patch('weko_workflow.utils.call_external_system') as mock_external:
            handle_finish_workflow(deposit, current_pid, None)
            mock_external.assert_not_called()


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
@pytest.mark.parametrize('timeout', [
    None,
    100
])
def test_update_cache_data(client, timeout):
    """
    Test update_cache_data function

    Args:
        client (fixture): cliant setting
    """

    key = "test_key"
    value = "test_value"

    with patch("weko_workflow.utils.current_cache.set") as mock_set:
        with patch("weko_workflow.utils.current_app"):
            update_cache_data(key, value, timeout)
            if timeout is None:
                # 51991 case.01(update_cache_data)
                mock_set.assert_called_once_with(key, value)
            else:
                # 51991 case.02(update_cache_data)
                mock_set.assert_called_once_with(key, value, timeout=timeout)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_update_cache_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_update_cache_data_timedelta(client):
    """
    Test update_cache_data function use timedelta

    Args:
        client (fixture): cliant setting
    """

    key = "test_key"
    value = "test_value"
    # expect current_app.config['PERMANENT_SESSION_LIFETIME']
    fallback_timeout = datetime.timedelta(days=1)

    with patch("weko_workflow.utils.current_cache.set") as mock_set:
        with patch("weko_workflow.utils.current_app") as mock_app:
            # 51991 case.03(update_cache_data)
            timeout = datetime.timedelta(seconds=60)
            update_cache_data(key, value, timeout)
            mock_set.assert_called_once_with(key, value, timeout=timeout)

    with patch("weko_workflow.utils.current_cache.set", side_effect=ResponseError('Test Error')) as mock_set:
        with patch("weko_workflow.utils.current_app") as mock_app:
            # 51991 case.04(update_cache_data)
            mock_app.config = {"PERMANENT_SESSION_LIFETIME": fallback_timeout}
            timeout = datetime.timedelta(seconds=0)
            with pytest.raises(ResponseError):
                update_cache_data(key, value, timeout=timeout)
                mock_set.assert_any_call(key, value, timeout=fallback_timeout)


# def get_cache_data(key: str):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_cache_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_cache_data(client):
    key = "test_key"
    value = "test_value"
    current_cache.set(key, value)
    result = get_cache_data(key)
    assert result == value


# def check_an_item_is_locked(item_id=None):
# def bulk_check_an_item_is_locked(item_ids=[]):
#     def check(workers):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_check_an_item_is_locked -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_an_item_is_locked(app):
    with app.app_context():
        with patch("weko_workflow.utils.inspect") as mock_inspect:
            mock_inspect_instance = mock_inspect.return_value
            # inspect(timeout=_timeout).ping()
            mock_inspect_instance.ping.return_value = True
            # inspect(timeout=_timeout).active()
            mock_inspect_instance.active.return_value = {
                'worker1': [
                    {'name': 'weko_search_ui.tasks.import_item', 'args': [{'id': '1'}]},
                    {'name': 'weko_search_ui.tasks.import_item', 'args': [{'id': '2'}]},
                ],
                'worker2': [
                    {'name': 'weko_search_ui.tasks.import_item', 'args': [{'id': '3'}, {'id': '99'}]},
                ],
            }
            # inspect(timeout=_timeout).reserved()
            mock_inspect_instance.reserved.return_value = {
                'worker3': [
                    {'name': 'weko_search_ui.tasks.import_item', 'args': [{'id': '4'}]},
                    {'name': 'weko_search_ui.tasks.test_task', 'args': [{'id': '5'}]},
                ],
            }

            item_ids = list(range(1,5))
            result = []
            for i in item_ids:
                if check_an_item_is_locked(str(i)):
                    result.append(str(i))

            assert bulk_check_an_item_is_locked(item_ids) == result == ["1","2","3","4"]

            assert check_an_item_is_locked() == False
            assert bulk_check_an_item_is_locked() == []


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
        assert get_url_root() == "http://TEST_SERVER.localdomain/"
        app.config["THEME_SITEURL"] = "https://weko3.ir.rcos.nii.ac.jp/"
        assert get_url_root() == "http://TEST_SERVER.localdomain/"

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
    assert record == {'_oai': {'id': 'oai:weko3.example.org:00000001', 'sets': ['1']}, 'path': ['1'], 'owner': 1, 'owners': [1], 'recid': '1', 'title': ['title'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-08-20'}, '_buckets': {'deposit': '3e99cfca-098b-42ed-b8a0-20ddd09b3e02'}, '_deposit': {'id': '1', 'pid': {'type': 'depid', 'value': '1', 'revision_id': 0}, 'owner': 1, 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'title', 'author_link': [], 'created_by': 1, 'item_type_id': '1', 'publish_date': '2022-08-20', 'publish_status': '0', 'weko_shared_ids': [], 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'title', 'subitem_1551255648112': 'ja','subitem_stop/continue': 'Continue'}]}, "item_1617186819068": {"attribute_name": "Identifier Registration","attribute_value_mlt": [{"subitem_identifier_reg_text" :"test/0000000001","subitem_identifier_reg_type": "JaLC"}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]},'item_1617605131499': {'attribute_name': 'File','attribute_type': 'file','attribute_value_mlt': [{'accessrole': 'open_access','date': [{'dateType': 'Available','dateValue': '2022-10-03'}],'displaytype': 'detail','filename': 'check_2022-03-10.tsv','filesize': [{'value': '460 ''B'}],'format': 'text/tab-separated-values','is_thumbnail': True,'licensetype': 'license_12','url': {'url': 'https://localhost/record/1/files/test.txt'},'version_id': '29dd361d-dc7f-49bc-b471-bdb5752afef5'}]},'item_1664947259584': {'attribute_name': 'サムネイル','attribute_value_mlt': [{'subitem_thumbnail': [{'thumbnail_label': 'test.png','thumbnail_url': '/api/files/29ad484d-4ed1-4caf-8b21-ab348ae7bf28/test.png?versionId=ecd5715e-4ca5-4e45-b93c-5089f52860a0'}]}]}, 'relation_version_is_last': True}


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
def test_get_allow_multi_thumbnail(app, db_register_full_action):
    result = get_allow_multi_thumbnail(1,"1")
    assert result == False

    result = get_allow_multi_thumbnail(1,None)
    assert result == None
# def is_usage_application_item_type(activity_detail):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_is_usage_application_item_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_is_usage_application_item_type(db_register_full_action):
    activity = db_register_full_action["activities"][0]
    result = is_usage_application_item_type(activity)
    assert result == False

    current_app.config.update(
        WEKO_ITEMS_UI_APPLICATION_ITEM_TYPES_LIST=["テストアイテムタイプ"]
    )
    result = is_usage_application_item_type(activity)
    assert result == True
# def is_usage_application(activity_detail):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_is_usage_application -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_is_usage_application(db_register_full_action):
    activity = db_register_full_action["activities"][0]
    result = is_usage_application(activity)
    assert result == False

    current_app.config.update(
        WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPES_LIST=["テストアイテムタイプ"]
    )
    result = is_usage_application(activity)
    assert result == True
# def send_mail_reminder(mail_info):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_send_mail_reminder -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@patch('weko_workflow.utils.get_mail_data')
@patch('weko_workflow.utils.replace_characters')
@patch('weko_workflow.utils.send_mail')
def test_send_mail_reminder(
    mock_send_mail, mock_replace_characters, mock_get_mail_data
):
    # Default test data
    test_mail_data = {
        'mail_subject': 'Test Subject',
        'mail_body': 'Test Body',
        'mail_recipients': ['test@example.com'],
        'mail_cc': ['cc@example.com'],
        'mail_bcc': ['bcc@example.com']
    }
    test_mail_info = {
        'mail_address': 'mail@example.com'
    }

    # Test for ValueError when the 'subject' key has no value
    empty_subject_data = copy.deepcopy(test_mail_data)
    empty_subject_data['mail_subject'] = ''
    mock_get_mail_data.return_value = empty_subject_data
    with pytest.raises(ValueError) as e:
        send_mail_reminder(test_mail_info)
    assert str(e.value) == 'Cannot get email subject'

    # Test for ValueError when the 'body' key has no value
    empty_body_data = copy.deepcopy(test_mail_data)
    empty_body_data['mail_body'] = ''
    mock_get_mail_data.return_value = empty_body_data
    with pytest.raises(ValueError) as e:
        send_mail_reminder(test_mail_info)
    assert str(e.value) == 'Cannot get email body'

    # Test for ValueError when the 'subject' key is missing
    missing_subject_data = copy.deepcopy(test_mail_data)
    del missing_subject_data['mail_subject']
    mock_get_mail_data.return_value = missing_subject_data
    with pytest.raises(ValueError) as e:
        send_mail_reminder(test_mail_info)
    assert str(e.value) == 'Cannot get email subject'

    # Test for ValueError when the 'body' key is missing
    missing_body_data = copy.deepcopy(test_mail_data)
    del missing_body_data['mail_body']
    mock_get_mail_data.return_value = missing_body_data
    with pytest.raises(ValueError) as e:
        send_mail_reminder(test_mail_info)
    assert str(e.value) == 'Cannot get email body'

    # Test for ValueError when mail sending fails
    mock_get_mail_data.return_value = copy.deepcopy(test_mail_data)
    mock_replace_characters.return_value = 'Replaced Body'
    mock_send_mail.return_value = False
    with pytest.raises(ValueError) as e:
        send_mail_reminder(test_mail_info)
    assert str(e.value) == 'Cannot send mail'

    # Test for successful mail sending
    mock_get_mail_data.return_value = copy.deepcopy(test_mail_data)
    mock_replace_characters.return_value = 'Replaced Body'
    mock_send_mail.return_value = True
    # TODO this should be deleted
    send_mail_reminder(test_mail_info)
    mock_send_mail.assert_called_with({
                    'mail_subject': 'Test Subject',
                    'mail_body': 'Replaced Body',
                    'mail_recipients': ['test@example.com', 'mail@example.com'],
                    'mail_cc': ['cc@example.com'],
                    'mail_bcc': ['bcc@example.com']
                })

# def send_mail_approval_done(mail_info):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_send_mail_approval_done -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@patch('weko_workflow.utils.replace_characters')
@patch('weko_workflow.utils.send_mail')
def test_send_mail_approval_done(mock_send_mail, mock_replace_characters):
    # Default test data
    test_mail_data = {
        'mail_subject': 'Test Subject',
        'mail_body': 'Test Body',
        'mail_recipients': ['test@example.com'],
        'mail_cc': ['cc@example.com'],
        'mail_bcc': ['bcc@example.com']
    }
    test_mail_info = {
        'register_user_mail': 'register@example.com'
    }

    # Test when the 'subject' key has no value
    empty_subject_data = test_mail_data.copy()
    empty_subject_data['mail_subject'] = ''
    with patch('weko_workflow.utils.email_pattern_approval_done',
               return_value=empty_subject_data):
        send_mail_approval_done(test_mail_info)
    mock_send_mail.assert_not_called()

    # Test when the 'body' key has no value
    empty_body_data = test_mail_data.copy()
    empty_body_data['mail_body'] = ''
    with patch('weko_workflow.utils.email_pattern_approval_done',
               return_value=empty_body_data):
        send_mail_approval_done(test_mail_info)
    mock_send_mail.assert_not_called()

    # Test when the 'subject' key is missing
    missing_subject_data = test_mail_data.copy()
    del missing_subject_data['mail_subject']
    with patch('weko_workflow.utils.email_pattern_approval_done',
               return_value=missing_subject_data):
        send_mail_approval_done(test_mail_info)
    mock_send_mail.assert_not_called()

    # Test when the 'body' key is missing
    missing_body_data = test_mail_data.copy()
    del missing_body_data['mail_body']
    with patch('weko_workflow.utils.email_pattern_approval_done',
               return_value=missing_body_data):
        send_mail_approval_done(test_mail_info)
    mock_send_mail.assert_not_called()

    # Test when mail sending succeeds
    mock_replace_characters.return_value = 'Replaced Body'
    with patch('weko_workflow.utils.email_pattern_approval_done',
               return_value=copy.deepcopy(test_mail_data)):
        send_mail_approval_done(test_mail_info)
        mock_send_mail.assert_called_with({
                        'mail_subject': 'Test Subject',
                        'mail_body': 'Replaced Body',
                        'mail_recipients': ['test@example.com', 'register@example.com'],
                        'mail_cc': ['cc@example.com'],
                        'mail_bcc': ['bcc@example.com']
                    })


# def send_mail_registration_done(mail_info):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_send_mail_registration_done -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@patch('weko_workflow.utils.get_mail_data')
@patch('weko_workflow.utils.replace_characters')
@patch('weko_workflow.utils.send_mail')
def test_send_mail_registration_done(
    mock_send_mail, mock_replace_characters, mock_get_mail_data
):
    # Default test data
    test_mail_data = {
        'mail_subject': 'Test Subject',
        'mail_body': 'Test Body',
        'mail_recipients': ['test@example.com'],
        'mail_cc': ['cc@example.com'],
        'mail_bcc': ['bcc@example.com']
    }
    test_mail_info = {
        'register_user_mail': 'register@example.com'
    }
    test_mail_id = 1

    # Test when the 'subject' key has no value
    empty_subject_data = test_mail_data.copy()
    empty_subject_data['mail_subject'] = ''
    mock_get_mail_data.return_value = empty_subject_data
    send_mail_registration_done(test_mail_info, test_mail_id)
    mock_send_mail.assert_not_called()

    # Test when the 'body' key has no value
    empty_body_data = test_mail_data.copy()
    empty_body_data['mail_body'] = ''
    mock_get_mail_data.return_value = empty_body_data
    send_mail_registration_done(test_mail_info, test_mail_id)
    mock_send_mail.assert_not_called()

    # Test when the 'subject' key is missing
    missing_subject_data = test_mail_data.copy()
    del missing_subject_data['mail_subject']
    mock_get_mail_data.return_value = missing_subject_data
    send_mail_registration_done(test_mail_info, test_mail_id)
    mock_send_mail.assert_not_called()

    # Test when the 'body' key is missing
    missing_body_data = test_mail_data.copy()
    del missing_body_data['mail_body']
    mock_get_mail_data.return_value = missing_body_data
    send_mail_registration_done(test_mail_info, test_mail_id)
    mock_send_mail.assert_not_called()

    # Test when mail sending succeeds
    mock_get_mail_data.return_value = copy.deepcopy(test_mail_data)
    mock_replace_characters.return_value = 'Replaced Body'
    send_mail_registration_done(test_mail_info, test_mail_id)
    mock_send_mail.assert_called_with({
                    'mail_subject': 'Test Subject',
                    'mail_body': 'Replaced Body',
                    'mail_recipients': ['test@example.com', 'register@example.com'],
                    'mail_cc': ['cc@example.com'],
                    'mail_bcc': ['bcc@example.com']
                })


# def send_mail_request_approval(mail_info):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_send_mail_request_approval -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@patch('weko_workflow.utils.replace_characters')
@patch('weko_workflow.utils.send_mail')
def test_send_mail_request_approval(mock_send_mail, mock_replace_characters):
    # Default test data
    test_mail_data = {
        'mail_subject': 'Test Subject',
        'mail_body': 'Test Body',
        'mail_recipients': ['test@example.com'],
        'mail_cc': ['cc@example.com'],
        'mail_bcc': ['bcc@example.com']
    }
    test_mail_info = {
        'next_step': 'approval_advisor',
        'advisor_mail_address': 'advisor@example.com',
        'guarantor_mail_address': 'guarantor@example.com'
    }

    # Sending email fails when 'mail_info' is empty
    send_mail_request_approval({})
    mock_send_mail.assert_not_called()

    # Test when the 'subject' key has no value
    empty_subject_data = test_mail_data.copy()
    empty_subject_data['mail_subject'] = ''
    with patch('weko_workflow.utils.email_pattern_request_approval',
               return_value=empty_subject_data):
        send_mail_request_approval(test_mail_info)
    mock_send_mail.assert_not_called()

    # Test when the 'body' key has no value
    empty_body_data = test_mail_data.copy()
    empty_body_data['mail_body'] = ''
    with patch('weko_workflow.utils.email_pattern_request_approval',
               return_value=empty_body_data):
        send_mail_request_approval(test_mail_info)
    mock_send_mail.assert_not_called()

    # Test when the 'subject' key is missing
    missing_subject_data = test_mail_data.copy()
    del missing_subject_data['mail_subject']
    with patch('weko_workflow.utils.email_pattern_request_approval',
               return_value=missing_subject_data):
        send_mail_request_approval(test_mail_info)
    mock_send_mail.assert_not_called()

    # Test when the 'body' key is missing
    missing_body_data = test_mail_data.copy()
    del missing_body_data['mail_body']
    with patch('weko_workflow.utils.email_pattern_request_approval',
               return_value=missing_body_data):
        send_mail_request_approval(test_mail_info)
    mock_send_mail.assert_not_called()

    # Test for successful mail sending when the next step is 'approval_advisor'
    mock_replace_characters.side_effect = ['Replaced Subject', 'Replaced Body']
    with patch('weko_workflow.utils.email_pattern_request_approval',
               return_value=copy.deepcopy(test_mail_data)):
        send_mail_request_approval(test_mail_info)
    mock_send_mail.assert_called_with({
                    'mail_subject': 'Replaced Subject',
                    'mail_body': 'Replaced Body',
                    'mail_recipients': ['test@example.com', 'advisor@example.com'],
                    'mail_cc': ['cc@example.com'],
                    'mail_bcc': ['bcc@example.com']
                })

    # Test for successful mail sending when the next step is 'approval_guarantor'
    test_mail_info['next_step'] = 'approval_guarantor'
    mock_replace_characters.side_effect = ['Replaced Subject', 'Replaced Body']
    with patch('weko_workflow.utils.email_pattern_request_approval',
               return_value=copy.deepcopy(test_mail_data)):
        send_mail_request_approval(test_mail_info)
    mock_send_mail.assert_called_with({
                    'mail_subject': 'Replaced Subject',
                    'mail_body': 'Replaced Body',
                    'mail_recipients': ['test@example.com', 'guarantor@example.com'],
                    'mail_cc': ['cc@example.com'],
                    'mail_bcc': ['bcc@example.com']
                })

    # Sending email fails when the 'next_step' is empty
    mock_send_mail.reset_mock()
    test_mail_info['next_step'] = ''
    mock_replace_characters.side_effect = ['Replaced Subject', 'Replaced Body']
    with patch('weko_workflow.utils.email_pattern_request_approval',
               return_value=copy.deepcopy(test_mail_data)):
        send_mail_request_approval(test_mail_info)
    mock_send_mail.assert_not_called()


# def send_mail(subject, recipient, body):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_send_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_send_mail():
    # Default test data
    test_mail_data = {
        'mail_subject': 'Test Subject',
        'mail_body': 'Test Body',
        'mail_recipients': ['test@example.com'],
        'mail_cc': ['cc@example.com'],
        'mail_bcc': ['bcc@example.com']
    }

    # Test for successful mail sending
    with patch('weko_workflow.utils.MailSettingView.send_statistic_mail', return_value=True) as mock_send_statistic_mail:
        assert send_mail(test_mail_data) == True
        mock_send_statistic_mail.assert_called_with({
            'subject': 'Test Subject',
            'recipients': ['test@example.com'],
            'cc': ['cc@example.com'],
            'bcc': ['bcc@example.com'],
            'body': 'Test Body'
        })

    # Test for unsuccessful mail sending
    with patch('weko_workflow.utils.MailSettingView.send_statistic_mail', return_value=True) as mock_send_statistic_mail:
        empty_mail_data = {}
        send_mail(empty_mail_data)
        mock_send_statistic_mail.assert_not_called()

# def email_pattern_registration_done(user_role, item_type_name):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_email_pattern_registration_done -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
#def test_email_pattern_registration_done(app,users,mocker):
#    mock_path = "weko_workflow.utils.get_mail_data"
#    with app.test_request_context():
#        config = current_app.config
#        login_user(users[2]["obj"])
#        from weko_items_ui.utils import get_current_user_role
#        role = get_current_user_role()
#
#        mocker_data = mocker.patch(mock_path)
#        subject, body = email_pattern_registration_done(role, "テストアイテムタイプ")
#        assert subject == None
#        assert body == None
#
#        config.update(
#            WEKO_ITEMS_UI_OUTPUT_REPORT="テストアイテムタイプ"
#        )
#        mocker_data = mocker.patch(mock_path)
#        email_pattern_registration_done(role, "テストアイテムタイプ")
#        mocker_data.assert_called_with(config["WEKO_WORKFLOW_RECEIVE_OUTPUT_REGISTRATION"])
#
#
#        config.update(
#            WEKO_ITEMS_UI_OUTPUT_REPORT="",
#            WEKO_ITEMS_UI_USAGE_REPORT = "テストアイテムタイプ"
#        )
#        mocker_data = mocker.patch(mock_path)
#        email_pattern_registration_done(role, "テストアイテムタイプ")
#        mocker_data.assert_called_with(config["WEKO_WORKFLOW_RECEIVE_USAGE_REPORT"])
#
#        config.update(
#            WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPES_LIST = ["テストアイテムタイプ"]
#        )
#        logout_user()
#        login_user(users[4]["obj"])
#        role = get_current_user_role()
#        config.update(
#            WEKO_ITEMS_UI_OUTPUT_REPORT="",
#        )
#        mocker_data = mocker.patch(mock_path)
#        email_pattern_registration_done(role, "テストアイテムタイプ")
#        mocker_data.assert_called_with(config["WEKO_WORKFLOW_RECEIVE_USAGE_APP_BESIDE"
#                                                "_PERFECTURE_AND_LOCATION_DATA_OF"
#                                                "_GENERAL_USER"])
#        config.update(
#            WEKO_ITEMS_UI_APPLICATION_FOR_PERFECTURES="テストアイテムタイプ",
#        )
#        mocker_data = mocker.patch(mock_path)
#        email_pattern_registration_done(role, "テストアイテムタイプ")
#        mocker_data.assert_called_with(config["WEKO_WORKFLOW_PERFECTURE_OR_LOCATION_DATA"
#                                                "_OF_GENERAL_USER"])
#
#        logout_user()
#        login_user(users[8]["obj"])
#        role = get_current_user_role()
#        config.update(
#            WEKO_ITEMS_UI_APPLICATION_FOR_PERFECTURES="",
#        )
#        mocker_data = mocker.patch(mock_path)
#        email_pattern_registration_done(role, "テストアイテムタイプ")
#        mocker_data.assert_called_with(config["WEKO_WORKFLOW_RECEIVE_USAGE_APP_BESIDE"
#                                                "_PERFECTURE_AND_LOCATION_DATA_OF_STUDENT_OR"
#                                                "_GRADUATED_STUDENT"])
#
#        config.update(
#            WEKO_ITEMS_UI_APPLICATION_FOR_PERFECTURES="テストアイテムタイプ",
#        )
#        mocker_data = mocker.patch(mock_path)
#        email_pattern_registration_done(role, "テストアイテムタイプ")
#        mocker_data.assert_called_with(config["WEKO_WORKFLOW_PERFECTURE_OR_LOCATION_DATA"
#                                   "_OF_STUDENT_OR_GRADUATED_STUDENT"])
#
#        logout_user()
#        login_user(users[2]["obj"])
#        role = get_current_user_role()
#        subject, body = email_pattern_registration_done(role, "テストアイテムタイプ")
#        assert subject == None
#        assert body == None


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
def test_get_mail_data(app, db_mail_templates, db_mail_template_users):
    mail_template, users, mail_template_users = db_mail_template_users
    valid_template_id = 1
    invalid_template_id = 0

    # Default data is returned if the template data is not found
    result = get_mail_data(invalid_template_id)
    assert result == {
        "mail_subject": "",
        "mail_body": "",
        "mail_recipients": [],
        "mail_cc": [],
        "mail_bcc": []
    }

    # All data is returned if the flag is True
    with patch.dict(
        app.config,
        {'INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED': True}
    ):
        result = get_mail_data(valid_template_id)
        assert result == {
            'mail_subject': 'Test Subject',
            'mail_body': 'Test Body',
            'mail_recipients': ['user1@example.com', 'user2@example.com'],
            'mail_cc': ['user1@example.com', 'user2@example.com'],
            'mail_bcc': ['user1@example.com', 'user2@example.com'],
        }

    # Only subject and body is returned if the flag is False
    with patch.dict(
        app.config,
        {'INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED': False}
    ):
        result = get_mail_data(valid_template_id)
        assert result == {
            'mail_subject': 'Test Subject',
            'mail_body': 'Test Body'
        }

    # Records are deleted if the related user is inactive or invalid
    with patch.dict(
        app.config,
        {'INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED': True}
    ):
        mtu = MailTemplateUsers()
        assert mtu.query.count() == 6
        users[0].active = False
        users[1].active = False
        result = get_mail_data(valid_template_id)
        assert result =={
            'mail_subject': 'Test Subject',
            'mail_body': 'Test Body',
            'mail_recipients': [],
            'mail_cc': [],
            'mail_bcc': [],
        }
        assert mtu.query.count() == 0

# def get_mail_data_tpl(file_name):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_mail_data_tpl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_mail_data_tpl(mocker):
    mock_file_path = mocker.patch('weko_workflow.utils.get_file_path', return_value='test_file_path')
    mock_subject = mocker.patch('weko_workflow.utils.get_subject_and_content', return_value=('subject', 'body'))
    subject, body = get_mail_data_tpl("test_file_name")
    assert subject == 'subject'
    assert body == 'body'
    mock_file_path.assert_called_once_with("test_file_name")
    mock_subject.assert_called_once_with('test_file_path')

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
    context = "url is [10]. restricted_fullname is [restricted_fullname]. restricted_research_plan = [restricted_research_plan]"
    data = {
        "url":"https://test_url.com",
        "restricted_fullname":"test_file.txt",
        "restricted_research_plan":"restricted_research_plan"
    }
    test = "url is https://test_url.com. restricted_fullname is test_file.txt. restricted_research_plan = restricted_research_plan"

    result = replace_characters(data,context)
    assert result == test
# def get_register_info(activity_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_register_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_register_info(app, db, db_register_full_action,users,mocker):
    with app.test_request_context():
        login_user(users[2]["obj"])
        activity_id = db_register_full_action["activities"][1].activity_id
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

    result = get_item_info(0)
    assert result == {}

    with patch("weko_workflow.utils.ItemsMetadata.get_record",side_effect=Exception("test error")):
        result = get_item_info(db_records[0][3].id)
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
def test_set_mail_info(app, db_register_full_action, mocker, db_records, db):
    config = current_app.config
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
        "subitem_advisor_university/institution":"test advisor university",
        "subitem_guarantor_university/institution":"test guarantor university",
        "subitem_restricted_access_research_title":"test_restricted_research_title",
        "subitem_restricted_access_dataset_usage":"test_restricted_dataset",
        "subitem_restricted_access_application_date":"test_restricted_date",
        "subitem_restricted_access_research_plan":"restricted_research_plan"
    }

    activity_id = db_register_full_action["activities"][0].activity_id

    test = {
        "university_institution":"test_institution",
        "fullname":"test_fullname",
        "activity_id":activity_id,
        "mail_address":"test@test.org",
        "dataset_requested":"test_dataset",
        "register_date":"",
        "advisor_fullname":"test advisor",
        "guarantor_fullname":"test guarantor",
        "url":"http://TEST_SERVER.localdomain/",
        "advisor_university_institution":"test advisor university",
        "guarantor_university_institution":"test guarantor university",
        "advisor_mail_address":"advisor@test.org",
        "guarantor_mail_address":"guarantor@test.org",
        "register_user_mail":"",
        "report_number":activity_id,
        "output_report_activity_id":activity_id,
        "output_report_title":"test_sub_title",
        "restricted_fullname":"test_fullname",
        'restricted_university_institution':"test_institution",
        "restricted_activity_id":activity_id,
        "restricted_research_title":"test_restricted_research_title",
        "restricted_data_name":"test_restricted_dataset",
        "restricted_application_date":"test_restricted_date",
        "restricted_mail_address":"test@test.org",
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_approver_name":"",
        "restricted_approver_affiliation":"",
        "restricted_site_name_ja":"name_ja",
        "restricted_site_name_en":"name_en",
        "restricted_institution_name_ja":config["THEME_INSTITUTION_NAME"]["ja"],
        "restricted_institution_name_en":config["THEME_INSTITUTION_NAME"]["en"],
        "restricted_site_mail":"default_sender",
        "restricted_site_url":"https://localhost",
        "mail_recipient":"test@test.org",
        "restricted_supervisor":"",
        "restricted_reference":"",
        "restricted_usage_activity_id":activity_id,
        "landing_url": '',
        "restricted_research_plan":"restricted_research_plan"
    }
    with app.test_request_context():
        result = set_mail_info(item_info,db_register_full_action["activities"][0],True)
        assert result == test

    test = {
        "university_institution":"test_institution",
        "fullname":"test_fullname",
        "activity_id":activity_id,
        "mail_address":"test@test.org",
        "dataset_requested":"test_dataset",
        "register_date":"2022-10-10",
        "advisor_fullname":"test advisor",
        "guarantor_fullname":"test guarantor",
        "url":"http://TEST_SERVER.localdomain/",
        "advisor_university_institution":"test advisor university",
        "guarantor_university_institution":"test guarantor university",
        "advisor_mail_address":"advisor@test.org",
        "guarantor_mail_address":"guarantor@test.org",
        "register_user_mail":"user@test.org",
        "report_number":activity_id,
        "output_report_activity_id":activity_id,
        "output_report_title":"test_sub_title",
        "restricted_fullname":"test_fullname",
        'restricted_university_institution':"test_institution",
        "restricted_activity_id":activity_id,
        "restricted_research_title":"test_restricted_research_title",
        "restricted_data_name":"test_restricted_dataset",
        "restricted_application_date":"test_restricted_date",
        "restricted_mail_address":"test@test.org",
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_approver_name":"",
        "restricted_approver_affiliation":"",
        "restricted_site_name_ja":"name_ja",
        "restricted_site_name_en":"name_en",
        "restricted_institution_name_ja":config["THEME_INSTITUTION_NAME"]["ja"],
        "restricted_institution_name_en":config["THEME_INSTITUTION_NAME"]["en"],
        "restricted_site_mail":"default_sender",
        "restricted_site_url":"https://localhost",
        "mail_recipient":"test@test.org",
        "restricted_supervisor":"",
        "restricted_reference":"",
        "restricted_usage_activity_id":activity_id,
        "landing_url": '',
        "restricted_research_plan":"restricted_research_plan"
    }
    with app.test_request_context():
        result = set_mail_info(item_info,db_register_full_action["activities"][0],False)
        assert result == test

    with app.test_request_context():
       record = WekoRecord.get_record(db_records[0][2].id)
       with patch("weko_workflow.utils.WekoRecord.get_record_by_pid", return_value = record):
           with patch("weko_workflow.utils.url_for", return_value = 'records/1'):
                result = set_mail_info(item_info,db_register_full_action["activities"][9],False)
                assert result["landing_url"] != ""

    with app.test_request_context():
        record = WekoRecord.get_record(db_records[0][2].id)
        with patch("weko_workflow.utils.WekoRecord.get_record_by_pid", return_value = record):
            with patch("weko_workflow.utils.url_for", return_value = 'records/1'):
                with patch("weko_workflow.utils.WekoRecord.get_file_data", return_value = [{"filename":"aaa.txt"}]):
                    with patch("weko_workflow.utils.extract_term_description", return_value=("","")):
                        result = set_mail_info(item_info,db_register_full_action["activities"][10],False)
                        assert result["terms_of_use_jp"] == ""
                        assert result["terms_of_use_en"] == ""

    with app.test_request_context():
        record = WekoRecord.get_record(db_records[0][2].id)
        with patch("weko_workflow.utils.WekoRecord.get_record_by_pid", return_value = record):
            with patch("weko_workflow.utils.WekoRecord.get_file_data", return_value = [{"filename":"recid/15"}]):
                with patch("weko_workflow.utils.extract_term_description", return_value=("","")):
                    item_id_1 = uuid.uuid4()
                    item_application_1 = ItemApplication(id = 1, item_id = item_id_1, item_application = {"workflow":"1", "terms":"term_free", "termsDescription":"利用規約自由入力"})
                    with db.session.begin_nested():
                        db.session.add(item_application_1)
                    db.session.commit()
                    db_register_full_action["activities"][10].extra_info = {"file_name":"recid/15"}
                    persistent_identifier = PersistentIdentifier(
                        pid_type="recid",
                        pid_value=item_id_1,
                        pid_provider="weko",
                        status="R",
                        object_type="item",
                        object_uuid=uuid.uuid4(),
                    )
                    mocker.patch("weko_workflow.utils.PersistentIdentifier.get", return_value = persistent_identifier)
                    result = set_mail_info(item_info,db_register_full_action["activities"][10],False)
                    assert result["terms_of_use_jp"] == ""
                    assert result["terms_of_use_en"] == ""

    with app.test_request_context():
        record = WekoRecord.get_record(db_records[0][2].id)
        with patch("weko_workflow.utils.WekoRecord.get_record_by_pid", return_value = record):
            with patch("weko_workflow.utils.url_for", return_value = 'records/1'):
                with patch("weko_workflow.utils.extract_term_description", return_value=("test_terms_ja","test_terms_en")):
                    result = set_mail_info(item_info,db_register_full_action["activities"][11],False)

    with app.test_request_context():
        record = WekoRecord.get_record(db_records[0][2].id)
        with patch("weko_workflow.utils.WekoRecord.get_record_by_pid", return_value = ""):
            # with patch("weko_workflow.utils.url_for", return_value = 'records/1'):
                with patch("weko_workflow.utils.WekoRecord.get_file_data", return_value = [{"filename":"aaa.txt"}]):
                    with patch("weko_workflow.utils.extract_term_description", return_value=("","")):
                        result = set_mail_info(item_info,db_register_full_action["activities"][10],False)

class MockDict():
    def __init__(self, data):
        for key in data:
            setattr(self, key, data[key])


# def extract_term_description(file_info):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_extract_term_description -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_extract_term_description(db):

    #testNo.15(W2023-22 2)
    file_info = {"terms": "term_free", "termsDescription": "test_terms"}
    test = ('', 'test_terms')
    result = extract_term_description(file_info)
    assert result == test

    #testNo.16(W2023-22 2)
    restricted_access_setting = {
    "secret_URL_file_download": {
        "secret_expiration_date": 30,
        "secret_expiration_date_unlimited_chk": False,
        "secret_download_limit": 10,
        "secret_download_limit_unlimited_chk": False,
    },
    "content_file_download": {
        "expiration_date": 30,
        "expiration_date_unlimited_chk": False,
        "download_limit": 10,
        "download_limit_unlimited_chk": False,
    },
    "usage_report_workflow_access": {
        "expiration_date_access": 500,
        "expiration_date_access_unlimited_chk": False,
    },
    "terms_and_conditions": [{"key": 1, "content": {"en": {"title": "TERMS OF USE", "content": "TERMS OF USE"}, "ja": {"title": "利用規約", "content": "利用規約"}}, "existed": True}]
    }

    restricted_access_setting2 = {
    "secret_URL_file_download": {
        "secret_expiration_date": 30,
        "secret_expiration_date_unlimited_chk": False,
        "secret_download_limit": 10,
        "secret_download_limit_unlimited_chk": False,
    },
    "content_file_download": {
        "expiration_date": 30,
        "expiration_date_unlimited_chk": False,
        "download_limit": 10,
        "download_limit_unlimited_chk": False,
    },
    "usage_report_workflow_access": {
        "expiration_date_access": 500,
        "expiration_date_access_unlimited_chk": False,
    },}

    file_info = {"terms": 1}
    test = "利用規約", "TERMS OF USE"
    mock_adminsettings = MockDict(restricted_access_setting)
    with patch("weko_workflow.utils.AdminSettings.get", return_value = mock_adminsettings):
        assert extract_term_description(file_info) == test

    #testNo.17(W2023-22 2)
    file_info = {}
    test = "", ""
    result = extract_term_description(file_info)
    assert result == test

    #testNo.18(W2023-22 2)
    file_info = {"terms": 1}
    test = "", ""
    with patch("weko_workflow.utils.AdminSettings.get", return_value = ""):
        assert extract_term_description(file_info) == test

    #testNo.19(W2023-22 2)
    file_info = {"terms": 2}
    test = "", ""
    with patch("weko_workflow.utils.AdminSettings.get", return_value = mock_adminsettings):
        assert extract_term_description(file_info) == test

# def process_send_reminder_mail(activity_detail, mail_template):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_process_send_reminder_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_process_send_reminder_mail(db, db_register_full_action, mocker):
    mocker.patch("weko_workflow.utils.get_item_info",return_value={})
    mocker.patch("weko_workflow.utils.set_mail_info",return_value={})
    mock_sender = mocker.patch("weko_workflow.utils.send_mail_reminder")
    process_send_reminder_mail(db_register_full_action["activities"][1], "template")
    mock_sender.assert_called_with({"mail_address":"comadmin@test.org","mail_id":"template"})

    user_profile = UserProfile(
        user_id=db_register_full_action["activities"][1].activity_login_user,
        _username="sysadmin",
        fullname="sysadmin user",
        timezone="asia",
        language="japanese",
    )
    db.session.add(user_profile)
    db.session.commit()
    mock_sender = mocker.patch("weko_workflow.utils.send_mail_reminder")
    process_send_reminder_mail(db_register_full_action["activities"][1],"template")
    mock_sender.assert_called_with({"mail_address":"comadmin@test.org","mail_id":"template","fullname":"sysadmin user"})

    with patch("weko_items_ui.utils.get_user_information",return_value=[{"email":""}]):
        with pytest.raises(ValueError) as e:
            process_send_reminder_mail(db_register_full_action["activities"][1],"template")
            assert str(e.value) == "Cannot get receiver mail address"

    with patch("weko_items_ui.utils.get_user_information",return_value=[{"email":"test@test.org","fullname":""}]):
        with patch("weko_workflow.utils.send_mail_reminder",side_effect=ValueError("test error")):
            with pytest.raises(ValueError) as e:
                process_send_reminder_mail(db_register_full_action["activities"][1],"template")
                assert str(e.value) == "test error"

# def process_send_reminder_mail(activity_detail, mail_template):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_process_send_reminder_mail_1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_process_send_reminder_mail_1(db, db_register_full_action, mocker):
    # 例外が発生しないことを確認する。
    mocker.patch("weko_workflow.utils.get_item_info",return_value={})
    mocker.patch("weko_workflow.utils.set_mail_info",return_value={})
    mock_sender = mocker.patch("weko_workflow.utils.send_mail_reminder")
    process_send_reminder_mail(db_register_full_action["activities"][6],"template")
    mock_sender.assert_called_with({"mail_address":"originalroleuser@test.org","mail_id":"template"})


# def process_send_notification_mail(
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_process_send_notification_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_process_send_notification_mail(db,db_register, mocker, users):
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
    action_mails_setting = {
        'previous': {
            'inform_itemReg': {
                'mail': 'test_mail'
            }
        },
        'next': {},
        'approval': False,
        'reject': False
    }

    with patch('weko_workflow.utils._check_mail_setting', return_value=True):
        process_send_notification_mail(activity,"item_login","next_step", action_mails_setting)
        mock_send_registration.assert_called_with(data, 'test_mail')

    login_user(users[2]["obj"])
    data = {
        "item_type_name":"テストアイテムタイプ",
        "next_step":"approval_",
        "approval_date":"2022-10-10",
        "approval_date_after_7_days": "2022-10-17",
        "31_march_corresponding_year": "2023-03-31"
    }
    process_send_notification_mail(activity,"item_registration","approval_", action_mails_setting)
    mock_send_approval_req.assert_called_with(data)
    data = {
        "item_type_name":"テストアイテムタイプ",
        "next_step":"next_step",
        "approval_date":"2022-10-10",
        "approval_date_after_7_days": "2022-10-17",
        "31_march_corresponding_year": "2023-03-31"
    }
    process_send_notification_mail(activity,"approval_administrator","next_step", action_mails_setting)
    mock_send_approval_done.assert_called_with(data)
    process_send_notification_mail(activity,"other_step","next_step", action_mails_setting)
# def get_application_and_approved_date(activities, columns):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_application_and_approval_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_application_and_approval_date(db,db_register_full_action,users):
    activities = db_register_full_action["activities"]
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
def test_get_workflow_item_type_names(db_register_full_action):
    activities = db_register_full_action["activities"]
    get_workflow_item_type_names(activities)

# def create_usage_report(activity_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_create_usage_report -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_create_usage_report(app,db_register_full_action, mocker):
    activity = db_register_full_action["activities"][1]
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
        activity.item_id,activity.activity_id,db_register_full_action["workflow"],None
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
        item_ = {'id': '1.1', 'pid': {'type': 'depid', 'value': '1.1', 'revision_id': 0}, 'lang': 'ja', 'owner': 1, 'title': 'related_title - ja_usage_title - 2 - ', 'owners': [1], 'status': 'published', '$schema': 'items/jsonschema/1', 'pubdate': '2022-08-20', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}, 'shared_user_ids': [], 'item_1617186331708': [{'subitem_1551255647225': 'ff', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}}
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
def test_modify_item_metadata(app,db,db_register_full_action,users,mocker):
    activity = db_register_full_action["activities"][1]
    item_id = activity.item_id
    item = ItemsMetadata.get_record(id_=item_id).dumps()
    workflow = db_register_full_action["workflow"]
    item_type_id = workflow.itemtype_id
    activity_id = activity.activity_id
    data_dict={'subitem_1551255647225': 'title', 'subitem_1551255648112': 'ja', 'subitem_identifier_reg_text': 'test_2/0000000001', 'subitem_identifier_reg_type': 'JaLC'}
    schema = ItemTypes.get_by_id(item_type_id).schema
    owner_id = users[2]["id"]
    related_title = "related_title"

    user_profile = UserProfile(
        user_id=db_register_full_action["activities"][1].activity_login_user,
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

    test = {'id': '1.1', 'pid': {'type': 'depid', 'value': '1.1', 'revision_id': 0}, 'lang': 'ja', 'owner': 1, 'title': 'related_title - ja_usage_title - 2 - ', 'owners': [1], 'status': 'published', '$schema': 'items/jsonschema/1', 'pubdate': '2022-08-20', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}, 'shared_user_ids': [], 'item_1617186331708': [{'subitem_1551255647225': 'ff', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}}
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
def test_update_activity_action(app,users,db_register_full_action):
    update_activity_action("1",1)

    current_app.config.update(
        WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION_USAGE_APPLICATION = "Start"
    )
    activity = db_register_full_action["activities"][1]
    update_activity_action(activity.activity_id,1)
    activity_action = WorkActivity().get_activity_action_comment(
        activity_id=activity.activity_id,
        action_id=1,
        action_order=1)
    assert activity_action.action_status == "M"
# def check_continue(response, activity_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_check_continue -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_continue(app,db_register_full_action):
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
    result = check_continue(response,db_register_full_action["activities"][4].activity_id)
    assert result == test
    test = {
        "check_handle":1,
        "check_continue":0
    }
    result = check_continue(response,db_register_full_action["activities"][5].activity_id)
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
        "shared_user_ids":[{"user":1}],
        "approval1":"test1@test.org",
        "approval2":"test2@test.org"
    }
    mock_update = mocker.patch("weko_workflow.utils.WorkActivity.update_activity")
    save_activity_data(data)
    mock_update.assert_called_with("test_id",{"shared_user_ids":[{"user":1}],"approval1":"test1@test.org","approval2":"test2@test.org"})

# def save_activity_data(data: dict) -> NoReturn:
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_save_activity_data_1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_save_activity_data_1(db_register_full_action, mocker):
    mock_update = mocker.patch("weko_workflow.utils.WorkActivity.update_activity")
    data = {
        "activity_id":db_register_full_action['activities'][0].activity_id,
        "shared_user_ids":[],
        "approval1":"test1@test.org",
        "approval2":"test2@test.org"
    }
    save_activity_data(data)
    assert db_register_full_action['activities'][0].shared_user_ids == '[]'
    # テストデータの元からshared_user_idsは[]だったので戻す必要なし

# def save_activity_data(data: dict) -> NoReturn:
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_save_activity_data_2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_save_activity_data_2(db_register_full_action, mocker):
    data = {
        "activity_id":db_register_full_action['activities'][0].activity_id,
        "shared_user_ids":[{"user":3}],
        "approval1":"test1@test.org",
        "approval2":"test2@test.org"
    }
    save_activity_data(data)
    assert db_register_full_action['activities'][0].shared_user_ids == [{"user":3}]
    # テストデータをもとに戻す
    db_register_full_action['activities'][0].shared_user_ids = []

# def send_mail_url_guest_user(mail_info: dict) -> bool:
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_send_mail_url_guest_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@patch('weko_workflow.utils.get_mail_data')
@patch('weko_workflow.utils.replace_characters')
@patch('weko_workflow.utils.send_mail')
def test_send_mail_url_guest_user(
    mock_send_mail, mock_replace_characters, mock_get_mail_data
):
    test_mail_data = {
        'mail_subject': 'Test Subject',
        'mail_body': 'Test Body',
        'mail_recipients': ['test@example.com'],
        'mail_cc': ['cc@example.com'],
        'mail_bcc': ['bcc@example.com']
    }
    test_mail_info = {
        'mail_address': 'mail@example.com'
    }

    # Test when the 'subject' key has no value
    empty_subject_data = test_mail_data.copy()
    empty_subject_data['mail_subject'] = ''
    mock_get_mail_data.return_value = empty_subject_data
    result = send_mail_url_guest_user(test_mail_info)
    assert result == False

    # Test when the 'body' key has no value
    empty_body_data = test_mail_data.copy()
    empty_body_data['mail_body'] = ''
    mock_get_mail_data.return_value = empty_body_data
    result = send_mail_url_guest_user(test_mail_info)
    assert result == False

    # Test when the 'subject' key is missing
    missing_subject_data = test_mail_data.copy()
    del missing_subject_data['mail_subject']
    mock_get_mail_data.return_value = missing_subject_data
    result = send_mail_url_guest_user(test_mail_info)
    assert result == False

    # Test when the 'body' key is missing
    missing_body_data = test_mail_data.copy()
    del missing_body_data['mail_body']
    mock_get_mail_data.return_value = missing_body_data
    result = send_mail_url_guest_user(test_mail_info)
    assert result == False

    # Test when mail sending fails
    mock_get_mail_data.return_value = copy.deepcopy(test_mail_data)
    mock_replace_characters.return_value = 'Replaced Body'
    mock_send_mail.return_value = False
    result = send_mail_url_guest_user(test_mail_info)
    assert result == False

    # Test when mail sending succeeds
    mock_get_mail_data.return_value = copy.deepcopy(test_mail_data)
    mock_replace_characters.return_value = 'Replaced Body'
    mock_send_mail.return_value = True
    result = send_mail_url_guest_user(test_mail_info)
    assert result == True
    mock_send_mail.assert_called_with({
                    'mail_subject': 'Test Subject',
                    'mail_body': 'Replaced Body',
                    'mail_recipients': ['test@example.com', 'mail@example.com'],
                    'mail_cc': ['cc@example.com'],
                    'mail_bcc': ['bcc@example.com']
                })

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
def test_init_activity_for_guest_user(app,db_register_full_action,mocker):
    with app.test_request_context():
        record_id = uuid.uuid4()
        data = {
            "workflow_id":db_register_full_action["workflow"].id,
            "flow_id":db_register_full_action["flow_define"].id,
            "extra_info":{
                "guest_mail":"guest@test.org",
                "file_name":"test.txt",
                "record_id":str(record_id)
            }
        }
        new_activit_id="A-20221003-00001"
        mocker.patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value=new_activit_id)
        mocker.patch("weko_workflow.utils.generate_guest_activity_token_value",return_value="QS0yMDIyMTAwMy0wMDAwMSAyMDIyLTEwLTAxIGd1ZXN0QHRlc3Qub3JnIENFMDZGREZCMTU4MjNBNUM=")
        activity, tmp_url = init_activity_for_guest_user(data,True)
        assert activity.activity_id == new_activit_id
        assert tmp_url == "http://TEST_SERVER.localdomain/workflow/activity/guest-user/test.txt?token=QS0yMDIyMTAwMy0wMDAwMSAyMDIyLTEwLTAxIGd1ZXN0QHRlc3Qub3JnIENFMDZGREZCMTU4MjNBNUM="
        _ , tmp_url = init_activity_for_guest_user(data,True)
        assert tmp_url == "http://TEST_SERVER.localdomain/workflow/activity/guest-user/test.txt?token=QS0yMDIyMTAwMy0wMDAwMSAyMDIyLTEwLTAxIGd1ZXN0QHRlc3Qub3JnIENFMDZGREZCMTU4MjNBNUM="


# def send_usage_application_mail_for_guest_user(guest_mail: str, temp_url: str):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_send_usage_application_mail_for_guest_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('order_if', [1,2])
def test_send_usage_application_mail_for_guest_user(app, db_register, mocker, records_restricted, db_records, db, order_if):
    mail_config = MailConfig(mail_default_sender="test_sender")
    db.session.add(mail_config)
    db.session.commit()
    mail = "guest@test.org"
    url = "https://test.com"
    mock_sender = mocker.patch("weko_workflow.utils.send_mail_url_guest_user")
    data = {"records_id":100, "file_name":"check_2022-03-10.tsv"}
    record = WekoRecord.get_record(db_records[0][2].id)
    if order_if==1:
        with patch("weko_workflow.utils.WekoRecord.get_record_by_pid", return_value = record):
            send_usage_application_mail_for_guest_user(mail, url, data)
        mock_sender.assert_called_with(
            {
                "mail_address":mail,
                "url_guest_user":url,
                "mail_id": '1',
                "restricted_institution_name_en": "",
                "restricted_institution_name_ja": "",
                "restricted_site_name_ja": "",
                "restricted_site_name_en": "",
                'terms_of_use_jp': '',
                'terms_of_use_en': '',
                "restricted_site_mail": "test_sender",
                "restricted_site_url": "https://localhost"
            }
        )

    if order_if==2:
        data = {"records_id":100, "file_name":"recid/15.0"}
        with patch("weko_workflow.utils.WekoRecord.get_record_by_pid", return_value = record):
            item_id_1 = uuid.uuid4()
            item_application_1 = ItemApplication(id = 1, item_id = item_id_1, item_application = {"workflow":"1", "terms":"term_free", "termsDescription":"利用規約自由入力"})
            with db.session.begin_nested():
                db.session.add(item_application_1)
            db.session.commit()
            class mockuuid:
                object_uuid = item_id_1
            with patch("weko_workflow.utils.PersistentIdentifier.get", return_value = mockuuid()):
                send_usage_application_mail_for_guest_user(mail, url, data)
        mock_sender.assert_called_with(
            {
                "mail_address":mail,
                "url_guest_user":url,
                "mail_id": '1',
                "restricted_institution_name_en": "",
                "restricted_institution_name_ja": "",
                "restricted_site_name_ja": "",
                "restricted_site_name_en": "",
                'terms_of_use_jp': '',
                'terms_of_use_en': '利用規約自由入力',
                "restricted_site_mail": "test_sender",
                "restricted_site_url": "https://localhost"
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
    assert result == None

    result = delete_guest_activity("not exist activity")
    assert result == False


# def get_activity_display_info(activity_id: str):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_activity_display_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_activity_display_info(app,db, users, db_register_full_action, mocker):
    with app.test_request_context():
        activity = db_register_full_action["activities"][1]
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
            {"ActivityId":activity_id,"ActionId":1,"ActionName":"Start","ActionVersion":"1.0.0","ActionEndpoint":"begin_action", "Author":"contributor@test.org", "Status":"action_doing", "ActionOrder":1},
            {"ActivityId":activity_id,"ActionId":3,"ActionName":"Item Registration","ActionVersion":"1.0.0","ActionEndpoint":"item_login", "Author":"contributor@test.org", "Status":"action_doing","ActionOrder":1},
            {"ActivityId":activity_id,"ActionId":3,"ActionName":"Item Registration","ActionVersion":"1.0.0","ActionEndpoint":"item_login", "Author":"", "Status":" ","ActionOrder":2},
            {"ActivityId":activity_id,"ActionId":5,"ActionName":"Item Link","ActionVersion":"1.0.0","ActionEndpoint":"item_link", "Author":"", "Status":" ","ActionOrder":3}
        ]
        endpoint, action_id, activity_detail, cur_action, histories, item, steps, temporary_comment, workflow_detail, owner_id, shared_user_ids = get_activity_display_info(activity_id)
        assert endpoint == "begin_action"
        assert action_id == 1
        assert activity_detail == activity
        assert cur_action == activity.action
        assert histories == [db_history1]
        assert item == ItemsMetadata.get_record(id_=activity.item_id)
        assert steps == test_steps
        assert temporary_comment == None
        assert workflow_detail == db_register_full_action["workflow"]

        mocker.patch("weko_workflow.utils.ItemsMetadata.get_record",side_effect=NoResultFound)
        activity.activity_status="C"
        db.session.merge(activity)
        db.session.commit()
        mocker.patch("weko_workflow.utils.WorkActivity.get_activity_action_comment",return_value=None)
        endpoint, action_id, activity_detail, cur_action, histories, item, steps, temporary_comment, workflow_detail, owner_id, shared_user_ids = get_activity_display_info(activity_id)
        assert endpoint == "begin_action"
        assert action_id == 1
        assert activity_detail == activity
        assert cur_action == activity.action
        assert histories == [db_history1]
        assert item == None
        assert steps == test_steps
        assert temporary_comment == ""
        assert workflow_detail == db_register_full_action["workflow"]

        # if activity_detail and activity_detail.item_id = FALSE
        sutab_get_activity_detail = WorkActivity().get_activity_detail(activity_id)
        sutab_get_activity_detail.item_id = None
        with patch("weko_workflow.api.WorkActivity.get_activity_detail", return_value=sutab_get_activity_detail):
            endpoint, action_id, activity_detail, cur_action, histories, item, steps, temporary_comment, workflow_detail, owner_id, shared_user_ids = get_activity_display_info(activity_id)
            assert item is None

        # if metadata: == True
        import json
        target_activity = Activity.query.filter_by(activity_id=activity_id).first()
        target_activity.temp_data = json.dumps({"metainfo":{"owner": 2, "shared_user_ids":[{"user": -1}, {"user": 1}]}})
        db.session.merge(activity)
        db.session.commit()
        endpoint, action_id, activity_detail, cur_action, histories, item, steps, temporary_comment, workflow_detail, owner_id, shared_user_ids = get_activity_display_info(activity_id)
        assert owner_id == 2
        assert shared_user_ids == [{"user": -1}, {"user": 1}]

# def __init_activity_detail_data_for_guest(activity_id: str, community_id: str):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test___init_activity_detail_data_for_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test___init_activity_detail_data_for_guest(app, db, users, db_register_full_action, mocker):
    with app.test_request_context():

        activity = db_register_full_action["activities"][1]
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
            {"ActivityId":activity_id,"ActionId":1,"ActionName":"Start","ActionVersion":"1.0.0","ActionEndpoint":"begin_action", "Author":"contributor@test.org", "Status":"action_doing", "ActionOrder":1},
            {"ActivityId":activity_id,"ActionId":3,"ActionName":"Item Registration","ActionVersion":"1.0.0","ActionEndpoint":"item_login", "Author":"contributor@test.org", "Status":"action_doing","ActionOrder":1},
            {"ActivityId":activity_id,"ActionId":3,"ActionName":"Item Registration","ActionVersion":"1.0.0","ActionEndpoint":"item_login", "Author":"", "Status":" ","ActionOrder":2},
            {"ActivityId":activity_id,"ActionId":5,"ActionName":"Item Link","ActionVersion":"1.0.0","ActionEndpoint":"item_link", "Author":"", "Status":" ","ActionOrder":3}
        ]
        action_endpoint = "begin_action"
        action_id=1
        activity_detail=activity
        cur_action=activity.action
        histories=[db_history1]
        item=ItemsMetadata.get_record(id_=activity.item_id)
        steps=test_steps,
        temporary_comment=None
        workflow_detail=db_register_full_action["workflow"]
        owner_id = 1
        shared_user_ids = []
        display_info = (action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)
        mocker.patch("weko_workflow.utils.get_activity_display_info",return_value=display_info)
        mocker.patch("weko_workflow.utils.get_approval_keys",return_value=[])
        community_id=""
        session['user_id'] = '1'
        session["guest_email"] = "guest@test.org"
        user_profile = {
            "results":{
                'subitem_user_name': "",
                'subitem_fullname': "",
                'subitem_mail_address': "guest@test.org",
                'subitem_displayname': "",
                'subitem_university/institution': '',
                'subitem_affiliated_division/department': '',
                'subitem_position': '',
                'subitem_phone_number': '',
                'subitem_position(others)': '',
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
            list_license=get_list_licence(),
            cur_action=cur_action,
            activity_id=activity_detail.activity_id,
            is_enable_item_name_link=True,
            enable_feedback_maillist=current_app.config[
                'WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL'],
            enable_contributor=current_app.config[
                'WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'],
            out_put_report_title={'en': 'Output Registration', 'ja': '成果物'},
            action_endpoint_key={},
            approval_email_key=[],
            step_item_login_url="weko_items_ui/iframe/item_edit.html",
            need_file=True,
            need_billing_file=False,
            records={'id': '1.1', 'pid': {'type': 'depid', 'value': '1.1', 'revision_id': 0}, 'lang': 'ja', 'owner': 1, 'title': 'title', 'owners': [1], 'status': 'published', '$schema': '/items/jsonschema/15', 'pubdate': '2022-08-20', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}, 'shared_user_ids': [], 'item_1617186331708': [{'subitem_1551255647225': 'ff', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}},
            record=[],
            jsonschema="/items/jsonschema/1",
            schemaform="/items/schemaform/1",
            item_save_uri="/items/iframe/model/save",
            files=[],
            endpoints={},
            need_thumbnail=False,
            files_thumbnail=[],
            allow_multi_thumbnail=False,
            id=db_register_full_action["workflow"].itemtype_id,
            owner_id = owner_id,
            shared_user_ids=shared_user_ids,
        )

        result = __init_activity_detail_data_for_guest(activity_id,community_id)
        assert test == result

        test_item_login_data = (
            "weko_items_ui/iframe/item_edit.html",
            True,
            False,
            item,
            "/items/jsonschema/1",
            "/items/schemaform/1",
            "/items/iframe/model/save",
            [],
            {},
            False,
            [],
            False,
            {"researchmap" : False}
        )
        mocker.patch("weko_items_ui.api.item_login",return_value=test_item_login_data)
        result = __init_activity_detail_data_for_guest(activity_id,community_id)
        assert result == test

# def prepare_data_for_guest_activity(activity_id: str) -> dict:
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_data_for_guest_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_prepare_data_for_guest_activity(app,db,users,db_register_full_action,mocker):
    with app.test_request_context():
        mocker.patch("weko_workflow.utils.__init_activity_detail_data_for_guest",return_value={})
        request_mock = mocker.patch.object(flask, "request")
        request_mock.method.return_value="GET"
        request_mock.form.return_value={"checked":True}
        activity = db_register_full_action["activities"][1]
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

        user_profile = {
            "results":{
                'subitem_user_name': "",
                'subitem_fullname': "",
                'subitem_mail_address': "guest@test.org",
                'subitem_displayname': "",
                'subitem_university/institution': '',
                'subitem_affiliated_division/department': '',
                'subitem_position': '',
                'subitem_phone_number': '',
                'subitem_position(others)': '',
                'subitem_affiliated_institution': [],
            }
        }

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
                workflow_detail=db_register_full_action["workflow"],
                user_profile=user_profile,
                list_license=get_list_licence(),
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
                records={'id': '1.1', 'pid': {'type': 'depid', 'value': '1.1', 'revision_id': 0}, 'lang': 'ja', 'owner': 1, 'title': 'title', 'owners': [1], 'status': 'published', '$schema': '/items/jsonschema/15', 'pubdate': '2022-08-20', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}, 'shared_user_ids': [], 'item_1617186331708': [{'subitem_1551255647225': 'ff', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}},
                record=[],
                jsonschema="/items/jsonschema/1",
                schemaform="/items/schemaform/1",
                item_save_uri="/items/iframe/model/save",
                files=[],
                endpoints={},
                need_thumbnail=False,
                files_thumbnail=[],
                allow_multi_thumbnail=False,
                id=db_register_full_action["workflow"].itemtype_id,
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
@patch('weko_workflow.utils.get_mail_data')
@patch('weko_workflow.utils.replace_characters')
@patch('weko_workflow.utils.send_mail')
def test_process_send_mail(
    mock_send_mail, mock_replace_characters, mock_get_mail_data, client
):
    # Default test data
    test_mail_data = {
        'mail_subject': 'Test Subject',
        'mail_body': 'Test Body',
        'mail_recipients': ['test@example.com'],
        'mail_cc': ['cc@example.com'],
        'mail_bcc': ['bcc@example.com']
    }
    test_mail_info = {
        'mail_recipient': 'mail@example.com',
    }
    test_mail_id = 1

    # Test when mail_info has no value for 'mail_recipient' key
    empty_mail_info = {}
    process_send_mail(empty_mail_info, test_mail_id)
    mock_send_mail.assert_not_called()

    # Test when the 'subject' key has no value
    empty_subject_data = test_mail_data.copy()
    empty_subject_data['mail_subject'] = ''
    mock_get_mail_data.return_value = empty_subject_data
    process_send_mail(test_mail_info, test_mail_id)
    mock_send_mail.assert_not_called()

    # Test when the 'body' key has no value
    empty_body_data = test_mail_data.copy()
    empty_body_data['mail_body'] = ''
    mock_get_mail_data.return_value = empty_body_data
    process_send_mail(test_mail_info, test_mail_id)
    mock_send_mail.assert_not_called()

    # Test when the 'subject' key is missing
    missing_subject_data = test_mail_data.copy()
    del missing_subject_data['mail_subject']
    mock_get_mail_data.return_value = missing_subject_data
    process_send_mail(test_mail_info, test_mail_id)
    mock_send_mail.assert_not_called()

    # Test when the 'body' key is missing
    missing_body_data = test_mail_data.copy()
    del missing_body_data['mail_body']
    mock_get_mail_data.return_value = missing_body_data
    process_send_mail(test_mail_info, test_mail_id)
    mock_send_mail.assert_not_called()

    # Test when mail sending succeeds
    mock_get_mail_data.return_value = copy.deepcopy(test_mail_data)
    mock_replace_characters.return_value = 'Replaced Body'
    process_send_mail(test_mail_info, test_mail_id)
    mock_send_mail.assert_called_with({
                    'mail_subject': 'Test Subject',
                    'mail_body': 'Replaced Body',
                    'mail_recipients': ['test@example.com', 'mail@example.com'],
                    'mail_cc': ['cc@example.com'],
                    'mail_bcc': ['bcc@example.com']
                })

# def process_send_mail_tpl(mail_info, mail_pattern_name):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_process_send_mail_tpl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_process_send_mail_tpl(app, mocker):
    mock_sender = mocker.patch('weko_workflow.utils.send_mail')
    mock_get_mail_data = mocker.patch('weko_workflow.utils.get_mail_data_tpl')
    mock_replace_characters = mocker.patch('weko_workflow.utils.replace_characters')
    mock_get_mail_data.return_value = ('subject', 'body')
    mock_replace_characters.return_value = 'replaced_body'
    mail_info = {
        'mail_recipient': 'recipient'
    }

    process_send_mail_tpl(mail_info, 'mail_pattern_name')
    mock_get_mail_data.assert_called_once_with('mail_pattern_name')
    mock_replace_characters.assert_called_once_with(mail_info, 'body')
    mock_sender.assert_called_once_with('subject', 'recipient', 'replaced_body')

    mock_sender = mocker.patch('weko_workflow.utils.send_mail')
    mock_get_mail_data = mocker.patch('weko_workflow.utils.get_mail_data_tpl')
    mock_replace_characters = mocker.patch('weko_workflow.utils.replace_characters')
    mock_get_mail_data.return_value = (None, None)
    process_send_mail_tpl(mail_info, 'mail_pattern_name')
    mock_get_mail_data.assert_called_with('mail_pattern_name')
    mock_replace_characters.assert_not_called()
    mock_sender.assert_not_called()

    mock_sender = mocker.patch('weko_workflow.utils.send_mail')
    mock_get_mail_data = mocker.patch('weko_workflow.utils.get_mail_data_tpl')
    mock_replace_characters = mocker.patch('weko_workflow.utils.replace_characters')
    mail_info = {}
    process_send_mail_tpl(mail_info, 'mail_pattern_name')
    mock_get_mail_data.assert_not_called()
    mock_replace_characters.assert_not_called()
    mock_sender.assert_not_called()

# def cancel_expired_usage_reports():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_cancel_expired_usage_reports -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_cancel_expired_usage_reports(db_register_full_action,mocker):
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
        "restricted_expiration_date_ja":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    activity = db_register["activities"][1]
    guest_activity = db_register["activities"][8]
    guest_activity_2 = db_register["activities"][12]
    guest_activity_3 = db_register["activities"][13]
    guest_activity_4 = db_register["activities"][14]
    next_step_approver_id = users[2]["id"]
    not_next_step_approver_id = 9999
    file_data={
                "file_url":"test_url",
                "expiration_date":"",
                "expiration_date_ja":"無制限",
                "expiration_date_en":"Unlimited"
            }
    guest_file_data={
                "file_url":"test_url",
                "expiration_date":"",
                "expiration_date_ja":"無制限",
                "expiration_date_en":"Unlimited",
                "guest_mail":"guest@test.org"
            }
    # no1, not guest, approval is True,previous.inform_approval is True
    actions_mail_setting={
        "previous":{"inform_reject": {"mail": "0", "send": False}, "inform_itemReg": {"mail": "0", "send": False}, "inform_itemReg_for_registerPerson":{"mail": "0", "send": True},
                     "inform_approval": {"mail": "0", "send": True}, "request_approval": {"mail": "0", "send": False},
                     "inform_reject_for_guest": {"mail": "0", "send": False}, "inform_approval_for_guest": {"mail": "0", "send": True},
                     "request_approval_for_guest": {"mail": "0", "send": False}},
        "next": {},
        "approval": True,
        "reject": False}
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    test_mail_info = {
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"無制限",
        "restricted_expiration_date_en":"Unlimited"
    }
    mock_sender = mocker.patch("weko_workflow.utils.process_send_mail")
    process_send_approval_mails(activity, actions_mail_setting,next_step_approver_id,file_data)
    mock_sender.assert_called_with(test_mail_info,"0")

    # no2, guest, approval is True,previous.inform_approval is True

    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    test_mail_info = {
        "restricted_download_link":"test_url",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"無制限",
        "restricted_expiration_date_en":"Unlimited",
        "mail_recipient":"guest@test.org"
    }
    mock_sender = mocker.patch("weko_workflow.utils.process_send_mail")
    process_send_approval_mails(guest_activity, actions_mail_setting,next_step_approver_id,guest_file_data)
    mock_sender.assert_called_with(test_mail_info,"0")

    # no3, not guest, approval is True,next.request_approval is True
    actions_mail_setting={
        "previous":{},
        "next": {"inform_reject": {"mail": "0", "send": False}, "inform_itemReg": {"mail": "0", "send": False}, "inform_itemReg_for_registerPerson":{"mail": "0", "send": True},
                 "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": True},
                   "inform_reject_for_guest": {"mail": "0", "send": False}, "inform_approval_for_guest": {"mail": "0", "send": False},
                  "request_approval_for_guest": {"mail": "0", "send": True}},
        "approval": True,
        "reject": False}
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    test_mail_info = {
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"無制限",
        "restricted_expiration_date_en":"Unlimited",
        "mail_recipient":"sysadmin@test.org"}
    mock_sender = mocker.patch("weko_workflow.utils.process_send_mail")
    process_send_approval_mails(activity, actions_mail_setting,next_step_approver_id,file_data)
    mock_sender.assert_called_with(test_mail_info,"0")

    # no4, approval is True,request_approval is True, but approver is none
    with patch('weko_workflow.utils.current_app.logger.error') as mock_logger_error:
        process_send_approval_mails(activity, actions_mail_setting,not_next_step_approver_id,file_data)
        mock_logger_error.assert_called_with("Does not have approval data")

    # no5, guest, approval is True,next.request_approval is True
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    test_mail_info = {
        "restricted_download_link":"test_url",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"無制限",
        "restricted_expiration_date_en":"Unlimited",
        "mail_recipient":"sysadmin@test.org"
    }
    mock_sender = mocker.patch("weko_workflow.utils.process_send_mail")
    process_send_approval_mails(guest_activity, actions_mail_setting,next_step_approver_id,guest_file_data)
    mock_sender.assert_called_with(test_mail_info,"0")

    # approval is True,previous.inform_approval is False,next.request_approval is False
    actions_mail_setting={
        "previous":{},
        "next": {"inform_reject": {"mail": "0", "send": False}, "inform_itemReg": {"mail": "0", "send": False}, "inform_itemReg_for_registerPerson":{"mail": "0", "send": True},
                "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False},
                "inform_reject_for_guest": {"mail": "0", "send": False}, "inform_approval_for_guest": {"mail": "0", "send": False},
                "request_approval_for_guest": {"mail": "0", "send": False}},
        "approval": True,
        "reject": False}
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
         "restricted_expiration_date_ja":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    process_send_approval_mails(activity, actions_mail_setting,next_step_approver_id,file_data)

    # no6, approval is True, previous.inform_approval is False,inform_itemreg is True
    actions_mail_setting={
        "previous":{"inform_reject": {"mail": "0", "send": False}, "inform_itemReg": {"mail": "0", "send": True}, "inform_itemReg_for_registerPerson":{"mail": "0", "send": False},
                   "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False},
                     "inform_reject_for_guest": {"mail": "0", "send": False}, "inform_approval_for_guest": {"mail": "0", "send": False},
                     "request_approval_for_guest": {"mail": "0", "send": False}},
        "next": {},
        "approval": True,
        "reject": False}
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    test_mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja": "無制限",
        "restricted_expiration_date_en": "Unlimited"}
    mock_sender = mocker.patch("weko_workflow.utils.process_send_mail")
    process_send_approval_mails(activity, actions_mail_setting,next_step_approver_id,file_data)
    mock_sender.assert_called_with(test_mail_info,"0")

    actions_mail_setting={
        "previous":{"inform_reject": {"mail": "0", "send": False}, "inform_itemReg": {"mail": "0", "send": True}, "inform_itemReg_for_registerPerson":{"mail": "0", "send": True},
                   "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False},
                     "inform_reject_for_guest": {"mail": "0", "send": False}, "inform_approval_for_guest": {"mail": "0", "send": False},
                     "request_approval_for_guest": {"mail": "0", "send": False}},
        "next": {},
        "approval": True,
        "reject": False}

    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    test_mail_info = {
        "restricted_download_link":"test_url",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"無制限",
        "restricted_expiration_date_en":"Unlimited",
        "mail_recipient":"user@test.org"
    }

    process_send_approval_mails(guest_activity_2, actions_mail_setting,next_step_approver_id,guest_file_data)
    mock_sender.assert_called_with(test_mail_info,"0")

    actions_mail_setting={
        "previous":{"inform_reject": {"mail": "0", "send": False}, "inform_itemReg": {"mail": "0", "send": True}, "inform_itemReg_for_registerPerson":{"mail": "0", "send": True},
                   "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False},
                     "inform_reject_for_guest": {"mail": "0", "send": False}, "inform_approval_for_guest": {"mail": "0", "send": False},
                     "request_approval_for_guest": {"mail": "0", "send": False}},
        "next": {},
        "approval": True,
        "reject": False}

    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    test_mail_info = {
        "restricted_download_link":"test_url",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"無制限",
        "restricted_expiration_date_en":"Unlimited",
        "mail_recipient":"user@test.org"
    }

    process_send_approval_mails(guest_activity_3, actions_mail_setting,next_step_approver_id,guest_file_data)
    mock_sender.assert_called_with(test_mail_info,"0")

     # approval is True, previous.inform_approval is False, previous is True, inform_itemReg.send is False
    actions_mail_setting={
        "previous":{"inform_itemReg": {"mail": "0", "send": False}},
        "next": {},
        "approval": True,
        "reject": False}
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    process_send_approval_mails(activity, actions_mail_setting,next_step_approver_id,file_data)

    actions_mail_setting={
        "previous":{"inform_itemReg_for_registerPerson":{"mail": "0", "send": True}},
        "next": {},
        "approval": True,
        "reject": False}
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    mock_sender = mocker.patch("weko_workflow.utils.process_send_mail")
    process_send_approval_mails(guest_activity_4, actions_mail_setting,next_step_approver_id,file_data)
    assert mock_sender.call_count == 2

    # no7, not guest, reject is True, previous.inform_reject is True
    actions_mail_setting={
        "previous":{"inform_reject": {"mail": "0", "send": True}, "inform_itemReg": {"mail": "0", "send": False},  "inform_itemReg_for_registerPerson":{"mail": "0", "send": True},
                    "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False},
                    "inform_reject_for_guest": {"mail": "0", "send": True}, "inform_approval_for_guest": {"mail": "0", "send": False},
                    "request_approval_for_guest": {"mail": "0", "send": False}},
        "next": {},
        "approval": False,
        "reject": True}
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    test_mail_info = {
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"無制限",
        "restricted_expiration_date_en":"Unlimited"
    }
    mock_sender = mocker.patch("weko_workflow.utils.process_send_mail")
    process_send_approval_mails(activity, actions_mail_setting,next_step_approver_id,file_data)
    mock_sender.assert_called_with(test_mail_info,"0")

    # no8, guest, reject is True, previous.inform_reject is True
    mail_info={
        "restricted_download_link":"",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"",
        "restricted_expiration_date_en":""
    }
    mocker.patch("weko_workflow.utils.set_mail_info",return_value=mail_info)
    test_mail_info = {
        "restricted_download_link":"test_url",
        "restricted_expiration_date":"",
        "restricted_expiration_date_ja":"無制限",
        "restricted_expiration_date_en":"Unlimited",
        "mail_recipient":"guest@test.org"
    }
    mock_sender = mocker.patch("weko_workflow.utils.process_send_mail")
    process_send_approval_mails(guest_activity, actions_mail_setting,next_step_approver_id,guest_file_data)
    mock_sender.assert_called_with(test_mail_info,"0")

    # reject is True, previous.inform_reject is False
    actions_mail_setting={
        "previous":{"inform_reject": {"mail": "0", "send": False}, "inform_itemReg": {"mail": "0", "send": False}, "inform_itemReg_for_registerPerson":{"mail": "0", "send": True},
                    "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False},
                    "inform_reject_for_guest": {"mail": "0", "send": False}, "inform_approval_for_guest": {"mail": "0", "send": False},
                    "request_approval_for_guest": {"mail": "0", "send": False}},
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
    process_send_approval_mails(activity, actions_mail_setting,next_step_approver_id,file_data)

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
    process_send_approval_mails(activity, actions_mail_setting,next_step_approver_id,file_data)

    # reject is True, previous is None
    actions_mail_setting={
        "previous":{},
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
    process_send_approval_mails(activity, actions_mail_setting,next_step_approver_id,file_data)

# def get_usage_data(item_type_id, activity_detail, user_profile=None):
#     def __build_metadata_for_usage_report(record_data: Union[dict, list],
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_usage_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_usage_data(app,db,db_register_full_action):

    # not exist extra_info activity
    activity = db_register_full_action["activities"][1]
    result = get_usage_data(1,activity)
    assert result == {}

    activity = db_register_full_action["activities"][8]
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
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_update_approval_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_update_approval_date(app,db_register_full_action,mocker):
    mocker.patch("weko_workflow.utils.update_approval_date_for_deposit")
    mocker.patch("weko_workflow.utils.update_system_data_for_item_metadata")
    mocker.patch("weko_workflow.utils.update_system_data_for_activity")

    activity = db_register_full_action["activities"][1]

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
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_create_record_metadata_for_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_create_record_metadata_for_user(app,db_register_full_action,mocker):
    mock_update_deposit = mocker.patch("weko_workflow.utils.update_system_data_for_item_metadata")
    mock_update_metadata = mocker.patch("weko_workflow.utils.update_approval_date_for_deposit")
    mock_update_system = mocker.patch("weko_workflow.utils.update_system_data_for_activity")

    activitiy = db_register_full_action["activities"][0]
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
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_update_system_data_for_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_update_system_data_for_activity(db_register_full_action):
    update_system_data_for_activity(None,None,None)

    key = "temp_key"
    value = {"data_key":"data_value"}
    activity = db_register_full_action["activities"][1]
    update_system_data_for_activity(activity,key,value)
    assert activity.temp_data == '{"metainfo": {"temp_key": {"data_key": "data_value"}}}'

    activity = db_register_full_action["activities"][2]
    update_system_data_for_activity(activity,key,value)
    assert activity.temp_data == '{"metainfo": {"temp_key": {"data_key": "data_value"}}}'


# def check_authority_by_admin(activity):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_check_authority_by_admin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_authority_by_admin(client, activity_acl, activity_acl_users):
    users = activity_acl_users["users"]

    # sysadmin user
    login_user(users[0])
    result = check_authority_by_admin(activity_acl[0])
    assert result == True

    # comadmin user, activity.item_id is None
    login_user(users[3])
    result = check_authority_by_admin(activity_acl[30])
    assert result == False

    # comadmin user, activity.item_id exist, path is not included in community index
    login_user(users[3])
    result = check_authority_by_admin(activity_acl[26])
    assert result == False

    # comadmin user, activity.item_id exist, path is included in community index
    login_user(users[3])
    result = check_authority_by_admin(activity_acl[21])
    assert result == True
    # not admin user
    login_user(users[2])
    result = check_authority_by_admin(activity_acl[21])
    assert result == False


# def validate_action_role_user(activity_id, action_id, action_order):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_validate_action_role_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_validate_action_role_user(db, activity_acl_users,workflow_with_action_role):
    users = activity_acl_users["users"]
    workflow = workflow_with_action_role
    login_user(users[2])

    # not set action role(user)
    activity = create_activity(db,"not_set_action_role(user)",1,["4"],users[2],-1,workflow[0],'M',3)
    is_set, is_allow, is_deny = validate_action_role_user(activity.activity_id, activity.action_id,activity.action_order)
    assert is_set == False
    assert is_allow == False
    assert is_deny == False

    # set action role as allow, self is include action role
    activity = create_activity(db,"not_set_action_role(user)",2,["4"],users[2],-1,workflow[1],'M',3)
    is_set, is_allow, is_deny = validate_action_role_user(activity.activity_id, activity.action_id,activity.action_order)
    assert is_set == True
    assert is_allow == True
    assert is_deny == False

    # set action role as allow, self is not include action role
    activity = create_activity(db,"not_set_action_role(user)",3,["4"],users[2],-1,workflow[2],'M',3)
    is_set, is_allow, is_deny = validate_action_role_user(activity.activity_id, activity.action_id,activity.action_order)
    assert is_set == True
    assert is_allow == False
    assert is_deny == True

    # set action role as deny, self is include action role
    activity = create_activity(db,"not_set_action_role(user)",4,["4"],users[2],-1,workflow[3],'M',3)
    is_set, is_allow, is_deny = validate_action_role_user(activity.activity_id, activity.action_id,activity.action_order)
    assert is_set == True
    assert is_allow == False
    assert is_deny == True

    # set action role as deny, self is not include action role
    activity = create_activity(db,"not_set_action_role(user)",5,["4"],users[2],-1,workflow[4],'M',3)
    is_set, is_allow, is_deny = validate_action_role_user(activity.activity_id, activity.action_id,activity.action_order)
    assert is_set == True
    assert is_allow == False
    assert is_deny == False

    # set action user as allow , self is include action user
    activity = create_activity(db,"not_set_action_role(user)",6,["4"],users[2],-1,workflow[5],'M',3)
    is_set, is_allow, is_deny = validate_action_role_user(activity.activity_id, activity.action_id,activity.action_order)
    assert is_set == True
    assert is_allow == True
    assert is_deny == False

    # set action user as allow , self is not include action user
    activity = create_activity(db,"not_set_action_role(user)",7,["4"],users[2],-1,workflow[6],'M',3)
    is_set, is_allow, is_deny = validate_action_role_user(activity.activity_id, activity.action_id,activity.action_order)
    assert is_set == True
    assert is_allow == False
    assert is_deny == True

    # set action user as deny , self is include action user
    activity = create_activity(db,"not_set_action_role(user)",8,["4"],users[2],-1,workflow[7],'M',3)
    is_set, is_allow, is_deny = validate_action_role_user(activity.activity_id, activity.action_id,activity.action_order)
    assert is_set == True
    assert is_allow == False
    assert is_deny == True

    # set action user as deny , self is not include action user
    activity = create_activity(db,"not_set_action_role(user)",9,["4"],users[2],-1,workflow[8],'M',3)
    is_set, is_allow, is_deny = validate_action_role_user(activity.activity_id, activity.action_id,activity.action_order)
    assert is_set == True
    assert is_allow == False
    assert is_deny == False


# def get_record_first_version(deposit):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_record_first_version -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_record_first_version(db_register_full_action,db_records):
    activity = db_register_full_action["activities"][1]
    record = WekoRecord.get_record(activity.item_id)
    deposit = WekoDeposit(record, record.model)


    result_deposit, pid = get_record_first_version(deposit)
    assert result_deposit == db_records[0][6]
    assert pid == db_records[0][0].object_uuid
# def get_files_and_thumbnail(activity_id, item):

# def get_pid_and_record(item_id):

# def get_items_metadata_by_activity_detail(activity_detail):

# def get_main_record_detail(activity_id,
#     def check_record(record):

# def prepare_doi_link_workflow(item_id, doi_input):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_prepare_doi_link_workflow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_prepare_doi_link_workflow(app):
    app.config["PRESERVE_CONTEXT_ON_EXCEPTION"] = False
    with app.test_request_context(data={}):
        doi_identifier = Identifier(id=1, repository='Root Index',jalc_flag= True,jalc_crossref_flag= True,jalc_datacite_flag=True,ndl_jalc_flag=True,
            jalc_doi='123',jalc_crossref_doi='1234',jalc_datacite_doi='12345',ndl_jalc_doi='123456',suffix='suffix_',
            created_userId='1',created_date=datetime.datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S'),
            updated_userId='1',updated_date=datetime.datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S')
        )
        with patch("weko_workflow.utils.get_identifier_setting",return_value=doi_identifier):

            doi_input = {'action_identifier_select': '1',
                          'action_identifier_jalc_doi': 'test_jalc_doi',
                          'action_identifier_jalc_cr_doi': 'test_cr_doi',
                          'action_identifier_jalc_dc_doi': 'test_dc_doi',
                          'action_identifier_ndl_jalc_doi': 'test_ndl_doi'
                          }
            # suffix_method is 0
            app.config["IDENTIFIER_GRANT_SUFFIX_METHOD"]=0
            result = prepare_doi_link_workflow("123456", doi_input)
            test = {
                'identifier_grant_jalc_doi_link': "https://doi.org/123/0000123456",
                'identifier_grant_jalc_cr_doi_link': "https://doi.org/1234/0000123456",
                'identifier_grant_jalc_dc_doi_link': "https://doi.org/12345/0000123456",
                'identifier_grant_ndl_jalc_doi_link': "https://doi.org/123456/test_ndl_doi"
            }
            assert result == test

            # suffix_method is 1
            app.config["IDENTIFIER_GRANT_SUFFIX_METHOD"]=1
            result = prepare_doi_link_workflow("123456", doi_input)
            test = {
                'identifier_grant_jalc_doi_link': "https://doi.org/123/suffix_test_jalc_doi",
                'identifier_grant_jalc_cr_doi_link': "https://doi.org/1234/suffix_test_cr_doi",
                'identifier_grant_jalc_dc_doi_link': "https://doi.org/12345/suffix_test_dc_doi",
                'identifier_grant_ndl_jalc_doi_link': "https://doi.org/123456/test_ndl_doi"
            }
            assert result == test

            # suffix_method is 2
            app.config["IDENTIFIER_GRANT_SUFFIX_METHOD"]=2
            result = prepare_doi_link_workflow("123456", doi_input)
            test = {
                'identifier_grant_jalc_doi_link': "https://doi.org/123/test_jalc_doi",
                'identifier_grant_jalc_cr_doi_link': "https://doi.org/1234/test_cr_doi",
                'identifier_grant_jalc_dc_doi_link': "https://doi.org/12345/test_dc_doi",
                'identifier_grant_ndl_jalc_doi_link': "https://doi.org/123456/test_ndl_doi"
            }
            assert result == test

        # not exist suffix
        not_suffix_identifier = Identifier(id=1, repository='Root Index',jalc_flag= True,jalc_crossref_flag= True,jalc_datacite_flag=True,ndl_jalc_flag=True,
            jalc_doi='123',jalc_crossref_doi='1234',jalc_datacite_doi='12345',ndl_jalc_doi='123456',
            created_userId='1',created_date=datetime.datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S'),
            updated_userId='1',updated_date=datetime.datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S')
        )
        with patch("weko_workflow.utils.get_identifier_setting",return_value = not_suffix_identifier):
            app.config["IDENTIFIER_GRANT_SUFFIX_METHOD"]=1
            result = prepare_doi_link_workflow("123456", doi_input)
            test = {
                'identifier_grant_jalc_doi_link': "https://doi.org/123/test_jalc_doi",
                'identifier_grant_jalc_cr_doi_link': "https://doi.org/1234/test_cr_doi",
                'identifier_grant_jalc_dc_doi_link': "https://doi.org/12345/test_dc_doi",
                'identifier_grant_ndl_jalc_doi_link': "https://doi.org/123456/test_ndl_doi"
            }
            assert result == test

         # doi is null
        null_identifier = Identifier(id=1, repository='Root Index')
        with patch("weko_workflow.utils.get_identifier_setting",return_value = null_identifier):
            app.config["IDENTIFIER_GRANT_SUFFIX_METHOD"]=0
            result = prepare_doi_link_workflow("123456", doi_input)
            test = {
                'identifier_grant_jalc_doi_link': "https://doi.org/<Empty>/0000123456",
                'identifier_grant_jalc_cr_doi_link': "https://doi.org/<Empty>/0000123456",
                'identifier_grant_jalc_dc_doi_link': "https://doi.org/<Empty>/0000123456",
                'identifier_grant_ndl_jalc_doi_link': "https://doi.org/<Empty>/test_ndl_doi"
            }
            assert result == test

        # identifier_setting is null
        with pytest.raises(Exception) as e:
            app.config["IDENTIFIER_GRANT_SUFFIX_METHOD"]=0
            result = prepare_doi_link_workflow("123456", doi_input)
            assert result == {}


# def get_pid_value_by_activity_detail(activity_detail):

# def check_doi_validation_not_pass(item_id, activity_id,


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_index_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
# def test_get_index_id():
    # """Get index ID base on activity id"""
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
    # raise BaseException

# def is_terms_of_use_only(workflow_id :int) -> bool:
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_is_terms_of_use_only -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_is_terms_of_use_only(app ,workflow ,workflow_open_restricted):
    with app.test_request_context():
        assert not is_terms_of_use_only(workflow["workflow"].id)
        assert is_terms_of_use_only(workflow_open_restricted[0]["workflow"].id)
        assert not is_terms_of_use_only(workflow_open_restricted[1]["workflow"].id)

# def grant_access_rights_to_all_open_restricted_files(activity_id :str ,permission:Union[FilePermission,GuestActivity] , activity_detail :Activity) -> dict:
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_grant_access_rights_to_all_open_restricted_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_grant_access_rights_to_all_open_restricted_files(app ,db,users ):
    activity_id = "20000101-99"
    file_permission = FilePermission(
        file_name= "bbb.txt"
        ,record_id=1
        ,status=-1
        ,usage_application_activity_id=activity_id
        ,user_id=users[0]["id"]
        ,usage_report_activity_id=None
    )
    db.session.add(file_permission)
    activity_detail:Activity = Activity()
    activity_detail.extra_info = {
                    "file_name": "bbb.txt"
                    , "record_id": 1
                    , "user_mail": users[0]["email"]
                }

    activity_id_guest = "20001231-99"
    guest_activity = GuestActivity(
        file_name= "bbb.txt"
        ,record_id=1
        ,status=-1
        ,activity_id=activity_id_guest
        ,user_mail=users[5]["email"]
        ,expiration_date=0
        ,is_usage_report=None
        ,token=''
    )
    db.session.add(guest_activity)
    activity_detail_guest:Activity = Activity()
    activity_detail_guest.extra_info = {
                    "file_name": "bbb.txt"
                    , "record_id": 1
                    , "guest_mail": users[5]["email"]
                }
    mock = MagicMock()
    mock.get_file_data = lambda : [{'accessrole' : 'open_restricted','filename':'aaa.txt'}
                                ,{'accessrole' : 'open_restricted','filename':'bbb.txt'}
                                ,{'accessrole' : 'open_access'    ,'filename':'ccc.txt'}]

    with app.test_request_context():
        with patch('weko_workflow.utils.WekoRecord.get_record_by_pid',return_value = mock):
            res = grant_access_rights_to_all_open_restricted_files(activity_id ,file_permission, activity_detail )
            # print(res)
            assert 'bbb.txt' in res["file_url"]

            fps = FilePermission.find_by_activity(activity_id)
            assert len(fps) == 2

            for fp in fps:
                assert fp.status == 1

                user = list(filter(lambda x : x["obj"].id == fp.user_id ,users))[0]

                fd = FileOnetimeDownload.find(
                    file_name = fp.file_name,
                    record_id = fp.record_id,
                    user_mail = user["obj"].email
                )
                assert len(fd) == 1

    with app.test_request_context():
        res = grant_access_rights_to_all_open_restricted_files(activity_id_guest ,guest_activity, activity_detail_guest )
        assert 'bbb.txt' in res["file_url"]
        fps = FilePermission.find_by_activity(activity_id_guest)
        assert len(fps) == 0
        fd = FileOnetimeDownload.find(
                    file_name = guest_activity.file_name,
                    record_id = guest_activity.record_id,
                    user_mail = users[5]["email"]
                )
        assert len(fd) == 1

    res = grant_access_rights_to_all_open_restricted_files(activity_id ,None, activity_detail )
    assert res == {}

# def get_contributors(pid_value)
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_contributors -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_contributors(db, users_1, db_records_1):
    # 引数のpid_valueをfalseに設定する。
    actual = get_contributors(False)
    assert actual == []

    # 引数のpid_valueをfalseに設定する。 user_id_list_json(List型) Listの中がdict
    user_id_list_json = [{"user":1},{"user":2}]
    actual = get_contributors(False, user_id_list_json=user_id_list_json, owner_id=1)
    expected = [{
                'userid' : 1,
                'username': "",
                'email' : "user1@sample.com",
                'owner' : True,
                'error': ''
                },{
                'userid' : 2,
                'username': "",
                'email' : "user2@sample.com",
                'owner' : False,
                'error': ''
                }]
    assert actual == expected

    # 引数のpid_valueをfalseに設定する。 user_id_list_json(List型) Listの中がstring
    user_id_list_json = ["漢字", "ひらがな"]
    actual = get_contributors(False, user_id_list_json=user_id_list_json, owner_id=1)
    expected = [{
                'userid' : 1,
                'username': "",
                'email' : "user1@sample.com",
                'owner' : True,
                'error': ''
                }]
    assert actual == expected

    # 引数のpid_valueをfalseに設定する。 user_id_list_json(Dict型)
    user_id_list_json = {"user": 1}
    actual = get_contributors(False, user_id_list_json=user_id_list_json, owner_id=1)
    expected = [{
                'userid' : 1,
                'username': "",
                'email' : "user1@sample.com",
                'owner' : True,
                'error': ''
                }]
    assert actual == expected

    # pid_value=196.0を設定
    user_profile_1 = UserProfile(
        user_id=1,
        _username="ユーザー1",
        fullname="ユーザー1 full",
        timezone="asia",
        language="japanese",
        _displayname="display ユーザー1"
    )
    user_profile_2 = UserProfile(
        user_id=2,
        _username="ユーザー2",
        fullname="ユーザー2 full",
        timezone="asia",
        language="japanese",
        _displayname="display ユーザー2"
    )
    db.session.add(user_profile_1)
    db.session.add(user_profile_2)
    db.session.commit()

    actual = get_contributors('196.0')
    assert actual == [{ 'userid' : 1,
                       'username': "ユーザー1",
                       'email' : "user1@sample.com",
                       'owner' : True,
                       'error': ''
                    }]

    # pid_value=196.1を設定
    # weko_shared_ids": [100] を設定（存在しないユーザーID）
    actual = get_contributors('197')
    expected = [{
                'userid' : 1,
                'username': "ユーザー1",
                'email' : "user1@sample.com",
                'owner' : True,
                'error': ''
                },
                {
                'userid' : 100,
                'username': '',
                'email' : '',
                'owner' : False,
                'error': 'The specified user ID is incorrect'
                }]
    assert sorted(actual, key=lambda x: x["userid"]) == sorted(expected, key=lambda x: x["userid"])

    expected = [{
            'userid' : 1,
            'username': "ユーザー1",
            'email' : "user1@sample.com",
            'owner' : True,
            'error': ''
            },
            {
            'userid' : 2,
            'username': "ユーザー2",
            'email' : "user2@sample.com",
            'owner' : False,
            'error': ''
            }]
    # user_id_list_jsonを設定
    user_id_list_json = [2]
    actual = get_contributors(None, user_id_list_json, owner_id=1)
    assert sorted(actual, key=lambda x: x["userid"]) == sorted(expected, key=lambda x: x["userid"])


status_list = [
    ('todo', '1', '2'),
    ('wait', '3', '4'),
    ('all', '5', '6'),
    ('test', '7', '8')
]
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_create_conditions_dict -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('status, limit, page', status_list)
def test_create_conditions_dict(status, limit, page):
    if status == 'todo':
        condition = create_conditions_dict(status, limit, page)
        assert condition.get('tab')[0] == status
        assert condition.get('sizetodo')[0] == limit
        assert condition.get('pagestodo')[0] == page
    elif status == 'wait':
        condition = create_conditions_dict(status, limit, page)
        assert condition.get('tab')[0] == status
        assert condition.get('sizewait')[0] == limit
        assert condition.get('pageswait')[0] == page
    elif status == 'all':
        condition = create_conditions_dict(status, limit, page)
        assert condition.get('tab')[0] == status
        assert condition.get('sizeall')[0] == limit
        assert condition.get('pagesall')[0] == page
    elif status == 'test':
        with pytest.raises(InvalidParameterValueError) as e:
            create_conditions_dict(status, limit, page)
        assert str(e.value) == '400 Bad Request: Invalid request parameter value.'
    else:
        assert False


role_list = [
    (0, True),  # contributor
    (1, True),  # repoadmin
    (2, True),  # sysadmin
    (3, True),  # comadmin
    (4, False), # general
    (7, False)  # anonymous
]
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_check_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('index, expect', role_list)
def test_check_role(app, users, index, expect):
    if index != 5:
        with app.test_request_context():
            login_user(users[index]['obj'])
            assert check_role() == expect
    else:
        assert check_role() == expect


etag_list = [
    ('match', True),
    ('not match', False),
    ('', False)
]
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_check_etag -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('etag, expect', etag_list)
def test_check_etag(i18n_app, etag, expect):
    assert bool(check_etag(etag)) == expect


pretty_list = [
    ('true', True),
    ('t', True),
    ('yes', True),
    ('1', True),
    ('aaa', False)
]
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_check_pretty -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('pretty, expect', pretty_list)
def test_check_pretty(app, pretty, expect):
    with app.test_request_context():
        check_pretty(pretty)
        assert current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] == expect

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_make_activitylog_tsv -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_make_activitylog_tsv(db_register,db_records):
    """test make_activitylog_tsv"""
    activities = []
    activities += ActivityHistory.query.filter_by(activity_id="2").all()
    activities += ActivityHistory.query.filter_by(activity_id="3").all()

    output_tsv = make_activitylog_tsv(activities)
    assert isinstance(output_tsv,str)
    assert len(output_tsv.splitlines()) == 1

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_delete_lock_activity_cache -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_delete_lock_activity_cache(client,users):
    data = {
        "locked_value": "1-1661748792565"
    }
    activity_id="A-22240219-00001"
    cache_key = "workflow_locked_activity_{}".format(activity_id)
    current_cache.delete(cache_key)
    # cur_locked_val is empty
    result = delete_lock_activity_cache(activity_id, data)
    assert result == None
    # cur_locked_val is not empty, cur_locked_val==locked_value
    current_cache.set(cache_key,data["locked_value"])
    result = delete_lock_activity_cache(activity_id, data)
    assert result == "Unlock success"
    assert current_cache.get(cache_key) == None
    # cur_locked_val is not empty, cur_locked_val!=locked_value
    wrong_val = "2-1234456778"
    current_cache.set(cache_key,wrong_val)
    result = delete_lock_activity_cache(activity_id, data)
    assert result == None
    assert current_cache.get(cache_key) == wrong_val

    current_cache.delete(cache_key)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_delete_user_lock_activity_cache -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_delete_user_lock_activity_cache(client,users):
    user = users[2]
    login_user(user["obj"])
    data = {
        "is_opened": False,
        "is_force": False,
    }
    activity_id = "A-22240219-00001"
    cache_key = "workflow_userlock_activity_{}".format(user["id"])
    current_cache.delete(cache_key)
    # cur_locked_val is empty
    result = delete_user_lock_activity_cache(activity_id, data)
    assert result == "Not unlock"
    # cur_locked_val is not empty, is_opened is False
    current_cache.set(cache_key, activity_id)
    result = delete_user_lock_activity_cache(activity_id, data)
    assert result == "User Unlock Success"
    assert current_cache.get(cache_key) == None

    # cur_locked_val is not empty, is_opened is True, is_force is False
    current_cache.set(cache_key, activity_id)
    data["is_opened"] = True
    result = delete_user_lock_activity_cache(activity_id, data)
    assert result == "Not unlock"

    # cur_locked_val is not empty, is_opened is True, is_force is True
    data["is_force"] = True
    result = delete_user_lock_activity_cache(activity_id, data)
    assert result == "User Unlock Success"
    assert current_cache.get(cache_key) == None

    current_cache.delete(cache_key)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_convert_to_timezone -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_convert_to_timezone():
    # UTC datetime
    dt_utc = datetime.datetime(2025, 3, 28, 12, 0, 0, tzinfo=pytz.utc)
    assert convert_to_timezone(dt_utc).strftime("%Y-%m-%d %H:%M:%S %Z") == "2025-03-28 12:00:00 UTC"

    # UTC -> Asia/Tokyo
    assert convert_to_timezone(dt_utc, "Asia/Tokyo").strftime("%Y-%m-%d %H:%M:%S %Z") == "2025-03-28 21:00:00 JST"

    # naive datetime を Asia/Tokyo に変換
    dt_naive = datetime.datetime(2025, 3, 28, 12, 0, 0)
    converted_dt = convert_to_timezone(dt_naive, "Asia/Tokyo")
    assert converted_dt.strftime("%Y-%m-%d %H:%M:%S %Z") == "2025-03-28 21:00:00 JST"

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_load_template -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_load_template(mocker):
    mocker.patch("os.path.exists", side_effect=lambda path: "test_template_en.txt" in path)
    mocker.patch("builtins.open", mocker.mock_open(read_data="Test Subject\nThis is a test email."))
    expected_result = {"subject": "Test Subject", "body": "This is a test email."}
    result = load_template("test_template_{language}.txt", "en")
    assert result == expected_result

    mocker.patch("os.path.exists", side_effect=lambda path: "test_template_ja.txt" in path)
    mocker.patch("builtins.open", mocker.mock_open(read_data="テスト件名\nこれはテストメールです。"))
    expected_result = {"subject": "テスト件名", "body": "これはテストメールです。"}
    result = load_template("test_template_{language}.txt", "ja")
    assert result == expected_result

    mocker.patch("os.path.exists", side_effect=lambda path: "test_template_en.txt" in path)
    mocker.patch("builtins.open", mocker.mock_open(read_data="Default Subject\nDefault body."))
    expected_result = {"subject": "Default Subject", "body": "Default body."}
    result = load_template("test_template_{language}.txt", "fr")
    assert result == expected_result

    mocker.patch("os.path.exists", side_effect=lambda path: "test_template_en.txt" in path)
    mocker.patch("builtins.open", mocker.mock_open(read_data="Default Subject\nDefault body."))
    expected_result = {"subject": "Default Subject", "body": "Default body."}
    result = load_template("test_template_{language}.txt")
    assert result == expected_result

    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("builtins.open", side_effect=FileNotFoundError)
    with pytest.raises(FileNotFoundError):
        load_template("test_template_{language}.txt", "fr")

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_fill_template -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_fill_template():
    # Embed name into the template
    template = {"subject": "Hello, {{ name }}!", "body": "Dear {{ name }}, welcome!"}
    data = {"name": "Alice"}
    expected_result = {"subject": "Hello, Alice!", "body": "Dear Alice, welcome!"}
    result = fill_template(template, data)
    assert result == expected_result

    # Replace multiple placeholders
    template = {"subject": "{{ user }}'s Order", "body": "Hi {{ user }}, your order #{{ order }} is ready."}
    data = {"user": "Bob", "order": "12345"}
    expected_result = {"subject": "Bob's Order", "body": "Hi Bob, your order #12345 is ready."}
    result = fill_template(template, data)
    assert result == expected_result

    # Missing data for some placeholders
    template = {"subject": "Hello, {{ name }}!", "body": "Dear {{ name }}, your age is {{ age }}."}
    data = {"name": "Charlie"}
    expected_result = {"subject": "Hello, Charlie!", "body": "Dear Charlie, your age is {{ age }}."}
    result = fill_template(template, data)
    assert result == expected_result

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_non_extract_files_by_recid -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_non_extract_files_by_recid(db_register, mocker):
    # Mock PersistentIdentifier.get
    mock_pid = mocker.patch("weko_workflow.utils.PersistentIdentifier.get")
    mock_pid.return_value = mocker.Mock(object_uuid="test_uuid")

    # Mock WorkActivity.get_workflow_activity_by_item_id
    mock_activity = mocker.patch("weko_workflow.utils.WorkActivity.get_workflow_activity_by_item_id")

    # Activity is None
    mock_activity.return_value = None
    result = get_non_extract_files_by_recid("12345")
    assert result is None

    # Activity has temp_data as a valid JSON string with non-extract files
    mock_activity.return_value = mocker.Mock(temp_data=json.dumps({
        "files": [
            {"filename": "file1.txt", "non_extract": True},
            {"filename": "file2.txt", "non_extract": False},
            {"filename": "file3.txt", "non_extract": True},
        ]
    }))
    result = get_non_extract_files_by_recid("12345")
    assert result == ["file1.txt", "file3.txt"]

    # Activity has temp_data as a valid JSON string with no non-extract files
    mock_activity.return_value = mocker.Mock(temp_data=json.dumps({
        "files": [
            {"filename": "file1.txt", "non_extract": False},
            {"filename": "file2.txt", "non_extract": False},
        ]
    }))
    result = get_non_extract_files_by_recid("12345")
    assert result == []

    # Activity has temp_data as an invalid JSON string
    mock_activity.return_value = mocker.Mock(temp_data="invalid_json")
    with pytest.raises(json.JSONDecodeError):
        get_non_extract_files_by_recid("12345")

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_check_activity_settings -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_activity_settings(app):
    # case: dict type settings
    mock_settings = {'activity_display_flg': True}

    true_dict_settings = {'activity_display_flg': True}
    false_dict_settings = {'activity_display_flg': False}
    other_dict_settings = {'other_flg': True}

    from types import SimpleNamespace
    true_obj_settings = SimpleNamespace(activity_display_flg=True)
    false_obj_settings = SimpleNamespace(activity_display_flg=False)
    other_obj_settings = SimpleNamespace(other_flg=True)

    with patch('weko_workflow.utils.AdminSettings.get', return_value=mock_settings):
        # mock current_app.config
        with app.app_context():
            # reset current_app.config before test
            current_app.config['WEKO_WORKFLOW_APPROVER_EMAIL_COLUMN_VISIBLE'] = None



            # check settings
            # case: settings is None
            check_activity_settings()
            assert current_app.config['WEKO_WORKFLOW_APPROVER_EMAIL_COLUMN_VISIBLE'] == True

            # case: dict type settings(True)
            check_activity_settings(true_dict_settings)
            assert current_app.config['WEKO_WORKFLOW_APPROVER_EMAIL_COLUMN_VISIBLE'] == True

            # case: dict type settings(False)
            check_activity_settings(false_dict_settings)
            assert current_app.config['WEKO_WORKFLOW_APPROVER_EMAIL_COLUMN_VISIBLE'] == False

            # case: dict type settings(Other), no changes from (case: dict type settings(False))
            check_activity_settings(other_dict_settings)
            assert current_app.config['WEKO_WORKFLOW_APPROVER_EMAIL_COLUMN_VISIBLE'] == False

            # case: object type settings(True)
            check_activity_settings(true_obj_settings)
            assert current_app.config['WEKO_WORKFLOW_APPROVER_EMAIL_COLUMN_VISIBLE'] == True

            # case: object type settings(False)
            check_activity_settings(false_obj_settings)
            assert current_app.config['WEKO_WORKFLOW_APPROVER_EMAIL_COLUMN_VISIBLE'] == False

            # case: object type settings(Other), no changes from (case: object type settings(False))
            check_activity_settings(other_obj_settings)
            assert current_app.config['WEKO_WORKFLOW_APPROVER_EMAIL_COLUMN_VISIBLE'] == False
