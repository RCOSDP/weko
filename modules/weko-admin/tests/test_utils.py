import csv
import uuid
from mock import patch
from datetime import datetime, timedelta
from flask import current_app
from io import StringIO
import pytest

from invenio_indexer.api import RecordIndexer

from weko_records.api import ItemTypes, SiteLicense,ItemsMetadata
from weko_user_profiles import UserProfile

from weko_admin.config import WEKO_ADMIN_MANAGEMENT_OPTIONS
from weko_admin.models import AdminLangSettings
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
    get_redis_cache,
    StatisticMail,
    get_system_default_language,
    str_to_bool,
    FeedbackMail
)

from tests.helpers import json_data

# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp


# def get_response_json(result_list, n_lst):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_response_json -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_response_json(app,site_license,item_type):
    n_lst = ItemTypes.get_latest()
    result_list = SiteLicense.get_records()
    result = get_response_json("","")
    assert result == {}
    
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
    result = get_search_setting()
    assert 1==2
    
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
    record = [{"file_key":"test_file_key1",
               "index_list":"test_index_list1",
               "total":1,"no_login":"True",
               "login":"False",
               "site_license":"test_site_license1",
               "admin":"False","reg":"test_reg1"},
              {"file_key":"test_file_key2",
               "index_list":"test_index_list2",
               "total":1,"no_login":"True",
               "login":"False",
               "site_license":"test_site_license2",
               "admin":"False","reg":"test_reg2",
               "group_counts":{"test_group":10}}]
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
    
    reset_redis_cache("test_cache","new_value1")
    assert redis_connect.get("test_cache") == b"new_value1"
    
    redis_connect.delete("test_cache")
    reset_redis_cache("test_cache","new_value2",10)
    assert redis_connect.get("test_cache") == b"new_value2"
    
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


# def is_exists_key_or_empty_in_redis(key):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_is_exists_key_or_empty_in_redis -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_is_exists_key_or_empty_in_redis(redis_connect,mocker):
    mocker.patch("weko_admin.utils.RedisConnection.connection",return_value=redis_connect)
    redis_connect.put("test_key",bytes("test_value","utf-8"))
    result = is_exists_key_in_redis("test_key")
    assert result == True


# def get_redis_cache(cache_key):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::test_get_redis_cache -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_redis_cache(redis_connect,mocker):
    mocker.patch("weko_admin.utils.RedisConnection.connection",return_value=redis_connect)
    redis_connect.delete("test_key")
    result = get_redis_cache("test_key")
    assert result == None
    
    redis_connect.put("test_key",bytes("test_value","utf-8"))
    result = get_redis_cache("test_key")
    assert result == "test_value"


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
    def test_send_mail_to_all(self,client,feedback_mail_settings,mocker):
        setting = {
                "data":[{"author_id":"2","email":"banned@test.org"}],
                "error":"",
                "is_sending_feedback":True,
                "root_url":"http://test_server"
            }
        mocker.patch("weko_admin.utils.FeedbackMail.get_feed_back_email_setting",return_value=setting)
        mocker.patch("weko_admin.utils.StatisticMail.get_banned_mail",return_value=[None])
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
        with patch("weko_admin.utils.get_system_default_language",return_value="ja"):
            mocker.patch("weko_admin.utils.StatisticMail.build_statistic_mail_subject",return_value="[No Site Name]2022-10 利用統計レポート")
            
            # not stats_date
            with patch("weko_admin.utils.FeedbackMail.get_feed_back_email_setting",return_value={"is_sending_feedback":False}):
                result = StatisticMail.send_mail_to_all(None,None)
                assert result == None
            
            list_mail_data = {
                "banned@test.org":{},
                "test.taro@test.org":{"author_id":"1","items":{}}
            }
            StatisticMail.send_mail_to_all(list_mail_data,None)
            assert 1==2
            
        with patch("weko_admin.utils.get_system_default_language",return_value="en"):
            pass

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
            "file_download":{"test_file_.sv":"10"}
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
            "data":[
            "test",
            {"not_find_key":"not_find_value","find_key":"find_value1"},
            {"not_find_key":"not_find_value","find_key":"find_value2"}
            ]
        }
        result = StatisticMail.find_value_in_dict("find_key",data)
        
        for i,r in enumerate(result):
            if i==0:
                assert r == "find_value1"
            elif i==1:
                assert r == "find_value2"


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
                    "hits":[
                        {"_source":self.data[0]},
                        {"_source":self.data[1]}
                    ]
                },
                "item_cnt":2
            }
        elif index == "test-weko":
            return {"item_cnt":2}
