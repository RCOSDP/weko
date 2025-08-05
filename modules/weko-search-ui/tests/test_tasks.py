# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
from datetime import datetime
import os
import json
import pathlib
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
    check_session_lifetime,
    check_flag_metadata_replace,
    check_import_item_splited
)

# def check_import_items_task(file_path, is_change_identifier: bool, host_url, lang="en", all_index_permission=True, can_edit_indexes=[]):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py::test_check_import_items_task -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_import_items_task(i18n_app, users, mocker):
    file_path = "/test/test/test.txt"
    check_result_has_error = {"error": "some_error"}
    check_result_valid  = {"list_record": [{"id": 1, "errors": []}], "data_path": "/tmp/data"}
    list_record_has_error  = {"list_record": [{"id": 1, "errors": ["test_error"]}], "data_path": "/tmp/data"}

    mocker.patch("shutil.rmtree", return_value="")
    mocker.patch("weko_search_ui.tasks.remove_temp_dir_task.apply_async", return_value="")

    with patch("weko_search_ui.tasks.check_tsv_import_items", return_value=check_result_has_error):
        res = check_import_items_task(file_path=file_path, is_change_identifier=True, host_url="https://localhost")
        assert res["error"] == "some_error"
    with patch("weko_search_ui.tasks.check_tsv_import_items", return_value=check_result_valid):
        res = check_import_items_task(file_path=file_path, is_change_identifier=True ,host_url="https://localhost")
        assert res["data_path"] == "/tmp/data"
        assert res["list_record"] == [{"id": 1, "errors": []}]
    with patch("weko_search_ui.tasks.check_tsv_import_items", return_value=list_record_has_error):
        res = check_import_items_task(file_path=file_path, is_change_identifier=True, host_url="https://localhost")
        assert "error" not in res
        assert res["data_path"] == "/tmp/data"
        assert res["list_record"] == [{"id": 1, "errors": ["test_error"]}]

    file_path = "tests/data/test.txt"
    data = {"error": None, 'data_path': 'test_path', 'list_record': [{'errors': None}]}

    p = pathlib.Path(file_path)
    p.touch()

    mock_datetime = mocker.patch('weko_search_ui.tasks.datetime', autospec=True)
    mock_datetime.now.return_value = datetime(2025, 4, 1, 12, 0, 0)
    mock_apply_async = mocker.patch('weko_search_ui.tasks.remove_temp_dir_task.apply_async', autospec=True)
    with patch("weko_search_ui.tasks.check_import_items", return_value=data):
        with patch("shutil.rmtree", return_value=""):
            result = check_import_items_task(file_path=file_path,is_change_identifier=True,host_url="https://localhost")
            assert result["start_date"] == "2025-04-01 12:00:00"
            assert result["end_date"] == "2025-04-01 12:00:00"
            assert result["data_path"] == "test_path"
            assert result["list_record"] == [{'errors': None}]
            assert not result.get("error")
            assert mock_apply_async.call_count == 0

            data['list_record'] = [{'errors': "error"}]
            result = check_import_items_task(file_path=file_path,is_change_identifier=True,host_url="https://localhost")
            assert result["start_date"] == "2025-04-01 12:00:00"
            assert result["end_date"] == "2025-04-01 12:00:00"
            assert result["data_path"] == "test_path"
            assert result["list_record"] == [{'errors': "error"}]
            assert not result.get("error")
            assert mock_apply_async.call_count == 1
    
    data = {"error": 'error', 'data_path': 'test_path', 'list_record': [{'errors': None}]}
    with patch("weko_search_ui.tasks.check_import_items", return_value=data):
        with patch("shutil.rmtree", return_value=""):
            # with patch('weko_search_ui.tasks.get_lifetime', return_value=1800):
            result = check_import_items_task(file_path=file_path,is_change_identifier=True,host_url="https://localhost")
            assert result["start_date"] == "2025-04-01 12:00:00"
            assert result["end_date"] == "2025-04-01 12:00:00"
            assert not result.get("data_path")
            assert not result.get("list_record")
            assert result['error'] == 'error'
    
    p.unlink()


