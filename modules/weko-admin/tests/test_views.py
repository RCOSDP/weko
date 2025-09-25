import json
import pytest
from flask import url_for, make_response, current_app
from flask_babelex import lazy_gettext as _
from flask_breadcrumbs import current_breadcrumbs
from flask_menu import current_menu
from mock import patch, MagicMock
from invenio_accounts.testutils import login_user_via_session
from weko_records.models import SiteLicenseInfo
from weko_admin.models import SessionLifetime, SiteInfo, AdminSettings
from weko_admin.views import (
    _has_admin_access,
    dbsession_clean,
    manual_send_site_license_mail
)
from tests.helpers import login, logout
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp

def assert_role(response,is_permission,status_code=403):
    if is_permission:
        assert response.status_code != status_code
    else:
        assert response.status_code == status_code

def response_data(response):
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
def test_set_lifetime(client,db,users):
    login_user_via_session(client,email=users[0]["email"])

    # exist sessino life time
    url = url_for("weko_admin.set_lifetime",minutes=200)
    res = client.get(url)
    assert response_data(res) == {"code":0,"msg":"Session lifetime was updated."}
    assert SessionLifetime.query.filter_by(is_delete=False).first().lifetime == 200

    SessionLifetime.query.filter_by(id=1).delete()
    db.session.commit()
    # not exist session life time
    url = url_for("weko_admin.set_lifetime",minutes=100)
    res = client.get(url)
    assert response_data(res) == {"code":0,"msg":"Session lifetime was updated."}
    assert SessionLifetime.query.filter_by(is_delete=False).first().lifetime == 100

    # raises BaseException
    with patch("weko_admin.views.SessionLifetime.get_validtime",side_effect=BaseException("test_error")):
        res = client.get(url)
        assert res.status_code == 400


#def lifetime():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_lifetime -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_lifetime(client,users,db,mocker):
    url = url_for("weko_admin.lifetime")
    # not login
    res = client.get(url)
    assert res.status_code == 302

    # not sysadmin
    login(client,obj=users[4]["obj"])
    res = client.get(url)
    assert res.status_code == 403
    logout(client)

    email = users[0]["email"]
    passwd = users[0]["obj"].password_plaintext
    #login(client,obj=users[0]["obj"])
    login(client,email=email,password=passwd)


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
                      ("180",_("180 mins")),("360",_("360 mins")),("720",_("720 mins")),("1440",_("1440 mins"))],
        form="lifetime"
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
                      ("180",_("180 mins")),("360",_("360 mins")),("720",_("720 mins")),("1440",_("1440 mins"))],
        form="not lifetime"
    )

    # method is not POST, session_lifetime is None
    SessionLifetime.query.delete()
    db.session.commit()
    mock_render = mocker.patch("weko_admin.views.render_template", return_value=make_response())
    res = client.get(url)
    assert res.status_code == 200
    args, kwargs = mock_render.call_args
    assert args[0] == "weko_admin/settings/lifetime.html"
    assert kwargs["current_lifetime"] == "30"
    assert kwargs["map_lifetime"] == [("15",_("15 mins")),("30",_("30 mins")),("45",_("45 mins")),("60",_("60 mins")),
                      ("180",_("180 mins")),("360",_("360 mins")),("720",_("720 mins")),("1440",_("1440 mins"))]


    # raises ValueError
    with patch("weko_admin.views.SessionLifetime.get_validtime",side_effect=ValueError("test_error")):
        res = client.get(url)
        assert res.status_code == 400

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
def test_session_info_offline(client,session_lifetime):
    url = url_for("weko_admin.session_info_offline")
    res = client.get(url)
    assert response_data(res) == {"user_id":None,"session_id":"None","_app_lifetime":"1:40:00","current_app_name":"test_weko_admin_app","lifetime":"1:40:00"}

def test_get_server_date(api):
    url = url_for("weko_admin.get_server_date")
    res = api.get(url)
    result = response_data(res)
    assert "year" in result
    assert "month" in result
    assert "day" in result

#def get_lang_list():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_lang_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_lang_list(api):
    url = url_for("weko_admin.get_lang_list")
    lang_list = [{"lang_code":"en","lang_name":"English","is_registered":True,"sequence":1},
                 {"lang_code":"ja","lang_name":"日本語","is_registered":True,"sequence":2}]
    with patch("weko_admin.views.get_admin_lang_setting",return_value=lang_list):
        res = api.get(url)
        assert response_data(res) == {"results":lang_list,"msg":"success"}
    with patch("weko_admin.views.get_admin_lang_setting",side_effect=Exception("test_error")):
        res = api.get(url)
        assert response_data(res) == {"msg":"test_error"}

#def save_lang_list():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_save_lang_list_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,is_permission",[
                         (0,True),# sysadmin
                         (1,True),# repoadmin
                         (2,False),# comadmin
                         (3,False),# contributor
                         (4,False),# generaluser
                         ])
