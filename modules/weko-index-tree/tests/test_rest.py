import json
import pytest
from flask import current_app, url_for
import os
import shutil
from mock import patch, MagicMock

from invenio_accounts.testutils import login_user_via_session
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from weko_admin.models import AdminLangSettings
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

class TestIndexActionResource:
    # .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexActionResource::test_post_acl_login -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    @pytest.mark.parametrize('id, is_permission', [
        (0, False),
        (1, False),
        (2, True),
        (3, True),
        (4, True),
        (5, False),
        (6, False),
    ])
    def test_post_acl_login(self, client_rest,users, id, is_permission):
        login_user_via_session(client=client_rest, email=users[id]['email'])
        url = url_for("weko_index_tree_rest.tid_index_action",index_id="1")
        res = client_rest.post(url,json={})
        if is_permission:
            assert res.status_code != 403
        else:
            assert res.status_code == 403

    # .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexActionResource::test_post_acl_guest -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    def test_post_acl_guest(self, client_rest, users):
        url = url_for("weko_index_tree_rest.tid_index_action",index_id="1")
        res = client_rest.post(url,json={})
        assert res.status_code == 401

    # .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexActionResource::test_post -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    def test_post(self, client_rest, users, test_indices, admin_lang_setting, redis_connect):
        os.environ['INVENIO_WEB_HOST_NAME'] = "test"
        login_user_via_session(client=client_rest, email=users[3]['email'])
        
        url = url_for("weko_index_tree_rest.tid_index_action",index_id="1")
        # not data
        res = client_rest.post(url,json={})
        assert res.status_code == 400
        
        # index is locked
        redis_connect.put("lock_index_1","test_lock".encode("UTF-8"))
        data = {"id":"12", "value":"test_new_index"}
        res = client_rest.post(url,json=data)
        assert res.status_code == 200
        assert json.loads(res.data) == {"status":200, "message":"","errors":["Index Delete is in progress on another device."]}
        redis_connect.delete("lock_index_1")
        
        # create failed
        with patch("weko_index_tree.api.Indexes.create",return_value=False):
            data = {"id":"12", "value":"test_new_index"}
            res = client_rest.post(url,json=data)
            assert res.status_code == 400
            
        with patch("weko_index_tree.api.Indexes.create",return_value=True) as mock_create:
            # create with ja, en
            data = {"id":"12", "value":"test_new_index"}
            res = client_rest.post(url,json=data)
            assert res.status_code == 201
            assert json.loads(res.data) == {"status":201, "message":"Index created successfully.","errors":[]}
            assert redis_connect.redis.exists("index_tree_view_test_ja") == True
            assert redis_connect.redis.exists("index_tree_view_test_en") == True
            redis_connect.delete("index_tree_view_test_ja")
            redis_connect.delete("index_tree_view_test_en")
            
            # create with en
            AdminLangSettings.update_lang(lang_code="ja",is_registered=False,sequence=0)
            res = client_rest.post(url,json=data)
            assert res.status_code == 201
            assert json.loads(res.data) == {"status":201, "message":"Index created successfully.","errors":[]}
            assert redis_connect.redis.exists("index_tree_view_test_ja") == False
            assert redis_connect.redis.exists("index_tree_view_test_en") == True
            redis_connect.delete("index_tree_view_test_en")

    # .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexActionResource::test_put_acl_login -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    @pytest.mark.parametrize('id, is_permission', [
        (0, False),
        (1, False),
        (2, True),
        (3, True),
        (4, True),
        (5, False),
        (6, False),
    ])
    def test_put_acl_login(self, client_rest, users, test_indices, id, is_permission):
        login_user_via_session(client=client_rest, email=users[id]['email'])
        url = url_for("weko_index_tree_rest.tid_index_action",index_id="1")
        res = client_rest.put(url,json={})
        if is_permission:
            assert res.status_code != 403
        else:
            assert res.status_code == 403

    # .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexActionResource::test_put_acl_guest -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    def test_put_acl_guest(self, client_rest, users, test_indices):
        url = url_for("weko_index_tree_rest.tid_index_action",index_id="1")
        res = client_rest.put(url,json={})
        assert res.status_code == 401

    # .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexActionResource::test_put -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    @pytest.mark.timeout(300)
    def test_put(self, client_rest, users, test_indices, redis_connect, admin_lang_setting):
        login_user_via_session(client=client_rest, email=users[3]['email'])
        os.environ['INVENIO_WEB_HOST_NAME'] = "test"
        url = url_for("weko_index_tree_rest.tid_index_action",index_id="1")  
        with patch("weko_search_ui.tasks.is_import_running", return_value=None), \
             patch("weko_index_tree.rest.is_index_locked", return_value=False), \
             patch("weko_index_tree.rest.check_doi_in_index", return_value=True), \
             patch("weko_index_tree.api.Indexes.update", return_value=False), \
             patch("weko_workflow.utils.get_cache_data", return_value=True):
            data = {
                "public_date":"","public_state":False,
                "harvest_public_state":False,
            }
            AdminLangSettings.update_lang(lang_code="ja",is_registered=False,sequence=0)
            res = client_rest.put(url,json=data)
            assert res.status_code == 200
            assert json.loads(res.data)=={'delete_flag': False,'errors': ['The index cannot be kept private because there are links from items that have a DOI.'],  'message': '','status': 200}

            data = {
                "public_date":"","public_state":True,
                "harvest_public_state":False,
            }
            AdminLangSettings.update_lang(lang_code="ja",is_registered=False,sequence=0)
            res = client_rest.put(url,json=data)
            assert res.status_code == 200
            assert json.loads(res.data)=={'delete_flag': False,'errors': ['Index harvests cannot be kept private because there are links from items that have a DOI.'],  'message': '','status': 200}

        with patch("weko_search_ui.tasks.is_import_running", return_value=None), \
             patch("weko_index_tree.rest.is_index_locked", return_value=False), \
             patch("weko_index_tree.rest.check_doi_in_index", return_value=False), \
             patch("weko_index_tree.api.Indexes.update", return_value=True), \
             patch("weko_workflow.utils.get_cache_data", return_value=True):
            data = {
                "public_date":"","public_state":False,
                "harvest_public_state":False,
            }
            AdminLangSettings.update_lang(lang_code="ja",is_registered=False,sequence=0)
            res = client_rest.put(url,json=data)
            assert res.status_code == 200
            assert json.loads(res.data)=={'delete_flag': False,'errors': [],  'message': 'Index updated successfully.','status': 200}

            # thumbnail_delete_flag is True, file is existed
            AdminLangSettings.update_lang(lang_code="en",is_registered=False,sequence=0)
            dir_path = os.path.join(current_app.instance_path,
                current_app.config['WEKO_THEME_INSTANCE_DATA_DIR'],
                'indextree')
            thumbnail_path = os.path.join(
                dir_path,
                "test_thumbail.txt"
            )
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)
            if not os.path.isfile(thumbnail_path):
                with open(thumbnail_path, "w") as f:
                    f.write("xxx")
            data = {
                "public_date":"","public_state":True,
                "harvest_public_state":True,
                "thumbnail_delete_flag":True,
                "image_name":"test/test_thumbail.txt"
            }
            res = client_rest.put(url,json=data)
            assert res.status_code == 200
            assert json.loads(res.data) == {"status":200, "message":'Index updated successfully.',"errors":[], "delete_flag":True}
            assert os.path.isfile(thumbnail_path) == False
        
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)
            if not os.path.isfile(thumbnail_path):
                with open(thumbnail_path, "w") as f:
                    f.write("xxx")
            data = {
                "public_date":"","public_state":True,
                "harvest_public_state":True,
                "thumbnail_delete_flag":False,
                "image_name":"test/test_thumbail.txt"
            }
            res = client_rest.put(url,json=data)
            assert res.status_code == 200
            assert json.loads(res.data) == {"status":200, "message":'Index updated successfully.',"errors":[], "delete_flag":False}
            assert os.path.isfile(thumbnail_path) == True
        
        if os.path.isdir(dir_path):
            shutil.rmtree(dir_path)
        
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexActionResource::test_delete_acl_login -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    @pytest.mark.parametrize('id, is_permission', [
        (0, False),
        (1, False),
        (2, True),
        (3, True),
        (4, True),
        (5, False),
        (6, False),
    ])
    def test_delete_acl_login(self, client_rest, users, test_indices, id, is_permission):
        os.environ['INVENIO_WEB_HOST_NAME'] = "test"
        login_user_via_session(client=client_rest, email=users[id]['email'])
        url = url_for("weko_index_tree_rest.tid_index_action",index_id="0")
        res = client_rest.delete(url)
        if is_permission:
            assert res.status_code != 403
        else:
            assert res.status_code == 403
    
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexActionResource::test_delete_acl_guest -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    def test_delete_acl_guest(self, client_rest, users, test_indices):
        url = url_for("weko_index_tree_rest.tid_index_action",index_id="0")
        res = client_rest.delete(url)
        assert res.status_code == 401

# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexActionResource::test_delete -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    def test_delete(self, client_rest, users, test_indices, redis_connect,admin_lang_setting,mocker):
        os.environ['INVENIO_WEB_HOST_NAME'] = "test"
        login_user_via_session(client=client_rest, email=users[3]['email'])
        url = url_for("weko_index_tree_rest.tid_index_action",index_id="0")
        # Incorrect index_id
        with patch("weko_search_ui.tasks.is_import_running", return_value="is_import_running"):  
            res = client_rest.delete(url)
            assert res.status_code == 204

        mocker.patch("weko_index_tree.rest.perform_delete_index", return_value=("test_msg","test_error"))
        url = url_for("weko_index_tree_rest.tid_index_action",index_id="1")

        # import running
        with patch("weko_search_ui.tasks.is_import_running", return_value="is_import_running"),patch("weko_workflow.utils.get_cache_data",return_value=True):
            res = client_rest.delete(url)
            assert res.status_code == 200
            assert json.loads(res.data)['errors'] == ['The index cannot be deleted becase import is in progress.']

        with patch("weko_search_ui.tasks.is_import_running", return_value=None),patch("weko_workflow.utils.get_cache_data",return_value=True):
            # delete with ja, en
            res = client_rest.delete(url)
            assert res.status_code == 200
            assert json.loads(res.data) == {"status": 200, "message": "test_msg", "errors":"test_error"}
            redis_connect.delete("index_tree_view_test_ja")
            redis_connect.delete("index_tree_view_test_en")

            # delete with en
            AdminLangSettings.update_lang(lang_code="ja",is_registered=False,sequence=0)
            res = client_rest.delete(url)
            assert res.status_code == 200
            assert json.loads(res.data) == {"status": 200, "message": "test_msg", "errors":"test_error"}
            assert redis_connect.redis.exists("index_tree_view_test_ja") == False
            assert redis_connect.redis.exists("index_tree_view_test_en") == True
            redis_connect.delete("index_tree_view_test_en")

