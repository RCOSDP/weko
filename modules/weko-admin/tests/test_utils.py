import csv
import uuid
from mock import patch
from datetime import datetime, timedelta
from flask import current_app, Markup
from io import StringIO
import pytest
import json

from invenio_indexer.api import RecordIndexer
from invenio_cache import current_cache

from weko_index_tree.api import Indexes
from weko_records.api import ItemTypes, SiteLicense,ItemsMetadata
from weko_user_profiles import UserProfile

from weko_admin.config import WEKO_ADMIN_MANAGEMENT_OPTIONS, WEKO_ADMIN_RESTRICTED_ACCESS_SETTINGS
from weko_admin.models import AdminLangSettings, FeedbackMailHistory, FeedbackMailFailed, SiteInfo
from weko_admin.utils import (
    get_response_json,
    allowed_file,
    get_search_setting,
    get_admin_lang_setting,
    update_admin_lang_setting,
    get_selected_language,
    get_api_certification_type,
    get_current_api_certification,
    save_api_certification,
    create_crossref_url,
    validate_certification,
    get_initial_stats_report,
    get_unit_stats_report,
    get_user_report_data,
    package_reports,
    make_stats_file,
    write_report_file_rows,
    reset_redis_cache,
    is_exists_key_in_redis,
    is_exists_key_or_empty_in_redis,
    get_redis_cache,
    StatisticMail,
    get_system_default_language,
    str_to_bool,
    FeedbackMail,
    validation_site_info,
    format_site_info_data,
    get_site_name_for_current_language,
    get_notify_for_current_language,
    __build_init_display_index,
    get_init_display_index,
    get_restricted_access,
    update_restricted_access,
    UsageReport,
    get_facet_search,
    get_item_mapping_list,
    create_facet_search_query,
    store_facet_search_query_in_redis,
    get_query_key_by_permission,
    get_facet_search_query,
    get_title_facets,
    is_exits_facet,
    overwrite_the_memory_config_with_db
)

from tests.helpers import json_data

# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp


# def get_response_json(result_list, n_lst):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_response_json -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_response_json(app,site_license,item_type):
    # result_list is not list
    result = get_response_json("","")
    assert result == {}
    
    n_lst = ItemTypes.get_latest()
    result_list = SiteLicense.get_records()
    test = {
        "site_license":[
            {"addresses":[{"finish_ip_address":["987","654","321","098"],"start_ip_address":["123","456","789","012"]}],
             "domain_name":"test_domain",
             "mail_address":"test@mail.com",
             "organization_name":"test data",
             "receive_mail_flag":"T"}
        ],
        "item_type":{"deny":[{"id":"2","name":"テストアイテムタイプ2"}],"allow":[{"id":"1","name":"テストアイテムタイプ1"}]}
    }
    result = get_response_json(result_list,n_lst)
    assert result == test
    
    result_list = [
        "test"
    ]


# def allowed_file(filename):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_allowed_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_allowed_file():
    filename = "test.txt"
    result = allowed_file(filename)
    assert result == False
    
    filename = "test.png"
    result = allowed_file(filename)
    assert result == True


# def get_search_setting():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_search_setting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_search_setting(app,search_management):
    with patch("weko_admin.utils.SearchManagement.get",return_value=None):
        result = get_search_setting()
        assert result == WEKO_ADMIN_MANAGEMENT_OPTIONS
    
    result = get_search_setting()
    assert result=={"init_disp_setting":{"init_disp_index":"","init_disp_index_disp_method":"0","init_disp_screen_setting":"0"}}
    
# def get_admin_lang_setting():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_admin_lang_setting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_admin_lang_setting(language_setting):
    test = [
        {"is_registered":True,"lang_code":"en","lang_name":"English","sequence":1},
        {"is_registered":True,"lang_code":"ja","lang_name":"日本語","sequence":2}]
    result = get_admin_lang_setting()
    assert result == test
    
    with patch("weko_admin.utils.AdminLangSettings.get_active_language",side_effect=Exception("test_error")):
        result = get_admin_lang_setting()
        assert result=="test_error"


# def update_admin_lang_setting(admin_lang_settings):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_update_admin_lang_setting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_update_admin_lang_setting(language_setting):
    admin_lang_settings = [
        {"lang_code":"en","lang_name":"English2","is_registered":False,"sequence":10},        
    ]
    result = update_admin_lang_setting(admin_lang_settings)
    assert result == "success"
    assert AdminLangSettings.query.filter_by(lang_code="en").one().lang_name == "English2"
    
    with patch("weko_admin.utils.AdminLangSettings.update_lang",side_effect=Exception("test_error")):
        result = update_admin_lang_setting(admin_lang_settings)
        assert result=="test_error"


# def get_selected_language():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_selected_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_selected_language(app,language_setting):
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        test = {
            "lang":[{"is_registered":True,"lang_code":"en","lang_name":"English","sequence":1},
                    {"is_registered":True,"lang_code":"ja","lang_name":"日本語","sequence":2}],
            "selected":"en"}
        result = get_selected_language()
        assert result == test
        with patch("weko_admin.utils.AdminLangSettings.get_registered_language",return_value=None):
            result = get_selected_language()
            assert result == {"lang":"", "selected":""}


# def get_api_certification_type():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_api_certification_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_api_certification_type(api_certificate):
    result = get_api_certification_type()
    assert result == [{"api_code":"crf","api_name":"CrossRef"}]
    
    with patch("weko_admin.utils.ApiCertificate.select_all",side_effect=Exception("test_error")):
        result = get_api_certification_type()
        assert result == "test_error"


# def get_current_api_certification(api_code):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_current_api_certification -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_current_api_certification(api_certificate):
    test = {"api_code":"crf","api_name":"CrossRef","cert_data":"test.test@test.org"}
    result = get_current_api_certification("crf")
    assert result == test
    
    with patch("weko_admin.utils.ApiCertificate.select_by_api_code",side_effect=Exception("test_error")):
        result = get_current_api_certification("crf")
        assert result == "test_error"


# def save_api_certification(api_code, cert_data):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_save_api_certification -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_save_api_certification(api_certificate):
    # not cert_data
    result = save_api_certification("","")
    assert result == {"results":"","error":"Account information is invalid. Please check again."}
    
    # cert_data, api_certificate
    result = save_api_certification("crf","test.test2@test.org")
    assert result == {"results":True,"error":""}
    
    # cert_data, not api_certificate
    result = save_api_certification("nii","test.test2@test.org")
    assert result == {"results":"","error":"Input type is invalid. Please check again."}
    
    # raise Exception
    with patch("weko_admin.utils.ApiCertificate.select_by_api_code",side_effect=Exception("test_error")):
        result = save_api_certification("crf","test.test2@test.org")
        assert result == {"results":"","error":"test_error"}


# def create_crossref_url(pid):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_create_crossref_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_create_crossref_url():
    with pytest.raises(ValueError) as e:
        create_crossref_url(None)
        assert str(e) == "PID is required"
    
    result = create_crossref_url("test_pid")
    assert result == "https://doi.crossref.org/openurl?pid=test_pid&id=doi:10.1047/0003-066X.59.1.29&format=json"


# def validate_certification(cert_data):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_validate_certification -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_validate_certification():
    from requests.models import Response
    mock_res = Response()
    mock_res._content = "test response content"
    with patch("weko_admin.utils.requests.get",return_value=mock_res):
        result = validate_certification("test_data")
        assert result == True


# def get_initial_stats_report():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_initial_stats_report -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_initial_stats_report(statistic_target):
    test = {"target":[
        {"id":"1","data":"Item registration report"},
        {"id":"2","data":"Item detail view report"},
        {"id":"3","data":"Contents download report"}]}
    result = get_initial_stats_report()
    assert result == test


# def get_unit_stats_report(target_id):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_unit_stats_report -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_unit_stats_report(statistic_target, statistic_unit):
    result = get_unit_stats_report("1")
    assert result == {"unit":[{"data":"Day","id":"1"},{"data":"Week","id":"2"},{"data":"Year","id":"3"},{"data":"Host","id":"5"}]}


# def get_user_report_data():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_user_report_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_user_report_data(users):
    with patch("weko_admin.utils.func.count", side_effect=Exception("test_error")):
        result = get_user_report_data()
        assert result == {}
    test = {
        "all":[
            {"role_name":"System Administrator","count":1},
            {"role_name":"Repository Administrator","count":2},
            {"role_name":"Contributor","count":1},
            {"role_name":"Community Administrator","count":1},
            {"role_name":"General","count":1},
            {"role_name":"Original Role","count":2},
            {"role_name":"Student","count":1},
            {"role_name":"Registered Users","count":9}
        ],
    }
    result = get_user_report_data()
    assert result == test


# def package_reports(all_stats, year, month):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_package_reports -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_package_reports(client,mocker):
    mock_stream = StringIO()
    mock_stream.write("test")
    mocker.patch("weko_admin.utils.make_stats_file",return_value=mock_stream)
    all_stats = {
        "file_download":"test_stats"
    }
    result = package_reports(all_stats,"2022","10")

    # raise Exception
    mocker.patch("weko_admin.utils.make_stats_file",side_effect=Exception("test_error"))
    with pytest.raises(Exception) as e:
        result = package_reports(all_stats,"2022","10")

