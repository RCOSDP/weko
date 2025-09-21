# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import json
import pytest
from unittest.mock import MagicMock, patch

from datetime import datetime
import pytz
from marshmallow import ValidationError

from weko_notifications.notifications import Notification
from weko_notifications.utils import (
    _get_params_for_registrant, inbox_url, notify_item_deleted, notify_item_imported,
    rfc3339, create_subscription, create_userprofile, get_push_template, user_uri,
    get_item_title
    )

# .tox/c1/bin/pytest --cov=weko_notifications tests/test_utils.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace

# def inbox_url():
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_utils.py::test_inbox_url -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_inbox_url(app):
    assert inbox_url() == "http://inbox:8080/inbox"
    assert inbox_url(_external=True) == f"{app.config['THEME_SITEURL']}/inbox"

    assert inbox_url(endpoint="/test") == "http://inbox:8080/test"
    assert inbox_url(endpoint="/test", _external=True) == f"{app.config['THEME_SITEURL']}/test"


# def user_uri():
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_utils.py::test_user_uri -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_user_uri(app, user_profiles):
    user_id = user_profiles[0].user_id
    assert user_uri(user_id) == f"{app.config['WEKO_NOTIFICATIONS_USERS_URI'].format(user_id=user_id)}"
    assert user_uri(user_id, _external=True) == f"{app.config['THEME_SITEURL']}/users/{user_id}"

# def rfc3339():
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_utils.py::test_rfc3339 -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_rfc3339():
    # Test default timezone (Asia/Tokyo)
    default_tz = pytz.timezone("Asia/Tokyo")
    default_time = datetime.now(default_tz).isoformat(timespec="seconds").replace("+00:00", "Z")
    assert rfc3339() == default_time

    # Test specific timezone (UTC)
    utc_tz = pytz.timezone("UTC")
    utc_time = datetime.now(utc_tz).isoformat(timespec="seconds").replace("+00:00", "Z")
    assert rfc3339("UTC") == utc_time


# def create_subscription(user_id, endpoint, expiration_time, p256dh, auth):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_utils.py::test_create_subscription -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_create_subscription(app, client):
    user_id = 1
    endpoint = "https://example.com/endpoint"
    expiration_time = "2025-12-31T23:59:59Z"
    p256dh = "test_p256dh_key"
    auth = "test_auth_key"

    root_url = client.application.config["THEME_SITEURL"]
    with app.test_request_context():
        subscription = create_subscription(user_id, endpoint, expiration_time, p256dh, auth)

    assert subscription["target"] == f"{root_url}/users/{user_id}"
    assert subscription["endpoint"] == endpoint
    assert subscription["expirationTime"] == expiration_time
    assert subscription["keys"]["p256dh"] == p256dh
    assert subscription["keys"]["auth"] == auth


# def create_userprofile(userprofile):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_utils.py::test_create_userprofile -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_create_userprofile(app, user_profiles, client, mocker):

    root_url = client.application.config["THEME_SITEURL"]
    with app.test_request_context():
        userprofile = create_userprofile(user_profiles[0])

    assert userprofile["uri"] == f"{root_url}/users/{user_profiles[0].user_id}"
    assert userprofile["displayname"] == user_profiles[0]._displayname
    assert userprofile["language"] == user_profiles[0].language
    assert userprofile["timezone"] == "GMT+9:00"


