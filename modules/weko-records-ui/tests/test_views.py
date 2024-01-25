from unittest.mock import MagicMock
import uuid
import pytest
import io
from flask import Flask, json, jsonify, session, url_for ,make_response
from flask_security.utils import login_user
from invenio_accounts.testutils import login_user_via_session
from invenio_mail.models import MailTemplateGenres
from mock import patch
from weko_deposit.api import WekoRecord
from werkzeug.exceptions import NotFound ,Forbidden
from sqlalchemy.orm.exc import MultipleResultsFound
from jinja2.exceptions import TemplatesNotFound
from weko_workflow.models import (
    Action,
    ActionStatus,
    ActionStatusPolicy,
    Activity,
    FlowAction,
    FlowDefine,
    WorkFlow,
)
from weko_records_ui.views import (
    _get_show_secret_url_button,
    check_permission,
    citation,
    escape_newline,
    get_image_src,
    get_license_icon,
    json_string_escape,
    pid_value_version,
    publish,
    restore,
    check_file_permission,
    record_from_pid,
    default_view_method,
    url_to_link,
    xml_string_escape,
    escape_str,
    init_permission,
    file_version_update,
    set_pdfcoverpage_header,
    parent_view_method,
    doi_ish_view_method,
    check_file_permission_period,
    get_file_permission,
    check_content_file_clickable,
    get_usage_workflow,
    get_workflow_detail,
    preview_able,
    get_uri,
)
from weko_records_ui.config import WEKO_RECORDS_UI_MAIL_TEMPLATE_SECRET_GENRE_ID

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def record_from_pid(pid_value):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_record_from_pid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_record_from_pid(app, records):
    indexer, results = records
    recid = results[0]["recid"]
    ret = record_from_pid(recid.pid_value)
    assert isinstance(ret, WekoRecord)

    ret = record_from_pid(0)
    assert ret == {}


# def url_to_link(field):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_url_to_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_url_to_link():
    assert url_to_link("file://localhost") == False
    assert url_to_link("http://localhost") == True
    assert url_to_link("https://localhost") == True


# def pid_value_version(pid_value):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_pid_value_version -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_pid_value_version():
    assert pid_value_version(1.1) == "1"
    assert pid_value_version(1.0) == "0"
    assert pid_value_version(1) == None
    assert pid_value_version("1") == None
    assert pid_value_version("1.1") == "1"
    
    pid_value_version(MagicMock())


