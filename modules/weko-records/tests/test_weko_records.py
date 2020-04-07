# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from flask import Flask

from weko_records import WekoRecords


def test_version():
    """Test version import."""
    from weko_records import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoRecords(app)
    assert 'weko-records' in app.extensions

    app = Flask('testapp')
    ext = WekoRecords()
    assert 'weko-records' not in app.extensions
    ext.init_app(app)
    assert 'weko-records' in app.extensions