# def make_stats_file(raw_stats, file_type, year, month):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_make_stats_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_make_stats_file(client,mocker):
    current_app.config.update(WEKO_ADMIN_OUTPUT_FORMAT="csv")
    mocker.patch("weko_admin.utils.write_report_file_rows")
    raw_stats=""
    file_type = ""
    year = "2022"
    month = "10"

    # filetype = index_access
    file_type = "index_access"
    raw_stats={"total":10}
    test = \
        'Detail Views Per Index\n'\
        'Aggregation Month,2022-10\n'\
        '""\n'\
        'Detail Views Per Index\n'\
        'Index,No. Of Views\n'\
        'Total Detail Views,10\n'
    result = make_stats_file(raw_stats,file_type,year,month)
    assert result.getvalue() == test
    
    # filetype = billing_file_download
    file_type = "billing_file_download"
    raw_stats={"all_groups":["test_group"]}
    test = \
        'No. Of Paid File Downloads\n'\
        'Aggregation Month,2022-10\n'\
        '""\n'\
        'No. Of Paid File Downloads\n'\
        'File Name,Registered Index Name,No. Of Times Downloaded,test_group,Non-Logged In User,Logged In User,Site License,Admin,Registrar\n'
    result = make_stats_file(raw_stats,file_type,year,month)
    assert result.getvalue() == test
    
    # filetype = site_access
    ## open_access in raw_stats
    file_type = "site_access"
    raw_stats={"open_access":"test_open_access"}
    test = \
        'Access Count By Site License\n'\
        'Aggregation Month,2022-10\n'\
        '""\n'\
        'Access Count By Site License\n'\
        'WEKO Top Page Access Count,Number Of Searches,Number Of Views,Number Of File download,Number Of File Regeneration\n'\
        '""\n'\
        'Access Number Breakdown By Site License\n'\
        'WEKO Top Page Access Count,Number Of Searches,Number Of Views,Number Of File download,Number Of File Regeneration\n'
    result = make_stats_file(raw_stats,file_type,year,month)
    assert result.getvalue() == test
    
    ## institution_name in raw_stats
    file_type = "site_access"
    raw_stats={"institution_name":"test_institution_name"}
    test = \
        'Access Count By Site License\n'\
        'Aggregation Month,2022-10\n'\
        '""\n'\
        'Access Count By Site License\n'\
        'WEKO Top Page Access Count,Number Of Searches,Number Of Views,Number Of File download,Number Of File Regeneration\n'\
        '""\n'\
        'Access Number Breakdown By Site License\n'\
        'Institution Name,WEKO Top Page Access Count,Number Of Searches,Number Of Views,Number Of File download,Number Of File Regeneration\n'
    result = make_stats_file(raw_stats,file_type,year,month)
    assert result.getvalue() == test
    
    ## open_access not in raw_stats,institution_name not in raw_stats
    file_type = "site_access"
    raw_stats={"other_raw":"test_institution_name"}
    test = \
        'Access Count By Site License\n'\
        'Aggregation Month,2022-10\n'\
        '""\n'\
        'Access Count By Site License\n'\
        'WEKO Top Page Access Count,Number Of Searches,Number Of Views,Number Of File download,Number Of File Regeneration\n'\
        '""\n'\
        'Access Number Breakdown By Site License\n'
    result = make_stats_file(raw_stats,file_type,year,month)
    assert result.getvalue() == test
    
    # filetype = other
    file_type = "detail_view"
    raw_stats={}
    test = \
        'Detail Views Count\n'\
        'Aggregation Month,2022-10\n'\
        '""\n'\
        'Detail Views Count\n'\
        'Title,Registered Index Name,View Count,Non-logged-in User\n'
    result = make_stats_file(raw_stats,file_type,year,month)
    assert result.getvalue() == test


# def write_report_file_rows(writer, records, file_type=None, other_info=None):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_write_report_file_rows -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_write_report_file_rows(db,users):
    record={}
    file_type=""
    other_info=""
    
    # records is None
    output = StringIO()
    writer = csv.writer(output,delimiter=",",lineterminator="\n")
    result = write_report_file_rows(writer,None)
    assert result == None
    
    # filetype is None
    output = StringIO()
    writer = csv.writer(output,delimiter=",",lineterminator="\n")
    record = [{"file_key":"test_file_key","index_list":"test_index_list","total":1,"no_login":"True","login":"False","site_license":"test_site_license","admin":"False","reg":"test_reg"}]
    write_report_file_rows(writer,record)
    assert output.getvalue() == "test_file_key,test_index_list,1,True,False,test_site_license,False,test_reg\n"
    
    # filetype is billiing_file_download
    output = StringIO()
    writer = csv.writer(output,delimiter=",",lineterminator="\n")
    record = {
        "record1": {"file_key":"test_file_key1",
               "index_list":"test_index_list1",
               "total":1,"no_login":"True",
               "login":"False",
               "site_license":"test_site_license1",
               "admin":"False","reg":"test_reg1"},
        "record2": {"file_key":"test_file_key2",
               "index_list":"test_index_list2",
               "total":1,"no_login":"True",
               "login":"False",
               "site_license":"test_site_license2",
               "admin":"False","reg":"test_reg2",
               "group_counts":{"test_group":10}}
    }
    other_info = ["test_group"]
    write_report_file_rows(writer,record,"billing_file_download",other_info)
    assert output.getvalue() == "test_file_key1,test_index_list1,1,True,False,test_site_license1,False,test_reg1\n"\
                                "test_file_key2,test_index_list2,1,10,True,False,test_site_license2,False,test_reg2\n"
    # filetype is index_access
    record = [{"index_name":"test_index","view_count":"10"}]
    output = StringIO()
    writer = csv.writer(output,delimiter=",",lineterminator="\n")
    write_report_file_rows(writer,record,"index_access")
    assert output.getvalue() == "test_index,10\n"
    
    # filetype is search_count
    record = [{"search_key":"test_search_key","count":"10"}]
    output = StringIO()
    writer = csv.writer(output,delimiter=",",lineterminator="\n")
    write_report_file_rows(writer,record,"search_count")
    assert output.getvalue() == "test_search_key,10\n"
    
    # filetype is user_roles
    record = [{"role_name":"test_role","count":"10"}]
    output = StringIO()
    writer = csv.writer(output,delimiter=",",lineterminator="\n")
    write_report_file_rows(writer,record,"user_roles")
    assert output.getvalue() == "test_role,10\n"
    
    # filetype is detail_view
    item_id = uuid.uuid4()
    ItemsMetadata.create({"title": ["title"]},item_id)
    record = [{"record_id":item_id,"index_names":"test_index","total_all":"10","total_not_login":"5"}]
    output = StringIO()
    writer = csv.writer(output,delimiter=",",lineterminator="\n")
    write_report_file_rows(writer,record,"detail_view")
    assert output.getvalue() == "['title'],test_index,10,5\n"
    
    # filetype is file_using_per_user
    userprofile = UserProfile(user_id=1,_displayname="test smith")
    db.session.add(userprofile)
    db.session.commit()
    record = [{"cur_user_id":"0","total_download":"10","total_preview":"5"},
              {"cur_user_id":"1","total_download":"10","total_preview":"5"}]
    output = StringIO()
    writer = csv.writer(output,delimiter=",",lineterminator="\n")
    write_report_file_rows(writer,record,"file_using_per_user")
    assert output.getvalue() == ",Guest,10,5\n"\
                                "user@test.org,,10,5\n"
    
    # filetype is top_page_access
    record = [{"host":"test_host","ip":"123.456.789","count":"10"}]
    output = StringIO()
    writer = csv.writer(output,delimiter=",",lineterminator="\n")
    write_report_file_rows(writer,record,"top_page_access")
    assert output.getvalue() == "test_host,123.456.789,10\n"
    
    # filetype is site_access
    ## other_info
    record = [{"top_view":"test_top_view","search":"test_search","record_view":"test_record_view","file_download":"test_file_download","file_preview":"test_file_preview"}]
    output = StringIO()
    writer = csv.writer(output,delimiter=",",lineterminator="\n")
    write_report_file_rows(writer,record,"site_access","test_other_info")
    assert output.getvalue() == "test_other_info,test_top_view,test_search,test_record_view,test_file_download,test_file_preview\n"
    
    # filetype is others
    record = [{"top_view":"test_top_view","search":"test_search","record_view":"test_record_view","file_download":"test_file_download","file_preview":"test_file_preview"}]
    output = StringIO()
    writer = csv.writer(output,delimiter=",",lineterminator="\n")
    write_report_file_rows(writer,record,"others","test_other_info")
    assert output.getvalue() == ""
    
    ## not other_info
    record = [{"name":"test_name","top_view":"test_top_view","search":"test_search","record_view":"test_record_view","file_download":"test_file_download","file_preview":"test_file_preview"}]
    output = StringIO()
    writer = csv.writer(output,delimiter=",",lineterminator="\n")
    write_report_file_rows(writer,record,"site_access")
    assert output.getvalue() == "test_name,test_top_view,test_search,test_record_view,test_file_download,test_file_preview\n"
    


# def reset_redis_cache(cache_key, value, ttl=None):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_reset_redis_cache -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_reset_redis_cache(redis_connect,mocker):
    redis_connect.put("test_cache",bytes("test_value","utf-8"))
    mocker.patch("weko_admin.utils.RedisConnection.connection",return_value=redis_connect)
    # cache_key exist, ttl is None
    reset_redis_cache("test_cache","new_value1")
    assert redis_connect.get("test_cache") == b"new_value1"
    # cache_key not exist, ttl is not None
    redis_connect.delete("test_cache")
    reset_redis_cache("test_cache","new_value2",10)
    assert redis_connect.get("test_cache") == b"new_value2"

    # raise Exception
    with mocker.patch("weko_admin.utils.RedisConnection.connection",side_effect=Exception("test_error")):
        with pytest.raises(Exception):
            reset_redis_cache("test_cache","")


# def is_exists_key_in_redis(key):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_is_exists_key_in_redis -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_is_exists_key_in_redis(redis_connect,mocker):
    mocker.patch("weko_admin.utils.RedisConnection.connection",return_value=redis_connect)
    redis_connect.put("test_key",bytes("test_value","utf-8"))
    result = is_exists_key_in_redis("test_key")
    assert result == True
    
    # raise Exception
    with patch("weko_admin.utils.RedisConnection.connection", side_effect=Exception("test_error")):
        result = is_exists_key_in_redis("test_key")
        assert result == False


# def is_exists_key_or_empty_in_redis(key):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_is_exists_key_or_empty_in_redis -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_is_exists_key_or_empty_in_redis(redis_connect,mocker):
    mocker.patch("weko_admin.utils.RedisConnection.connection",return_value=redis_connect)
    redis_connect.put("test_key1",bytes("test_value1","utf-8"))
    result = is_exists_key_or_empty_in_redis("test_key1")
    assert result == True
    
    redis_connect.put("test_key2",bytes("","utf-8"))
    result = is_exists_key_or_empty_in_redis("test_key2")
    assert result == False
    
    # raise Exception
    with patch("weko_admin.utils.RedisConnection.connection", side_effect=Exception("test_error")):
        result = is_exists_key_or_empty_in_redis("test_key1")
        assert result == False


# def get_redis_cache(cache_key):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_redis_cache -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_redis_cache(redis_connect,mocker):
    mocker.patch("weko_admin.utils.RedisConnection.connection",return_value=redis_connect)
    redis_connect.delete("test_key")
    # cache_key is not exist
    result = get_redis_cache("test_key")
    assert result == None
    
    # cache_key is exist
    redis_connect.put("test_key",bytes("test_value","utf-8"))
    result = get_redis_cache("test_key")
    assert result == "test_value"
    
    # raise Exception
    with patch("weko_admin.utils.RedisConnection.connection", side_effect=Exception("test_error")):
        result = get_redis_cache("test_key")
        assert result == None

