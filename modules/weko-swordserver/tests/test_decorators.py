

import pytest
from werkzeug.datastructures import FileStorage
from flask_login.utils import login_user

from invenio_deposit.scopes import write_scope
from invenio_oauth2server.ext import verify_oauth_token_and_set_current_user

from weko_swordserver.errors import ErrorType, WekoSwordserverException
from weko_swordserver.decorators import check_oauth, check_on_behalf_of,check_package_contents


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_decorators.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp

# def check_oauth(*scopes):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_decorators.py::test_check_oauth -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_check_oauth(app,client,users,tokens):
    headers = {}
    with app.test_request_context(headers=headers):
        res = check_oauth()(lambda x,y:x+y)(x=1,y=2)
        assert res == 3
        
    headers = {
        "Authorization":"Bearer {}".format(tokens["token"].access_token),
    }
    with app.test_request_context(headers=headers):
        login_user(users[0]["obj"])
        verify_oauth_token_and_set_current_user()
        res = check_oauth(write_scope.id)(lambda x,y:x+y)(x=1,y=2)
        assert res == 3

    headers = {
        "Authorization":"Bearer {}".format(tokens["token"].access_token),
    }
    with app.test_request_context(headers=headers):
        with pytest.raises(WekoSwordserverException) as e:
            res = check_oauth(write_scope.id)(lambda x,y:x+y)(x=1,y=2)
            assert e.errorType == ErrorType.AuthenticationFailed
            assert e.message == "Authentication is failed."


# def check_on_behalf_of():
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_decorators.py::test_check_on_behalf_of -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_check_on_behalf_of(app):
    with app.test_request_context():
        res = check_on_behalf_of()(lambda x,y: x+y)(x=1,y=2)
        assert res == 3
    with app.test_request_context(headers={"On-Behalf-Of":"test"}):
        with pytest.raises(WekoSwordserverException) as e:
            res = check_on_behalf_of()(lambda x,y: x+y)(x=1,y=2)
            assert e.errorType == ErrorType.OnBehalfOfNotAllowed
            assert e.message == "Not support On-Behalf-Of."


# def check_package_contents():
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_decorators.py::test_check_package_contents -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_check_package_contents(app,make_zip):
    with app.test_request_context():
        with pytest.raises(WekoSwordserverException) as e:
            res = check_package_contents()(lambda x,y:x+y)(x=1,y=2)
            assert e.errorType == ErrorType.ContentMalformed
            assert e.message == "No file part."
    zip = make_zip()
    storage=FileStorage(filename="",stream=zip)
    with app.test_request_context(data=dict(file=storage)):
        with pytest.raises(WekoSwordserverException) as e:
            res = check_package_contents()(lambda x,y:x+y)(x=1,y=2)
            assert e.errorType == ErrorType.ContentMalformed
            assert e.message == "No selected file."
