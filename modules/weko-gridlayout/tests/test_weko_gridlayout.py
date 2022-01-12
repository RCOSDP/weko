# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-gridlayout is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask

from weko_gridlayout import WekoGridLayout


def test_version():
    """Test version import."""
    from weko_gridlayout import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoGridLayout(app)
    assert 'weko-gridlayout' in app.extensions

    app = Flask('testapp')
    ext = WekoGridLayout()
    assert 'weko-gridlayout' not in app.extensions
    ext.init_app(app)
    assert 'weko-gridlayout' in app.extensions


# def test_view(base_client):
#     """Test view."""
#     res = base_client.get("/")
#     assert res.status_code == 200
#     assert 'Welcome to weko-gridlayout' in str(res.data)
