# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from flask import Flask

from weko_theme import WekoTheme


def test_version():
    """Test version import."""
    from weko_theme import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoTheme(app)
    assert 'weko-theme' in app.extensions

    app = Flask('testapp')
    ext = WekoTheme()
    assert 'weko-theme' not in app.extensions
    ext.init_app(app)
    assert 'weko-theme' in app.extensions


def test_view(app):
    """Test view."""
    WekoTheme(app)
    with app.test_client() as client:
        res = client.get("/")
        assert res.status_code == 200
        assert 'Welcome to weko-theme' in str(res.data)
