from weko_records_ui.ipaddr import  check_site_license_permission,match_ip_addr
from mock import patch
from unittest.mock import MagicMock

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_ipaddr.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp


# def check_site_license_permission():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_ipaddr.py::test_check_site_license_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_site_license_permission(app,site_license_info):
    with app.test_request_context():
        assert check_site_license_permission()==False

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_ipaddr.py::test_check_site_license_permission2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_site_license_permission2(app,site_license_info,site_license_ipaddr):
    with app.test_request_context(headers={'X-Real-IP': '192.168.0.1'}):
        assert check_site_license_permission()==True

    with app.test_request_context(headers={'X-Forwarded-For': '192.168.1.1, 192.168.0.1'}):
        # Trueを期待したいところだが、現状NG
        assert check_site_license_permission()==False

    with app.test_request_context(headers={'X-Real-IP': '192.168.255.1'}):
        assert check_site_license_permission()==False

    with app.test_request_context(headers={'X-Forwarded-For': '192.168.254.1, 192.168.255.1'}):
        assert check_site_license_permission()==False
    
    with app.test_request_context(headers={'X-Real-IP': '192.168.0.1','X-Forwarded-For': '192.168.254.1, 192.168.255.1'}):
        assert check_site_license_permission()==True

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_ipaddr.py::test_check_site_license_permission_shib_domain -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_site_license_permission_shib_domain(app, site_license_info):
    from flask_security import AnonymousUser
    from types import SimpleNamespace
    
    class DummyShibUser:
        def __init__(self, org):
            self.shib_organization = org
    
    dummy_user = SimpleNamespace()
    dummy_user.is_authenticated = True
    dummy_user.shib_weko_user = [DummyShibUser('domain')]
    
    with app.test_request_context():
        import weko_records_ui.ipaddr as ipaddr_mod
        with patch.object(ipaddr_mod, 'current_user', dummy_user):
            assert ipaddr_mod.check_site_license_permission() is True
    
    dummy_user2 = SimpleNamespace()
    dummy_user2.is_authenticated = True
    dummy_user2.shib_weko_user = [DummyShibUser('otherdomain')]
    with app.test_request_context():
        with patch.object(ipaddr_mod, 'current_user', dummy_user2):
            assert ipaddr_mod.check_site_license_permission() is False

    anon_user = AnonymousUser()
    with app.test_request_context():
        with patch.object(ipaddr_mod, 'current_user', anon_user):
            assert ipaddr_mod.check_site_license_permission() is False

            

# def match_ip_addr(addr, ip_addr):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_ipaddr.py::test_match_ip_addr -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_match_ip_addr():
    addr = {"start_ip_address": "192.168.0.0","finish_ip_address":"192.168.0.255"}
    ip_addr = "192.168.0.100"
    assert match_ip_addr(addr,ip_addr) == True
    ip_addr = "192.168.1.100"
    assert match_ip_addr(addr,ip_addr) == False