# -*- coding: utf-8 -*-
""" Pytest for weko_logging tasks."""

import pytest

from weko_logging.tasks import export_all_user_activity_logs, delete_log
from weko_logging.utils import UserActivityLogUtils


# def export_all_user_activity_logs():
# .tox/c1/bin/pytest --cov=weko_logging tests/test_tasks.py::test_export_all_user_activity_logs -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_export_all_user_activity_logs(app, redis_connect, mocker):

    # Test Case 1: When the export is successful
    redis_connect.delete(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY)
    redis_connect.delete(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_URL_KEY)
    mock_export = mocker.patch("weko_logging.tasks.UserActivityLogUtils.package_export_log")
    mock_export.return_value = "test_url.txt"

    result = export_all_user_activity_logs()
    assert result == "test_url.txt"

    # Test Case 2: When the export is failed
    redis_connect.delete(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY)
    redis_connect.delete(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_URL_KEY)
    mock_export.return_value = None

    result = export_all_user_activity_logs()
    assert result is None

    # Test Case 3: When the export raises an exception
    redis_connect.delete(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY)
    redis_connect.delete(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_URL_KEY)
    mock_export.side_effect = Exception

    with pytest.raises(Exception):
        export_all_user_activity_logs()


# def delete_log():
# .tox/c1/bin/pytest --cov=weko_logging tests/test_tasks.py::test_delete_log -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_delete_log(app, redis_connect, mocker):

    mock_delete = mocker.patch("weko_logging.tasks.UserActivityLogUtils.delete_log")

    # Test Case 1: When the log is deleted
    delete_log()

    # Test Case 2: When the log raises an exception
    mock_delete.side_effect = Exception
    with pytest.raises(Exception):
        delete_log()
