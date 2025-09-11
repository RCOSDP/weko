from unittest.mock import MagicMock
import pytest
import json
import redis
from invenio_accounts.models import Role
from flask import url_for,request,make_response,current_app,Flask
from flask_login.utils import login_user,logout_user
from flask_menu import current_menu
from flask_security import url_for_security
from mock import patch
from invenio_accounts.models import User
from weko_accounts.api import ShibUser
from weko_accounts.models import ShibbolethUser
from weko_accounts.views import (
    _has_admin_access,
    init_menu,
    _redirect_method,
    find_user_by_email,
    shib_sp_login,
    _adjust_shib_admin_DB,
    urlencode
)
from weko_admin.models import AdminSettings

def set_session(client,data):
    with client.session_transaction() as session:
        for k, v in data.items():
            session[k] = v
#def _has_admin_access():
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_has_admin_access -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
#def test_has_admin_access(request_context,users):
#    login_user(users[0]["obj"])
#    result = _has_admin_access()
#    assert result == True
#    logout_user()
#    login_user(users[4]["obj"])
#    result = _has_admin_access()
#    assert result == False
#def init_menu():
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_init_menu -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_init_menu(request_context):
    init_menu()
    assert current_menu.submenu("setting.admin").active == True
    assert current_menu.submenu("settings.admin").url == "/admin/"
    assert current_menu.submenu("settings.admin").text == '<i class="fa fa-cogs fa-fw"></i> Administration'


# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_adjust_shib_admin_DB -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_adjust_shib_admin_DB(app, db, mocker):
    # TESTING=True
    with patch("weko_accounts.views.AdminSettings.query.filter_by") as mock_filter:
        _adjust_shib_admin_DB()
        assert mock_filter.call_count == 0

    # TESTING=False, AdminSettings not exist
    app.config.update(TESTING=False)
    adminsettings = AdminSettings(id=1, name="test")
    db.session.add(adminsettings)
    db.session.commit()
    _adjust_shib_admin_DB()
    assert AdminSettings.query.filter_by(name="blocked_user_settings").first() is not None
    assert AdminSettings.query.filter_by(name="shib_login_enable").first() is not None
    assert AdminSettings.query.filter_by(name="shib_login_enable").first() is not None
    assert AdminSettings.query.filter_by(name="default_role_settings").first() is not None

    # TESTING=False, AdminSettings exist
    app.config.update(WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED=True)
    with patch("weko_accounts.views.db.session.add") as db_add, \
            patch("weko_accounts.views.db.session.commit") as db_commit:
        _adjust_shib_admin_DB()
        assert db_add.call_count == 0
        assert db_commit.call_count == 3


#def _redirect_method(has_next=False):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_redirect_method -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_redirect_method(app,mocker):
    url = "/test?page=1&size=10"
    with app.test_request_context(url):
        mock_render = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
        _redirect_method(False)
        mock_render.assert_called_with(url_for('security.login'))

        mock_render = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
        _redirect_method(True)
        mock_render.assert_called_with(url_for('security.login',next=url))

        current_app.config.update(
            WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED=True
        )
        mock_render = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
        _redirect_method(False)
        mock_render.assert_called_with("http://test_server.localdomain/secure/login.py")

        mock_render = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
        _redirect_method(True)
        mock_render.assert_called_with("http://test_server.localdomain/secure/login.py?next="+url)

#def index():
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_index(client,mocker):
    mock_render = mocker.patch("weko_accounts.views.render_template",return_value=make_response())
    res = client.get(url_for("weko_accounts.index"))
    mock_render.assert_called_with("weko_accounts/index.html",module_name="WEKO-Accounts")

