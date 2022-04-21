import json
import pytest
from flask import current_app
from mock import patch
from invenio_accounts.testutils import login_user_via_session


user_results_index = [
    (0, 403),
    (1, 403),
    (2, 200),
    (3, 200),
    (4, 200)
]

@pytest.mark.parametrize('id, status_code', user_results_index)
def test_index_action_put_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    with patch('weko_index_tree.rest.is_index_locked', return_value=True):
        res = client_rest.put('/tree/index/1',
                               data=json.dumps({'test':'test'}),
                               content_type='application/json')
        assert res.status_code == status_code


def test_index_action_put_guest(client_rest, users):
    with patch('weko_index_tree.rest.is_index_locked', return_value=True):
        res = client_rest.put('/tree/index/1',
                          data=json.dumps({'test':'test'}),
                          content_type='application/json')
        assert res.status_code == 401


@pytest.mark.parametrize('id, status_code', user_results_index)
def test_index_action_post_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    with patch('weko_index_tree.rest.is_index_locked', return_value=True):
        res = client_rest.post('/tree/index/1',
                               data=json.dumps({'test':'test'}),
                               content_type='application/json')
        assert res.status_code == status_code


def test_index_action_post_guest(client_rest, users):
    with patch('weko_index_tree.rest.is_index_locked', return_value=True):
        res = client_rest.post('/tree/index/1',
                               data=json.dumps({'test':'test'}),
                               content_type='application/json')
        assert res.status_code == 401


@pytest.mark.parametrize('id, status_code', user_results_index)
def test_index_action_delete_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    with patch('weko_index_tree.rest.perform_delete_index', return_value=('test_msg','test_err')):
        res = client_rest.delete('/tree/index/1',
                               data=json.dumps({'test':'test'}),
                               content_type='application/json')
        assert res.status_code == status_code


def test_index_action_delete_guest(client_rest, users):
    with patch('weko_index_tree.rest.perform_delete_index', return_value=('test_msg','test_err')):
        res = client_rest.delete('/tree/index/1',
                               data=json.dumps({'test':'test'}),
                               content_type='application/json')
        assert res.status_code == 401


user_results_tree = [
    (0, 403),
    (1, 403),
    (2, 202),
    (3, 202),
    (4, 202)
]


@pytest.mark.parametrize('id, status_code', user_results_tree)
def test_tree_action_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    with patch('weko_index_tree.rest.Indexes.move', return_value={'r':'moved'}):
        res = client_rest.put('/tree/move/1',
                              data=json.dumps({'test':'test'}),
                              content_type='application/json')
        assert res.status_code == status_code


def test_tree_action_guest(client_rest, users):
    with patch('weko_index_tree.rest.Indexes.move', return_value={'r':'moved'}):
        res = client_rest.put('/tree/move/1',
                              data=json.dumps({'test':'test'}),
                              content_type='application/json')
        assert res.status_code == 4031