def test_save_lang_list_acl(api,users,index,is_permission):
    url = url_for("weko_admin.save_lang_list")
    login_user_via_session(client=api, email=users[index]["email"])
    with patch("weko_admin.views.update_admin_lang_setting", return_value=""):
        with patch("weko_index_tree.utils.delete_index_trees_from_redis"):
            res = api.post(url,data=json.dumps({}),
                            content_type="application/json")
            assert_role(res,is_permission)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_save_lang_list_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_save_lang_list_acl_guest(api, users):
    url = url_for("weko_admin.save_lang_list")
    with patch("weko_admin.views.update_admin_lang_setting", return_value=""):
        with patch("weko_index_tree.utils.delete_index_trees_from_redis"):
            res = api.post(url,data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_save_lang_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_save_lang_list(api, users, redis_connect):
    import os
    os.environ['INVENIO_WEB_HOST_NAME'] = "test"
    url = url_for("weko_admin.save_lang_list")
    login_user_via_session(client=api, email=users[0]["email"])
    redis_connect.put("index_tree_view_test_ja","test_ja_index_tree".encode("UTF-8"),ttl_secs=30)
    redis_connect.put("index_tree_view_test_en","test_en_index_tree".encode("UTF-8"),ttl_secs=30)
    # content_type != application/json
    res = api.post(url,data="test_data",content_type="plain/text")
    assert response_data(res) == {"msg":"Header Error"}

    # content_type = application/json
    data = [{"lang_code":"ja","is_registered":True},{"lang_code":"en","is_registered":False}]
    with patch("weko_admin.views.update_admin_lang_setting",return_value="success"):
        res = api.post(url,json=data)
        assert redis_connect.redis.exists("index_tree_view_test_ja") == True
        assert redis_connect.redis.exists("index_tree_view_test_en") == False
        assert response_data(res) == {"msg":"success"}


#def get_selected_lang():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_selected_lang -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_selected_lang(api):
    url = url_for("weko_admin.get_selected_lang")
    with patch("weko_admin.views.get_selected_language",return_value={"lang":"ja","selected":"ja"}):
        res = api.get(url)
        assert response_data(res) == {"lang":"ja","selected":"ja"}

    # raises Exception
    with patch("weko_admin.views.get_selected_language",side_effect=Exception("test_error")):
        res = api.get(url)
        assert response_data(res) == {"error":"test_error"}


#def get_api_cert_type():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_api_cert_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_api_cert_type(api):
    url = url_for("weko_admin.get_api_cert_type")
    with patch("weko_admin.views.get_api_certification_type",return_value=[{"api_code":"test_api","aip_name":"test_name"}]):
        res = api.get(url)
        assert response_data(res) == {"results":[{"api_code":"test_api","aip_name":"test_name"}],"error":""}

    # raises Exception
    with patch("weko_admin.views.get_api_certification_type",side_effect=Exception("test_error")):
        res = api.get(url)
        assert response_data(res) == {"results":"","error":"test_error"}


#def get_curr_api_cert(api_code=''):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_api_cert_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_curr_api_cert(api):
    url = url_for("weko_admin.get_curr_api_cert",api_code="test_code")
    with patch("weko_admin.views.get_current_api_certification",return_value={"api_code":"test_code","api_name":"test_name","cert_data":"test_data"}):
        res = api.get(url)
        assert response_data(res) == {"results":{"api_code":"test_code","api_name":"test_name","cert_data":"test_data"},"error":""}

    # raises Exception
    with patch("weko_admin.views.get_current_api_certification",side_effect=Exception("test_error")):
        res = api.get(url)
        assert response_data(res) == {"results":"","error":"test_error"}


#def save_api_cert_data():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_save_api_cert_data_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,is_permission",[
                         (0,True),# sysadmin
                         (1,False),# repoadmin
                         (2,False),# comadmin
                         (3,False),# contributor
                         (4,False),# generaluser
                         ])
def test_save_api_cert_data_acl(api,users,index,is_permission):
    url = url_for("weko_admin.save_api_cert_data")
    login_user_via_session(client=api, email=users[index]["email"])
    res = api.post(url,data=json.dumps({}),content_type="application/json")
    assert_role(res,is_permission)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_save_api_cert_data_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_save_api_cert_data_acl_guest(api):
    url = url_for("weko_admin.save_api_cert_data")
    res = api.post(url,data=json.dumps({}),content_type="application/json")
    assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_save_api_cert_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_save_api_cert_data(api, users):
    url = url_for("weko_admin.save_api_cert_data")
    login_user_via_session(client=api, email=users[0]["email"])
    # content_type != application/json
    res = api.post(url,data="test_data",content_type="plain/text")
    assert response_data(res) == {"error":"Header Error"}

    # cert_data is None
    data = {"api_code":"","cert_data":None}
    res = api.post(url,json=data)
    assert response_data(res) == {"error":"Account information is invalid. Please check again."}

    # api_code is 'crf' and validate_certification is True
    with patch("weko_admin.views.validate_certification",return_value=True):
        with patch("weko_admin.views.save_api_certification",return_value={"results":"success","error":""}):
            data = {"api_code":"crf","cert_data":"test_cert_data"}
            res = api.post(url,json=data)
            assert response_data(res) == {"results":"success","error":""}

    # api_code is 'oaa'
    with patch("weko_admin.views.save_api_certification",return_value={"results":"success","error":""}):
        data = {"api_code":"oaa","cert_data":"test_cert_data"}
        res = api.post(url,json=data)
        assert response_data(res) == {"results":"success","error":""}

    # else
    with patch("weko_admin.views.validate_certification",return_value=False):
        data = {"api_code":"","cert_data":"test_cert_data"}
        res = api.post(url,json=data)
        assert response_data(res) == {"error":"Account information is invalid. Please check again."}


