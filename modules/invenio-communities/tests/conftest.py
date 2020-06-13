# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile

import pytest
from flask import Flask
from flask_babelex import Babel
from flask_celeryext import FlaskCeleryExt
from flask_menu import Menu
from invenio_accounts import InvenioAccounts
from invenio_accounts.testutils import create_test_user
from invenio_assets import InvenioAssets
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_indexer import InvenioIndexer
from invenio_mail import InvenioMail
from invenio_oaiserver import InvenioOAIServer
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from invenio_communities import InvenioCommunities
from invenio_communities.models import Community
from invenio_communities.views.api import blueprint as api_blueprint
from invenio_communities.views.ui import blueprint as ui_blueprint


@pytest.yield_fixture()
def app(request):
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    app = Flask('testapp', instance_path=instance_path)
    app.config.update(
        TESTING=True,
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        COMMUNITIES_MAIL_ENABLED=False,
        SECRET_KEY='CHANGE_ME',
        SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SEARCH_ELASTIC_HOSTS=os.environ.get(
            'SEARCH_ELASTIC_HOSTS', None),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        OAISERVER_REGISTER_RECORD_SIGNALS=True,
        OAISERVER_REGISTER_SET_SIGNALS=False,
        OAISERVER_ID_PREFIX='oai:localhost:recid/',
        SERVER_NAME='inveniosoftware.org',
        THEME_SITEURL='https://inveniosoftware.org',
        MAIL_SUPPRESS_SEND=True,
    )
    FlaskCeleryExt(app)
    Menu(app)
    Babel(app)
    InvenioDB(app)
    InvenioAccounts(app)
    InvenioAssets(app)
    InvenioSearch(app)
    InvenioRecords(app)
    InvenioIndexer(app)
    InvenioOAIServer(app)
    InvenioCommunities(app)
    InvenioMail(app)

    app.register_blueprint(ui_blueprint)
    app.register_blueprint(api_blueprint, url_prefix='/api/communities')

    with app.app_context():
        yield app

    shutil.rmtree(instance_path)


@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)) and \
            app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite://':
        create_database(db_.engine.url)
    db_.create_all()

    yield db_

    db_.session.remove()
    db_.session.close()
    if str(db_.engine.url) != 'sqlite://':
        drop_database(str(db_.engine.url))


@pytest.fixture()
def user():
    """Create a example user."""
    return create_test_user('test@test.org')


@pytest.fixture()
def communities(app, db, user):
    """Create some example communities."""
    user1 = db_.session.merge(user)

    comm0 = Community.create(community_id='comm1', user_id=user1.id,
                             title='Title1', description='Description1')
    comm1 = Community.create(community_id='comm2', user_id=user1.id, title='A')
    comm2 = Community.create(community_id='oth3', user_id=user1.id)
    return comm0, comm1, comm2


@pytest.yield_fixture()
def disable_request_email(app):
    """Fixture for disabling request emails."""
    orig = app.config['COMMUNITIES_MAIL_ENABLED']
    app.config['COMMUNITIES_MAIL_ENABLED'] = False
    yield
    app.config['COMMUNITIES_MAIL_ENABLED'] = orig


@pytest.fixture()
def communities_for_filtering(app, db, user):
    """Create some example communities."""
    user1 = db_.session.merge(user)

    comm0 = Community.create(community_id='comm1', user_id=user1.id,
                             title='Test1',
                             description=('Beautiful is better than ugly. '
                                          'Explicit is better than implicit.'))
    comm1 = Community.create(community_id='comm2', user_id=user1.id,
                             title='Testing case 2',
                             description=('Flat is better than nested. '
                                          'Sparse is better than dense.'))
    comm2 = Community.create(community_id='oth3', user_id=user1.id,
                             title='A word about testing',
                             description=('Errors should never pass silently. '
                                          'Unless explicitly silenced.'))
    return comm0, comm1, comm2
