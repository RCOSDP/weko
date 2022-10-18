# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
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

"""Helper functions for tests."""

from flask import url_for


def sign_up(app, client, email=None, password=None):
    """Register a user."""
    with app.test_request_context():
        register_url = url_for('security.register')

    client.post(register_url, data=dict(
        email=email or app.config['TEST_USER_EMAIL'],
        password=password or app.config['TEST_USER_PASSWORD'],
    ), environ_base={'REMOTE_ADDR': '127.0.0.1'})


def login(app, client, obj = None, email=None, password=None):
    """Log the user in with the test client."""
    with app.test_request_context():
        login_url = url_for('security.login')

    if obj:
        email = obj.email
        password = obj.password_plaintext
        client.post(login_url, data=dict(
            email=email or app.config['TEST_USER_EMAIL'],
            password=password or app.config['TEST_USER_PASSWORD'],
        ))
    else:
        client.post(login_url, data=dict(
            email=email or app.config['TEST_USER_EMAIL'],
            password=password or app.config['TEST_USER_PASSWORD'],
        ))

def logout(app,client):
    with app.test_request_context():
        logout_url = url_for("security.logout")
    client.get(logout_url)
