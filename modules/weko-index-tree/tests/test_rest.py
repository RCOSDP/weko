import json
import pytest
from flask import current_app, url_for
import os
import shutil
from mock import patch, MagicMock

from invenio_accounts.testutils import login_user_via_session
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from weko_admin.models import AdminLangSettings
from weko_index_tree.models import Index
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

from flask_oauthlib.provider import OAuth2Provider
from invenio_oauth2server.views.server import login_oauth2_user
from weko_index_tree.api import Indexes
from weko_index_tree.errors import PermissionError
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexManagementAPI -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko_index_tree/.tox/c1/tmp --full-trace -p no:warnings

class TestIndexManagementAPI:
    # インデックスツリーの構造（indices_for_api）
    # Root Index 0
    # ├── Sample Index [1623632832836]
    # ├── parent Index [1740974499997]
    # │   ├── child Index 1 [1740974554289]
    # │   ├── child Index 2 [1740974612379]

    @property
    def count_indices(self):
        return Index.query.count()

    # .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexManagementAPI::test_get_v1 -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko_index_tree/.tox/c1/tmp --full-trace -p no:warnings
    def test_get_v1(self, app, client_rest, auth_headers_noroleuser, auth_headers_sysadmin, auth_headers_sysadmin_without_scope, create_auth_headers, indices_for_api):
        """
        インデックス管理API-インデクス取得
        - 全インデックス取得: ユーザー権限に応じた取得可否を確認
        - 特定のインデックス取得: 存在する/しないインデックスの取得、およびアクセス制御の確認
        - インデックスツリー取得: 親インデックスから子インデックスが正しく取得できるかを確認
        - 認証なしアクセス: 認証が必要なAPIに対してUnauthorized(401)が返るか確認
        """

        oauth2 = OAuth2Provider()
        oauth2.after_request(login_oauth2_user)

        default_indices = [0, 1740974499997, 1740974612379]
        admin_indices = [0, 1623632832836, 1740974499997, 1740974554289, 1740974612379, 1740974612380]

        # 全インデックス取得テスト（ユーザー権限に応じた取得可否を確認）
        self.run_get_all_indices(app, client_rest, auth_headers_noroleuser, 200, expected_indices=default_indices)
        self.run_get_all_indices(app, client_rest, auth_headers_sysadmin, 200, expected_indices=admin_indices)

        for role, headers in create_auth_headers.items():
            print(f"Testing get indices for {role}")
            if role in ["sysadmin", "repoadmin", "comadmin"]:
                self.run_get_all_indices(app, client_rest, headers, 200, expected_indices=admin_indices)
                self.run_get_specific_index(app, client_rest, 1740974499997, headers, 200)
                self.run_get_specific_index(app, client_rest, 1740974554289, headers, 200)
            else:
                self.run_get_all_indices(app, client_rest, headers, 200, expected_indices=default_indices)
                self.run_get_specific_index(app, client_rest, 1740974499997, headers, 200)
                self.run_get_specific_index(app, client_rest, 1740974554289, headers, 403)

        # 特定のインデックス取得テスト（異なる権限によるアクセス確認）
        self.run_get_specific_index(app, client_rest, 1740974499997, auth_headers_noroleuser, 200)  # 一般ユーザー（public_state=True）
        self.run_get_specific_index(app, client_rest, 1740974554289, auth_headers_noroleuser, 403)  # 一般ユーザー（public_state=False）
        self.run_get_specific_index(app, client_rest, 1740974554289, auth_headers_sysadmin_without_scope, 403)  # 管理者、scopeなしtoken（public_state=False）
        self.run_get_specific_index(app, client_rest, 1740974499997, auth_headers_sysadmin, 200)  # 管理者（全取得可能）
        self.run_get_specific_index(app, client_rest, 9999999999999, auth_headers_sysadmin, 404)  # 存在しないID

        # インデックスツリー取得テスト（親インデックスを指定し、子インデックスを取得できるか確認）
        self.run_get_index_tree(app, client_rest, 1740974499997, auth_headers_noroleuser, [1740974499997, 1740974612379])  # 一般ユーザー
        self.run_get_index_tree(app, client_rest, 1740974499997, auth_headers_sysadmin, [1740974499997, 1740974554289, 1740974612379, 1740974612380])  # 管理者

        # 認証なしでのアクセス試行テスト（Unauthorized(401)を確認）
        self.run_get_index_unauthorized(app, client_rest)

        # VersionNotFoundRESTError
        url = "v2/tree"
        response = client_rest.get(url, headers=auth_headers_sysadmin)
        assert response.status_code == 400

        # エラー
        with patch("weko_index_tree.api.Indexes.get_all_indexes", side_effect=PermissionError):
            with patch("weko_index_tree.api.Indexes.get_index", side_effect=PermissionError):
                url = "v1/tree"
                response = client_rest.get(url, headers=auth_headers_sysadmin)
                assert response.status_code == 403

        with patch("weko_index_tree.api.Indexes.get_all_indexes", side_effect=SQLAlchemyError):
            with patch("weko_index_tree.api.Indexes.get_index", side_effect=SQLAlchemyError):
                url = "v1/tree"
                response = client_rest.get(url, headers=auth_headers_sysadmin)
                assert response.status_code == 500

        with patch("weko_index_tree.api.Indexes.get_all_indexes", side_effect=Exception):
            with patch("weko_index_tree.api.Indexes.get_index", side_effect=Exception):
                url = "v1/tree"
                response = client_rest.get(url, headers=auth_headers_sysadmin)
                assert response.status_code == 500

        url = "v1/tree"
        headers = {"If-None-Match": "true"}
        headers.update(auth_headers_sysadmin)
        response = client_rest.get(url, headers=headers)
        assert response.status_code == 200

    def run_get_all_indices(self, app, client_rest, user_role, expected_status, expected_indices):
        """
        全インデックス取得APIのテスト
        - 権限に応じて取得できるインデックスが異なることを確認
        - 取得結果に含まれるすべての `cid` を抽出し、期待されるインデックスと比較
        """
        url = "v1/tree"
        response = client_rest.get(url, headers=user_role)
        assert response.status_code == expected_status
        if response.status_code == 200:
            data = response.json
            assert "index" in data, "レスポンスJSONに 'index' キーが含まれていない"
            retrieved_indices = self.extract_all_cids(data["index"])
            assert set(retrieved_indices) == set(expected_indices), f"取得インデックスが想定外: {retrieved_indices}"

    def extract_all_cids(self, index_data):
        """
        再帰的に `cid` を抽出するヘルパー関数
        """
        cids = [index_data["cid"]]
        for child in index_data.get("children", []):
            cids.extend(self.extract_all_cids(child))
        return cids

    def run_get_specific_index(self, app, client_rest, index_id, user_role, expected_status):
        """
        特定のインデックス取得APIのテスト
        - 指定したインデックスIDが取得できるか確認
        - ユーザー権限に応じたアクセス可否を確認
        """
        url = f"v1/tree/{index_id}"
        response = client_rest.get(url, headers=user_role)
        assert response.status_code == expected_status
        if response.status_code == 200:
            data = response.json
            assert "index" in data, "レスポンスJSONに 'index' キーが含まれていない"
            retrieved_indices = self.extract_all_cids(data["index"])
            assert index_id in retrieved_indices, f"取得したインデックスIDが一致しない: {retrieved_indices}"

    def run_get_index_tree(self, app, client_rest, index_id, user_role, expected_child_indices):
        """
        インデックスツリー取得APIのテスト
        - 親インデックスを指定して、適切な子インデックスが取得できるか確認
        """
        url = f"v1/tree/{index_id}"
        response = client_rest.get(url, headers=user_role)
        assert response.status_code == 200
        data = response.json
        assert "index" in data, "レスポンスJSONに 'index' キーが含まれていない"
        retrieved_indices = self.extract_all_cids(data["index"])
        assert set(retrieved_indices) == set(expected_child_indices), f"取得した子インデックスが想定外: {retrieved_indices}"

    def run_get_index_unauthorized(self, app, client_rest):
        """
        認証なしでインデックス取得を試みるテスト
        - 認証が必要なAPIにアクセスし、Unauthorized(401)が返ることを確認
        """
        url = "v1/tree"
        response = client_rest.get(url, headers={})
        assert response.status_code == 401
        print(f"Unauthorizedアクセスエラー: {response.get_data(as_text=True)}")


    # .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexManagementAPI::test_post_v1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_index_tree/.tox/c1/tmp --full-trace -p no:warnings
    def test_post_v1(self, app, db, client_rest, auth_headers_sysadmin, auth_headers_noroleuser, auth_headers_sysadmin_without_scope,create_auth_headers,admin_lang_setting, indices_for_api):
        """
        インデックス管理API-インデックス登録
        - 正常系: インデックスの作成が成功するか確認
        - 異常系:
          - 認証なしでのアクセスが拒否されるか(401)
          - 権限のないユーザーが403エラーを受け取るか
          - 必須パラメータなしのリクエストで400エラーを返すか
          - サーバーエラー時に500を返すか
        """

        json_ = {
            "index": {
                "parent": 0,
                "index_name": "テストインデックス",
                "index_name_english": "Test Index",
                "index_link_name": "テストリンク",
                "index_link_name_english": "Test Link",
                "index_link_enabled": True,
                "comment": "テストコメント",
                "more_check": False,
                "display_no": 5,
                "harvest_public_state": True,
                "display_format": "1",
                "public_state": False,
                "public_date": "20250401",
                "rss_status": False,
                "browsing_role": "3,4,-98,-99",
                "contribute_role": "",
                "browsing_group": "3,4,-98,-99",
                "contribute_group": "",
                "online_issn": "",
            }
        }

        with patch("weko_index_tree.tasks.update_oaiset_setting.delay",side_effect = MagicMock()):
            # 正常にインデックスを作成できるか（200）
            self.run_create_index_success(app, client_rest, auth_headers_sysadmin, json_)
            self.create_index_with_default_values(client_rest,auth_headers_sysadmin)
            # 認証なしのリクエストが拒否されるか（401）
            self.run_create_index_unauthorized(app, client_rest)

            allowed_roles = ["sysadmin", "repoadmin"]
            for role, headers in create_auth_headers.items():
                if role in allowed_roles:
                    # print(f"{role} should be able to create index (200)")
                    self.run_create_index_success(app, client_rest, headers, json_)
                else:
                    # print(f"{role} should NOT be able to create index (403)")
                    self.run_create_index_forbidden(app, client_rest, headers)

            # 権限のないユーザーが403エラーを受け取るか
            self.run_create_index_forbidden(app, client_rest, auth_headers_noroleuser)
            self.run_create_index_forbidden(app, client_rest, auth_headers_sysadmin_without_scope)

            # DBエラー発生時に500エラーが返るか
            self.run_create_index_server_error(app, client_rest, auth_headers_sysadmin)

            # VersionNotFoundRESTError
            url = "v2/tree/index/"
            response = client_rest.post(url, headers=auth_headers_sysadmin, json=json_)
            assert response.status_code == 400

            url = "v1/tree/index/"
            # empty body
            response = client_rest.post(url, headers=auth_headers_sysadmin)
            assert response.status_code == 400
            assert response.json["message"] == "Bad Request: Failed to parse provided."
            # invalid body
            response = client_rest.post(url, headers=auth_headers_sysadmin,json=123)
            assert response.status_code == 400
            assert response.json["message"] == "Bad Request: Invalid payload, {'_schema': ['Invalid input type.']}"
            # missing required field
            response = client_rest.post(url, headers=auth_headers_sysadmin,json={})
            assert response.status_code == 400
            assert response.json["message"] == "Bad Request: Invalid payload, {'index': {'parent': ['Missing data for required field.']}}"

            from copy import deepcopy
            invalid_parrent_id = deepcopy(json_)
            invalid_parrent_id["index"]["parent"] = 999999
            response = client_rest.post(url, headers=auth_headers_sysadmin,json=invalid_parrent_id)
            assert response.status_code == 404
            assert response.json["message"] == "Index not found: 999999."

            private_parrent_id = deepcopy(json_)
            private_parrent_id["index"]["parent"] = 1740974499997

            with patch("weko_index_tree.rest.can_user_access_index", return_value=False):
                url = "v1/tree/index/"
                response = client_rest.post(url, headers=auth_headers_sysadmin, json=private_parrent_id)
                assert response.status_code == 403

            url = "v1/tree/index/"
            # parent is not deleted
            count_before = self.count_indices
            response = client_rest.post(url, headers=auth_headers_sysadmin, json=private_parrent_id)
            assert response.status_code == 200
            data = response.json
            assert data["index"]["parent"] == 1740974499997
            assert self.count_indices == count_before + 1, "Index has not been created successfully"

            # parent is deleted
            url = "v1/tree/index/"
            parent = Indexes.get_index(1740974499997)
            parent.is_deleted = True
            db.session.commit()
            response = client_rest.post(url, headers=auth_headers_sysadmin, json=private_parrent_id)
            assert response.status_code == 404
            assert response.json["message"] == "Index is deleted: 1740974499997."

            # エラー
            with patch("weko_index_tree.api.Indexes.create", return_value=None):
                url = "v1/tree/index/"
                response = client_rest.post(url, headers=auth_headers_sysadmin, json=json_)
                assert response.status_code == 500

            with patch("weko_index_tree.api.Indexes.update", return_value=None):
                count_before = self.count_indices
                url = "v1/tree/index/"
                response = client_rest.post(url, headers=auth_headers_sysadmin, json=json_)
                assert response.status_code == 500
                assert self.count_indices == count_before, "Index has been created successfully"

                # DBエラーを発生させるために `Indexes.get_all_indexes` をモック
            with patch("weko_index_tree.api.Indexes.create", side_effect=SQLAlchemyError):
                url = "v1/tree/index/"
                response = client_rest.post(url, headers=auth_headers_sysadmin, json=json_)
                assert response.status_code == 500

            with patch("weko_index_tree.api.Indexes.update", side_effect=SQLAlchemyError):
                count_before = self.count_indices
                url = "v1/tree/index/"
                response = client_rest.post(url, headers=auth_headers_sysadmin, json=json_)
                assert response.status_code == 500
                assert self.count_indices == count_before, "Index has been created successfully"

            with patch("weko_index_tree.api.Indexes.update", side_effect=Exception):
                count_before = self.count_indices
                url = "v1/tree/index/"
                response = client_rest.post(url, headers=auth_headers_sysadmin, json=json_)
                assert response.status_code == 500
                assert self.count_indices == count_before, "Index has been created successfully"

    def create_index_with_default_values(self, client_rest, auth_headers):
        """Test creating an index with empty JSON to ensure default values are used."""
        count_before = self.count_indices
        json_ = {"index": {"parent": 0}}
        url = "v1/tree/index/"
        response = client_rest.post(url, headers=auth_headers, json=json_)
        assert response.status_code == 200
        created_index = response.json
        from weko_index_tree.models import Index
        from weko_index_tree.api import Indexes
        created_index_db = Index.query.order_by(Index.created.desc()).first()
        assert created_index_db is not None
        assert created_index_db.parent == 0
        assert created_index_db.index_name == "New Index"
        assert created_index_db.index_name_english == "New Index"
        assert created_index_db.index_link_name == ""
        assert created_index_db.index_link_name_english == "New Index"
        assert created_index_db.index_link_enabled is False
        assert created_index_db.comment == ""
        assert created_index_db.more_check is False
        assert created_index_db.display_no == 5
        assert created_index_db.harvest_public_state is True
        assert created_index_db.display_format == "1"
        assert created_index_db.public_state is False
        assert created_index_db.public_date is None
        assert created_index_db.rss_status is False
        assert set(created_index_db.browsing_role.split(",")) == set(map(lambda x: str(x["id"]), Indexes.get_account_role()))
        assert set(created_index_db.browsing_role.split(",")) == set(map(lambda x: str(x["id"]), Indexes.get_account_role()))
        assert created_index_db.browsing_group == ""
        assert created_index_db.contribute_group == ""
        assert created_index_db.online_issn == ""
        assert self.count_indices == count_before + 1, "Index has not been created successfully"

        # print("Test passed: Index created with default values.")

    def run_create_index_success(self, app, client_rest, auth_headers, json_):
        """
        正常にインデックスを作成できるか確認（200）
        """
        count_before = self.count_indices
        url = "v1/tree/index/"
        response = client_rest.post(url, headers=auth_headers, json=json_)
        assert response.status_code == 200
        data = response.json
        assert "index" in data, "レスポンスに 'index' キーが含まれていない"
        assert data["index"]["index_name"] == "テストインデックス", "インデックス名が一致しない"
        assert data["index"]["index_name_english"] == "Test Index", "英語のインデックス名が一致しない"
        assert self.count_indices == count_before + 1, "Index has not been created successfully"

    def run_create_index_unauthorized(self, app, client_rest):
        """
        認証なしでのリクエストが401エラーを返すか確認
        """
        url = "v1/tree/index/"
        headers = {"Accept-Language": "ja"}
        payload = {
            "index": {
                "index_name": "Unauthorized Test"
            }
        }

        response = client_rest.post(url, headers=headers, json=payload)
        assert response.status_code == 401, "認証なしのリクエストが401にならなかった"
        # print(f"Unauthorizedアクセスエラー: {response.get_data(as_text=True)}")

    def run_create_index_forbidden(self, app, client_rest, auth_headers):
        """
        権限のないユーザーが403エラーを受け取るか確認
        """
        url = "v1/tree/index/"
        payload = {
            "index": {
                "index_name": "Forbidden Test"
            }
        }

        response = client_rest.post(url, headers=auth_headers, json=payload)
        assert response.status_code == 403, "権限なしユーザーのリクエストが403にならなかった"

    def run_create_index_server_error(self, app, client_rest, auth_headers):
        """
        DBエラー発生時に500エラーを返すか確認
        """
        count_before = self.count_indices
        url = "v1/tree/index/"
        payload = {
            "index": {
                "parent": "0",
                "index_name": "DB Error Test"
            }
        }

        # DBエラーを発生させるために `record_class.create` をモック
        with patch("weko_index_tree.api.Indexes.create", side_effect=SQLAlchemyError):
            response = client_rest.post(url, headers=auth_headers, json=payload)
            assert response.status_code == 500, "DBエラー発生時のリクエストが500にならなかった"
            assert self.count_indices == count_before, "Index has been created when it should not have been"

    # .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexManagementAPI::test_put_v1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_index_tree/.tox/c1/tmp --full-trace -p no:warnings
    def test_put_v1(self, app, client_rest, auth_headers_sysadmin, auth_headers_noroleuser,auth_headers_noroleuser_1,auth_headers_sysadmin_without_scope, create_auth_headers, indices_for_api):
        """
        インデックス管理API - インデックス更新
        - 正常系: インデックスの更新が成功するか確認
        - 異常系:
          - 認証なしでのアクセスが拒否されるか (401)
          - 権限のないユーザーが 403 エラーを受け取るか
          - 存在しないIDを指定した場合 404 を返すか
          - 必須パラメータなしのリクエストで 400 エラーを返すか
          - サーバーエラー時に 500 を返すか
        """
        payload = {
            "index": {
                "index_name": "更新テストインデックス",
                "index_name_english": "Updated Test Index",
                "index_link_name": "更新リンク",
                "index_link_name_english": "Updated Link"
            }
        }

        with patch("weko_index_tree.tasks.update_oaiset_setting.delay",side_effect = MagicMock()):
            # 正常にインデックスを更新できるか（200）
            self.run_update_index_success(app, client_rest, auth_headers_sysadmin)

            # 認証なしのリクエストが拒否されるか（401）
            self.run_update_index_unauthorized(app, client_rest)

            allowed_roles = ["sysadmin", "repoadmin"]
            for role, headers in create_auth_headers.items():
                if role in allowed_roles:
                    print(f"{role} should be able to update index (200)")
                    self.run_update_index_success(app, client_rest, headers)
                else:
                    print(f"{role} should NOT be able to update index (403)")
                    self.run_update_index_forbidden(app, client_rest, headers)

            # 権限のないユーザーが403エラーを受け取るか
            self.run_update_index_forbidden(app, client_rest, auth_headers_noroleuser)
            self.run_update_index_forbidden(app, client_rest, auth_headers_sysadmin_without_scope)

            # 存在しないインデックスIDで404エラー
            self.run_update_index_not_found(app, client_rest, auth_headers_sysadmin)

            # 無効なリクエストデータで400エラー
            self.run_update_index_bad_request(app, client_rest, auth_headers_sysadmin)

            # DBエラー発生時に500エラー
            self.run_update_index_server_error(app, client_rest, auth_headers_sysadmin)

            # ユーザーは目標インデックスへのアクセス権限持つか（403/200）
            url = "v1/tree/index/1740974554289"
            response = client_rest.put(url, headers=auth_headers_noroleuser_1, json=payload)
            assert response.status_code == 403
            print(response.get_data())
            response = client_rest.put(url, headers=auth_headers_sysadmin, json=payload)
            assert response.status_code == 200

            with patch("weko_index_tree.rest.can_user_access_index", return_value=False):
                url = "v1/tree/index/1740974554289"
                response = client_rest.put(url, headers=auth_headers_sysadmin, json=payload)
                assert response.status_code == 403

            # VersionNotFoundRESTError
            url = "v2/tree/index/9999999999999"
            response = client_rest.put(url, headers=auth_headers_sysadmin, json={})
            assert response.status_code == 400

            url = "v1/tree/index/1740974499997"
            response = client_rest.put(url, headers=auth_headers_sysadmin, json={"index":""})
            assert response.status_code == 400

            url = "v1/tree/index/1740974499997"
            with patch("weko_index_tree.api.Indexes.update", return_value=None):
                response = client_rest.put(url, headers=auth_headers_sysadmin, json=payload)
                assert response.status_code == 500

            with patch("weko_index_tree.api.Indexes.get_index", side_effect=PermissionError):
                response = client_rest.put(url, headers=auth_headers_sysadmin, json=payload)
                assert response.status_code == 403

            with patch("weko_index_tree.api.Indexes.get_index", side_effect=Exception):
                response = client_rest.put(url, headers=auth_headers_sysadmin, json=payload)
                assert response.status_code == 500

    def run_update_index_success(self, app, client_rest, auth_headers):
        """
        正常にインデックスを更新できるか確認（200）
        """
        index_id = 1740974499997  # 存在するインデックスID
        url = f"v1/tree/index/{index_id}"
        payload = {
            "index": {
                "index_name": "更新テストインデックス",
                "index_name_english": "Updated Test Index",
                "index_link_name": "更新リンク",
                "index_link_name_english": "Updated Link"
            }
        }

        response = client_rest.put(url, headers=auth_headers, json=payload)
        assert response.status_code == 200
        data = response.json
        assert data["index"]["index_name"] == "更新テストインデックス", "インデックス名が更新されていない"
        assert data["index"]["index_name_english"] == "Updated Test Index", "英語のインデックス名が更新されていない"

        with app.app_context():
            updated_index = Indexes.get_index(index_id)
            assert updated_index is not None, f"インデックスID {index_id} がDBに存在しない"
            assert updated_index.index_name == "更新テストインデックス", "DBのインデックス名が更新されていない"
            assert updated_index.index_name_english == "Updated Test Index", "DBの英語のインデックス名が更新されていない"
            assert updated_index.index_link_name == "更新リンク", "DBのリンク名が更新されていない"
            assert updated_index.index_link_name_english == "Updated Link", "DBの英語のリンク名が更新されていない"

    def run_update_index_unauthorized(self, app, client_rest):
        """
        認証なしでのリクエストが401エラーを返すか確認
        """
        index_id = 1740974499997
        url = f"v1/tree/index/{index_id}"
        payload = {"index": {"index_name": "Unauthorized Update"}}

        response = client_rest.put(url, headers={}, json=payload)
        assert response.status_code == 401, "認証なしのリクエストが401にならなかった"

    def run_update_index_forbidden(self, app, client_rest, auth_headers):
        """
        権限のないユーザーが403エラーを受け取るか確認
        """
        index_id = 1740974499997
        url = f"v1/tree/index/{index_id}"
        payload = {"index": {"index_name": "Forbidden Update"}}

        response = client_rest.put(url, headers=auth_headers, json=payload)
        assert response.status_code == 403, "権限なしユーザーのリクエストが403にならなかった"

    def run_update_index_not_found(self, app, client_rest, auth_headers):
        """
        存在しないインデックスIDで404エラーを確認
        """
        index_id = 9999999999999  # 存在しないID
        url = f"v1/tree/index/{index_id}"
        payload = {"index": {"index_name": "Not Found Test"}}

        response = client_rest.put(url, headers=auth_headers, json=payload)
        assert response.status_code == 404, "存在しないインデックスIDで404にならなかった"

    def run_update_index_bad_request(self, app, client_rest, auth_headers):
        """
        無効なリクエストデータで400エラーを確認
        """
        index_id = 1740974499997
        url = f"v1/tree/index/{index_id}"
        payload = {"wrong_key": "This is invalid data"}  # "index"キーがない

        response = client_rest.put(url, headers=auth_headers, json=payload)
        assert response.status_code == 400, "無効なリクエストデータで400にならなかった"

    def run_update_index_server_error(self, app, client_rest, auth_headers):
        """
        DBエラー発生時に500エラーを確認
        """
        index_id = 1740974499997
        url = f"v1/tree/index/{index_id}"
        payload = {"index": {"index_name": "DB Error Test"}}

        # DBエラーを発生させるために `Indexes.update` をモック
        with patch("weko_index_tree.api.Indexes.update", side_effect=SQLAlchemyError):
            response = client_rest.put(url, headers=auth_headers, json=payload)
            assert response.status_code == 500, "DBエラー発生時のリクエストが500にならなかった"

    # .tox/c1/bin/pytest --cov=weko_index_tree tests/test_rest.py::TestIndexManagementAPI::test_delete_v1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_index_tree/.tox/c1/tmp --full-trace
    def test_delete_v1(self, app, client_rest, auth_headers_sysadmin, auth_headers_noroleuser, auth_headers_sysadmin_without_scope, create_auth_headers, indices_for_api):
        """
        インデックス管理API - インデックス削除
        - 正常系: インデックスの削除が成功するか確認
        - 異常系:
          - 認証なしでのアクセスが拒否されるか (401)
          - 権限のないユーザーが 403 エラーを受け取るか
          - 存在しないIDを指定した場合 404 を返すか
          - サーバーエラー時に 500 を返すか
        """
        with patch("weko_index_tree.tasks.delete_oaiset_setting.delay",side_effect = MagicMock()):
            with patch("weko_index_tree.tasks.update_oaiset_setting.delay",side_effect = MagicMock()):
                # 認証なしのリクエストが拒否されるか（401）
                self.run_delete_index_unauthorized(app, client_rest)

                allowed_roles = ["sysadmin", "repoadmin"]
                for role, headers in create_auth_headers.items():
                    if role in allowed_roles:
                        print(f"{role} should be able to delete index (200)")
                        url = "v1/tree/index/"
                        response = client_rest.post(url, headers=auth_headers_sysadmin, json={"index":{"parent_id": "1623632832836"}})
                        id = response.json["index"]["id"]
                        print(id)
                        self.run_delete_index_success(app, client_rest, headers, id)
                    else:
                        print(f"{role} should NOT be able to delete index (403)")
                        self.run_delete_index_forbidden(app, client_rest, headers)

                # 権限のないユーザーが403エラーを受け取るか
                self.run_delete_index_forbidden(app, client_rest, auth_headers_noroleuser)
                self.run_delete_index_forbidden(app, client_rest, auth_headers_sysadmin_without_scope)

                # 存在しないインデックスIDで404エラー
                self.run_delete_index_not_found(app, client_rest, auth_headers_sysadmin)

                # DBエラー発生時に500エラー
                self.run_delete_index_server_error(app, client_rest, auth_headers_sysadmin)

                # VersionNotFoundRESTError
                url = "v2/tree/index/9999999999999"
                response = client_rest.delete(url, headers=auth_headers_sysadmin)
                assert response.status_code == 400

                url = "v1/tree/index/1740974612379"

                with patch("weko_index_tree.rest.can_user_access_index", return_value=False):
                    url = "v1/tree/index/1740974612379"
                    response = client_rest.delete(url, headers=auth_headers_sysadmin)
                    assert response.status_code == 403


                with patch("weko_index_tree.api.Indexes.delete", return_value=None):
                    response = client_rest.delete(url, headers=auth_headers_sysadmin)
                    assert response.status_code == 500

                with patch("weko_index_tree.api.Indexes.delete", side_effect=PermissionError):
                    response = client_rest.delete(url, headers=auth_headers_sysadmin)
                    assert response.status_code == 403

                with patch("weko_index_tree.api.Indexes.delete", side_effect=Exception):
                    response = client_rest.delete(url, headers=auth_headers_sysadmin)
                    assert response.status_code == 500

    def run_delete_index_success(self, app, client_rest, auth_headers, index_id):
        """
        正常にインデックスを削除できるか確認（200）
        """
        url = f"v1/tree/index/{index_id}"

        # 削除APIを呼び出す
        response = client_rest.delete(url, headers=auth_headers)
        assert response.status_code == 200, f"削除APIのレスポンスコードが200ではなく {response.status_code}"
        assert json.loads(response.data)["message"] == "Index deleted successfully."

        # DBからデータを再取得して検証
        with app.app_context():
            deleted_index = Indexes.get_index(index_id)
            assert deleted_index is None, f"削除後もインデックスID {index_id} がDBに存在する"

    def run_delete_index_unauthorized(self, app, client_rest):
        """
        認証なしでのリクエストが401エラーを返すか確認
        """
        index_id = 1740974499997
        url = f"v1/tree/index/{index_id}"

        response = client_rest.delete(url, headers={})
        assert response.status_code == 401, "認証なしのリクエストが401にならなかった"

    def run_delete_index_forbidden(self, app, client_rest, auth_headers):
        """
        権限のないユーザーが403エラーを受け取るか確認
        """
        index_id = 1740974499997
        url = f"v1/tree/index/{index_id}"

        response = client_rest.delete(url, headers=auth_headers)
        assert response.status_code == 403, "権限なしユーザーのリクエストが403にならなかった"

    def run_delete_index_not_found(self, app, client_rest, auth_headers):
        """
        存在しないインデックスIDで404エラーを確認
        """
        index_id = 9999999999999  # 存在しないID
        url = f"v1/tree/index/{index_id}"

        response = client_rest.delete(url, headers=auth_headers)
        assert response.status_code == 404, "存在しないインデックスIDで404にならなかった"

    def run_delete_index_server_error(self, app, client_rest, auth_headers):
        """
        DBエラー発生時に500エラーを確認
        """
        index_id = 1740974499997
        url = f"v1/tree/index/{index_id}"

        # DBエラーを発生させるために `Indexes.delete` をモック
        with patch.object(Indexes, "delete", side_effect=SQLAlchemyError):
            response = client_rest.delete(url, headers=auth_headers)
            assert response.status_code == 500, "DBエラー発生時のリクエストが500にならなかった"
