# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import copy
import json
import os
import shutil
import sys
import tempfile
from os.path import dirname, join

import pytest
from elasticsearch import VERSION as ES_VERSION
from elasticsearch.exceptions import RequestError
from flask import Flask, url_for
from flask_login import LoginManager, UserMixin
from helpers import create_record
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_indexer import InvenioIndexer
from invenio_indexer.api import RecordIndexer
from invenio_indexer.signals import before_record_index
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_rest import InvenioREST
from invenio_search import InvenioSearch, RecordsSearch, current_search, \
    current_search_client
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_records_rest import InvenioRecordsREST, config
from invenio_records_rest.facets import terms_filter
from invenio_records_rest.utils import PIDConverter
from invenio_records_rest.views import create_blueprint_from_app

sys.path.append(os.path.dirname(__file__))


class TestSearch(RecordsSearch):
    """Test record search."""

    class Meta:
        """Test configuration."""

        index = 'invenio-records-rest'
        doc_types = None

    def __init__(self, **kwargs):
        """Add extra options."""
        super(TestSearch, self).__init__(**kwargs)
        self._extra.update(**{'_source': {'excludes': ['_access']}})


class IndexFlusher(object):
    """Simple object to flush an index."""

    def __init__(self, search_class):
        """Initialize instance."""
        self.search_class = search_class

    def flush_and_wait(self):
        """Flush index and wait until operation is fully done."""
        current_search.flush_and_refresh(self.search_class.Meta.index)


@pytest.yield_fixture(scope='session')
def search_class():
    """Search class."""
    yield TestSearch


@pytest.yield_fixture()
def search_url():
    """Search class."""
    yield url_for('invenio_records_rest.recid_list')


@pytest.yield_fixture()
def app(request, search_class):
    """Flask application fixture.

    Note that RECORDS_REST_ENDPOINTS is used during application creation to
    create blueprints on the fly, hence once you have this fixture in a test,
    it's too late to customize the configuration variable. You can however
    customize it using parameterized tests:

    .. code-block:: python

    @pytest.mark.parametrize('app', [dict(
        endpoint=dict(
            search_class='conftest:TestSearch',
        )
    def test_mytest(app, db, es):
        # ...

    This will parameterize the default 'recid' endpoint in
    RECORDS_REST_ENDPOINTS.

    Alternatively:

    .. code-block:: python

    @pytest.mark.parametrize('app', [dict(
        records_rest_endpoints=dict(
            recid=dict(
                search_class='conftest:TestSearch',
            )
        )
    def test_mytest(app, db, es):
        # ...

    This will fully parameterize RECORDS_REST_ENDPOINTS.
    """
    instance_path = tempfile.mkdtemp()
    app = Flask('testapp', instance_path=instance_path)
    app.config.update(
        ACCOUNTS_JWT_ENABLE=False,
        INDEXER_DEFAULT_DOC_TYPE='testrecord',
        INDEXER_DEFAULT_INDEX=search_class.Meta.index,
        RECORDS_REST_ENDPOINTS=copy.deepcopy(config.RECORDS_REST_ENDPOINTS),
        RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_RESULTS_SIZE=10,
        RECORDS_REST_DEFAULT_SEARCH_INDEX=search_class.Meta.index,
        RECORDS_REST_FACETS={
            search_class.Meta.index: {
                'aggs': {
                    'stars': {'terms': {'field': 'stars'}}
                },
                'post_filters': {
                    'stars': terms_filter('stars'),
                }
            }
        },
        RECORDS_REST_SORT_OPTIONS={
            search_class.Meta.index: dict(
                year=dict(
                    fields=['year'],
                )
            )
        },
        SERVER_NAME='localhost:5000',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        TESTING=True,
    )
    app.config['RECORDS_REST_ENDPOINTS']['recid']['search_class'] = \
        search_class

    # Parameterize application.
    if hasattr(request, 'param'):
        if 'endpoint' in request.param:
            app.config['RECORDS_REST_ENDPOINTS']['recid'].update(
                request.param['endpoint'])
        if 'records_rest_endpoints' in request.param:
            original_endpoint = app.config['RECORDS_REST_ENDPOINTS']['recid']
            del app.config['RECORDS_REST_ENDPOINTS']['recid']
            for new_endpoint_prefix, new_endpoint_value in \
                    request.param['records_rest_endpoints'].items():
                new_endpoint = dict(original_endpoint)
                new_endpoint.update(new_endpoint_value)
                app.config['RECORDS_REST_ENDPOINTS'][new_endpoint_prefix] = \
                    new_endpoint

    app.url_map.converters['pid'] = PIDConverter

    InvenioDB(app)
    InvenioREST(app)
    InvenioRecords(app)
    InvenioIndexer(app)
    InvenioPIDStore(app)
    search = InvenioSearch(app)
    search.register_mappings(search_class.Meta.index, 'mock_module.mappings')
    InvenioRecordsREST(app)
    app.register_blueprint(create_blueprint_from_app(app))

    with app.app_context():
        yield app

    # Teardown instance path.
    shutil.rmtree(instance_path)