#def get_init_selection(selection=""):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_init_selection -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_init_selection(api,mocker):
    mocker.patch("weko_admin.views.get_initial_stats_report",return_value={"target":[{"id":"1","data":"test_data"}]})
    mocker.patch("weko_admin.views.get_unit_stats_report",return_value={"unit":["test_value"]})

    # selection = target
    url = url_for("weko_admin.get_init_selection",selection="target")
    res = api.get(url)
    assert response_data(res) == {"target":[{"id":"1","data":"test_data"}]}

    # selection is other
    url = url_for("weko_admin.get_init_selection",selection="other")
    res = api.get(url)
    assert response_data(res) == {"unit":["test_value"]}

    with patch("weko_admin.views.get_unit_stats_report", side_effect=Exception("test_error")):
        url = url_for("weko_admin.get_init_selection",selection="other")
        res = api.get(url)
        assert response_data(res) == {"error":"test_error"}


#def get_email_author():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_email_author_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,is_permission",[
                         (0,True),# sysadmin
                         (1,True),# repoadmin
                         (2,True),# comadmin
                         (3,True),# contributor
                         (4,True),# generaluser
                         ])
def test_get_email_author_acl(api,users,index,is_permission):
    login_user_via_session(api,email=users[index]["email"])
    url = url_for("weko_admin.get_email_author")
    with patch("weko_admin.views.FeedbackMail.search_author_mail",return_value={}):
        res = api.post(url,json={},)
        assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_email_author_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_email_author_acl_guest(api):
    url = url_for("weko_admin.get_email_author")
    with patch("weko_admin.views.FeedbackMail.search_author_mail",return_value={}):
        res = api.post(url,json={},)
        assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_email_author -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_email_author(api,users):
    login_user_via_session(api,email=users[0]["email"])
    url = url_for("weko_admin.get_email_author")
    with patch("weko_admin.views.FeedbackMail.search_author_mail",return_value={"key":"value"}):
        res = api.post(url,json={"key":"data"})
        assert response_data(res) == {"key":"value"}

#def get_repository_list():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_repository_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,repositories",[
    (0,[{'id': 'Root Index'}, {'id': 'repo1'}]),
    (2,[{'id': 'repo1'}]),
    ])
@patch("invenio_communities.models.Community")
def test_get_repository_list(mock_community,api,users,index,repositories):
    url = url_for("weko_admin.get_repository_list")
    login_user_via_session(api, email=users[index]["email"])
    community = MagicMock(id="repo1")
    mock_community.query.all.return_value = [community]
    mock_community.get_repositories_by_user.return_value = [community]
    res = api.get(url)
    assert json.loads(res.data) == {'success': True, 'repositories': repositories, 'error': ''}

#def update_feedback_mail():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_update_feedback_mail_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,is_permission",[
                         (0,True),# sysadmin
                         (1,True),# repoadmin
                         (2,True),# comadmin
                         (3,False),# contributor
                         (4,False),# generaluser
                         ])
def test_update_feedback_mail_acl(api,users,index,is_permission):
    url = url_for("weko_admin.update_feedback_mail")
    login_user_via_session(client=api, email=users[index]["email"])
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={}):
        res = api.post(url,json={})
        assert_role(res,is_permission)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_update_feedback_mail_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_update_feedback_mail_guest(api):
    url = url_for("weko_admin.update_feedback_mail")
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={}):
        res = api.post(url,json={})
        assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_update_feedback_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_update_feedback_mail(api, users):
    url = url_for("weko_admin.update_feedback_mail")
    login_user_via_session(client=api, email=users[0]["email"])
    # update success
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={"error":""}):
        res = api.post(url,json={})
        assert response_data(res) == {"success":True, "error":""}

    # update failed
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={"error":"Cannot update Feedback email settings."}):
        res = api.post(url,json={})
        assert response_data(res) == {"success":False, "error":"Cannot update Feedback email settings."}


#def get_feedback_mail():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_feedback_mail_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,is_permission",[
                         (0,True),# sysadmin
                         (1,True),# repoadmin
                         (2,True),# comadmin
                         (3,False),# contributor
                         (4,False),# generaluser
                         ])
