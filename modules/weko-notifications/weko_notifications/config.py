# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-notifications."""

WEKO_NOTIFICATIONS = True
"""Enable or disable module extensions."""

WEKO_NOTIFICATIONS_TEMPLATE = "weko_notifications/settings/notifications.html"
"""Default base template for the demo page."""

WEKO_NOTIFICATIONS_BASE_TEMPLATE = None
"""Base templates for user profile module."""

WEKO_NOTIFICATIONS_SETTINGS_TEMPLATE = None
"""Settings base templates for user profile module."""

WEKO_NOTIFICATIONS_INBOX_ADDRESS = "http://inbox:8080"
"""Address of the inbox."""

WEKO_NOTIFICATIONS_INBOX_ENDPOINT = "/inbox"
"""Endpoint of the inbox."""

COAR_NOTIFY_CONTEXT = [
    "https://www.w3.org/ns/activitystreams",
    "https://coar-notify.net"
]
"""COAR-Notify context."""

WEKO_NOTIFICATIONS_PUSH_TEMPLATE_PATH = ""
"""Path to the push template."""
