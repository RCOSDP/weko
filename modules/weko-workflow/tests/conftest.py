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
from flask_menu import Menu
from invenio_accounts import InvenioAccounts
from invenio_accounts.views.settings import blueprint as invenio_accounts_blueprint
from invenio_db import InvenioDB
from weko_workflow import WekoWorkflow
from weko_workflow.views import blueprint as weko_workflow_blueprint


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
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI', 'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/invenio'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        ACCOUNTS_USERINFO_HEADERS=True,
    )
    app_.testing = True
    Babel(app_)
    Menu(app_)
    InvenioAccounts(app_)
    InvenioDB(app_)
    WekoWorkflow(app_)
    app_.register_blueprint(invenio_accounts_blueprint)
    app_.register_blueprint(weko_workflow_blueprint)
    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app
