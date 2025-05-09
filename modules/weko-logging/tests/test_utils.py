# -*- coding: utf-8 -*-
""" Pytest for weko_logging utils."""

import json
import pytest
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from mock import patch

from invenio_files_rest.models import FileInstance
from weko_logging.models import UserActivityLog
from weko_logging.utils import UserActivityLogUtils


# UserActivityLogUtils.package_export_log(cls)
# .tox/c1/bin/pytest --cov=weko_logging tests/test_utils.py::test_package_export_log -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_package_export_log(db, users, redis_connect, location):
    """Test package_export_log."""

    mock_date = datetime.now()

    # Case 1 cache_url is None
    log_data1 = UserActivityLog(
        date=mock_date,
        user_id=users[0]["id"],
        community_id=None,
        parent_id=None,
        log={},
        remarks="test_remarks1"
    )
    log_data2 = UserActivityLog(
        date=mock_date,
        user_id=users[1]["id"],
        community_id=None,
        parent_id=1,
        log={},
        remarks="test_remarks2"
    )

    db.session.add(log_data1)
    db.session.flush()
    db.session.add(log_data2)
    db.session.commit()

    redis_connect.delete(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_URL_KEY)
    actual_url = UserActivityLogUtils.package_export_log()
    assert actual_url is not None

    # Case 2 cache_url is not None
    mock_dict = {
        "start_time": datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
        "end_time": datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
        "file_uri": "test_file_uri.zip"
    }
    redis_connect.put(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_URL_KEY, bytes(json.dumps(mock_dict), "utf-8"))
    mock_file_instance = FileInstance.create()
    with patch("weko_logging.utils.FileInstance.get_by_uri") as mock_create:
        mock_create.return_value = mock_file_instance
        with patch("weko_logging.utils.FileInstance.set_contents"):
            actual_url = UserActivityLogUtils.package_export_log()
            mock_create.assert_called_once()

    # Case 3 exception occurs when writing log data to tsv
    with pytest.raises(Exception) as ex:
        with patch("weko_logging.utils.UserActivityLogUtils._write_log_to_tsv") as mock_write_log_to_tsv:
            mock_write_log_to_tsv.side_effect = Exception("test_exception")
            UserActivityLogUtils.package_export_log()

    # Case 4 exception occurs when getting file instance
    with pytest.raises(Exception) as ex:
        with patch("weko_logging.utils.FileInstance.get_by_uri") as mock_get_file_instance:
            mock_get_file_instance.return_value = None
            UserActivityLogUtils.package_export_log()
        assert str(ex.value) == "FileInstance record not found."


# UserActivityLogUtils.cancel_export_log(cls)
# .tox/c1/bin/pytest --cov=weko_logging tests/test_utils.py::test_cancel_export_log -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_cancel_export_log(app, redis_connect, mock_async_result_factory):
    """Test delete_log."""

    # Case 1: export status is None
    redis_connect.delete(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY)
    assert UserActivityLogUtils.cancel_export_log()

    # Case 2: export status is revoked
    mock_export_status = {
        "start_time": datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
        "task_id": "test_task_id"
    }
    mock_async_result = mock_async_result_factory("test_task_id", "REVOKED", "test_result")
    redis_connect.put(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY, bytes(json.dumps(mock_export_status), "utf-8"))
    with patch("weko_logging.utils.revoke") as mock_revoke:
        with patch("weko_logging.utils.AsyncResult") as mocker_async_result:
            mocker_async_result.return_value = mock_async_result
            assert UserActivityLogUtils.cancel_export_log()
            assert redis_connect.get(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY) == bytes("", "utf-8")
            assert redis_connect.get(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_URL_KEY) == bytes("", "utf-8")

    # Case 3: export status is successful
    mock_export_status = {
        "start_time": datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
        "task_id": "test_task_id"
    }
    mock_async_result = mock_async_result_factory("test_task_id", "SUCCESS", "test_result")
    redis_connect.put(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY, bytes(json.dumps(mock_export_status), "utf-8"))
    with patch("weko_logging.utils.revoke") as mock_revoke:
        with patch("weko_logging.utils.AsyncResult") as mocker_async_result:
            mocker_async_result.return_value = mock_async_result
            assert not UserActivityLogUtils.cancel_export_log()
            assert redis_connect.get(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY) != bytes("", "utf-8")

    # Case 4: exception occurs
    mock_export_status = {
        "start_time": datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
        "task_id": "test_task_id"
    }
    mock_async_result = mock_async_result_factory("test_task_id", "SUCCESS", "test_result")
    redis_connect.put(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY, bytes(json.dumps(mock_export_status), "utf-8"))
    with patch("weko_logging.utils.AsyncResult") as mocker_async_result:
        mocker_async_result.return_value = mock_async_result
        with patch("weko_logging.utils.revoke") as mock_revoke:
            mock_revoke.side_effect = Exception("test_exception")
            assert not UserActivityLogUtils.cancel_export_log()
            assert redis_connect.get(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY) != bytes("", "utf-8")


