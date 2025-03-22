# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import datetime
import os
import shutil
import tempfile
import uuid
from contextlib import contextmanager
from copy import deepcopy
import json
from mock import Mock, patch
from six import BytesIO
import pytest

# imported to make sure that
# login_oauth2_user(valid, oauth) is included
import invenio_oauth2server.views.server  # noqa


from elasticsearch import Elasticsearch
from elasticsearch_dsl import response, Search
from sqlalchemy_utils.functions import create_database, database_exists
from kombu import Exchange, Queue
from flask import Flask, appcontext_pushed, g
from flask.cli import ScriptInfo
from flask_celeryext import FlaskCeleryExt

from invenio_access import InvenioAccess
from invenio_accounts import InvenioAccounts, InvenioAccountsREST
from invenio_access.models import ActionRoles, ActionUsers
from invenio_accounts.testutils import create_test_user
from invenio_accounts.models import Role, User
from invenio_cache import InvenioCache
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_marc21 import InvenioMARC21
from invenio_indexer import InvenioIndexer
from invenio_oauth2server import InvenioOAuth2Server, InvenioOAuth2ServerREST
from invenio_oauth2server.models import Token
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.minters import recid_minter
from invenio_pidrelations.config import PIDRELATIONS_RELATION_TYPES
from invenio_queues import InvenioQueues
from invenio_queues.proxies import current_queues
from invenio_records import InvenioRecords
from invenio_records.api import Record
from invenio_search import InvenioSearch, current_search, current_search_client
from werkzeug.local import LocalProxy

from invenio_stats import InvenioStats, current_stats as _current_stats
from invenio_stats.contrib.event_builders import build_file_unique_id, \
    build_record_unique_id, file_download_event_builder
from invenio_stats.contrib.registrations import register_queries
from invenio_stats.config import STATS_EVENTS, STATS_AGGREGATIONS, STATS_QUERIES
from invenio_stats.processors import EventsIndexer
from invenio_stats.models import StatsEvents, StatsAggregation, StatsBookmark
from invenio_stats.tasks import aggregate_events, process_events
from invenio_stats.views import blueprint

from tests.helpers import json_data, create_record


def mock_iter_entry_points_factory(data, mocked_group):
    """Create a mock iter_entry_points function."""
    from pkg_resources import iter_entry_points

    def entrypoints(group, name=None):
        if group == mocked_group:
            for entrypoint in data:
                yield entrypoint
        else:
            for x in iter_entry_points(group=group, name=name):
                yield x
    return entrypoints


@pytest.fixture()
def records(db):
    record_data = json_data("data/test_records.json")
    item_data = json_data("data/test_items.json")
    record_num = len(record_data)
    result = []
    for d in range(record_num):
        result.append(create_record(record_data[d], item_data[d]))
    db.session.commit()
    yield result


@pytest.yield_fixture()
def mock_gethostbyaddr():
    with patch("invenio_stats.contrib.event_builders.gethostbyaddr", return_value="test_host"):
        yield


@pytest.yield_fixture()
def event_entrypoints():
    """Declare some events by mocking the invenio_stats.events entrypoint.

    It yields a list like [{event_type: <event_type_name>}, ...].
    """
    data = []
    result = []
    for idx in range(5):
        event_type_name = 'event_{}'.format(idx)
        from pkg_resources import EntryPoint
        entrypoint = EntryPoint(event_type_name, event_type_name)
        conf = dict(event_type=event_type_name,
                    templates='invenio_stats.contrib.record_view',
                    processor_class=EventsIndexer)
        entrypoint.load = lambda conf=conf: (lambda: [conf])
        data.append(entrypoint)
        result.append(conf)

    # including file-download
    from pkg_resources import EntryPoint
    entrypoint = EntryPoint('invenio_files_rest', 'test_dir')
    conf = dict(event_type='file-download',
                templates='invenio_stats.contrib.file_download',
                processor_class=EventsIndexer)
    entrypoint.load = lambda conf=conf: (lambda: [conf])
    data.append(entrypoint)

    # including record-view
    entrypoint = EntryPoint('invenio_records_ui', 'test_dir')
    conf = dict(event_type='record-view',
                templates='invenio_stats.contrib.record_view',
                processor_class=EventsIndexer)
    entrypoint.load = lambda conf=conf: (lambda: [conf])
    data.append(entrypoint)

    entrypoints = mock_iter_entry_points_factory(data, 'invenio_stats.events')

    with patch('invenio_stats.ext.iter_entry_points', entrypoints):
        yield result


