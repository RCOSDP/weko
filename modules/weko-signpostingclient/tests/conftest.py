# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Signpostingclient is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

from __future__ import absolute_import, print_function

import shutil
import tempfile
from os.path import dirname, join
import json

import pytest
from flask import Flask
from flask_babelex import Babel

from weko_signpostingclient import WekoSignpostingclient
from weko_signpostingclient.views import blueprint


@pytest.yield_fixture(scope='session')
def test_maked_data():
    path = 'data/maked_data.json'
    yield load_data(path)


@pytest.yield_fixture(scope='session')
def test_link_str():
    path = 'data/link_str.json'
    yield load_data(path)['url']


def load_data(path):
    with open(join(dirname(__file__), path)) as fp:
        data = json.load(fp)
    return data


@pytest.fixture
def base_app(instance_path):
    app_ = Flask('testapp', instance_path=instance_path)
    app_.config.update(
        THEME_SITEURL='https://test.com',
        SECRET_KEY='CHANGE_ME',
        SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
        SERVER_NAME='localhost:5000',
        TESTING=True,
        WEB_HOST='http://test.com',
        NGINX_HOST='nginx'
    )

    WekoSignpostingclient(app_)

    return app_


@pytest.yield_fixture()
def app(base_app):
    with base_app.app_context():
        yield base_app


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
#         WekoSignpostingclient(app)
#         app.register_blueprint(blueprint)
#         return app
#     return factory
