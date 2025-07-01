import pytest
import json
from mock import patch, call
from flask import current_app,url_for,make_response
from invenio_accounts.testutils import login_user_via_session as login
from weko_admin.models import AdminSettings
from invenio_accounts.models import User
from sqlalchemy.orm.session import object_session


class TestShibSettingView:

    def test_index_acl_guest(self,client,session_time):
        url = url_for("shibboleth.index",_external=True)
        res = client.get(url)
        assert res.status_code == 302
    @pytest.mark.parametrize('user_index, is_can',[
        (0,True),
        (1,True),
        (2,False),
        (3,False),
        (4,False),
        (5,False),
        (6,False),
    ])
    def test_index_acl(self,client,users,user_index,is_can,mocker, admin_settings):
        mocker.patch("weko_accounts.admin.ShibSettingView.render",return_value=make_response())
        login(client=client,email=users[user_index]["email"])
        url = url_for("shibboleth.index",_external=True)
        res = client.get(url)
        if is_can:
            assert res.status_code != 403
        else:
            assert res.status_code == 403
    # .tox/c1/bin/pytest --cov=weko_accounts tests/test_admin.py::TestShibSettingView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_index(self,app,client,users,mocker, admin_settings, db):
        with app.app_context():
            user = User.query.filter_by(email=users[0]['email']).first()
            login(client=client, user=user)
            url = url_for("shibboleth.index")
            sibuser_html = 'weko_accounts/setting/shibuser.html'
            mock_flash = mocker.patch("weko_accounts.admin.flash")
            mock_render = mocker.patch("weko_accounts.admin.ShibSettingView.render",return_value=make_response())
            current_app.config["WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED"] = True

            # モックに渡す変数を設定
            role_list = current_app.config['WEKO_ACCOUNTS_ROLE_LIST']
            attr_list = current_app.config['WEKO_ACCOUNTS_ATTRIBUTE_LIST']
            block_user_list = admin_settings[0].settings['blocked_ePPNs']
            role_order = ["gakunin_role", "orthros_outside_role", "extra_role"]
            roles = {key: admin_settings[2].settings[key] for key in role_order}
            set_language = "en"
            shib_flg = "1"
            attr_order = ["shib_eppn", "shib_role_authority_name", "shib_mail", "shib_user_name"]
            attributes = {key: admin_settings[3].settings[key] for key in attr_order}

            data = {
                "submit": "shib_form",
                "shibbolethRadios": "1",
                "block-eppn-option-list": json.dumps(block_user_list),
                "enable-login-user-list": [],
            }

            for i, (_, value) in enumerate(roles.items()):
                data[f"role-lists{i}"] = value

            for i, (_, value) in enumerate(attributes.items()):
                data[f"attr-lists{i}"] = value

            # new_shib_flg = 1
            res = client.post(url, data=data)

            assert admin_settings[1].settings["shib_flg"] is True
            assert res.status_code==200
            mock_render.assert_called_with(
                sibuser_html,
                shib_flg=shib_flg,
                set_language=set_language,
                role_list=role_list,
                attr_list=attr_list,
                block_user_list=block_user_list,
                enable_login_user_list=[],
                **roles,
                **attributes
            )
            mock_flash.assert_called_with('Updated Shibboleth settings', category='success')
            mock_flash.reset_mock()

            current_app.config["WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED"] = False

            data["shibbolethRadios"] = "0"

            # new_shib_flg = 0
            res = client.post(url, data=data)

            assert res.status_code == 200
            assert admin_settings[1].settings["shib_flg"] is False
            shib_flg = "0"
            mock_render.assert_called_with(
                sibuser_html,
                shib_flg=shib_flg,
                set_language=set_language,
                role_list=role_list,
                attr_list=attr_list,
                block_user_list=block_user_list,
                enable_login_user_list=[],
                **roles,
                **attributes
            )
            mock_flash.assert_called_with('Updated Shibboleth settings', category='success')
            mock_flash.reset_mock()

            # デフォルトロールを変更
            mock_render = mocker.patch("weko_accounts.admin.ShibSettingView.render",return_value=make_response())
            roles = {
                "gakunin_role": "Repository Administrator",
                "orthros_outside_role": "None",
                "extra_role": "Contributor"}

            for i, (_, value) in enumerate(roles.items()):
                data[f"role-lists{i}"] = value

            res = client.post(url, data=data)

            assert res.status_code == 200
            assert admin_settings[2].settings["gakunin_role"] == "Repository Administrator"
            assert admin_settings[2].settings["orthros_outside_role"] == "None"
            assert admin_settings[2].settings["extra_role"] == "Contributor"
            mock_render.assert_called_with(
                sibuser_html,
                shib_flg=shib_flg,
                set_language=set_language,
                role_list=role_list,
                attr_list=attr_list,
                block_user_list=block_user_list,
                enable_login_user_list=[],
                **roles,
                **attributes
            )
            mock_flash.assert_has_calls([
                call('Gakunin Role was updated.', category='success'),
                call('Orthros Role was updated.', category='success'),
                call('Extra Role was updated.', category='success')
            ])
            mock_flash.reset_mock()

            # 属性を変更
            mock_render = mocker.patch("weko_accounts.admin.ShibSettingView.render",return_value=make_response())
            attributes = {
                "shib_eppn": "eduPersonAffiliation",
                "shib_role_authority_name": "eppn",
                "shib_mail": "DisplayName",
                "shib_user_name": "sn"}

            for i, (_, value) in enumerate(attributes.items()):
                data[f"attr-lists{i}"] = value

            res = client.post(url, data=data)

            assert res.status_code == 200
            assert admin_settings[3].settings["shib_eppn"] == "eduPersonAffiliation"
            assert admin_settings[3].settings["shib_role_authority_name"] == "eppn"
            assert admin_settings[3].settings["shib_mail"] == "DisplayName"
            assert admin_settings[3].settings["shib_user_name"] == "sn"
            mock_render.assert_called_with(
                sibuser_html,
                shib_flg=shib_flg,
                set_language=set_language,
                role_list=role_list,
                attr_list=attr_list,
                block_user_list=block_user_list,
                enable_login_user_list=[],
                **roles,
                **attributes
            )
            mock_flash.assert_has_calls([
                call('Shibboleth Eppn mapping was updated.', category='success'),
                call('Shibboleth Role Authority Name mapping was updated.', category='success'),
                call('Shibboleth Mail mapping was updated.', category='success'),
                call('Shibboleth User Name mapping was updated.', category='success')
            ])
            mock_flash.reset_mock()


            # ブロックユーザーを変更
            mock_render = mocker.patch("weko_accounts.admin.ShibSettingView.render",return_value=make_response())
            block_user_list = ['test1','test2','test3']
            data["block-eppn-option-list"] = json.dumps(block_user_list)

            res = client.post(url, data=data)

            assert res.status_code == 200
            assert "test1" in admin_settings[0].settings["blocked_ePPNs"]

            mock_render.assert_called_with(
                sibuser_html,
                shib_flg=shib_flg,
                set_language=set_language,
                role_list=role_list,
                attr_list=attr_list,
                block_user_list=str(block_user_list),
                enable_login_user_list=[],
                **roles,
                **attributes
            )
            mock_flash.assert_called_with('Updated User Login Block settings', category='success')
            mock_flash.reset_mock()

            # No changes
            mock_render = mocker.patch("weko_accounts.admin.ShibSettingView.render",return_value=make_response())
            res = client.post(url, data=data)

            assert res.status_code == 200
            mock_render.assert_called_with(
                sibuser_html,
                shib_flg=shib_flg,
                set_language=set_language,
                role_list=role_list,
                attr_list=attr_list,
                block_user_list=block_user_list,
                enable_login_user_list=[],
                **roles,
                **attributes
            )
            mock_flash.assert_called_with('Shibboleth Settings have been saved.', category='success')
            mock_flash.reset_mock()

            # raise BaseException
            with patch("weko_accounts.admin.ShibSettingView.render",side_effect=BaseException):
                res = client.post(url)
                assert res.status_code == 400
                mock_flash.assert_not_called()

            # method is GET
            mock_render = mocker.patch("weko_accounts.admin.ShibSettingView.render",return_value=make_response())
            res = client.get(url)
            assert res.status_code == 200
            mock_render.assert_called_with(
                sibuser_html,
                shib_flg=shib_flg,
                set_language=set_language,
                role_list=role_list,
                attr_list=attr_list,
                block_user_list=block_user_list,
                enable_login_user_list=[],
                **roles,
                **attributes
            )
            mock_flash.assert_not_called()

    @pytest.fixture
    def admin_settings(self, db):
        settings = list()
        settings.append(AdminSettings(id=6,name="blocked_user_settings",settings={"blocked_ePPNs": []}))
        settings.append(AdminSettings(id=7,name="shib_login_enable",settings={"shib_flg": False}))
        settings.append(AdminSettings(id=8,name="default_role_settings",settings={
                        "gakunin_role": "Contributor",
                        "orthros_outside_role": "Community Administrator",
                        "extra_role": "None"}))
        settings.append(AdminSettings(id=9,name="attribute_mapping",settings={
                        "shib_eppn": "eppn",
                        "shib_role_authority_name": "eduPersonAffiliation",
                        "shib_mail": "mail",
                        "shib_user_name": "DisplayName"}))
        db.session.add_all(settings)
        db.session.commit()
        return settings
