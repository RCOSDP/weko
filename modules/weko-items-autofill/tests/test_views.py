
import pytest
import json
from invenio_accounts.testutils import login_user_via_session

user_results = [
    (0,403),
    (1,200),
    (2,200),
    (3,200),
    (4,200),
]


@pytest.mark.parametrize('id, status_code', user_results)
def test_get_auto_fill_record_data_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]['email'])
    res = client_api.post('/autofill/get_auto_fill_record_data',
                      data=json.dumps({}),
                      content_type='application/json')
    assert res.status_code == status_code


def test_get_auto_fill_record_data_guest(client_api, users):
    res = client_api.post('/autofill/get_auto_fill_record_data',
                          data=json.dumps({}),
                          content_type='application/json')
    assert res.status_code == 302
