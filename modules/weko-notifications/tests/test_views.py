# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

import json
import pytest
from unittest.mock import patch

import requests
from flask import jsonify, request
from invenio_accounts.testutils import login_user_via_session

from weko_notifications.forms import handle_notifications_form
from weko_notifications.utils import inbox_url
from weko_notifications.views import init_push_templates
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_views.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace

# def init_push_templates():
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_views.py::test_init_push_templates -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_init_push_templates(app, mocker):
    # Mock the get_push_template and requests.post responses
    with patch("weko_notifications.views.get_push_template") as mock_get_templates, \
        patch("weko_notifications.views.requests.post") as mock_post:

        # Test case 1: No templates
        mock_get_templates.return_value = None
        init_push_templates()
        mock_post.assert_not_called()

        # Test case 2: Successfully post templates
        mock_get_templates.return_value = [{"template": "test1"}, {"template": "test2"}]
        init_push_templates()
        assert mock_post.call_count == 2
        mock_post.assert_has_calls([
            mocker.call(inbox_url(endpoint="/push-template"), json={"template": "test1"}),
            mocker.call(inbox_url(endpoint="/push-template"), json={"template": "test2"})
        ])

        mock_post.reset_mock()

        # Test case 3: Request exception
        mock_post.side_effect = requests.RequestException()
        init_push_templates()
        mock_post.assert_called_once()



# def user_settings():
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_views.py::test_user_settings -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_user_settings(app, users, client, mocker):
    mock_flash = mocker.patch("weko_notifications.views.flash")

    # Login user
    login_user_via_session(client=client, email=users[0]["email"])

    # Test GET request
    mocker.patch("weko_notifications.views.render_template", return_value=jsonify(code=200))
    response = client.get("/account/settings/notifications/")
    assert response.status_code == 200

    form = {
        "notifications-subscribe_webpush": "y",
        "notifications-webpush_endpoint": "test_endpoint",
        "notifications-webpush_expiration_time": "",
        "notifications-webpush_p256dh": "",
        "notifications-webpush_auth": "",
        "notifications-subscribe_email": "y",
    }

    # Test POST request - successful subscription
    with patch("weko_notifications.views.handle_notifications_form", side_effect=lambda form: form.process(formdata=request.form)) as mock_handle_form, \
            patch("weko_notifications.views.create_subscription") as mock_create_sub, \
            patch("weko_notifications.views.create_userprofile") as mock_create_profile, \
            patch("weko_notifications.views.requests.post") as mock_post:

        response = client.post("/account/settings/notifications/", data=form)
        assert response.status_code == 200
        mock_handle_form.assert_called_once()
        mock_create_sub.assert_called_once()
        mock_create_profile.assert_called_once()
        assert mock_post.call_count == 2

    # Test POST request - unsuccessful subscription
    with patch("weko_notifications.views.handle_notifications_form", side_effect=lambda form: form.process(formdata=request.form)) as mock_handle_form, \
            patch("weko_notifications.views.inbox_url") as mock_inbox_url, \
            patch("weko_notifications.views.requests.post") as mock_post:

        mock_inbox_url.side_effect = Exception()

        response = client.post("/account/settings/notifications/", data=form)
        assert response.status_code == 200
        mock_inbox_url.assert_called_once_with(endpoint="/subscribe")
        mock_post.assert_not_called()
        mock_flash.assert_called_with("Failed to update push subscription.", category="error")

    form = {
        "notifications-subscribe_webpush": "",
        "notifications-webpush_endpoint": "test_endpoint",
        "notifications-webpush_expiration_time": "",
        "notifications-webpush_p256dh": "",
        "notifications-webpush_auth": "",
        "notifications-subscribe_email": "y",
    }
    # # Test POST request - unsubscribe
    with patch("weko_notifications.views.handle_notifications_form", side_effect=lambda form: form.process(formdata=request.form)) as mock_handle_form, \
            patch("weko_notifications.views.inbox_url") as mock_inbox_url, \
            patch("weko_notifications.views.requests.post") as mock_post:

        response = client.post("/account/settings/notifications/", data=form)
        assert response.status_code == 200
        mock_inbox_url.assert_called_once_with(endpoint="/unsubscribe")
        mock_post.assert_called_once()

    mock_flash.reset_mock()

    with patch("weko_notifications.views.handle_notifications_form", side_effect=Exception()) as mock_handle_form:
        response = client.post("/account/settings/notifications/", data=form)
        assert response.status_code == 200
        mock_handle_form.assert_called_once()
        mock_flash.assert_called_with("Failed to update push subscription.", category="error")

    mock_flash.reset_mock()

    form = {
        "notifications-subscribe_webpush": "y",
        "notifications-webpush_endpoint": "",
        "notifications-webpush_expiration_time": "",
        "notifications-webpush_p256dh": "",
        "notifications-webpush_auth": "",
        "notifications-subscribe_email": "y",
    }
    # Test POST request - missing subscription info
    with patch("weko_notifications.views.handle_notifications_form", side_effect=lambda form: form.process(formdata=request.form)) as mock_handle_form, \
            patch("weko_notifications.views.create_subscription") as mock_create_sub, \
            patch("weko_notifications.views.create_userprofile") as mock_create_profile, \
            patch("weko_notifications.views.NotificationsUserSettings.get_by_user_id") as mock_user_settings:

        response = client.post("/account/settings/notifications/", data=form)
        assert response.status_code == 200
        mock_handle_form.assert_called_once()
        mock_create_sub.assert_not_called()
        mock_create_profile.assert_not_called()
        mock_flash.assert_called_with(
            "Failed to get subscription information. Please try again.",
            category="error"
        )




# def notifications():
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_views.py::test_notifications -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_notifications(app, users, client):
    """Test notifications API endpoint."""

    # Mock NotificationClient


    # Test unauthorized access
    response = client.get("/notifications")
    assert response.status_code == 401, json.dumps(response.get_json())

    # Test authorized access
    login_user_via_session(client=client, email=users[0]["email"])
    mock_notifications = ["notification1", "notification2"]
    with patch("weko_notifications.client.NotificationClient.notifications", return_value=mock_notifications):
        response = client.get("/notifications")

    assert response.status_code == 200, json.dumps(response.get_json())

    data = response.get_json()
    assert data["code"] == 200
    assert data["message"] == "Notifications retrieved successfully."
    assert data["count"] == 2
    assert data["notifications"] == mock_notifications