# def check_rocrate_import_items_task(file_path, is_change_identifier: bool, host_url, packaging, mapping_id, lang="en"):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py::test_check_rocrate_import_items_task -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_rocrate_import_items_task(i18n_app, users, mocker):
    # Fixed datetime for mocking
    fixed_dt = datetime(2024, 6, 1, 12, 0, 0)
    fixed_dt_str = fixed_dt.strftime("%Y-%m-%d %H:%M:%S")

    # Patch datetime.now() to return fixed_dt
    mocker.patch("weko_search_ui.tasks.datetime")
    weko_search_ui_tasks_datetime = __import__("weko_search_ui.tasks", fromlist=["datetime"]).datetime
    weko_search_ui_tasks_datetime.now.return_value = fixed_dt

    # Patch dependencies
    mocker.patch("weko_search_ui.tasks.shutil.rmtree")
    mocker.patch("weko_search_ui.tasks.remove_temp_dir_task.apply_async")
    mocker.patch("weko_search_ui.tasks.get_lifetime", return_value=3600)
    mocker.patch("weko_search_ui.tasks.TempDirInfo.set")
    mocker.patch("weko_search_ui.tasks.check_flag_metadata_replace")
    mocker.patch("weko_search_ui.tasks.check_import_item_splited")

    file_path = "/tmp/test/rocrate.zip"
    packaging = "ro-crate"
    mapping_id = 123
    host_url = "http://localhost"
    lang = "en"
    can_edit_indexes = []

    # Case 1: No error in check_result
    list_record = [{"id": 1, "errors": []}]
    check_result = {"list_record": list_record, "data_path": "/tmp/data"}
    mocker.patch("weko_search_ui.tasks.check_jsonld_import_items", return_value=check_result)

    result = check_rocrate_import_items_task(
        file_path=file_path,
        is_change_identifier=True,
        host_url=host_url,
        packaging=packaging,
        mapping_id=mapping_id,
        lang=lang,
        can_edit_indexes=can_edit_indexes
    )
    assert result["start_date"] == fixed_dt_str
    assert result["end_date"] == fixed_dt_str
    assert result["data_path"] == "/tmp/data"
    assert result["list_record"] == list_record
    assert "error" not in result

    # Case 2: All records have errors, triggers remove_temp_dir_task
    list_record_err = [{"id": 1, "errors": ["err1"]}]
    check_result_err = {"list_record": list_record_err, "data_path": "/tmp/data2"}
    mocker.patch("weko_search_ui.tasks.check_jsonld_import_items", return_value=check_result_err)

    result = check_rocrate_import_items_task(
        file_path=file_path,
        is_change_identifier=True,
        host_url=host_url,
        packaging=packaging,
        mapping_id=mapping_id,
        lang=lang,
        can_edit_indexes=can_edit_indexes
    )
    assert result["start_date"] == fixed_dt_str
    assert result["end_date"] == fixed_dt_str
    assert result["data_path"] == "/tmp/data2"
    assert result["list_record"] == list_record_err

    # Case 3: check_result has error key
    check_result_with_error = {"list_record": [], "data_path": "/tmp/data3", "error": "some error"}
    mocker.patch("weko_search_ui.tasks.check_jsonld_import_items", return_value=check_result_with_error)

    result = check_rocrate_import_items_task(
        file_path=file_path,
        is_change_identifier=True,
        host_url=host_url,
        packaging=packaging,
        mapping_id=mapping_id,
        lang=lang,
        can_edit_indexes=can_edit_indexes
    )
    assert result["start_date"] == fixed_dt_str
    assert result["end_date"] == fixed_dt_str
    assert result["error"] == "some error"
    assert "list_record" not in result or result["list_record"] == []

