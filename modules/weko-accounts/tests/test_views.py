
import pytest
import json
import redis
from invenio_accounts.models import Role
from flask import url_for,request,make_response,current_app,Flask
from flask_login.utils import login_user,logout_user
from flask_menu import current_menu
from mock import patch,MagicMock
from weko_accounts.api import ShibUser
from weko_accounts.views import (
    _has_admin_access,
    init_menu,
    _redirect_method,
    shib_sp_login,
    update_roles,
    handle_shib_bind_gakunin_map_groups
)
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
        mock_render.assert_called_with("http://TEST_SERVER.localdomain/secure/login.php")
        
        mock_render = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
        _redirect_method(True)
        mock_render.assert_called_with("http://TEST_SERVER.localdomain/secure/login.php?next="+url)
        
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
    client.get(url+"?SHIB_ATTR_SESSION_ID=2222")
    mock_redirect_.assert_called_once()
    
    

    redis_connect.put("Shib-Session-1111",bytes("","utf-8"))
    # not cache_val
    mock_redirect_ = mocker.patch("weko_accounts.views._redirect_method",return_value=make_response())
    client.get(url+"?SHIB_ATTR_SESSION_ID=1111")
    mock_redirect_.assert_called_once()
    assert redis_connect.redis.exists("Shib-Session-1111") == False
    
    mock_get_relation = mocker.patch("weko_accounts.views.ShibUser.get_relation_info")
    mock_new_relation = mocker.patch("weko_accounts.views.ShibUser.new_relation_info")
    mock_shib_login = mocker.patch("weko_accounts.views.ShibUser.shib_user_login")
    
    redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))
    # is_auto_bind is false, check_in is error
    mock_redirect_ = mocker.patch("weko_accounts.views._redirect_method",return_value=make_response())
    with patch("weko_accounts.views.ShibUser.check_in",return_value="test_error"):
        client.get(url+"?SHIB_ATTR_SESSION_ID=1111")
        mock_get_relation.assert_called_once()
        mock_redirect_.assert_called_once()
        assert redis_connect.redis.exists("Shib-Session-1111") == False
    
    redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))
    
    set_session(client,{"shib_session_id":"1111"})
    with patch("weko_accounts.views.ShibUser.check_in",return_value=None):
        # is_auto_bind is true,shib_user is None
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
        with patch("weko_accounts.views.ShibUser",return_value=shibuser):
            mock_redirect = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
            client.get(url)
            mock_redirect.assert_called_with("/next_page")
            mock_shib_login.assert_called_once()
            assert redis_connect.redis.exists("Shib-Session-1111") == False
    # raise BaseException
    with patch("weko_accounts.views.RedisConnection",side_effect=BaseException("test_error")):
        res = client.get(url+"?SHIB_ATTR_SESSION_ID=1111")
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
                mock_redirect = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
                client.post(url,data=form)
                mock_redirect.assert_called_with("/")
                assert redis_connect.redis.exists("Shib-Session-1111") is False
                
                # exist ShibUser.shib_user
                set_session(client,{"csrf_random":"test_csrf","shib_session_id":"1111","next":"/next_page"})
                redis_connect.put("Shib-Session-1111",bytes('{"shib_eppn":"test_eppn"}',"utf-8"))

                shibuser = ShibUser({})
                shibuser.shib_user = "test_user"
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

#def shib_login():
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_shib_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_shib_login(client,redis_connect,users,mocker):
    mocker.patch("weko_accounts.views.RedisConnection.connection",return_value=redis_connect)
    mocker.patch("weko_accounts.views.generate_random_str",return_value="asdfghjkl")
    url_base = url_for("weko_accounts.shib_login")
    
    # not shib_session_id
    mock_flash = mocker.patch("weko_accounts.views.flash")
    client.get(url_base)
    mock_flash.assert_called_with("Missing SHIB_ATTR_SESSION_ID!",category="error")
    
    url = url_base+"?SHIB_ATTR_SESSION_ID=2222"
    
    # not exist cache_key
    mock_flash = mocker.patch("weko_accounts.views.flash")
    client.get(url)
    mock_flash.assert_called_with("Missing SHIB_CACHE_PREFIX!",category="error")
    
    url = url_base+"?SHIB_ATTR_SESSION_ID=1111"
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
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_update_roles -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

def test_update_roles(app, db,mocker):
    with app.app_context():
        # テストデータの準備
        map_group_list = ['group1', 'group2']
        existing_roles = {'group1', 'group3'}

        # 既存のロールを追加
        for role_name in existing_roles:
            role = Role(name=role_name, description="description")
            db.session.add(role)
        db.session.commit()

        # update_rolesの呼び出し
        update_roles(map_group_list, existing_roles)

        # 結果の検証
        roles = Role.query.all()
        role_names = [role.name for role in roles]
        assert 'group1' in role_names
        assert 'group2' in role_names
        assert 'group3' not in role_names

