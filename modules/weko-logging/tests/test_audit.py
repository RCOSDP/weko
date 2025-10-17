# -*- coding: utf-8 -*-
"""Pytest for weko_logging.audit."""

import logging
from weko_logging.audit import WekoLoggingUserActivity, get_level_from_string
from weko_logging.handler import UserActivityLogHandler

# def init_app(self, app):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_audit.py::test_init_app -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging
def test_init_app(app):
    test = WekoLoggingUserActivity()
    test.init_app(app)
    logger_sample = logging.getLogger("weko-logging-activity")
    assert isinstance(app.extensions["weko-logging-activity"], type(logger_sample))


# def init_config(self, app):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_audit.py::test_init_config -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging
def test_init_config(app):
    test = WekoLoggingUserActivity()

    test.init_config(app)
    assert "WEKO_LOGGING_OPERATION_MASTER" in app.config
    assert "WEKO_LOGGING_USER_ACTIVITY_DB_SETTING" in app.config
    assert "WEKO_LOGGING_FS_INTERVAL" not in app.config


# def init_logger(self, app):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_audit.py::test_init_logger -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging
def test_init_logger(app):
    test = WekoLoggingUserActivity()

    # Test Case 1: When the logger is not initialized
    test.init_logger(app)
    logger_sample = logging.getLogger("user-activity")
    assert isinstance(app.extensions["weko-logging-activity"], type(logger_sample))
    assert len(logger_sample.handlers) == 3
    assert isinstance(logger_sample.handlers[0], UserActivityLogHandler)
    assert logger_sample.handlers[0].level == logging.ERROR

    # Test Case 2: When the logger is initialized
    test.init_logger(app)
    logger_sample = logging.getLogger("user-activity")
    assert isinstance(app.extensions["weko-logging-activity"], type(logger_sample))
    assert len(logger_sample.handlers) == 3
    assert isinstance(logger_sample.handlers[0], logging.StreamHandler)
    assert logger_sample.handlers[0].level == logging.ERROR
    assert logger_sample.handlers[0].formatter._fmt == "[%(asctime)s] - %(levelname)s - %(filename)s - %(name)s - %(funcName)s - %(message)s [in %(pathname)s:%(lineno)d]"


# def get_level_from_string(level):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_audit.py::test_get_level_from_string -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging
def test_get_level_from_string():

    # Test Case 1: When the log level is "ERROR"
    assert get_level_from_string("ERROR") == logging.ERROR

    # Test Case 2: When the log level is "INFO"
    assert get_level_from_string("INFO") == logging.INFO

    # Test Case 3: When the log level is "DEBUG"
    assert get_level_from_string("DEBUG") == logging.DEBUG
