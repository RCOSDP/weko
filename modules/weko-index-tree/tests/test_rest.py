import json
import pytest
from flask import current_app
from mock import patch

from invenio_accounts.testutils import login_user_via_session
from invenio_records_rest.config import RECORDS_REST_ENDPOINTS

from weko_index_tree.rest import (
    need_record_permission,
    create_blueprint  
)


user_results_index = [
    (0, 403),
    (1, 403),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
]

user_results_tree = [
    (0, 403),
    (1, 403),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
]


# def need_record_permission(factory_name):
def test_need_record_permission(i18n_app):
    assert need_record_permission('read_permission_factory')


#     def need_record_permission_builder(f):
#         def need_record_permission_decorator(self, *args,
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
        assert res.status_code == 403


# def create_blueprint(app, endpoints):
#         record_class = obj_or_import_string(
#             options.get('record_class'), default=Indexes)
#             record_class=record_class,
def test_create_blueprint(i18n_app, app):
    endpoints = app.config['WEKO_SEARCH_REST_ENDPOINTS']
    assert create_blueprint(app, endpoints)


# class IndexActionResource(ContentNegotiatedMethodView):
#     def __init__(self, ctx, record_serializers=None,
#     def get(self, index_id):
#             index = self.record_class.get_index_with_role(index_id)


#     def post(self, index_id, **kwargs):
#             if not self.record_class.create(index_id, data):
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


#     def put(self, index_id, **kwargs):
#             if not self.record_class.update(index_id, **data):
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


#     def delete(self, index_id, **kwargs):
#         msg, errors = perform_delete_index(index_id, self.record_class, action)
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


# class IndexTreeActionResource(ContentNegotiatedMethodView):
#     def __init__(self, ctx, record_serializers=None,
#     def get(self, **kwargs):
#                     tree = self.record_class.get_contribute_tree(
#                     tree = self.record_class.get_contribute_tree(pid)
#                     tree = self.record_class.get_browsing_tree()
#                     tree = self.record_class.get_more_browsing_tree(
#                         tree = self.record_class.get_browsing_tree(
#                         tree = self.record_class.get_more_browsing_tree(
#                 tree = self.record_class.get_index_tree()
#     def put(self, index_id, **kwargs):
#         moved = self.record_class.move(index_id, **data)
