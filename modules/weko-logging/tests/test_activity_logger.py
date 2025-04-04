# -*- coding: utf-8 -*-
""" User activity log test """

from datetime import datetime
import logging

import pytest

from invenio_accounts.testutils import login_user_via_session

from weko_logging.activity_logger import UserActivityLogger
from weko_logging.models import UserActivityLog


# def __init__(self, app):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_activity_logger.py::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_init(app):
    """
    Test init app.

    :param app: Flask application.
    """
    UserActivityLogger(app)


# def UserActivityLogger:
# .tox/c1/bin/pytest --cov=weko_logging tests/test_activity_logger.py::test_log_error_success -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
@pytest.mark.parametrize(
    "user_exists, eppn_exists, ip_addr_exists, client_id_exists, source_exists," \
    "parent_id_exists, target_exists, remarks_exists, community_id_exists",
    [
        (True, True, True, True, True, True, True, True, True),
        (False, False, True, True, True, True, True, True, True),
        (True, False, True, True, True, True, True, True, True),
        (True, True, False, True, True, True, True, True, True),
        (True, True, True, False, True, True, True, True, True),
        (True, True, True, True, False, True, True, True, False),
        (True, True, True, True, True, False, True, True, True),
        (True, True, True, True, True, True, False, True, True),
        (True, True, True, True, True, True, True, False, True),
        (True, True, True, True, True, True, True, True, False),
    ]
)
def test_log_error_success(app, client, db, users, communities,
                       user_exists, eppn_exists, ip_addr_exists, client_id_exists,
                       source_exists, parent_id_exists, target_exists, remarks_exists,
                       community_id_exists, caplog, mocker):
    """
    Test error handler.

    :param app: Flask application.
    """

    caplog.set_level(logging.INFO)

    # user_id
    mock_current_user = mocker.patch("weko_logging.handler.current_user")
    if user_exists:
        login_user_via_session(client=client, email=users[0]['email'])
        mock_current_user.is_authenticated = True
        mock_current_user.id = users[0]["id"]

        if eppn_exists:
            mock_current_user.shib_weko_user[0].shib_eppn = "test_eppn"
        else:
            mock_current_user.shib_weko_user = []
    else:
        mock_current_user.is_authenticated = False
        mock_current_user.id = None
        mock_current_user.shib_weko_user = []

    mock_request = mocker.patch("weko_logging.handler.request")
    mock_request.headers.getlist.return_value = None

    # ip address
    mock_request.remote_addr = "123.456.789.001" if ip_addr_exists else None

    # client_id
    if client_id_exists:
        mock_request.oauth.client.client_id = "test_client_id"
    else:
        mock_request.oauth = None

    # parent_id
    expected_parent_id = None
    if parent_id_exists:
        log_record = UserActivityLog(
            date=datetime.now(), user_id=users[0]["id"], community_id=None,
            parent_id=None, log={"operation": "test"}, remarks="test")
        db.session.add(log_record)
        db.session.commit()
        expected_parent_id = log_record.id

    # target
    expected_operation = "ITEM_BULK_CREATE"
    expected_target_key = None
    if target_exists:
        expected_operation = "ITEM_CREATE"
        expected_target_key = 2

    # remarks
    expected_remarks = None
    if remarks_exists:
        expected_remarks = "test"

    # community_id and path
    community_id = communities[0].id
    if source_exists:
        if community_id_exists:
            mock_request.path = f"https://test_server/c/{community_id}/item/2"
        else:
            mock_request.path = "https://test_server/item/2"
    else:
        mock_request.path = None

    UserActivityLogger.error(
        operation=expected_operation, parent_id=expected_parent_id,
        target_key=expected_target_key, remarks=expected_remarks,)

    assert len(caplog.records) == 1

    records = UserActivityLog.query.all()
    if not user_exists:
        assert len(records) == 3
    elif parent_id_exists:
        assert len(records) == 2
    else:
        assert len(records) == 1


