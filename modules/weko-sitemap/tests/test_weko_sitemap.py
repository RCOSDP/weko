# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-sitemap is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask

from weko_sitemap import WekoSitemap


def test_version():
    """Test version import."""
    from weko_sitemap import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoSitemap(app)
    assert 'weko-sitemap' in app.extensions

    app = Flask('testapp')
    ext = WekoSitemap()
    assert 'weko-sitemap' not in app.extensions
    ext.init_app(app)
    assert 'weko-sitemap' in app.extensions
