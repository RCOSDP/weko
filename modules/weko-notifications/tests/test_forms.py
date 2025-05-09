# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

import pytest
from flask_login.utils import login_user

from weko_notifications.forms import handle_notifications_form, NotificationsForm

# .tox/c1/bin/pytest --cov=weko_notifications tests/test_forms.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace

# def handle_notifications_form(form):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_forms.py::test_handle_notifications_form -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_handle_notifications_form(app, db, users, mocker):
    """Test handle_notifications_form."""
    form = {
        "notifications-subscribe_webpush": "",
        "notifications-webpush_endpoint": "",
        "notifications-webpush_expiration_time": "",
        "notifications-webpush_p256dh": "",
        "notifications-webpush_auth": "",
        "notifications-subscribe_email": "y",
    }
    mock_flash = mocker.patch("weko_notifications.forms.flash")
    mock_settings = mocker.patch("weko_notifications.forms.NotificationsUserSettings.create_or_update")
    users[0]["obj"].confirmed_at = "2025-01-01 00:00:00"
    db.session.commit()

    with app.test_request_context(method="POST", data=form):
        notifications_form = NotificationsForm(
            subscribe_webpush=False,
            webpush_endpoint="",
            webpush_expiration_time="",
            webpush_p256dh="",
            webpush_auth="",
            subscribe_email="",
            prefix="notifications"
        )
        notifications_form.subscribe_email.errors = []
        mocker.patch.object(notifications_form, "validate_on_submit", return_value=True)
        login_user(users[0]["obj"])
        handle_notifications_form(notifications_form)

    mock_flash.assert_called_with("Notifications settings updated.", category="success")
    mock_settings.assert_called_with(
        user_id=users[0]["obj"].id,
        subscribe_email=True
    )

    mock_flash.reset_mock()
    mock_settings.reset_mock()

    users[0]["obj"].confirmed_at = None
    db.session.commit()
    with app.test_request_context(method="POST", data=form):
        notifications_form = NotificationsForm(
            subscribe_webpush=False,
            webpush_endpoint="",
            webpush_expiration_time="",
            webpush_p256dh="",
            webpush_auth="",
            subscribe_email="",
            prefix="notifications"
        )
        notifications_form.subscribe_email.errors = []
        mocker.patch.object(notifications_form, "validate_on_submit", return_value=True)
        login_user(users[0]["obj"])
        handle_notifications_form(notifications_form)
    assert notifications_form.subscribe_email.errors == [
        "Email notifications require a confirmed email address."
    ]
    mock_settings.assert_not_called()

    mock_flash.assert_not_called()
    mock_settings.reset_mock()

    with app.test_request_context(method="POST", data=form):
        notifications_form = NotificationsForm(
            subscribe_webpush=False,
            webpush_endpoint="",
            webpush_expiration_time="",
            webpush_p256dh="",
            webpush_auth="",
            subscribe_email="",
            prefix="notifications"
        )
        mocker.patch.object(notifications_form, "validate_on_submit", return_value=False)
        login_user(users[0]["obj"])
        handle_notifications_form(notifications_form)
    mock_settings.assert_not_called()
    mock_flash.assert_called_with(
        "Failed to update your notifications settings.", category="error"
    )
    mock_flash.reset_mock()
    mock_settings.reset_mock()