@pytest.yield_fixture()
def query_entrypoints(custom_permission_factory):
    """Same as event_entrypoints for queries."""
    from pkg_resources import EntryPoint
    entrypoint = EntryPoint('invenio_stats', 'queries')
    data = []
    result = []
    conf = [dict(
        query_name='test-query',
        query_class=CustomQuery,
        query_config=dict(
            index='stats-file-download',
            doc_type='file-download-day-aggregation',
            copy_fields=dict(
                bucket_id='bucket_id',
            ),
            required_filters=dict(
                bucket_id='bucket_id',
            )
        ),
        permission_factory=custom_permission_factory
    ),
        dict(
        query_name='test-query2',
        query_class=CustomQuery,
        query_config=dict(
            index='stats-file-download',
            doc_type='file-download-day-aggregation',
            copy_fields=dict(
                bucket_id='bucket_id',
            ),
            required_filters=dict(
                bucket_id='bucket_id',
            )
        ),
        permission_factory=custom_permission_factory
    )]

    result += conf
    result += register_queries()
    entrypoint.load = lambda conf=conf: (lambda: result)
    data.append(entrypoint)

    entrypoints = mock_iter_entry_points_factory(data, 'invenio_stats.queries')

    with patch('invenio_stats.ext.iter_entry_points',
               entrypoints):
        yield result


@pytest.yield_fixture()
def mock_anonymization_salt():
    """Mock the "get_anonymization_salt" function."""
    with patch('invenio_stats.processors.get_anonymization_salt',
               return_value='test-salt'):
        yield


def date_range(start_date, end_date):
    """Get all dates in a given range."""
    if start_date >= end_date:
        for n in range((start_date - end_date).days + 1):
            yield end_date + datetime.timedelta(n)
    else:
        for n in range((end_date - start_date).days + 1):
            yield start_date + datetime.timedelta(n)


@pytest.yield_fixture()
def event_queues(app, event_entrypoints):
    """Delete and declare test queues."""
    current_queues.delete()
    try:
        current_queues.declare()
        yield
    finally:
        current_queues.delete()


