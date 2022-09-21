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

"""Module tests for weko admin."""

import random
from datetime import timedelta

from flask import Flask, current_app, url_for

from weko_admin import WekoAdmin


def test_version():
    """Test version import."""
    from weko_admin import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testwekoadmin_app')
    ext = WekoAdmin(app)
    assert 'weko-admin' in app.extensions

    app = Flask('testapp')
    ext = WekoAdmin()
    assert 'weko-admin' not in app.extensions
    ext.init_app(app)
    assert 'weko-admin' in app.extensions


def test_view(app, db):
    """
    Test view.

    :param app: The flask application.
    """
    WekoAdmin(app)
    with app.test_client() as client:
        hello_url = url_for('weko_admin.lifetime')
        res = client.get(hello_url)
        code = res.status_code
        assert code == 200 or code == 301 or code == 302
        if res.status_code == 200:
            assert 'lifetimeRadios' in str(res.data)


def test_set_lifetime(app, db):
    """Test set lifetime."""
    valid_time = (15, 30, 45, 60, 180, 360, 720, 1440)
    set_time = random.choice(valid_time)
    WekoAdmin(app)
    with app.test_client() as client:
        hello_url = url_for('weko_admin.set_lifetime', minutes=set_time)
        res = client.get(hello_url)
        assert res.status_code == 200
        assert 'Session lifetime was updated' in str(res.data)
        assert app.permanent_session_lifetime.seconds == timedelta(
            minutes=int(set_time)).seconds
