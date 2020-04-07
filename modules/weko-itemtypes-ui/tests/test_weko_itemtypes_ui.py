# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from flask import Flask

from weko_itemtypes_ui import WekoItemtypesUI


def test_version():
    """Test version import."""
    from weko_itemtypes_ui import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoItemtypesUI(app)
    assert 'weko-itemtypes-ui' in app.extensions

    app = Flask('testapp')
    ext = WekoItemtypesUI()
    assert 'weko-itemtypes-ui' not in app.extensions
    ext.init_app(app)
    assert 'weko-itemtypes-ui' in app.extensions


def test_view(app):
    """Test view."""
    WekoItemtypesUI(app)
    with app.test_client() as client:
        res = client.post("/itemtypes/mapping", data={})
        assert res.status_code == 200
        assert 'Header Error' in str(res.data)