#def shib_auto_login():
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_shib_auto_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_shib_auto_login(client,redis_connect,mocker):
    url = url_for("weko_accounts.shib_auto_login")
    set_session(client,{"shib_session_id":None})
    # not exist shib_session_id
    mock_redirect_ = mocker.patch("weko_accounts.views._redirect_method",return_value=make_response())
    client.get(url)
    mock_redirect_.assert_called_once()


    mocker.patch("weko_accounts.views.RedisConnection.connection",return_value=redis_connect)
    # not exist cache
    mock_redirect_ = mocker.patch("weko_accounts.views._redirect_method",return_value=make_response())
    client.get(url+"?Shib-Session-ID=2222")
    mock_redirect_.assert_called_once()



    redis_connect.put("Shib-Session-1111",bytes("","utf-8"))
    # not cache_val
    mock_redirect_ = mocker.patch("weko_accounts.views._redirect_method",return_value=make_response())
    client.get(url+"?Shib-Session-ID=1111")
    mock_redirect_.assert_called_once()
    assert redis_connect.redis.exists("Shib-Session-1111") == False

    mock_get_relation = mocker.patch("weko_accounts.views.ShibUser.get_relation_info")
    mock_new_relation = mocker.patch("weko_accounts.views.ShibUser.new_relation_info")
    mock_shib_login = mocker.patch("weko_accounts.views.ShibUser.shib_user_login")

    redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))
    # is_auto_bind is false, check_in is error
    mock_redirect_ = mocker.patch("weko_accounts.views._redirect_method",return_value=make_response())
    with patch("weko_accounts.views.ShibUser.check_in",return_value="test_error"):
        client.get(url+"?Shib-Session-ID=1111")
        mock_get_relation.assert_called_once()
        mock_redirect_.assert_called_once()
        assert redis_connect.redis.exists("Shib-Session-1111") == False

    redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))

    set_session(client,{"shib_session_id":"1111"})
    with patch("weko_accounts.views.ShibUser.check_in",return_value=None):
        # is_auto_bind is true,shib_user is None
        shibuser = ShibUser({})
        shibuser.user = User(id=1)
        with patch("weko_accounts.views.ShibUser",return_value=shibuser):
            mock_redirect = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
            client.get(url)
            mock_new_relation.assert_called_once()
            mock_shib_login.assert_not_called()
            mock_redirect.assert_called_with("/")
            assert redis_connect.redis.exists("Shib-Session-1111") == False

        # is_auto_bind is true,shib_user exis
        redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))
        set_session(client,{"shib_session_id":"1111","next":"/next_page"})

        shibuser = ShibUser({})
        shibuser.shib_user = "test_user"
        shibuser.user = User(id=1)
        with patch("weko_accounts.views.ShibUser",return_value=shibuser):
            mock_redirect = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
            client.get(url+'?next=/next_page')
            mock_redirect.assert_called_with("/next_page")
            mock_shib_login.assert_called_once()
            assert redis_connect.redis.exists("Shib-Session-1111") == False
    # raise BaseException
    with patch("weko_accounts.views.RedisConnection",side_effect=BaseException("test_error")):
        res = client.get(url+"?Shib-Session-ID=1111")
        assert res.status_code == 400