def test_get_feedback_mail_acl(api, users, index, is_permission):
    login_user_via_session(client=api, email=users[index]["email"])
    url = url_for("weko_admin.get_feedback_mail")
    with patch("weko_admin.views.FeedbackMail.get_feed_back_email_setting",return_value={"data":["datas"],"is_sending_feedback":True,"root_url":"http://test.com","error":""}):
        res = api.post(url)
        assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_feedback_mail_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_feedback_mail_acl_guest(api):
    url = url_for("weko_admin.get_feedback_mail")
    with patch("weko_admin.views.FeedbackMail.get_feed_back_email_setting",return_value={"data":["datas"],"is_sending_feedback":True,"root_url":"http://test.com","error":""}):
        res = api.post(url)
        assert res.status_code == 401

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_feedback_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_feedback_mail(api, users):
    login_user_via_session(client=api, email=users[0]["email"])
    url = url_for("weko_admin.get_feedback_mail")
    with patch("weko_admin.views.FeedbackMail.get_feed_back_email_setting",return_value={"data":["datas"],"is_sending_feedback":True,"root_url":"http://test.com","error":""}):
        res = api.post(url, json={"repo_id": "Root Index"})
        assert response_data(res) == {"data":["datas"],"is_sending_feedback":True,"error":""}

    # data.get(error)
    with patch("weko_admin.views.FeedbackMail.get_feed_back_email_setting",return_value={"error":"test_error"}):
        res = api.post(url, json={"repo_id": "Root Index"})
        assert response_data(res) == {"data":"","is_sending_feedback":"","error":"test_error"}


#def get_send_mail_history():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_send_mail_history -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_send_mail_history(api, mocker):
    mocker.patch("weko_admin.views.FeedbackMail.load_feedback_mail_history",side_effect=lambda x, y:{"page":x})
    url = url_for("weko_admin.get_send_mail_history")
    input = {"page":2, "repo_id":"Root Index"}
    res = api.get(url,query_string=input)
    assert response_data(res) == {"page":2}

    input = {"page":"not page", "repo_id":"Root Index"}
    res = api.get(url,query_string=input)
    assert response_data(res) == {"page":1}


#def get_failed_mail():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_failed_mail_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,is_permission",[
                         (0,True),# sysadmin
                         (1,True),# repoadmin
                         (2,False),# comadmin
                         (3,False),# contributor
                         (4,False),# generaluser
                         ])
def test_get_failed_mail_acl(api, users, index, is_permission, mocker):
    mocker.patch("weko_admin.views.FeedbackMail.load_feedback_failed_mail",side_effect=lambda x,y:{"history_id":x,"page":y})
    login_user_via_session(client=api, email=users[index]["email"])
    url = url_for("weko_admin.get_failed_mail")
    res = api.post(url,data={"page":5,"id":3})
    assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_failed_mail_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_failed_mail_acl_guest(api, mocker):
    mocker.patch("weko_admin.views.FeedbackMail.load_feedback_failed_mail",side_effect=lambda x,y:{"history_id":x,"page":y})
    url = url_for("weko_admin.get_failed_mail")
    res = api.post(url,data={"page":5,"id":3})
    assert res.status_code == 401

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_failed_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_failed_mail(api, users,mocker):
    mocker.patch("weko_admin.views.FeedbackMail.load_feedback_failed_mail",side_effect=lambda x,y:{"history_id":x,"page":y})
    login_user_via_session(client=api, email=users[0]["email"])
    url = url_for("weko_admin.get_failed_mail")
    res = api.post(url,json={"page":5,"id":3})
    assert response_data(res) == {"history_id":3,"page":5}

    res = api.post(url,json={"page":"not page","id":"not id"})
    assert response_data(res) == {"history_id":1,"page":1}

#def resend_failed_mail():
class Mock_FeedbackMail:
    @classmethod
    def get_mail_data_by_history_id(cls, history_id):
        pass

    @classmethod
    def update_history_after_resend(cls, history_id):
        pass

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_resend_failed_mail_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,is_permission",[
                         (0,True),# sysadmin
                         (1,True),# repoadmin
                         (2,False),# comadmin
                         (3,False),# contributor
                         (4,False),# generaluser
                         ])
def test_resend_failed_mail_acl(api, users, index, is_permission):
    login_user_via_session(client=api, email=users[index]["email"])
    url = url_for("weko_admin.resend_failed_mail")
    mock_feedbackmail = MagicMock(side_effect = Mock_FeedbackMail)
    with patch("weko_admin.views.FeedbackMail", mock_feedbackmail):
        with patch("weko_admin.views.StatisticMail.send_mail_to_all", return_value=""):
            res = api.post(url,data=json.dumps({}),content_type="application/json")
            assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_resend_failed_mail_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_resend_failed_mail_guest(api):
    mock_feedbackmail = MagicMock(side_effect = Mock_FeedbackMail)
    url = url_for("weko_admin.resend_failed_mail")
    with patch("weko_admin.views.FeedbackMail", mock_feedbackmail):
        with patch("weko_admin.views.StatisticMail.send_mail_to_all", return_value=""):
            res = api.post(url,data=json.dumps({}),content_type="application/json")
            assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_resend_failed_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_resend_failed_mail(api,users,mocker):
    url = url_for("weko_admin.resend_failed_mail")
    login_user_via_session(client=api, email=users[0]["email"])
    mocker.patch("weko_admin.views.FeedbackMail",side_effect=Mock_FeedbackMail)
    with patch("weko_admin.views.StatisticMail.send_mail_to_one"):
        res = api.post(url, json={"history_id":1})
        assert response_data(res) == {"success":True, "error":""}

    with patch("weko_admin.views.StatisticMail.send_mail_to_one",side_effect=Exception("test_error")):
        res = api.post(url, json={"history_id":1})
        assert response_data(res) == {"success":False, "error":"Request package is invalid"}

