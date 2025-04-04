# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Signpostingserver is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

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
import copy
from os.path import dirname, join

import pytest
from flask import Flask
from flask_babelex import Babel
from utils import create_record
from invenio_accounts import InvenioAccounts
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_records import InvenioRecords
from invenio_records import Record
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore import current_pidstore
from invenio_accounts.testutils import create_test_user
from sqlalchemy_utils.functions import create_database, database_exists
from invenio_records_ui import InvenioRecordsUI

from weko_signpostingserver import WekoSignpostingserver
from weko_signpostingserver.views import blueprint
from weko_workflow import WekoWorkflow


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
    path = 'data/record_data.json'
    with open(join(dirname(__file__), path)) as fp:
        records = json.load(fp)
    yield records


@pytest.yield_fixture()
def test_records(db, test_data):
    result = []
    for r in test_data:
        result.append(create_record(r))
    db.session.commit()
    yield result


@pytest.yield_fixture(scope='session')
def test_link_str():
    path = 'data/link_str.json'
    with open(join(dirname(__file__), path)) as fp:
        data = json.load(fp)
    yield data


@pytest.fixture(scope='module')
def celery_config():
    """Override pytest-invenio fixture.

    TODO: Remove this fixture if you add Celery support.
    """
    return {}


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
        WEB_HOST='test.com',
        OAISERVER_METADATA_FORMATS=oaiserver,
        RECORDS_UI_ENDPOINTS=dict(
            recid_signposting=dict(
                pid_type='recid',
                route='/records/<pid_value>',
                view_imp='weko_signpostingserver.api.requested_signposting',
                methods=['HEAD']
            ),
        ),
    )
    InvenioAccounts(app_)
    InvenioDB(app_)
    InvenioRecords(app_)
    InvenioRecordsUI(app_)
    InvenioPIDStore(app_)
    WekoWorkflow(app_)
    WekoSignpostingserver(app_)
    # with app_.app_context():
    #     if str(db.engine.url) != 'sqlite://' and \
    #        not database_exists(str(db.engine.url)):
    #         create_database(str(db.engine.url))
    return app_


@pytest.yield_fixture()
def app(base_app):
    with base_app.app_context():
        yield base_app


oaiserver = {
    'jpcoar_1.0': {
        'serializer': (
            'weko_schema_ui.utils:dumps_oai_etree', {
                'schema_type': 'jpcoar',
            }
        ),
        'namespace': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/',
        'schema': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/jpcoar_scm.xsd',
    },
    'oai_dc': {
        'serializer': (
            'weko_schema_ui.utils:dumps_oai_etree', {
                'schema_type': 'oai_dc',
            }
        ),
        'namespace': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
        'schema': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
    },
    'ddi': {
        'serializer': (
            'weko_schema_ui.utils:dumps_oai_etree', {
                'schema_type': 'ddi',
            }
        ),
        'namespace': 'ddi:codebook:2_5',
        'schema': 'https://ddialliance.org/Specification'
                  '/DDI-Codebook/2.5/XMLSchema/codebook.xsd',
    },
}

# @pytest.fixture(scope='module')
# def create_app(instance_path):
#     """Application factory fixture."""
#     def factory(**config):
#         app = Flask('testapp', instance_path=instance_path)
#         app.config.update(**config)
#         Babel(app)
#         WekoSignpostingserver(app)
#         app.register_blueprint(blueprint)
#         return app
#     return factory
