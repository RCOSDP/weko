# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from flask import Flask

from weko_items_ui import WekoItemsUI


def test_version():
    """Test version import."""
    from weko_items_ui import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoItemsUI(app)
    assert 'weko-items-ui' in app.extensions

    app = Flask('testapp')
    ext = WekoItemsUI()
    assert 'weko-items-ui' not in app.extensions
    ext.init_app(app)
    assert 'weko-items-ui' in app.extensions


def test_view(app):
    """Test view."""
    WekoItemsUI(app)
    with app.test_client() as client:
        res = client.get("/items/jsonschema/0")
        assert res.status_code == 200
        res = client.get("/items/schemaform/0")
        assert res.status_code == 200
