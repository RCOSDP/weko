import os
from os.path import dirname, join
from flask import url_for,current_app,make_response
from flask_admin import Admin
from mock import patch
import json
from io import BytesIO
import pytest
from datetime import datetime
from wtforms.validators import ValidationError
from werkzeug.datastructures import ImmutableMultiDict

from weko_admin.ext import WekoAdmin
from weko_admin.config import WEKO_ADMIN_USE_MAIL_TEMPLATE_EDIT

# def role_has_access(endpoint=None)
#.tox/c1/bin/pytest --cov=weko_admin tests/test_ext.py::test_role_has_access -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_role_has_access(app,users):
    test = WekoAdmin()
    #W2023-22-2 TestNo.23
    app.config.update(WEKO_ADMIN_USE_MAIL_TEMPLATE_EDIT = True)
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        assert test.role_has_access('mailtemplates') == True
    
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert test.role_has_access('mailtemplates') == False
    
    #W2023-22-2 TestNo.24
    app.config.update(WEKO_ADMIN_USE_MAIL_TEMPLATE_EDIT = False)
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        assert test.role_has_access('mailtemplates') == False

    #W2023-22-2 TestNo.25
    app.config.pop("WEKO_ADMIN_USE_MAIL_TEMPLATE_EDIT")
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):  
        assert test.role_has_access('mailtemplates') == True

    app.config.update(WEKO_ADMIN_USE_MAIL_TEMPLATE_EDIT = False)
    assert test.role_has_access('mailtemplates') == False
    

    


