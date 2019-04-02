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

import json

from flask import url_for
from flask_security.utils import hash_password
from invenio_access import InvenioAccess
from invenio_access.models import ActionRoles, ActionUsers
from invenio_access.permissions import superuser_access
from invenio_accounts.models import Role, User
from invenio_db import db

from weko_authors.models import Authors


test_author_dict = {
    'authorIdInfo': [{
        'authorId': 'a1', 'authorIdShowFlg': 'true', 'idType': 'cinii'}],
    'authorNameInfo': [{
        'familyName': 'a1', 'firstName': 'a1', 'fullName': 'a1 a1',
        'language': 'ja-Kana', 'nameFormat': 'familyNmAndNm',
        'nameShowFlg': True}],
    'emailInfo': [{'email': 'a1@a.com'}],
    'gather_flg': 0,
    'id': '\\',
    'pk_id': '12345678'
}


def sign_up(app, client, email=None, password=None):
    """Register a user."""
    with app.test_request_context():
        register_url = url_for('security.register')

    res = client.post(register_url, data=dict(
        email=email or app.config['TEST_USER_EMAIL'],
        password=password or app.config['TEST_USER_PASSWORD'],
    ), environ_base={'REMOTE_ADDR': '127.0.0.1'})


def login(app, client, email=None, password=None):
    """Log the user in with the test client."""
    with app.test_request_context():
        login_url = url_for('security.login')

    res = client.post(login_url, data=dict(
        email=email or app.config['TEST_USER_EMAIL'],
        password=password or app.config['TEST_USER_PASSWORD'],
    ))


def create_admin(app, client, email=None, password=None):
    """Create admin user and give superuser permissions."""
    with app.app_context():
        test_admin = User(
            email=email or app.config['TEST_USER_EMAIL'],
            password=hash_password(password or
                                   app.config['TEST_USER_PASSWORD']),
            active=True
        )
        db.session.add(test_admin)
        db.session.commit()
        db.session.add(ActionUsers.allow(superuser_access, user=test_admin))
        db.session.commit()


def create_test_author():
    """Makes test author dict."""
    test_author = dict()
    test_author['authorIdInfo'] = [dict(
        authorId='a1', authorIdShowFlg='true', idType='cinii'
    )]
    test_author['authorNameInfo'] = [dict(
        familyName='a1', firstName='a1', fullName='a1 a1',
        language='ja-Kana', nameFormat='familyNmAndNm',
        nameShowFlg=True
    )]
    test_author['emailInfo'] = [dict(email='a1@a.com')]
    test_author['gather_flg'] = 0
    test_author['id'] = '\\'
    test_author['pk_id'] = '12345678'
    return test_author


def insert_author(app, db, test_author_data):
    """Inserts test author."""
    test_author = dict(id=test_author_data['pk_id'],
                       json=json.dumps(test_author_data))
    with app.app_context():
        author = Authors(**test_author)
        db.session.add(author)
        db.session.commit()
