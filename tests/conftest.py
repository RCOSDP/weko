# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""WEKO3 pytest docstring."""

import os

import pytest
from pytest_invenio.fixtures import app, app_config


# need to init this fixture to create app,
# please refer to:
# invenio_app.factory.create_app,
# invenio_app.factory.create_ui
# invenio_app.factory.create_api
# for difference purposes
# please also refer to pytest_invenio.fixtures.app to get
# idea why we need this fixture
@pytest.fixture(scope='module')
def create_app():
    """Create_app."""
    from invenio_app.factory import create_ui

    print("Inside parent")
    return create_ui


# customize the "app_config" from the pytest_invenio.fixtures for our purpose
@pytest.fixture(scope='module')
def app_config(app_config):
    """App_config."""
    app_config['ACCOUNTS_USE_CELERY'] = False
    app_config['LOGIN_DISABLED'] = False
    app_config['SECRET_KEY'] = 'long_nguyen'
    app_config[
        'SQLALCHEMY_DATABASE_URI'] = \
        'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/test'
    app_config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app_config['SQLALCHEMY_ECHO'] = False
    app_config['TEST_USER_EMAIL'] = 'test_user@example.com'
    app_config['TEST_USER_PASSWORD'] = 'test_password'
    app_config['TESTING'] = True
    app_config['WTF_CSRF_ENABLED'] = False
    app_config['DEBUG'] = False
    app_config['SEARCH_INDEX_PREFIX'] = 'test-tenant123'

    return app_config


@pytest.fixture(scope='module')
def client(app):
    """Client."""
    with app.test_client() as client:
        return client


@pytest.fixture
def full_record():
    """Full record fixture."""
    record = {'item_1574156725144': {'subitem_usage_location': 'sage location',
                                     'pubdate': '2019-12-08',
                                     '$schema': '/items/jsonschema/19',
                                     'title': 'username'}}

    return record
