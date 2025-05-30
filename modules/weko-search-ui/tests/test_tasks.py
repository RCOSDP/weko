# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
import os
import json
import pytest
import unittest
from flask import current_app, make_response, request
from mock import patch, MagicMock, Mock
from flask_login import current_user
from mock import patch

from weko_index_tree.api import Indexes
from weko_search_ui.tasks import (
    check_import_items_task,
    check_rocrate_import_items_task,
    import_item,
    remove_temp_dir_task,
    export_all_task,
    write_files_task,
    is_import_running,
    check_celery_is_run,
    delete_task_id_cache_on_revoke,
    check_session_lifetime
)

# def check_import_items_task(file_path, is_change_identifier: bool, host_url, lang="en"):
def test_check_import_items_task(i18n_app, users):
    file_path = "/test/test/test.txt"
    data = {"error": None}

    with patch("weko_search_ui.utils.check_import_items", return_value=data):
        with patch("shutil.rmtree", return_value=""):
            with patch("weko_search_ui.tasks.remove_temp_dir_task.apply_async", return_value=""):
                assert check_import_items_task(file_path=file_path,is_change_identifier=True,host_url="https://localhost")


# def check_rocrate_import_items_task(file_path, is_change_identifier: bool, host_url, packaging, mapping_id, lang="en"):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py::test_check_rocrate_import_items_task -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_rocrate_import_items_task(i18n_app, users):
    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data',
        'rocrate_import',
        'new_crate_v2.zip'
    )
    list_record = [
        {
            "$schema": "/items/jsonschema/30001",
            "metadata": {
                "publish_status": "public",
                "edit_mode": "Keep",
                "feedback_mail_list": [
                    {
                        "mail": "wekosoftware@nii.ac.jp",
                        "author_id": ""
                    }
                ],
                "path": [
                    1623632832836
                ],
                "files_info": [
                    {
                        "key": "item_30001_file22",
                        "items": []
                    }
                ]
            },
            "item_type_name": "デフォルトアイテムタイプ（シンプル）",
            "item_type_id": 30001,
            "publish_status": "public",
            "file_path": [
                "sample.rst",
                "data.csv"
            ],
            "non_extract": [
                "data.csv"
            ],
            "is_change_identifier": False,
            "identifier_key": "item_30001_identifier_registration13",
            "errors": [
                "Please specify PubDate with YYYY-MM-DD.",
                "'item_30001_title0' is a required property",
                "'item_30001_resource_type11' is a required property",
                "Title is required item.",
                "'pubdate' is a required property"
            ],
            "warnings": [],
            "status": "new",
            "id": None
        }
    ]

    with patch("weko_search_ui.utils.check_jsonld_import_items", return_value=list_record):
        with patch("shutil.rmtree", return_value=""):
            with patch("weko_search_ui.tasks.remove_temp_dir_task.apply_async", return_value=""):
                assert check_rocrate_import_items_task(file_path=file_path,is_change_identifier=True,host_url="https://localhost",packaging="ro-crate",mapping_id="30001",lang="en")