#def manual_send_site_license_mail(start_month, end_month):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_manual_send_site_license_mail_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,is_permission",[
                         (0,True),# sysadmin
                         (1,True),# repoadmin
                         (2,True),# comadmin
                         (3,False),# contributor
                         (4,False),# generaluser
                         ])
def test_manual_send_site_license_mail_acl(api,users,site_license,index,is_permission):
    url = url_for("weko_admin.manual_send_site_license_mail",start_month="202201",end_month="202203")
    login_user_via_session(client=api, email=users[index]["email"])
    with patch("weko_admin.views.QueryCommonReportsHelper.get", return_value={"institution_name":[]}):
        with patch("weko_admin.views.send_site_license_mail"):
            res = api.post(url,data={"repo_id": "Root Index"})
            assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_manual_send_site_license_mail_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_manual_send_site_license_mail_guest(api, site_license):
    url = url_for("weko_admin.manual_send_site_license_mail",start_month="202201",end_month="202203")
    with patch("weko_admin.views.QueryCommonReportsHelper.get", return_value={"institution_name":[]}):
        with patch("weko_admin.views.send_site_license_mail"):
            res = api.post(url,data=json.dumps({}),content_type="application/json")
            assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_manual_send_site_license_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_manual_send_site_license_mail(api, db, users, mocker):
    url = url_for("weko_admin.manual_send_site_license_mail",start_month="202201",end_month="202203")
    login_user_via_session(client=api, email=users[0]["email"])
    #res = api.post(url)
    #assert res == None

    site_license1 = SiteLicenseInfo(
        organization_id=0,
        organization_name="test data1",
        receive_mail_flag="T",
        mail_address="test@mail.com",
        domain_name="test_domain",
    )
    site_license2 = SiteLicenseInfo(
        organization_id=1,
        organization_name="test data2",
        receive_mail_flag="T",
        mail_address="test@mail.com",
        domain_name="test_domain",
    )
    db.session.add(site_license1)
    db.session.add(site_license2)
    db.session.commit()

    report_helper_result = {"institution_name":[{"name":"other_name"},{"name":"test data1"}]}
    mocker.patch("weko_admin.views.QueryCommonReportsHelper.get",return_value=report_helper_result)
    mock_send = mocker.patch("weko_admin.views.send_site_license_mail")
    res = api.post(url, data={"repo_id": "Root Index"})
    assert res.data == b"finished"
    mock_send.assert_has_calls(
        [mocker.call("test data1",["test@mail.com"],"202201-202203",{"name":"test data1"}),
        mocker.call("test data2",["test@mail.com"],"202201-202203",{"file_download":0,"file_preview":0,"record_view":0,"search":0,"top_view":0}),
        ]
    )

    # call with repo_id
    res = manual_send_site_license_mail("202201", "202203", "Root Index")
    assert res == "finished"
    mock_send.assert_has_calls(
        [mocker.call("test data1",["test@mail.com"],"202201-202203",{"name":"test data1"}),
        mocker.call("test data2",["test@mail.com"],"202201-202203",{"file_download":0,"file_preview":0,"record_view":0,"search":0,"top_view":0}),
        ]
    )

    # send_list is None
    SiteLicenseInfo.query.delete()
    db.session.commit()
    with pytest.raises(TypeError):
        res = api.post(url)

#def get_site_license_send_mail_settings():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_site_license_send_mail_settings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_site_license_send_mail_settings(db, api, users):
    url = url_for("weko_admin.get_site_license_send_mail_settings")
    login_user_via_session(client=api, email=users[0]["email"])

    site_license1 = SiteLicenseInfo(
        organization_id=0,
        organization_name="test data1",
        receive_mail_flag="T",
        mail_address="test@mail.com",
        domain_name="test_domain",
        repository_id="Root Index"
    )
    db.session.add(site_license1)
    db.session.commit()

    res = api.get(url, query_string={"repo_id":"Root Index"})
    assert response_data(res) == {'sitelicenses': [{
                                    'organization_id': 0,
                                    'organization_name': 'test data1',
                                    'receive_mail_flag': 'T',
                                    'mail_address': 'test@mail.com'}],
                                'auto_send': False}


    setting = AdminSettings(id=3,name='site_license_mail_settings',settings={"Root Index": {"auto_send_flag": True}})
    db.session.add(setting)
    db.session.commit()

    res = api.get(url, query_string={"repo_id":"Root Index"})
    assert response_data(res) == {'sitelicenses': [{
                                    'organization_id': 0,
                                    'organization_name': 'test data1',
                                    'receive_mail_flag': 'T',
                                    'mail_address': 'test@mail.com'}],
                                'auto_send': True}

#def update_site_info():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_update_site_info_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,is_permission",[
                         (0,True),# sysadmin
                         (1,True),# repoadmin
                         (2,False),# comadmin
                         (3,False),# contributor
                         (4,False),# generaluser
                         ])
