import pytest
from mock import patch
from flask import current_app,url_for,make_response
from invenio_accounts.testutils import login_user_via_session as login

class TestShibSettingView:
    
    def test_index_acl_guest(self,client,session_time):
        url = url_for("shibboleth.index",_external=True)
        res = client.get(url)
        assert res.status_code == 302
    @pytest.mark.parametrize('user_index, is_can',[
        (0,True),
        (1,False),
        (2,False),
        (3,False),
        (4,False),
        (5,False),
        (6,False),
    ])
    def test_index_acl(self,client,users,user_index,is_can,mocker):
        mocker.patch("weko_accounts.admin.ShibSettingView.render",return_value=make_response())
        login(client=client,email=users[user_index]["email"])
        url = url_for("shibboleth.index",_external=True)
        res = client.get(url)
        if is_can:
            assert res.status_code != 403
        else:
            assert res.status_code == 403
    # .tox/c1/bin/pytest --cov=weko_accounts tests/test_admin.py::TestShibSettingView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_index(self,client,users,mocker):
        login(client=client,email=users[0]["email"])
        url = url_for("shibboleth.index")
        sibuser_html = 'weko_accounts/setting/shibuser.html'
        mock_render = mocker.patch("weko_accounts.admin.ShibSettingView.render",return_value=make_response())
        current_app.config.update(
            WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED=True
        )
        # shib_flg = 1
        res = client.post(url,data=dict(
            submit="shib_form",
            shibbolethRadios="1"
        ))
        assert current_app.config["WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED"] == True
        assert res.status_code==200
        mock_render.assert_called_with(sibuser_html,shib_flg="1")
        
        mock_render = mocker.patch("weko_accounts.admin.ShibSettingView.render",return_value=make_response())
        current_app.config.update(
            WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED=False
        )
        # shib_flg = 0
        res = client.post(url,data=dict(
            submit="shib_form",
            shibbolethRadios="0"
        ))
        assert res.status_code == 200
        assert current_app.config["WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED"] == False
        mock_render.assert_called_with(sibuser_html,shib_flg="0")
        
        # raise BaseException
        with patch("weko_accounts.admin.ShibSettingView.render",side_effect=BaseException):
            res = client.post(url)
            assert res.status_code == 400
        
        # method is GET
        mock_render = mocker.patch("weko_accounts.admin.ShibSettingView.render",return_value=make_response())
        res = client.get(url)
        assert res.status_code == 200
        mock_render.assert_called_with(sibuser_html,shib_flg="0")