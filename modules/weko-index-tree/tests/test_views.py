import json
import pytest
from flask import current_app, make_response, request
from flask_login import current_user
from mock import patch
from werkzeug.local import LocalProxy

from invenio_accounts.testutils import login_user_via_session

from invenio_oauth2server.models import Token
from weko_index_tree.models import Index
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
    def _request_process(data):
        return client_api.post(
            "/api/indextree/create",
            data=json.dumps(data),
            content_type="application/json",
            headers=auth_headers,
        )

    _data = {
        "parent_id": 0,
        "index_info": {}
    }
    login_user_via_session(client=client_api, email=users[0]["email"])
    res = _request_process({})
    assert res.status_code == 400
    assert res.get_data(as_text=True) == "No data to create."

    res = _request_process(_data)
    assert res.status_code == 400
    assert res.get_data(as_text=True) == "index_info can not be null."

    _data["index_info"] = {
        "index_name": "Test Index",
        "index_name_english": "Test Index",
        "comment": "",
        "public_state": False,
        "harvest_public_state": True
    }
    res = _request_process(_data)
    assert res.status_code == 400

    with patch("weko_index_tree.api.Indexes.update", return_value=Index(id=100, index_name="Test Index")):
        res = _request_process(_data)
        res_data = json.loads(res.get_data(as_text=True))
        assert res.status_code == 201
        assert res_data["index_name"] == "Test Index"

    with patch("weko_index_tree.api.Indexes.create", return_value=False):
        res = _request_process(_data)
        assert res.status_code == 400
        assert res.get_data(as_text=True) == "Could not create data."

    with patch("weko_index_tree.api.Indexes.update", return_value=None):
        res = _request_process(_data)
        assert res.status_code == 400
        assert res.get_data(as_text=True) == "Could not update data."


# def dbsession_clean(exception):