def test_update_site_info_acl(api,users,index,is_permission):
    url = url_for("weko_admin.update_site_info")
    login_user_via_session(client=api, email=users[index]["email"])
    with patch("weko_admin.views.format_site_info_data", return_value=""):
        with patch("weko_admin.views.validation_site_info", return_value={"error":"error"}):
            res = api.post(url,data=json.dumps({}),content_type="application/json")
            assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_update_site_info_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_update_site_info_guest(api):
    url = url_for("weko_admin.update_site_info")
    with patch("weko_admin.views.format_site_info_data", return_value=""):
        with patch("weko_admin.views.validation_site_info", return_value={"error":"error"}):
            res = api.post(url,data=json.dumps({}),content_type="application/json")
            assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_update_site_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_update_site_info(api, users, mocker):
    url = url_for("weko_admin.update_site_info")
    login_user_via_session(client=api, email=users[0]["email"])

    mocker.patch("weko_admin.views.format_site_info_data",return_value={"format":"test_format_data"})
    mocker.patch("weko_admin.views.SiteInfo.update",return_value="update success")
    mocker.patch("weko_admin.views.overwrite_the_memory_config_with_db")
    with patch("weko_admin.views.validation_site_info",return_value={"error":"test_error"}):
        res = api.post(url, json={})
        assert response_data(res) == {"error":"test_error"}

    with patch("weko_admin.views.validation_site_info",return_value={}):
        res = api.post(url, json={})
        assert response_data(res) == {"format":"test_format_data"}


#def get_site_info():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_site_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_site_info(api,db,users,site_info,mocker):
    url = url_for("weko_admin.get_site_info")
    login_user_via_session(client=api, email=users[0]["email"])
    with patch("weko_admin.views.SiteInfo.get",return_value=None):
        res = api.get(url)
        assert res.status_code == 200
        assert response_data(res) == {"google_tracking_id_user":"test_google_tracking_id"}

        current_app.config.pop("GOOGLE_TRACKING_ID_USER")
        res = api.get(url)
        assert res.status_code == 200
        assert response_data(res) == {}

    current_app.config["GOOGLE_TRACKING_ID_USER"] = "test_tracking_id"

    test = {
        "copy_right":"test_copy_right1",
        "description":"test site info1.",
        "keyword":"test keyword1",
        "favicon":"test,favicon1",
        "favicon_name":"test favicon name1",
        "site_name":[{"name":"name11"}],
        "notify":{"name":"notify11"},
        "google_tracking_id_user":"11",
        "ogp_image":"http://test_server/api/admin/ogp_image",
        "ogp_image_name":"test ogp image name1"
    }
    #with patch("weko_admin.views.SiteInfo.get",return_value=site_info[0]):
    res = api.get(url)
    assert response_data(res) == test

    test = {
        "copy_right":"test_copy_right2",
        "description":"test site info2.",
        "keyword":"test keyword2",
        "favicon":"test favicon2",
        "favicon_name":"test favicon name2",
        "site_name":{"name":"name21"},
        "notify":{"name":"notify21"},
        "google_tracking_id_user":None,
    }
    SiteInfo.query.delete()
    db.session.commit()
    db.session.add(site_info[1])
    db.session.commit()
    #with patch("weko_admin.views.SiteInfo.get",return_value=site_info[1]):
    res = api.get(url)
    assert response_data(res) == test

    current_app.config.pop("GOOGLE_TRACKING_ID_USER")
    test = {
        "copy_right":"test_copy_right2",
        "description":"test site info2.",
        "keyword":"test keyword2",
        "favicon":"test favicon2",
        "favicon_name":"test favicon name2",
        "site_name":{"name":"name21"},
        "notify":{"name":"notify21"},
        "google_tracking_id_user":None,
    }
    res = api.get(url)
    assert response_data(res) == test


#def get_avatar():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_avatar -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_avatar(api,site_info,mocker):
    url = url_for("weko_admin.get_avatar")
    with patch("weko_admin.views.SiteInfo.get",return_value=None):
        res = api.get(url)
        assert response_data(res) == {}

    res = api.get(url)
    assert res.status_code == 200


#def get_ogp_image():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_ogp_image -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_ogp_image(api, db, site_info, file_instance, mocker):
    url = url_for("weko_admin.get_ogp_image")

    mock_send = mocker.patch("invenio_files_rest.models.FileInstance.send_file",return_value=make_response())
    res = api.get(url)
    mock_send.assert_called_with(
        "test ogp image name1",
        mimetype="application/octet-stream",
        as_attachment=True
    )

    with patch("invenio_files_rest.models.FileInstance.get_by_uri",return_value=None):
        res = api.get(url)
        assert response_data(res) == {}
    SiteInfo.query.delete()
    db.session.commit()
    res = api.get(url)
    assert response_data(res) == {}



#def get_search_init_display_index(selected_index=None):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_search_init_display_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_search_init_display_index(api):
    url = url_for("weko_admin.get_search_init_display_index",selected_index=1)
    data = [{"id":"0","parent":"#","text":"Root Index","state":{"opened":True}}]
    with patch("weko_admin.views.get_init_display_index",return_value=data):
        res = api.get(url)
        assert response_data(res) == {"indexes":data}


#def save_restricted_access():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_search_init_display_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,is_permission",[
                         (0,True),# sysadmin
                         (1,True),# repoadmin
                         (2,False),# comadmin
                         (3,False),# contributor
                         (4,False),# generaluser
                         ])
