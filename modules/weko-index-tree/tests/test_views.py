import json
import pytest
from mock import patch
from weko_index_tree.views import set_expand
from invenio_accounts.testutils import login_user_via_session


user_results = [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
]


# def get_rss_data():


# def set_expand():
@pytest.mark.parametrize('id,status_code', user_results)
def test_set_expand_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    res = client_api.post("/api/indextree/set_expand",
                          data=json.dumps({}),
                          content_type="application/json")
    assert res.status_code == status_code


def test_set_expand_guest(client_api, users):
    res = client_api.post("/api/indextree/set_expand",
                          data=json.dumps({}),
                          content_type="application/json")
    assert res.status_code == 302


# def create_index():



