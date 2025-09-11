# -*- coding: utf-8 -*-
#
# Copyright (C) 2018, 2019 Esteban J. G. Gabancho.
#
# Invenio-S3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Pytest configuration."""
from __future__ import absolute_import, print_function

import hashlib
import os
import shutil
import tempfile

import boto3
import pytest
from flask import Flask, current_app
from invenio_app.factory import create_api
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_db.utils import drop_alembic_version_table
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Location
from moto import mock_s3
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_s3 import InvenioS3, S3FSFileStorage


@pytest.fixture(scope='module')
def app_config(app_config):
    """Customize application configuration."""
    app_config[
        'FILES_REST_STORAGE_FACTORY'] = 'invenio_s3.s3fs_storage_factory'
    app_config['S3_ENDPOINT_URL'] = None

    app_config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI',
                                           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest')
    app_config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app_config['TESTING'] = True
    app_config['S3_ACCESS_KEY_ID'] = 'test'
    app_config['S3_SECRET_ACCESS_KEY'] = 'test'
    app_config['S3_DEFAULT_BLOCK_SIZE'] = 1024  # 1 KB
    app_config['S3_MAXIMUM_NUMBER_OF_PARTS'] = 10
    return app_config


@pytest.fixture(scope='module')
def create_app():
    """Application factory fixture."""
    def factory(**config):
        app = Flask('testapp')
        app.config.update(**config)

        InvenioDB(app)
        InvenioFilesREST(app)
        InvenioS3(app)

        return app

    return factory

@pytest.fixture(scope='module')
def base_app():
    """Flask application fixture."""
    app = Flask('testapp')

    app.config.update(
    FILES_REST_STORAGE_FACTORY='invenio_s3:s3_storage_factory',
    S3_ENDPOINT_URL=None,
    S3_ACCESS_KEY_ID= '',
    S3_SECRET_ACCESS_KEY = '',
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI',
                                           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
    SQLALCHEMY_TRACK_MODIFICATIONS = True,
    TESTING = True
    )

    InvenioDB(app)
    InvenioFilesREST(app)
    InvenioS3(app)

    return app

@pytest.yield_fixture(scope='module')
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture(scope='module')
def database(app):
    """Get setup database."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()
    drop_alembic_version_table()

@pytest.fixture(scope='module')
def location_path():
    """Temporary directory for location path."""
    tmppath = tempfile.mkdtemp()
    yield str(tmppath)
    shutil.rmtree(tmppath)


@pytest.fixture(scope='module')
def location(location_path, database):
    """File system locations."""
    loc = Location(
        name='testloc',
        uri=location_path,
        default=True,
        type='s3',
        access_key='',
        secret_key='',
        s3_endpoint_url="https://s3.amazonaws.com",
        s3_send_file_directly=True,
        s3_maximum_number_of_parts=1000,
        s3_default_block_size=10*1024*1024,
        s3_url_expiration=3600
    )
    database.session.add(loc)
    database.session.commit()
    return loc

@pytest.fixture(scope='function')
def s3_bucket(app):
    """S3 bucket fixture."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'test'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
    with mock_s3():
        session = boto3.Session(
            aws_access_key_id='test',
            aws_secret_access_key='test',
        )
        s3 = session.resource('s3')
        bucket = s3.create_bucket(Bucket='test_invenio_s3')

        yield bucket

        for obj in bucket.objects.all():
            obj.delete()
        bucket.delete()


@pytest.fixture(scope='function')
def s3fs_testpath(s3_bucket):
    """S3 test path."""
    return 's3://{}/path/to/data'.format(s3_bucket.name)


@pytest.fixture(scope='function')
def s3fs(s3_bucket, s3fs_testpath, location):
    """Instance of S3FSFileStorage."""
    s3_storage = S3FSFileStorage(
        s3fs_testpath,
        size=0,
        modified=None,
        clean_dir=True,
        location=location
    )
    return s3_storage


@pytest.fixture
def file_instance_mock(s3fs_testpath):
    """Mock of a file instance."""
    class FileInstance(object):
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    return FileInstance(
        id='deadbeef-65bd-4d9b-93e2-ec88cc59aec5',
        uri=s3fs_testpath,
        size=4,
        updated=None)


@pytest.fixture()
def get_md5():
    """Get MD5 of data."""
    def inner(data, prefix=True):
        m = hashlib.md5()
        m.update(data)
        return "md5:{0}".format(m.hexdigest()) if prefix else m.hexdigest()

    return inner