# UserActivityLogUtils.delete_log(cls)
# .tox/c1/bin/pytest --cov=weko_logging tests/test_utils.py::test_delete_log -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_delete_log(app, db):
    """Test delete_log."""

    def _create_test_data():
        UserActivityLog.query.delete()
        db.session.flush()
        mock_date = datetime.now()
        # today
        log_data1 = UserActivityLog(
            date=mock_date,
            log={"data": "today_data"},
        )
        # before 2 days
        log_data2 = UserActivityLog(
            date=mock_date - timedelta(days=2),
            log={"data": "before_2_days_data"},
        )
        # before 3 weeks
        log_data3 = UserActivityLog(
            date=mock_date - timedelta(weeks=3),
            log={"data": "before_3_weeks_data"},
        )
        # before 4 months
        log_data4 = UserActivityLog(
            date=mock_date - relativedelta(months=4),
            log={"data": "before_4_months_data"},
        )
        # before 5 years
        log_data5 = UserActivityLog(
            date=mock_date - relativedelta(years=5),
            log={"data": "before_5_years_data"},
        )
        db.session.add(log_data1)
        db.session.add(log_data2)
        db.session.add(log_data3)
        db.session.add(log_data4)
        db.session.add(log_data5)
        db.session.commit()

    # Case 1: config is None
    with pytest.raises(Exception) as ex:
        UserActivityLogUtils.delete_log()
        ex.message == "WEKO_LOGGING_USER_ACTIVITY_SETTING is not set."

    # Case 2: when or interval is None
    with patch("weko_logging.utils.current_app") as mock_current_app:
        mock_current_app.config.get.return_value = {"delete": {}}
        with pytest.raises(Exception) as ex:
            UserActivityLogUtils.delete_log()
            ex.message == "WEKO_LOGGING_USER_ACTIVITY_SETTING.delete.when or interval is not set."

    # Case 3: when is invalid
    with app.test_request_context():
        app.config.update(
            dict(WEKO_LOGGING_USER_ACTIVITY_SETTING={"delete": {"when": "test_when", "interval": 1}})
        )
        with pytest.raises(Exception) as ex:
            UserActivityLogUtils.delete_log()
            ex.message == "WEKO_LOGGING_USER_ACTIVITY_SETTING.delete.when is invalid."

    # Case 4: delete logs (when: days)
    with app.test_request_context():
        _create_test_data()
        app.config.update(
            dict(WEKO_LOGGING_USER_ACTIVITY_SETTING={"delete": {"when": "days", "interval": 2}})
        )
        UserActivityLogUtils.delete_log()
        actual_records = UserActivityLog.query.all()
        assert len(actual_records) == 1

    # Case 5: delete logs (when: weeks)
    with app.test_request_context():
        _create_test_data()
        app.config.update(
            dict(WEKO_LOGGING_USER_ACTIVITY_SETTING={"delete": {"when": "weeks", "interval": 3}})
        )
        UserActivityLogUtils.delete_log()
        actual_records = UserActivityLog.query.all()
        assert len(actual_records) == 2

    # Case 6: delete logs (when: months)
    with app.test_request_context():
        _create_test_data()
        app.config.update(
            dict(WEKO_LOGGING_USER_ACTIVITY_SETTING={"delete": {"when": "months", "interval": 4}})
        )
        UserActivityLogUtils.delete_log()
        actual_records = UserActivityLog.query.all()
        assert len(actual_records) == 3

    # Case 7: delete logs (when: years)
    with app.test_request_context():
        _create_test_data()
        app.config.update(
            dict(WEKO_LOGGING_USER_ACTIVITY_SETTING={"delete": {"when": "years", "interval": 5}})
        )
        UserActivityLogUtils.delete_log()
        actual_records = UserActivityLog.query.all()
        assert len(actual_records) == 4


# UserActivityLogUtils.get_export_task_status(cls)
# .tox/c1/bin/pytest --cov=weko_logging tests/test_utils.py::test_get_export_task_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_get_export_task_status(app, redis_connect):
    """Test get_export_task_status."""
    start_time = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
    task_id = "test_task_id"

    redis_connect.put(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY,
                      bytes(json.dumps({"start_time": start_time, "task_id": task_id}), "utf-8"))

    actual = UserActivityLogUtils.get_export_task_status()
    expected = {"start_time": start_time, "task_id": task_id}
    assert actual == expected


