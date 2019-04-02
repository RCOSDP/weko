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

from elasticsearch import Elasticsearch
from flask import Flask
from flask_babelex import Babel
from flask_mail import Mail
from flask_menu import Menu
from flask_security.utils import encrypt_password
from invenio_access import InvenioAccess
from invenio_access.models import ActionRoles, ActionUsers
from invenio_access.permissions import superuser_access
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import Role, User
from invenio_accounts.views import blueprint as accounts_blueprint
from invenio_admin import InvenioAdmin
from invenio_db import InvenioDB, db
from invenio_indexer import InvenioIndexer
from invenio_indexer.api import RecordIndexer
from invenio_search import InvenioSearch
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database
from weko_admin import WekoAdmin


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.yield_fixture()
def base_app():
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    app_ = Flask(__name__, instance_path=instance_path)

    app_.config.update(
        ACCOUNTS_USE_CELERY=False,
        LOGIN_DISABLED=False,
        SECRET_KEY='SECRET_KEY!#$',
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'sqlite://'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TEST_USER_EMAIL='info@inveniosoftware.org',
        TEST_USER_PASSWORD='uspass123',
        TESTING=True,
        WTF_CSRF_ENABLED=False
    )
    Babel(app_)
    Mail(app_)
    Menu(app_)
    InvenioDB(app_)
    InvenioAccounts(app_)
    app_.register_blueprint(accounts_blueprint)
    InvenioAccess(app_)

    # client = Elasticsearch(hosts=[os.environ.get('ES_HOST', 'localhost')])
    # search = InvenioSearch(app_, client=client)
    # search.register_mappings('records', 'data')
    # InvenioIndexer(app_)
    # RecordIndexer(app_)

    WekoAdmin(app_)
    InvenioAdmin(app_)

    with app_.app_context():
        if str(db.engine.url) != "sqlite://" and \
                not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()
        # list(search.create(ignore=[400]))
        # search.flush_and_refresh('_all')

    yield app_

    with app_.app_context():
        drop_database(str(db.engine.url))
    shutil.rmtree(instance_path)


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app
