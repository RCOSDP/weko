# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask

from weko_swordserver import WekoSWORDServer


def test_version():
    """Test version import."""
    from weko_swordserver import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoSWORDServer(app)
    assert 'weko-swordserver' in app.extensions

    app = Flask('testapp')
    ext = WekoSWORDServer()
    assert 'weko-swordserver' not in app.extensions
    ext.init_app(app)
    assert 'weko-swordserver' in app.extensions


def test_view(client,sessionlifetime):
    """Test view."""
    res = client.get("/")
    assert res.status_code == 200
    assert 'Welcome to WEKO-SWORDServer' in str(res.data)
