from unittest.mock import MagicMock
import uuid
import pytest
import io
import copy
from flask import Flask, json, jsonify, session, url_for ,make_response
from flask_security.utils import login_user
from flask_babelex import gettext as _
from invenio_accounts.testutils import login_user_via_session
from invenio_files_rest.models import ObjectVersion
from invenio_mail.models import MailTemplateGenres
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from mock import patch
from lxml import etree
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
from weko_records_ui.models import PDFCoverPageSettings, FilePermission
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
    get_item_usage_workflow,
    get_workflow_detail,
    preview_able,
    get_uri,
    get_bucket_list,
    copy_bucket,
    get_file_place,
    replace_file,
)
from .helpers import login, logout
from io import BytesIO
from werkzeug.datastructures import FileStorage
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
    assert url_to_link("https://localhost/records/123/files/file.pdf") == True


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
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_publish -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_publish(client, records, users, communities, mocker):
    login_user_via_session(client=client, email=users[0]["email"])
    indexer, records_info = records
    
    mock_commit = mocker.patch("weko_records_ui.views.db.session.commit")
    mock_commit2 = mocker.patch("invenio_records.api.Record.commit")

    mock_update_es_data = mocker.patch("weko_deposit.api.WekoIndexer.update_es_data")
    
    # Test Case 1: community id exists
    mock_request = mocker.patch("weko_records_ui.views.request")
    mock_request.values = {"community": 1}
    actual_response = publish(records_info[0]["recid"], records_info[0]["record"], template=None)
    assert actual_response.status_code == 302
    assert actual_response.location == "/records/1?community=1"

    # Test Case 2: community id exists
    mock_request.values = {}
    actual_response = publish(records_info[0]["recid"], records_info[0]["record"], template=None)
    assert actual_response.status_code == 302
    assert actual_response.location == "/records/1"


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
@pytest.mark.timeout(60)
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

