import pytest
from flask import request,current_app,session,make_response
from flask_login.utils import login_user
import hashlib
from weko_accounts.utils import (
    get_remote_addr,
    generate_random_str,
    parse_attributes,
    login_required_customize,
    roles_required
)


#def get_remote_addr():
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_utils.py::test_get_remote_addr -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_remote_addr(app):
    result = get_remote_addr()
    assert result == None
    with app.test_request_context(
        headers={
            "X-Real-IP":'192.168.0.1',
            
        },environ_base={'REMOTE_ADDR': '10.0.0.1'}
    ):
        result = get_remote_addr()
        assert result == '192.168.0.1'

    with app.test_request_context(headers={
        "X-Forwarded-For":"192.168.254.1, 192.168.255.1"},environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == "192.168.254.1"
    
    with app.test_request_context(headers={
         "X-Real-IP":'192.168.0.1',"X-Forwarded-For":"192.168.254.1, 192.168.255.1"},environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == '192.168.0.1'
    
    with app.test_request_context(headers={
    },environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == '10.0.0.1'
    
    with app.test_request_context(headers={
    },environ_base={}):
        result = get_remote_addr()
        assert result == None

    # WEKO_ACCOUNTS_REAL_IP = None
    app.config["WEKO_ACCOUNTS_REAL_IP"] = None
    result = get_remote_addr()
    assert result == None
    with app.test_request_context(
        headers={
            "X-Real-IP":'192.168.0.1',
            
        },environ_base={'REMOTE_ADDR': '10.0.0.1'}
    ):
        result = get_remote_addr()
        assert result == '192.168.0.1'

    with app.test_request_context(headers={
        "X-Forwarded-For":"192.168.254.1, 192.168.255.1"},environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == "192.168.254.1"
    
    with app.test_request_context(headers={
         "X-Real-IP":'192.168.0.1',"X-Forwarded-For":"192.168.254.1, 192.168.255.1"},environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == '192.168.0.1'
    
    with app.test_request_context(headers={
    },environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == '10.0.0.1'
    
    with app.test_request_context(headers={
    },environ_base={}):
        result = get_remote_addr()
        assert result == None

    app.config["WEKO_ACCOUNTS_REAL_IP"] = "remote_add"
    result = get_remote_addr()
    assert result == None
    with app.test_request_context(
        headers={
            "X-Real-IP":'192.168.0.1',
            
        },environ_base={'REMOTE_ADDR': '10.0.0.1'}
    ):
        result = get_remote_addr()
        assert result == '10.0.0.1'

    with app.test_request_context(headers={
        "X-Forwarded-For":"192.168.254.1, 192.168.255.1"},environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == '10.0.0.1'
    
    with app.test_request_context(headers={
         "X-Real-IP":'192.168.0.1',"X-Forwarded-For":"192.168.254.1, 192.168.255.1"},environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == '10.0.0.1'
    
    with app.test_request_context(headers={
    },environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == '10.0.0.1'
    
    with app.test_request_context(headers={
    },environ_base={}):
        result = get_remote_addr()
        assert result == None
    
    app.config["WEKO_ACCOUNTS_REAL_IP"] = "x_real_ip"
    result = get_remote_addr()
    assert result == None
    with app.test_request_context(
        headers={
            "X-Real-IP":'192.168.0.1',
            
        },environ_base={'REMOTE_ADDR': '10.0.0.1'}
    ):
        result = get_remote_addr()
        assert result == '192.168.0.1'

    with app.test_request_context(headers={
        "X-Forwarded-For":"192.168.254.1, 192.168.255.1"},environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == '10.0.0.1'
    
    with app.test_request_context(headers={
         "X-Real-IP":'192.168.0.1',"X-Forwarded-For":"192.168.254.1, 192.168.255.1"},environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == '192.168.0.1'
    
    with app.test_request_context(headers={
    },environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == '10.0.0.1'
    
    with app.test_request_context(headers={
    },environ_base={}):
        result = get_remote_addr()
        assert result == None
    
    app.config["WEKO_ACCOUNTS_REAL_IP"] = "x_forwarded_for"
    result = get_remote_addr()
    assert result == None
    with app.test_request_context(
        headers={
            "X-Real-IP":'192.168.0.1',
            
        },environ_base={'REMOTE_ADDR': '10.0.0.1'}
    ):
        result = get_remote_addr()
        assert result == '10.0.0.1'

    with app.test_request_context(headers={
        "X-Forwarded-For":"192.168.254.1, 192.168.255.1"},environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == "192.168.254.1"
    
    with app.test_request_context(headers={
         "X-Real-IP":'192.168.0.1',"X-Forwarded-For":"192.168.254.1, 192.168.255.1"},environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == '192.168.254.1'
    
    with app.test_request_context(headers={
    },environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == '10.0.0.1'
    
    with app.test_request_context(headers={
    },environ_base={}):
        result = get_remote_addr()
        assert result == None
    
    app.config["WEKO_ACCOUNTS_REAL_IP"] = "x_forwarded_for_rev"
    result = get_remote_addr()
    assert result == None
    with app.test_request_context(
        headers={
            "X-Real-IP":'192.168.0.1',
            
        },environ_base={'REMOTE_ADDR': '10.0.0.1'}
    ):
        result = get_remote_addr()
        assert result == '10.0.0.1'

    with app.test_request_context(headers={
        "X-Forwarded-For":"192.168.254.1, 192.168.255.1"},environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == "192.168.255.1"
    
    with app.test_request_context(headers={
         "X-Real-IP":'192.168.0.1',"X-Forwarded-For":"192.168.254.1, 192.168.255.1"},environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == '192.168.255.1'
    
    with app.test_request_context(headers={
    },environ_base={'REMOTE_ADDR': '10.0.0.1'}):
        result = get_remote_addr()
        assert result == '10.0.0.1'
    
    with app.test_request_context(headers={
    },environ_base={}):
        result = get_remote_addr()
        assert result == None

#def generate_random_str(length=128):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_utils.py::test_generate_random_str -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_generate_random_str(mocker):
    import string
    random_list = string.ascii_letters+string.digits
    import random
    rng = random.SystemRandom()
    mocker.patch("weko_accounts.utils.random.SystemRandom",return_value=rng)

    mock_choice = mocker.spy(rng,"choice")
    result = generate_random_str(10)
    mock_choice.assert_has_calls([mocker.call(random_list) for _ in range(10)])

#def parse_attributes():
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_utils.py::test_parse_attributes -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_parse_attributes(app):
    current_app.config.update(
        WEKO_ACCOUNTS_SSO_ATTRIBUTE_MAP= {
            "SHIB_ATTR_EPPN":(True, 'shib_eppn'),
            'SHIB_ATTR_MAIL': (False, 'shib_mail'),
            'SHIB_ATTR_USER_NAME': (False, 'shib_user_name'),
        }
    )
    with app.test_request_context(
        method="POST",data={"SHIB_ATTR_EPPN":"test_eppn","SHIB_ATTR_MAIL":"test@test.org"}
    ):
        attrs, error = parse_attributes()
        assert attrs == {"shib_eppn":"test_eppn",'shib_mail':"test@test.org",'shib_user_name':"G_test_eppn"}
        assert error == False
    with app.test_request_context(
        method="POST",data={}
    ):
        attrs ,error = parse_attributes()
        assert attrs == {"shib_eppn":"",'shib_mail':"",'shib_user_name':""}
        assert error == True
    with app.test_request_context(
        "/?SHIB_ATTR_EPPN=test_eppn&SHIB_ATTR_MAIL=test@test.org",method="GET"
    ):
        attrs ,error = parse_attributes()
        assert attrs == {"shib_eppn":"test_eppn",'shib_mail':"test@test.org",'shib_user_name':"G_test_eppn"}
        assert error == False
    # eppn what length is 254
    test_eppn = 'test_eppn1234567890test_eppn1234567890test_eppn1234567890test_eppn1234567890test_eppn1234567890test_eppn1234567890test_eppn1234567890' + \
        'test_eppn1234567890test_eppn1234567890test_eppn1234567890test_eppn1234567890test_eppn1234567890test_eppn1234567890test_ep'
    with app.test_request_context(
        method="POST", data={"SHIB_ATTR_EPPN": test_eppn, "SHIB_ATTR_MAIL": "test@test.org"}
    ):
        attrs, error = parse_attributes()
        hash_eppn = hashlib.sha256(test_eppn.encode()).hexdigest()
        assert attrs == {"shib_eppn": test_eppn, "shib_mail": "test@test.org", "shib_user_name": "G_" + hash_eppn}
        assert error == False

#def login_required_customize(func):
#    def decorated_view(*args, **kwargs):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_utils.py::test_login_required_customize -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_login_required_customize(app,users,mocker):
    # method is EXEMPT_METHODS
    with app.test_request_context(method="OPTIONS"):
        result = login_required_customize(lambda x,y:x+y)(x=1,y=2) 
        assert result == 3
    # is_authenticated is True
    with app.test_request_context(method="GET"):
        login_user(users[0]["obj"])
        result = login_required_customize(lambda x,y:x+y)(x=1,y=2) 
        assert result == 3
    # is_authenticated is False,not exist guest_token
    with app.test_request_context(method="GET"):
        result = login_required_customize(lambda x,y:x+y)(x=1,y=2)
        assert result.status_code == 302
    # is_authenticated is False, exist guest_token
    with app.test_request_context(method="GET"):
        session["guest_token"] = "test_token"
        result = login_required_customize(lambda x,y:x+y)(x=1,y=2)
        assert result == 3
    # _login_disabled is True
    mocker.patch("weko_accounts.utils.current_app.login_manager._login_disabled",return_value=True)
    with app.test_request_context(method="GET"):
        result = login_required_customize(lambda x,y:x+y)(x=1,y=2)
        assert result == 3
#def roles_required(roles):
#    def decorator(func):
#        def decorated_view(*args, **kwargs):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_utils.py::test_roles_required -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_roles_required(app,users,mocker):
    roles = ["System Administrator"]
    # method is EXEMPT_METHODS
    with app.test_request_context(method="OPTIONS"):
        result = roles_required(roles)(lambda x,y:x+y)(x=1,y=2) 
        assert result == 3
    # is_authenticated is True,user.role in roles
    with app.test_request_context(method="GET"):
        login_user(users[0]["obj"])
        result = roles_required(roles)(lambda x,y:x+y)(x=1,y=2) 
        assert result == 3
    # is_authenticated is True,user.role not in roles
    with app.test_request_context(method="GET"):
        login_user(users[1]["obj"])
        mock_abort = mocker.patch("weko_accounts.utils.abort",return_value=make_response())
        result = roles_required(roles)(lambda x,y:x+y)(x=1,y=2) 
        mock_abort.assert_called_with(403)
    # is_authenticated is False,not exist guest_token
    with app.test_request_context(method="GET"):
        mock_abort = mocker.patch("weko_accounts.utils.abort",return_value=make_response())
        result = roles_required(roles)(lambda x,y:x+y)(x=1,y=2)
        mock_abort.assert_called_with(401)
    # is_authenticated is False, exist guest_token
    with app.test_request_context(method="GET"):
        session["guest_token"] = "test_token"
        result = roles_required(roles)(lambda x,y:x+y)(x=1,y=2)
        assert result == 3
    
    # _login_disabled is True
    mocker.patch("weko_accounts.utils.current_app.login_manager._login_disabled",return_value=True)
    with app.test_request_context(method="GET"):
        result = roles_required(roles)(lambda x,y:x+y)(x=1,y=2)
        assert result == 3