def test_get_push_template(app, mocker):
    # Mock the template path in the app config
    mock_template_path = "/mock/path/to/template.json"
    app.config["WEKO_NOTIFICATIONS_PUSH_TEMPLATE_PATH"] = mock_template_path

    # Mock the logger
    mock_logger = mocker.patch("flask.current_app.logger")

    with patch("flask.current_app.logger") as mock_logger:
    # Template file does not exist
        mocker.patch("os.path.isfile", return_value=False)
        assert get_push_template() is None
        mock_logger.error.assert_called_with(
            "Push template path is not set or file does not exist: {}".format(mock_template_path)
        )

    with patch("flask.current_app.logger") as mock_logger:
    # Template file exists but contains invalid JSON
        mocker.patch("os.path.isfile", return_value=True)
        mocker.patch("builtins.open", mocker.mock_open(read_data="invalid json"))
        mocker.patch("json.load", side_effect=TypeError("Invalid JSON"))
        with pytest.raises(TypeError):
            get_push_template()

    with patch("flask.current_app.logger") as mock_logger:
    # Template file exists but contains invalid JSON
        mocker.patch("os.path.isfile", return_value=True)
        mocker.patch("builtins.open", mocker.mock_open(read_data=[{"test": "not dict"}]))
        mocker.patch("json.load", return_value=[{"test": "not dict"}])

        assert get_push_template() is None


    # Template file exists and contains valid JSON
    valid_template = {
        "template1": {
            "name": "Template 1",
            "description": "Description 1",
            "type": "type1",
            "templates": {
                "en": {"title": "Title 1", "body": "Body 1"},
                "ja": {"title": "タイトル1", "body": "本文1"},
            },
        }
    }

    mocker.patch("os.path.isfile", return_value=True)
    mocker.patch("builtins.open", mocker.mock_open(read_data=json.dumps(valid_template)))
    mocker.patch("json.load", return_value=valid_template)
    templates = get_push_template()
    assert templates == [
        {
            "name": "Template 1",
            "description": "Description 1",
            "type": "type1",
            "language": "en",
            "title": "Title 1",
            "body": "Body 1",
        },
        {
            "name": "Template 1",
            "description": "Description 1",
            "type": "type1",
            "language": "ja",
            "title": "タイトル1",
            "body": "本文1",
        },
    ]


# def _get_params_for_registrant(target_id, actor_id, shared_id):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_utils.py::test__get_params_for_registrant -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test__get_params_for_registrant():
    # Test with shared_id == -1
    target_id = 1
    actor_id = 2
    shared_id = -1
    with patch("weko_notifications.utils.UserProfile.get_by_userid") as mock_get_params:
        mock_get_params.return_value = MagicMock()
        mock_get_params.return_value.username = "Test User"
        set_target_id, actor_name = _get_params_for_registrant(target_id, actor_id, shared_id)
        assert set_target_id == {target_id}
        assert actor_name == "Test User"

    # Test with shared_id != -1
        shared_id = 3
    # with patch("weko_notifications.utils.UserProfile.get_by_userid") as mock_get_params:
    #     mock_get_params.return_value = MagicMock()
    #     mock_get_params.return_value.username = "Test User"
        set_target_id, actor_name = _get_params_for_registrant(target_id, actor_id, shared_id)
        assert set_target_id == {target_id, shared_id}
        assert actor_name == "Test User"


# def get_item_title(recid):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_utils.py::test_get_item_title -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_get_item_title(app, mocker):
    recid = 12345
    object_title = "Test Item Title"

    mock_pid = MagicMock()
    mock_pid.object_uuid = "uuid-1234"

    mocker.patch("weko_notifications.utils.PersistentIdentifier.get", return_value=mock_pid)
    mock_deposit = MagicMock()
    mock_deposit.get.return_value = object_title
    mocker.patch("weko_notifications.utils.WekoDeposit.get_record", return_value=mock_deposit)

    title = get_item_title(recid)
    assert title == object_title

    # Test exception handling
    mocker.patch("weko_notifications.utils.PersistentIdentifier.get", side_effect=Exception("Test Exception"))
    mock_logger = mocker.patch("flask.current_app.logger")
    title = get_item_title(recid)
    assert title is None
    mock_logger.error.assert_called_with("Failed to get item title from recid: {}".format(recid))


