# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
# Copyright (C)      2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

import datetime
import os
import shutil
import tempfile
import uuid
from contextlib import contextmanager
from copy import deepcopy
from io import BytesIO
from unittest.mock import Mock, patch

import pytest
from flask import appcontext_pushed, g
from flask.cli import ScriptInfo
from helpers import mock_date
from invenio_accounts.testutils import create_test_user
from invenio_app.factory import create_api as _create_api
from invenio_db import db as db_
from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_oauth2server.models import Token
from invenio_pidstore.minters import recid_minter
from invenio_queues.proxies import current_queues
from invenio_records.api import Record
from invenio_search import current_search, current_search_client
from kombu import Exchange
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_stats.contrib.config import (
    AGGREGATIONS_CONFIG,
    EVENTS_CONFIG,
    QUERIES_CONFIG,
)
from invenio_stats.contrib.event_builders import (
    build_file_unique_id,
    build_record_unique_id,
    file_download_event_builder,
)
from invenio_stats.processors import EventsIndexer, anonymize_user
from invenio_stats.tasks import aggregate_events


@pytest.fixture()
def mock_anonymization_salt():
    """Mock the "get_anonymization_salt" function."""
    with patch(
        "invenio_stats.processors.get_anonymization_salt", return_value="test-salt"
    ):
        yield


def date_range(start_date, end_date):
    """Get all dates in a given range."""
    if start_date >= end_date:
        for n in range((start_date - end_date).days + 1):
            yield end_date + datetime.timedelta(n)
    else:
        for n in range((end_date - start_date).days + 1):
            yield start_date + datetime.timedelta(n)


@pytest.fixture()
def event_queues(app):
    """Delete and declare test queues."""
    current_queues.delete()
    try:
        current_queues.declare()
        yield
    finally:
        current_queues.delete()


@pytest.fixture(scope="module")
def events_config():
    """Events config for the tests."""
    stats_events = deepcopy(EVENTS_CONFIG)
    for idx in range(5):
        event_name = "event_{}".format(idx)
        stats_events[event_name] = {
            "cls": EventsIndexer,
            "templates": "invenio_stats.contrib.record_view",
        }
    return stats_events


@pytest.fixture(scope="module")
def aggregations_config():
    """Aggregations config for the tests."""
    return deepcopy(AGGREGATIONS_CONFIG)


@pytest.fixture()
def queries_config(app, custom_permission_factory):
    """Queries config for the tests."""
    stats_queries = deepcopy(QUERIES_CONFIG)
    stats_queries.update(
        {
            "test-query": {
                "cls": CustomQuery,
                "params": {
                    "index": "stats-file-download",
                    "copy_fields": {
                        "bucket_id": "bucket_id",
                    },
                    "required_filters": {
                        "bucket_id": "bucket_id",
                    },
                },
                "permission_factory": custom_permission_factory,
            },
            "test-query2": {
                "cls": CustomQuery,
                "params": {
                    "index": "stats-file-download",
                    "copy_fields": {
                        "bucket_id": "bucket_id",
                    },
                    "required_filters": {
                        "bucket_id": "bucket_id",
                    },
                },
                "permission_factory": custom_permission_factory,
            },
        }
    )

    # store the original config value
    original_value = app.config.get("STATS_QUERIES")
    app.config["STATS_QUERIES"] = stats_queries
    yield stats_queries
    # set the original value back
    app.config["STATS_QUERIES"] = original_value


@pytest.fixture(scope="module")
def app_config(app_config, db_uri, events_config, aggregations_config):
    """Application configuration."""
    app_config.update(
        {
            "SQLALCHEMY_DATABASE_URI": db_uri,
            "STATS_MQ_EXCHANGE": Exchange(
                "test_events",
                type="direct",
                delivery_mode="transient",  # in-memory queue
                durable=True,
            ),
            "STATS_QUERIES": {},
            "STATS_EVENTS": events_config,
            "STATS_AGGREGATIONS": aggregations_config,
        }
    )
    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return _create_api


@pytest.fixture(scope="function")
def search_clear(search_clear):
    """Clear search indices after test finishes (function scope)."""
    current_search_client.indices.delete(index="*")
    current_search_client.indices.delete_template("*")
    list(current_search.create())
    list(current_search.put_templates())
    yield search_clear
    current_search_client.indices.delete(index="*")
    current_search_client.indices.delete_template("*")