# def publish(pid, record, template=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_publish_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_publish_acl_guest(client, records):
    url = url_for("invenio_records_ui.recid_publish", pid_value=1, _external=True)
    res = client.post(url)
    assert res.status_code == 302
    assert res.location == "http://test_server/records/1"


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_publish_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 302),
        # (1, 302),
        # (2, 302),
        # (3, 302),
        # (4, 302),
        # (5, 302),
        # (6, 302),
        # (7, 302),
    ],
)
def test_publish_acl(client, records, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("invenio_records_ui.recid_publish", pid_value=1, _external=True)
    res = client.post(url)
    assert res.status_code == status_code
    assert res.location == "http://test_server/records/1"


# def export(pid, record, template=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_export_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_export_acl_guest(client, records):
    url = url_for(
        "invenio_records_ui.recid_export", pid_value=1, format="json", _external=True
    )
    res = client.post(url)
    assert res.status_code == 405

    res = client.get(url)
    assert res.status_code == 200

    url = url_for(
        "invenio_records_ui.recid_export", pid_value=1, format="bibtex", _external=True
    )
    res = client.get(url)
    assert res.status_code == 200

    url = url_for(
        "invenio_records_ui.recid_export", pid_value=1, format="oai_dc", _external=True
    )
    res = client.get(url)
    assert res.status_code == 200

    url = url_for(
        "invenio_records_ui.recid_export",
        pid_value=1,
        format="jpcoar_1.0",
        _external=True,
    )
    res = client.get(url)
    assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_export_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        # (1, 302),
        # (2, 302),
        # (3, 302),
        # (4, 302),
        # (5, 302),
        # (6, 302),
        # (7, 302),
    ],
)
def test_export_acl(client, records, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for(
        "invenio_records_ui.recid_export", pid_value=1, format="json", _external=True
    )
    res = client.post(url)
    assert res.status_code == 405

    url = url_for(
        "invenio_records_ui.recid_export", pid_value=1, format="bibtex", _external=True
    )
    res = client.get(url)
    assert res.status_code == status_code

    url = url_for(
        "invenio_records_ui.recid_export", pid_value=1, format="oai_dc", _external=True
    )
    res = client.get(url)
    assert res.status_code == status_code

    url = url_for(
        "invenio_records_ui.recid_export",
        pid_value=1,
        format="jpcoar_1.0",
        _external=True,
    )
    res = client.get(url)
    assert res.status_code == status_code


# def get_image_src(mimetype):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_get_image_src -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_image_src():
    assert get_image_src("text/plain") == "/static/images/icon/icon_16_txt.jpg"
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
        == "/static/images/icon/icon_16_ppt.jpg"
    )
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.presentationml.slide"
        )
        == "/static/images/icon/icon_16_ppt.jpg"
    )
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.presentationml.slideshow"
        )
        == "/static/images/icon/icon_16_ppt.jpg"
    )
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.presentationml.template"
        )
        == "/static/images/icon/icon_16_ppt.jpg"
    )
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        == "/static/images/icon/icon_16_xls.jpg"
    )
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.template"
        )
        == "/static/images/icon/icon_16_xls.jpg"
    )
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        == "/static/images/icon/icon_16_doc.jpg"
    )
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.template"
        )
        == "/static/images/icon/icon_16_doc.jpg"
    )
    assert get_image_src("application/msword") == "/static/images/icon/icon_16_doc.jpg"
    assert (
        get_image_src("application/vnd.ms-excel")
        == "/static/images/icon/icon_16_xls.jpg"
    )
    assert (
        get_image_src("application/vnd.ms-powerpoint")
        == "/static/images/icon/icon_16_ppt.jpg"
    )
    assert get_image_src("application/zip") == "/static/images/icon/icon_16_zip.jpg"
    assert get_image_src("audio/mpeg") == "/static/images/icon/icon_16_music.jpg"
    assert get_image_src("application/xml") == "/static/images/icon/icon_16_xml.jpg"
    assert get_image_src("image/jpeg") == "/static/images/icon/icon_16_picture.jpg"
    assert get_image_src("application/pdf") == "/static/images/icon/icon_16_pdf.jpg"
    assert get_image_src("video/x-flv") == "/static/images/icon/icon_16_flash.jpg"
    assert get_image_src("video/mpeg") == "/static/images/icon/icon_16_movie.jpg"
    assert get_image_src("application/json") == "/static/images/icon/icon_16_others.jpg"


# def get_license_icon(license_type):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_get_license_icon -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_license_icon(app):
    with app.test_request_context(headers=[("Accept-Language", "ja")]):
        assert get_license_icon("license_12") == (
            "static/images/default88x31(0).png",
            "Creative Commons CC0 1.0 Universal Public Domain Designation",
            "https://creativecommons.org/publicdomain/zero/1.0/",
        )
        assert get_license_icon("license_free") == ("", "", "#")


#     # In case of current lang is not JA, set to default.
#     current_lang = 'default' if current_i18n.language != 'ja' \
# def check_permission(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_check_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_permission(app, records, users):
    indexer, results = records
    record = results[0]["record"]

    assert check_permission(record) == False

    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert check_permission(record) == True

    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        assert check_permission(record) == False


# def check_file_permission(record, fjson):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_check_file_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
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
    ],
)
def test_check_file_permission(app,records,users,id,result):
    indexer, results = records
    record = results[0]["record"]
    assert isinstance(record,WekoRecord)==True
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        assert check_file_permission(record,record['item_1617605131499'])==result