@pytest.yield_fixture()
def instance_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path, mock_gethostbyaddr):
    """Flask application fixture without InvenioStats."""
    app_ = Flask('testapp', instance_path=instance_path)
    stats_events = {
        'file-download': deepcopy(STATS_EVENTS['file-download']),
        'record-view': {
            'signal': 'invenio_records_ui.signals.record_viewed',
            'event_builders': ['invenio_stats.contrib.event_builders'
                               '.record_view_event_builder']
        }
    }
    stats_events.update({'event_{}'.format(idx): {} for idx in range(5)})
    app_.config.update(dict(
        CELERY_ALWAYS_EAGER=True,
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND='memory',
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        CELERY_RESULT_BACKEND='cache',
        CACHE_REDIS_URL="redis://redis:6379/0",
        CACHE_REDIS_DB=0,
        CACHE_REDIS_HOST="redis",

        QUEUES_BROKER_URL="amqp://guest:guest@rabbitmq:5672//",
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite://'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        SEARCH_ELASTIC_HOSTS=os.environ.get(
            'SEARCH_ELASTIC_HOSTS', 'elasticsearch'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        TESTING=True,
        OAUTH2SERVER_CLIENT_ID_SALT_LEN=64,
        OAUTH2SERVER_CLIENT_SECRET_SALT_LEN=60,
        OAUTH2SERVER_TOKEN_PERSONAL_SALT_LEN=60,
        OAUTH2_CACHE_TYPE="simple",
        SEARCH_INDEX_PREFIX='test-',
        STATS_MQ_EXCHANGE=Exchange(
            'test_events',
            type='direct',
            delivery_mode='transient',  # in-memory queue
            durable=True,
        ),
        SECRET_KEY='asecretkey',
        SERVER_NAME='localhost',
        PIDRELATIONS_RELATION_TYPES=PIDRELATIONS_RELATION_TYPES,
        STATS_QUERIES=STATS_QUERIES,
        STATS_EVENTS=stats_events,
        STATS_AGGREGATIONS=STATS_AGGREGATIONS,
        INDEXER_MQ_QUEUE = Queue("indexer", exchange=Exchange("indexer", type="direct"), routing_key="indexer",queue_arguments={"x-queue-type":"quorum"})
    ))
    FlaskCeleryExt(app_)
    InvenioAccess(app_)
    InvenioAccounts(app_)
    InvenioAccountsREST(app_)
    InvenioDB(app_)
    InvenioRecords(app_)
    InvenioFilesREST(app_)
    InvenioPIDStore(app_)
    InvenioCache(app_)
    InvenioQueues(app_)
    InvenioIndexer(app_)
    InvenioOAuth2Server(app_)
    InvenioOAuth2ServerREST(app_)
    InvenioMARC21(app_)
    InvenioSearch(app_, entry_point_group=None, client=Elasticsearch("http://elasticsearch:9200"))

    current_stats = LocalProxy(lambda: app_.extensions["invenio-stats"])
    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture with InvenioStats."""
    InvenioStats(base_app)
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def client(app):
    app.register_blueprint(blueprint, url_prefix="/api/stats")
    with app.test_client() as client:
        yield client


@pytest.fixture()
def role_users(app, db):
    """Create users."""
    ds = app.extensions["invenio-accounts"].datastore
    user_count = User.query.filter_by(email="user@test.org").count()
    if user_count != 1:
        user = create_test_user(email="user@test.org")
        contributor = create_test_user(email="contributor@test.org")
        comadmin = create_test_user(email="comadmin@test.org")
        repoadmin = create_test_user(email="repoadmin@test.org")
        sysadmin = create_test_user(email="sysadmin@test.org")
        generaluser = create_test_user(email="generaluser@test.org")
        originalroleuser = create_test_user(email="originalroleuser@test.org")
        originalroleuser2 = create_test_user(email="originalroleuser2@test.org")
    else:
        user = User.query.filter_by(email="user@test.org").first()
        contributor = User.query.filter_by(email="contributor@test.org").first()
        comadmin = User.query.filter_by(email="comadmin@test.org").first()
        repoadmin = User.query.filter_by(email="repoadmin@test.org").first()
        sysadmin = User.query.filter_by(email="sysadmin@test.org").first()
        generaluser = User.query.filter_by(email="generaluser@test.org")
        originalroleuser = create_test_user(email="originalroleuser@test.org")
        originalroleuser2 = create_test_user(email="originalroleuser2@test.org")

    role_count = Role.query.filter_by(name="System Administrator").count()
    if role_count != 1:
        sysadmin_role = ds.create_role(name="System Administrator")
        repoadmin_role = ds.create_role(name="Repository Administrator")
        contributor_role = ds.create_role(name="Contributor")
        comadmin_role = ds.create_role(name="Community Administrator")
        general_role = ds.create_role(name="General")
        originalrole = ds.create_role(name="Original Role")
    else:
        sysadmin_role = Role.query.filter_by(name="System Administrator").first()
        repoadmin_role = Role.query.filter_by(name="Repository Administrator").first()
        contributor_role = Role.query.filter_by(name="Contributor").first()
        comadmin_role = Role.query.filter_by(name="Community Administrator").first()
        general_role = Role.query.filter_by(name="General").first()
        originalrole = Role.query.filter_by(name="Original Role").first()

    # Assign access authorization
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action="superuser-access", user=sysadmin),
        ]
        db.session.add_all(action_users)
        action_roles = [
            ActionRoles(action="superuser-access", role=sysadmin_role),
            ActionRoles(action="admin-access", role=repoadmin_role),
            ActionRoles(action="schema-access", role=repoadmin_role),
            ActionRoles(action="index-tree-access", role=repoadmin_role),
            ActionRoles(action="indextree-journal-access", role=repoadmin_role),
            ActionRoles(action="item-type-access", role=repoadmin_role),
            ActionRoles(action="item-access", role=repoadmin_role),
            ActionRoles(action="files-rest-bucket-update", role=repoadmin_role),
            ActionRoles(action="files-rest-object-delete", role=repoadmin_role),
            ActionRoles(action="files-rest-object-delete-version", role=repoadmin_role),
            ActionRoles(action="files-rest-object-read", role=repoadmin_role),
            ActionRoles(action="search-access", role=repoadmin_role),
            ActionRoles(action="detail-page-acces", role=repoadmin_role),
            ActionRoles(action="download-original-pdf-access", role=repoadmin_role),
            ActionRoles(action="author-access", role=repoadmin_role),
            ActionRoles(action="items-autofill", role=repoadmin_role),
            ActionRoles(action="stats-api-access", role=repoadmin_role),
            ActionRoles(action="read-style-action", role=repoadmin_role),
            ActionRoles(action="update-style-action", role=repoadmin_role),
            ActionRoles(action="detail-page-acces", role=repoadmin_role),
            ActionRoles(action="admin-access", role=comadmin_role),
            ActionRoles(action="index-tree-access", role=comadmin_role),
            ActionRoles(action="indextree-journal-access", role=comadmin_role),
            ActionRoles(action="item-access", role=comadmin_role),
            ActionRoles(action="files-rest-bucket-update", role=comadmin_role),
            ActionRoles(action="files-rest-object-delete", role=comadmin_role),
            ActionRoles(action="files-rest-object-delete-version", role=comadmin_role),
            ActionRoles(action="files-rest-object-read", role=comadmin_role),
            ActionRoles(action="search-access", role=comadmin_role),
            ActionRoles(action="detail-page-acces", role=comadmin_role),
            ActionRoles(action="download-original-pdf-access", role=comadmin_role),
            ActionRoles(action="author-access", role=comadmin_role),
            ActionRoles(action="items-autofill", role=comadmin_role),
            ActionRoles(action="detail-page-acces", role=comadmin_role),
            ActionRoles(action="detail-page-acces", role=comadmin_role),
            ActionRoles(action="item-access", role=contributor_role),
            ActionRoles(action="files-rest-bucket-update", role=contributor_role),
            ActionRoles(action="files-rest-object-delete", role=contributor_role),
            ActionRoles(
                action="files-rest-object-delete-version", role=contributor_role
            ),
            ActionRoles(action="files-rest-object-read", role=contributor_role),
            ActionRoles(action="search-access", role=contributor_role),
            ActionRoles(action="detail-page-acces", role=contributor_role),
            ActionRoles(action="download-original-pdf-access", role=contributor_role),
            ActionRoles(action="author-access", role=contributor_role),
            ActionRoles(action="items-autofill", role=contributor_role),
            ActionRoles(action="detail-page-acces", role=contributor_role),
            ActionRoles(action="detail-page-acces", role=contributor_role),
        ]
        db.session.add_all(action_roles)
        ds.add_role_to_user(sysadmin, sysadmin_role)
        ds.add_role_to_user(repoadmin, repoadmin_role)
        ds.add_role_to_user(contributor, contributor_role)
        ds.add_role_to_user(comadmin, comadmin_role)
        ds.add_role_to_user(generaluser, general_role)
        ds.add_role_to_user(originalroleuser, originalrole)
        ds.add_role_to_user(originalroleuser2, originalrole)
        ds.add_role_to_user(originalroleuser2, repoadmin_role)
        

    return [
        {"email": contributor.email, "id": contributor.id, "obj": contributor},
        {"email": repoadmin.email, "id": repoadmin.id, "obj": repoadmin},
        {"email": sysadmin.email, "id": sysadmin.id, "obj": sysadmin},
        {"email": comadmin.email, "id": comadmin.id, "obj": comadmin},
        {"email": generaluser.email, "id": generaluser.id, "obj": sysadmin},
        {
            "email": originalroleuser.email,
            "id": originalroleuser.id,
            "obj": originalroleuser,
        },
        {
            "email": originalroleuser2.email,
            "id": originalroleuser2.id,
            "obj": originalroleuser2,
        },
        {"email": user.email, "id": user.id, "obj": user},
    ]


@pytest.yield_fixture()
def db(app):
    """Setup database."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


