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

from invenio_cache import InvenioCache, current_cache
from invenio_oaiserver import InvenioOAIServer, current_oaiserver
from invenio_oaiserver.ext import _AppState


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


def test_view(app, db):
    """Test view."""
    with app.test_client() as client:
        res = client.get("/oai?verb=Identify")
        assert res.status_code == 200

        # no XSL transformation by default
        assert b'xml-stylesheet' not in res.data

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_invenio_oaiserver.py::test_view_with_xsl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_view_with_xsl(app, db):
    """Test view."""
    with app.test_client() as client:
        app.config['OAISERVER_XSL_URL'] = 'testdomain.com/oai2.xsl'
        res = client.get("/oai?verb=Identify")
        assert res.status_code == 200

        assert b'xml-stylesheet' in res.data


def test_alembic(app, db):
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

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_invenio_oaiserver.py::test_AppState -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_AppState():
    # register signal, exist cache
    app = Flask("test_app")
    app.config.update(CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis",
        OAISERVER_CACHE_KEY="DynamicOAISets::",
        OAISERVER_REGISTER_RECORD_SIGNALS=True,
        OAISERVER_REGISTER_SET_SIGNALS=True)
    InvenioCache(app)
    with app.app_context():
        current_cache.delete("DynamicOAISets::")

        state = _AppState(app=app,cache=current_cache)
        assert state.sets == None
        state.sets = "test_value"
        assert state.sets == "test_value"
        state.unregister_signals()
        
    
    # not register signal, not exist cache
    app = Flask("test_app")
    app.config.update(OAISERVER_REGISTER_RECORD_SIGNALS=False,
        OAISERVER_REGISTER_SET_SIGNALS=False)
    with app.app_context():
        state = _AppState(app=app)
        state.sets="test_value"
        state.unregister_signals()
    
    app = Flask("test_app")
    app.config.update(OAISERVER_REGISTER_RECORD_SIGNALS=True,
        OAISERVER_REGISTER_SET_SIGNALS=False)
    with app.app_context():
        state = _AppState(app=app)