# def get_item_usage_workflow(record)
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_get_item_usage_workflow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_item_usage_workflow(records):
    indexer, results = records
    record = results[0]["record"]
    provide_list = {"workflow":"1", "terms":"term_free", "termsDescription":"利用規約自由入力"}
    with patch("weko_records_ui.views.get_item_provide_list",return_value=provide_list):
        class Mocklocale:
            id = 0
            def get_language_name(self, bbb):
                return "Japanese"
        with patch("weko_records_ui.views.get_locale", return_value = Mocklocale()):
            terms=["利用規約自由入力",  "Terms of Use Free Input"]
            with patch("weko_records_ui.views.extract_term_description",return_value =terms):
                terms, provide= get_item_usage_workflow(record)
                assert terms == "利用規約自由入力"
                assert provide == "1"

    provide_list = {"workflow":"1", "terms":"1111111111"}
    with patch("weko_records_ui.views.get_item_provide_list",return_value=provide_list):
        with patch("weko_records_ui.views.get_locale") as pi:
            terms=["",  "Terms of Use Free Input"]
            with patch("weko_records_ui.views.extract_term_description",return_value =terms):
                pi.get_language_name = MagicMock()
                terms, provide= get_item_usage_workflow(record)
                assert terms == "Terms of Use Free Input"
                assert provide == "1" 

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
                        with patch('weko_workflow.api.GetCommunity.get_community_by_root_node_id',return_value=None):
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
                            with patch('weko_records_ui.views.AdminSettings.get'
                                        , side_effect=lambda name , dict_to_object : {'display_stats' : False} if name == 'display_stats_settings' else None):
                                assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200
                            with patch('weko_records_ui.views.AdminSettings.get'
                                        , side_effect=lambda name , dict_to_object : {'items_search_author' : "author"} if name == 'items_display_settings' else None):
                                assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200
                            with patch('weko_records_ui.views.AdminSettings.get'
                                        , side_effect=lambda name , dict_to_object : {'display_request_form' : False} if name == 'items_display_settings' else None):
                                assert default_view_method(recid, record ,'helloworld.pdf').status_code == 200
                            with patch('weko_records_ui.views.AdminSettings.get'
                                        , side_effect=lambda name , dict_to_object : {'display_request_form' : True} if name == 'items_display_settings' else None):
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
                                with patch('weko_workflow.api.GetCommunity.get_community_by_root_node_id',return_value=[{'id':'33','thumbnail_path':''}]):
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
@pytest.mark.timeout(300)
def test_set_pdfcoverpage_header_acl_error(app, client, records, users, id, result, pdfcoverpagesetting):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_records_ui.set_pdfcoverpage_header",_external=True)
    res = client.get(url)
    assert res.status_code == 308
    assert res.location == 'http://test_server/admin/pdfcoverpage/'
    s = PDFCoverPageSettings.find(1)
    assert s is not None
    assert s.header_output_image == ''

    data = {'availability':'enable', 'header-display':'string', 'header-output-string':'Weko Univ', 'header-display-position':'center', 'pdfcoverpage_form': '',
        'header-output-image': (io.BytesIO(b"some initial text data"), 'test.png')}
    with patch('weko_records_ui.views.db.session.commit', side_effect=Exception("")):
        res = client.post(url,data=data)
        assert res.status_code == 302
        s = PDFCoverPageSettings.find(1)
        assert s is not None
        assert s.header_output_image == ''

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
    s = PDFCoverPageSettings.find(1)
    assert s is not None
    assert s.header_output_image == ''

    data = {'availability':'enable', 'header-display':'string', 'header-output-string':'Weko Univ', 'header-display-position':'center', 'pdfcoverpage_form': '',
        'header-output-image': (io.BytesIO(b"some initial text data"), 'test.png')}
    res = client.post(url,data=data)
    assert res.status_code == 302
    assert res.location == 'http://test_server/admin/pdfcoverpage'
    s = PDFCoverPageSettings.find(1)
    assert s is not None
    assert s.header_output_image != ''

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

    with patch("weko_records_ui.views.has_update_version_role", return_value=True):
        _data['is_show'] = '1'
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
    assert citation(record,record.pid)=='Joho, Taro, Joho, Taro, Joho, Taro, 2021, en_conference paperITEM00000009(public_open_access_simple): Publisher, 1–3 p.'