# def notify_item_imported(target_id, recid, actor_id, object_name=None, shared_id=-1):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_utils.py::test_notify_item_imported -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_notify_item_imported(app, mocker):
    target_id = 1
    recid = 12345
    actor_id = 2
    object_name = "Test Object"
    shared_ids = []

    mocker.patch("weko_notifications.utils._get_params_for_registrant", return_value=({target_id}, "Test User"))
    mocker.patch("weko_notifications.notifications.Notification.send")

    mock_create_notification = mocker.patch("weko_notifications.notifications.Notification.create_item_registered", side_effect=Notification.create_item_registered)
    notify_item_imported(target_id, recid, actor_id, object_name, shared_ids)

    mock_create_notification.assert_called_once_with(target_id, recid, actor_id, actor_name="Test User", object_name=object_name)

    mock_create_notification.reset_mock()

    mock_create_notification.side_effect = ValidationError("Validation error")
    mock_logger = mocker.patch("flask.current_app.logger")
    notify_item_imported(target_id, recid, actor_id, object_name, shared_ids=[3])

    mock_create_notification.assert_called_once_with(target_id, recid, actor_id, actor_name="Test User", object_name=object_name)
    mock_logger.error.assert_called_with("Failed to send notification for item import.")

    mock_create_notification.reset_mock()

    mock_create_notification.side_effect = Exception("Unexpected error")
    mock_logger = mocker.patch("flask.current_app.logger")
    notify_item_imported(target_id, recid, actor_id, object_name, shared_ids=[3])
    mock_create_notification.assert_called_once_with(target_id, recid, actor_id, actor_name="Test User", object_name=object_name)
    mock_logger.error.assert_called_with("Unexpected error occurred while sending notification for item import.")

    # object_name is None
    mock_create_notification.reset_mock()
    mock_get_item_title = mocker.patch("weko_notifications.utils.get_item_title", return_value="Fetched Title")
    notify_item_imported(target_id, recid, actor_id, object_name=None, shared_ids=shared_ids)
    mock_get_item_title.assert_called_once_with(recid)
    mock_create_notification.assert_called_once_with(target_id, recid, actor_id, actor_name="Test User", object_name="Fetched Title")


# def notify_item_deleted(target_id, recid, actor_id, object_name=None, shared_id=-1):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_utils.py::test_notify_item_deleted -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_notify_item_deleted(app, mocker):
    target_id = 1
    recid = 12345
    actor_id = 2
    object_name = "Test Object"
    shared_ids = []

    mocker.patch("weko_notifications.utils._get_params_for_registrant", return_value=({target_id}, "Test User"))
    mocker.patch("weko_notifications.notifications.Notification.send")

    mock_create_notification = mocker.patch("weko_notifications.notifications.Notification.create_item_deleted", side_effect=Notification.create_item_deleted)
    notify_item_deleted(target_id, recid, actor_id, object_name, shared_ids)

    mock_create_notification.assert_called_once_with(target_id, recid, actor_id, actor_name="Test User", object_name=object_name)

    mock_create_notification.reset_mock()

    mock_create_notification.side_effect = ValidationError("Validation error")
    mock_logger = mocker.patch("flask.current_app.logger")
    notify_item_deleted(target_id, recid, actor_id, object_name, shared_ids=[3])

    mock_create_notification.assert_called_once_with(target_id, recid, actor_id, actor_name="Test User", object_name=object_name)
    mock_logger.error.assert_called_with("Failed to send notification for item deletion.")

    mock_create_notification.reset_mock()

    mock_create_notification.side_effect = Exception("Unexpected error")
    mock_logger = mocker.patch("flask.current_app.logger")
    notify_item_deleted(target_id, recid, actor_id, object_name, shared_ids=[3])
    mock_create_notification.assert_called_once_with(target_id, recid, actor_id, actor_name="Test User", object_name=object_name)
    mock_logger.error.assert_called_with("Unexpected error occurred while sending notification for item deletion.")

    # object_name is None
    mock_create_notification.reset_mock()
    mock_get_item_title = mocker.patch("weko_notifications.utils.get_item_title", return_value="Fetched Title")
    notify_item_deleted(target_id, recid, actor_id, object_name=None, shared_ids=shared_ids)
    mock_get_item_title.assert_called_once_with(recid)
    mock_create_notification.assert_called_once_with(target_id, recid, actor_id, actor_name="Test User", object_name="Fetched Title")
