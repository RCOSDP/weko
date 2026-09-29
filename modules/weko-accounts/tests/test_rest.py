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

from weko_accounts.errors import VersionNotFoundRESTError, UserAllreadyLoggedInError, \
    InvalidCredentialsError, InvalidLoginRequestError, DisabledUserError


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
    assert res.status_code == InvalidCredentialsError.code
    assert res_data['message'] == InvalidCredentialsError.description
    unknown_user_body = res.get_data()

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
    assert res.status_code == InvalidCredentialsError.code
    assert res_data['message'] == InvalidCredentialsError.description
    # Unknown account and wrong password are indistinguishable
    assert res.get_data() == unknown_user_body

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


# .tox/c1/bin/pytest --cov=weko_accounts tests/test_rest.py::test_WekoLogin_post_invalid_body -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_WekoLogin_post_invalid_body(app, client, users_login):
    """Malformed request bodies are rejected with 400."""
    version = 'v1'
    bodies = [
        None,
        [],
        {},
        {'email': users_login[5]['email']},
        {'password': 'dummy'},
        {'email': users_login[5]['email'], 'password': 1},
        {'email': ['a'], 'password': 'dummy'},
        {'email': '', 'password': ''},
    ]
    for body in bodies:
        res = client.post(
            f'/{version}/login',
            data=json.dumps(body),
            content_type='application/json',
        )
        res_data = json.loads(res.get_data())
        assert res.status_code == InvalidLoginRequestError.code
        assert res_data['message'] == InvalidLoginRequestError.description

    # Body that is not JSON at all
    res = client.post(
        f'/{version}/login',
        data='not json',
        content_type='application/json',
    )
    assert res.status_code == InvalidLoginRequestError.code


# .tox/c1/bin/pytest --cov=weko_accounts tests/test_rest.py::test_WekoAccountsREST_limiter -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_WekoAccountsREST_limiter(instance_path):
    """Only the login API of the REST application is rate limited."""
    import os

    from flask import Flask
    from invenio_db import db as db_
    from weko_accounts import WekoAccountsREST
    from weko_accounts.utils import login_limiter

    app_ = Flask('testapi', instance_path=instance_path)
    app_.config.update(
        WEKO_API_LIMIT_RATE_DEFAULT=['2 per minute'],
        # the teardown of the REST blueprint commits the db session.
        # sqlite is not used, because invenio-db registers sqlite settings
        # on every engine and breaks the other tests
        SQLALCHEMY_DATABASE_URI=os.getenv(
            'SQLALCHEMY_DATABASE_URI',
            'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db_.init_app(app_)
    # Flask-Limiter registers the limit every time as_view() applies the
    # decorator, so the limits of the apps made by the other tests pile up.
    # A real process makes the REST application only once.
    login_limiter._dynamic_route_limits.clear()
    before = len(app_.before_request_funcs.get(None, []))
    ext = WekoAccountsREST(app_)

    # the shared limiter, whose default limits apply to every endpoint,
    # is not initialized on the REST application
    assert app_.extensions.get('limiter') is login_limiter
    after = len(app_.before_request_funcs.get(None, []))
    assert after == before + 1

    # Initializing again on the same app does not register the hook twice
    ext.init_limiter(app_)
    assert len(app_.before_request_funcs.get(None, [])) == after

    @app_.route('/other')
    def other():
        return 'ok'

    login_limiter.reset()
    with app_.test_client() as c:
        # the login API is limited by WEKO_API_LIMIT_RATE_DEFAULT
        codes = [c.post('/v1/login', data='x',
                        content_type='application/json').status_code
                 for _ in range(3)]
        assert codes[:2] == [InvalidLoginRequestError.code] * 2
        assert codes[2] == 429

        # other endpoints are not limited
        assert all(c.get('/other').status_code == 200 for _ in range(5))


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
