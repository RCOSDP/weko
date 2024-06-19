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
from os.path import dirname, getsize, join

import pytest
from flask import Flask, request
from flask_iiif.restful import current_iiif
from invenio_access import InvenioAccess
from invenio_accounts import InvenioAccounts
from invenio_db import InvenioDB
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Bucket, Location, ObjectVersion

from invenio_iiif import InvenioIIIFAPI
from invenio_iiif.previewer import blueprint


@pytest.fixture(scope='session')
def image_path():
    """Path to test image.

    The test image was downloaded from Flickr and marked as public domain.
    """
    return join(dirname(__file__), u'image-public-domain.jpg')


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


@pytest.fixture(scope='module')
def create_app():
    """Application factory fixture."""
    def factory(**config):
        app = Flask('testapp')
        app.config.update(
            SERVER_NAME='localhost',
            **config
        )

        InvenioDB(app)
        InvenioAccounts(app)
        InvenioAccess(app)
        InvenioFilesREST(app)
        InvenioIIIFAPI(app)

        app.register_blueprint(blueprint)

        return app
    return factory


@pytest.fixture(autouse=True)
def clear_cache(appctx):
    """Clear cache after each test."""
    current_iiif.cache().flush()


@pytest.fixture(scope='module')
def location_path():
    """Temporary directory for location path."""
    tmppath = tempfile.mkdtemp()
    yield tmppath
    shutil.rmtree(tmppath)


@pytest.fixture(scope='module')
def location(location_path, database):
    """File system locations."""
    loc = Location(
        name='testloc',
        uri=location_path,
        default=True
    )
    database.session.add(loc)
    database.session.commit()
    return loc


@pytest.fixture(scope='module')
def image_object(database, location, image_path):
    """Get ObjectVersion of test image."""
    bucket = Bucket.create()
    database.session.commit()

    with open(image_path, 'rb') as fp:
        obj = ObjectVersion.create(
            bucket, u'test-ünicode.png', stream=fp, size=getsize(image_path)
        )
    database.session.commit()
    return obj


@pytest.fixture(scope='module')
def image_uuid(image_object):
    """Get image UUID (Flask-IIIF term, not actual an UUID)."""
    return u'{}:{}:{}'.format(
        image_object.bucket_id,
        image_object.version_id,
        image_object.key
    )
