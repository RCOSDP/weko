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

"""API tests."""

from flask import url_for
from flask_security import current_user
from helpers import login, sign_up

from weko_user_profiles import current_userprofile


def test_logged_out_user_has_anonymous_profile(app):
    """AnonymousUser should have AnonymousUserProfile."""
    with app.test_request_context():
        profile_url = url_for('invenio_userprofiles.profile')

    with app.test_client() as client:
        resp = client.get(profile_url, follow_redirects=True)
        assert resp.status_code == 200
        assert 'name="login_user_form"' in resp.get_data(as_text=True)
        assert current_user.is_anonymous and \
            current_userprofile.is_anonymous


def test_get_current_userprofile(app):
    """Test get_current_userprofile."""
    with app.test_request_context():
        profile_url = url_for('invenio_userprofiles.profile')

    with app.test_client() as client:
        # Logged in user should have userprofile
        sign_up(app, client)
        login(app, client)
        resp = client.get(profile_url)
        assert 'name="profile_form"' in resp.get_data(as_text=True)
        assert current_userprofile.is_anonymous is False
        assert current_user.id == current_userprofile.user_id
