# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Items-Autofill is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-items-autofill."""

from flask_babelex import gettext as _

WEKO_ITEMS_AUTOFILL_DEFAULT_VALUE = 'foobar'
"""Default value for the application."""

WEKO_ITEMS_AUTOFILL_BASE_TEMPLATE = 'weko_items_autofill/base.html'
"""Default base template for the demo page."""

WEKO_ITEMS_AUTOFILL_API_UPDATED = True

WEKO_ITEMS_AUTOFILL_ITEMS_AUTOFILL = [
    'title',
    'sourceTitle',
    'language',
    'creator',
    'pageStart',
    'pageEnd',
    'date',
    'publisher',
    'relatedIdentifier'
]
""" Item autofill list """

WEKO_ITEMS_AUTOFILL_CROSSREF_API_URL = 'https://doi.crossref.org'
"""Crossref API URL"""

WEKO_ITEMS_AUTOFILL_CROSSREF_API_PID = ''
"""Crossref API PID"""

WEKO_ITEMS_AUTOFILL_SYS_HTTP_PROXY = ''

WEKO_ITEMS_AUTOFILL_SYS_HTTPS_PROXY = ''

WEKO_ITEMS_AUTOFILL_REQUEST_TIMEOUT = 5
"""Request time out"""

WEKO_ITEMS_AUTOFILL_CROSSREF_RESPONSE_RESULT = [
    'title',
    'language',
    'author',
    'page',
    'published-online',
    'publisher',
    'ISBN'
]

WEKO_ITEMS_AUTOFILL_SELECT_OPTION = {
    'options': [
        {'value': 'Default', 'text': _('Select_the_ID')},
        {'value': 'CrossRef', 'text': 'CrossRef'}
    ]
}