class MockEs():
    def __init__(self,**keywargs):
        self.indices = self.MockIndices()
        self.es = Elasticsearch()

    @property
    def transport(self):
        return self.es.transport

    class MockIndices():
        def __init__(self,**keywargs):
            self.mapping = dict()
        def delete(self,index):
            pass
        def delete_template(self,index):
            pass
        def create(self,index,body,ignore):
            self.mapping[index] = body
        def put_alias(self,index, name, ignore):
            pass
        def put_template(self,name, body, ignore):
            pass
        def refresh(self,index):
            pass
        def exists(self, index, **kwargs):
            if index in self.mapping:
                return True
            else:
                return False
        def flush(self,index):
            pass
        
        def search(self,index,doc_type,body,**kwargs):
            pass


@pytest.yield_fixture()
def es(app):
    """Provide elasticsearch access, create and clean indices.

    Don't create template so that the test or another fixture can modify the
    enabled events.
    """
    current_search_client.indices.delete(index='test-*')
    # item_create event
    with open("invenio_stats/contrib/item_create/v6/item-create-v1.json", "r") as f:
        item_create_mapping = json.load(f)
    item_create_mapping.update({'aliases':
        {'{}events-stats-item-create'.format(app.config['SEARCH_INDEX_PREFIX']): {'is_write_index': True}}})
    current_search_client.indices.create(
        index='{}events-stats-item-create-0001'.format(app.config['SEARCH_INDEX_PREFIX']),
        body=item_create_mapping, ignore=[400, 404]
    )
    # item_create aggr
    with open("invenio_stats/contrib/aggregations/aggr_item_create/v6/aggr-item-create-v1.json", "r") as f:
        aggr_item_create_mapping = json.load(f)
    aggr_item_create_mapping.update({'aliases':
        {'{}stats-item-create'.format(app.config['SEARCH_INDEX_PREFIX']): {'is_write_index': True}}})
    current_search_client.indices.create(
        index='{}stats-item-create-0001'.format(app.config['SEARCH_INDEX_PREFIX']),
        body=aggr_item_create_mapping, ignore=[400, 404]
    )
    # top_view event
    with open("invenio_stats/contrib/top_view/v6/top-view-v1.json", "r") as f:
        top_view_mapping = json.load(f)
    top_view_mapping.update({'aliases':
        {'{}events-stats-top-view'.format(app.config['SEARCH_INDEX_PREFIX']): {'is_write_index': True}}})
    current_search_client.indices.create(
        index='{}events-stats-top-view-0001'.format(app.config['SEARCH_INDEX_PREFIX']),
        body=top_view_mapping, ignore=[400, 404]
    )
    # top_view aggr
    with open("invenio_stats/contrib/aggregations/aggr_top_view/v6/aggr-top-view-v1.json", "r") as f:
        aggr_top_view_mapping = json.load(f)
    aggr_top_view_mapping.update({'aliases':
        {'{}stats-top-view'.format(app.config['SEARCH_INDEX_PREFIX']): {'is_write_index': True}}})
    current_search_client.indices.create(
        index='{}stats-top-view-0001'.format(app.config['SEARCH_INDEX_PREFIX']),
        body=aggr_top_view_mapping, ignore=[400, 404]
    )
    # search event
    with open("invenio_stats/contrib/search/v6/search-v1.json", "r") as f:
        search_mapping = json.load(f)
    search_mapping.update({'aliases':
        {'{}events-stats-search'.format(app.config['SEARCH_INDEX_PREFIX']): {'is_write_index': True}}})
    current_search_client.indices.create(
        index='{}events-stats-search-0001'.format(app.config['SEARCH_INDEX_PREFIX']),
        body=search_mapping, ignore=[400, 404]
    )
    # search aggr
    with open("invenio_stats/contrib/aggregations/aggr_search/v6/aggr-search-v1.json", "r") as f:
        aggr_search_mapping = json.load(f)
    aggr_search_mapping.update({'aliases':
        {'{}stats-search'.format(app.config['SEARCH_INDEX_PREFIX']): {'is_write_index': True}}})
    current_search_client.indices.create(
        index='{}stats-search-0001'.format(app.config['SEARCH_INDEX_PREFIX']),
        body=aggr_search_mapping, ignore=[400, 404]
    )
    # file_download event
    with open("invenio_stats/contrib/file_download/v6/file-download-v1.json", "r") as f:
        file_download_mapping = json.load(f)
    file_download_mapping.update({'aliases':
        {'{}events-stats-file-download'.format(app.config['SEARCH_INDEX_PREFIX']): {'is_write_index': True}}})
    current_search_client.indices.create(
        index='{}events-stats-file-download-0001'.format(app.config['SEARCH_INDEX_PREFIX']),
        body=file_download_mapping, ignore=[400, 404]
    )
    # file_download aggr
    with open("invenio_stats/contrib/aggregations/aggr_file_download/v6/aggr-file-download-v1.json", "r") as f:
        aggr_file_download_mapping = json.load(f)
    aggr_file_download_mapping.update({'aliases':
        {'{}stats-file-download'.format(app.config['SEARCH_INDEX_PREFIX']): {'is_write_index': True}}})
    current_search_client.indices.create(
        index='{}stats-file-download-0001'.format(app.config['SEARCH_INDEX_PREFIX']),
        body=aggr_file_download_mapping, ignore=[400, 404]
    )
    # file_preview event
    with open("invenio_stats/contrib/file_preview/v6/file-preview-v1.json", "r") as f:
        file_preview_mapping = json.load(f)
    file_preview_mapping.update({'aliases':
        {'{}events-stats-file-preview'.format(app.config['SEARCH_INDEX_PREFIX']): {'is_write_index': True}}})
    current_search_client.indices.create(
        index='{}events-stats-file-preview-0001'.format(app.config['SEARCH_INDEX_PREFIX']),
        body=file_preview_mapping, ignore=[400, 404]
    )
    # file_preview aggr
    with open("invenio_stats/contrib/aggregations/aggr_file_preview/v6/aggr-file-preview-v1.json", "r") as f:
        aggr_file_preview_mapping = json.load(f)
    aggr_file_preview_mapping.update({'aliases':
        {'{}stats-file-preview'.format(app.config['SEARCH_INDEX_PREFIX']): {'is_write_index': True}}})
    current_search_client.indices.create(
        index='{}stats-file-preview-0001'.format(app.config['SEARCH_INDEX_PREFIX']),
        body=aggr_file_preview_mapping, ignore=[400, 404]
    )
    # record_view event
    with open("invenio_stats/contrib/record_view/v6/record-view-v1.json", "r") as f:
        record_view_mapping = json.load(f)
    record_view_mapping.update({'aliases':
        {'{}events-stats-record-view'.format(app.config['SEARCH_INDEX_PREFIX']): {'is_write_index': True}}})
    current_search_client.indices.create(
        index='{}events-stats-record-view-0001'.format(app.config['SEARCH_INDEX_PREFIX']),
        body=record_view_mapping, ignore=[400, 404]
    )
    # record_view aggr
    with open("invenio_stats/contrib/aggregations/aggr_record_view/v6/aggr-record-view-v1.json", "r") as f:
        aggr_record_view_mapping = json.load(f)
    aggr_record_view_mapping.update({'aliases':
        {'{}stats-record-view'.format(app.config['SEARCH_INDEX_PREFIX']): {'is_write_index': True}}})
    current_search_client.indices.create(
        index='{}stats-record-view-0001'.format(app.config['SEARCH_INDEX_PREFIX']),
        body=aggr_record_view_mapping, ignore=[400, 404]
    )
    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index='test-*')