#def confirm_user():
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_confirm_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_confirm_user(client,redis_connect,mocker):
    mocker.patch("weko_accounts.views.RedisConnection.connection",return_value=redis_connect)
    mocker.patch("weko_accounts.views.ShibUser.shib_user_login")
    url = url_for("weko_accounts.confirm_user")

    # not correct csrf_random
    set_session(client,{"csrf_random":"xxxx"})
    form = {"csrf_random":"test_csrf"}
    mock_flash = mocker.patch("weko_accounts.views.flash")
    client.post(url,data=form)
    mock_flash.assert_called_with("csrf_random",category="error")

    # not exist shib_session_id
    set_session(client,{"csrf_random":"test_csrf","shib_session_id":None})
    mock_flash = mocker.patch("weko_accounts.views.flash")
    client.post(url,data=form)
    mock_flash.assert_called_with("shib_session_id",category="error")

    # not exist cache_key
    set_session(client,{"csrf_random":"test_csrf","shib_session_id":"2222"})
    mock_flash = mocker.patch("weko_accounts.views.flash")
    client.post(url,data=form)
    mock_flash.assert_called_with("cache_key",category="error")

    set_session(client,{"csrf_random":"test_csrf","shib_session_id":"1111"})
    # not exist cache_value
    redis_connect.put("Shib-Session-1111",bytes("","utf-8"))
    mock_flash = mocker.patch("weko_accounts.views.flash")
    client.post(url,data=form)
    mock_flash.assert_called_with("cache_val",category="error")
    assert redis_connect.redis.exists("Shib-Session-1111") is False

    # shib_user.check_weko_user is false
    redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))
    with patch("weko_accounts.views.ShibUser.check_weko_user",return_value=False):
        mock_flash = mocker.patch("weko_accounts.views.flash")
        client.post(url,data=form)
        mock_flash.assert_called_with("check_weko_user",category="error")
        assert redis_connect.redis.exists("Shib-Session-1111") is False

    redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))
    with patch("weko_accounts.views.ShibUser.check_weko_user",return_value=True):
        # shib_user.bind_relation_info is false
        with patch("weko_accounts.views.ShibUser.bind_relation_info",return_value=False):
            redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))
            mock_flash = mocker.patch("weko_accounts.views.flash")
            client.post(url,data=form)
            mock_flash.assert_called_with("FAILED bind_relation_info!",category="error")
        with patch("weko_accounts.views.ShibUser.bind_relation_info",return_value=True):
            # ShibUser.check_in is error
            with patch("weko_accounts.views.ShibUser.check_in",return_value="test_error"):
                mock_flash = mocker.patch("weko_accounts.views.flash")
                client.post(url,data=form)
                mock_flash.assert_called_with("test_error",category="error")
                assert redis_connect.redis.exists("Shib-Session-1111") is False
            with patch("weko_accounts.views.ShibUser.check_in",return_value=None):
                # ShibUser.shib_user is None,not exist next in session
                redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))
                shibuser = ShibUser({})
                shibuser.user = User(id=1)
                with patch("weko_accounts.views.ShibUser",return_value=shibuser):
                    mock_redirect = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
                    client.post(url,data=form)
                    mock_redirect.assert_called_with("/")
                    assert redis_connect.redis.exists("Shib-Session-1111") is False

                    # exist ShibUser.shib_user
                    set_session(client,{"csrf_random":"test_csrf","shib_session_id":"1111","next":"/next_page"})
                    redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))

                shibuser = ShibUser({})
                shibuser.shib_user = "test_user"
                shibuser.user = User(id=1)
                with patch("weko_accounts.views.ShibUser",return_value=shibuser):
                    mock_redirect = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
                    mock_flash = mocker.patch("weko_accounts.views.flash")
                    client.post(url,data=form)
                    mock_redirect.assert_called_with("/next_page")
                    assert redis_connect.redis.exists("Shib-Session-1111") is False

    # raise BaseException
    with patch("weko_accounts.views._redirect_method",side_effect=BaseException("test_error")):
        res = client.post(url,data=form)
        assert res.status_code == 400

