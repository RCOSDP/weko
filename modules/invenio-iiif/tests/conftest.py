# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import shutil
import tempfile
import os
from os.path import dirname, getsize, join

import pytest
from flask import Flask, request
from flask_babelex import Babel
from flask_mail import Mail
from flask_menu import Menu
from flask_iiif.restful import current_iiif
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from invenio_access import InvenioAccess
from invenio_accounts import InvenioAccounts
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_i18n import InvenioI18N

from invenio_iiif import InvenioIIIFAPI, InvenioIIIF
from invenio_iiif.previewer import blueprint

from tests.helpers import json_data, create_record

@pytest.fixture()
def image_path():
    """Path to test image.

    The test image was downloaded from Flickr and marked as public domain.
    """
    return join(dirname(__file__), u'data/image-public-domain.jpg')

@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)

@pytest.fixture()
def base_app(instance_path):
    app_ = Flask('test_invenio_iiif_app', instance_path=instance_path)
    app_.config.update(
        TESTING=True,
        SERVER_NAME='test_server',
        ACCOUNTS_USE_CELERY=False,
        SECRET_KEY='SECRET_KEY',
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #      'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                         'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        SEARCH_UI_SEARCH_INDEX="test-search-weko",
        WEKO_AUTHORS_ES_INDEX_NAME="test-weko-authors",
        INDEXER_DEFAULT_DOCTYPE="item-v1.0.0",
        INDEXER_FILE_DOC_TYPE="content",
        PRESERVE_CONTEXT_ON_EXCEPTION = False,
        THEME_SITEURL = 'https://localhost',
    )
    app_.login_manager = dict(_login_disabled=True)
    Babel(app_)
    InvenioI18N(app_)
    InvenioDB(app_)
    Mail(app_)
    Menu(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioFilesREST(app_)
    InvenioIIIF(app_)
    InvenioIIIFAPI(app_)
    
    app_.register_blueprint(blueprint)
    
    yield app_
    
@pytest.yield_fixture()
def app(base_app):
    
    with base_app.app_context():
        yield base_app

@pytest.yield_fixture()
def client(app):
    with app.test_client() as client:
        yield client
        
@pytest.yield_fixture()
def db(app):
    # if not database_exists(str(db_.engine.url)) and \
    #         app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite://':
    #     create_database(db_.engine.url)
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


@pytest.fixture(scope='module')
def permission_factory():
    """Permission factory that allow access based on header value."""
    def factory(obj, action):
        class Permission(object):
            def can(self):
                return request.headers.get('Authorization') != 'deny'
        return Permission()
    return factory


@pytest.fixture(scope='module')
def app_config(app_config, permission_factory):
    """Customize application configuration."""
    app_config['FILES_REST_PERMISSION_FACTORY'] = permission_factory
    app_config['PREVIEWER_ABSTRACT_TEMPLATE'] = 'invenio_iiif/base.html'
    return app_config


@pytest.fixture(autouse=True)
def clear_cache(app):
    """Clear cache after each test."""
    current_iiif.cache().flush()

@pytest.fixture()
def location(app, db, instance_path):
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=instance_path, default=True)
        db.session.add(loc)
    db.session.commit()
    return loc


@pytest.fixture()
def records(db,location):
    record_data = json_data("data/test_records.json")
    item_data = json_data("data/test_items.json")
    
    record_num = len(record_data)
    result = []
    for d in range(record_num):
        result.append(create_record(record_data[d], item_data[d]))
        db.session.commit()

    yield result


@pytest.fixture()
def add_file(db, location):
    def factory(record, contents=b'test example', filename="generic_file.txt"):
        b = Bucket.create()
        r = RecordsBuckets.create(bucket=b, record=record.model)
        ObjectVersion.create(b,filename)
        stream = BytesIO(contents)
        record.files[filename] = stream
        record.files.dumps()
        record.commit()
        db.session.commit()
        return b,r
    return factory


@pytest.fixture()
def image_object(db, location, image_path):
    bucket = Bucket.create()
    db.session.commit()

    with open(image_path, 'rb') as fp:
        obj = ObjectVersion.create(
            bucket, u'test-ünicode.png', stream=fp, size=getsize(image_path)
        )
    db.session.commit()
    return obj

@pytest.fixture()
def image_uuid(image_object):
    """Get image UUID (Flask-IIIF term, not actual an UUID)."""
    return u'{}:{}:{}'.format(
        image_object.bucket_id,
        image_object.version_id,
        image_object.key
    )
