# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from flask import Flask

from weko_index_tree import WekoIndexTree


def test_version():
    """Test version import."""
    from weko_index_tree import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoIndexTree(app)
    assert 'weko-index-tree' in app.extensions

    app = Flask('testapp')
    ext = WekoIndexTree()
    assert 'weko-index-tree' not in app.extensions
    ext.init_app(app)
    assert 'weko-index-tree' in app.extensions


def test_view(app):
    """Test view."""
    WekoIndexTree(app)
    with app.test_client() as client:
        res = client.get("/")
        assert res.status_code == 200
        assert 'Welcome to weko-index-tree' in str(res.data)
