import os
import json
import pytest
from flask import current_app, make_response, request
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

# def check_import_items_task(file_path, is_change_identifier: bool, host_url, lang="en"): ~ GETS STUCK AND DELETES DATA FOLDER
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


# def export_all_task(root_url, user_id, data): ~ GETS STUCK
# def test_export_all_task(i18n_app, users, client_request_args, records):
    # with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
    #     # Doesn't return a value
    #     assert not export_all_task(
    #         root_url="https://localhost:4404/",
    #         user_id=users[3]['obj'].id,
    #         data=records
    #     )


# def delete_exported_task(uri, cache_key):
def test_delete_exported_task(i18n_app, users, file_instance_mock, redis_connect):
    # uri = file_instance_mock
    cache_key = "test_cache_key"

    datastore = redis_connect
    datastore.put(cache_key, json.dumps({'1':'a'}).encode('utf-8'), ttl_secs=30)

    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        # Doesn't return a value
        assert not delete_exported_task("",cache_key)


# def is_import_running(): ~ GETS STUCK
# def test_is_import_running(i18n_app, users, celery):
#     with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
#         assert not is_import_running()


# def check_celery_is_run(): ~ GETS STUCK
# def test_check_celery_is_run(i18n_app, users):
#     with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
#             assert check_celery_is_run()
