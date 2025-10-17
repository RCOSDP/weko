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
from sqlalchemy_utils.functions import create_database, database_exists

sys.path.append(os.path.dirname(__file__))


@pytest.yield_fixture()
def db(app):
    import invenio_db
    from invenio_db import shared
    db = invenio_db.db = shared.db = shared.SQLAlchemy(
        metadata=shared.MetaData(naming_convention=shared.NAMING_CONVENTION)
    )
    db.init_app(app)
    if not database_exists(str(db.engine.url)):
        create_database(str(db.engine.url))

    yield db
    db.session.remove()
    db.drop_all()
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