import json
import pytest
from flask import url_for, make_response
from flask_babelex import lazy_gettext as _
from flask_breadcrumbs import current_breadcrumbs
from flask_menu import current_menu
from mock import patch, MagicMock
from invenio_accounts.testutils import login_user_via_session

from weko_admin.models import SessionLifetime
from weko_admin.views import (
    _has_admin_access
)
from tests.helpers import login, logout
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp

def assert_role(response,is_permission,status_code=403):
    if is_permission:
        assert response.status_code != status_code
    else:
        assert response.status_code == status_code

def response_data(response):
    print(response.data)
    return json.loads(response.data)

#def _has_admin_access():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_has_admin_access -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_has_admin_access(client,users):
    # login with sysadmin
    login(client,obj=users[0]["obj"])
    result = _has_admin_access()
    assert result == True
    logout(client)
    
    # login with generaluser
    login(client,obj=users[4]["obj"])
    result = _has_admin_access()
    assert result == False
    logout(client)

#def set_lifetime(minutes):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_set_lifetime -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_set_lifetime(client,db):
    url = url_for("weko_admin.set_lifetime",minutes=100,_external=False)
    print(url)
    
    # not exist session life time
    res = client.get(url)
    assert response_data(res) == {"code":0,"msg":"Session lifetime was updated."}
    assert SessionLifetime.query.filter_by(is_delete=False).first().lifetime == 100
    
    # exist sessino life time
    url = url_for("weko_admin.set_lifetime",minutes=200)
    res = client.get(url)
    assert response_data(res) == {"code":0,"msg":"Session lifetime was updated."}
    assert SessionLifetime.query.filter_by(is_delete=False).first().lifetime == 200

    # raises BaseException
    with patch("weko_admin.views.SessionLifetime.get_validtime",side_effect=BaseException("test_error")):
        res = client.get(url)
        assert res.status_code == 400


#def lifetime():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_lifetime -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_lifetime(client,users,db,mocker):
    url = url_for("weko_admin.lifetime")
    print(SessionLifetime.query.filter_by(is_delete=False).first())
    # not login
    res = client.get(url)
    assert res.status_code == 302
    
    # not sysadmin
    login(client,obj=users[4]["obj"])
    res = client.get(url)
    assert res.status_code == 403
    logout(client)
    
    login(client,obj=users[0]["obj"])

    
    db.session.add(SessionLifetime(lifetime=100))
    db.session.commit()
    # method is POST, submit is lifetime
    mock_render = mocker.patch("weko_admin.views.render_template",return_value=make_response())
    mock_flash = mocker.patch("weko_admin.views.flash")
    res = client.post(url,data={"submit":"lifetime","lifetimeRadios":"45"})
    assert res.status_code == 200
    mock_render.assert_called_with(
        "weko_admin/settings/lifetime.html",
        current_lifetime="45",
        map_lifetime=[("15",_("15 mins")),("30",_("30 mins")),("45",_("45 mins")),("60",_("60 mins")),
                      ("180",_("180 mins")),("360",_("360 mins")),("720",_("720 mins")),("1440",_("1440 mins"))]
    )
    mock_flash.assert_called_with("Session lifetime was updated.",category="success")
    
    # method is POST, submit is not lifitime
    mock_render = mocker.patch("weko_admin.views.render_template",return_value=make_response())
    res = client.post(url,data={"submit":"not lifetime"})
    assert res.status_code == 200
    mock_render.assert_called_with(
        "weko_admin/settings/lifetime.html",
        current_lifetime="45",
        map_lifetime=[("15",_("15 mins")),("30",_("30 mins")),("45",_("45 mins")),("60",_("60 mins")),
                      ("180",_("180 mins")),("360",_("360 mins")),("720",_("720 mins")),("1440",_("1440 mins"))]
    )
    
    # raises BaseException
    with patch("weko_admin.views.SessionLifetime.get_validtime",side_effect=BaseException("test_error")):
        res = client.get(url)
        assert res.status_code == 400
    
    
    assert current_menu.submenu("settings.lifetime").active == True
    assert current_menu.submenu("settings.lifetime").url == "/accounts/settings/session/"
    assert current_menu.submenu("settings.lifetime").text == '<i class="fa fa-cogs fa-fw"></i> Session'
    assert list(map(lambda x:x.url,list(current_breadcrumbs))) == ["#","#","#","/accounts/settings/session/"]