# def check_file_permission_period(record, fjson):
# Error
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_check_file_permission_period -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        # (0, True),
        # (1, True),
        # (2, True),
        # (3, True),
        # (4, True),
        # (5, True),
        # (6, True),
        (7, True), # id=1
    ],
)
def test_check_file_permission_period(app,records,db_file_permission,users,id,result):
    indexer, results = records
    record = results[0]["record"]
    assert isinstance(record,WekoRecord)==True
    fjson = record['item_1617605131499']['attribute_value_mlt'][0]
    # fjson = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': 'image/jpeg', 'filename': 'helloworld.pdf', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': 2700000.0, 'mimetype': 'image/jpeg', 'file_order': 0}
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        with patch("weko_records_ui.views.check_permission_period" , return_value=True):
            assert check_file_permission_period(record,fjson)==result

        # data1 = MagicMock()
        # data2 = MagicMock()
        # assert check_file_permission_period(record,fjson)


# def get_file_permission(record, fjson):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_get_file_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, None),
        # (1, True),
        # (2, True),
        # (3, True),
        # (4, True),
        # (5, True),
        # (6, True),
        # (7, True),
    ],
)
def test_get_file_permission(app,records,users,id,result,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    assert isinstance(record,WekoRecord)==True
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
            assert get_file_permission(record,record['item_1617605131499']['attribute_value_mlt'][0])==result


# def check_content_file_clickable(record, fjson):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_check_content_file_clickable -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, False),
        # (1, True),
        # (2, True),
        # (3, True),
        # (4, True),
        # (5, True),
        # (6, True),
        # (7, True),
    ],
)
def test_check_content_file_clickable(app,records,users,id,result):
    indexer, results = records
    record = results[0]["record"]
    assert isinstance(record,WekoRecord)==True
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        with patch("weko_records_ui.permissions.check_open_restricted_permission", return_value=False):
            assert check_content_file_clickable(record,record['item_1617605131499'])==False


# def get_usage_workflow(file_json):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_get_usage_workflow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_usage_workflow(app, users, workflows):
    _file_json = {
        'provide': [
            {
                'role_id': "3",
                'workflow_id': "2"
            }
            ,
            {
                'role_id': "none_loggin",
                'workflow_id': "3"
            }
        ]
    }
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        res = get_usage_workflow(_file_json)
        assert res=="2"
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        res = get_usage_workflow(_file_json)
        assert res==None

    data1 = MagicMock()
    data1.is_authenticated = False

    with patch("flask_login.utils._get_user", return_value=data1):
        res = get_usage_workflow(_file_json)
        assert res=="3"


# def get_workflow_detail(workflow_id):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_get_workflow_detail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_workflow_detail(app,workflows):
    wf = workflows['workflow']
    ret,isterm = get_workflow_detail(wf.id)
    assert isinstance(ret,WorkFlow) and isinstance(isterm,bool)

    with pytest.raises(NotFound):
        ret,isterm = get_workflow_detail(0)
    

