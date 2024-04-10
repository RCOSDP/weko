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

from flask import json

from weko_accounts.errors import VersionNotFoundRESTError, UserAllreadyLoggedInError, UserNotFoundError, InvalidPasswordError, DisabledUserError


# .tox/c1/bin/pytest --cov=weko_accounts tests/test_rest.py::test_WekoLogin_post -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_WekoLogin_post(app, client, users_login):
    """Test WekoLogin.post method."""

    version = 'v1'
    invalid_version = 'v0'

    # Invalid version : 400 error
    req_json = {
        'email': users_login[5]['email'],
        'password': users_login[5]['obj'].password_plaintext,
    }
    res = client.post(
        f'/{invalid_version}/login',
        data=json.dumps(req_json),
        content_type='application/json',
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == VersionNotFoundRESTError.code
    assert res_data['message'] == VersionNotFoundRESTError.description

    # Invalid user : 403 error
    req_json = {
        'email': 'dummy',
        'password': users_login[5]['obj'].password_plaintext,
    }
    res = client.post(
        f'/{version}/login',
        data=json.dumps(req_json),
        content_type='application/json',
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == UserNotFoundError.code
    assert res_data['message'] == UserNotFoundError.description

    # Invalid password : 403 error
    req_json = {
        'email': users_login[5]['email'],
        'password': 'dummy',
    }
    res = client.post(
        f'/{version}/login',
        data=json.dumps(req_json),
        content_type='application/json',
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == InvalidPasswordError.code
    assert res_data['message'] == InvalidPasswordError.description

    # Inactive user : 403 error
    req_json = {
        'email': users_login[9]['email'],
        'password': users_login[9]['obj'].password_plaintext,
    }
    res = client.post(
        f'/{version}/login',
        data=json.dumps(req_json),
        content_type='application/json',
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == DisabledUserError.code
    assert res_data['message'] == DisabledUserError.description

    # Normal : 200
    req_json = {
        'email': users_login[5]['email'],
        'password': users_login[5]['obj'].password_plaintext,
    }
    res = client.post(
        f'/{version}/login',
        data=json.dumps(req_json),
        content_type='application/json',
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data['id'] == users_login[5]['id']
    assert res_data['email'] == users_login[5]['email']

    # User is already logged in : 400 error
    req_json = {
        'email': users_login[5]['email'],
        'password': users_login[5]['obj'].password_plaintext,
    }
    res = client.post(
        f'/{version}/login',
        data=json.dumps(req_json),
        content_type='application/json',
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == UserAllreadyLoggedInError.code
    assert res_data['message'] == UserAllreadyLoggedInError.description


# .tox/c1/bin/pytest --cov=weko_accounts tests/test_rest.py::test_WekoLogout_post -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_WekoLogout_post(app, client, users_login):
    """Test WekoLogout.post method."""

    version = 'v1'
    invalid_version = 'v0'

    # Invalid version : 400 error
    res = client.post(
        f'/{invalid_version}/logout',
        data=json.dumps(None),
        content_type='application/json',
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == VersionNotFoundRESTError.code
    assert res_data['message'] == VersionNotFoundRESTError.description

    # Normal : 200
    req_json = {
        'email': users_login[5]['email'],
        'password': users_login[5]['obj'].password_plaintext,
    }
    client.post(
        f'/{version}/login',
        data=json.dumps(req_json),
        content_type='application/json',
    )
    res = client.post(
        f'/{version}/logout',
        data=json.dumps(None),
        content_type='application/json',
    )
    assert res.status_code == 200

    # User is already logged out : 200
    res = client.post(
        f'/{version}/logout',
        data=json.dumps(None),
        content_type='application/json',
    )
    assert res.status_code == 200