@pytest.fixture()
def db():
    """Recreate db at each test that requires it."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


@pytest.fixture(scope="module")
def app(base_app, search):
    """Invenio application with search only (no db)."""
    yield base_app


@pytest.fixture()
def config_with_index_prefix(app):
    """Add index prefix to the app config."""
    # set the config (store the original value as well just to be sure)
    original_value = app.config.get("SEARCH_INDEX_PREFIX")
    app.config["SEARCH_INDEX_PREFIX"] = "test-"

    yield app.config

    # set the original value back
    app.config["SEARCH_INDEX_PREFIX"] = original_value


@pytest.fixture()
def celery(app):
    """Get queueobject for testing bulk operations."""
    return app.extensions["flask-celeryext"].celery


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


@pytest.fixture()
def dummy_location(db):
    """File system location."""
    tmppath = tempfile.mkdtemp()

    loc = Location(name="testloc", uri=tmppath, default=True)
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


@pytest.fixture()
def objects(bucket):
    """File system location."""
    # Create older versions first
    for key, content in [("LICENSE", b"old license"), ("README.rst", b"old readme")]:
        ObjectVersion.create(bucket, key, stream=BytesIO(content), size=len(content))

    # Create new versions
    objs = []
    for key, content in [("LICENSE", b"license file"), ("README.rst", b"readme file")]:
        objs.append(
            ObjectVersion.create(
                bucket, key, stream=BytesIO(content), size=len(content)
            )
        )

    yield objs


@pytest.fixture(scope="session")
def sequential_ids():
    """Sequential uuids for files."""
    ids = [
        uuid.UUID(("0000000000000000000000000000000" + str(i))[-32:])
        for i in range(100000)
    ]
    yield ids


@pytest.fixture()
def mock_users():
    """Create mock users."""
    mock_auth_user = Mock()
    mock_auth_user.get_id = lambda: "123"
    mock_auth_user.is_authenticated = True

    mock_anon_user = Mock()
    mock_anon_user.is_authenticated = False
    return {"anonymous": mock_anon_user, "authenticated": mock_auth_user}


@pytest.fixture()
def mock_user_ctx(mock_users):
    """Run in a mock authenticated user context."""
    with patch("invenio_stats.utils.current_user", mock_users["authenticated"]):
        yield


@pytest.fixture()
def request_headers():
    """Return request headers for normal user and bot."""
    return {
        "user": {
            "USER_AGENT": "Mozilla/5.0 (Windows NT 6.1; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko)"
            "Chrome/45.0.2454.101 Safari/537.36"
        },
        "robot": {"USER_AGENT": "googlebot"},
        "machine": {"USER_AGENT": "Wget/1.14 (linux-gnu)"},
    }


@pytest.fixture()
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


@pytest.fixture()
def mock_event_queue(app, mock_datetime, request_headers, objects, mock_user_ctx):
    """Create a mock queue containing a few file download events."""
    mock_queue = Mock()
    mock_queue.routing_key = "stats-file-download"
    with patch("datetime.datetime", mock_datetime), app.test_request_context(
        headers=request_headers["user"]
    ):
        events = [
            build_file_unique_id(file_download_event_builder({}, app, objects[0]))
            for idx in range(100)
        ]
        mock_queue.consume.return_value = iter(events)
    # Save the queued events for later tests
    mock_queue.queued_events = deepcopy(events)
    return mock_queue


def generate_events(
    app,
    file_number=5,
    event_number=100,
    robot_event_number=0,
    start_date=datetime.date(2017, 1, 1),
    end_date=datetime.date(2017, 1, 7),
):
    """Queued events for processing tests."""
    current_queues.declare()

    def _unique_ts_gen():
        ts = 0
        while True:
            ts += 1
            yield ts

    def generator_list():
        unique_ts = _unique_ts_gen()
        for file_idx in range(file_number):
            for entry_date in date_range(start_date, end_date):
                file_id = "F000000000000000000000000000000{}".format(file_idx + 1)
                bucket_id = "B000000000000000000000000000000{}".format(file_idx + 1)

                def build_event(is_robot=False):
                    ts = next(unique_ts)
                    return {
                        "timestamp": datetime.datetime.combine(
                            entry_date, datetime.time(minute=ts % 60, second=ts % 60)
                        ).isoformat(),
                        "bucket_id": bucket_id,
                        "file_id": file_id,
                        "file_key": "test.pdf",
                        "size": 9000,
                        "visitor_id": 100,
                        "is_robot": is_robot,
                    }

                for event_idx in range(event_number):
                    yield build_event()
                for event_idx in range(robot_event_number):
                    yield build_event(True)

    mock_queue = Mock()
    mock_queue.consume.return_value = generator_list()
    mock_queue.routing_key = "stats-file-download"

    EventsIndexer(
        mock_queue,
        preprocessors=[build_file_unique_id, anonymize_user],
        double_click_window=0,
    ).run()
    current_search.flush_and_refresh(index="*")


@pytest.fixture()
def indexed_events(app, search_clear, mock_user_ctx, request):
    """Parametrized pre indexed sample events."""
    generate_events(app=app, **request.param)
    yield


@pytest.fixture()
def aggregated_events(app, search_clear, mock_user_ctx, request):
    """Parametrized pre indexed sample events."""
    list(current_search.put_templates(ignore=[400]))
    generate_events(app=app, **request.param)
    run_date = request.param.get("run_date", request.param["end_date"].timetuple()[:3])

    with patch("invenio_stats.aggregations.datetime", mock_date(*run_date)):
        aggregate_events(["file-download-agg"])
    current_search.flush_and_refresh(index="*")
    yield


@pytest.fixture()
def users(app, db):
    """Create users."""
    user1 = create_test_user(email="info@inveniosoftware.org", password="tester")
    user2 = create_test_user(email="info2@inveniosoftware.org", password="tester2")

    user1.allowed_token = Token.create_personal(
        name="allowed_token", user_id=user1.id, scopes=[]
    ).access_token
    user2.allowed_token = Token.create_personal(
        name="allowed_token", user_id=user2.id, scopes=[]
    ).access_token
    return {"authorized": user1, "unauthorized": user2}


def get_deleted_docs(index):
    """Get all deleted docs from an search index."""
    return current_search_client.indices.stats()["indices"][index]["total"]["docs"][
        "deleted"
    ]


def _create_file_download_event(
    timestamp,
    bucket_id="B0000000000000000000000000000001",
    file_id="F0000000000000000000000000000001",
    size=9000,
    file_key="test.pdf",
    visitor_id=100,
    user_id=None,
):
    """Create a file_download event content."""
    doc = {
        "timestamp": datetime.datetime(*timestamp).isoformat(),
        # What:
        "bucket_id": str(bucket_id),
        "file_id": str(file_id),
        "file_key": file_key,
        "size": size,
        "visitor_id": visitor_id,
        "user_id": user_id,
    }
    return build_file_unique_id(doc)


def _create_record_view_event(
    timestamp,
    record_id="R0000000000000000000000000000001",
    pid_type="recid",
    pid_value="1",
    visitor_id=100,
    user_id=None,
):
    """Create a file_download event content."""
    doc = {
        "timestamp": datetime.datetime(*timestamp).isoformat(),
        # What:
        "record_id": record_id,
        "pid_type": pid_type,
        "pid_value": pid_value,
        "visitor_id": visitor_id,
        "user_id": user_id,
    }
    return build_record_unique_id(doc)


@pytest.fixture()
def custom_permission_factory(users):
    """Test denying permission factory."""

    def permission_factory(query_name, params, *args, **kwargs):
        permission_factory.query_name = query_name
        permission_factory.params = params
        from flask_login import current_user

        if current_user.is_authenticated and current_user.id == users["authorized"].id:
            return type("Allow", (), {"can": lambda self: True})()
        return type("Deny", (), {"can": lambda self: False})()

    permission_factory.query_name = None
    permission_factory.params = None
    return permission_factory


@pytest.fixture()
def sample_histogram_query_data():
    """Sample query parameters."""
    yield {
        "mystat": {
            "stat": "bucket-file-download-histogram",
            "params": {
                "start_date": "2017-1-1",
                "end_date": "2017-7-1",
                "interval": "day",
                "bucket_id": "B0000000000000000000000000000001",
                "file_key": "test.pdf",
            },
        }
    }


class CustomQuery:
    """Mock query class."""

    def __init__(self, *args, **kwargs):
        """Mock constructor."""
        pass

    def run(self, *args, **kwargs):
        """Sample response."""
        return {"bucket_id": "test_bucket", "value": 100}