# def default_view_method(pid, record, filename=None, template=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_default_view_method -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
#     """Display default view.
#     def _get_rights_title(result, rights_key, rights_values, current_lang, meta_options):
def test_default_view_method(app, records, itemtypes, indexstyle ,users):
    indexer, results = records
    record = results[0]["record"]
    recid = results[0]["recid"]
    with app.test_request_context():
        with patch('weko_records_ui.views.check_original_pdf_download_permission', return_value=True):
            with patch("weko_records_ui.views.get_search_detail_keyword", return_value={}):
                with patch("weko_records_ui.views.get_index_link_list", return_value=[]):
                    with patch("weko_records_ui.views.render_template", return_value=make_response()):
                        assert default_view_method(recid, record, 'helloworld.pdf').status_code == 200
                        # # need to fix
                        # with pytest.raises(Exception) as e:
                        #     res = default_view_method(recid, record, 'helloworld.pdf')
                        # assert e.type==TemplatesNotFound

                        default_view_method(recid, record )
                        with pytest.raises(NotFound) : #404
                            default_view_method(recid, record ,'notfound.pdf')
                        with pytest.raises(NotFound) : #404
                            default_view_method(recid, record ,'[No FileName]')

                        def cannnot():
                            return False
                        file_permission_factory = MagicMock()
                        file_permission_factory.can = cannnot
                        with patch('weko_records_ui.views.file_permission_factory', return_value=file_permission_factory):
                            with patch('weko_records_ui.views._redirect_method', return_value="redirect"):
                                assert default_view_method(recid, record ,'helloworld.pdf') == "redirect"
                            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                                with pytest.raises(Forbidden) : #404
                                    assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200
                        with patch('weko_records_ui.views.is_show_email_of_creator', return_value=True):
                            assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200
                        with patch('weko_records_ui.views.AdminSettings.get'
                                    , side_effect=lambda name , dict_to_object : {'display_stats' : False} if name == 'display_stats_settings' else None):
                            assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200
                        with patch('weko_records_ui.views.AdminSettings.get'
                                    , side_effect=lambda name , dict_to_object : {'items_search_author' : "author"} if name == 'items_display_settings' else None):
                            assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200
                        with patch('weko_search_ui.utils.get_data_by_property', return_value=(False,False)):
                            with patch('weko_records_ui.views.selected_value_by_language' ,return_value="helloworld.pdf"):
                                assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200
                        with patch('weko_records_ui.views.get_record_permalink', return_value=False):
                            assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200
                        
                            record.update(
                                {'system_identifier_doi' :  
                                    {"attribute_value_mlt" :[{'subitem_systemidt_identifier':"permalink_uri"}]}})
                            assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200


                        def side_effect(arg):
                            values = ['a', 'b']
                            return values[arg]
                        # with patch('weko_search_ui.utils.get_sub_item_value', side_effect=side_effect):
                        #     default_view_method(recid, record ,'helloworld.pdf')
                        pid_ver = MagicMock
                        pid_ver.exists = False
                        with patch('weko_records_ui.views.PIDVersioning',return_value=pid_ver):
                            with pytest.raises(NotFound) : #404
                                assert default_view_method(recid, record ,'helloworld.pdf')

                        pid_ver = MagicMock
                        pid_ver.exists = True
                        pid_ver.is_last_child = False
                        mock = MagicMock
                        mock.object_uuid = uuid.uuid4()
                        pid_ver.children = [mock]
                        pid_ver.get_children = lambda ordered,pid_status : [mock]
                        with patch('weko_records_ui.views.PIDVersioning',return_value=pid_ver):
                            with patch('weko_records_ui.views.WekoRecord.get_record',return_value={'_deposit':{'status':'draft'}}):
                                assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200
                        
                        with patch('weko_records_ui.views.WekoRecord.get_record',side_effect=Exception):
                            assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200
                        with patch('weko_records_ui.views.ItemLink.get_item_link_info',return_value={"relation":"res"}):
                            assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200
                        
                        index = MagicMock()
                        index.index_name = ""
                        index.index_name_english ="index"
                        with patch('weko_records_ui.views.Indexes.get_index',return_value=index):
                            assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200

                        #test No.6(W2023-22 3-5)    
                        restricted_errorMsg = {"content_file_download": {"expiration_date": 30,"expiration_date_unlimited_chk": False,"download_limit": 10,"download_limit_unlimited_chk": False,},"usage_report_workflow_access": {"expiration_date_access": 500,"expiration_date_access_unlimited_chk": False,},"terms_and_conditions": [],"error_msg":{"key" : "","content" : {"ja" : {"content" : "このデータは利用できません（権限がないため）。"},"en":{"content" : "This data is not available for this user"}}}}
                        with patch('weko_admin.utils.get_restricted_access' ,return_value = restricted_errorMsg):
                            assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200
                        
                        with patch('weko_records_ui.views.AdminSettings.get'
                                , side_effect=lambda name , dict_to_object : {'password_enable' : True,"terms_and_conditions":""} if name == 'restricted_access' else None):
                            assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200


