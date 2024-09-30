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
from mock import patch

from flask import _request_ctx_stack, Flask, current_app, url_for, session

from invenio_i18n.ext import current_i18n

from weko_admin import WekoAdmin

from weko_admin.models import AdminLangSettings, SessionLifetime

from tests.helpers import login, logout

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

# .tox/c1/bin/pytest --cov=weko_admin tests/test_weko_admin.py::test_role_has_access -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_role_has_access(app, users):
    admin = WekoAdmin(app)
    with app.test_request_context():
        with app.test_client() as client:
            # raise Exception
            with patch("weko_admin.ext.db.session.query", side_effect=Exception("test_error")):
                result = admin.role_has_access()
                assert result == False
            
            login(client,users[0]["obj"])
            result = admin.role_has_access()
            assert result == True
            logout(client)
            
            login(client,users[1]["obj"])
            result = admin.role_has_access()
            assert result == False
            logout(client)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_weko_admin.py::test_is_accessible_to_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_is_accessible_to_role(app, db, users,mocker):
    admin = WekoAdmin(app)
    with app.test_client() as client:
        login(client,users[0]["obj"])
        assert current_app.extensions["admin"][0]._views[0].is_accessible.__name__ == "role_has_access"
        assert current_app.extensions["admin"][0]._views[0].is_visible.func.__name__ == "role_has_access"
        assert current_app.extensions["admin"][0]._views[0].is_visible.args[0] == "inclusionrequest"
        
        res = client.get("/ping")
        
# .tox/c1/bin/pytest --cov=weko_admin tests/test_weko_admin.py::test_set_default_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_set_default_language(app, db, users):
    admin = WekoAdmin(app)
    url = url_for('security.login')
    user = users[0]["obj"]
    email = user.email
    password = user.password_plaintext
    data = dict(
        email=email,
        password=password
    )
    with app.test_client() as client:
        # registered_language is []
        client.post(url,data=data)
        
        # registered_language is not []
        en = AdminLangSettings(
            lang_code="en",
            lang_name="English",
            is_registered=True,
            sequence=1,
            is_active=True
        )
        db.session.add(en)
        db.session.commit()
        client.post(url,data=data)
        
        # selected_language in session
        with client.session_transaction() as session:
            session["selected_language"] = "en"
        client.post(url,data=data,headers={"Accept-Language":"ja"})
        
        # path is /ping
        res = client.get("/ping")
    # ctx is exist, ctx has babel_locale
    with app.test_request_context(url):
        with app.test_client() as client:
            current_i18n.locale
            app.preprocess_request()

# .tox/c1/bin/pytest --cov=weko_admin tests/test_weko_admin.py::test_make_session_permanent -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_make_session_permanent(app,db,users):
    admin = WekoAdmin(app)
    target_method = app.before_first_request_funcs[2]
    with app.test_request_context("/test_path"):
        # SessionLifetime is None
        target_method()
        sl = SessionLifetime.query.filter_by().first()
        # SessionLifetime is not None
        assert sl.lifetime == 60
        target_method()
        
    # path is /ping
    with app.test_request_context("/ping"):
        target_method()

    # path is /admin/items/import/
    with app.test_request_context("/admin/items/import/"):
        target_method()
