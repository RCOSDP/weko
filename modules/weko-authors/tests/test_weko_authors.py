# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from flask import Flask

from weko_authors import WekoAuthors


def test_version():
    """Test version import."""
    from weko_authors import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoAuthors(app)
    assert 'weko-authors' in app.extensions

    app = Flask('testapp')
    ext = WekoAuthors()
    assert 'weko-authors' not in app.extensions
    ext.init_app(app)
    assert 'weko-authors' in app.extensions


def bak_test_view(app):
    """Test view."""
    WekoAuthors(app)
    with app.test_client() as client:
        res = client.get("/")
        assert res.status_code == 200
        assert 'Welcome to weko-authors' in str(res.data)