# .tox/c1/bin/pytest --cov=weko_logging tests/test_activity_logger.py::test_log_error_invalid_case -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_log_error_invalid_case(app, client, db, users, caplog, mocker):
    """
    Test error handler.

    :param app: Flask application.
    """

    caplog.set_level(logging.INFO)

    # user_id
    mock_current_user = mocker.patch("weko_logging.handler.current_user")

    login_user_via_session(client=client, email=users[0]['email'])
    mock_current_user.is_authenticated = True
    mock_current_user.id = users[0]["id"]
    mock_current_user.shib_weko_user = []

    mock_request = mocker.patch("weko_logging.handler.request")
    mock_request.headers.getlist.return_value = None

    # ip address
    mock_request.remote_addr = "123.456.789.001"

    # client_id
    mock_request.oauth = None

    # parent_id
    expected_parent_id = None

    # target
    expected_target_key = 2

    # community_id and path
    mock_request.path = "https://test_server/item/2"

    # Test Case 1: invalid operation
    with pytest.raises(ValueError) as excinfo:
        UserActivityLogger.error(
            operation="INVALID_OPERATION", parent_id=expected_parent_id,
            target_key=expected_target_key)
        assert "Invalid operation: INVALID_OPERATION" in str(excinfo.value)

    # Test Case 2: target is null and target_key is not null
    with pytest.raises(ValueError) as excinfo:
        UserActivityLogger.error(
            operation="ITEM_BULK_CREATE", parent_id=expected_parent_id,
            target_key=expected_target_key)
        assert "target is None and target_key is not None" in str(excinfo.value)

    # Test Case 3: target is not null and target_key is null
    with pytest.raises(ValueError) as excinfo:
        UserActivityLogger.error(
            operation="ITEM_CREATE", parent_id=expected_parent_id,
            target_key=None)
        assert "target is None and target_key is not None" in str(excinfo.value)


# def UserActivityLogger:
# .tox/c1/bin/pytest --cov=weko_logging tests/test_activity_logger.py::test_log_info_success -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
@pytest.mark.parametrize(
    "user_exists, eppn_exists, ip_addr_exists, client_id_exists, source_exists," \
    "parent_id_exists, target_exists, remarks_exists, community_id_exists",
    [
        (True, True, True, True, True, True, True, True, True),
        (False, False, True, True, True, True, True, True, True),
        (True, False, True, True, True, True, True, True, True),
        (True, True, False, True, True, True, True, True, True),
        (True, True, True, False, True, True, True, True, True),
        (True, True, True, True, False, True, True, True, False),
        (True, True, True, True, True, False, True, True, True),
        (True, True, True, True, True, True, False, True, True),
        (True, True, True, True, True, True, True, False, True),
        (True, True, True, True, True, True, True, True, False),
    ]
)
def test_log_info_success(app, client, db, users, communities,
                       user_exists, eppn_exists, ip_addr_exists, client_id_exists,
                       source_exists, parent_id_exists, target_exists, remarks_exists,
                       community_id_exists, caplog, mocker):
    """
    Test error handler.

    :param app: Flask application.
    """

    caplog.set_level(logging.INFO)

    # user_id
    mock_current_user = mocker.patch("weko_logging.handler.current_user")
    if user_exists:
        login_user_via_session(client=client, email=users[0]['email'])
        mock_current_user.is_authenticated = True
        mock_current_user.id = users[0]["id"]

        if eppn_exists:
            mock_current_user.shib_weko_user[0].shib_eppn = "test_eppn"
        else:
            mock_current_user.shib_weko_user = []
    else:
        mock_current_user.is_authenticated = False
        mock_current_user.id = None
        mock_current_user.shib_weko_user = []

    mock_request = mocker.patch("weko_logging.handler.request")
    mock_request.headers.getlist.return_value = None

    # ip address
    mock_request.remote_addr = "123.456.789.001" if ip_addr_exists else None

    # client_id
    if client_id_exists:
        mock_request.oauth.client.client_id = "test_client_id"
    else:
        mock_request.oauth = None

    # parent_id
    expected_parent_id = None
    if parent_id_exists:
        log_record = UserActivityLog(
            date=datetime.now(), user_id=users[0]["id"], community_id=None,
            parent_id=None, log={"operation": "test"}, remarks="test")
        db.session.add(log_record)
        db.session.commit()
        expected_parent_id = log_record.id

    # target
    expected_operation = "ITEM_BULK_CREATE"
    expected_target_key = None
    if target_exists:
        expected_operation = "ITEM_CREATE"
        expected_target_key = 2

    # remarks
    expected_remarks = None
    if remarks_exists:
        expected_remarks = "test"

    # community_id and path
    community_id = communities[0].id
    if source_exists:
        if community_id_exists:
            mock_request.path = f"https://test_server/c/{community_id}/item/2"
        else:
            mock_request.path = "https://test_server/item/2"
    else:
        mock_request.path = None

    UserActivityLogger.info(
        operation=expected_operation, parent_id=expected_parent_id,
        target_key=expected_target_key, remarks=expected_remarks,)

    assert len(caplog.records) == 1

    records = UserActivityLog.query.all()
    if not user_exists:
        assert len(records) == 3
    elif parent_id_exists:
        assert len(records) == 2
    else:
        assert len(records) == 1