# def import_item(item, request_info):
def test_import_item(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        # Doesn't return a value
        assert not import_item("item", "request_info")


# def remove_temp_dir_task(path):
def test_remove_temp_dir_task(i18n_app, users, indices):
    current_path = os.path.dirname(os.path.abspath(__file__))
    file_name = 'index.json'
    file_path = os.path.join(
        current_path,
        'temp',
    )

    try:
        os.mkdir(file_path)
    except:
        pass

    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        # Doesn't return a value
        assert not remove_temp_dir_task(file_path)


# def delete_task_id_cache
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py::test_delete_task_id_cache -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_delete_task_id_cache(app, users, redis_connect, mocker):
    class MockAsyncResult:
        def __init__(self,task_id):
            self.task_id=task_id
        @property
        def state(self):
            if self.task_id == "revoked_task":
                return "REVOKED"
            else:
                return "SUCCESS"
    mocker.patch("weko_search_ui.tasks.AsyncResult",side_effect=MockAsyncResult)
    cache_key = "test_task_id_cache"

    # cache_data != task_id
    redis_connect.put(cache_key, "success_task".encode("utf-8"))
    delete_task_id_cache_on_revoke("revoked_task", cache_key)
    assert redis_connect.redis.exists(cache_key) == True

    # cache_data==task_id, state != REVOKED
    delete_task_id_cache_on_revoke("success_task", cache_key)
    assert redis_connect.redis.exists(cache_key) == True

    # cache_data==task_id, state == REVOKED
    redis_connect.redis.delete(cache_key)
    redis_connect.put(cache_key, "revoked_task".encode("utf-8"))
    delete_task_id_cache_on_revoke("revoked_task", cache_key)
    assert redis_connect.redis.exists(cache_key) == False


# def export_all_task(root_url, user_id, data, start_time):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py::test_export_all_task -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_export_all_task(i18n_app, users):
    try:
        with patch("weko_search_ui.tasks.export_all"):
            export_all_task('/', users[3]['obj'].id, {}, '2024/05/02 13:24:51')
    except:
        assert False

# def write_files_task(export_path, pickle_file_name, user_id)
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py::test_write_files_task -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_write_files_task(redis_connect, users, mocker):
    class MockOpen:
        def __init__(self, path, encoding=None):
            self.path = path
            self.encoding = encoding
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_value, traceback):
            pass

    start_time_str = '2024/05/12 04:33:51'
    def create_file_json(cancel_flg):
        return {
            'start_time': start_time_str,
            'finish_time': '',
            'export_path': '',
            'cancel_flg': cancel_flg,
            'write_file_status': {
                '1': 'started'
            }
        }

    def create_pickle_data(name):
        return {
            'item_type_id': '',
            'name': name,
            'root_url': '',
            'jsonschema': 'items/jsonschema/',
            'keys': [],
            'labels': [],
            'recids': [],
            'data': {}
        }

    def mock_open(path, encoding=None):
        return MockOpen(path, encoding)

    with patch('flask_login.utils._get_user', return_value=users[3]['obj']):
        mocker.patch('builtins.open', side_effect=mock_open)
        mock_remove=mocker.patch('weko_search_ui.tasks.os.remove')
        current_app.config["WEKO_ADMIN_CACHE_PREFIX"]="test_cache_prefix_{name}_{user_id}_"
        msg_key = current_app.config['WEKO_ADMIN_CACHE_PREFIX'].format(
            name='MSG_EXPORT_ALL',
            user_id=current_user.get_id()
        )
        file_cache_key = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name='RUN_MSG_EXPORT_ALL_FILE_CREATE',
            user_id=current_user.get_id()
        )
        task_cache_key = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name='KEY_EXPORT_ALL',
            user_id=current_user.get_id()
        )
        datastore = redis_connect
        pickle_filename = 'test_path/test_file.part1.pickle'

        # cancel_flg is False, result of write_files is True, export_file's name includes 'part'
        file_json = create_file_json(False)
        file_json['write_file_status']['2'] = 'waiting'
        datastore.put(file_cache_key, json.dumps(file_json).encode('utf-8'), ttl_secs=30)
        with patch('weko_search_ui.tasks.write_files', return_value=True), \
                patch('weko_search_ui.tasks.pickle.load', return_value=create_pickle_data('test.part1')):
            write_files_task('export_path',pickle_filename, current_user.get_id())
            result_data = datastore.get(file_cache_key).decode('utf-8')
            assert json.loads(result_data) == {
                'start_time': start_time_str,
                'finish_time': '',
                'export_path': '',
                'cancel_flg': False,
                'write_file_status': {
                    '.1': 'finished',
                    '1': 'started',
                    '2': 'waiting'
                }
            }
            assert datastore.get(task_cache_key).decode('utf-8') == "None"
            mock_remove.assert_called_with(f"{'export_path'}/{pickle_filename}")
            mock_remove.reset_mock()

        # cancel_flg is False, result of write_files is False, export_file's name doesn't include 'part'
        datastore.delete(file_cache_key)
        datastore.put(file_cache_key, json.dumps(create_file_json(False)).encode('utf-8'), ttl_secs=30)
        with patch('weko_search_ui.tasks.write_files', return_value=False), \
                patch('weko_search_ui.tasks.pickle.load', return_value=create_pickle_data('test')):
            write_files_task('export_path', pickle_filename, current_user.get_id())
            result_data = datastore.get(file_cache_key).decode('utf-8')
            assert json.loads(result_data) == {
                'start_time': start_time_str,
                'finish_time': '',
                'export_path': '',
                'cancel_flg': True,
                'write_file_status': {
                    '.1': 'error',
                    '1': 'started',
                }
            }
            assert datastore.get(msg_key).decode('utf-8') == 'Export failed.'
            assert datastore.get(task_cache_key).decode('utf-8') == "None"
            mock_remove.assert_called_with(f"{'export_path'}/{pickle_filename}")
            mock_remove.reset_mock()


# def is_import_running():
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py::test_is_import_running -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_is_import_running(i18n_app):
    with patch("weko_search_ui.tasks.check_celery_is_run",return_Value=True):
        with patch("celery.task.control.inspect.active",return_Value=MagicMock()):
            with patch("celery.task.control.inspect.reserved",return_Value=MagicMock()):
                assert is_import_running()==None


# def check_celery_is_run():
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py::test_check_celery_is_run -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_celery_is_run(i18n_app):
    with patch("celery.task.control.inspect.ping",return_value={'hostname': True}):
        assert check_celery_is_run()==True

    with patch("celery.task.control.inspect.ping",return_value={}):
        assert check_celery_is_run()==False


class TestCheckSessionLifetime(unittest.TestCase):
    @patch('weko_search_ui.tasks.get_lifetime')
    def test_check_session_lifetime(self, mock_get_lifetime):
        """Test check_session_lifetime function with mocked get_lifetime."""
        # Test when session lifetime is greater than or equal to one day
        mock_get_lifetime.return_value = 86400
        self.assertTrue(check_session_lifetime())
        mock_get_lifetime.return_value = 86401
        self.assertTrue(check_session_lifetime())

        # Test when session lifetime is less than one day
        mock_get_lifetime.return_value = 86399
        self.assertFalse(check_session_lifetime())
