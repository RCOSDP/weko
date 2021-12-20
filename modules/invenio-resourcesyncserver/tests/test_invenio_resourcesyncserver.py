# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# INVENIO-ResourceSyncServer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask

from invenio_resourcesyncserver import InvenioResourceSyncServer


def test_version():
    """Test version import."""
    from invenio_resourcesyncserver import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = InvenioResourceSyncServer(app)
    assert 'invenio-resourcesyncserver' in app.extensions

    app = Flask('testapp')
    ext = InvenioResourceSyncServer()
    assert 'invenio-resourcesyncserver' not in app.extensions
    ext.init_app(app)
    assert 'invenio-resourcesyncserver' in app.extensions
