import os
import json
import pytest
from flask import current_app, make_response, request
from flask_login import current_user
from mock import patch

from weko_search_ui.tasks import (
    check_import_items_task,
    import_item,
    remove_temp_dir_task,
    export_all_task,
    delete_exported_task,
    is_import_running,
    check_celery_is_run
)

"""
# def check_import_items_task(file_path, is_change_identifier: bool, host_url, lang="en"):
def test_check_import_items_task(i18n_app, users):
    current_path = os.path.dirname(os.path.abspath(__file__))
    file_name = 'index.json'
    file_path = os.path.join(
            current_path,
            'data',
            file_name)
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert check_import_items_task(file_path=file_path,is_change_identifier=True,host_url="https://localhost")


# def import_item(item, request_info):
def test_import_item(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert import_item()


# def remove_temp_dir_task(path):
def test_remove_temp_dir_task(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            assert remove_temp_dir_task()


# def export_all_task(root_url):
def test_export_all_task(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            assert export_all_task()


# def delete_exported_task(uri, cache_key):
def test_delete_exported_task(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            assert delete_exported_task()


# def is_import_running():
def test_is_import_running(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            assert is_import_running()


# def check_celery_is_run():
def test_check_celery_is_run(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            assert check_celery_is_run()
"""