# UserActivityLogUtils.set_export_status(cls, start_time=None, task_id=None)
# .tox/c1/bin/pytest --cov=weko_logging tests/test_utils.py::test_set_export_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_set_export_status(app, redis_connect):
    """Test set_export_status."""

    # Case 1: start_time and task_id are not None
    start_time = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
    task_id = "test_task_id"

    UserActivityLogUtils.set_export_status(start_time=start_time, task_id=task_id)

    actual_cache_data = redis_connect.get(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY)
    actual = actual_cache_data.decode("utf-8")
    assert actual == json.dumps({"start_time": start_time, "task_id": task_id})

    # Case 2: start_time is None
    task_id2 = "test_task_id2"

    UserActivityLogUtils.set_export_status(task_id=task_id2)
    actual_cache_data = redis_connect.get(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY)
    actual = actual_cache_data.decode("utf-8")
    assert actual == json.dumps({"start_time": start_time, "task_id": task_id2})

    # Case 3: task_id is None
    start_time2 = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")

    UserActivityLogUtils.set_export_status(start_time=start_time2)
    actual_cache_data = redis_connect.get(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY)
    actual = actual_cache_data.decode("utf-8")
    assert actual == json.dumps({"start_time": start_time2, "task_id": task_id2})


# UserActivityLogUtils.get_export_url(cls)
# .tox/c1/bin/pytest --cov=weko_logging tests/test_utils.py::test_get_export_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_get_export_url(app, redis_connect):
    """Test get_export_url."""
    start_time = datetime.strftime(datetime.now() - timedelta(hours=2), "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
    file_uri = "test_file_uri.zip"

    redis_connect.put(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_URL_KEY,
                      bytes(json.dumps({"start_time": start_time, "end_time": end_time, "file_uri": file_uri}), "utf-8"))

    actual = UserActivityLogUtils.get_export_url()
    expected = {"start_time": start_time, "end_time": end_time, "file_uri": file_uri}
    assert actual == expected


# UserActivityLogUtils.save_export_url(cls, start_time, end_time, file_uri)
# .tox/c1/bin/pytest --cov=weko_logging tests/test_utils.py::test_save_export_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_save_export_url(app, redis_connect):
    """Test save_export_url."""
    start_time = datetime.strftime(datetime.now() - timedelta(hours=2), "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
    file_uri = "test_file_uri.zip"

    UserActivityLogUtils.save_export_url(start_time, end_time, file_uri)

    actual_cache_data = redis_connect.get(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_URL_KEY)
    actual = actual_cache_data.decode("utf-8")
    assert actual == json.dumps({"start_time": start_time, "end_time": end_time, "file_uri": file_uri})


# UserActivityLogUtils.clear_export_status(cls)
# .tox/c1/bin/pytest --cov=weko_logging tests/test_utils.py::test_clear_export_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_clear_export_status(app, redis_connect):
    """Test clear_export_status."""
    redis_connect.put(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY, bytes("test_status","utf-8"))
    redis_connect.put(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_URL_KEY, bytes("test_url","utf-8"))
    UserActivityLogUtils.clear_export_status()
    assert redis_connect.get(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY) == bytes("", "utf-8")
    assert redis_connect.get(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_URL_KEY) == bytes("", "utf-8")


# UserActivityLogUtils._write_log_to_tsv(cls, log_data: list)
# .tox/c1/bin/pytest --cov=weko_logging tests/test_utils.py::test_write_log_to_tsv -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_write_log_to_tsv(users):
    """Test _write_log_to_tsv."""

    # Case 1: log_data is empty
    log_data = []
    actual = UserActivityLogUtils._write_log_to_tsv(log_data)
    assert actual == ""

    # Case 2: log_data is not empty
    mock_date = datetime.now()
    log_data = [
        {
            "id": "test_id1",
            "date": mock_date,
            "user_id": users[0]["id"],
            "community_id": "test_community1",
            "parent_id": 1,
            "log": {},
            "remarks": "test_remarks1"
        },
        {
            "id": "test_id2",
            "date": mock_date,
            "user_id": users[1]["id"],
            "community_id": "test_community2",
            "parent_id": 2,
            "log": {},
            "remarks": "test_remarks2"
        }
    ]
    actual = UserActivityLogUtils._write_log_to_tsv(log_data)
    expected_format = "id\tdate\tuser_id\tcommunity_id\tparent_id\tlog\tremarks\r\n" \
                        "test_id1\t{}\t{}\ttest_community1\t1\t{}\ttest_remarks1\r\n" \
                        "test_id2\t{}\t{}\ttest_community2\t2\t{}\ttest_remarks2\r\n"
    assert actual == expected_format.format(
                            mock_date, users[0]["id"], json.dumps({}), mock_date, users[1]["id"], json.dumps({})
                        )