#def confirm_user_without_page():
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_confirm_user_without_page -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_confirm_user_without_page(client,redis_connect,mocker):
    mocker.patch("weko_accounts.views.RedisConnection.connection",return_value=redis_connect)
    mocker.patch("weko_accounts.views.ShibUser.shib_user_login")
    url = url_for("weko_accounts.confirm_user_without_page")

    # not exist shib_session_id
    mock_flash = mocker.patch("weko_accounts.views.flash")
    client.get(url, query_string={"Shib-Session-ID":None})
    mock_flash.assert_called_with("shib_session_id",category="error")

    # not exist cache_key
    mock_flash = mocker.patch("weko_accounts.views.flash")
    client.get(url, query_string={"Shib-Session-ID":"2222"})
    mock_flash.assert_called_with("cache_key",category="error")

    # not exist cache_value
    redis_connect.put("Shib-Session-1111",bytes("","utf-8"))
    mock_flash = mocker.patch("weko_accounts.views.flash")
    client.get(url, query_string={"Shib-Session-ID":"1111"})
    mock_flash.assert_called_with("cache_val",category="error")
    assert redis_connect.redis.exists("Shib-Session-1111") is False

    redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))
    with patch("weko_accounts.views.ShibUser.check_weko_user",return_value=True):
        # shib_user.bind_relation_info is false
        with patch("weko_accounts.views.ShibUser.bind_relation_info",return_value=False):
            redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))
            mock_flash = mocker.patch("weko_accounts.views.flash")
            client.get(url, query_string={"Shib-Session-ID":"1111"})
            mock_flash.assert_called_with("FAILED bind_relation_info!",category="error")
            assert redis_connect.redis.exists("Shib-Session-1111") is False
        with patch("weko_accounts.views.ShibUser.bind_relation_info",return_value=True):
            # ShibUser.check_in is error
            with patch("weko_accounts.views.ShibUser.check_in",return_value="test_error"):
                redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))
                mock_flash = mocker.patch("weko_accounts.views.flash")
                client.get(url, query_string={"Shib-Session-ID":"1111"})
                mock_flash.assert_called_with("test_error",category="error")
                assert redis_connect.redis.exists("Shib-Session-1111") is False
            with patch("weko_accounts.views.ShibUser.check_in",return_value=None):
                # ShibUser.shib_user is None,not exist next in session
                redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))
                mock_redirect = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
                client.get(url, query_string={"Shib-Session-ID":"1111"})
                mock_redirect.assert_called_with("/")
                assert redis_connect.redis.exists("Shib-Session-1111") is False

                # exist ShibUser.shib_user
                redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))

                shibuser = ShibUser({})
                shibuser.shib_user = "test_user"
                with patch("weko_accounts.views.ShibUser",return_value=shibuser):
                    mock_redirect = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
                    mock_flash = mocker.patch("weko_accounts.views.flash")
                    client.get(url, query_string={"Shib-Session-ID":"1111"})
                    mock_redirect.assert_called_with("/")
                    assert redis_connect.redis.exists("Shib-Session-1111") is False

                # exist ShibUser.shib_user
                redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))

                shibuser = ShibUser({})
                shibuser.shib_user = "test_user"
                with patch("weko_accounts.views.ShibUser",return_value=shibuser):
                    mock_redirect = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
                    mock_flash = mocker.patch("weko_accounts.views.flash")
                    client.get(url, query_string={"Shib-Session-ID":"1111","next":"/next_page"})
                    mock_redirect.assert_called_with("/next_page")
                    assert redis_connect.redis.exists("Shib-Session-1111") is False

    # raise BaseException
    with patch("weko_accounts.views._redirect_method",side_effect=BaseException("test_error")):
        res = client.get(url)
        assert res.status_code == 400


#def shib_login():
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_shib_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_shib_login(client,redis_connect,users,mocker):
    mocker.patch("weko_accounts.views.RedisConnection.connection",return_value=redis_connect)
    mocker.patch("weko_accounts.views.generate_random_str",return_value="asdfghjkl")
    url_base = url_for("weko_accounts.shib_login")

    # not shib_session_id
    mock_flash = mocker.patch("weko_accounts.views.flash")
    client.get(url_base)
    mock_flash.assert_called_with("Missing Shib-Session-ID!",category="error")

    url = url_base+"?Shib-Session-ID=2222"

    # not exist cache_key
    mock_flash = mocker.patch("weko_accounts.views.flash")
    client.get(url)
    mock_flash.assert_called_with("Missing SHIB_CACHE_PREFIX!",category="error")

    url = url_base+"?Shib-Session-ID=1111"
    # not cache_val
    redis_connect.put("Shib-Session-1111",bytes('',"utf-8"))
    mock_flash = mocker.patch("weko_accounts.views.flash")
    client.get(url)
    mock_flash.assert_called_with("Missing SHIB_ATTR!",category="error")
    assert redis_connect.redis.exists("Shib-Session-1111") is False

    # exist user
    redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn","shib_mail":"user@test.org"}',"utf-8"))
    mock_render = mocker.patch("weko_accounts.views.render_template",return_value=make_response())
    client.get(url)
    mock_render.assert_called_with('weko_accounts/confirm_user.html',csrf_random="asdfghjkl",email="user@test.org")

    # not exist user
    redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn","shib_mail":"not_exist_user@test.org"}',"utf-8"))
    mock_render = mocker.patch("weko_accounts.views.render_template",return_value=make_response())
    client.get(url)
    mock_render.assert_called_with('weko_accounts/confirm_user.html',csrf_random="asdfghjkl",email="")

    # raise BaseException
    with patch("weko_accounts.views.flash",side_effect=BaseException("test_error")):
        res = client.get(url_base)
        assert res.status_code == 400

