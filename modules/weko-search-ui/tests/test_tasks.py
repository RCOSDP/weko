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


# def check_import_items_task(file_path, is_change_identifier: bool, host_url, lang="en"):
# def test_check_import_items_task(i18n_app, users):
#     current_path = os.path.dirname(os.path.abspath(__file__))
#     file_name = 'index.json'
#     file_path = os.path.join(
#             current_path,
#             'data',
#             file_name)
#     with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
#         assert check_import_items_task(file_path=file_path,is_change_identifier=True,host_url="https://localhost")


# def import_item(item, request_info):
# def remove_temp_dir_task(path):
# def export_all_task(root_url):
# def delete_exported_task(uri, cache_key):
# def is_import_running():
# def check_celery_is_run():