# class FeedbackMail:
class TestFeedbackMail:
#     def search_author_mail(cls, request_data: dict) -> dict:
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_search_author_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_search_author_mail(self,client,mocker):
        mock_indexer = RecordIndexer()
        data = json_data("data/test_authors.json")
        mock_indexer.client=MockClient(data)
        mocker.patch("weko_admin.utils.RecordIndexer",return_value=mock_indexer)
        
        request_data = {
            "searchKey":"",
            "numOfPage":"10",
            "pageNumber":"1"
        }
        author_data = json_data("data/test_authors.json")
        test = {
            "hits":{"hits":[
                {"_source":author_data[0]},
                {"_source":author_data[1]}
            ]},
            "item_cnt":{"item_cnt":2}
        }
        result = FeedbackMail.search_author_mail(request_data)
        
        assert result == test
#     def get_feed_back_email_setting(cls):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_get_feed_back_email_setting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_feed_back_email_setting(self, feedback_mail_settings):
        with patch("weko_admin.utils.FeedbackMailSetting.get_all_feedback_email_setting",return_value=[]):
            result = FeedbackMail.get_feed_back_email_setting()
            assert result == {"data":"","is_sending_feedback":"","root_url":"","error":""}
        with patch("weko_admin.utils.FeedbackMailSetting.get_all_feedback_email_setting",return_value=[feedback_mail_settings[1]]):
            test = {
                "data":[{"author_id":"2","email":None}],
                "error":"",
                "is_sending_feedback":True,
                "root_url":"http://test_server"
            }
            result = FeedbackMail.get_feed_back_email_setting()
            assert result == test
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
#             keyword {str} -- search keyword (default: {'author_id'})
# .tox/c1/bin/pytest --cov=weko_admin tests/test_utils.py::TestFeedbackMail::test_convert_feedback_email_data_to_string -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_convert_feedback_email_data_to_string(self):
        result = FeedbackMail.convert_feedback_email_data_to_string("not list")
        assert result == None
        
        data = [
            { "author_id": "1", "email": "test.taro@test.org" },
            { "author_id": "2", "email": "test.smith@test.org" }
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
    def test_load_feedback_mail_history(self,feedback_mail_histories):
        test = {
            "data":[{"start_time":"2022-10-01 01:02:03.045","end_time":"2022-10-01 02:03:04.056","count":2,"error":0,"id":1,"is_latest":True,"success":2}],
            "error":"",
            "records_per_page":20,
            "selected_page":1,
            "total_page":1
        }
        result = FeedbackMail.load_feedback_mail_history(1)
        assert result ==test
        
        with patch("weko_admin.utils.FeedbackMailHistory.get_all_history",side_effect=Exception("test_error")):
            test = {
                "data":[],
                "error":"Cannot get data. Detail: test_error",
                "records_per_page":0,
                "selected_page":0,
                "total_page":0
            }
            result = FeedbackMail.load_feedback_mail_history(1)
            assert result ==test
#     @classmethod
#     def load_feedback_failed_mail(cls, id, page_num):

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

#     @classmethod
#     def get_mail_data_by_history_id(cls, history_id):
#     @classmethod
#     def update_history_after_resend(cls, history_id):
# def validation_site_info(site_info):
# def format_site_info_data(site_info):
# def get_site_name_for_current_language(site_name):
# def get_notify_for_current_language(notify):
# def __build_init_display_index(indexes: list,
#                 index['a_attr'] = {"class": "jstree-clicked"}
# def get_init_display_index(init_disp_index: str) -> list:
#         root_index['a_attr'] = {"class": "jstree-clicked"}
# def get_restricted_access(key: str = None):
# def update_restricted_access(restricted_access: dict):
#     def parse_content_file_download():
#     def validate_content_file_download():
#     def validate_usage_report_wf_access():
#     def parse_usage_report_wf_access():
# class UsageReport:
#     def __init__(self):
#     def get_activities_per_page(
#     def __count_activities(self):
#     def __format_usage_report_data(self) -> list:
#     def send_reminder_mail(self, activities_id: list,
#         site_mail = self.__get_default_mail_sender()
#     def __get_site_info():
#     def __get_usage_report_email_and_url(self, activity) -> Tuple[str, str]:
#     def __build_user_info(self, record_data: Union[RecordMetadata, list],
#     def __get_default_mail_sender():
#         """Get default mail sender.
#         return mail_config.get('mail_default_sender', '')
# def get_facet_search(id: int = None):
# def get_item_mapping_list():
#     def handle_prefix_key(pre_key, key):
#     def get_mapping(pre_key, key, value, mapping_list):
# def create_facet_search_query():
#     def create_agg_by_aggregations(aggregations, key, val):
#     def create_aggregations(facets):
#     def create_post_filters(facets):
# def store_facet_search_query_in_redis():
# def get_query_key_by_permission(has_permission):
# def get_facet_search_query(has_permission=True):
# def get_title_facets():
# def is_exits_facet(data, id):
# def overwrite_the_memory_config_with_db(app, site_info):
#             app.config.setdefault(
#             app.config.setdefault(