# def soft_delete(recid):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_soft_delete_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_soft_delete_acl_guest(client, records):
    # 51994 case.04(soft_delete)
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
        # 51994 case.01, 05(soft_delete)
        with patch("flask.templating._render", return_value=""):
            with patch("weko_records_ui.views.call_external_system") as mock_external:
                pid = PersistentIdentifier.query.filter_by(
                    pid_type='recid', pid_value='1').first()
                assert pid.status == PIDStatus.REGISTERED
                res = client.post(url)
                assert res.status_code == status_code
                pid = PersistentIdentifier.query.filter_by(
                    pid_type='recid', pid_value='1').first()
                if status_code == 200:
                    assert pid.status == PIDStatus.DELETED
                    mock_external.assert_called_once()
                    assert mock_external.call_args[1]["old_record"] is not None
                    assert "new_record" not in mock_external.call_args[1]
                else:
                    assert pid.status == PIDStatus.REGISTERED
                    mock_external.assert_not_called()

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_soft_delete_with_del_ver_prefix -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (6, 200), # originalroleuser
    ],
)
def test_soft_delete_with_del_ver_prefix(client, records, users, id, status_code):
    """Test soft_delete when recid starts with 'del_ver_'."""
    login_user_via_session(client=client, email=users[id]["email"])
    # Arrange
    recid = "del_ver_12345"

    # 51994 case.02(soft_delete)
    with patch("weko_records_ui.views.delete_version") as mock_delete_version:
        # Act
        res = client.post(url_for("weko_records_ui.soft_delete", recid=recid, _external=True))

        # Assert
        assert res.status_code == status_code
        mock_delete_version.assert_called_once_with("12345")

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_soft_delete_locked -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (6, 200), # originalroleuser
    ],
)
def test_soft_delete_locked(client, records, users, id, status_code):
    """Test soft_delete when item is locked."""
    login_user_via_session(client=client, email=users[id]["email"])
    
    # 51994 case.03(soft_delete)
    with patch("weko_records_ui.views.is_workflow_activity_work", return_value=True):
        res = client.post(url_for("weko_records_ui.soft_delete", recid=1, _external=True))
        expected_response = {
            "code": -1,
            "is_locked": True,
            "msg": _("MSG_WEKO_RECORDS_UI_IS_EDITING_TRUE")
        }
        assert res.status_code == status_code
        assert json.loads(res.data) == expected_response

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_soft_delete_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_soft_delete_exception(client, records, users):
    """Test soft_delete when raise Exception."""
    login_user_via_session(client=client, email=users[2]["email"])
    expected_response = {
            "code": -1,
            "is_locked": True,
            "msg": "Test Error."
        }
    with patch("weko_records_ui.views.has_update_version_role", return_value=True):
        with patch("flask.templating._render", return_value=""):
            pid = PersistentIdentifier.query.filter_by(pid_type='recid', pid_value='1').first()
            assert pid.status == PIDStatus.REGISTERED
            with patch("weko_records_ui.views.soft_delete_imp", side_effect=Exception([{
                "is_locked": True,
                "msg": "Test Error."
            }])):
                with pytest.raises(Exception):
                    # 51994 case.06, 07(soft_delete)
                    res = client.post(url_for("weko_records_ui.soft_delete", recid=1, _external=True))

                    
                    pid = PersistentIdentifier.query.filter_by(pid_type='recid', pid_value='1').first()
                    assert pid.status == PIDStatus.REGISTERED
                    assert res.status_code == 500
                    assert res.json == expected_response
    
    
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
        "file_name": "helloworld.pdf",
        "activity_id": "A-00000000-00000"
    }
    url = url_for(
        "weko_records_ui.init_permission", recid=1
    )

    res = client.post(url, data=json.dumps(_data), headers=[('Content-Type', 'application/json')])
    assert res.status_code == 200
    res = FilePermission.query.all()
    assert len(res)==1

