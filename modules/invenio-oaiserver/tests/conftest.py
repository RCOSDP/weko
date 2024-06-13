# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

import os
import shutil
import tempfile

import pytest
from flask import Flask
from flask_celeryext import FlaskCeleryExt
from helpers import load_records, remove_records
from invenio_db import InvenioDB, db
from invenio_i18n import InvenioI18N
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch
from invenio_search.engine import SearchEngine
from sqlalchemy_utils.functions import create_database, database_exists, drop_database

from invenio_oaiserver import InvenioOAIServer
from invenio_oaiserver.views.server import blueprint


@pytest.yield_fixture
def app():
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    app = Flask("testapp", instance_path=instance_path)
    app.config.update(
        CELERY_ALWAYS_EAGER=True,
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        CELERY_RESULT_BACKEND="cache",
        JSONSCHEMAS_HOST="inveniosoftware.org",
        TESTING=True,
        SECRET_KEY="CHANGE_ME",
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SERVER_NAME="app",
        OAISERVER_ID_PREFIX="oai:inveniosoftware.org:recid/",
        OAISERVER_QUERY_PARSER_FIELDS=["title_statement"],
        OAISERVER_RECORD_INDEX="_all",
        OAISERVER_REGISTER_SET_SIGNALS=True,
    )
    if not hasattr(app, "cli"):
        from flask_cli import FlaskCLI

        FlaskCLI(app)

    InvenioDB(app)
    FlaskCeleryExt(app)
    InvenioJSONSchemas(app)
    InvenioRecords(app)
    InvenioPIDStore(app)
    client = SearchEngine(hosts=["localhost"])
    search = InvenioSearch(app, client=client)
    search.register_mappings("records", "data")
    InvenioIndexer(app)
    InvenioOAIServer(app)
    InvenioI18N(app)

    app.register_blueprint(blueprint)

    with app.app_context():
        if str(db.engine.url) != "sqlite://" and not database_exists(
            str(db.engine.url)
        ):
            create_database(str(db.engine.url))
        db.create_all()
        list(search.delete(ignore=[404]))
        list(search.create())
        search.flush_and_refresh("_all")

    with app.app_context():
        yield app

    with app.app_context():
        db.session.close()
        if str(db.engine.url) != "sqlite://":
            drop_database(str(db.engine.url))
        list(search.delete(ignore=[404]))
        search.client.indices.delete("*-percolators")
    shutil.rmtree(instance_path)


@pytest.yield_fixture
def authority_data(app):
    """Test indexation using authority data."""
    schema = "http://localhost:5000/marc21/authority/ad-v1.0.0.json"
    with app.test_request_context():
        records = load_records(
            app=app, filename="data/marc21/authority.xml", schema=schema
        )
    yield records
    with app.test_request_context():
        remove_records(app, records)


@pytest.yield_fixture
def bibliographic_data(app):
    """Test indexation using bibliographic data."""
    schema = "http://localhost:5000/marc21/bibliographic/bd-v1.0.0.json"
    with app.test_request_context():
        records = load_records(
            app=app, filename="data/marc21/bibliographic.xml", schema=schema
        )
    yield records
    with app.test_request_context():
        remove_records(app, records)


@pytest.yield_fixture
def without_oaiset_signals(app):
    """Temporary disable oaiset signals."""
    from invenio_oaiserver import current_oaiserver

    current_oaiserver.unregister_signals_oaiset()
    yield
    current_oaiserver.register_signals_oaiset()


@pytest.fixture
def schema():
    """Get record schema."""
    return {
        "allOf": [
            {
                "type": "object",
                "properties": {
                    "title_statement": {
                        "type": "object",
                        "properties": {"title": {"type": "string"}},
                    },
                    "genre": {"type": "string"},
                },
            },
            {
                "$ref": "http://inveniosoftware.org/schemas/"
                "oaiserver/internal-v1.1.0.json",
            },
        ]
    }
