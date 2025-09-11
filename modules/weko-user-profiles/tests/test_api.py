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

import pytz
from datetime import datetime, timezone
from mock import patch

from flask import url_for,g,current_app
from flask_login.utils import login_user

# def test_logged_out_user_has_anonymous_profile(app):
#     """Anonymoususer should have AnonymousUserProfile."""
#     with app.test_request_context():
#         profile_url = url_for('invenio_userprofiles.profile')

from weko_user_profiles.api import _get_current_userprofile, localize_time
from weko_user_profiles.models import AnonymousUserProfile,UserProfile


#def test_logged_out_user_has_anonymous_profile(app):
#    """Anonymoususer should have AnonymousUserProfile."""
#    with app.test_request_context():
#        profile_url = url_for('weko_user_profiles.profile')
#
#    with app.test_client() as client:
#        resp = client.get(profile_url, follow_redirects=True)
#        assert resp.status_code == 200
#        assert 'name="login_user_form"' in resp.get_data(as_text=True)
#        assert current_user.is_anonymous and \
#            current_userprofile.is_anonymous

# def _get_current_userprofile()
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_api.py::test_get_current_userprofile -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_get_current_userprofile(req_context,db,users):
    # is anonymous
    result = _get_current_userprofile()
    assert type(_get_current_userprofile()) == AnonymousUserProfile
    
    # not exist profile
    user1 = users[0]
    login_user(user1["obj"])
    result = _get_current_userprofile()
    assert result.user_id == user1["id"]
    assert g.userprofile.user_id == user1["id"]
    
    # exist profile
    user2 = users[1]
    user_profile = UserProfile(user_id=int(user2["id"]))
    db.session.add(user_profile)
    db.session.commit()
    g.userprofile=user_profile
    result = _get_current_userprofile()
    assert result.user_id == user2["id"]
    assert g.userprofile.user_id == user2["id"]


# def localize_time(dtime):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_api.py::test_localize_time -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_localize_time(req_context,db,users,user_profiles,mocker):
    dtime = datetime(2022,10,1,1,2,3,4)
    
    # exist current_userprofile
    mocker.patch("weko_user_profiles.api._get_current_userprofile",return_value=user_profiles[0])
    result = localize_time(dtime)
    assert result == datetime(2022,10,1,10,2,3,4,
                              tzinfo=pytz.timezone('Etc/GMT-9'))
    
    # not exist current_userprofile
    current_app.config.update(
        BABEL_DEFAULT_TIMEZONE="Asia/Shanghai"
    )
    mocker.patch("weko_user_profiles.api._get_current_userprofile",return_value=None)
    result = localize_time(dtime)
    
    #assert result == datetime(2022,10,1,)
    assert result == datetime(2022,10,1,1,2,3,4,
                              tzinfo=timezone.utc)
    
    # not exist current_userprofile and config
    current_app.config.pop("BABEL_DEFAULT_TIMEZONE")
    result = localize_time(dtime)
    assert result == datetime(2022,10,1,1,2,3,4,
                              tzinfo=timezone.utc)
    
    # raise BaseException
    with patch("weko_user_profiles.api._get_current_userprofile",side_effect=BaseException):
        result = localize_time(dtime)
        assert result == datetime(2022,10,1,1,2,3,4,
                                  tzinfo=timezone.utc)


#def test_get_current_userprofile(app):
#    """Test get_current_userprofile."""
#    with app.test_request_context():
#        profile_url = url_for('weko_user_profiles.profile')
#
#
#    with app.test_client() as client:
#        # Logged in user should have userprofile
#        sign_up(app, client)
#        login(app, client)
#        resp = client.get(profile_url)
#        assert 'name="profile_form"' in resp.get_data(as_text=True)
#        assert current_userprofile.is_anonymous is False
#        assert current_user.id == current_userprofile.user_id
        