@pytest.yield_fixture()
def es_with_templates(app, es):
    """Provide elasticsearch access, create and clean indices and templates."""
    list(current_search.put_templates())
    yield current_search_client


@pytest.fixture()
def celery(app):
    """Get queueobject for testing bulk operations."""
    return app.extensions['flask-celeryext'].celery


@pytest.fixture()
def script_info(app):
    """Get ScriptInfo object for testing CLI."""
    return ScriptInfo(create_app=lambda info: app)


@contextmanager
def user_set(app, user):
    """User set."""
    def handler(sender, **kwargs):
        g.user = user
    with appcontext_pushed.connected_to(handler, app):
        yield


@pytest.yield_fixture()
def dummy_location(db):
    """File system location."""
    tmppath = tempfile.mkdtemp()

    loc = Location(
        name='testloc',
        uri=tmppath,
        default=True
    )
    db.session.add(loc)
    db.session.commit()

    yield loc

    shutil.rmtree(tmppath)


@pytest.fixture()
def record(db):
    """File system location."""
    return Record.create({})


@pytest.fixture()
def pid(db, record):
    """File system location."""
    return recid_minter(record.id, record)


@pytest.fixture()
def bucket(db, dummy_location):
    """File system location."""
    b1 = Bucket.create()
    return b1


