# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-notifications."""

import pytz
from datetime import datetime

from flask import current_app

def inbox_url(_external=False):
    """Return the inbox URL.

    Args:
        _external (bool): Whether to return the URL with the full domain.
    """
    address = (
        current_app.config["THEME_SITEURL"]
        if _external
        else current_app.config["WEKO_NOTIFICATIONS_INBOX_ADDRESS"]
    )

    return address + current_app.config["WEKO_NOTIFICATIONS_INBOX_ENDPOINT"]


def rfc3339(timezone=None):
    """Return the current time in RFC3339 format.

    Args:
        timezone (str | None):
            The timezone to use. Defaults to "Asia/Tokyo".
    """
    tz = pytz.timezone(timezone or "Asia/Tokyo")
    return datetime.now(tz).isoformat(timespec="seconds").replace("+00:00", "Z")
