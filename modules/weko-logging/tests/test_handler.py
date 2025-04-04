# -*- coding: utf-8 -*-
""" Pytest for weko_logging log handler."""

import logging

from weko_logging.handler import UserActivityLogHandler
from weko_logging.models import UserActivityLog


# def __init__(self, app):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_handler.py::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging
def test_init(app):
    handler = UserActivityLogHandler(app)
    assert handler.app == app


# def emit(self, record):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_handler.py::test_emit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging
def test_emit(app, users, mocker, caplog):
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

    # Test Case 3: When parent_id is None
    logger = logging.getLogger("user-activity")
    logger.error("test", extra={
        "operation": "CREATE_ITEM",
        "target_key": 2,
        "remarks": "test",
    })
    assert len(caplog.records) == 3
    records = UserActivityLog.query.all()
    assert len(records) == 1

# def get_community_id_from_path(cls):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_handler.py::test_get_community_id_from_path -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_get_community_id_from_path(app, mocker):

    mock_request = mocker.patch("weko_logging.handler.request")

    # Test Case 1: When the path not contains "/c/"
    mock_request.path = "https://test_server/cc/sample"

    community_id = UserActivityLogHandler.get_community_id_from_path()
    assert community_id is None

    # Test Case 2: When the path contains "/c/"
    mock_request.path = "https://test_server/c/community_sample"

    community_id = UserActivityLogHandler.get_community_id_from_path()
    assert community_id == "community_sample"

    # Test Case 3: When the path not contains "/c/" and the query param "community" exists
    mock_request.path = "https://test_server/cc/sample"
    mock_request.args = {"community": "community_sample2"}

    community_id = UserActivityLogHandler.get_community_id_from_path()
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