#def shib_sp_login():
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_shib_sp_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_shib_sp_login(client, redis_connect,mocker, db, users):
    mocker.patch("weko_accounts.views.RedisConnection.connection",return_value=redis_connect)
    url = url_for("weko_accounts.shib_sp_login")

    # not shib_session_id
    with patch("weko_accounts.views.redirect",return_value=make_response()) as mock_redirect:
        mock_flash = mocker.patch("weko_accounts.views.flash")
        client.post(url,data={})
        mock_flash.assert_called_with("Missing Shib-Session-ID!",category="error")
        mock_redirect.assert_called_with(url_for("security.login"))

    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED=True
    )
    form = {
        "SShib-Session-ID":"1111"
    }

    # parse_attribute is error
    with patch("weko_accounts.views.parse_attributes",return_value=("attr",True)):
        mock_flash = mocker.patch("weko_accounts.views.flash")
        client.post(url,data=form)
        mock_flash.assert_called_with("Missing SHIB_ATTRs!",category="error")

    # Check if shib_eppn is not included in the blocked user list
    try:
        db.session.add(AdminSettings(
            id=11,
            name="blocked_user_settings",
            settings='{"blocked_ePPNs": ["ePPN1", "ePPN2", "ePPN3", "ePPN5", "ePPP*"]}'
        ))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise
    finally:
        db.session.remove()

    # Match with blocked user
    mock_flash = mocker.patch("weko_accounts.views.flash")
    form = {
        "Shib-Session-ID":"1111",
        "eppn":"ePPN3"
    }
    client.post(url,data=form)
    mock_flash.assert_called_with("Failed to login.",category="error")
    mock_redirect_ = mocker.patch("weko_accounts.views._redirect_method",return_value=make_response())

    # Match found with a blocked user from the wildcard
    mock_flash = mocker.patch("weko_accounts.views.flash")
    form = {
        "Shib-Session-ID":"1111",
        "eppn":"ePPP3"
    }
    client.post(url,data=form)
    mock_flash.assert_called_with("Failed to login.",category="error")
    mock_redirect_ = mocker.patch("weko_accounts.views._redirect_method",return_value=make_response())

    # Not a blocked user
    form = {
        "Shib-Session-ID":"1111",
        "eppn":"test_eppn"
    }

    # WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPSがTrueの場合のテスト
    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS=True
    )
    mock_sync_shib_gakunin_map_groups = mocker.patch("weko_accounts.views.sync_shib_gakunin_map_groups", return_value=None)
    client.post(url, data=form)
    mock_sync_shib_gakunin_map_groups.assert_called_once()

    # sync_shib_gakunin_map_groupsが例外をスローする場合のテスト
    mock_sync_shib_gakunin_map_groups = mocker.patch("weko_accounts.views.sync_shib_gakunin_map_groups", side_effect=Exception("test_exception"))
    mock_redirect_method = mocker.patch("weko_accounts.views._redirect_method", return_value=make_response())
    res = client.post(url, data=form)
    mock_redirect_method.assert_called_once()
    assert res.status_code == 200  # _redirect_methodが呼び出されることを確認

    # WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPSがFalseの場合のテスト
    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS=False
    )
    mock_sync_shib_gakunin_map_groups.reset_mock()
    res = client.post(url, data=form)
    mock_sync_shib_gakunin_map_groups.assert_not_called()

    # shib_user.get_relation_info is None
    with patch("weko_accounts.views.ShibUser.get_relation_info",return_value=None)\
        and patch("weko_accounts.views.redirect",return_value=make_response()):
        res = client.post(url,data=form)
        assert res.status_code == 200
        assert res.data.decode() == "/weko/shib/login?Shib-Session-ID=1111&next=%2F"
        with client.session_transaction() as session:
            assert 'shib_session_id' not in session
    # shib_user.get_relation_info is not None
    with patch("weko_accounts.views.ShibUser.get_relation_info",return_value="chib_user")\
        and patch("weko_accounts.views.redirect",return_value=make_response()):
        res = client.post(url,data=form)
        assert res.status_code == 200
        assert res.data.decode() == "/weko/shib/login?Shib-Session-ID=1111&next=%2F"
        with client.session_transaction() as session:
            assert 'shib_session_id' not in session

    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED=True,
        WEKO_ACCOUNTS_SKIP_CONFIRMATION_PAGE=True
    )
    # shib_user.get_relation_info is None
    with patch("weko_accounts.views.ShibUser.get_relation_info",return_value=None):
        with patch("weko_accounts.views.find_user_by_email",return_value=None):
            res = client.post(url,data=form)
            assert res.status_code == 200
            # assert res.data.decode() == "/weko/confim/user/skip?Shib-Session-ID=1111&next=%2F"
            assert res.data.decode() == "/weko/auto/login?next=%2F"
            with client.session_transaction() as session:
                assert session.get("shib_session_id") == "1111"
                session.clear()
        with patch("weko_accounts.views.find_user_by_email",return_value="shib_user"):
            res = client.post(url,data=form)
            assert res.status_code == 200
            # assert res.data.decode() == "/weko/auto/login?Shib-Session-ID=1111&next=%2F"
            assert res.data.decode() == "/weko/confim/user/skip?Shib-Session-ID=1111&next=%2F"
            with client.session_transaction() as session:
                assert 'shib_session_id' not in session

    # shib_user.get_relation_info is not None
    with patch("weko_accounts.views.ShibUser.get_relation_info",return_value="shib_user"):
        res = client.post(url,data=form)
        assert res.status_code == 200
        assert res.data.decode() == "/weko/auto/login?Shib-Session-ID=1111&next=%2F"
        with client.session_transaction() as session:
            assert 'shib_session_id' not in session

    # raise BaseException
    with patch("weko_accounts.views.flash",side_effect=BaseException("test_error"))\
        and patch("weko_accounts.views._redirect_method",return_value=make_response()) as mock_redirect_:
        res = client.post(url,data={})
        mock_redirect_.assert_called_once()

    # all attributes have value and some shibboleth_user records don't have target eppn
    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED=True,
        WEKO_ACCOUNTS_SHIB_ALLOW_USERNAME_INST_EPPN=True
    )
    headers = {
        'HTTP_WEKOID': 'test_weko',
        'HTTP_WEKOSOCIETYAFFILIATION': 'test_aff'
    }
    form = {
        'eppn': 'test_eppn',
        'mail': 'testuser@example.org',
        'Shib-Session-ID': 'session',
        'HTTP_WEKOID': headers['HTTP_WEKOID'],
        'HTTP_WEKOSOCIETYAFFILIATION': headers['HTTP_WEKOSOCIETYAFFILIATION']
    }
    res = client.post(url, data=form, headers=headers)
    assert res.status_code == 200
    assert res.data.decode('utf-8') == '/weko/auto/login?next=%2F'
    with db.session.begin_nested():
        shib_users = ShibbolethUser.query.all()
        assert len(shib_users) == 0
    with client.session_transaction() as session:
        assert session.get("shib_session_id") == "session"
        session.clear()

    # all attributes have value and some shibboleth_user records have target eppn
    with db.session.begin_nested():
        weko_user = User.query.filter_by(email=users[0]['email']).first()
        insert_shib_user = ShibbolethUser().create(weko_user, shib_eppn='test_eppn')
        db.session.add(insert_shib_user)
    res = client.post(url, data=form, headers=headers)
    assert res.status_code == 200
    assert res.data.decode('utf-8') == '/weko/auto/login?Shib-Session-ID=session&next=%2F'
    result_shib_user = ShibbolethUser.query.filter_by(shib_eppn='test_eppn').first()
    assert result_shib_user.shib_mail == form['mail']
    assert result_shib_user.shib_user_name == headers['HTTP_WEKOID']
    assert result_shib_user.shib_role_authority_name == headers['HTTP_WEKOSOCIETYAFFILIATION']
    with db.session.begin_nested():
        db.session.delete(result_shib_user)
    with client.session_transaction() as session:
        assert 'shib_session_id' not in session

    # HTTP_WEKOID has no value
    headers = {
        'HTTP_WEKOID': '',
        'HTTP_WEKOSOCIETYAFFILIATION': 'test_aff'
    }
    form = {
        'eppn': 'test_eppn',
        'mail': 'testuser@example.org',
        'Shib-Session-ID': 'session',
        'HTTP_WEKOID': headers['HTTP_WEKOID'],
        'HTTP_WEKOSOCIETYAFFILIATION': headers['HTTP_WEKOSOCIETYAFFILIATION']
    }
    res = client.post(url, data=form, headers=headers)
    assert res.status_code == 200
    assert res.data.decode('utf-8') == '/weko/auto/login?next=%2F'
    with client.session_transaction() as session:
        assert session.get("shib_session_id") == "session"
        session.clear()

    # WEKO_ACCOUNTS_SHIB_ALLOW_USERNAME_INST_EPPN is False
    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_ALLOW_USERNAME_INST_EPPN=False
    )
    headers = {
        'HTTP_WEKOID': 'test_weko',
        'HTTP_WEKOSOCIETYAFFILIATION': 'test_aff'
    }
    form = {
        'eppn': 'test_eppn',
        'mail': 'testuser@example.org',
        'Shib-Session-ID': 'session',
        'HTTP_WEKOID': headers['HTTP_WEKOID'],
        'HTTP_WEKOSOCIETYAFFILIATION': headers['HTTP_WEKOSOCIETYAFFILIATION']
    }
    res = client.post(url, data=form, headers=headers)
    assert res.status_code == 200
    assert res.data.decode('utf-8') == '/weko/auto/login?next=%2F'
    with client.session_transaction() as session:
        assert session.get("shib_session_id") == "session"
        session.clear()

    # eppn has no value
    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_ALLOW_USERNAME_INST_EPPN=True
    )
    form = {
        'eppn': '',
        'mail': 'testuser@example.org',
        'Shib-Session-ID': 'session',
        'HTTP_WEKOID': headers['HTTP_WEKOID'],
        'HTTP_WEKOSOCIETYAFFILIATION': headers['HTTP_WEKOSOCIETYAFFILIATION']
    }
    res = client.post(url, data=form, headers=headers)
    assert res.status_code == 200
    assert res.data.decode('utf-8') == '/weko/auto/login?next=%2F'
    with client.session_transaction() as session:
        assert session.get("shib_session_id") == "session"
        session.clear()

    # HTTP_WEKOID and eppn have no value
    headers = {
        'HTTP_WEKOID': '',
        'HTTP_WEKOSOCIETYAFFILIATION': 'test_aff'
    }
    form = {
        'eppn': '',
        'mail': 'testuser@example.org',
        'Shib-Session-ID': 'session',
        'HTTP_WEKOID': headers['HTTP_WEKOID'],
        'HTTP_WEKOSOCIETYAFFILIATION': headers['HTTP_WEKOSOCIETYAFFILIATION']
    }
    res = client.post(url, data=form, headers=headers)
    assert res.status_code == 200
    assert res.data.decode('utf-8') == ''

    # WEKO_ACCOUNTS_SHIB_ALLOW_USERNAME_INST_EPPN is False and eppn has no value
    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_ALLOW_USERNAME_INST_EPPN=False
    )
    headers = {
        'HTTP_WEKOID': 'test_weko',
        'HTTP_WEKOSOCIETYAFFILIATION': 'test_aff'
    }
    form = {
        'eppn': '',
        'mail': 'testuser@example.org',
        'Shib-Session-ID': 'session',
        'HTTP_WEKOID': headers['HTTP_WEKOID'],
        'HTTP_WEKOSOCIETYAFFILIATION': headers['HTTP_WEKOSOCIETYAFFILIATION']
    }
    res = client.post(url, data=form, headers=headers)
    assert res.status_code == 200
    assert res.data.decode('utf-8') == ''

    # WEKO_ACCOUNTS_SHIB_ALLOW_USERNAME_INST_EPPN is False and eppn has no value
    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_ALLOW_USERNAME_INST_EPPN=False
    )
    res = client.post(url, data=form, headers=headers)
    assert res.status_code == 200
    assert res.data.decode('utf-8') == ''

    # WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED is False
    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED=False
    )
    form = {
        'eppn': 'test_eppn',
        'mail': 'testuser@example.org',
        'Shib-Session-ID': 'session',
        'HTTP_WEKOID': headers['HTTP_WEKOID'],
        'HTTP_WEKOSOCIETYAFFILIATION': headers['HTTP_WEKOSOCIETYAFFILIATION']
    }
    res = client.post(url, data=form, headers=headers)
    assert res.status_code == 200
    assert res.data.decode('utf-8') == '/weko/auto/login?next=%2F'
    with client.session_transaction() as session:
        assert session.get("shib_session_id") == "session"
        session.clear()

    # Shib-Session-ID has no value
    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED=True
    )
    form = {
        'eppn': 'test_eppn',
        'mail': 'testuser@example.com',
        'Shib-Session-ID': '',
        'HTTP_WEKOID': headers['HTTP_WEKOID'],
        'HTTP_WEKOSOCIETYAFFILIATION': headers['HTTP_WEKOSOCIETYAFFILIATION']
    }
    res = client.post(url, data=form, headers=headers)
    assert res.status_code == 200
    assert res.data.decode('utf-8') == '/weko/auto/login?next=%2F'
    with client.session_transaction() as session:
        assert session.get("shib_session_id") == ""
        session.clear()

    # WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED is False and Shib-Session-ID has no value
    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED=False
    )
    res = client.post(url, data=form, headers=headers)
    assert res.status_code == 302
    assert res.headers['Location'] == url_for("security.login", _external=True)


