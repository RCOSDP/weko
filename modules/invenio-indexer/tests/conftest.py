# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

import os
import shutil
import tempfile

import pytest
from celery.messaging import establish_connection
from flask import Flask
from flask_celeryext import FlaskCeleryExt
from invenio_db import InvenioDB, db
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch
from invenio_search.engine import dsl
from sqlalchemy_utils.functions import create_database, database_exists, drop_database

from invenio_indexer import InvenioIndexer
from kombu import Exchange, Queue
from unittest.mock import patch

@patch.dict('os.environ', {'INVENIO_OPENSEARCH_USER': 'invenio', 'INVENIO_OPENSEARCH_PASSWORD': 'openpass123!'})
@pytest.fixture()
def base_app(request):
    """Base application fixture."""
    instance_path = tempfile.mkdtemp()
    app = Flask("testapp", instance_path=instance_path)
    app.config.update(
        
        BROKER_URL='amqp://guest:guest@172.19.0.4:5672/',
        CELERY_BROKER_URL=os.environ.get(
            "BROKER_URL", "amqp://guest:guest@rabbitmq:5672//"
        ),
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_TASK_EAGER_PROPAGATES=True,
        CELERY_RESULT_BACKEND="cache",
        JSONSCHEMAS_URL_SCHEME='http',
        SECRET_KEY='CHANGE_ME',
        SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
        INDEXER_DEFAULT_INDEX="records-default-v1.0.0",
        INDEXER_MQ_QUEUE = Queue("indexer",
                                 exchange=Exchange("indexer", type="direct"), routing_key="indexer",auto_delete=False,queue_arguments={"x-queue-type":"quorum"}),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        # ),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        SEARCH_ELASTIC_HOSTS=os.environ.get(
                'SEARCH_ELASTIC_HOSTS', 'opensearch'),
        SEARCH_HOSTS=os.environ.get(
            'SEARCH_HOST', 'opensearch'
        ),
        
        SEARCH_CLIENT_CONFIG={"http_auth":("invenio","openpass123!"),"use_ssl":True, "verify_certs":False},
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    FlaskCeleryExt(app)
    InvenioDB(app)
    InvenioRecords(app)
    search = InvenioSearch(app, entry_point_group=None)
    search.register_mappings("records", "tests.data")

    with app.app_context():
        if not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()

    def teardown():
        with app.app_context():
            drop_database(str(db.engine.url))
        shutil.rmtree(instance_path)

    request.addfinalizer(teardown)
    return app


@pytest.fixture()
def app(base_app):
    """Flask application fixture."""
    InvenioIndexer(base_app)
    return base_app


@pytest.fixture()
def queue(app):
    """Get queue object for testing bulk operations."""
    _queue = (app.config['INDEXER_MQ_QUEUE'])

    with app.app_context():
        with establish_connection() as c:
            q = _queue(c)
            q.declare()
            q.purge()

    return _queue


@pytest.fixture(scope="function")
def search_prefix(app):
    """Sets the search prefix."""
    tmp = app.config["SEARCH_INDEX_PREFIX"]
    app.config["SEARCH_INDEX_PREFIX"] = "test-"
    yield
    app.config["SEARCH_INDEX_PREFIX"] = tmp


@pytest.fixture(scope="function")
def record_cls_with_index(app):
    """Record class with index field."""

    class Record:
        """Simulates a record class with an IndexField.

        Since the IndexField has the __get__ method overwritten
        to return the actual index object this class behaves in
        the same way.
        """

        index = dsl.Index(app.config["INDEXER_DEFAULT_INDEX"])

    return Record