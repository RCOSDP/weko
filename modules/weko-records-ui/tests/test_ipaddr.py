from weko_records_ui.ipaddr import  check_site_license_permission,match_ip_addr


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_ipaddr.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp


# def check_site_license_permission():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_ipaddr.py::test_check_site_license_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_site_license_permission(app,site_license_info):
    with app.test_request_context():
        assert check_site_license_permission()==False


# def match_ip_addr(addr, ip_addr):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_ipaddr.py::test_match_ip_addr -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_match_ip_addr():
    addr = {"start_ip_address": "192.168.0.0","finish_ip_address":"192.168.0.255"}
    ip_addr = "192.168.0.100"
    assert match_ip_addr(addr,ip_addr) == True
    ip_addr = "192.168.1.100"
    assert match_ip_addr(addr,ip_addr) == False
    