#def shib_stub_login():
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_shib_stub_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_shib_stub_login(client,mocker):
    url = url_for("weko_accounts.shib_stub_login")+"?next=/next_page"

    # WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED is false
    res = client.get(url)
    assert res.status_code == 403

    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED=True
    )
    # WEKO_ACCOUNTS_SHIB_IDP_LOGIN_ENABLED is true
    mock_redirect = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
    res = client.get(url)
    mock_redirect.assert_called_with("http://test_server.localdomain/secure/login.py?next=/next_page")

    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_IDP_LOGIN_ENABLED=False
    )
    # WEKO_ACCOUNTS_SHIB_IDP_LOGIN_ENABLED is true
    mock_render_template = mocker.patch("weko_accounts.views.render_template",return_value=make_response())
    res = client.get(url)
    mock_render_template.assert_called_with(
        'weko_accounts/login_shibuser_pattern_1.html',
        module_name="WEKO-Accounts",
        return_url='http://test_server.localdomain/secure/login.py',
        sp_entityID='https://localhost/shibboleth-sp',
        sp_handlerURL='https://localhost/Shibboleth.sso'
    )


#def shib_logout():
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_shib_logout -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_shib_logout(client, users, mocker):
    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        mocker.patch("weko_accounts.views.ShibUser.shib_user_logout")
        res = client.get(url_for("weko_accounts.shib_logout"))
        assert res.data == bytes("logout success","utf-8")


# def find_user_by_email(shib_attributes):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_find_user_by_email -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_find_user_by_email(app, users):

    with app.test_request_context():
        user = find_user_by_email({"shib_mail": users[0].get("email")})
        assert user.email == users[0].get("email")
        assert user.id == users[0].get("id")

        user = find_user_by_email({"shib_mail": "invalid.email@nii.ac.jp"})
        assert user is None


# def urlencode(value):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_urlencode -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_urlencode(app):
    app.jinja_env.filters["urlencode"] = urlencode
    # test urlencode
    template = app.jinja_env.from_string('{{"http://localhost:5000/weko/accounts/shib/login?SHIB_ATTR_SESSION_ID=1111&next=/next_page"|urlencode}}')
    actual = template.render()
    assert actual == "http%3A%2F%2Flocalhost%3A5000%2Fweko%2Faccounts%2Fshib%2Flogin%3FSHIB_ATTR_SESSION_ID%3D1111%26next%3D%2Fnext_page"
