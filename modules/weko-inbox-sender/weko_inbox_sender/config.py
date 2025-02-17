# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Inbox-Sender is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-inbox-sender."""

INBOX_VERIFY_TLS_CERTIFICATE = False
""" If True, verify the server’s TLS certificate """

NGINX_PORT = '443'

NGINX_HOST = 'nginx:' + NGINX_PORT

INBOX_URL = 'https://' + NGINX_HOST + '/inbox'
# nginxのIPに合わせる