# Error
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_init_permission_acl_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
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
def test_init_permission_acl_error(client, records,users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    _data = {
        "file_name": None,
        "activity_id": None
    }
    url = url_for(
        "weko_records_ui.init_permission", recid=1
    )

    with pytest.raises(Exception) as e:
        res = client.post(url, data=json.dumps(_data), headers=[('Content-Type', 'application/json')])
        assert e.type==KeyError
        res = FilePermission.query.all()
        assert len(res)==0


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
    # 404を発生させるとwebassets.exceptions.FilterErrorが発生する対策
    app.register_error_handler(404, None)

    url = url_for("weko_records_ui.get_uri",  _external=True)
    res = client.post(url,data=json.dumps({"uri":"https://localhost/record/1/files/001.jpg","pid_value":"1","accessrole":"1"}), content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data)=={'status': True}

    res = client.post(url,data=json.dumps({"uri":"https://localhost/001.jpg","pid_value":"1","accessrole":"1"}), content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data)=={'status': True}

    # Invalid request data
    res = client.post("/get_uri")
    assert res.status_code == 400

    # Invalid pid_value
    res = client.post(url,data=json.dumps({"uri":"https://localhost/001.jpg","pid_value":"test","accessrole":"1"}), content_type='application/json', follow_redirects=False)
    assert res.status_code == 404


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_default_view_method_fix35133 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_default_view_method_fix35133(app, records, itemtypes, indexstyle,mocker):
    indexer, results = records
    record = results[0]["record"]
    recid = results[0]["recid"]
    etree_str = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2022-10-07T06:11:40Z</responseDate><request identifier="oai:repository.dl.itc.u-tokyo.ac.jp:02005680" verb="getrecord" metadataPrefix="jpcoar_1.0">https://repository.dl.itc.u-tokyo.ac.jp/oai</request><getrecord><record><header><identifier>oai:repository.dl.itc.u-tokyo.ac.jp:02005680</identifier><datestamp>2022-09-27T06:40:27Z</datestamp></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">『史料編纂掛備用写真画像図画類目録』画像の部：新旧架番号対照表</dc:title><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/123" nameIdentifierScheme="ORCID">123</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="en">creator name</jpcoar:creatorName><jpcoar:familyName xml:lang="en">creator family name</jpcoar:familyName><jpcoar:givenName xml:lang="en">creator given name</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="en">creator alternative name</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="test uri" nameIdentifierScheme="ISNI">affi name id</jpcoar:nameIdentifier><jpcoar:affiliationName xml:lang="en">affi name</jpcoar:affiliationName></jpcoar:affiliation></jpcoar:creator><dc:rights>CC BY</dc:rights><datacite:description xml:lang="ja" descriptionType="Other">『史料編纂掛備用寫眞畫像圖畫類目録』（1905年）の「画像」（肖像画模本）の部に著録する資料の架番号の新旧対照表。史料編纂所所蔵肖像画模本データベースおよび『目録』版面画像へのリンク付き。『画像史料解析センター通信』98（2022年10月）に解説記事あり。</datacite:description><dc:publisher xml:lang="ja">東京大学史料編纂所附属画像史料解析センター</dc:publisher><dc:publisher xml:lang="en">Center for the Study of Visual Sources, Historiographical Institute, The University of Tokyo</dc:publisher><datacite:date dateType="Issued">2022-09-30</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_ddb1">dataset</dc:type><jpcoar:identifier identifierType="HDL">http://hdl.handle.net/2261/0002005680</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://repository.dl.itc.u-tokyo.ac.jp/records/2005680</jpcoar:identifier><jpcoar:relation relationType="references"><jpcoar:relatedIdentifier identifierType="URI">https://clioimg.hi.u-tokyo.ac.jp/viewer/list/idata/850/8500/20/%28a%29/?m=limit</jpcoar:relatedIdentifier></jpcoar:relation><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>point longitude test</datacite:pointLongitude><datacite:pointLatitude>point latitude test</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>1</datacite:westBoundLongitude><datacite:eastBoundLongitude>2</datacite:eastBoundLongitude><datacite:southBoundLatitude>3</datacite:southBoundLatitude><datacite:northBoundLatitude>4</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>geo location place test</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:file><jpcoar:URI objectType="dataset">https://repository.dl.itc.u-tokyo.ac.jp/record/2005680/files/comparison_table_of_preparation_image_catalog.xlsx</jpcoar:URI><jpcoar:mimeType>application/vnd.openxmlformats-officedocument.spreadsheetml.sheet</jpcoar:mimeType><jpcoar:extent>121.7KB</jpcoar:extent><datacite:date dateType="Available">2022-09-27</datacite:date></jpcoar:file></jpcoar:jpcoar></metadata></record></getrecord></OAI-PMH>'
    et = etree.fromstring(etree_str)
    mock_render_template = mocker.patch("weko_records_ui.views.render_template")
    with app.test_request_context():
        with patch('weko_records_ui.views.check_original_pdf_download_permission', return_value=True):
            with patch("weko_records_ui.views.getrecord",return_value=et):
                with patch('weko_workflow.api.GetCommunity.get_community_by_root_node_id',return_value=None):
                    default_view_method(recid, record)
                    args, kwargs = mock_render_template.call_args
                    assert kwargs["google_scholar_meta"] == [
                            {'name': "citation_title","data": "『史料編纂掛備用写真画像図画類目録』画像の部：新旧架番号対照表"},
                            {"name": "citation_publisher", "data": "東京大学史料編纂所附属画像史料解析センター"},
                            {'name': 'citation_publication_date', 'data': "2022-09-30"},
                            {"name": "citation_author","data": "creator name"},
                            {"name":"citation_pdf_url","data":"https://repository.dl.itc.u-tokyo.ac.jp/record/2005680/files/comparison_table_of_preparation_image_catalog.xlsx"},
                            {'name': 'citation_dissertation_institution','data':""},
                            {'name': 'citation_abstract_html_url','data': 'http://TEST_SERVER/records/1'},
                        ]
                    assert kwargs["google_dataset_meta"] == '{"@context": "https://schema.org/", "@type": "Dataset", "citation": ["http://hdl.handle.net/2261/0002005680", "https://repository.dl.itc.u-tokyo.ac.jp/records/2005680"], "creator": [{"@type": "Person", "alternateName": "creator alternative name", "familyName": "creator family name", "givenName": "creator given name", "identifier": "123", "name": "creator name"}], "description": "『史料編纂掛備用寫眞畫像圖畫類目録』（1905年）の「画像」（肖像画模本）の部に著録する資料の架番号の新旧対照表。史料編纂所所蔵肖像画模本データベースおよび『目録』版面画像へのリンク付き。『画像史料解析センター通信』98（2022年10月）に解説記事あり。", "distribution": [{"@type": "DataDownload", "contentUrl": "https://repository.dl.itc.u-tokyo.ac.jp/record/2005680/files/comparison_table_of_preparation_image_catalog.xlsx", "encodingFormat": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}, {"@type": "DataDownload", "contentUrl": "https://raw.githubusercontent.com/RCOSDP/JDCat-base/main/apt.txt", "encodingFormat": "text/plain"}, {"@type": "DataDownload", "contentUrl": "https://raw.githubusercontent.com/RCOSDP/JDCat-base/main/environment.yml", "encodingFormat": "application/x-yaml"}, {"@type": "DataDownload", "contentUrl": "https://raw.githubusercontent.com/RCOSDP/JDCat-base/main/postBuild", "encodingFormat": "text/x-shellscript"}], "includedInDataCatalog": {"@type": "DataCatalog", "name": "https://localhost"}, "license": ["CC BY"], "name": "『史料編纂掛備用写真画像図画類目録』画像の部：新旧架番号対照表", "spatialCoverage": [{"@type": "Place", "geo": {"@type": "GeoCoordinates", "latitude": "point latitude test", "longitude": "point longitude test"}}, {"@type": "Place", "geo": {"@type": "GeoShape", "box": "1 3 2 4"}}, "geo location place test"]}'
# def create_secret_url_and_send_mail(pid:PersistentIdentifier, record:WekoRecord, filename:str, **kwargs) -> str:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_create_secret_url_and_send_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_create_secret_url_and_send_mail(app,client,db,users,records, db_mailTemplateGenre, db_mailtemplates):
    app.config['WEKO_WORKFLOW_DATE_FORMAT'] = "%Y-%m-%d"
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

        with patch('weko_records_ui.views.process_send_mail', return_value = False):
            with patch("flask.templating._render", return_value=""):
                res = client.post(secret_file_url ,data=json.dumps({}), content_type='application/json')
                assert res.status_code == 500

        
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
        (1, False), #repoadmin
        (2, False), #sysadmin
        (3, False), #comadmin
        (4, False), #generaluser
        (5, False), #originalroleuser (owner)
        (6, False), #originalroleuser2 (repoadmin)
        (7, False), #user (weko_shared owner)
    ],
)
def test__get_show_secret_url_button(users,records,id ,is_show):
    indexer, results = records
    # 80
    i = 0
    role = ["open_access" , "open_no" ,"open_date"]
    for record in results:
        record["record"]['owner'] = users[5]["id"]
        record["record"]['weko_shared_ids'] = [users[7]["id"]]
        file_data = record["record"].get_file_data()
        if len(file_data) > 0:
            file_data[0].update({'accessrole':role[i%3]})
            file_data[0].update({'date':[{"dateValue" :'2999-12-31'}]})
            i = i + 1

    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        res = []
        for record in results:
            if 'filename' in record:
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
        file_data = record["record"].get_file_data()
        if len(file_data) > 0:
            file_data[0].update({'accessrole':role[i%3]})
            file_data[0].update({'date':[{"dateValue" :'2999-12-31'}]})
            i = i + 1
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        res = []
        for record in results:
            if 'filename' in record:
                res.append( _get_show_secret_url_button(record["record"] , record["filename"]) )

    assert res[0] == False
    assert res[1] == False
    assert res[2] == False