@pytest.yield_fixture()
def objects(bucket):
    """File system location."""
    # Create older versions first
    for key, content in [
            ('LICENSE', b'old license'),
            ('README.rst', b'old readme')]:
        ObjectVersion.create(
            bucket, key, stream=BytesIO(content), size=len(content)
        )

    # Create new versions
    objs = []
    for key, content in [
            ('LICENSE', b'license file'),
            ('README.rst', b'readme file')]:
        obj = ObjectVersion.create(
                bucket, key, stream=BytesIO(content),
                size=len(content)
            )
        obj.userrole = 'guest'
        obj.site_license_name = ''
        obj.site_license_flag = False
        obj.index_list = []
        obj.userid = 0
        obj.item_id = 1
        obj.item_title = 'test title'
        obj.is_billing_item = False
        obj.billing_file_price = 0
        obj.user_group_list = []
        objs.append(obj)

    yield objs


@pytest.yield_fixture(scope="session")
def sequential_ids():
    """Sequential uuids for files."""
    ids = [uuid.UUID((
        '0000000000000000000000000000000' + str(i))[-32:])
        for i in range(100000)]
    yield ids


@pytest.fixture()
def mock_users():
    """Create mock users."""
    mock_auth_user = Mock()
    mock_auth_user.get_id = lambda: '123'
    mock_auth_user.is_authenticated = True

    mock_anon_user = Mock()
    mock_anon_user.is_authenticated = False
    return {
        'anonymous': mock_anon_user,
        'authenticated': mock_auth_user
    }


@pytest.yield_fixture()
def mock_user_ctx(mock_users):
    """Run in a mock authenticated user context."""
    with patch('invenio_stats.utils.current_user',
               mock_users['authenticated']):
        yield


@pytest.fixture()
def request_headers():
    """Return request headers for normal user and bot."""
    return dict(
        user={'USER_AGENT':
              'Mozilla/5.0 (Windows NT 6.1; WOW64) '
              'AppleWebKit/537.36 (KHTML, like Gecko)'
              'Chrome/45.0.2454.101 Safari/537.36'},
        robot={'USER_AGENT': 'googlebot'},
        machine={'USER_AGENT': 'Wget/1.14 (linux-gnu)'}
    )


