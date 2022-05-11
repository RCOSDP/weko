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

"""Pytest for weko admin configuration."""

import os
import shutil
import tempfile

import pytest
from flask import Flask
from flask_babelex import Babel
from flask_mail import Mail
from flask_menu import Menu
from invenio_accounts import InvenioAccounts
from invenio_admin import InvenioAdmin
from invenio_db import InvenioDB, db
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from weko_admin import WekoAdmin
from weko_admin.views import blueprint


@pytest.fixture()
def base_app():
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    app_ = Flask('test_weko_admin_app', instance_path=instance_path)
    app_.config.update(
        ACCOUNTS_USE_CELERY=False,
        LOGIN_DISABLED=False,
        SECRET_KEY='testing_key',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SEARCH_ELASTIC_HOSTS=os.environ.get(
            'SEARCH_ELASTIC_HOSTS', None),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SQLALCHEMY_ECHO=False,
        TEST_USER_EMAIL='test_user@example.com',
        TEST_USER_PASSWORD='test_password',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    app_.testing = True
    app_.login_manager = dict(_login_disabled=True)
    Babel(app_)
    Mail(app_)
    Menu(app_)
    InvenioDB(app_)
    InvenioAccounts(app_)
    InvenioAdmin(app_)
    WekoAdmin(app_)
    app_.register_blueprint(blueprint)

    with app_.app_context():
        if str(db.engine.url) != "sqlite://" \
                and not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()

    yield app_

    with app_.app_context():
        drop_database(str(db.engine.url))
    shutil.rmtree(instance_path)


@pytest.fixture()
def app(base_app):
    """Flask application fixture."""
    return base_app
