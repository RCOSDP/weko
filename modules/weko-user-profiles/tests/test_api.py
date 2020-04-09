# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""API tests."""

from flask import url_for
from flask_security import current_user
from helpers import login, sign_up

from weko_user_profiles import current_userprofile


def test_logged_out_user_has_anonymous_profile(app):
    """Anonymoususer should have AnonymousUserProfile."""
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