# .tox/c1/bin/pytest --cov=weko_logging tests/test_activity_logger.py::test_log_info_invalid_case -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_log_info_invalid_case(app, client, db, users, caplog, mocker):
    """
    Test error handler.

    :param app: Flask application.
    """

    caplog.set_level(logging.INFO)

    # user_id
    mock_current_user = mocker.patch("weko_logging.handler.current_user")

    login_user_via_session(client=client, email=users[0]['email'])
    mock_current_user.is_authenticated = True
    mock_current_user.id = users[0]["id"]
    mock_current_user.shib_weko_user = []

    mock_request = mocker.patch("weko_logging.handler.request")
    mock_request.headers.getlist.return_value = None

    # ip address
    mock_request.remote_addr = "123.456.789.001"

    # client_id
    mock_request.oauth = None

    # parent_id
    expected_parent_id = None

    # target
    expected_target_key = 2

    # community_id and path
    mock_request.path = "https://test_server/item/2"

    # Test Case 1: invalid operation
    with pytest.raises(ValueError) as excinfo:
        UserActivityLogger.info(
            operation="INVALID_OPERATION", parent_id=expected_parent_id,
            target_key=expected_target_key)
        assert "Invalid operation: INVALID_OPERATION" in str(excinfo.value)

    # Test Case 2: target is null and target_key is not null
    with pytest.raises(ValueError) as excinfo:
        UserActivityLogger.info(
            operation="ITEM_BULK_CREATE", parent_id=expected_parent_id,
            target_key=expected_target_key)
        assert "target is None and target_key is not None" in str(excinfo.value)

    # Test Case 3: target is not null and target_key is null
    with pytest.raises(ValueError) as excinfo:
        UserActivityLogger.info(
            operation="ITEM_CREATE", parent_id=expected_parent_id,
            target_key=None)
        assert "target is None and target_key is not None" in str(excinfo.value)


# .tox/c1/bin/pytest --cov=weko_logging tests/test_activity_logger.py::test_log_other -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_log_other(app, client, db, users, caplog, mocker):
    """
    Test error handler.

    :param app: Flask application.
    """

    caplog.set_level(logging.INFO)

    # user_id
    mock_current_user = mocker.patch("weko_logging.handler.current_user")

    login_user_via_session(client=client, email=users[0]['email'])
    mock_current_user.is_authenticated = True
    mock_current_user.id = users[0]["id"]
    mock_current_user.shib_weko_user = []

    mock_request = mocker.patch("weko_logging.handler.request")
    mock_request.headers.getlist.return_value = None

    # ip address
    mock_request.remote_addr = "123.456.789.001"

    # client_id
    mock_request.oauth = None

    # parent_id
    expected_parent_id = None

    # target
    expected_target_key = 2

    # community_id and path
    mock_request.path = "https://test_server/item/2"

    # Test Case 1: get ip address from header (X-Forwarded-For)
    mock_request.headers.getlist.return_value = ["123.456.789.001"]

    UserActivityLogger.error(
        operation="ITEM_CREATE", parent_id=expected_parent_id,
        target_key=expected_target_key)

    assert len(caplog.records) == 1
    records = UserActivityLog.query.all()
    assert len(records) == 1

    # Test Case 2: raised exception when db.flush
    mock_flush = mocker.patch("weko_logging.handler.db.session.flush")
    mock_flush.side_effect = Exception("Flush error")
    with pytest.raises(Exception) as excinfo:
        UserActivityLogger.error(
            operation="ITEM_CREATE", parent_id=expected_parent_id,
            target_key=expected_target_key)
        assert "Flush error" in str(excinfo.value)


# def get_next_parent_id(cls):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_activity_logger.py::test_get_next_parent_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_get_next_parent_id(app, db, users):
    """
    Test get next parent id.

    :param app: Flask application.
    """
    class MockSession:
        def __init__(self):
            self.id = {"user_activity_logs_id_seq":1}
        def execute(self, sequence):
            name = sequence.name
            self.id[name] += 1
            return self.id[name]
    session = MockSession()

    # Test Case 1: When the parent_id is None
    parent_id = UserActivityLogger.get_next_parent_id(session)
    assert parent_id == 2
