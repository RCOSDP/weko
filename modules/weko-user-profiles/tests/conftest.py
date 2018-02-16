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

"""Pytest configuration."""

import os
import shutil
import tempfile

import pytest
from flask import Flask
from flask_babelex import Babel
from flask_mail import Mail
from flask_menu import Menu
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint as accounts_blueprint
from invenio_db import InvenioDB, db
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from weko_user_profiles import WekoUserProfiles
from weko_user_profiles.views import blueprint_ui_init


@pytest.yield_fixture()
def base_app():
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    base_app = Flask(__name__, instance_path=instance_path)

    base_app.config.update(
        ACCOUNTS_USE_CELERY=False,
        LOGIN_DISABLED=False,
        SECRET_KEY='testing_key',
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'sqlite://'),
        TEST_USER_EMAIL='test_user@example.com',
        TEST_USER_PASSWORD='test_password',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    Babel(base_app)
    Mail(base_app)
    Menu(base_app)
    InvenioDB(base_app)
    InvenioAccounts(base_app)
    base_app.register_blueprint(accounts_blueprint)

    with base_app.app_context():
        if str(db.engine.url) != "sqlite://" and \
                not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()

    yield base_app

    with base_app.app_context():
        drop_database(str(db.engine.url))
    shutil.rmtree(instance_path)


def _init_userprofiles_app(app_):
    """Init UserProfiles modules."""
    WekoUserProfiles(app_)
    app_.register_blueprint(blueprint_ui_init)
    return app_


@pytest.fixture
def app(base_app):
    """Flask application."""
    return _init_userprofiles_app(base_app)


@pytest.fixture
def app_with_csrf(base_app):
    """Flask application with CSRF security enabled."""
    base_app.config.update(
        WTF_CSRF_ENABLED=True,
    )
    return _init_userprofiles_app(base_app)