# def get_system_default_language():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_system_default_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_system_default_language(language_setting):
    result = get_system_default_language()
    assert result == "en"
    
    with patch("weko_admin.utils.AdminLangSettings.get_registered_language",return_value=None):
        result = get_system_default_language()
        assert result == "en"


# class StatisticMail
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestStatisticMail:

#     def get_send_time(cls):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail::test_get_send_time -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_send_time(self):
        test = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        result = StatisticMail.get_send_time()
        
        assert result == test


#     def send_mail_to_all(cls, list_mail_data=None, stats_date=None):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail::test_send_mail_to_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_send_mail_to_all(self,client,feedback_mail_settings,site_info,mocker):
        setting = {
                "data":[{"author_id":"2","email":"banned@test.org"}],
                "error":"",
                "is_sending_feedback":True,
                "root_url":"http://test_server"
            }
        mocker.patch("weko_admin.utils.FeedbackMail.get_feed_back_email_setting",return_value=setting)
        mocker.patch("weko_admin.utils.StatisticMail.get_banned_mail",return_value=["banned@test.org"])
        mocker.patch("weko_admin.utils.StatisticMail.get_send_time",return_value="2022-10")
        mocker.patch("weko_admin.utils.StatisticMail.get_list_statistic_data")
        mocker.patch("weko_admin.utils.FeedbackMailHistory.get_sequence",return_value="1")
        body = {
            "user_name":"テスト 太郎",
            "organization":"No Site Name",
            "time":"2022-10",
            "data":"----------------------------------------\n[Title] : title2\n[URL] : http://test.com/records/2\n[DetailView] : 3\n[FileDownload] : \n    test_file2_1.tsv(10)\n    test_file2_2.tsv(20)\n",
            "total_item":1,
            "total_file":2,
            "total_detail_view":3,
            "total_download":30
        }
        mocker.patch("weko_admin.utils.StatisticMail.fill_email_data",return_value=body)
        mocker.patch("weko_admin.utils.StatisticMail.send_mail",return_value=True)
        mocker.patch("weko_admin.utils.get_system_default_language",return_value="en")
        mocker.patch("weko_admin.utils.StatisticMail.build_statistic_mail_subject",return_value="[No Site Name]2022-10 利用統計レポート")
        
        # is_sending_feedback is False, stats_date is None
        with patch("weko_admin.utils.FeedbackMail.get_feed_back_email_setting",return_value={"is_sending_feedback":False}):
            result = StatisticMail.send_mail_to_all(None,None)
            assert result == None
            
        # list_mail_data is None, get_feedback_mail_list is None
        with patch("weko_search_ui.utils.get_feedback_mail_list", return_value=None):
            result = StatisticMail.send_mail_to_all(None,None)
            assert result == None
        
        mail_data = {
            "banned@test.org":{},
            "test.taro@test.org":{"author_id":"1","items":{}},
            "test.hanako@test.org":{"author_id":"2","items":{}}
        }
        mocker.patch("weko_search_ui.utils.get_feedback_mail_list", return_value=mail_data)
        # system_default_language is ja
        with patch("weko_admin.utils.get_system_default_language", return_value="ja"):
            result = StatisticMail.send_mail_to_all(None,"2022-11")
        # system_default_language is other
        with patch("weko_admin.utils.get_system_default_language", return_value="du"):
            result = StatisticMail.send_mail_to_all(None,"2022-11")
        
        # system_default_language is en
        # host_url[-1] is "/"
        current_app.config.update(THEME_SITEURL="https://localhost/")
        result = StatisticMail.send_mail_to_all(None,"2022-11")
        
        with patch("weko_admin.utils.StatisticMail.send_mail", side_effect=[True, False]):
            StatisticMail.send_mail_to_all(mail_data,"2022-11")
        
        with patch("weko_admin.utils.StatisticMail.build_statistic_mail_subject", side_effect=Exception("test_error")):
            StatisticMail.send_mail_to_all(mail_data,"2022-11")


#     def get_banned_mail(cls, list_banned_mail):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail::test_get_banned_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_banned_mail(self):
        list_banned_mail = []
        result = StatisticMail.get_banned_mail(list_banned_mail)
        assert result == []
        
        list_banned_mail = [{"email":"test1@test.org"},{"email":"test2@test.org"}]
        result = StatisticMail.get_banned_mail(list_banned_mail)
        assert result == ["test1@test.org","test2@test.org"]


#     def convert_download_count_to_int(cls, download_count):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail::test_convert_download_count_to_int -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_convert_download_count_to_int(self,app):
        download_count = "10"
        result = StatisticMail.convert_download_count_to_int(download_count)
        assert result == 10
        
        download_count = "12.234"
        result = StatisticMail.convert_download_count_to_int(download_count)
        assert result == 12
        
        # raise Exception
        download_count = "test.1"
        result = StatisticMail.convert_download_count_to_int(download_count)
        assert result == 0


#     def get_list_statistic_data(cls, list_item_id, time, root_url):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail::test_get_list_statistic_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_list_statistic_data(self,records,mocker):
        list_item_id=[records[0][2].id,records[1][2].id]
        time = datetime.now().strftime("%Y-%m")
        root_url = "http://test.com"
        
        item_info = [{
                "title":"title",
                "url":"http://test.com/records/1",
                "detail_view":"2",
                "file_download":{"test_file.tsv":"10"}
            },
            {
                "title":"title2",
                "url":"http://test.com/records/2",
                "detail_view":"3",
                "file_download":{"test_file2_1.tsv":"10","test_file2_2.tsv":"20"}
            }
        ]
        mocker.patch("weko_admin.utils.StatisticMail.get_item_information",side_effect=item_info)
        mocker.patch("weko_admin.utils.StatisticMail.convert_download_count_to_int",side_effect=lambda x:int(x))
        
        test = {
            "data": [
                {
                    "title":"title",
                    "url":"http://test.com/records/1",
                    "detail_view":"2",
                    "file_download":["test_file.tsv(10)"]
                },
                {
                    "title":"title2",
                    "url":"http://test.com/records/2",
                    "detail_view":"3",
                    "file_download":["test_file2_1.tsv(10)","test_file2_2.tsv(20)"]
                }
            ],
            "summary": {
                "total_item":2,
                "total_files":3,
                "total_view":5,
                "total_download":40
            }
        }
        result = StatisticMail.get_list_statistic_data(list_item_id, time, root_url)
        assert result == test


#     def get_item_information(cls, item_id, time, root_url):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail::test_get_item_information -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_item_information(self,records,mocker):
        item_id = records[0][2].id
        time = datetime.now().strftime("%Y-%m")
        root_url = "http://test.com"
        
        mocker.patch("weko_admin.utils.StatisticMail.get_item_view",return_value="2")
        mocker.patch("weko_admin.utils.StatisticMail.get_item_download",return_value={"test_file.tsv":"10"})
        test = {
            "title":"title",
            "url":"http://test.com/records/1",
            "detail_view":"2",
            "file_download":{"test_file.tsv":"10"}
        }
        result = StatisticMail.get_item_information(item_id,time,root_url)
        assert result == test

#     def get_item_view(cls, item_id, time):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail::test_get_item_view -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_item_view(self,records,mocker):
        mocker.patch("weko_admin.utils.QueryRecordViewCount.get_data",return_value={"total":1,"country":{},"period":[]})
        item_id = records[0][0].object_uuid
        time = datetime.now().strftime("%Y-%m")
        result = StatisticMail.get_item_view(item_id,time)
        assert result == "1"


#     def get_item_download(cls, data, time):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail::test_get_item_download -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_item_download(self,mocker):
        with patch("weko_admin.utils.StatisticMail.get_file_in_item",return_value=None):
            result = StatisticMail.get_item_download("","")
            assert result == {}
        mocker.patch("weko_admin.utils.StatisticMail.get_file_in_item",return_value={"list_file_key":["test_file1","test_file2"]})
        mocker.patch("weko_admin.utils.QueryFileStatsCount.get_data",return_value={"download_total":10})
        time = datetime.now().strftime("%Y-%m")
        data = {}
        result = StatisticMail.get_item_download(data,time)
        assert result == {"test_file1":"10","test_file2":"10"}


#     def find_value_in_dict(cls, key, data):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail::test_find_value_in_dict -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_find_value_in_dict(self):
        data = {
            "data1":[
                "test",
                {"not_find_key":"not_find_value","find_key":"find_value1"},
                {"not_find_key":"not_find_value","find_key":"find_value2"}
            ],
            "data2":{
                "find_key":"find_value3"
            }
        }
        result = StatisticMail.find_value_in_dict("find_key",data)
        
        for i,r in enumerate(result):
            if i==0:
                assert r == "find_value1"
            elif i==1:
                assert r == "find_value2"
            elif i==3:
                assert r == "find_value3"


#     def get_file_in_item(cls, data):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail::test_get_file_in_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_file_in_item(self,mocker):
        data = {
            "_buckets":{"deposit":"test_deposit_id"}
        }
        def mock_find_value(key,data):
            keys = ["test_key1","test_key2"]
            for _key in keys:
                yield _key
        mocker.patch("weko_admin.utils.StatisticMail.find_value_in_dict",side_effect=mock_find_value)
        
        result = StatisticMail.get_file_in_item(data)
        assert result == {"bucket_id":"test_deposit_id","list_file_key":["test_key1","test_key2"]}



