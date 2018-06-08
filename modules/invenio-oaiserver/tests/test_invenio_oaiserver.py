# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

import pytest
from flask import Flask
from invenio_db import db

from invenio_oaiserver import InvenioOAIServer, current_oaiserver


def test_version():
    """Test version import."""
    from invenio_oaiserver import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = InvenioOAIServer(app)
    assert 'invenio-oaiserver' in app.extensions

    app = Flask('testapp')
    ext = InvenioOAIServer()
    assert 'invenio-oaiserver' not in app.extensions
    ext.init_app(app)
    assert 'invenio-oaiserver' in app.extensions
    with app.app_context():
        current_oaiserver.unregister_signals()


def test_view(app):
    """Test view."""
    with app.test_client() as client:
        res = client.get("/oai2d?verb=Identify")
        assert res.status_code == 200

        # no XSL transformation by default
        assert b'xml-stylesheet' not in res.data


def test_view_with_xsl(app):
    """Test view."""
    with app.test_client() as client:
        app.config['OAISERVER_XSL_URL'] = 'testdomain.com/oai2.xsl'
        res = client.get("/oai2d?verb=Identify")
        assert res.status_code == 200

        assert b'xml-stylesheet' in res.data


def test_alembic(app):
    """Test alembic recipes."""
    ext = app.extensions['invenio-db']

    if db.engine.name == 'sqlite':
        raise pytest.skip('Upgrades are not supported on SQLite.')

    assert not ext.alembic.compare_metadata()
    db.drop_all()
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()
    ext.alembic.stamp()
    ext.alembic.downgrade(target='96e796392533')
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()
