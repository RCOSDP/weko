# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-notifications."""

import pytz
from datetime import datetime


def rfc3339(timezone=None):
    """Return the current time in RFC3339 format.

    Args:
        timezone (str | None):
            The timezone to use. Defaults to "Asia/Tokyo".
    """
    tz = pytz.timezone(timezone or "Asia/Tokyo")
    now = datetime.now(tz).replace(microsecond=0).isoformat()
    if now.endswith('+00:00'):
        now = now[:-6] + 'Z'
    return now