# def create_secret_url_and_send_mail(pid:PersistentIdentifier, record:WekoRecord, filename:str, **kwargs) -> str:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test__get_show_secret_url_button3 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, is_show",
    [
        (1, False), #repoadmin
    ],
)
def test__get_show_secret_url_button3(users,records,id,is_show):
    indexer, results = records
    # 80
    i = 0
    role = ["open_access" , "open_no" ,"open_date"]
    for record in results:
        record["record"]['owner'] = users[5]["id"]
        record["record"]['weko_shared_ids'] = [users[7]["id"]]
        file_data = record["record"].get_file_data()
        if len(file_data) > 0:
            file_data[0].update({'accessrole':role[i%3]})
            file_data[0].update({'date':[{"dateValue" :'2999-12-31'}]})
            i = i + 1
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        res = []
        for record in results:
            if 'filename' in record:
                res.append( _get_show_secret_url_button(record["record"] , record["filename"]) )

    assert res[0] == False
    assert res[1] == is_show
    assert res[2] == False


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_publish -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_publish(app, client, records):
    record = WekoRecord.get_record_by_pid("1")
    mock_pid = MagicMock()
    mock_pid.last_child = record.pid
    record["publish_status"] = "0"
    record_0_a = copy.deepcopy(record)
    record_0_b = copy.deepcopy(record)
    record_0_c = copy.deepcopy(record)
    record["publish_status"] = "1"
    record_1_a = copy.deepcopy(record)
    record_1_b = copy.deepcopy(record)
    record_1_c = copy.deepcopy(record)
    with patch("weko_records_ui.views.PIDVersioning", mock_pid):
        with patch("weko_records_ui.views.url_for", return_value=""):
            with patch("weko_records_ui.views.call_external_system") as mock_external:
                with patch("weko_records_ui.views.WekoRecord.commit"):
                    with patch("weko_records_ui.views.WekoRecord.get_record_by_pid", return_value=record_0_a):
                        with app.test_request_context(data={"status": "1"}):
                            publish(record.pid, record_0_b)
                            mock_external.assert_called_with(old_record=record_0_c, new_record=record_1_c)
                    with patch("weko_records_ui.views.WekoRecord.get_record_by_pid", return_value=record_1_a):
                        with app.test_request_context(data={"status": "0"}):
                            publish(record.pid, record_1_b)
                            mock_external.assert_called_with(old_record=record_1_c, new_record=record_0_c)

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_request_context -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_bucket_list(app,records,users):
    with app.test_request_context():
        with patch("weko_records_ui.views.get_s3_bucket_list", return_value=[]):
            response = get_bucket_list()
            assert response.status_code == 200
        with patch("weko_records_ui.views.get_s3_bucket_list",side_effect=Exception):
            response = get_bucket_list()
            assert response.status_code == 400

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_copy_bucket -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_copy_bucket(app,records,users, client):

    login(client,obj=users[0]["obj"])
    url = url_for("weko_records_ui.copy_bucket")
    with patch("weko_records_ui.views.copy_bucket_to_s3", return_value={}):
        res = client.post(
            url,
            data=json.dumps({
            'pid': '1',
            'file_name': 'helloworld.pdf',
            'bucket_id': '1',
            'checked': 'True',
            'bucket_name': 'name',
            }),
            content_type='application/json',
        )
        assert res.status_code == 200
    with patch("weko_records_ui.views.copy_bucket_to_s3",side_effect=Exception):
        res = client.post(
            url,
            data=json.dumps({
            'pid': '1',
            'file_name': 'helloworld.pdf',
            'bucket_id': '1',
            'checked': 'True',
            'bucket_name': 'name',
            }),
            content_type='application/json',
        )
        assert res.status_code == 400

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_get_file_place -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_file_place(app,records,users, client):
    login(client,obj=users[0]["obj"])
    url = url_for("weko_records_ui.get_file_place")
    with patch(
        "weko_records_ui.views.get_file_place_info",
        return_value={
            "file_place": 'file_place',
            "uri": 'uri',
            "new_bucket_id": 'new_bucket_id',
            "new_version_id": 'new_version_id'
       }
    ):
        res = client.post(
            url,
            data={
                'pid': '1',
                'bucket_id': '1',
                'file_name': 'helloworld.pdf',
            },
        )
        assert res.status_code == 200
    with patch("weko_records_ui.views.get_file_place_info",side_effect=Exception):
        res = client.post(
            url,
            data={
                'pid': '1',
                'bucket_id': '1',
                'file_name': 'helloworld.pdf',
            },
        )
        assert res.status_code == 400

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_replace_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_replace_file(app,records,users, client):
    login(client,obj=users[0]["obj"])
    url = url_for("weko_records_ui.replace_file")
    # テスト用のデータを用意
    test_data = b'Hello, World!' # バイナリデータ
    # BytesIOオブジェクトを作成
    # FileStorageオブジェクトを作成
    with patch("weko_records_ui.views.replace_file_bucket", return_value={}):
        res = client.post(
            url,
            data={
                'return_file_place': 'S3',
                'pid': '1',
                'bucket_id':'1',
                'file_name': 'helloworld.pdf',
                'file_size': 100,
                'file_checksum': '86266081366d3c950c1cb31fbd9e1c38e4834fa52b568753ce28c87bc31252cd',
                'new_bucket_id': '1',
                'new_version_id': '1',
            },
        )
        assert res.status_code == 200
    with patch("weko_records_ui.views.replace_file_bucket",side_effect=Exception):
        res = client.post(
            url,
            data={
                'return_file_place': 'S3',
                'pid': '1',
                'bucket_id':'1',
                'file_name': 'helloworld.pdf',
                'file_size': 100,
                'file_checksum': '86266081366d3c950c1cb31fbd9e1c38e4834fa52b568753ce28c87bc31252cd',
                'new_bucket_id': '1',
                'new_version_id': '1',
            },
        )
        assert res.status_code == 400
    with patch("weko_records_ui.views.replace_file_bucket", return_value={}):
        virtual_file = BytesIO(test_data)
        file = FileStorage(stream=virtual_file, filename='helloworld.pdf', content_type='application/pdf')
        res = client.post(
            url,
            data={
                'return_file_place': 'local',
                'pid': '1',
                'bucket_id':'1',
                'file_name': 'helloworld.pdf',
                'file_size': 100,
                'file_checksum': '86266081366d3c950c1cb31fbd9e1c38e4834fa52b568753ce28c87bc31252cd',
                'new_bucket_id': '1',
                'new_version_id': '1',
                'file': file,
            },
        )
        assert res.status_code == 200
    with patch("weko_records_ui.views.replace_file_bucket",side_effect=Exception):
        virtual_file = BytesIO(test_data)
        file = FileStorage(stream=virtual_file, filename='helloworld.pdf', content_type='application/pdf')
        res = client.post(
            url,
            data={
                'return_file_place': 'local',
                'pid': '1',
                'bucket_id':'1',
                'file_name': 'helloworld.pdf',
                'file_size': 100,
                'file_checksum': '86266081366d3c950c1cb31fbd9e1c38e4834fa52b568753ce28c87bc31252cd',
                'new_bucket_id': '1',
                'new_version_id': '1',
                'file': file,
            },
        )
        assert res.status_code == 400