# class IndexTreeActionResource(ContentNegotiatedMethodView):
#     def __init__(self, ctx, record_serializers=None,
#     def get(self, **kwargs):
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



class TestIndexTreeActionResource:
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexTreeActionResource::test_put_acl_login -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    @pytest.mark.parametrize('id, is_permission', [
        (0, False),
        (1, False),
        (2, True),
        (3, True),
        (4, True),
        (5, False),
        (6, False),
    ])
    def test_put_acl_login(self,client_rest, users,test_indices, id, is_permission):
        login_user_via_session(client=client_rest, email=users[id]['email'])
        data = {"pre_parent":"0","parent":"0","position":"0"}
        index_id="3"
        url = "/tree/move/{}".format(index_id)
        with patch("weko_search_ui.tasks.is_import_running", return_value=None), \
             patch("weko_index_tree.rest.is_index_locked", return_value=False), \
             patch("weko_index_tree.rest.check_doi_in_index", return_value=True), \
             patch("weko_index_tree.api.Indexes.update", return_value=False), \
             patch("weko_workflow.utils.get_cache_data", return_value=True):
            res = client_rest.put(url,json=data)
            if is_permission:
                assert res.status_code != 403
            else:
                assert res.status_code == 403
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexTreeActionResource::test_put_acl_guest -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    def test_put_acl_guest(self, app,client_rest, users):
        data = {"pre_parent":"0","parent":"0","position":"0"}
        index_id="3"
        url = "/tree/move/{}".format(index_id)
        res = client_rest.put(url,json={})
        assert res.status_code == 401

    # .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexTreeActionResource::test_put -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    def test_put(self, client_rest, users, test_indices, admin_lang_setting, redis_connect, without_session_remove):
        os.environ['INVENIO_WEB_HOST_NAME'] = "test"
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            index_id="3"
            url = "/tree/move/{}".format(index_id)
            # not data
            res = client_rest.put(url,json={})
            assert res.json == {'status': 400, 'message': 'Could not load data.'}
            assert res.status_code == 400

            # import running
            with patch("weko_search_ui.tasks.is_import_running", return_value="is_import_running"), \
                patch("weko_workflow.utils.get_cache_data",return_value=True):
                data = {"pre_parent":"0","parent":"0","position":"0"}
                index_id="3"
                url = "/tree/move/{}".format(index_id)
                res = client_rest.put(url,json=data)
                assert res.status_code == 202
                assert json.loads(res.data)['message'] == 'The index cannot be moved becase import is in progress.'

            with patch("weko_search_ui.tasks.is_import_running", return_value=None):
                # move with jp, en
                data = {"pre_parent":"0","parent":"0","position":"0"}
                index_id="3"
                url = "/tree/move/{}".format(index_id)
                res = client_rest.put(url,json=data)
                assert res.status_code == 201
                assert json.loads(res.data) == {'message': 'Index moved successfully.', 'status': 201}
                assert redis_connect.redis.exists("index_tree_view_test_ja") == True
                assert redis_connect.redis.exists("index_tree_view_test_en") == True
                redis_connect.delete("index_tree_view_test_ja")
                redis_connect.delete("index_tree_view_test_en")

                # move with en
                AdminLangSettings.update_lang(lang_code="ja",is_registered=False,sequence=0)
                data = {"pre_parent":"0","parent":"0","position":"1"}
                res = client_rest.put(url,json=data)
                assert res.status_code == 201
                assert json.loads(res.data) == {'message': 'Index moved successfully.', 'status': 201}
                assert redis_connect.redis.exists("index_tree_view_test_ja") == False
                assert redis_connect.redis.exists("index_tree_view_test_en") == True
                redis_connect.delete("index_tree_view_test_en")
        
            # move failed
        with patch("weko_search_ui.tasks.is_import_running", return_value=None),\
            patch("flask_login.utils._get_user", return_value=users[4]['obj']):
            AdminLangSettings.update_lang(lang_code="en",is_registered=False,sequence=0)
            data = {"pre_parent":"0","parent":"0","position":"0"}
            res = client_rest.put(url,json=data)
            assert res.status_code == 202
            assert json.loads(res.data) == {'message': 'You can not move the index.', 'status': 202}
            assert redis_connect.redis.exists("index_tree_view_test_ja") == False
            assert redis_connect.redis.exists("index_tree_view_test_en") == False


# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::test_get_parent_index_tree -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_index_tree/.tox/c1/tmp --full-trace
def test_get_parent_index_tree(client_rest, users, test_indices):
    os.environ['INVENIO_WEB_HOST_NAME'] = 'test'

    res = client_rest.get('/v1/tree/index/11/parent')
    assert res.status_code == 200
    data = json.loads(res.get_data())
    assert data['index']['name'] == 'Test index 11'
    assert data['index']['parent']['name'] == 'Test index 1'

    res = client_rest.get('/v1/tree/index/11/parent?pretty=true')
    assert res.status_code == 200
    str_data = res.get_data().decode('utf-8')
    assert '    ' in str_data

    headers = {}
    headers['Accept-Language'] = 'ja'
    res = client_rest.get('/v1/tree/index/11/parent', headers=headers)
    assert res.status_code == 200
    data = json.loads(res.get_data())
    assert data['index']['name'] == 'テストインデックス 11'
    assert data['index']['parent']['name'] == 'テストインデックス 1'


# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::test_get_parent_index_tree_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_index_tree/.tox/c1/tmp --full-trace
def test_get_parent_index_tree_error(client_rest, users, communities, test_indices):
    os.environ['INVENIO_WEB_HOST_NAME'] = 'test'

    res = client_rest.get('/v1/tree/index/11/parent')
    etag = res.headers['Etag']
    last_modified = res.headers['Last-Modified']

    # Check Etag
    headers = {}
    headers['If-None-Match'] = etag
    res = client_rest.get('/v1/tree/index/11/parent', headers=headers)
    assert res.status_code == 304

    # Check Last-Modified
    headers = {}
    headers['If-Modified-Since'] = last_modified
    res = client_rest.get('/v1/tree/index/11/parent', headers=headers)
    assert res.status_code == 304

    # Invalid version
    res = client_rest.get('/v0/tree/index/11/parent')
    assert res.status_code == 400

    # Access denied
    res = client_rest.get('/v1/tree/index/31/parent')
    assert res.status_code == 403

    # Index not found
    res = client_rest.get('/v1/tree/index/100/parent')
    assert res.status_code == 404

    with patch('weko_index_tree.api.Indexes.get_index_tree', MagicMock(side_effect=SQLAlchemyError())):
        res = client_rest.get('/v1/tree/index/11/parent')
        assert res.status_code == 500
