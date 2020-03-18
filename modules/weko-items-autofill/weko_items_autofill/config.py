# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Items-Autofill is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-items-autofill."""

WEKO_ITEMS_AUTOFILL_DEFAULT_VALUE = 'foobar'
"""Default value for the application."""

WEKO_ITEMS_AUTOFILL_BASE_TEMPLATE = 'weko_items_autofill/base.html'
"""Default base template for the demo page."""

WEKO_ITEMS_AUTOFILL_API_UPDATED = True

WEKO_ITEMS_AUTOFILL_CROSSREF_API_URL = 'https://doi.crossref.org'
"""Crossref API URL"""

WEKO_ITEMS_AUTOFILL_CiNii_API_URL = 'https://ci.nii.ac.jp'

WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE = 'en'
"""Crossref default language"""

WEKO_ITEMS_AUTOFILL_SYS_HTTP_PROXY = ''
"""HTTP proxy"""

WEKO_ITEMS_AUTOFILL_SYS_HTTPS_PROXY = ''
"""HTTPS proxy"""

WEKO_ITEMS_AUTOFILL_REQUEST_TIMEOUT = 5
"""Request time out"""

WEKO_ITEMS_AUTOFILL_API_CACHE_TIMEOUT = 50

WEKO_ITEMS_AUTOFILL_SELECT_OPTION = [
    {'value': 'CrossRef', 'text': 'CrossRef'},
    {'value': 'CiNii', 'text': 'CiNii'}
]
"""API select option"""

WEKO_ITEMS_AUTOFILL_CROSSREF_REQUIRED_ITEM = [
    "title",
    "creator",
    "contributor",
    "sourceTitle",
    "sourceIdentifier",
    "volume",
    "issue",
    "pageStart",
    "pageEnd",
    "date",
    "relation"
]
"""CrossRef required item"""
WEKO_ITEMS_CROSSREF_REQUIRED_ITEM = [
    "article_title",
    "author",
    "contributor",
    "organization",
    "journal_title",
    "volume",
    "issue",
    "first_page",
    "last_page",
    "year",
    "issn",
    "isbn",
    "doi",
]

WEKO_ITEMS_CROSSREF_CONTRIBUTOR = [
    "editor",
    "chair",
    "translator"
]

WEKO_ITEMS_AUTOFILL_CINII_REQUIRED_ITEM = [
    "title",
    "alternative",
    "creator",
    "contributor",
    "description",
    "subject",
    "sourceTitle",
    "volume",
    "issue",
    "pageStart",
    "pageEnd",
    "numPages",
    "date",
    "publisher",
    "sourceIdentifier",
    "relation"
]
"""CiNii required item"""

WEKO_ITEMS_AUTOFILL_DEFAULT_PAGE_NUMBER = 1
"""Default page number"""
