import json
import pytest
from flask import current_app, make_response, request
from flask_login import current_user
from mock import patch
from werkzeug.local import LocalProxy

from invenio_accounts.testutils import login_user_via_session

from weko_index_tree.views import set_expand, get_rss_data, create_index


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
def test_get_rss_data(app, i18n_app, indices, es, mock_user_ctx, client_request_args):
    assert get_rss_data()


# def set_expand():
@pytest.mark.parametrize('id, status_code', user_results)
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
    assert res.status_code == 200


# def create_index():
def test_create_index(i18n_app, users, mock_users, mock_user_ctx, client_request_args):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert create_index()



