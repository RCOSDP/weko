# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Handle is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask

from weko_handle import WekoHandle


def test_version():
    """Test version import."""
    from weko_handle import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoHandle(app)
    assert 'weko-handle' in app.extensions

    app = Flask('testapp')
    ext = WekoHandle()
    assert 'weko-handle' not in app.extensions
    ext.init_app(app)
    assert 'weko-handle' in app.extensions
