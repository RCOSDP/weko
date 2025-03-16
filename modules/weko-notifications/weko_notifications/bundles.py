# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-notifications."""

from flask_assets import Bundle


notifications_settings_css = Bundle(
    "css/weko_notifications/notifications.settings.css",
    output="gen/notifications_settings.%(version)s.css"
)
