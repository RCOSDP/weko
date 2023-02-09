# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_tasks.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
import os
import json
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
    check_celery_is_run
)

# def check_import_items_task(file_path, is_change_identifier: bool, host_url, lang="en"):
def test_check_import_items_task(i18n_app, users):
    file_path = "/test/test/test.txt"
    data = {"error": None}

    with patch("weko_search_ui.utils.check_import_items", return_value=data):
        with patch("shutil.rmtree", return_value=""):
            with patch("weko_search_ui.tasks.remove_temp_dir_task.apply_async", return_value=""):
                assert check_import_items_task(file_path=file_path,is_change_identifier=True,host_url="https://localhost")
                

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
def test_delete_exported_task(i18n_app, users, file_instance_mock, redis_connect):
    # uri = file_instance_mock
    cache_key = "test_cache_key"

    datastore = redis_connect
    datastore.put(cache_key, json.dumps({'1':'a'}).encode('utf-8'), ttl_secs=30)
    
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        # Doesn't return a value
        assert not delete_exported_task("",cache_key)


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