#     def fill_email_data(cls, statistic_data, mail_data,
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail::test_fill_email_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_fill_email_data(self,mocker):
        statistic_data = {
            "data":[{
                    "title":"title2",
                    "url":"http://test.com/records/2",
                    "detail_view":"3",
                    "file_download":["test_file2_1.tsv(10)","test_file2_2.tsv(20)"]
                }],
            "summary": {
                "total_item":1,
                "total_files":2,
                "total_view":3,
                "total_download":30
            }
        }
        mail_data = {
            "user_name":"テスト 太郎",
            "organization":"No Site Name",
            "time":"2022-10"
        }
        
        # system_default_language is ja
        data_content_ja = '----------------------------------------\n[Title] : title2\n[URL] : http://test.com/records/2\n[DetailView] : 3\n[FileDownload] : \n    test_file2_1.tsv(10)\n    test_file2_2.tsv(20)\n'
        mocker.patch("weko_admin.utils.StatisticMail.build_mail_data_to_string",return_value=data_content_ja)
        mock_render = mocker.patch("weko_admin.utils.Template.render")
        test = {
            "user_name":"テスト 太郎",
            "organization":"No Site Name",
            "time":"2022-10",
            "data":data_content_ja,
            "total_item":1,
            "total_file":2,
            "total_detail_view":3,
            "total_download":30
        }
        StatisticMail.fill_email_data(statistic_data,mail_data,"ja")
        mock_render.assert_called_with(test)
        
        # system_default_language is en
        data_content_en = '----------------------------------------\n[Title] : title2\n[URL] : http://test.com/records/2\n[DetailView] : 3\n[FileDownload] : \n    test_file2_1.tsv(10)\n    test_file2_2.tsv(20)\n'
        mocker.patch("weko_admin.utils.StatisticMail.build_mail_data_to_string",return_value=data_content_en)
        mock_render = mocker.patch("weko_admin.utils.Template.render")
        test = {
            "user_name":"テスト 太郎",
            "organization":"No Site Name",
            "time":"2022-10",
            "data":data_content_en,
            "total_item":1,
            "total_file":2,
            "total_detail_view":3,
            "total_download":30
        }
        StatisticMail.fill_email_data(statistic_data,mail_data,"en")
        mock_render.assert_called_with(test)
        
        # system_default_language is other
        data_content_en = '----------------------------------------\n[Title] : title2\n[URL] : http://test.com/records/2\n[DetailView] : 3\n[FileDownload] : \n    test_file2_1.tsv(10)\n    test_file2_2.tsv(20)\n'
        mocker.patch("weko_admin.utils.StatisticMail.build_mail_data_to_string",return_value=data_content_en)
        mock_render = mocker.patch("weko_admin.utils.Template.render")
        test = {
            "user_name":"テスト 太郎",
            "organization":"No Site Name",
            "time":"2022-10",
            "data":data_content_en,
            "total_item":1,
            "total_file":2,
            "total_detail_view":3,
            "total_download":30
        }
        StatisticMail.fill_email_data(statistic_data,mail_data,"du")
        mock_render.assert_called_with(test)


#     def send_mail(cls, recipient, body, subject):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail::test_send_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_send_mail(self,client,mocker):
        recipient = "test@test.org"
        body = {
            "user_name":"テスト 太郎",
            "organization":"No Site Name",
            "time":"2022-10",
            "data":"----------------------------------------\n[Title] : title2\n[URL] : http://test.com/records/2\n[DetailView] : 3\n[FileDownload] : \n    test_file2_1.tsv(10)\n    test_file2_2.tsv(20)\n",
            "total_item":1,
            "total_file":2,
            "total_detail_view":3,
            "total_download":30
        }
        body = str(body)
        subject = "[No Site Name]2022-10 利用統計レポート"
        
        mock_send = mocker.patch("weko_admin.utils.MailSettingView.send_statistic_mail",return_value=True)
        test = {
            "subject":subject,
            "body":body,
            "recipient":recipient
        }
        result = StatisticMail.send_mail(recipient,body,subject)
        mock_send.assert_called_with(test)


#     def build_statistic_mail_subject(cls, title, send_date,
#                                      system_default_language):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail::test_build_statistic_mail_subject -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_build_statistic_mail_subject(self):
        title = "No Site Name"
        send_date = "2022-10"
        
        # language = ja
        result = StatisticMail.build_statistic_mail_subject(title,send_date,"ja")
        assert result == "[No Site Name]2022-10 利用統計レポート"

        # language = en
        result = StatisticMail.build_statistic_mail_subject(title,send_date,"en")
        assert result == "[No Site Name]2022-10 Usage Statistics Report"

        # language = others
        result = StatisticMail.build_statistic_mail_subject(title,send_date,"zf")
        assert result == "[No Site Name]2022-10 Usage Statistics Report"

#     def build_mail_data_to_string(cls, data, system_default_language):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail::test_build_mail_data_to_string -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_build_mail_data_to_string(self,):
        data = []

        # not data
        result = StatisticMail.build_mail_data_to_string(data,"en")
        assert result == ""
        
        data =  [{
                    "title":"title2",
                    "url":"http://test.com/records/2",
                    "detail_view":"3",
                    "file_download":["test_file2_1.tsv(10)","test_file2_2.tsv(20)"]
                }]
        
        # language = ja
        test = \
            '----------------------------------------\n'\
            '[タイトル] : title2\n'\
            '[URL] : http://test.com/records/2\n'\
            '[閲覧回数] : 3\n'\
            '[ファイルダウンロード回数] :     test_file2_1.tsv(10)\n'\
            '    test_file2_2.tsv(20)\n'
        result = StatisticMail.build_mail_data_to_string(data,"ja")
        assert result == test
        
        # language is not ja
        test = \
            '----------------------------------------\n'\
            '[Title] : title2\n'\
            '[URL] : http://test.com/records/2\n'\
            '[DetailView] : 3\n'\
            '[FileDownload] : \n'\
            '    test_file2_1.tsv(10)\n'\
            '    test_file2_2.tsv(20)\n'
        result = StatisticMail.build_mail_data_to_string(data,"en")
        assert result == test

#     def get_author_name(cls, mail, author_id):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestStatisticMail::test_get_author_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_author_name(self,authors):
        mail = "test@test.org"
        result = StatisticMail.get_author_name(mail,None)
        assert result == mail
        
        result = StatisticMail.get_author_name(mail,"not_exist_author")
        assert result == mail
        
        result = StatisticMail.get_author_name(mail,authors[1].id)
        assert result == mail
        
        result = StatisticMail.get_author_name(mail,authors[0].id)
        assert result == "テスト 太郎"


# def str_to_bool(str):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_str_to_bool -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_str_to_bool():
    result = str_to_bool("true")
    assert result == True
    result = str_to_bool("f")
    assert result == False
    
class MockClient:
    def __init__(self,author_data):
        self.data = author_data
    
    def search(self,index=None,doc_type=None,body=None):
        if index == "test_weko-authors":
            return {
                "hits":{
                    "hits":[{"_source": d} for d in self.data]
                },
                "item_cnt":3
            }
        elif index == "test-weko":
            return {"item_cnt":3}
# class FeedbackMail:
class TestFeedbackMail:
#     def search_author_mail(cls, request_data: dict) -> dict:
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_search_author_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_search_author_mail(self,client,mocker):
        mock_indexer = RecordIndexer()
        data = json_data("data/test_authors.json")
        data.append({"authorIdInfo":None})
        mock_indexer.client=MockClient(data)
        mocker.patch("weko_admin.utils.RecordIndexer",return_value=mock_indexer)
        
        request_data = {
            "searchKey":"",
            "numOfPage":"10",
            "pageNumber":"1"
        }
        author_data = json_data("data/test_authors.json")
        author_data.append({"authorIdInfo":None})
        test = {
            "hits":{"hits":[{"_source":d} for d in author_data]},
            "item_cnt":{"item_cnt":3}
        }
        # not exist search_key
        result = FeedbackMail.search_author_mail(request_data)
        assert result == test
        
        # exist search_key
        request_data = {
            "searchKey":"test_key",
            "numOfPage":"10",
            "pageNumber":"1"
        }
        result = FeedbackMail.search_author_mail(request_data)
        assert result == test
#     def get_feed_back_email_setting(cls):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_get_feed_back_email_setting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_feed_back_email_setting(self, feedback_mail_settings):
        
        # len(setting) = 0
        with patch("weko_admin.utils.FeedbackMailSetting.get_all_feedback_email_setting",return_value=[]):
            result = FeedbackMail.get_feed_back_email_setting()
            assert result == {"data":"","is_sending_feedback":"","root_url":"","error":""}
        
        # not exist manual_email
        with patch("weko_admin.utils.FeedbackMailSetting.get_all_feedback_email_setting",return_value=[feedback_mail_settings[1]]):
            test = {
                "data":[{"author_id":"2","email":None}],
                "error":"",
                "is_sending_feedback":True,
                "root_url":"http://test_server"
            }
            result = FeedbackMail.get_feed_back_email_setting()
            assert result == test
        
        # exist manual_email
        test = {
                "data":[{"author_id":"1","email":"test.taro@test.org"},
                        {"author_id":"2","email":None},
                        {"author_id":"","email":"test.manual1@test.org"},
                        {"author_id":"","email":"test.manual2@test.org"}],
                "error":"",
                "is_sending_feedback":True,
                "root_url":"http://test_server"
            }
        result = FeedbackMail.get_feed_back_email_setting()
        assert result == test


#     def update_feedback_email_setting(cls, data,
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_update_feedback_email_setting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_update_feedback_email_setting(self,feedback_mail_settings,mocker):
        mocker.patch("weko_admin.utils.FeedbackMail.handle_update_message",return_value={"error":""})
        mocker.patch("weko_admin.utils.FeedbackMail.validate_feedback_mail_setting",return_value=None)
        mocker.patch("weko_admin.utils.FeedbackMail.get_list_manual_email",return_value={"email":["test.manual@test.org"]})
        mocker.patch("weko_admin.utils.FeedbackMail.convert_feedback_email_data_to_string",return_value="1,2")
        data = [
            { "author_id": "1", "email": "test.taro@test.org" },
            { "author_id": "2", "email": "test.smith@test.org" },
            { "author_id": "", "email": "test.manual@test.org" }
        ]
        is_sending_feedback = True
        root_url = "http://test_server"
        
        # exist error_message
        with patch("weko_admin.utils.FeedbackMail.validate_feedback_mail_setting",return_value="Duplicate Email Addresses."):
            result = FeedbackMail.update_feedback_email_setting(data,is_sending_feedback,root_url)
            assert result == {"error":"Duplicate Email Addresses."}
        
        # len(current_setting) == 0
        with patch("weko_admin.utils.FeedbackMailSetting.get_all_feedback_email_setting",return_value=[]):
            result = FeedbackMail.update_feedback_email_setting(data,is_sending_feedback,root_url)
            assert result == {"error":""}

        result = FeedbackMail.update_feedback_email_setting(data,is_sending_feedback,root_url)
        assert result == {"error":""}
        
        result = FeedbackMail.update_feedback_email_setting(None,False,root_url)
        assert result == {"error":""}

        
#     def convert_feedback_email_data_to_string(cls, data, keyword='author_id'):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_convert_feedback_email_data_to_string -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_convert_feedback_email_data_to_string(self):
        # data is not list
        result = FeedbackMail.convert_feedback_email_data_to_string("not list")
        assert result == None
        
        data = [
            { "author_id": "1", "email": "test.taro@test.org" },
            { "author_id": "2", "email": "test.smith@test.org" },
            { "email": "not.author_id@test.org"}
        ]
        result = FeedbackMail.convert_feedback_email_data_to_string(data)
        assert result == "1,2"


