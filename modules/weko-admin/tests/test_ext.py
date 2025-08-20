from mock import patch

from weko_admin.ext import WekoAdmin

# def role_has_access(endpoint=None)
#.tox/c1/bin/pytest --cov=weko_admin tests/test_ext.py::test_role_has_access -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_role_has_access(app,users):
    test = WekoAdmin()
    #W2023-22-2 TestNo.23
    with patch("weko_admin.admin.AdminSettings.get", return_value={"edit_mail_templates_enable": True}):
        with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
            assert test.role_has_access('mailtemplates') == True

        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            assert test.role_has_access('mailtemplates') == True

    #W2023-22-2 TestNo.24
    with patch("weko_admin.admin.AdminSettings.get", return_value={"edit_mail_templates_enable": False}):
        with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
            assert test.role_has_access('mailtemplates') == False

    #W2023-22-2 TestNo.25
    with patch("weko_admin.admin.AdminSettings.get", return_value={}):
        with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
            assert test.role_has_access('mailtemplates') == False

    with patch("weko_admin.admin.AdminSettings.get", return_value={"edit_mail_templates_enable": False}):
        assert test.role_has_access('mailtemplates') == False

    app.config.update({
        "WEKO_USERPROFILES_CUSTOMIZE_ENABLED": False
    })
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        assert test.role_has_access('profile_settings') == False

        app.config.update({
            "WEKO_USERPROFILES_CUSTOMIZE_ENABLED": True
        })
        assert test.role_has_access('profile_settings') == True

    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        assert test.role_has_access('restricted_access') == True
    
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert test.role_has_access('restricted_access') == False
    
    app.config.update(WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS = False)
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        assert test.role_has_access('restricted_access') == True
    
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert test.role_has_access('restricted_access') == False
