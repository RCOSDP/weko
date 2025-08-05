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

"""Module tests foe weko-accounts."""

from flask import Flask
from flask_security import Security, SQLAlchemyUserDatastore
from unittest.mock import patch
from invenio_accounts.models import User, Role
from weko_accounts import WekoAccounts


def test_version():
    """Test version import."""
    from weko_accounts import __version__
    assert __version__

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_weko_accounts.py::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_init():
    """Test extension initialization."""
    with patch('weko_accounts.ext.WekoAccounts.init_login'):
        app = Flask('testapp')
        ext = WekoAccounts(app)
        assert 'weko-accounts' in app.extensions

        app = Flask('testapp')
        ext = WekoAccounts()
        assert 'weko-accounts' not in app.extensions
        ext.init_app(app)
        assert 'weko-accounts' in app.extensions

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_weko_accounts.py::test_init_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_init_login(db, users):
    app = Flask('testapp')
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)

    with app.app_context():
        accounts = WekoAccounts()
        with patch.object(security._state, 'login_context_processor') as mock_lcp:
            accounts.init_login(app)
            mock_lcp.assert_called()

def test_view(app,session_time):
    """
    Test view.

    :param app: The flask application.
    """
    WekoAccounts(app)
    with app.test_client() as client:
        from flask import url_for
        url = url_for("weko_accounts.index")
        res = client.get(url)
        assert res.status_code == 200
        assert 'Welcome to WEKO-Accounts' in str(res.data)