#     def get_list_manual_email(cls, data):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_get_list_manual_email -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_list_manual_email(self,client):
        result = FeedbackMail.get_list_manual_email("not list")
        assert result == None
        
        data = [
            { "author_id": "1", "email": "test.taro@test.org" },
            { "author_id": "", "email": "test.manual@test.org" }
        ]
        result = FeedbackMail.get_list_manual_email(data)
        assert result == {"email":["test.manual@test.org"]}


#     def handle_update_message(cls, result, success):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_handle_update_message -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_handle_update_message(self):
        result = FeedbackMail.handle_update_message({"key":"value","error":""},True)
        assert result == {"key":"value","error":""}
        
        result = FeedbackMail.handle_update_message({"key":"value"},False)
        assert result == {"key":"value","error":"Cannot update Feedback email settings."}


#     def validate_feedback_mail_setting(cls, data):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_validate_feedback_mail_setting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_validate_feedback_mail_setting(self,mocker):
        data = [
            { "author_id": "1", "email": "test.taro@test.org" },
            { "author_id": "2", "email": "test.smith@test.org" }
        ]
        # author is duplicated
        mocker.patch("weko_admin.utils.FeedbackMail.convert_feedback_email_data_to_string",return_value="1,1")
        result = FeedbackMail.validate_feedback_mail_setting(data)
        assert result == "Author is duplicated."
        
        # duplicate email
        mocker.patch("weko_admin.utils.FeedbackMail.convert_feedback_email_data_to_string",side_effect=["1,2","test@test.org,test@test.org"])
        result = FeedbackMail.validate_feedback_mail_setting(data)
        assert result == "Duplicate Email Addresses."
        
        mocker.patch("weko_admin.utils.FeedbackMail.convert_feedback_email_data_to_string",side_effect=["1,2","test.taro@test.org,test.smith@test.org"])
        result = FeedbackMail.validate_feedback_mail_setting(data)
        assert result == None


#     def load_feedback_mail_history(cls, page_num):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_load_feedback_mail_history -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_load_feedback_mail_history(self,db,feedback_mail_histories):
        # page_num_start > len(all_history)
        with patch("weko_admin.utils.FeedbackMailHistory.get_all_history",return_value = ["test_history1"]):
            test = {
                'data': [],
                'total_page': 0,
                'selected_page': 0,
                'records_per_page': 0,
                'error': 'Cannot get data. Detail: Page out of range'
            }
            result = FeedbackMail.load_feedback_mail_history(20)
            assert result == test
        
        test = {
            "data":[
                {"start_time":"2022-10-01 01:02:03.045","end_time":"2022-10-01 02:03:04.056","count":2,"error":0,"id":2,"is_latest":True,"success":2},
                {"start_time":"2022-10-01 01:02:03.045","end_time":"2022-10-01 02:03:04.056","count":2,"error":0,"id":1,"is_latest":True,"success":2}],
            "error":"",
            "records_per_page":20,
            "selected_page":1,
            "total_page":1
        }
        result = FeedbackMail.load_feedback_mail_history(1)
        assert result ==test
        
        # not path break
        history_data = []
        for i in range(len(feedback_mail_histories),41):
            history_data.append(
                FeedbackMailHistory(
                    start_time=datetime(2022,10,1,1,2,3,45678),
                    end_time=datetime(2022,10,1,2,3,4,56789),
                    stats_time="2022-10",
                    count=i,
                    error=0,
                    is_latest=True
                )
            )
        db.session.add_all(history_data)
        db.session.commit()
        result = FeedbackMail.load_feedback_mail_history(2)
        assert len(result["data"]) == 20
        
        
#     def load_feedback_failed_mail(cls, id, page_num):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_load_feedback_failed_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_load_feedback_failed_mail(self, db, feedback_mail_faileds):
        # page_num_start > len(feedbackmail_failed)
        with patch("weko_admin.utils.FeedbackMailFailed.get_by_history_id", return_value=["test_history"]):
            test = {
                'data': [],
                'total_page': 0,
                'selected_page': 0,
                'records_per_page': 0,
                'error': 'Cannot get data. Detail: Page out of range'
            }
            result = FeedbackMail.load_feedback_failed_mail(1,20)
            assert result == test
        
        test = {
                'data': [{'mail': 'test.taro@test.org', 'name': 'テスト 太郎'}],
                'total_page': 1,
                'selected_page': 1,
                'records_per_page': 10,
                'error': ''
            }
        result = FeedbackMail.load_feedback_failed_mail(1,1)
        assert result == test
        
        # not path break
        history_data = []
        for i in range(len(feedback_mail_faileds), 21):
            history_data.append(
                FeedbackMailFailed(
                    history_id=1,
                    author_id=1,
                    mail="test.test1@test.org"
                )
            )
        db.session.add_all(history_data)
        db.session.commit()
        result = FeedbackMail.load_feedback_failed_mail(1,2)
        assert len(result["data"]) == 10


#     def get_email_name(cls, author_id, mail):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_get_email_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_email_name(self,authors):
        mail = "test@test.org"
        result = FeedbackMail.get_email_name(None,mail)
        assert result == mail
        
        result = FeedbackMail.get_email_name("not_exist_author",mail)
        assert result == mail
        
        result = FeedbackMail.get_email_name(authors[1].id,mail)
        assert result == mail
        
        result = FeedbackMail.get_email_name(authors[0].id,mail)
        assert result == "テスト 太郎"


#     def get_newest_email(cls, author_id, mail):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_get_newest_email -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_newest_email(self,authors):
        mail = "test@test.org"
        result = FeedbackMail.get_newest_email(None,mail)
        assert result == mail
        
        result = FeedbackMail.get_newest_email("not_exist_author",mail)
        assert result == mail
        
        result = FeedbackMail.get_newest_email(authors[1].id,mail)
        assert result == mail
        
        result = FeedbackMail.get_newest_email(authors[0].id,mail)
        assert result == "test.taro@test.org"


#     def get_total_page(cls, data_length, page_max_record):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_get_total_page -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_total_page(self):
        result = FeedbackMail.get_total_page(4,2)
        assert result == 2
        
        result = FeedbackMail.get_total_page(4,3)
        assert result == 2

#     def get_mail_data_by_history_id(cls, history_id):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_get_mail_data_by_history_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_mail_data_by_history_id(self,feedback_mail_faileds,feedback_mail_histories):
        # not exist history
        result = FeedbackMail.get_mail_data_by_history_id("not exist history")
        assert result == None
        
        # not exist failed
        result = FeedbackMail.get_mail_data_by_history_id(feedback_mail_histories[1].id)
        assert result == None
        
        with patch("weko_search_ui.utils.get_feedback_mail_list",return_value={}):
            result = FeedbackMail.get_mail_data_by_history_id(feedback_mail_histories[0].id)
            assert result == None
        mail_list = {
            "test.taro@test.org":{"items":{},"author_id":""},
            "test.test1@test.org":{"items":{},"author_id":"1"},
        }
        test = {
            "data":{"test.test1@test.org":{"items":{},"author_id":"1"}},
            "stats_date":"2022-10"
        }
        with patch("weko_search_ui.utils.get_feedback_mail_list",return_value=mail_list):
            result = FeedbackMail.get_mail_data_by_history_id(feedback_mail_histories[0].id)
            assert result == test


#     def update_history_after_resend(cls, history_id):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_update_history_after_resend -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_update_history_after_resend(self,feedback_mail_histories):
        FeedbackMail.update_history_after_resend(feedback_mail_histories[0].id)
        assert feedback_mail_histories[0].is_latest == False


# def validation_site_info(site_info):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_validation_site_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_validation_site_info(mocker):
    lang_settings = [
        {"is_registered":True,"lang_code":"en","lang_name":"English","sequence":1},
        {"is_registered":True,"lang_code":"ja","lang_name":"日本語","sequence":2}]
    mocker.patch("weko_admin.utils.get_admin_lang_setting",return_value=lang_settings)

    # not site_name
    result = validation_site_info({})
    assert result == {"error":'Must set at least 1 site name.',"data":[],"status":False}
    
    # All site＿names have no name
    site_info = {
        "site_name":[
            {'index': 0, 'language': 'en'},
            {'index': 1, 'language': 'ja'}
        ],
    }
    result = validation_site_info(site_info)
    assert result == {"error":'Must set at least 1 site name.',"data":["site_name_0"],"status":False}
    
    # site_name have no name
    site_info = {
        "site_name":[
            {'index': 0, 'language': 'en', "name":"test site"},
            {'index': 1, 'language': 'ja', "name":""}
        ],
    }
    result = validation_site_info(site_info)
    assert result == {"error":'Please input site information for empty field.',
                      "data":["site_name_1"],"status":False}
    
    # 2 or more same language in site_name
    site_info = {
        "site_name":[
            {'index': 0, 'language': 'en', "name":"test site1"},
            {'index': 1, 'language': 'en', "name":"test site2"}
        ],
    }
    result = validation_site_info(site_info)
    assert result == {"error":'The same language is set for many site names.',
                      "data":["site_name_0","site_name_1"],"status":False}
    
    # index in item > registered_language
    site_info = {
        "site_name":[
            {'index': 0, 'language': 'en', "name":"test site1"},
            {'index': 1, 'language': 'ja', "name":"テスト サイト"},
            {'index': 3, 'language': 'du', "name":"テスト サイト3"}
        ],
    }
    result = validation_site_info(site_info)
    assert result == {"error":'Language is deleted from Registered Language of system.',
                      "data":["site_name_3"],"status":False}
    
    # language in item not in lang_list
    site_info = {
        "site_name":[
            {'index': 0, 'language': 'en', "name":"test site1"},
            {'index': 1, 'language': 'zh', "name":"テスト サイト2"}
        ],
    }
    result = validation_site_info(site_info)
    assert result == {"error":'Language is deleted from Registered Language of system.',
                      "data":["site_name_1"],"status":False}
    
    # len(notify_name) > 1000
    site_info = {
        "site_name":[
            {'index': 0, 'language': 'en', "name":"test site"},
            {'index': 1, 'language': 'ja', "name":"テスト サイト"}
        ],
        "notify":[
            {"language":"en","notify_name":"a"*1001}
        ]
    }
    result = validation_site_info(site_info)
    assert result == {"error":'The limit is 1000 characters',
                      "data":["notify_None"],"status":False}
    
    # not exist error
    site_info = {
        'site_name': [
            {'index': 0, 'language': 'en', 'name': 'test site'},
            {'index': 1, 'language': 'ja', 'name': 'テスト サイト'}
        ],
        'copy_right': 'test copy right',
        'description': 'this is test description',
        'keyword': 'test_keyword1\ntest_keyword2',
        'favicon': '/static/favicon.ico',
        'favicon_name': 'JAIRO Cloud icon',
        'notify': [{'language': 'en', 'notify_name': ''}],
        'google_tracking_id_user': 'test_tracking_id',
        'ogp_image': '', 
        'ogp_image_name': '', 
    }
    result = validation_site_info(site_info)
    assert result == {"error":'',
                      "data":[],"status":True}


