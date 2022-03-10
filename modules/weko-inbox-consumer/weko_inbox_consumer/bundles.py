# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Inbox-Consumer is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

from flask_assets import Bundle


push_notify_js = Bundle(
    'js/check_inbox.js',
    output='gen/inbox_check.%(version)s.js'
)


interval_check_js = Bundle(
    'js/interval_check.js',
    output='get/interval_check.%(version)s.js'
)