# def default_view_method(pid, record, filename=None, template=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_default_view_method2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
#     """Display default view.
#     def _get_rights_title(result, rights_key, rights_values, current_lang, meta_options):
def test_default_view_method2(app, records, itemtypes, indexstyle ,users,db_community):
    indexer, results = records
    record = results[0]["record"]
    recid = results[0]["recid"]
    with app.test_request_context("/?file_order=0&community=community&onetime_file_url=/extra_info"):
        with patch('weko_records_ui.views.check_original_pdf_download_permission', return_value=True):
            with patch("weko_records_ui.views.get_search_detail_keyword", return_value={}):
                with patch("weko_records_ui.views.get_index_link_list", return_value=[]):
                    with patch("weko_records_ui.views.render_template", return_value=make_response()):
                        
                        assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200

                        with patch('weko_workflow.api.GetCommunity.get_community_by_id',return_value=[]):
                            with pytest.raises(AttributeError):
                                default_view_method(recid, record ,'[No FileName]')
                        
                        del record["item_1617605131499"]["attribute_value_mlt"][0]["filename"]
                        with pytest.raises(NotFound) : #404
                            default_view_method(recid, record ,'helloworld.pdf')
                        
                        del record["item_1617605131499"] # files
                        with pytest.raises(NotFound) : #404
                            default_view_method(recid, record ,'helloworld.pdf')
                    


# def doi_ish_view_method(parent_pid_value=0, version=0):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_doi_ish_view_method_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_doi_ish_view_method_acl_guest(app,client,records):
    url = url_for("weko_records_ui.doi_ish_view_method", parent_pid_value=1, _external=True)
    res = client.get(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server/login/?next=%2Fr%2F1'


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_doi_ish_view_method_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, False),
        # (1, True),
        # (2, True),
        # (3, True),
        # (4, True),
        # (5, True),
        # (6, True),
        # (7, True),
    ],
)
def test_doi_ish_view_method_acl(app,client,records,users,id,result):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_records_ui.doi_ish_view_method", parent_pid_value=1, _external=True)
    res = client.get(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server/records/1.1'

    assert "302 FOUND" in doi_ish_view_method(parent_pid_value=1, version=1)


# def parent_view_method(pid_value=0):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_parent_view_method_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_parent_view_method_acl_guest(app,client,records):
    url = url_for("weko_records_ui.parent_view_method", pid_value=1, _external=True)
    res = client.get(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server/login/?next=%2Frecords%2Fparent%3A1'

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_parent_view_method_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, False),
        # (1, True),
        # (2, True),
        # (3, True),
        # (4, True),
        # (5, True),
        # (6, True),
        # (7, True),
    ],
)
def test_parent_view_method_acl(app,client,records,users,id,result):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_records_ui.parent_view_method", pid_value=1, _external=True)
    res = client.get(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server/records/1.1'


# def set_pdfcoverpage_header():
# Error
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_set_pdfcoverpage_header_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_set_pdfcoverpage_header_acl_guest(app, client, records, pdfcoverpagesetting):
    url = url_for("weko_records_ui.set_pdfcoverpage_header",_external=True)
    res = client.get(url)
    assert res.status_code == 308
    assert res.location == 'http://test_server/admin/pdfcoverpage/'

    res = client.post(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server/login/?next=%2Frecords%2Fparent%3A1'

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_set_pdfcoverpage_header_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, False),
        # (1, True),
        # (2, True),
        # (3, True),
        # (4, True),
        # (5, True),
        # (6, True),
        # (7, True),
    ],
)
def test_set_pdfcoverpage_header_acl(app, client, records, users, id, result, pdfcoverpagesetting):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_records_ui.set_pdfcoverpage_header",_external=True)
    res = client.get(url)
    assert res.status_code == 308
    assert res.location == 'http://test_server/admin/pdfcoverpage/'

    data = {'availability':'enable', 'header-display':'string', 'header-output-string':'Weko Univ', 'header-display-position':'center', 'pdfcoverpage_form': '',
    'header-output-image': (io.BytesIO(b"some initial text data"), 'test.png')}
    res = client.post(url,data=data)
    assert res.status_code == 302
    assert res.location == 'http://test_server/admin/pdfcoverpage'

    data = {'availability':'enable', 'header-display':'image', 'header-output-string':'Weko Univ', 'header-display-position':'center', 'pdfcoverpage_form': '',
    'header-output-image': (io.BytesIO(b"some initial text data"), 'test.png')}
    res = client.post(url,data=data)
    assert res.status_code == 302
    assert res.location == 'http://test_server/admin/pdfcoverpage'