# def format_site_info_data(site_info):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_format_site_info_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_format_site_info_data():
    site_info = {
        'site_name': [
            {'index': 0, 'language': 'en', 'name': 'test site'},
            {'index': 1, 'language': 'ja', 'name': 'テスト サイト'}
        ], 
        'copy_right': 'test copy right ', 
        'google_tracking_id_user': 'test_tracking_id', 
        'keyword': 'test_keyword1\ntest_keyword2', 
        'description': 'this is test description', 
        'favicon_name': 'JAIRO Cloud icon', 
        'favicon': '/static/favicon.ico', 
        'ogp_image_name': '', 
        'ogp_image': '', 
        'notify': [{'language': 'en', 'notify_name': '', 'index': 0}]
    }
    test = {
        'site_name': [
            {'index': 0, 'language': 'en', 'name': 'test site'},
            {'index': 1, 'language': 'ja', 'name': 'テスト サイト'}
        ],
        'copy_right': 'test copy right',
        'description': 'this is test description',
        'keyword': 'test_keyword1\ntest_keyword2',
        'favicon': '/static/favicon.ico',
        'favicon_name': 'JAIRO Cloud icon',
        'notify': [{'language': 'en', 'notify_name': ''}],
        'google_tracking_id_user': 'test_tracking_id',
        'ogp_image': '', 
        'ogp_image_name': '', 
    }
    result = format_site_info_data(site_info)
    assert result == test


# def get_site_name_for_current_language(site_name):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_site_name_for_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_site_name_for_current_language(app):
    # not site_name
    result = get_site_name_for_current_language("")
    assert result == ""
    
    with app.test_request_context(headers=[('Accept-Language', 'ja')]):
        # current_i18.language = item.language
        site_name = [
            {'index': 0, 'language': 'en', 'name': 'test site'},
            {'index': 1, 'language': 'ja', 'name': 'テスト サイト'}
        ]
        result = get_site_name_for_current_language(site_name)
        assert result == "テスト サイト"
        
        # language = en
        site_name = [
            {'index': 0, 'language': 'zh', 'name': 'テスト サイト'},
            {'index': 1, 'language': 'en', 'name': 'test site'},
            
        ]
        result = get_site_name_for_current_language(site_name)
        assert result == "test site"
    with app.test_request_context(headers=[('Accept-Language', 'en')]):
        # language = en
        site_name = [
            {'index': 0, 'language': 'ja', 'name': 'テスト サイト1'},
            {'index': 1, 'language': 'zh', 'name': 'テスト サイト2'}
        ]
        result = get_site_name_for_current_language(site_name)
        assert result == "テスト サイト1"

# def get_notify_for_current_language(notify):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_notify_for_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_notify_for_current_language(app):
    with app.test_request_context(headers=[('Accept-Language', 'ja')]):
        # not notify
        result = get_notify_for_current_language([])
        assert result == ""
        
        # current_i18n.language = language
        notify = [
            {'language': 'en', 'notify_name': 'notify_en'},
            {'language': 'ja', 'notify_name': 'notify_ja'}
        ]
        result = get_notify_for_current_language(notify)
        assert result == "notify_ja"
        
        # en = language
        notify = [
            {'language': 'zh', 'notify_name': 'notify_zh'},
            {'language': 'en', 'notify_name': 'notify_en'}
        ]
        result = get_notify_for_current_language(notify)
        assert result == "notify_en"
    # not current_i18n.language, not en
    with app.test_request_context(headers=[('Accept-Language', 'en')]):
        notify = [
            {'language': 'zh', 'notify_name': 'notify_zh'},
            {'language': 'ja', 'notify_name': 'notify_ja'}
        ]
        result = get_notify_for_current_language(notify)
        assert result == ""


# def __build_init_display_index(indexes: list,
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_build_init_display_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_build_init_display_index(app,indexes):
    with app.test_request_context(headers=[('Accept-Language', 'en')]):
        
        indexes_list = Indexes.get_index_tree()
        init_display_indexes = [{
            "id":"0",
            "parent":"#",
            "text":"Root Index",
            "state":{"opened":True}
        }]
        init_desp_index="1557819733276"
        __build_init_display_index(indexes_list,init_display_indexes,init_desp_index)
        test = [
            {"id":"0","parent":"#","text":"Root Index","state":{"opened":True}},
            {'id': '1557819692844','parent': '0','text': Markup('Contents Type')},
            {'a_attr': {'class': 'jstree-clicked'},'id': '1557819733276','parent': '1557819692844','state': {'selected': True},'text': Markup('conference paper')},
        ]
        assert init_display_indexes == test


# def get_init_display_index(init_disp_index: str) -> list:
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_init_display_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_init_display_index(app,indexes,mocker):
    current_cache.delete("index_tree_json")
    mocker.patch("weko_admin.utils.__build_init_display_index")
    with app.test_request_context(headers=[('Accept-Language', 'en')]):
        result = get_init_display_index("1")
        assert result == [{"id":"0","parent":"#","text":"Root Index","state":{"opened":True}}]
        
        result = get_init_display_index("0")
        assert result == [{"a_attr":{"class":"jstree-clicked"},"id":"0","parent":"#","text":"Root Index","state":{"opened":True,"selected":True}}]


# def get_restricted_access(key: str = None):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_restricted_access -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_restricted_access(app, admin_settings):

    #test No.3 (W2023-22 3(5))
    with patch("weko_admin.utils.AdminSettings.get",return_value=None):
        result = get_restricted_access("not exist key")
        assert result == {}

    #test No.3 (W2023-22 3(5))
    # not key
    result = get_restricted_access("")
    assert result == admin_settings[5].settings
    
    #test No.3 (W2023-22 3(5))
    result = get_restricted_access("usage_report_workflow_access")
    assert result == admin_settings[5].settings["usage_report_workflow_access"]

    #test No.1 (W2023-22 3(5))
    with patch("weko_admin.utils.AdminSettings.get",return_value=admin_settings[8].settings):
        result = get_restricted_access("error_msg")
        assert result == admin_settings[5].settings["error_msg"]

    #test No.2 (W2023-22 3(5))
    result = get_restricted_access("error_msg")
    assert result == admin_settings[5].settings["error_msg"]

# def update_restricted_access(restricted_access: dict):
#     def parse_content_file_download():
#     def validate_content_file_download():
#     def validate_usage_report_wf_access():
#     def parse_usage_report_wf_access():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_update_restricted_access -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_update_restricted_access(admin_settings):
    data = {
        "terms_and_conditions": []
    }
    result = update_restricted_access(data)
    assert result == True

    #9
    data = {
        "secret_URL_file_download": {
            'secret_expiration_date':"",
            "secret_expiration_date_unlimited_chk": False,
            "secret_download_limit": 10,
            "secret_download_limit_unlimited_chk": False,
        }
    }
    result = update_restricted_access(data)
    assert result == False
    #10
    data = {
        "terms_and_conditions": [
            {
                "key": "167635525648",
                "content": {
                    "en": {
                        "title": "terms of servece 1",
                        "content": "this is the text that \"terms of service1\""
                    },
                    "ja": {
                        "title": "利用規約１",
                        "content": "利用規約１の本文です"
                    }
                },
                "existed": True
            }
        ],
        "content_file_download": {
            "download_limit": 1,
            "expiration_date": 1,
            "download_limit_unlimited_chk": False,
            "expiration_date_unlimited_chk": False
        },
        "secret_URL_file_download": {
            "secret_enable": True,
            "secret_download_limit": 1,
            "secret_expiration_date": 1,
            "secret_download_limit_unlimited_chk": False,
            "secret_expiration_date_unlimited_chk": False
        },
        "usage_report_workflow_access": {
            "expiration_date_access": 1,
            "expiration_date_access_unlimited_chk": False
        }
    }
    result = update_restricted_access(data)
    assert result == True
    assert get_restricted_access() == data

    # 11 14
    param = {
        "secret_URL_file_download": {
            "secret_enable": True, 
            "secret_expiration_date": "30",
            "secret_expiration_date_unlimited_chk": True,
            "secret_download_limit": "10",
            "secret_download_limit_unlimited_chk": False,
        }
    }
    expect = {
        "secret_URL_file_download": {
            "secret_enable": True, 
            "secret_expiration_date": 9999999,
            "secret_expiration_date_unlimited_chk": True,
            "secret_download_limit": 10,
            "secret_download_limit_unlimited_chk": False,
        }
    }
    result = update_restricted_access(param)
    assert result == True
    assert get_restricted_access() == expect

    # 12 13
    param = {
        "secret_URL_file_download": {
            "secret_enable": True, 
            "secret_expiration_date": "30",
            "secret_expiration_date_unlimited_chk": False,
            "secret_download_limit": "10",
            "secret_download_limit_unlimited_chk": True,
        }
    }
    expect = {
        "secret_URL_file_download": {
            "secret_enable": True, 
            "secret_expiration_date": 30,
            "secret_expiration_date_unlimited_chk": False,
            "secret_download_limit": 9999999,
            "secret_download_limit_unlimited_chk": True,
        }
    }
    result = update_restricted_access(param)
    assert result == True
    assert get_restricted_access() == expect
    
    # validate_secret_URL_file_download is False
    # 15-1
    data = {
        "secret_URL_file_download": {
            "secret_enable": True, 
            "secret_expiration_date": None, #check this
            "secret_expiration_date_unlimited_chk": False, #check this
            "secret_download_limit": 10,
            "secret_download_limit_unlimited_chk": False,
        }
    }
    result = update_restricted_access(data)
    assert result == False
    
    # 15-2
    data = {
        "secret_URL_file_download": {
            "secret_enable": True, 
            "secret_expiration_date": 30,
            "secret_expiration_date_unlimited_chk": False,
            "secret_download_limit": None, #check this
            "secret_download_limit_unlimited_chk": False,#check this
        }
    }
    result = update_restricted_access(data)
    assert result == False

    # 15-3
    data = {
        "secret_URL_file_download": {
            "secret_enable": True, 
            "secret_expiration_date": 0, #check this
            "secret_expiration_date_unlimited_chk": False, 
            "secret_download_limit": 10,
            "secret_download_limit_unlimited_chk": False,
        }
    }
    result = update_restricted_access(data)
    assert result == False

    # 15-4
    data = {
        "secret_URL_file_download": {
            "secret_enable": True, 
            "secret_expiration_date": 30,
            "secret_expiration_date_unlimited_chk": False, 
            "secret_download_limit": 0, #check this
            "secret_download_limit_unlimited_chk": False,
        }
    }
    result = update_restricted_access(data)
    assert result == False

    # 15-5
    data = {
        "secret_URL_file_download": {
            "secret_enable": True, 
            "secret_expiration_date": -1,#check this
            "secret_expiration_date_unlimited_chk": False, 
            "secret_download_limit": 10, 
            "secret_download_limit_unlimited_chk": False,
        }
    }
    result = update_restricted_access(data)
    assert result == False

    # 15-6
    data = {
        "secret_URL_file_download": {
            "secret_enable": True, 
            "secret_expiration_date": 30,
            "secret_expiration_date_unlimited_chk": False, 
            "secret_download_limit": -1, #check this
            "secret_download_limit_unlimited_chk": False,
        }
    }
    result = update_restricted_access(data)
    assert result == False

    # validate_secret_URL_file_download is True
    # 16
    data = {
        "secret_URL_file_download": {
            "secret_enable": True, 
            "secret_expiration_date": 1, #check this
            "secret_expiration_date_unlimited_chk": False,
            "secret_download_limit": 1,
            "secret_download_limit_unlimited_chk": False,
        }
    }
    result = update_restricted_access(data)
    assert result == True


    # validate_content_file_download is False
    data = {
        "content_file_download": {
            "expiration_date": 0,
            "expiration_date_unlimited_chk": False,
            "download_limit": 0,
            "download_limit_unlimited_chk": False,
        }
    }
    result = update_restricted_access(data)
    assert result == False
    data = {
        "content_file_download": {
            "expiration_date": -1,
            "expiration_date_unlimited_chk": True,
            "download_limit": -1,
            "download_limit_unlimited_chk": True,
        }
    }
    result = update_restricted_access(data)
    assert result == False
    # validate_content_file_download is True
    data = {
        "content_file_download": {
            "expiration_date": 30,
            "expiration_date_unlimited_chk": True,
            "download_limit": 10,
            "download_limit_unlimited_chk": True,
        }
    }
    result = update_restricted_access(data)
    assert result == True
    assert 9999999 == get_restricted_access("content_file_download").get("expiration_date")
    assert 9999999 == get_restricted_access("content_file_download").get("download_limit")

    
    data = {
        "content_file_download": {
            "expiration_date": 30,
            "expiration_date_unlimited_chk": False,
            "download_limit": 10,
            "download_limit_unlimited_chk": False,
        }
    }
    result = update_restricted_access(data)
    assert result == True
    
    # validate_usage_report_wf_access is False
    data = {
            "usage_report_workflow_access": {
                "expiration_date_access": 0,
                "expiration_date_access_unlimited_chk": False,
            }
        }
    result = update_restricted_access(data)
    assert result == False
    
    data = {
            "usage_report_workflow_access": {
                "expiration_date_access": -500,
                "expiration_date_access_unlimited_chk": False,
            }
        }
    result = update_restricted_access(data)
    assert result == False
    
    # validate_usage_report_wf_access is True
    data = {
            "usage_report_workflow_access": {
                "expiration_date_access": 500,
                "expiration_date_access_unlimited_chk": False,
            }
        }
    result = update_restricted_access(data)
    assert result == True
    
    data = {
            "usage_report_workflow_access": {
                "expiration_date_access": 500,
                "expiration_date_access_unlimited_chk": True,
            }
        }
    result = update_restricted_access(data)
    assert result == True
    assert 9999999 == get_restricted_access("usage_report_workflow_access").get("expiration_date_access")


