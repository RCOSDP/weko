# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# INVENIO-ResourceSyncClient is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask, url_for

from invenio_resourcesyncclient import INVENIOResourceSyncClient


def test_version():
    """Test version import."""
    from invenio_resourcesyncclient import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = INVENIOResourceSyncClient(app)
    assert 'invenio-resourcesyncclient' in app.extensions

    app = Flask('testapp')
    ext = INVENIOResourceSyncClient()
    assert 'invenio-resourcesyncclient' not in app.extensions
    ext.init_app(app)
    assert 'invenio-resourcesyncclient' in app.extensions


def test_view(app, db, client):
    """Test view."""
    res = client.get('/resync/')
    assert res.status_code == 404
