# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-notifications."""

from __future__ import absolute_import, print_function

from .client import NotificationClient
from .ext import WekoNotifications
from .notifications import Notification
from .version import __version__

__all__ = ('__version__', 'WekoNotifications')