@pytest.yield_fixture()
def mock_datetime():
    """Mock datetime.datetime.

    Use set_utcnow to set the current utcnow time.
    """
    class NewDate(datetime.datetime):
        _utcnow = (2017, 1, 1)

        @classmethod
        def set_utcnow(cls, value):
            cls._utcnow = value

        @classmethod
        def utcnow(cls):
            return cls(*cls._utcnow)

    yield NewDate


@pytest.yield_fixture()
def mock_event_queue(app, mock_datetime, request_headers, objects,
                     event_entrypoints, mock_user_ctx):
    """Create a mock queue containing a few file download events."""
    mock_queue = Mock()
    mock_queue.routing_key = 'stats-file-download'
    with patch('datetime.datetime', mock_datetime), \
            app.test_request_context(headers=request_headers['user']):
        events = [
            build_file_unique_id(
                file_download_event_builder({'unique_session_id': 'S0000000000000000000000000000001'},
                                            app, objects[0])
            ) for idx in range(100)
        ]
        mock_queue.consume.return_value = iter(events)
    # Save the queued events for later tests
    mock_queue.queued_events = deepcopy(events)
    return mock_queue


@pytest.fixture()
def mock_es_execute():
    def _dummy_response(data):
        if isinstance(data, str):
            with open(data, "r") as f:
                data = json.load(f)
        dummy=response.Response(Search(), data)
        return dummy
    return _dummy_response


def generate_file_events(app, event_type, file_number=5, event_number=100, robot_event_number=0,
                    start_date=datetime.date(2022, 10, 1),
                    end_date=datetime.date(2022, 10, 7)):
    """Queued events for processing tests."""
    current_queues.declare()

    def _unique_ts_gen():
        ts = 0
        while True:
            ts += 1
            yield ts

    def generator_list():
        unique_ts = _unique_ts_gen()
        res = []
        for file_idx in range(file_number):
            user_data = user_role[file_idx % 3]
            for entry_date in date_range(start_date, end_date):
                file_id = 'F000000000000000000000000000000{}'.\
                    format(file_idx + 1)
                bucket_id = 'B000000000000000000000000000000{}'.\
                    format(file_idx + 1)

                def build_event(is_robot=False):
                    ts = next(unique_ts)
                    return dict(
                        timestamp=datetime.datetime.combine(
                            entry_date,
                            datetime.time(minute=ts % 60,
                                          second=ts % 60)).
                        isoformat(),
                        bucket_id=bucket_id,
                        file_id=file_id,
                        root_file_id=file_id,
                        file_key='test.pdf',
                        size=9000,
                        accessrole='open_access',
                        visitor_id=100,
                        is_robot=is_robot,
                        item_id='1',
                        index_list='test_index',
                        userrole=user_data["role"],
                        site_license_flag=False,
                        is_restricted=False,
                        user_goup_names="",
                        cur_user_id=user_data["id"],
                        item_title='test_item',
                        remote_addr="test_remote_addr",
                        hostname='test_hostname',
                        unique_session_id="xxxxxxx"
                    )

                for event_idx in range(event_number):
                    res.append(build_event())
                for event_idx in range(robot_event_number):
                    res.append(build_event(True))
        return res

    user_role = [
        {
            "id": 2,
            "role": "System Administrator"
        },
        {
            "id": 7,
            "role": ""
        },
        {
            "id": 0,
            "role": "guest"
        }
    ]
    events = generator_list()
    for e in events:
        e = build_file_unique_id(e)

    # register into elastisearch.
    event_type = 'file-download'
    _current_stats.publish(event_type, events)
    process_events([event_type])


@pytest.yield_fixture()
def indexed_file_download_events(app, es, mock_user_ctx, request):
    """Parametrized pre indexed sample events."""
    generate_file_events(app=app, event_type="file-download", **request.param)
    current_search_client.indices.flush(index='test-*')
    yield


@pytest.yield_fixture()
def aggregated_file_download_events(app, es, mock_user_ctx, request):
    """Parametrized pre indexed sample events."""
    for t in current_search.put_templates(ignore=[400]):
        pass
    generate_file_events(app=app, event_type="file-download", **request.param)
    aggregate_events(
        ['file-download-agg'],
        start_date='2022-10-01',
        end_date='2022-10-30',
        update_bookmark=False,
        manual=True)
    current_search_client.indices.flush(index='test-*')
    yield