# def import_item(item, request_info):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py::test_import_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_import_item(i18n_app, users, mocker):
    mock_datetime = mocker.patch("weko_search_ui.tasks.datetime")
    mock_datetime.now.return_value = datetime(2025, 1, 1, 12, 00, 00)
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        with patch("weko_search_ui.tasks.import_items_to_system", return_value={}):
            res = import_item({"item"}, "request_info")
            assert res == {"start_date": "2025-01-01 12:00:00"}
        with patch("weko_search_ui.tasks.import_items_to_system", side_effect=Exception("test error")):
            res = import_item({"item"}, "request_info")
            assert res == None

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

        # cancel_flg is True
        datastore.delete(file_cache_key)
        datastore.put(file_cache_key, json.dumps(create_file_json(True)).encode('utf-8'), ttl_secs=30)
        write_files_task('export_path', pickle_filename, current_user.get_id())
        result_data = datastore.get(file_cache_key).decode('utf-8')
        assert json.loads(result_data) == {
            'start_time': start_time_str,
            'finish_time': '',
            'export_path': '',
            'cancel_flg': True,
            'write_file_status': {
                'part1.1': 'canceled',
                '1': 'started',
            }
        }
        mock_remove.assert_called_with(f"{'export_path'}/{pickle_filename}")
        mock_remove.reset_mock()

        # raise exception in write_files
        datastore.delete(file_cache_key)
        datastore.put(file_cache_key, json.dumps(create_file_json(False)).encode('utf-8'), ttl_secs=30)
        with patch('weko_search_ui.tasks.write_files', side_effect=Exception("test error")):
            write_files_task('export_path', pickle_filename, current_user.get_id())
            result_data = datastore.get(file_cache_key).decode('utf-8')
            assert json.loads(result_data) == {
                'start_time': start_time_str,
                'finish_time': '',
                'export_path': '',
                'cancel_flg': True,
                'write_file_status': {
                    'part1.1': 'error',
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
    mock_task_valid = {"celery@worker1": [{"name": "weko_search_ui.tasks.import_item"}]}
    mock_task_invalid = {"celery@worker1": [{"name": "invalid_task_name"}]}
    with patch("weko_search_ui.tasks.check_celery_is_run", return_value=True):
        with patch("celery.task.control.inspect.active", return_value=MagicMock()):
            with patch("celery.task.control.inspect.reserved", return_value=MagicMock()):
                assert is_import_running() == None
            with patch("celery.task.control.inspect.reserved", return_value=mock_task_valid):
                assert is_import_running() == "is_import_running"
            with patch("celery.task.control.inspect.reserved", return_value=mock_task_invalid):
                assert is_import_running() == None
        with patch("celery.task.control.inspect.active", return_value=mock_task_valid):
            assert is_import_running() == "is_import_running"
        with patch("celery.task.control.inspect.active", return_value=mock_task_invalid):
            with patch("celery.task.control.inspect.reserved", return_value=MagicMock()):
                assert is_import_running() == None
    with patch("weko_search_ui.tasks.check_celery_is_run", return_value=False):
        assert is_import_running() == "celery_not_run"


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


# def check_flag_metadata_replace(list_record):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py::test_check_flag_metadata_replace -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_flag_metadata_replace(i18n_app):
    # not metadata_replace
    list_record = [{"id": 1, "errors": [], "metadata_replace": False}]
    check_flag_metadata_replace(list_record)
    assert list_record == [{"id": 1, "errors": [], "metadata_replace": False}]

    # metadata_replace
    list_record = [{"id": 1, "errors": ["test_error."], "metadata_replace": True}]
    check_flag_metadata_replace(list_record)
    assert list_record == [{
        "id": 1, "metadata_replace": True,
        "errors": ["test_error.",
                   "RO-Crate インポートでは、`wk:metadata_replace`フラグを有効にできません。"]
    }]


# def check_import_item_splited(check_result):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py::test_check_import_item_splited -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_import_item_splited(i18n_app):
    # not splited
    check_result = {"list_record": [{"id": 1}]}
    check_import_item_splited(check_result)
    assert check_result == {"list_record": [{"id": 1}]}

    # splited
    check_result = {"list_record": [{"id": 1}, {"id": 2}]}
    check_import_item_splited(check_result)
    assert check_result == {
        "list_record": [{"id": 1}, {"id": 2}],
        "error": "RO-Crate インポートでは、`wk:isSplited`フラグを有効にできません。"
    }
