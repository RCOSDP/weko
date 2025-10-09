# -*- coding: utf-8 -*-
""" Pytest for weko_logging log handler."""

import logging
from mock import MagicMock

from weko_logging.handler import UserActivityLogHandler
from weko_logging.models import UserActivityLog


# def __init__(self, app):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_handler.py::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_init(app):
    handler = UserActivityLogHandler(app)
    assert handler.app == app


# def emit(self, record):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_handler.py::test_emit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_emit(app, users, mocker, caplog, communities):
    caplog.set_level(logging.DEBUG)

    # Test Case 1: ignored when error level is not ERROR or INFO
    logger = logging.getLogger("user-activity")
    logger.debug("test", extra={
        "operation": "CRAETE_ITEM",
        "target_key": 2,
        "remarks": "remarks",
    })
    assert len(caplog.records) == 0
    records = UserActivityLog.query.all()
    assert len(records) == 0
    logger = logging.getLogger("user-activity")
    logger.warning("test", extra={
        "operation": "CRAETE_ITEM",
        "target_key": 2,
        "remarks": "remarks",
    })
    assert len(caplog.records) == 1
    records = UserActivityLog.query.all()
    assert len(records) == 0

    # Test Case 2: ignored when operation is None
    logger = logging.getLogger("user-activity")
    logger.error("test", extra={
        "target_key": None,
        "remarks": "test",
    })
    assert len(caplog.records) == 2
    records = UserActivityLog.query.all()
    assert len(records) == 0

    # Test Case 3: When request_info is None
    logger = logging.getLogger("user-activity")
    logger.error("test", extra={
        "operation": "ITEM_CREATE",
        "target_key": 2,
        "remarks": "test",
    })
    assert len(caplog.records) == 3
    records = UserActivityLog.query.all()
    assert len(records) == 1

    # Test Case 4: When community_id is not None
    logger = logging.getLogger("user-activity")
    logger.error("test", extra={
        "operation": "ITEM_CREATE",
        "target_key": 2,
        "remarks": "test",
        "community_id": "community_sample",
    })
    assert len(caplog.records) == 4
    records = UserActivityLog.query.all()
    assert len(records) == 2

    # Test Case 5: When request_info exists
    logger = logging.getLogger("user-activity")
    logger.error("test", extra={
        "operation": "ITEM_CREATE",
        "target_key": 2,
        "remarks": "test",
        "request_info": {
            "path": "https://test_server/cc/sample",
            "args": {"c": "community_sample2"},
            "log_group_id": "log_group_123",
        },
    })
    assert len(caplog.records) == 5
    records = UserActivityLog.query.all()
    assert len(records) == 3


# def get_community_id_from_path(cls):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_handler.py::test_get_community_id_from_path -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_get_community_id_from_path(app, mocker):

    mock_request = mocker.patch("weko_logging.handler.request")

    # Test Case 1: When the path not contains "/c/"
    mock_request.path = "https://test_server/cc/sample"

    community_id = UserActivityLogHandler.get_community_id_from_path(None)
    assert community_id is None

    # Test Case 2: When the path contains "/c/"
    mock_request.path = "https://test_server/c/community_sample"

    community_id = UserActivityLogHandler.get_community_id_from_path(None)
    assert community_id == "community_sample"

    # Test Case 3: When the path not contains "/c/" and the query param "community" exists
    mock_request.path = "https://test_server/cc/sample"
    mock_request.args = {"c": "community_sample2"}

    community_id = UserActivityLogHandler.get_community_id_from_path(None)
    assert community_id == "community_sample2"

    # Test Case 4: When the path not contains "/c/" (with request_info)
    request_info = {
        "path": "https://test_server/cc/sample",
    }
    community_id = UserActivityLogHandler.get_community_id_from_path(request_info)
    assert community_id is None

    # Test Case 5: When the path contains "/c/" (with request_info)
    request_info = {
        "path": "https://test_server/c/community_sample",
    }

    community_id = UserActivityLogHandler.get_community_id_from_path(request_info)
    assert community_id == "community_sample"

    # Test Case 6: When the path not contains "/c/" and the query param "community" exists (with request_info)
    request_info = {
        "path": "https://test_server/cc/sample",
        "args": {"c": "community_sample2"},
    }

    community_id = UserActivityLogHandler.get_community_id_from_path(request_info)
    assert community_id == "community_sample2"


# def get_user_id(cls):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_handler.py::test_get_user_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_get_user_id(app, users, mocker):

    # Test Case 1: When the current user is not authenticated
    user_id = UserActivityLogHandler.get_user_id()
    assert user_id is None

    # Test Case 2: When the current user is authenticated
    mock_current_user = mocker.patch("weko_logging.handler.current_user")
    mock_current_user.is_authenticated = True
    mock_current_user.id = users[0]["id"]
    user_id = UserActivityLogHandler.get_user_id()
    assert user_id == 5


# def get_summary_from_request(cls):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_handler.py::test_get_summary_from_request -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_get_summary_from_request(app, mocker):
    # Test Case 1: request is None
    actual1 = UserActivityLogHandler.get_summary_from_request()
    assert actual1 == {}

    mock_request = mocker.patch("weko_logging.handler.request")
    mock_request.remote_addr = None
    mock_request.headers = {}
    mock_request.path = None
    mock_request.oauth = None
    mock_request.args = {}

    # Test Case 2: request has remote_addr
    mock_request.remote_addr = "172.0.0.1"
    actual2 = UserActivityLogHandler.get_summary_from_request()
    assert actual2 == {
        "ip_address": "172.0.0.1",
    }

    # Test Case 3: request has X-Forwarded-For header
    mock_request.remote_addr = None
    mock_request.headers = MagicMock()
    mock_request.headers.getlist.return_value = ["172.0.0.2"]
    actual3 = UserActivityLogHandler.get_summary_from_request()
    assert actual3 == {
        "ip_address": "172.0.0.2",
    }

    # Test Case 4: request has path
    mock_request.path = "https://test_server/cc/sample"
    actual4 = UserActivityLogHandler.get_summary_from_request()
    assert actual4 == {
        "ip_address": "172.0.0.2",
        "path": "https://test_server/cc/sample",
    }

    # Test Case 5: request has oauth
    mock_request.oauth = MagicMock()
    mock_request.oauth.client.client_id = "test_client_id"
    actual5 = UserActivityLogHandler.get_summary_from_request()
    assert actual5 == {
        "ip_address": "172.0.0.2",
        "path": "https://test_server/cc/sample",
        "client_id": "test_client_id",
    }

    # Test Case 6: request has args
    mock_request.args = {
        "c": "community_sample2",
    }
    actual6 = UserActivityLogHandler.get_summary_from_request()
    assert actual6 == {
        "ip_address": "172.0.0.2",
        "path": "https://test_server/cc/sample",
        "client_id": "test_client_id",
        "args": {
            "c": "community_sample2",
        },
    }