#     def handle_over_max_file_size(error):
# def file_version_update():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_file_version_update_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_file_version_update_acl_guest(client, records):
    url = url_for("weko_records_ui.file_version_update",_external=True)
    res = client.put(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server/login/?next=%2Ffile_version%2Fupdate'


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_file_version_update_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        # (1, 302),
        # (2, 302),
        # (3, 302),
        # (4, 302),
        # (5, 302),
        # (6, 302),
        # (7, 302),
    ],
)
def test_file_version_update_acl(client, records, users, id, status_code):
    _data = {}
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_records_ui.file_version_update",_external=True)
    res = client.put(url)
    assert res.status_code == status_code
    assert json.loads(res.data) == {'status': 0, 'msg': 'Insufficient permission'}

    # need to fix
    with patch("weko_records_ui.views.has_update_version_role", return_value=True):
        with pytest.raises(Exception) as e:
            res = client.put(url, data=_data)
        assert e.type == MultipleResultsFound

        _data['bucket_id'] = 'none bucket'
        _data['key'] = 'none key'
        _data['version_id'] = 'version_id'
        res = client.put(url, data=_data)
        assert res.status_code == status_code
        assert json.loads(res.data) == {'status': 0, 'msg': 'Invalid data'}

        data1 = MagicMock()
        data1.is_show = 1

        with patch("invenio_files_rest.models.ObjectVersion.get", return_value=data1):
            file_version_update()

# def citation(record, pid, style=None, ln=None):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_citation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_citation(records):
    indexer, results = records
    record = results[0]["record"]
    assert citation(record,record.pid)==None


# def soft_delete(recid):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_soft_delete_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_soft_delete_acl_guest(client, records):
    url = url_for(
        "weko_records_ui.soft_delete", recid=1, _external=True
    )
    res = client.post(url)
    assert res.status_code == 302


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_soft_delete_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 500), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 500), # generaluser
        (5, 500), # originalroleuser 
        (6, 200), # originalroleuser2
        (7, 500), # user
    ],
)
def test_soft_delete_acl(client, records, users, id, status_code):
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        url = url_for(
            "weko_records_ui.soft_delete", recid=1, _external=True
        )
        with patch("flask.templating._render", return_value=""):
            res = client.post(url)
            assert res.status_code == status_code


# def restore(recid):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_restore_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_restore_acl_guest(client, records):
    url = url_for(
        "weko_records_ui.restore", recid=1, _external=True
    )
    res = client.post(url)
    assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_restore_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 500), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 500), # generaluser
        (5, 500), # originalroleuser 
        (6, 200), # originalroleuser2
        (7, 500), # user
    ],
)
def test_restore_acl(client, records, users, id, status_code):
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        url = url_for(
            "weko_records_ui.restore", recid=1, _external=True
        )
        with patch("flask.templating._render", return_value=""):
            res = client.post(url)
            assert res.status_code == status_code

# def init_permission(recid):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_init_permission_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_init_permission_acl_guest(client, records):
    url = url_for(
        "weko_records_ui.init_permission", recid=1, _external=True
    )
    res = client.post(url)
    assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_init_permission_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
