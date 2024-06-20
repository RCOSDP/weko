# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Fix compatibility with werkzeug due to flask_oauthlib imports."""

import sys

import werkzeug


def monkey_patch_werkzeug_contrib():
    """Patch missing module."""
    try:
        from werkzeug import contrib
    except ImportError:
        import cachelib

        sys.modules["werkzeug.contrib.cache"] = cachelib


def monkey_patch_werkzeug_base():
    """Patch top level removed modules."""
    try:
        from werkzeug import cached_property
    except ImportError:
        werkzeug.cached_property = werkzeug.utils.cached_property
        werkzeug.parse_options_header = werkzeug.http.parse_options_header
        werkzeug.url_quote = werkzeug.urls.url_quote
        werkzeug.url_decode = werkzeug.urls.url_decode
        werkzeug.url_encode = werkzeug.urls.url_encode


def monkey_patch_werkzeug():
    """Patch all the missing werkzeug modules."""
    monkey_patch_werkzeug_base()
    monkey_patch_werkzeug_contrib()
