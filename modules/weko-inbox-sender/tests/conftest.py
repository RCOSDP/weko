# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Inbox-Sender is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile
import uuid
import json
from os.path import dirname, join

import pytest
from flask import Flask
from flask_babelex import Babel
from helper import create_record
from invenio_accounts import InvenioAccounts
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_records import InvenioRecords
from invenio_records import Record
from invenio_pidstore import InvenioPIDStore
from invenio_accounts.testutils import create_test_user
from sqlalchemy_utils.functions import create_database, database_exists
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidrelations.models import PIDRelation
from invenio_pidrelations.contrib.versioning import PIDVersioning
from weko_inbox_sender import WekoInboxSender
from weko_inbox_sender.views import blueprint
from weko_workflow import WekoWorkflow
from weko_theme import WekoTheme


@pytest.yield_fixture()
def db(app):
    if not database_exists(str(db_.engine.url)) and \
            app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite://':
        create_database(db_.engine.url)
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


@pytest.yield_fixture(scope='session')
def test_data():
    path = 'data/testrecords.json'
    with open(join(dirname(__file__), path)) as fp:
        records = json.load(fp)
    yield records


@pytest.yield_fixture(scope='session')
def test_payload():
    path = 'data/test_payload.json'
    with open(join(dirname(__file__), path)) as fp:
        payload = json.load(fp)
    yield payload


@pytest.yield_fixture(scope='session')
def test_pushdata():
    path = 'data/test_pushdata.json'
    with open(join(dirname(__file__), path)) as fp:
        payload = json.load(fp)
    yield payload


@pytest.yield_fixture()
def test_records(db, test_data):
    result = []
    for r in test_data:
        result.append(create_record(r))
    db.session.commit()
    yield result


@pytest.fixture()
def test_pid(db):
    uuid1 = uuid.uuid4()
    print(uuid1)
    pid1 = PersistentIdentifier.create(
        'recid',
        '1',
        object_type='rec',
        object_uuid=uuid1,
        status=PIDStatus.REGISTERED,
    )
    pid1_p = PersistentIdentifier.create(
        'parent',
        'parent:1',
        object_type='rec',
        object_uuid=uuid1,
        status=PIDStatus.REGISTERED,
    )
    doi1 = PersistentIdentifier.create(
        'doi',
        'https://doi.org',
        object_type='rec',
        object_uuid=uuid1,
        status=PIDStatus.REGISTERED
    )
    uuid1_1 = uuid.uuid4()
    pid1_1 = PersistentIdentifier.create(
        'recid',
        '1.1',
        object_type='rec',
        object_uuid=uuid1_1,
        status=PIDStatus.REGISTERED,
    )
    relation_p0 = PIDRelation.create(pid1_p, pid1, 2)
    relation_p1 = PIDRelation.create(pid1_p, pid1_1, 2)
    print(PersistentIdentifier.get('parent', 'parent:'+str(1)))
    uuid2 = uuid.uuid4()
    pid2 = PersistentIdentifier.create(
        'recid',
        '2',
        object_type='rec',
        object_uuid=uuid2,
        status=PIDStatus.REGISTERED,
    )
    pid2_p = PersistentIdentifier.create(
        'parent',
        'parent:2',
        object_type='rec',
        object_uuid=uuid2,
        status=PIDStatus.REGISTERED,
    )

    relation_p2 = PIDRelation.create(pid2_p, pid2, 2)

    pids = [(pid1, uuid1)]
    db.session.commit()
    yield pids


@pytest.fixture()
def base_app(instance_path):
    app_ = Flask('testapp', instance_path=instance_path)
    app_.config.update(
        THEME_SITEURL='https://test.com',
        SECRET_KEY='CHANGE_ME',
        SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
        SERVER_NAME='localhost:5000',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        TESTING=True,
        PRESERVE_CONTEXT_ON_EXCEPTION=False,
        WEB_HOST="127.0.0.1"
    )
    InvenioAccounts(app_)
    InvenioDB(app_)
    InvenioRecords(app_)
    InvenioPIDStore(app_)
    WekoWorkflow(app_)
    WekoTheme(app_)
    InvenioPIDRelations(app_)

    WekoInboxSender(app_)
    # with app_.app_context():
    #     if str(db.engine.url) != 'sqlite://' and \
    #        not database_exists(str(db.engine.url)):
    #         create_database(str(db.engine.url))
    return app_


@pytest.yield_fixture()
def app(base_app):
    with base_app.app_context():
        yield base_app


@pytest.fixture()
def user():
    return create_test_user(email="test@test.org")


@pytest.fixture(scope='module')
def celery_config():
    """Override pytest-invenio fixture.

    TODO: Remove this fixture if you add Celery support.
    """
    return {}


# @pytest.fixture(scope='module')
# def create_app(instance_path):
#     """Application factory fixture."""
#     def factory(**config):
#         app = Flask('testapp', instance_path=instance_path)
#         app.config.update(**config)
#         Babel(app)
#         WekoInboxSender(app)
#         app.register_blueprint(blueprint)
#         return app
#     return factory