# class UsageReport:
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestUsageReport -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestUsageReport:
#     def __init__(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestUsageReport::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_init(self):
        usage_report = UsageReport()
        
#     def get_activities_per_page(
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestUsageReport::test_get_activities_per_page -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_activities_per_page(self, activities, mocker):
        mocker.patch("weko_admin.utils.UsageReport._UsageReport__count_activities")
        usage_report = UsageReport()
        usage_report._UsageReport__activities_number = 1
        # activities_id is None, page> self.__page_number
        result = usage_report.get_activities_per_page(activities_id=None, size=1, page=2)
        assert result == {'page': 1, 'size': 1, 'activities': [{'activity_id': '31001', 'item_name': 'test item31001', 'workflow_name': 'test workflow31001', 'action_status': 'action_doing', 'user_mail': None}], 'number_of_pages': 1}
        usage_report._UsageReport__activities_number = 2
        result = usage_report.get_activities_per_page(activities_id=[activities[0].id], size=1, page=1)
        assert result == {'page': 1, 'size': 1, 'activities': [{'activity_id': '1', 'item_name': 'test item1', 'workflow_name': 'test workflow1', 'action_status': 'action_doing', 'user_mail': None}], 'number_of_pages': 2}


#     def __count_activities(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestUsageReport::test_count_activities -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_count_activities(self, activities):
        usage_report = UsageReport()
        usage_report._UsageReport__count_activities()
        assert usage_report._UsageReport__activities_number == 1

#     def __format_usage_report_data(self) -> list:
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestUsageReport::test_format_usage_report_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_format_usage_report_data(self, activities):
        usage_report = UsageReport()
        test = [
            {'action_status': 'action_doing',
                'activity_id': '1',
                'item_name': 'test item1',
                'user_mail': None,
                'workflow_name': 'test workflow1'},
            {'action_status': 'action_doing',
                'activity_id': '31001',
                'item_name': 'test item31001',
                'user_mail': None,
                'workflow_name': 'test workflow31001'},
            {'action_status': 'action_doing',
                'activity_id': '2',
                'item_name': 'test item1',
                'user_mail': 'test.guest@test.org',
                'workflow_name': 'test workflow1'},
            {'action_status': 'action_doing',
                'activity_id': '3',
                'item_name': 'test item1',
                'user_mail': None,
                'workflow_name': 'test workflow1'},
        ]
        usage_report._UsageReport__usage_report_activities_data = activities
        result = usage_report._UsageReport__format_usage_report_data()
        assert result == test


#     def send_reminder_mail(self, activities_id: list,
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestUsageReport::test_send_reminder_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_send_reminder_mail(self, app, activities, mocker):
        mail_template = current_app.config.get(
            "WEKO_WORKFLOW_REQUEST_FOR_REGISTER_USAGE_REPORT")
        def mock_email_and_url(activity):
            url = "http://test_server/workflow/activity/detail/{}".format(activity.id)
            return url, "test.test@test.org"
        mocker.patch("weko_admin.utils.UsageReport._UsageReport__get_usage_report_email_and_url", side_effect=mock_email_and_url)
        mocker.patch("weko_workflow.utils.get_mail_data", return_value=("test_subject", "test_body"))
        mocker.patch("weko_workflow.utils.replace_characters", return_value="test_body")
        usage_report = UsageReport()
        acts = [
            activities[1],# not exist item_id, extra_info
            activities[3], # exist item_id, extra_info
        ]
        mocker.patch("weko_workflow.utils.send_mail", return_value=True)
        result = usage_report.send_reminder_mail([],mail_template, acts)
        assert result == True
        
        # not exist activities and mail_template, failed send mail
        mocker.patch("weko_workflow.utils.send_mail", return_value=False)
        result = usage_report.send_reminder_mail(["1","2"],None, None)
        assert result == False

#     def __get_site_info():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestUsageReport::test_get_site_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_site_info(self):
        usage_report = UsageReport()
        # len(site_info.site_name) == 1
        site_info = SiteInfo(
            site_name=[{"name":"test_site_name"}],
            notify={"name":"test_notify"}
        )
        with patch("weko_admin.utils.SiteInfo.get", return_value=site_info):
            name_en, name_ja = usage_report._UsageReport__get_site_info()
            assert name_en == "test_site_name"
            assert name_ja == "test_site_name"
        
        # len(site_info.site_name) == 2
        site_info = SiteInfo(
            site_name=[{"name":"test_site_name","language":"en"},{"name":"テストサイト名","language":"ja"}],
            notify={"name":"test_notify"}
        )
        with patch("weko_admin.utils.SiteInfo.get", return_value=site_info):
            name_en, name_ja = usage_report._UsageReport__get_site_info()
            assert name_en == "test_site_name"
            assert name_ja == "テストサイト名"
        
        # len(site_info.site_name) == 3
        site_info = SiteInfo(
            site_name=[
                {"name":"test_site_name","language":"en"},
                {"name":"テストサイト名","language":"ja"},
                {"name":"test_site_name","language":"en2"}
            ],
            notify={"name":"test_notify"}
        )
        with patch("weko_admin.utils.SiteInfo.get", return_value=site_info):
            name_en, name_ja = usage_report._UsageReport__get_site_info()
            assert name_en == ""
            assert name_ja == ""
        
        # not exist site_name
        with patch("weko_admin.utils.SiteInfo.get", return_value={}):
            name_en, name_ja = usage_report._UsageReport__get_site_info()
            assert name_en == ""
            assert name_ja == ""
            
        
#     def __get_usage_report_email_and_url(self, activity) -> Tuple[str, str]:
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestUsageReport::test_get_usage_report_email_and_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_usage_report_email_and_url(self, app, activities, mocker):
        usage_report = UsageReport()
        with app.test_request_context():
            # not is_guest
            url, email = usage_report._UsageReport__get_usage_report_email_and_url(activities[0])
            assert url
            assert email == None
            
            # is_guest
            url, email = usage_report._UsageReport__get_usage_report_email_and_url(activities[2])
            assert url
            assert email == "test.guest@test.org"


#     def __build_user_info(self, record_data: Union[RecordMetadata, list],
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestUsageReport::test_build_user_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_build_user_info(self):
        record_data = {
            "subitem_restricted_access_name":"test_value",
            "subitem_test_item":["subitem_test_item1"]
        }
        usage_report = UsageReport()
        result = {}
        usage_report._UsageReport__build_user_info(record_data, result)
        assert result == {"restricted_fullname": "test_value"}
        
#     def __get_default_mail_sender():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestUsageReport::test_get_default_mail_sender -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_default_mail_sender(self,mail_config):
        usage_report = UsageReport()
        
        result = usage_report._UsageReport__get_default_mail_sender()
        assert result == "test_sender"