#.tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_handle_shib_bind_gakunin_map_group_test2 -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
#mock_request_form.getを直接モックするパターン
def test_handle_shib_bind_gakunin_map_group_test2(app, client, mocker):
    with app.app_context():
        # モックの設定
        app.config['WEKO_ACCOUNTS_IDP_ENTITY_ID'] = 'test_entity_id'

        mock_redis_connection = mocker.patch('weko_accounts.views.RedisConnection')
        mock_datastore = MagicMock()
        mock_redis_connection.return_value.connection.return_value = mock_datastore

        # map_groups が存在する場合のテスト
        mock_datastore.get = MagicMock(return_value=json.dumps(['group1', 'group2']))

        mock_role_query = mocker.patch('weko_accounts.views.Role.query')
        mock_role_query.all = MagicMock(return_value=[
            Role(name='group1', description=''),
            Role(name='group3', description='')
        ])

        mock_update_roles = mocker.patch('weko_accounts.views.update_roles')

        # フォームデータを送信
        with client.post("/", data={'WEKO_ACCOUNTS_IDP_ENTITY_ID': 'test_entity_id'}):
            # 関数の呼び出し
            response = handle_shib_bind_gakunin_map_groups()

            # 結果の検証
            assert request.form.get('WEKO_ACCOUNTS_IDP_ENTITY_ID') == 'test_entity_id'
            mock_redis_connection.return_value.connection.assert_called_with(db=app.config['CACHE_REDIS_DB'], kv=True)
            mock_datastore.get.assert_called_with('shib:test_entity_id')
            mock_role_query.all.assert_called_once()
            mock_update_roles.assert_called_with(['group1', 'group2'], {'group1', 'group3'})

            assert response is None

            mock_role_query.all.reset_mock()
            mock_update_roles.reset_mock()

            # map_groups が存在しない場合のテスト
            mock_datastore.get.return_value = None

            # 関数の呼び出し
            response = handle_shib_bind_gakunin_map_groups()

            # 結果の検証
            assert request.form.get('WEKO_ACCOUNTS_IDP_ENTITY_ID') == 'test_entity_id'
            mock_redis_connection.return_value.connection.assert_called_with(db=app.config['CACHE_REDIS_DB'], kv=True)
            mock_datastore.get.assert_called_with('shib:test_entity_id')
            mock_role_query.all.assert_not_called()
            mock_update_roles.assert_not_called()

            assert response is None

            mock_role_query.all.reset_mock()
            mock_update_roles.reset_mock()

            # map_group_list と existing_roles が一致する場合のテスト
            mock_datastore.get.return_value = json.dumps(['group1', 'group2'])
            mock_role_query.all.return_value = [
                Role(name='group1', description=''),
                Role(name='group2', description='')
            ]

            # 関数の呼び出し
            response = handle_shib_bind_gakunin_map_groups()

            # 結果の検証
            assert request.form.get('WEKO_ACCOUNTS_IDP_ENTITY_ID') == 'test_entity_id'
            mock_redis_connection.return_value.connection.assert_called_with(db=app.config['CACHE_REDIS_DB'], kv=True)
            mock_datastore.get.assert_called_with('shib:test_entity_id')
            mock_role_query.all.assert_called_once()
            mock_update_roles.assert_not_called()

            assert response is None
            mock_role_query.all.reset_mock()
            mock_update_roles.reset_mock()

            # map_group_list と existing_roles が一致しない場合のテスト
            mock_datastore.get.return_value = json.dumps(['group1', 'group3'])
            mock_role_query.all.return_value = [
                Role(name='group1', description=''),
                Role(name='group2', description='')
            ]

            # 関数の呼び出し
            response = handle_shib_bind_gakunin_map_groups()

            # 結果の検証
            assert request.form.get('WEKO_ACCOUNTS_IDP_ENTITY_ID') == 'test_entity_id'
            mock_redis_connection.return_value.connection.assert_called_with(db=app.config['CACHE_REDIS_DB'], kv=True)
            mock_datastore.get.assert_called_with('shib:test_entity_id')
            mock_role_query.all.assert_called_once()
            mock_update_roles.assert_called_with(['group1', 'group3'], {'group1', 'group2'})

            assert response is None

