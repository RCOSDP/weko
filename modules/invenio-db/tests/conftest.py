# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os, sys
import shutil
import tempfile
import pytest
from flask import Flask
from flask.cli import ScriptInfo
from mock import patch
from os.path import dirname, join
from pkg_resources import EntryPoint
from werkzeug.utils import import_string
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

sys.path.append(os.path.dirname(__file__))


def _remove_sqlite_listeners():
    """Remove SQLite specific event listeners from Engine class."""
    from invenio_db.shared import do_sqlite_connect, do_sqlite_begin
    if event.contains(Engine, 'connect', do_sqlite_connect):
        event.remove(Engine, 'connect', do_sqlite_connect)
    if event.contains(Engine, 'begin', do_sqlite_begin):
        event.remove(Engine, 'begin', do_sqlite_begin)


def _safe_sqlite_connect(dbapi_connection, connection_record):
    """Safe version of do_sqlite_connect that only executes PRAGMA for SQLite."""
    # Check if this is actually a SQLite connection
    connection_class_name = type(dbapi_connection).__module__
    if 'sqlite' in connection_class_name.lower():
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()


def _safe_sqlite_begin(dbapi_connection):
    """Safe version of do_sqlite_begin that only executes BEGIN for SQLite."""
    connection_class_name = type(dbapi_connection).__module__
    if 'sqlite' in connection_class_name.lower():
        dbapi_connection.execute('BEGIN')


@pytest.fixture(autouse=True, scope='function')
def cleanup_sqlite_listeners():
    """Cleanup SQLite listeners and replace with safe versions for PostgreSQL."""
    import invenio_db.shared as shared_module
    _remove_sqlite_listeners()
    # Patch the functions to be safe for non-SQLite connections
    original_connect = shared_module.do_sqlite_connect
    original_begin = shared_module.do_sqlite_begin
    shared_module.do_sqlite_connect = _safe_sqlite_connect
    shared_module.do_sqlite_begin = _safe_sqlite_begin
    yield
    _remove_sqlite_listeners()
    shared_module.do_sqlite_connect = original_connect
    shared_module.do_sqlite_begin = original_begin


@pytest.yield_fixture()
def db(app):
    import invenio_db
    from invenio_db import shared
    # Remove SQLite-specific event listeners that would fail on PostgreSQL
    _remove_sqlite_listeners()
    db = invenio_db.db = shared.db = shared.SQLAlchemy(
        metadata=shared.MetaData(naming_convention=shared.NAMING_CONVENTION)
    )
    db.init_app(app)
    # Remove listeners again after init_app as it may re-register them
    _remove_sqlite_listeners()
    database_url = str(db.engine.url)
    db.session.remove()
    db.engine.dispose()
    # Remove listeners before database_exists as it creates a new engine
    _remove_sqlite_listeners()
    if database_exists(database_url):
        _remove_sqlite_listeners()
        drop_database(database_url)
    _remove_sqlite_listeners()
    create_database(database_url)

    yield db
    db.session.remove()
    db.engine.dispose()
    _remove_sqlite_listeners()
    if database_exists(database_url):
        _remove_sqlite_listeners()
        drop_database(database_url)
    # os.remove(join(dirname(__file__),"../test.db"))


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)

@pytest.fixture()
def base_app(instance_path):
    app_ = Flask(
        "testapp",
        instance_path=instance_path
    )
    app_.config.update(
        SECRET_KEY="SECRET_KEY",
        TESTING=True,
        SERVER_NAME="test_server",
        DB_VERSIONING=False,
        DB_VERSIONING_USER_MODEL=None,
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI','sqlite:///test.db')
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
    )
    
    #InvenioDB(app_)
    
    return app_

@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app

@pytest.fixture()
def script_info(app):
    """Get ScriptInfo object for testing CLI."""
    return ScriptInfo(create_app=lambda info: app)

class MockEntryPoint(EntryPoint):
    """Mocking of entrypoint."""

    def load(self):
        """Mock load entry point."""
        if self.name == 'importfail':
            raise ImportError()
        else:
            return import_string(self.name)
def _mock_entry_points(name):
    data = {
        'invenio_db.models': [MockEntryPoint('demo.child', 'demo.child'),
                              MockEntryPoint('demo.parent', 'demo.parent')],
        'invenio_db.models_a': [
            MockEntryPoint('demo.versioned_a', 'demo.versioned_a'),
        ],
        'invenio_db.models_b': [
            MockEntryPoint('demo.versioned_b', 'demo.versioned_b'),
        ],
    }
    names = data.keys() if name is None else [name]
    for key in names:
        for entry_point in data.get(key, []):
            yield entry_point

@pytest.yield_fixture()
def mock_entry_points():
    with patch("pkg_resources.iter_entry_points",_mock_entry_points):
        yield
    
    modules = ["demo", "demo.child", "demo.parent", "demo.versioned_a","demo.versioned_b"]
    for module in modules:
        if module in sys.modules:
            del sys.modules[module]