@pytest.yield_fixture()
def indexed_file_preview_events(app, es, mock_user_ctx, request):
    """Parametrized pre indexed sample events."""
    generate_file_events(app=app, event_type="file-preview", **request.param)
    yield


@pytest.yield_fixture()
def aggregated_file_preview_events(app, es, mock_user_ctx, request):
    """Parametrized pre indexed sample events."""
    for t in current_search.put_templates(ignore=[400]):
        pass
    generate_file_events(app=app, event_type="file-preview", **request.param)
    aggregate_events(['file-preview-agg'])
    current_search_client.indices.flush(index='test-*')
    yield


@pytest.yield_fixture()
def stats_events_for_db(app, db):
    def base_event(id, event_type):
        return StatsEvents(
            source_id=str(id),
            index='test-events-stats-{}'.format(event_type),
            type='stats-{}'.format(event_type),
            source=json.dumps({'test': 'test'}),
            date=datetime.datetime(2023, 1, 1, 1, 0, 0)
        )
    
    try:
        with db.session.begin_nested():
            db.session.add(base_event(1, 'top-view'))
        db.session.commit()
    except:
        db.session.rollback()


@pytest.fixture()
def users(app, db):
    """Create users."""
    user1 = create_test_user(email='info@inveniosoftware.org',
                             password='tester')
    user2 = create_test_user(email='info2@inveniosoftware.org',
                             password='tester2')

    user1.allowed_token = Token.create_personal(name='allowed_token',
                                                user_id=user1.id,
                                                scopes=[]
                                                ).access_token
    user2.allowed_token = Token.create_personal(name='allowed_token',
                                                user_id=user2.id,
                                                scopes=[]
                                                ).access_token
    return {'authorized': user1, 'unauthorized': user2}


def get_deleted_docs(index):
    """Get all deleted docs from an ES index."""
    return current_search_client.indices.stats()[
        'indices'][index]['total']['docs'][
        'deleted']


def _create_file_download_event(timestamp,
                                bucket_id='B0000000000000000000000000000001',
                                file_id='F0000000000000000000000000000001',
                                size=9000,
                                file_key='test.pdf',
                                visitor_id=100,
                                user_id=None,
                                remote_addr='192.168.0.1',
                                unique_session_id='S0000000000000000000000000000001'):
    """Create a file_download event content."""
    doc = dict(
        timestamp=datetime.datetime(*timestamp).isoformat(),
        # What:
        bucket_id=str(bucket_id),
        file_id=str(file_id),
        file_key=file_key,
        size=size,
        visitor_id=visitor_id,
        user_id=user_id,
        remote_addr=remote_addr,
        unique_session_id=unique_session_id,
    )
    return build_file_unique_id(doc)


def _create_record_view_event(timestamp,
                              record_id='R0000000000000000000000000000001',
                              pid_type='recid',
                              pid_value='1',
                              visitor_id=100,
                              user_id=None,
                              remote_addr='192.168.0.1',
                              unique_session_id='S0000000000000000000000000000001'):
    """Create a file_download event content."""
    doc = dict(
        timestamp=datetime.datetime(*timestamp).isoformat(),
        # What:
        record_id=record_id,
        pid_type=pid_type,
        pid_value=pid_value,
        visitor_id=visitor_id,
        user_id=user_id,
        remote_addr=remote_addr,
        unique_session_id=unique_session_id,
    )
    return build_record_unique_id(doc)


@pytest.fixture()
def custom_permission_factory(users):
    """Test denying permission factory."""
    def permission_factory(query_name, params, *args, **kwargs):
        permission_factory.query_name = query_name
        permission_factory.params = params
        from flask_login import current_user
        if current_user.is_authenticated and \
                current_user.id == users['authorized'].id:
            return type('Allow', (), {'can': lambda self: True})()
        return type('Deny', (), {'can': lambda self: False})()
    permission_factory.query_name = None
    permission_factory.params = None
    return permission_factory


@pytest.yield_fixture()
def sample_histogram_query_data():
    """Sample query parameters."""
    yield {"mystat":
           {"stat": "bucket-file-download-histogram",
            "params": {"start_date": "2017-1-1",
                       "end_date": "2017-7-1",
                       "interval": "day",
                       "bucket_id":
                       "B0000000000000000000000000000001",
                       "file_key": "test.pdf"
                       }
            }
           }


class CustomQuery:
    """Mock query class."""

    def __init__(self, *args, **kwargs):
        """Mock constructor to accept the query_config parameters."""
        pass

    def run(self, *args, **kwargs):
        """Sample response."""
        return dict(bucket_id='test_bucket',
                    value=100)
