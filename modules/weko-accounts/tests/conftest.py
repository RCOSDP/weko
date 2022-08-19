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

"""Pytest for weko-accounts configuration."""

import shutil
import tempfile

import pytest
from flask import Flask
from flask_babelex import Babel
from weko_accounts import WekoAccounts
from weko_accounts.views import blueprint
from invenio_access import InvenioAccess
from invenio_admin import InvenioAdmin
from invenio_i18n import InvenioI18N
from invenio_accounts import InvenioAccounts
from flask_menu import Menu
from invenio_db import InvenioDB
from flask_mail import Mail

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
    InvenioI18N(app_)
    InvenioDB(app_)
    Mail(app_)
    Menu(app_)
    InvenioDB(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioAdmin(app_)
    WekoAccounts(app_)
    app_.register_blueprint(blueprint)
    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app
