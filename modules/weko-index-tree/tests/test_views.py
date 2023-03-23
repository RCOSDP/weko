import json
import pytest
from flask import current_app, make_response, request
from flask_login import current_user
from mock import patch
from werkzeug.local import LocalProxy

from invenio_accounts.testutils import login_user_via_session

from invenio_oauth2server.models import Token
from weko_index_tree.views import set_expand, get_rss_data, create_index


user_results = [
    (0, 200),
]


# def get_rss_data():
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_views.py::test_get_rss_data -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_get_rss_data(app, i18n_app, indices, es, mock_user_ctx, client_request_args):
    _data = {
        'hits': {
            'hits': [
                {
                    '_id': '1'
                },
                {
                    '_id': '2'
                }
            ]
        }
    }
    with patch('weko_index_tree.views.get_elasticsearch_records_data_by_indexes', return_value=_data):
        with patch('weko_items_ui.utils.find_hidden_items', return_value=['1']):
            with patch('weko_gridlayout.utils.build_rss_xml', return_value='test'):
                res = get_rss_data()
                assert res == 'test'


# def set_expand():
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_views.py::test_set_expand_login -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
@pytest.mark.parametrize('id, status_code', user_results)
def test_set_expand_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    res = client_api.post("/api/indextree/set_expand",
                        data=json.dumps({}),
                        content_type="application/json")
    assert res.status_code == status_code

    with patch("weko_index_tree.views.session", return_value={'index_tree_expand_state': ['1']}):
        res = client_api.post("/api/indextree/set_expand",
                            data=json.dumps({'index_id': '1'}),
                            content_type="application/json")
        assert res.status_code == status_code

        res = client_api.post("/api/indextree/set_expand",
                            data=json.dumps({'index_id': '2'}),
                            content_type="application/json")
        assert res.status_code == status_code


# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_views.py::test_set_expand_guest -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_set_expand_guest(client_api, users):
    res = client_api.post("/api/indextree/set_expand",
                          data=json.dumps({}),
                          content_type="application/json")
    assert res.status_code == 200


# def create_index():
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_views.py::test_create_index -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_create_index(client_api, db, users, auth_headers):
    _data = {
        "parent_id": 0,
        "index_info": {}
    }
    login_user_via_session(client=client_api, email=users[0]["email"])
    res = client_api.post("/api/indextree/create",
                        data=json.dumps({}),
                        headers=auth_headers)
    assert res.status_code == 400

    res = client_api.post("/api/indextree/create",
                        data=json.dumps(_data),
                        content_type="application/json",
                        headers=auth_headers)
    assert res.status_code == 400

    _data["index_info"] = {
        "index_name": "Test Index",
        "index_name_english": "Test Index",
        "comment": "",
        "public_state": False,
        "harvest_public_state": True
    }
    res = client_api.post("/api/indextree/create",
                        data=json.dumps(_data),
                        content_type="application/json",
                        headers=auth_headers)
    assert res.status_code == 400


# def dbsession_clean(exception):
