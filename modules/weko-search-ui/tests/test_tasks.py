# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
import datetime
import os
import json
import pathlib
import pytest
from flask import current_app, make_response, request
from mock import patch, MagicMock, Mock
from flask_login import current_user
from mock import patch

from weko_index_tree.api import Indexes
from weko_search_ui.tasks import (
    check_import_items_task,
    import_item,
    remove_temp_dir_task,
    export_all_task,
    delete_exported_task,
    is_import_running,
    check_celery_is_run,
    delete_task_id_cache
)

# def check_import_items_task(file_path, is_change_identifier: bool, host_url, lang="en"):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py::test_check_import_items_task -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_import_items_task(i18n_app, users, mocker):
    file_path = "tests/data/test.txt"
    data = {"error": None, 'data_path': 'test_path', 'list_record': [{'errors': None}]}

    p = pathlib.Path(file_path)
    p.touch()

    mock_datetime = mocker.patch('weko_search_ui.tasks.datetime', autospec=True)
    mock_datetime.now.return_value = datetime.datetime(2025, 4, 1, 12, 0, 0)
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
    delete_task_id_cache("revoked_task", cache_key)
    assert redis_connect.redis.exists(cache_key) == True
    
    # cache_data==task_id, state != REVOKED
    delete_task_id_cache("success_task", cache_key)
    assert redis_connect.redis.exists(cache_key) == True
    
    # cache_data==task_id, state == REVOKED
    redis_connect.redis.delete(cache_key)
    redis_connect.put(cache_key, "revoked_task".encode("utf-8"))
    delete_task_id_cache("revoked_task", cache_key)
    assert redis_connect.redis.exists(cache_key) == False
    
    
# def export_all_task(root_url, user_id, data):
def test_export_all_task(i18n_app, users):
    with patch("weko_search_ui.utils.export_all", return_value="/"):
        with patch("weko_admin.utils.reset_redis_cache", return_value=""):
            with patch("weko_search_ui.tasks.delete_exported_task", return_value=""):
                # Doesn't return a value
                assert not export_all_task(
                    root_url="/",
                    user_id=users[3]['obj'].id,
                    data={}
                )


# def delete_exported_task(uri, cache_key):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py::test_delete_exported_task -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_delete_exported_task(i18n_app, db, users, file_instance_mock, redis_connect):
    from invenio_files_rest.models import FileInstance, Location
    # uri = file_instance_mock
    cache_key = "test_cache_key"
    task_key = "test_task_key"
    
    file_uri = "test_location%test.txt"
    datastore = redis_connect
    datastore.put(cache_key, json.dumps({'1':'a'}).encode('utf-8'), ttl_secs=30)
    datastore.put(task_key, "test_task_id".encode("utf-8"))
    
    location=Location(name="testloc",uri="test_location")
    db.session.add(location)
    db.session.commit()
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        # exist cache_key
        file_instance = FileInstance(uri=file_uri)
        db.session.add(file_instance)
        db.session.commit()
        delete_exported_task(file_uri,cache_key,task_key)
        assert redis_connect.redis.exists(task_key) == False
        assert redis_connect.redis.exists(cache_key) == False
        
        # not exist cache_key
        file_instance = FileInstance(uri=file_uri)
        db.session.add(file_instance)
        db.session.commit()
        delete_exported_task(file_uri,cache_key,task_key)
        assert redis_connect.redis.exists(task_key) == False
        assert redis_connect.redis.exists(cache_key) == False
        


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
