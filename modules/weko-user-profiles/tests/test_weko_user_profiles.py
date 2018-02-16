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

"""Module tests."""

import pytest
from flask import Flask
from flask_babelex import Babel
from flask_mail import Mail
from flask_menu import Menu
from invenio_accounts import InvenioAccounts
from invenio_db import InvenioDB, db

from weko_user_profiles import WekoUserProfiles


def test_version():
    """Test version import."""
    from weko_user_profiles import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    app.config.update(
        ACCOUNTS_USE_CELERY=False
    )
    Babel(app)
    Mail(app)
    Menu(app)
    InvenioDB(app)
    InvenioAccounts(app)
    ext = WekoUserProfiles(app)
    assert 'weko-user-profiles' in app.extensions

    app = Flask('testapp')
    app.config.update(
        ACCOUNTS_USE_CELERY=False
    )
    Babel(app)
    Mail(app)
    Menu(app)
    InvenioDB(app)
    InvenioAccounts(app)
    ext = WekoUserProfiles()
    assert 'weko-user-profiles' not in app.extensions
    ext.init_app(app)
    assert 'weko-user-profiles' in app.extensions


def test_alembic(app):
    """Test alembic recipes."""
    ext = app.extensions['invenio-db']

    with app.app_context():
        if db.engine.name == 'sqlite':
            raise pytest.skip('Upgrades are not supported on SQLite.')

        assert not ext.alembic.compare_metadata()
        db.drop_all()
        ext.alembic.upgrade()

        assert not ext.alembic.compare_metadata()
        ext.alembic.downgrade(target='96e796392533')
        ext.alembic.upgrade()

        assert not ext.alembic.compare_metadata()
        ext.alembic.downgrade(target='96e796392533')