#.tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_handle_shib_bind_gakunin_map_groups_errors -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_handle_shib_bind_gakunin_map_groups_errors(app, client, mocker):
    with app.app_context():
        # モックの設定
        mock_redis_connection = mocker.patch('weko_accounts.views.RedisConnection')
        mock_datastore = MagicMock()
        mock_redis_connection.return_value.connection.return_value = mock_datastore

        mock_logger = mocker.patch('flask.current_app.logger.error')

        # redis.ConnectionErrorのテスト
        mock_datastore.get.side_effect = redis.ConnectionError('test_redis_error')
        with client.post("/", data={'WEKO_ACCOUNTS_IDP_ENTITY_ID': 'test_entity_id'}):
            response = handle_shib_bind_gakunin_map_groups()

        mock_logger.assert_called_with("Redis connection error: test_redis_error")
        assert response == ('test_redis_error', 500)

        # その他の例外のテスト
        mock_datastore.get.side_effect = Exception('test_exception')
        with client.post("/", data={'WEKO_ACCOUNTS_IDP_ENTITY_ID': 'test_entity_id'}):
            response = handle_shib_bind_gakunin_map_groups()

        mock_logger.assert_called_with("Unexpected error: test_exception")
        assert response == ('test_exception', 500)

        # KeyErrorのテスト
        mock_datastore.get.side_effect = KeyError('test_key_error')
        with client.post("/", data={'WEKO_ACCOUNTS_IDP_ENTITY_ID': 'test_entity_id'}):
            response = handle_shib_bind_gakunin_map_groups()

        mock_logger.assert_called_with("Missing key in request headers: 'test_key_error'")
        assert response == ("'test_key_error'", 400)

#def shib_sp_login():
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_shib_sp_login -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_shib_sp_login(client, redis_connect,mocker):
    mocker.patch("weko_accounts.views.RedisConnection.connection",return_value=redis_connect)
    url = url_for("weko_accounts.shib_sp_login")

    # not shib_session_id
    mock_flash = mocker.patch("weko_accounts.views.flash")
    mock_redirect = mocker.patch("weko_accounts.views.redirect",return_value=make_response())
    client.post(url,data={})
    mock_flash.assert_called_with("Missing SHIB_ATTR_SESSION_ID!",category="error")
    mock_redirect.assert_called_with(url_for("security.login"))
    
    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED=True
    )
    form = {
        "SHIB_ATTR_SESSION_ID":"1111"
    }
    
    # parse_attribute is error
    with patch("weko_accounts.views.parse_attributes",return_value=("attr",True)):
        mock_flash = mocker.patch("weko_accounts.views.flash")
        client.post(url,data=form)
        mock_flash.assert_called_with("Missing SHIB_ATTRs!",category="error")
        
    form = {
        "SHIB_ATTR_SESSION_ID":"1111",
        "SHIB_ATTR_EPPN":"test_eppn"
    }

    # WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPSがTrueの場合のテスト
    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS=True
    )
    mock_handle_shib_bind_gakunin_map_groups = mocker.patch("weko_accounts.views.handle_shib_bind_gakunin_map_groups", return_value=None)
    client.post(url, data=form)
    mock_handle_shib_bind_gakunin_map_groups.assert_called_once()

    # handle_shib_bind_gakunin_map_groupsがエラーレスポンスを返す場合のテスト
    mock_handle_shib_bind_gakunin_map_groups = mocker.patch("weko_accounts.views.handle_shib_bind_gakunin_map_groups", return_value=("error", 400))
    res = client.post(url, data=form)
    assert res.status_code == 400
    assert res.data == b"error"

    # WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPSがFalseの場合のテスト
    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS=False
    )

    # shib_user.get_relation_info is None
    with patch("weko_accounts.views.ShibUser.get_relation_info",return_value=None):
        res = client.post(url,data=form)
        assert res.status_code == 200
        #assert res.url == "/weko/shib/login?SHIB_ATTR_SESSION_ID=1111&_method=GET"
    # shib_user.get_relation_info is not None
    with patch("weko_accounts.views.ShibUser.get_relation_info",return_value="chib_user"):
        res = client.post(url,data=form)
        assert res.status_code == 200
        #assert res == "/weko/auto/login?SHIB_ATTR_SESSION_ID=1111&_method=GET"
    
    # raise BaseException
    with patch("weko_accounts.views.flash",side_effect=BaseException("test_error")):
        mock_redirect_ = mocker.patch("weko_accounts.views._redirect_method",return_value=make_response())
        res = client.post(url,data={})
        mock_redirect_.assert_called_once()
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
    mock_redirect.assert_called_with("http://test_server.localdomain/secure/login.php")
    
    current_app.config.update(
        WEKO_ACCOUNTS_SHIB_IDP_LOGIN_ENABLED=False
    )
    # WEKO_ACCOUNTS_SHIB_IDP_LOGIN_ENABLED is true
    mock_render_template = mocker.patch("weko_accounts.views.render_template",return_value=make_response())
    res = client.get(url)
    mock_render_template.assert_called_with('weko_accounts/login_shibuser_pattern_1.html',module_name="WEKO-Accounts")
    
#def shib_logout():
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_views.py::test_shib_logout -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_shib_logout(client, mocker):
    mocker.patch("weko_accounts.views.ShibUser.shib_user_logout")
    res = client.get(url_for("weko_accounts.shib_logout"))
    assert res.data == bytes("logout success","utf-8")