# Error
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 400),
        # (1, 302),
        # (2, 302),
        # (3, 302),
        # (4, 302),
        # (5, 302),
        # (6, 302),
        # (7, 302),
    ],
)
def test_init_permission_acl(client, records,users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    _data = {
        'file_name': 'helloworld.pdf',
        'activity_id': 'A-00000000-00000',
    }
    url = url_for(
        "weko_records_ui.init_permission", recid=1, _external=True
    )
    res = client.post(url, data=_data,headers = {"Content-Type" : "application/json"})
    assert res.status_code == status_code


# def escape_str(s):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_escape_str -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_escape_str():
    assert escape_str("\n")==""


# def escape_newline(s):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_escape_newline -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_escape_newline():
    assert escape_newline("\r") == '<br/>'
    assert escape_newline("\r\n") == '<br/>'
    assert escape_newline("\n") == '<br/>'
    assert escape_newline("\r\r\n\n") == '<br/><br/><br/>'

# def json_string_escape(s):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_json_string_escape -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

def test_json_string_escape():
    assert json_string_escape("\x5c") == "\\\\"
    assert json_string_escape("\x08") == "\\b"
    assert json_string_escape("\x0a") == "\\n"
    assert json_string_escape("\x0d") == "\\r"
    assert json_string_escape("\x09") == "\\t"
    assert json_string_escape("\x0c") == "\\f"
    assert json_string_escape("\x0c") == "\\f"
    assert json_string_escape('"\x0c"') == '\\"\\f\\"'


# def xml_string_escape(s):
def test_xml_string_escape():
    assert xml_string_escape("&<>") == "&amp;&lt;&gt;"


# def preview_able(file_json):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_preview_able -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_preview_able(app):
    mimetype = "image/jpeg"
    size = 200000
    file_json = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': mimetype, 'filename': '001.jpg', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': size, 'mimetype': mimetype, 'file_order': 0}
    with app.test_request_context():
        ret = preview_able(file_json)
        assert isinstance(ret,bool)
        assert ret == True

    mimetype = "application/msword"
    size = 2000
    file_json = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': mimetype, 'filename': '001.jpg', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': size, 'mimetype': mimetype, 'file_order': 0}
    with app.test_request_context():
        ret = preview_able(file_json)
        assert isinstance(ret,bool)
        assert ret == True
    

    size = 20000000000000
    file_json = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': mimetype, 'filename': '001.jpg', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': size, 'mimetype': mimetype, 'file_order': 0}
    with app.test_request_context():
        ret = preview_able(file_json)
        assert isinstance(ret,bool)
        assert ret == False

# def get_uri():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_get_uri -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_uri(app,client,db_sessionlifetime,records):
    url = url_for("weko_records_ui.get_uri",  _external=True)
    res = client.post(url,data=json.dumps({"uri":"https://localhost/record/1/files/001.jpg","pid_value":"1","accessrole":"1"}), content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data)=={'status': True}

    res = client.post(url,data=json.dumps({"uri":"https://localhost/001.jpg","pid_value":"1","accessrole":"1"}), content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data)=={'status': True}

# def create_secret_url_and_send_mail(pid:PersistentIdentifier, record:WekoRecord, filename:str, **kwargs) -> str:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_create_secret_url_and_send_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_create_secret_url_and_send_mail(app,client,db,users,records,db_restricted_access_secret,db_mailTemplateGenre,db_mailtemplates):
    indexer, results = records
    record = results[1]
            
    # 79
    id = 1 #repoadmin
    secret_file_url = url_for("invenio_records_ui.recid_secret_url"
                                ,pid_value=results[1]["recid"].pid_value
                                ,filename=results[1]["filename"])
    login_user_via_session(client=client, user=users[id]["obj"] ,email=users[id]["email"])
    with patch('weko_records_ui.views._get_show_secret_url_button',return_value = True):
        with patch('weko_records_ui.views.process_send_mail',return_value = True):
                #with app.test_request_context():
                    #W2023-22-2 TestNo.7
                    res = client.get(secret_file_url)
                    assert res.status_code == 405

                    #W2023-22-2 TestNo.4
                    res = client.post(secret_file_url ,data=json.dumps({}), content_type='application/json')
                    assert res.status_code == 200

        
    #W2023-22-2 TestNo.6
    with patch('weko_records_ui.views._get_show_secret_url_button',return_value = False):
        with patch('weko_records_ui.views.process_send_mail',return_value = True):
            with patch("flask.templating._render", return_value=""):
                res = client.post(secret_file_url ,data=json.dumps({}), content_type='application/json')
                assert res.status_code == 403
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_create_secret_url_and_send_mail_2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_create_secret_url_and_send_mail_2(app,client,db,users,records,db_restricted_access_secret):
    indexer, results = records
    record = results[1]
            
    # 79
    id = 1 #repoadmin
    secret_file_url = url_for("invenio_records_ui.recid_secret_url"
                                ,pid_value=results[1]["recid"].pid_value
                                ,filename=results[1]["filename"])
    login_user_via_session(client=client, user=users[id]["obj"] ,email=users[id]["email"])
    with patch('weko_records_ui.views._get_show_secret_url_button',return_value = True):
        #W2023-22-2 TestNo.5
            with patch('weko_records_ui.views.process_send_mail',return_value = False):
                with patch("flask.templating._render", return_value=""):
                    res = client.post(secret_file_url ,data=json.dumps({}), content_type='application/json')
                    assert res.status_code == 500

