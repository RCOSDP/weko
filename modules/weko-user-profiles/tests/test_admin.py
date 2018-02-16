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

from flask import Flask, url_for
from flask.ext.admin import Admin
from invenio_admin import InvenioAdmin
from invenio_db import db

from weko_user_profiles import WekoUserProfiles
from weko_user_profiles.admin import UserProfileView, user_profile_adminview


def test_admin(app):
    """Test flask-admin interace."""
    WekoUserProfiles(app)

    assert isinstance(user_profile_adminview, dict)

    assert 'model' in user_profile_adminview
    assert 'modelview' in user_profile_adminview

    admin = Admin(app, name="Test")

    user_model = user_profile_adminview.pop('model')
    user_view = user_profile_adminview.pop('modelview')
    admin.add_view(user_view(user_model, db.session,
                             **user_profile_adminview))

    with app.test_request_context():
        request_url = url_for('userprofile.index_view')

    with app.app_context():
        with app.test_client() as client:
            res = client.get(
                request_url,
                follow_redirects=True
            )
            assert res.status_code == 200
            assert b'Username' in (res.get_data())
            assert b'Full Name' in (res.get_data())
