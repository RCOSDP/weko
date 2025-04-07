# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import json
import pytest
from unittest.mock import patch

from datetime import datetime
import pytz

from weko_notifications.utils import inbox_url, rfc3339, create_subscription, create_userprofile, get_push_template

# .tox/c1/bin/pytest --cov=weko_notifications tests/test_utils.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace

# def inbox_url():
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_utils.py::test_inbox_url -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_inbox_url(app):
    assert inbox_url() == "http://inbox:8080/inbox"
    assert inbox_url(_external=True) == f"{app.config['THEME_SITEURL']}/inbox"

    assert inbox_url("/test") == "http://inbox:8080/test"
    assert inbox_url("/test", _external=True) == f"{app.config['THEME_SITEURL']}/test"


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

    root_url = client.application.config["SERVER_NAME"]
    with app.test_request_context():
        subscription = create_subscription(user_id, endpoint, expiration_time, p256dh, auth)

    assert subscription["target"] == f"http://{root_url}/user/{user_id}"
    assert subscription["endpoint"] == endpoint
    assert subscription["expirationTime"] == expiration_time
    assert subscription["keys"]["p256dh"] == p256dh
    assert subscription["keys"]["auth"] == auth


# def create_userprofile(userprofile):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_utils.py::test_create_userprofile -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_create_userprofile(app, user_profiles, client, mocker):

    root_url = client.application.config["SERVER_NAME"]
    with app.test_request_context():
        userprofile = create_userprofile(user_profiles[0])

    assert userprofile["uri"] == f"http://{root_url}/user/{user_profiles[0].user_id}"
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