def test_save_restricted_access_acl(api,users,index,is_permission):
    url = url_for("weko_admin.save_restricted_access")
    login_user_via_session(client=api, email=users[index]["email"])
    with patch("weko_admin.views.update_restricted_access",return_value=True):
        res = api.post(url,data=json.dumps({}),content_type="application/json")
        assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_save_restricted_access_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_save_restricted_access_guest(api):
    url = url_for("weko_admin.save_restricted_access")
    with patch("weko_admin.views.update_restricted_access",return_value=True):
        res = api.post(url,data=json.dumps({}),content_type="application/json")
        assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_save_restricted_access -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_save_restricted_access(api, users):
    url = url_for("weko_admin.save_restricted_access")
    login_user_via_session(client=api, email=users[0]["email"])
    with patch("weko_admin.views.update_restricted_access",return_value=False):
        res = api.post(url,json={})
        assert response_data(res) == {"status":False,"msg":"Could not save data."}

    with patch("weko_admin.views.update_restricted_access",return_value=True):
        res = api.post(url,json={})
        assert response_data(res) == {"status":True,"msg":"Restricted Access was successfully updated."}


#def get_usage_report_activities():
class MockUsageReport:
    def __init__(self):
        pass

    def get_activities_per_page(self, activities_id, size, page):
        return {}
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_usage_report_activities_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,is_permission",[
                         (0,True),# sysadmin
                         (1,True),# repoadmin
                         (2,False),# comadmin
                         (3,False),# contributor
                         (4,False),# generaluser
                         ])
def test_get_usage_report_activities_acl(api,users,index,is_permission):
    url = url_for("weko_admin.get_usage_report_activities")
    login_user_via_session(client=api, email=users[index]["email"])
    mock_usagereport = MagicMock(side_effect=MockUsageReport)
    with patch("weko_admin.views.UsageReport", mock_usagereport):
        res = api.post(url,data=json.dumps({}),content_type="application/json")
        assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_usage_report_activities_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_usage_report_activities_guest(api):
    url = url_for("weko_admin.get_usage_report_activities")
    mock_usagereport = MagicMock(side_effect=MockUsageReport)
    with patch("weko_admin.views.UsageReport", mock_usagereport):
        res = api.post(url,data=json.dumps({}),content_type="application/json")
        assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_get_usage_report_activities -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_get_usage_report_activities(api,users,mocker):
    url = url_for("weko_admin.get_usage_report_activities")
    login_user_via_session(client=api, email=users[0]["email"])
    res = api.get(url,query_string={"page":3,"size":10})
    assert response_data(res) == {"page":1,"size":10,"activities":[],"number_of_pages":0}

    res = api.post(url,json={"page":3,"size":10,"activity_ids":[1]})
    assert response_data(res) == {"page":1,"size":10,"activities":[],"number_of_pages":0}


#def send_mail_reminder_usage_report():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_send_mail_reminder_usage_report_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,is_permission",[
                         (0,True),# sysadmin
                         (1,True),# repoadmin
                         (2,False),# comadmin
                         (3,False),# contributor
                         (4,False),# generaluser
                         ])
def test_send_mail_reminder_usage_report_acl(api,users,index,is_permission):
    url = url_for("weko_admin.send_mail_reminder_usage_report")
    login_user_via_session(client=api, email=users[index]["email"])
    res = api.post(url,data=json.dumps({}),content_type="application/json")
    assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_send_mail_reminder_usage_report_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_send_mail_reminder_usage_report_guest(api):
    url = url_for("weko_admin.send_mail_reminder_usage_report")
    res = api.post(url,data=json.dumps({}),content_type="application/json")
    assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_send_mail_reminder_usage_report -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_send_mail_reminder_usage_report(api,users,mocker):
    login_user_via_session(client=api, email=users[0]["email"])
    class MockUsage:
        def send_reminder_mail(self,activities_id,mail_id=None,activities=None,forced_send=False):
            return True
    mocker.patch("weko_admin.views.UsageReport",return_value=MockUsage())

    url = url_for("weko_admin.send_mail_reminder_usage_report")
    res = api.post(url,json={})
    assert response_data(res) == {"status":False}

    url = url_for("weko_admin.send_mail_reminder_usage_report")
    res = api.post(url,json={"activity_ids":[1,2,3]})
    assert response_data(res) == {"status":True}


#def save_facet_search():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_save_facet_search_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,is_permission",[
                         (0,True),# sysadmin
                         (1,True),# repoadmin
                         (2,False),# comadmin
                         (3,False),# contributor
                         (4,False),# generaluser
                         ])