#def session_info_offline():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_session_info_offline -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_session_info_offline(client):
    url = url_for("weko_admin.session_info_offline")
    res = client.get(url)
    print(response_data(res))
    assert 1==2
#def get_lang_list():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_lang_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_lang_list(api):
    lang_list = [{"lang_code":"en","lang_name":"English","is_registered":True,"sequence":1},
                 {"lang_code":"ja","lang_name":"日本語","is_registered":True,"sequence":2}]
    with patch("weko_admin.views.get_admin_lang_setting",return_value=lang_list):
        pass
    with patch("weko_admin.views.get_admin_lang_setting",side_effect=Exception("test_error")):
        pass
#def save_lang_list():
def test_save_lang_list_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    with patch("weko_admin.views.update_admin_lang_setting", return_value=""):
        res = client.post("/api/admin/save_lang",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200

def test_save_lang_list_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_admin.views.update_admin_lang_setting", return_value=""):
        res = client.post("/api/admin/save_lang",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200


def test_save_lang_list_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    with patch("weko_admin.views.update_admin_lang_setting", return_value=""):
        res = client.post("/api/admin/save_lang",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_save_lang_list_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    with patch("weko_admin.views.update_admin_lang_setting", return_value=""):
        res = client.post("/api/admin/save_lang",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_save_lang_list_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    with patch("weko_admin.views.update_admin_lang_setting", return_value=""):
        res = client.post("/api/admin/save_lang",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_save_lang_list_guest(client, users):
    with patch("weko_admin.views.update_admin_lang_setting", return_value=""):
        res = client.post("/api/admin/save_lang",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 302
#def get_selected_lang():
#def get_api_cert_type():
#def get_curr_api_cert(api_code=''):
#def save_api_cert_data():
def test_save_api_cert_data_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    res = client.post("/api/admin/save_api_cert_data",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 200


def test_save_api_cert_data_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    res = client.post("/api/admin/save_api_cert_data",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 200


def test_save_api_cert_data_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    res = client.post("/api/admin/save_api_cert_data",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 403


def test_save_api_cert_data_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    res = client.post("/api/admin/save_api_cert_data",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 403


def test_save_api_cert_data_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    res = client.post("/api/admin/save_api_cert_data",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 403


def test_save_api_cert_data_guest(client, users):
    res = client.post("/api/admin/save_api_cert_data",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 302
#def get_init_selection(selection=""):


#def get_email_author():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_email_author_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,is_permission",[
                         (0,True),# sysadmin
                         (1,True),# repoadmin
                         (2,False),# comadmin
                         (3,False),# contributor
                         (4,False),# generaluser
                         ])
def test_get_email_author_acl(client,users,index,is_permission):
    login_user_via_session(client,email=users[index]["email"])
    with patch("weko_admin.views.FeedbackMail.search_author_mail",return_value={}):
        res = client.post('/api/admin/search_email',json={},)
        assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_email_author_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_email_author_acl_guest(client):
    with patch("weko_admin.views.FeedbackMail.search_author_mail",return_value={}):
        res = client.post('/api/admin/search_email',json={},)
        assert res.status_code == 302



#def update_feedback_mail():
def test_update_feedback_mail_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={}):
        res = client.post("/api/admin/update_feedback_mail",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200


def test_update_feedback_mail_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={}):
        res = client.post("/api/admin/update_feedback_mail",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200


def test_update_feedback_mail_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={}):
        res = client.post("/api/admin/update_feedback_mail",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_update_feedback_mail_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={}):
        res = client.post("/api/admin/update_feedback_mail",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_update_feedback_mail_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={}):
        res = client.post("/api/admin/update_feedback_mail",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_update_feedback_mail_guest(client, users):
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={}):
        res = client.post("/api/admin/update_feedback_mail",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 302
#def get_feedback_mail():
#def get_send_mail_history():
#def get_failed_mail():
#def resend_failed_mail():
class Mock_FeedbackMail:
    @classmethod
    def get_mail_data_by_history_id(cls, history_id):
        pass
    
    @classmethod
    def update_history_after_resend(cls, history_id):
        pass


def test_resend_failed_mail_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    mock_feedbackmail = MagicMock(side_effect = Mock_FeedbackMail)
    with patch("weko_admin.views.FeedbackMail", mock_feedbackmail):
        with patch("weko_admin.views.StatisticMail.send_mail_to_all", return_value=""):
            res = client.post("/api/admin/resend_failed_mail",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_resend_failed_mail_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    mock_feedbackmail = MagicMock(side_effect = Mock_FeedbackMail)
    with patch("weko_admin.views.FeedbackMail", mock_feedbackmail):
        with patch("weko_admin.views.StatisticMail.send_mail_to_all", return_value=""):
            res = client.post("/api/admin/resend_failed_mail",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_resend_failed_mail_comadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    mock_feedbackmail = MagicMock(side_effect = Mock_FeedbackMail)
    with patch("weko_admin.views.FeedbackMail", mock_feedbackmail):
        with patch("weko_admin.views.StatisticMail.send_mail_to_all", return_value=""):
            res = client.post("/api/admin/resend_failed_mail",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_resend_failed_mail_cont(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    mock_feedbackmail = MagicMock(side_effect = Mock_FeedbackMail)
    with patch("weko_admin.views.FeedbackMail", mock_feedbackmail):
        with patch("weko_admin.views.StatisticMail.send_mail_to_all", return_value=""):
            res = client.post("/api/admin/resend_failed_mail",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_resend_failed_mail_gene(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    mock_feedbackmail = MagicMock(side_effect = Mock_FeedbackMail)
    with patch("weko_admin.views.FeedbackMail", mock_feedbackmail):
        with patch("weko_admin.views.StatisticMail.send_mail_to_all", return_value=""):
            res = client.post("/api/admin/resend_failed_mail",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403

def test_resend_failed_mail_guest(client, users):
    mock_feedbackmail = MagicMock(side_effect = Mock_FeedbackMail)
    with patch("weko_admin.views.FeedbackMail", mock_feedbackmail):
        with patch("weko_admin.views.StatisticMail.send_mail_to_all", return_value=""):
            res = client.post("/api/admin/resend_failed_mail",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 302
#def manual_send_site_license_mail(start_month, end_month):
def test_manual_send_site_license_mail_sysadmin(client, users, site_license):
    login_user_via_session(client=client, email=users[4]["email"])
    with patch("weko_admin.views.QueryCommonReportsHelper.get", return_value={"institution_name":[]}):
        with patch("weko_admin.views.send_site_license_mail"):
            res = client.post("/api/admin/sitelicensesendmail/send/202201/202203",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_manual_send_site_license_mail_repoadmin(client, users, site_license):
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_admin.views.QueryCommonReportsHelper.get", return_value={"institution_name":[]}):
        with patch("weko_admin.views.send_site_license_mail"):
            res = client.post("/api/admin/sitelicensesendmail/send/202201/202203",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_manual_send_site_license_mail_comadmin(client, users, site_license):
    login_user_via_session(client=client, email=users[2]["email"])
    with patch("weko_admin.views.QueryCommonReportsHelper.get", return_value={"institution_name":[]}):
        with patch("weko_admin.views.send_site_license_mail"):
            res = client.post("/api/admin/sitelicensesendmail/send/202201/202203",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_manual_send_site_license_mail_cont(client, users, site_license):
    login_user_via_session(client=client, email=users[1]["email"])
    with patch("weko_admin.views.QueryCommonReportsHelper.get", return_value={"institution_name":[]}):
        with patch("weko_admin.views.send_site_license_mail"):
            res = client.post("/api/admin/sitelicensesendmail/send/202201/202203",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_manual_send_site_license_mail_gene(client, users, site_license):
    login_user_via_session(client=client, email=users[0]["email"])
    with patch("weko_admin.views.QueryCommonReportsHelper.get", return_value={"institution_name":[]}):
        with patch("weko_admin.views.send_site_license_mail"):
            res = client.post("/api/admin/sitelicensesendmail/send/202201/202203",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_manual_send_site_license_mail_guest(client, users, site_license):
    with patch("weko_admin.views.QueryCommonReportsHelper.get", return_value={"institution_name":[]}):
        with patch("weko_admin.views.send_site_license_mail"):
            res = client.post("/api/admin/sitelicensesendmail/send/202201/202203",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 302
#def update_site_info():
def test_update_site_info_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    with patch("weko_admin.views.format_site_info_data", return_value=""):
        with patch("weko_admin.views.validation_site_info", return_value={"error":"error"}):
            res = client.post("/api/admin/update_site_info",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_update_site_info_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_admin.views.format_site_info_data", return_value=""):
        with patch("weko_admin.views.validation_site_info", return_value={"error":"error"}):
            res = client.post("/api/admin/update_site_info",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_update_site_info_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    with patch("weko_admin.views.format_site_info_data", return_value=""):
        with patch("weko_admin.views.validation_site_info", return_value={"error":"error"}):
            res = client.post("/api/admin/update_site_info",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_update_site_info_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    with patch("weko_admin.views.format_site_info_data", return_value=""):
        with patch("weko_admin.views.validation_site_info", return_value={"error":"error"}):
            res = client.post("/api/admin/update_site_info",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_update_site_info_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    with patch("weko_admin.views.format_site_info_data", return_value=""):
        with patch("weko_admin.views.validation_site_info", return_value={"error":"error"}):
            res = client.post("/api/admin/update_site_info",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_update_site_info_guest(client, users):
    with patch("weko_admin.views.format_site_info_data", return_value=""):
        with patch("weko_admin.views.validation_site_info", return_value={"error":"error"}):
            res = client.post("/api/admin/update_site_info",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 302
#def get_site_info():
#def get_avatar():
#def get_ogp_image():
#def get_search_init_display_index(selected_index=None):
#def save_restricted_access():
def test_save_restricted_access_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    with patch("weko_admin.views.update_restricted_access",return_value=True):
        res = client.post("/api/admin/restricted_access/save",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200


def test_save_restricted_access_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_admin.views.update_restricted_access",return_value=True):
        res = client.post("/api/admin/restricted_access/save",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200


def test_save_restricted_access_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    with patch("weko_admin.views.update_restricted_access",return_value=True):
        res = client.post("/api/admin/restricted_access/save",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_save_restricted_access_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    with patch("weko_admin.views.update_restricted_access",return_value=True):
        res = client.post("/api/admin/restricted_access/save",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_save_restricted_access_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    with patch("weko_admin.views.update_restricted_access",return_value=True):
        res = client.post("/api/admin/restricted_access/save",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_save_restricted_access_guest(client, users):
    with patch("weko_admin.views.update_restricted_access",return_value=True):
        res = client.post("/api/admin/restricted_access/save",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 302
#def get_usage_report_activities():
class MockUsageReport:
    def __init__(self):
        pass

    def get_activities_per_page(self, activities_id, size, page):
        return {}


def test_get_usage_report_activities_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    mock_usagereport = MagicMock(side_effect=MockUsageReport)
    with patch("weko_admin.views.UsageReport", mock_usagereport):
        res = client.post("/api/admin/restricted_access/"\
                          "get_usage_report_activities",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200


def test_get_usage_report_activities_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    mock_usagereport = MagicMock(side_effect=MockUsageReport)
    with patch("weko_admin.views.UsageReport", mock_usagereport):
        res = client.post("/api/admin/restricted_access/"\
                          "get_usage_report_activities",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200


def test_get_usage_report_activities_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    mock_usagereport = MagicMock(side_effect=MockUsageReport)
    with patch("weko_admin.views.UsageReport", mock_usagereport):
        res = client.post("/api/admin/restricted_access/"\
                          "get_usage_report_activities",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_get_usage_report_activities_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    mock_usagereport = MagicMock(side_effect=MockUsageReport)
    with patch("weko_admin.views.UsageReport", mock_usagereport):
        res = client.post("/api/admin/restricted_access/"\
                          "get_usage_report_activities",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_get_usage_report_activities_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    mock_usagereport = MagicMock(side_effect=MockUsageReport)
    with patch("weko_admin.views.UsageReport", mock_usagereport):
        res = client.post("/api/admin/restricted_access/"\
                          "get_usage_report_activities",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_get_usage_report_activities_guest(client, users):
    mock_usagereport = MagicMock(side_effect=MockUsageReport)
    with patch("weko_admin.views.UsageReport", mock_usagereport):
        res = client.post("/api/admin/restricted_access/"\
                          "get_usage_report_activities",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 302



























#def send_mail_reminder_usage_report():
def test_send_mail_reminder_usage_report_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])

    res = client.post("/api/admin/restricted_access/send_mail_reminder",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 200


def test_send_mail_reminder_usage_report_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])

    res = client.post("/api/admin/restricted_access/send_mail_reminder",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 200


def test_send_mail_reminder_usage_report_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])

    res = client.post("/api/admin/restricted_access/send_mail_reminder",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 403


def test_send_mail_reminder_usage_report_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])

    res = client.post("/api/admin/restricted_access/send_mail_reminder",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 403


def test_send_mail_reminder_usage_report_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])

    res = client.post("/api/admin/restricted_access/send_mail_reminder",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 403


def test_send_mail_reminder_usage_report_guest(client, users):
    res = client.post("/api/admin/restricted_access/send_mail_reminder",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 302
#def save_facet_search():
def test_save_facet_search_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    with patch("weko_admin.views.is_exits_facet", return_value=True):
        with patch("weko_admin.views.store_facet_search_query_in_redis", return_value=""):
            res = client.post("/api/admin/facet-search/save",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_save_facet_search_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_admin.views.is_exits_facet", return_value=True):
        with patch("weko_admin.views.store_facet_search_query_in_redis", return_value=""):
            res = client.post("/api/admin/facet-search/save",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_save_facet_search_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    with patch("weko_admin.views.is_exits_facet", return_value=True):
        with patch("weko_admin.views.store_facet_search_query_in_redis", return_value=""):
            res = client.post("/api/admin/facet-search/save",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_save_facet_search_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    with patch("weko_admin.views.is_exits_facet", return_value=True):
        with patch("weko_admin.views.store_facet_search_query_in_redis", return_value=""):
            res = client.post("/api/admin/facet-search/save",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_save_facet_search_guest(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    with patch("weko_admin.views.is_exits_facet", return_value=True):
        with patch("weko_admin.views.store_facet_search_query_in_redis", return_value=""):
            res = client.post("/api/admin/facet-search/save",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_save_facet_search_guest(client, users):
    with patch("weko_admin.views.is_exits_facet", return_value=True):
        with patch("weko_admin.views.store_facet_search_query_in_redis", return_value=""):
            res = client.post("/api/admin/facet-search/save",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 302
#def remove_facet_search():
def test_remove_facet_search_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    data = {"id":[]}
    with patch("weko_admin.views.store_facet_search_query_in_redis", return_value={}):
        res = client.post("api/admin/facet-search/remove",
                          data=json.dumps(data),
                          content_type="application/json")
        assert res.status_code == 200


def test_remove_facet_search_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    data = {"id":[]}
    with patch("weko_admin.views.store_facet_search_query_in_redis", return_value={}):
        res = client.post("api/admin/facet-search/remove",
                          data=json.dumps(data),
                          content_type="application/json")
        assert res.status_code == 200


def test_remove_facet_search_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    data = {"id":[]}
    with patch("weko_admin.views.store_facet_search_query_in_redis", return_value={}):
        res = client.post("api/admin/facet-search/remove",
                          data=json.dumps(data),
                          content_type="application/json")
        assert res.status_code == 403


def test_remove_facet_search_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    data = {"id":[]}
    with patch("weko_admin.views.store_facet_search_query_in_redis", return_value={}):
        res = client.post("api/admin/facet-search/remove",
                          data=json.dumps(data),
                          content_type="application/json")
        assert res.status_code == 403


def test_remove_facet_search_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    data = {"id":[]}
    with patch("weko_admin.views.store_facet_search_query_in_redis", return_value={}):
        res = client.post("api/admin/facet-search/remove",
                          data=json.dumps(data),
                          content_type="application/json")
        assert res.status_code == 403


def test_remove_facet_search_guest(client, users):
    data = {"id":[]}
    with patch("weko_admin.views.store_facet_search_query_in_redis", return_value={}):
        res = client.post("api/admin/facet-search/remove",
                          data=json.dumps(data),
                          content_type="application/json")
        assert res.status_code == 302