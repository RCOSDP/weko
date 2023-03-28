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

user_tree_action = [
    (0, 403),
    (1, 403),
    (2, 202),
    (3, 202),
    (4, 202),
    (5, 403),
    (6, 403),
]

user_tree_action2 = [
    (2, 201),
    (3, 201),
    (4, 201),
]

user_results_index = [
    (0, 403),
    (1, 403),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 403),
    (6, 403),
]

user_create_results1 = [
    (0, 403),
    (1, 403),
    (2, 400),
    (3, 400),
    (4, 400),
    (5, 403),
    (6, 403),
]

user_create_results2 = [
    (0, 403),
    (1, 403),
    (2, 201),
    (3, 201),
    (4, 201),
    (5, 403),
    (6, 403),
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
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::test_tree_action_login -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
@pytest.mark.parametrize('id, status_code', user_tree_action)
def test_tree_action_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    with patch('weko_index_tree.rest.Indexes.move', return_value={'r':'moved'}):
        res = client_rest.put('/tree/move/1',
                              data=json.dumps({'test':'test'}),
                              content_type='application/json')
        assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::test_tree_action_login2 -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
@pytest.mark.parametrize('id, status_code', user_tree_action2)
def test_tree_action_login2(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    with patch('weko_index_tree.rest.Indexes.move', return_value={'is_ok': True}):
        res = client_rest.put('/tree/move/1',
                              data=json.dumps({'test':'test'}),
                              content_type='application/json')
        assert res.status_code == status_code


def test_tree_action_guest(client_rest, users):
    with patch('weko_index_tree.rest.Indexes.move', return_value={'r':'moved'}):
        res = client_rest.put('/tree/move/1',
                              data=json.dumps({'test':'test'}),
                              content_type='application/json')
        assert res.status_code == 401


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
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::test_index_action_get0_login -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_index_action_get0_login(client_rest, users, communities, test_indices):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        res = client_rest.get('/tree/index/0',
                              content_type='application/json')
        assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::test_index_action_get1_login -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_index_action_get1_login(client_rest, users, communities, test_indices):
    with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
        res = client_rest.get('/tree/index/1',
                              content_type='application/json')
        assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::test_index_action_get3_login -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_index_action_get3_login(client_rest, users, communities, test_indices):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        res = client_rest.get('/tree/index/3',
                              content_type='application/json')
        assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::test_index_action_get3_guest -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_index_action_get3_guest(client_rest, users, communities, test_indices):
    res = client_rest.get('/tree/index/3',
                          content_type='application/json')
    assert res.status_code == 200


#     def post(self, index_id, **kwargs):
#             if not self.record_class.create(index_id, data):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::test_index_action_put_login -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
@pytest.mark.parametrize('id, status_code', user_results_index)
def test_index_action_put_login(app, client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    with patch('weko_index_tree.rest.is_index_locked', return_value=True):
        res = client_rest.put('/tree/index/1',
                            data=json.dumps({'test':'test'}),
                            content_type='application/json')
        assert res.status_code == status_code

    with patch('weko_index_tree.rest.is_index_locked', return_value=False):
        with patch('weko_index_tree.rest.check_doi_in_index', return_value=True):
            res = client_rest.put('/tree/index/1',
                                data=json.dumps({'public_state': True}),
                                content_type='application/json')
            assert res.status_code == status_code

            res = client_rest.put('/tree/index/1',
                                data=json.dumps({'harvest_public_state': True}),
                                content_type='application/json')
            assert res.status_code == status_code

        app.config['WEKO_THEME_INSTANCE_DATA_DIR'] = 'data'
        res = client_rest.put('/tree/index/1',
                            data=json.dumps(
                                {'public_state': True, 
                                    'harvest_public_state': True,
                                    'thumbnail_delete_flag': True,
                                    'image_name': 'test/test_file.jpg'}),
                            content_type='application/json')
        if id in [2, 3, 4]:
            assert res.status_code == 400
        else:
            assert res.status_code == status_code

        with patch('weko_index_tree.rest.os.path.isfile', return_value=True):
            with patch('weko_index_tree.rest.os.remove', return_value=True):
                res = client_rest.put('/tree/index/1',
                                    data=json.dumps(
                                        {'public_state': True, 
                                            'harvest_public_state': True,
                                            'thumbnail_delete_flag': True,
                                            'image_name': 'test/test_file.jpg'}),
                                    content_type='application/json')
                if id in [2, 3, 4]:
                    assert res.status_code == 400
                else:
                    assert res.status_code == status_code

        with patch('weko_index_tree.rest.save_index_trees_to_redis', return_value=True):
            with patch('weko_index_tree.rest.Indexes.update', return_value=True):
                res = client_rest.put('/tree/index/1',
                                    data=json.dumps(
                                        {'public_state': True, 
                                        'harvest_public_state': True}),
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
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::test_index_action_post1_login -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
@pytest.mark.parametrize('id, status_code', user_results_index)
def test_index_action_post1_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    with patch('weko_index_tree.rest.is_index_locked', return_value=True):
        res = client_rest.post('/tree/index/1',
                               data=json.dumps({'test':'test'}),
                               content_type='application/json')
        assert res.status_code == status_code


# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::test_index_action_post2_login -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
@pytest.mark.parametrize('id, status_code', user_create_results1)
def test_index_action_post2_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    with patch('weko_index_tree.rest.is_index_locked', return_value=False):
        res = client_rest.post('/tree/index/2',
                               data=json.dumps({'test':'test'}),
                               content_type='application/json')
        assert res.status_code == status_code


# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::test_index_action_post3_login -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
@pytest.mark.parametrize('id, status_code', user_create_results2)
def test_index_action_post3_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    with patch('weko_index_tree.rest.is_index_locked', return_value=False):
        with patch('weko_index_tree.api.Indexes.create', return_value=True):
            res = client_rest.post('/tree/index/3',
                                data=json.dumps({'test':'test'}),
                                content_type='application/json')
            assert res.status_code == status_code


# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::test_index_action_post1_guest -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_index_action_post1_guest(client_rest, users):
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
        with patch('weko_index_tree.rest.save_index_trees_to_redis', return_value=None):
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
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::test_index_tree_action_get_login -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
@pytest.mark.parametrize('id, status_code', user_results_index)
def test_index_tree_action_get_login(client_rest, users, communities, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    res = client_rest.get('/tree', content_type='application/json')
    assert res.status_code == 200

    res = client_rest.get('/tree?action=browsing', content_type='application/json')
    assert res.status_code == 200

    res = client_rest.get('/tree?action=browsing&more_ids=1', content_type='application/json')
    assert res.status_code == 200

    res = client_rest.get('/tree?action=browsing&community=comm1',
                            content_type='application/json')
    assert res.status_code == 200

    res = client_rest.get('/tree?action=browsing&community=comm1&more_ids=1',
                            content_type='application/json')
    assert res.status_code == 200

    res = client_rest.get('/tree?action=browsing&community=comm',
                            content_type='application/json')
    assert res.status_code == 200