# def create_secret_url_and_send_mail(pid:PersistentIdentifier, record:WekoRecord, filename:str, **kwargs) -> str:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test__get_show_secret_url_button -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, is_show",
    [
        (0, False), #contributor
        (1, True), #repoadmin
        (2, True), #sysadmin
        (3, False), #comadmin
        (4, False), #generaluser
        (5, True), #originalroleuser (owner)
        (6, True), #originalroleuser2 (repoadmin)
        (7, False), #user (weko_shared owner)
    ],
)
def test__get_show_secret_url_button(users,records ,db_restricted_access_secret,id ,is_show):
    indexer, results = records
    # 80
    i = 0
    role = ["open_access" , "open_no" ,"open_date"]
    for record in results:
        record["record"]['owner'] = users[5]["id"]
        record["record"]['weko_shared_ids'] = [users[7]["id"]]
        record["record"].get_file_data()[0].update({'accessrole':role[i]})
        record["record"].get_file_data()[0].update({'date':[{"dateValue" :'2999-12-31'}]})
        i = i + 1

    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        res = []
        for record in results:
            res.append( _get_show_secret_url_button(record["record"] , record["filename"]) )
        
    assert not res[0]
    assert res[1] == is_show
    assert res[2] == is_show

# def create_secret_url_and_send_mail(pid:PersistentIdentifier, record:WekoRecord, filename:str, **kwargs) -> str:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test__get_show_secret_url_button2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, is_show",
    [
        (1, True), #repoadmin
    ],
)
def test__get_show_secret_url_button2(users,records ,id,is_show):
    indexer, results = records
    # 80
    # pattern of not db_restricted_access_secret 
    i = 0
    role = ["open_access" , "open_no" ,"open_date"]
    for record in results:
        record["record"]['owner'] = users[5]["id"]
        record["record"]['weko_shared_ids'] = [users[7]["id"]]
        record["record"].get_file_data()[0].update({'accessrole':role[i]})
        record["record"].get_file_data()[0].update({'date':[{"dateValue" :'2999-12-31'}]})
        i = i + 1
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        res = []
        for record in results:
            res.append( _get_show_secret_url_button(record["record"] , record["filename"]) )
    
    assert res[0] == False
    assert res[1] == False
    assert res[2] == False

# def create_secret_url_and_send_mail(pid:PersistentIdentifier, record:WekoRecord, filename:str, **kwargs) -> str:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test__get_show_secret_url_button3 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, is_show",
    [
        (1, True), #repoadmin
    ],
)
def test__get_show_secret_url_button3(users,records ,db_restricted_access_secret,id,is_show):
    indexer, results = records
    # 80
    i = 0
    role = ["open_access" , "open_no" ,"open_date"]
    for record in results:
        record["record"]['owner'] = users[5]["id"]
        record["record"]['weko_shared_ids'] = [users[7]["id"]]
        record["record"].get_file_data()[0].update({'accessrole':role[i]})
        record["record"].get_file_data()[0].update({'date':[{"dateValue" :'1999-12-31'}]})
        i = i + 1
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        res = []
        for record in results:
            res.append( _get_show_secret_url_button(record["record"] , record["filename"]) )
    
    assert res[0] == False
    assert res[1] == is_show
    assert res[2] == False
