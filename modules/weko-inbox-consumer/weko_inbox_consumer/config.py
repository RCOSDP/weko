# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Inbox-Consumer is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-inbox-consumer."""

WEKO_INBOX_CONSUMER_DEFAULT_VALUE = 'foobar'
"""Default value for the application."""

WEKO_INBOX_CONSUMER_BASE_TEMPLATE = 'weko_inbox_consumer/base.html'
"""Default base template for the demo page."""

WEKO_INBOX_CHECK_BUTTON_TEMPLATE = \
    'weko_inbox_consumer/inbox_check_button.html'

WEKO_INBOX_CONSUMER_SETTING_TEMPLATE = \
    'weko_inbox_consumer/setting/checkinterval.html'

WEKO_CHECK_INBOX_INTERVAL = 120000

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

DEFAULT_NOTIFY_RETENTION_DAYS = 7

INBOX_VERIFY_TLS_CERTIFICATE = False
""" If True, verify the server’s TLS certificate """