# def get_facet_search(id: int = None):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_facet_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_facet_search(client,facet_search_settings):
    # id is None
    test = {
        "name_en": "",
        "name_jp": "",
        "mapping": "",
        "active": True,
        "aggregations": [],
        "display_number": 5,
        "is_open":True,
        "ui_type": "CheckboxList"
    }
    result = get_facet_search(None)
    assert result == test
    
    result  = get_facet_search(1)
    assert result == {"name_en":"Data Language","name_jp":"データの言語","mapping":"language","aggregations":[],"active":True}


# def get_item_mapping_list():
#     def handle_prefix_key(pre_key, key):
#     def get_mapping(pre_key, key, value, mapping_list):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_item_mapping_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_item_mapping_list(facet_search_settings):
    result = get_item_mapping_list()
    assert result == ['','path','item_type_id','itemtype.keyword','publish_status','_oai.id','_oai.sets','control_number','title','feedback_mail_list.author_id','feedback_mail_list.email','alternative','creator.nameIdentifier','creator.creatorName','creator.familyName','creator.givenName','creator.creatorAlternative','creator.affiliation.nameIdentifier','creator.affiliation.affiliationName','contributor.@attributes.contributorType','contributor.nameIdentifier','contributor.contributorName','contributor.familyName','contributor.givenName','contributor.contributorAlternative','contributor.affiliation.nameIdentifier','contributor.affiliation.affiliationName','accessRights','rightsHolder.nameIdentifier','rightsHolder.rightsHolderName','subject.value','subject.subjectScheme','description.value','description.descriptionType','date.dateType','date.value','language','identifier.identifierType','identifierRegistration.identifierType','relation.relatedIdentifier.identifierType','relation.relatedTitle','relation.relationType.item_links','relation.relationType.item_title','temporal','text1.raw','text2.raw','text3.raw','text4.raw','text5.raw','text6.raw','text7.raw','text8.raw','text9.raw','text10.raw','text11.raw','text12.raw','text13.raw','text14.raw','text15.raw','text16.raw','text17.raw','text18.raw','text19.raw','text20.raw','text21.raw','text22.raw','text23.raw','text24.raw','text25.raw','text26.raw','text27.raw','text28.raw','text29.raw','text30.raw','geoLocation.geoLocationPlace','fundingReference.funderIdentifier','fundingReference.funderName','fundingReference.awardNumber','fundingReference.awardTitle','sourceIdentifier.identifierType','author_link.raw','dateGranted','degreeGrantor.nameIdentifier','degreeGrantor.degreeGrantorName','conference.conferenceName','conference.conferenceSequence','conference.conferencePlace','conference.conferenceCountry','file.URI.objectType','file.mimeType','file.extent','file.date.dateType','file.date.value','content.file_id','content.groups']


# def create_facet_search_query():
#     def create_agg_by_aggregations(aggregations, key, val):
#     def create_aggregations(facets):
#     def create_post_filters(facets):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_create_facet_search_query -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_create_facet_search_query(facet_search_settings):
    has_permission, no_permission = create_facet_search_query()
    test_has_permission = {
        "test-weko":{
            "aggs":{"Data Language":{"terms":{"field":"language","size":1000}},
                    "Data Type":{"aggs":{"Data Type":{"terms":{"field":"description.value","size":1000}}},
                                 "filter":{"bool":{"must":[{"term":{"description.descriptionType":"Other"}}]}}},
                    "raw_test": {"terms": {"field": "test.fields.raw","size": 1000}}
            },
            "post_filters":{"Data Language":"language","Data Type":"description.value","raw_test":"test.raw"}
        }
    }
    test_no_permission = {
        'test-weko': {
            'aggs': {'Data Language': {'aggs': {'Data Language': {'terms': {'field': 'language','size': 1000}}},
                                        'filter': {'bool': {'must': [{'term': {'publish_status': '0'}}]}}},
                    'Data Type': {'aggs': {'Data Type': {'terms': {'field': 'description.value','size': 1000}}},
                                'filter': {'bool': {'must': [{'term': {'description.descriptionType': 'Other'}},{'term': {'publish_status': '0'}}]}}},
                    'raw_test': {'aggs': {'raw_test': {'terms':{'field': 'test.fields.raw','size':1000}}},
                                 'filter':{'bool':{'must':[{'term':{'publish_status':'0'}}]}}}
                    },
                   'post_filters': {'Data Language': 'language',
                                    'Data Type': 'description.value',
                                    'raw_test':'test.raw'}},
    }
    assert has_permission == test_has_permission
    assert no_permission == test_no_permission


# def store_facet_search_query_in_redis():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_store_facet_search_query_in_redis -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_store_facet_search_query_in_redis(mocker):
    has_permission = {
        "test-weko":{
            "aggs":{"Data Language":{"terms":{"field":"language","size":1000}},
                    "Data Type":{"aggs":{"Data Type":{"terms":{"field":"description.value","size":1000}}},
                                 "filter":{"bool":{"must":[{"term":{"description.descriptionType":"Other"}}]}}}
            },
            "post_filters":{"Data Language":"language","Data Type":"description.value"}
        }
    }
    no_permission = {
        'test-weko': {
            'aggs': {'Data Language': {'aggs': {'Data Language': {'terms': {'field': 'language','size': 1000}}},
                                        'filter': {'bool': {'must': [{'term': {'publish_status': '0'}}]}}},
                    'Data Type': {'aggs': {'Data Type': {'terms': {'field': 'description.value','size': 1000}}},
                                'filter': {'bool': {'must': [{'term': {'description.descriptionType': 'Other'}},{'term': {'publish_status': '0'}}]}}}},
                   'post_filters': {'Data Language': 'language',
                                    'Data Type': 'description.value'}},
    }
    mocker.patch("weko_admin.utils.create_facet_search_query",return_value=(has_permission,no_permission))
    mocker.patch("weko_admin.utils.reset_redis_cache")
    store_facet_search_query_in_redis()


# def get_query_key_by_permission(has_permission):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_query_key_by_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_query_key_by_permission():
    result = get_query_key_by_permission(True)
    assert result == 'facet_search_query_has_permission'
    
    result = get_query_key_by_permission(False)
    assert result == 'facet_search_query_no_permission'


# def get_facet_search_query(has_permission=True):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_facet_search_query -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_facet_search_query(app,mocker):
    mocker.patch("weko_admin.utils.store_facet_search_query_in_redis")
    cache_data = {
      "test-weko": {
        "aggs": {
          "Data Language": {"filter": {"bool": { "must": [{ "term": { "publish_status": "0" } }] }},
            "aggs": {"Data Language": { "terms": { "field": "language", "size": 1000 } }}},
          "Data Type": {"filter": {"bool": {"must": [{ "term": { "description.descriptionType": "Other" } },{ "term": { "publish_status": "0" } }]}},
            "aggs": {"Data Type": {"terms": { "field": "description.value", "size": 1000 }}}},
          "raw_test": {"filter": {"bool": { "must": [{ "term": { "publish_status": "0" } }] }},
            "aggs": {"raw_test": { "terms": { "field": "test.fields.raw", "size": 1000 } }}}
        },
        "post_filters": {"Data Language": "language","Data Type": "description.value","raw_test": "test.raw"}
      }
    }
    cache_data = json.dumps(cache_data)
    
    # not exist cache
    with patch("weko_admin.utils.is_exists_key_or_empty_in_redis", return_value=False):
        with patch("weko_admin.utils.get_redis_cache", side_effect=[None, cache_data]):
            result = get_facet_search_query()
            assert result
            
    with patch("weko_admin.utils.is_exists_key_or_empty_in_redis", return_value=True):
        with patch("weko_admin.utils.get_redis_cache", side_effect=[cache_data, cache_data]):
            result = get_facet_search_query()
            assert result


# def get_title_facets():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_title_facets -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_title_facets(app,facet_search_settings):
    with app.test_request_context(headers=[('Accept-Language', 'en')]):
        titles, order = get_title_facets()
        assert titles == {"Data Language":"Data Language","Data Type":"Data Type","raw_test":"raw_test"}
        assert order == {1:"Data Language",3:"Data Type",4:"raw_test"}


# def is_exits_facet(data, id):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_is_exits_facet -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_is_exits_facet(app, facet_search_settings):
    with app.test_request_context(headers=[('Accept-Language', 'en')]):
        # not id > 0
        result = is_exits_facet({"name_en":"Data Type","name_jp":"データタイプ","mapping":"description.value"},None)
        assert result == True
        result = is_exits_facet({"name_en":"not exist facet","name_jp":"存在しないファセット","mapping":"not exist mapping"},None)
        assert result == False
        
        # id > 0
        result = is_exits_facet({"name_en":"Data Type","name_jp":"データタイプ","mapping":"description.value"},"3")
        assert result == False
        result = is_exits_facet({"name_en":"Data Type","name_jp":"データタイプ","mapping":"description.value"},"100")
        assert result == True
        
# def overwrite_the_memory_config_with_db(app, site_info):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_overwrite_the_memory_config_with_db -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_overwrite_the_memory_config_with_db(app,client,site_info):
    from flask import Flask
    
    site_info_not_google = SiteInfo(
        site_name=[{"name":"test_site_info"}],
        notify={"name":"test_notify"}
    )
    
    site_info_google1 = SiteInfo(
        site_name=[{"name":"test_site_info"}],
        notify={"name":"test_notify"},
        google_tracking_id_user="test_tracking_id1",
    )
    site_info_google2 = SiteInfo(
        site_name=[{"name":"test_site_info"}],
        notify={"name":"test_notify"},
        google_tracking_id_user="test_tracking_id2",
    )

    app = Flask("test_weko_admin_app")
    # site_info is None
    overwrite_the_memory_config_with_db(app, None)
    
    # site_info.google_tracking_id_user is not exist
    overwrite_the_memory_config_with_db(app, site_info_not_google)
    
    # GOOGLE_TRACKING_ID_USER is not exist
    overwrite_the_memory_config_with_db(app, site_info_google1)
    assert app.config["GOOGLE_TRACKING_ID_USER"] == "test_tracking_id1"

    overwrite_the_memory_config_with_db(app, site_info_google2)
    assert app.config["GOOGLE_TRACKING_ID_USER"] == "test_tracking_id2"

import json
import pytest
from flask import current_app, make_response, request, url_for
from flask_login import current_user
from mock import patch

from weko_admin.utils import (
    get_title_facets
)

# def get_title_facets():
def test_get_title_facets(i18n_app, users, facet_search_settings):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        titles, order, uiTypes, isOpens, displayNumbers = get_title_facets()
        assert uiTypes
        assert isOpens
        assert displayNumbers
