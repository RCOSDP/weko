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

import shutil
import tempfile

# NOTE: Importing weko_records_ui (directly, or indirectly through any of
# its submodules such as .models/.permissions/.utils) pulls in a large graph
# of other WEKO modules (weko_workflow, weko_items_ui, weko_search_ui,
# weko_gridlayout, weko_theme, ...). That graph has a pre-existing circular
# import: weko_workflow.utils imports names from weko_records_ui.utils,
# which itself (transitively, via weko_gridlayout/weko_theme) imports
# weko_workflow.api. If weko_records_ui is the first of the two to start
# importing, weko_records_ui.utils is caught mid-import when
# weko_workflow.utils reaches back into it, and the import fails with
# "cannot import name 'create_onetime_download_url'". This reproduces on
# the unmodified codebase (i.e. it is not caused by this fix) and is simply
# avoided by finishing the import of weko_workflow first, which is what
# invenio's real application factory happens to do via its own entry-point
# ordering. Doing it once here, before any test module imports
# weko_records_ui, keeps every test in this package working.
import weko_workflow  # noqa: F401

import pytest
from flask import Flask
from flask_babelex import Babel
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import Role, User
from invenio_accounts.testutils import create_test_user
from invenio_db import InvenioDB
from invenio_db import db as db_

from weko_records_ui.models import FileOnetimeDownload

#: Role names matching the defaults in weko_records_ui.config.
SUPER_ROLE_NAME = 'System Administrator'
COMMUNITY_ROLE_NAME = 'Community Administrator'


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""
    app_ = Flask('testapp', instance_path=instance_path)
    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        TESTING=True,
    )
    Babel(app_)
    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.fixture()
def full_app(instance_path):
    """Flask application wired up with DB + accounts.

    Used by tests that need a real (SQLAlchemy-backed) User/Role/
    FileOnetimeDownload model layer and a real flask_login current_user,
    e.g. for weko_records_ui.permissions and the onetime-download helpers
    in weko_records_ui.utils/.models. Kept separate from base_app/app above
    so the pre-existing, lightweight tests keep working unmodified.
    """
    app_ = Flask('test_weko_records_ui_db_app', instance_path=instance_path)
    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite://',
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        WEKO_PERMISSION_SUPER_ROLE_USER=[
            SUPER_ROLE_NAME, 'Repository Administrator'],
        WEKO_PERMISSION_ROLE_COMMUNITY=[COMMUNITY_ROLE_NAME],
    )
    Babel(app_)
    InvenioDB(app_)
    InvenioAccounts(app_)
    with app_.app_context():
        yield app_


@pytest.yield_fixture()
def db(full_app):
    """Set up only the DB tables needed by these tests.

    A plain db.create_all() is not usable here: importing weko_workflow
    (see the note above) registers the SQLAlchemy metadata for every model
    in the whole WEKO module graph on the shared invenio_db.db instance,
    and some of those unrelated models are not creatable standalone (e.g.
    anonymous check constraints that need the naming convention of tables
    that will never be created here). So only the tables actually
    exercised by these tests are created/dropped.
    """
    tables = [
        User.__table__,
        Role.__table__,
        db_.metadata.tables['accounts_userrole'],
        FileOnetimeDownload.__table__,
    ]
    db_.metadata.create_all(bind=db_.engine, tables=tables)
    yield db_
    db_.session.remove()
    db_.metadata.drop_all(bind=db_.engine, tables=tables)


@pytest.fixture()
def users(db):
    """A few plain (non-privileged) test users."""
    return {
        'owner': create_test_user(
            email='owner@example.org', password='pass123'),
        'shared': create_test_user(
            email='shared@example.org', password='pass123'),
        'other': create_test_user(
            email='other@example.org', password='pass123'),
    }


@pytest.fixture()
def super_user(db):
    """A user holding the (super) System Administrator role."""
    role = Role(name=SUPER_ROLE_NAME)
    db.session.add(role)
    user = create_test_user(email='super@example.org', password='pass123')
    user.roles.append(role)
    db.session.commit()
    return user


@pytest.fixture()
def community_user(db):
    """A user holding the Community Administrator role."""
    role = Role(name=COMMUNITY_ROLE_NAME)
    db.session.add(role)
    user = create_test_user(
        email='community@example.org', password='pass123')
    user.roles.append(role)
    db.session.commit()
    return user