@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)) and \
            app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite://':
        create_database(db_.engine.url)
    db_.create_all()

    yield db_

    db_.session.remove()
    db_.drop_all()


@pytest.yield_fixture()
def es(app):
    """Elasticsearch fixture."""
    try:
        list(current_search.create())
    except RequestError:
        list(current_search.delete(ignore=[404]))
        list(current_search.create(ignore=[400]))
    current_search_client.indices.refresh()
    yield current_search_client
    list(current_search.delete(ignore=[404]))


def record_indexer_receiver(sender, json=None, record=None, index=None,
                            **kwargs):
    """Mock-receiver of a before_record_index signal."""
    if ES_VERSION[0] == 2:
        suggest_byyear = {}
        suggest_byyear['context'] = {
            'year': json['year']
        }
        suggest_byyear['input'] = [json['title'], ]
        suggest_byyear['output'] = json['title']
        suggest_byyear['payload'] = copy.deepcopy(json)

        suggest_title = {}
        suggest_title['input'] = [json['title'], ]
        suggest_title['output'] = json['title']
        suggest_title['payload'] = copy.deepcopy(json)

        json['suggest_byyear'] = suggest_byyear
        json['suggest_title'] = suggest_title

    elif ES_VERSION[0] >= 5:
        suggest_byyear = {}
        suggest_byyear['contexts'] = {
            'year': [str(json['year'])]
        }
        suggest_byyear['input'] = [json['title'], ]

        suggest_title = {}
        suggest_title['input'] = [json['title'], ]
        json['suggest_byyear'] = suggest_byyear
        json['suggest_title'] = suggest_title

    return json


@pytest.yield_fixture()
def indexer(app, es):
    """Create a record indexer."""
    InvenioIndexer(app)
    before_record_index.connect(record_indexer_receiver, sender=app)
    yield RecordIndexer()


@pytest.yield_fixture(scope='session')
def test_data():
    """Load test records."""
    path = 'data/testrecords.json'
    with open(join(dirname(__file__), path)) as fp:
        records = json.load(fp)
    yield records


@pytest.yield_fixture()
def test_records(db, test_data):
    """Load test records."""
    result = []
    for r in test_data:
        result.append(create_record(r))
    db.session.commit()
    yield result


@pytest.yield_fixture()
def indexed_records(search_class, indexer, test_records):
    """Get a function to wait for records to be flushed to index."""
    for pid, record in test_records:
        indexer.index_by_id(record.id)
    current_search.flush_and_refresh(index=search_class.Meta.index)
    yield test_records


@pytest.yield_fixture(scope='session')
def test_patch():
    """A JSON patch."""
    yield [{'op': 'replace', 'path': '/year', 'value': 1985}]


@pytest.yield_fixture
def default_permissions(app):
    """Test default deny all permission."""
    for key in ['RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY',
                'RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY',
                'RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY',
                'RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY']:
        app.config[key] = getattr(config, key)

    lm = LoginManager(app)

    # Allow easy login for tests purposes :-)
    class User(UserMixin):
        def __init__(self, id):
            self.id = id

    @lm.request_loader
    def load_user(request):
        uid = request.args.get('user', type=int)
        if uid:
            return User(uid)
        return None

    yield app

    app.extensions['invenio-records-rest'].reset_permission_factories()