def test_save_facet_search_acl(api,users,index,is_permission):
    url = url_for("weko_admin.save_facet_search")
    login_user_via_session(client=api, email=users[index]["email"])
    with patch("weko_admin.views.is_exits_facet", return_value=True):
        with patch("weko_admin.views.store_facet_search_query_in_redis", return_value=""):
            res = api.post(url,data=json.dumps({}),content_type="application/json")
            assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_save_facet_search_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_save_facet_search_guest(api):
    url = url_for("weko_admin.save_facet_search")
    with patch("weko_admin.views.is_exits_facet", return_value=True):
        with patch("weko_admin.views.store_facet_search_query_in_redis", return_value=""):
            res = api.post(url,data=json.dumps({}),content_type="application/json")
            assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_save_facet_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_save_facet_search(api, users, mocker):
    mocker.patch("weko_admin.views.store_facet_search_query_in_redis")
    url = url_for("weko_admin.save_facet_search")
    login_user_via_session(client=api, email=users[0]["email"])
    with patch("weko_admin.views.is_exits_facet",return_value=True):
        res = api.post(url,json={"id":1})
        assert response_data(res) == {"status":False,"msg":"The item name/mapping is already exists. Please input other faceted item/mapping."}
    with patch("weko_admin.views.is_exits_facet",return_value=False):
        with patch("weko_admin.views.FacetSearchSetting.create",return_value=True):
            res = api.post(url,json={})
            assert response_data(res) == {"status":True, "msg":"Success"}

        with patch("weko_admin.views.FacetSearchSetting.create",return_value=False):
            res = api.post(url,json={})
            assert response_data(res) == {"status":False,"msg":"Failed to create due to server error."}

        with patch("weko_admin.views.FacetSearchSetting.update_by_id",return_value=True):
            res = api.post(url,json={"id":[2]})
            assert response_data(res) == {"status":True, "msg":"Success"}
        with patch("weko_admin.views.FacetSearchSetting.update_by_id",return_value=False):
            res = api.post(url,json={"id":[2]})
            assert response_data(res) == {"status":False,"msg":"Failed to update due to server error."}


#def remove_facet_search():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_remove_facet_search_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index,is_permission",[
                         (0,True),# sysadmin
                         (1,True),# repoadmin
                         (2,False),# comadmin
                         (3,False),# contributor
                         (4,False),# generaluser
                         ])
def test_remove_facet_search_acl(api,users,index,is_permission):
    url = url_for("weko_admin.remove_facet_search")
    login_user_via_session(client=api, email=users[index]["email"])
    data = {"id":[]}
    with patch("weko_admin.views.store_facet_search_query_in_redis", return_value={}):
        res = api.post(url,data=json.dumps(data),content_type="application/json")
        assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_remove_facet_search_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_remove_facet_search_guest(api):
    url = url_for("weko_admin.remove_facet_search")
    data = {"id":[]}
    with patch("weko_admin.views.store_facet_search_query_in_redis", return_value={}):
        res = api.post(url,data=json.dumps(data),content_type="application/json")
        assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_remove_facet_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_remove_facet_search(api, users, mocker):
    url = url_for("weko_admin.remove_facet_search")
    login_user_via_session(client=api, email=users[0]["email"])
    mocker.patch("weko_admin.views.store_facet_search_query_in_redis")
    res = api.post(url,json={"id":""})
    assert response_data(res) == {"status":False,"msg":"Failed to delete due to server error."}

    with patch("weko_admin.views.FacetSearchSetting.delete",return_value=True):
        res = api.post(url,json={"id":"1"})
        assert response_data(res) == {"status":True,"msg":"Success"}
    with patch("weko_admin.views.FacetSearchSetting.delete",return_value=False):
        res = api.post(url,json={"id":"1"})
        assert response_data(res) == {"status":False,"msg":"Failed to delete due to server error."}


# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_dbsession_clean -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_dbsession_clean(app, db):
    from weko_records.models import ItemTypeName
    # exist exception
    itemtype_name1 = ItemTypeName(id=1,name="テスト1",has_site_license=True, is_active=True)
    db.session.add(itemtype_name1)
    dbsession_clean(None)
    assert ItemTypeName.query.filter_by(id=1).first().name == "テスト1"

    # raise Exception
    itemtype_name2 = ItemTypeName(id=2,name="テスト2",has_site_license=True, is_active=True)
    db.session.add(itemtype_name2)
    with patch("weko_items_autofill.views.db.session.commit",side_effect=Exception):
        dbsession_clean(None)
        assert ItemTypeName.query.filter_by(id=2).first() is None

    # not exist exception
    itemtype_name3 = ItemTypeName(id=3,name="テスト3",has_site_license=True, is_active=True)
    db.session.add(itemtype_name3)
    dbsession_clean(Exception)
    assert ItemTypeName.query.filter_by(id=3).first() is None


# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_send_profile_settings_save -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_send_profile_settings_save(api, users):
    url = url_for("weko_admin.send_profile_settings_save")
    login_user_via_session(client=api, email=users[0]["email"])

    # 正常系テスト
    valid_data = {
        "profiles_templates": {
            "fullname": {"label_name": "Full Name", "visible": True, "format": "text", "options": []},
            "university": {"label_name": "University", "visible": True, "format": "text", "options": []}
        }
    }

    with patch("weko_admin.models.AdminSettings.update", return_value=True):
        res = api.post(url, json=valid_data)
        assert response_data(res) == {"status": "success", "msg": "Settings updated successfully"}

    # 無効なデータテスト
    invalid_data = {}

    res = api.post(url, json=invalid_data)
    assert response_data(res) == {"status": "error", "msg": "Invalid data"}

    # 例外発生時のテスト
    with patch("weko_admin.models.AdminSettings.update", side_effect=Exception('DB error')):
        res = api.post(url, json=valid_data)
        assert response_data(res) == {"status": "error", "msg": "Failed to update settings"}
