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

"""Tests for user profile views."""

import pytest
from flask import url_for, json,make_response, current_app, g, jsonify
from mock import patch
from flask_breadcrumbs import current_breadcrumbs
from flask._compat import text_type
from flask.json import JSONEncoder as BaseEncoder
from flask_security import url_for_security
from flask_menu import current_menu
from flask_login import login_user
from speaklater import _LazyString
from wtforms import StringField, SelectField

from invenio_accounts.models import User
from invenio_accounts.testutils import login_user_via_session

import weko_user_profiles
from weko_user_profiles import WekoUserProfiles
from weko_user_profiles.forms import ProfileForm,EmailProfileForm
from weko_user_profiles.views import (
    blueprint_ui_init, 
    blueprint_api_init,
    userprofile,
    init_common,
    profile_form_factory,
    init_ui
    )

from tests.helpers import login, sign_up

class TestJSONEncoder(BaseEncoder):
    def default(self, o):
        if isinstance(o, _LazyString):
            return text_type(o)

        return BaseEncoder.default(self, o)


def prefix(name, data):
    """Prefix all keys with value."""
    data = {"{0}-{1}".format(name, k): v for (k, v) in data.items()}
    data['submit'] = name
    return data


def test_profile_in_registration(base_app,db):
    """Test accounts registration form."""
    base_app.config.update(USERPROFILES_EXTEND_SECURITY_FORMS=True)
    WekoUserProfiles(base_app)
    base_app.register_blueprint(blueprint_ui_init)
    app = base_app

    with app.test_request_context():
        register_url = url_for_security('register')

    with app.test_client() as client:
        resp = client.get(register_url)
    #     assert 'profile.username' in resp.get_data(as_text=True)
    #     assert 'profile.full_name' in resp.get_data(as_text=True)

    #     data = {
    #         'email': 'test_user@example.com',
    #         'password': 'test_password',
    #         'profile.username': 'TestUser',
    #         'profile.full_name': 'Test C. User',
    #     }
    #     resp = client.post(register_url, data=data, follow_redirects=True)

    # with app.test_request_context():
    #     user = User.query.filter_by(email='test_user@example.com').one()
    #     assert user.profile.username == 'TestUser'
    #     assert user.profile.full_name == 'Test C. User'

    # with app.test_client() as client:
    #     resp = client.get(register_url)
    #     data = {
    #         'email': 'newuser@example.com',
    #         'password': 'test_password',
    #         'profile.username': 'TestUser',
    #         'profile.full_name': 'Same Username',
    #     }
    #     resp = client.post(register_url, data=data)
    #     assert resp.status_code == 200
    #     assert 'profile.username' in resp.get_data(as_text=True)


def test_template_filter(app,db):
    """Test template filter."""
    with app.app_context():
        user = User(email='test@example.com', password='test_password')
        db.session.add(user)
        db.session.commit()


def test_profile_view_not_accessible_without_login(app,register_bp,db):
    """Test the user can't access profile settings page without logging in."""
    with app.test_request_context():
        profile_url = url_for('weko_user_profiles.profile')

    with app.test_client() as client:
        resp = client.get(profile_url, follow_redirects=True)
        assert resp.status_code == 200
        assert 'name="login_user_form"' in str(resp.data)


def test_profile_view(app,register_bp,db):
    """Test the profile view."""
    app.config['USERPROFILES_EMAIL_ENABLED'] = False
    with app.test_request_context():
        profile_url = url_for('weko_user_profiles.profile')

    with app.test_client() as client:
        sign_up(app, client)
        login(app, client)
        # resp = client.get(profile_url)
        # assert resp.status_code == 200
        # assert 'name="profile_form"' in str(resp.data)

        # # Valid submission should work
        # resp = client.post(profile_url, data=prefix('profile', dict(
        #     username=test_usernames['valid'],
        #     full_name='Valid Name', )))

        # assert resp.status_code == 200
        # data = resp.get_data(as_text=True)
        # assert test_usernames['valid'] in data
        # assert 'Valid' in data
        # assert 'Name' in data

        # # Invalid submission should not save data
        # resp = client.post(profile_url, data=prefix('profile', dict(
        #     username=test_usernames['invalid_characters'],
        #     full_name='Valid Name', )))

        # assert resp.status_code == 200
        # assert test_usernames['invalid_characters'] in \
        #     resp.get_data(as_text=True)

        # resp = client.get(profile_url)
        # assert resp.status_code == 200
        # assert test_usernames['valid'] in resp.get_data(as_text=True)

        # # Whitespace should be trimmed
        # client.post(profile_url, data=prefix('profile', dict(
        #     username='{0} '.format(test_usernames['valid']),
        #     full_name='Valid Name ', )))
        # resp = client.get(profile_url)

        # assert resp.status_code == 200
        # data = resp.get_data(as_text=True)
        # assert test_usernames['valid'] in data
        # assert 'Valid Name ' not in data


def test_profile_name_exists(app,register_bp,db):
    """Test the profile view."""
    app.config['USERPROFILES_EMAIL_ENABLED'] = False

    with app.test_request_context():
        profile_url = url_for('weko_user_profiles.profile')

    # Create an existing user
    email1 = 'exiting@example.org'
    password1 = '123456'
    with app.test_client() as client:
        sign_up(app, client, email=email1, password=password1)
        login(app, client, email=email1, password=password1)
    #     assert client.get(profile_url).status_code == 200
    #     resp = client.post(profile_url, data=prefix('profile', dict(
    #         username='existingname', full_name='Valid Name',)))
    #     assert 'has-error' not in resp.get_data(as_text=True)

    # # Create another user and try setting username to same as above user.
    # with app.test_client() as client:
    #     sign_up(app, client)
    #     login(app, client)
    #     resp = client.get(profile_url)
    #     assert resp.status_code == 200

    #     resp = client.post(profile_url, data=prefix('profile', dict(
    #         username='existingname', full_name='Another name',
    #     )))
    #     assert resp.status_code == 200
    #     assert 'Username already exists.' in resp.get_data(as_text=True)

    #     # Now set it to something else and do it twice.
    #     data = prefix('profile', dict(
    #         username='valid', full_name='Another name', ))

    #     resp = client.post(profile_url, data=data)
    #     assert resp.status_code == 200
    #     assert 'has-error' not in resp.get_data(as_text=True)

    #     resp = client.post(profile_url, data=data)
    #     assert resp.status_code == 200
    #     assert 'has-error' not in resp.get_data(as_text=True)


def test_send_verification_form(app,register_bp,db):
    """Test send verification form."""
    mail = app.extensions['mail']

    with app.test_request_context():
        profile_url = url_for('weko_user_profiles.profile')

    with app.test_client() as client:
        sign_up(app, client)
        login(app, client)
        # resp = client.get(profile_url)
        # assert resp.status_code == 200
        # assert 'You have not yet verified your email address' in \
        #     resp.get_data(as_text=True)

        # with mail.record_messages() as outbox:
        #     assert len(outbox) == 0
        #     resp = client.post(profile_url, data=prefix('verification', dict(
        #         send_verification_email='Title'
        #     )))
        #     assert len(outbox) == 1


def test_change_email(app,register_bp,db):
    """Test send verification form."""
    mail = app.extensions['mail']

    with app.test_request_context():
        profile_url = url_for('weko_user_profiles.profile')

    # Create an existing user
    email1 = 'exiting@example.org'
    password1 = '123456'
    with app.test_client() as client:
        sign_up(app, client, email=email1, password=password1)
        login(app, client, email=email1, password=password1)
    #     assert client.get(profile_url).status_code == 200

    # with app.test_client() as client:
    #     sign_up(app, client)
    #     login(app, client)
    #     resp = client.get(profile_url)
    #     assert resp.status_code == 200

    #     data = prefix('profile', dict(
    #         username='test',
    #         full_name='Test User',
    #         email=app.config['TEST_USER_EMAIL'],
    #         email_repeat=app.config['TEST_USER_EMAIL'],
    #     ))

    #     # Test that current_user stops validation of email
    #     client.post(profile_url, data=data)
    #     assert resp.status_code == 200
    #     assert 'has-error' not in resp.get_data(as_text=True)

    #     # Test existing email of another user.
    #     data['profile-email_repeat'] = data['profile-email'] = email1
    #     resp = client.post(profile_url, data=data)
    #     assert 'has-error' in resp.get_data(as_text=True)

    #     # Test empty email
    #     data['profile-email_repeat'] = data['profile-email'] = ''
    #     resp = client.post(profile_url, data=data)
    #     assert 'has-error' in resp.get_data(as_text=True)

    #     # Test not an email
    #     data['profile-email_repeat'] = data['profile-email'] = 'sadfsdfs'
    #     resp = client.post(profile_url, data=data)
    #     assert 'has-error' in resp.get_data(as_text=True)

    #     # Test different emails
    #     data['profile-email_repeat'] = 'typo@example.org'
    #     data['profile-email'] = 'new@example.org'
    #     resp = client.post(profile_url, data=data)
    #     assert 'has-error' in resp.get_data(as_text=True)

    #     # Test whitespace
    #     with mail.record_messages() as outbox:
    #         assert len(outbox) == 0
    #         data['profile-email_repeat'] = data['profile-email'] \
    #         = 'new@ex.org'
    #         resp = client.post(profile_url, data=data)
    #         assert 'has-error' not in resp.get_data(as_text=True)
    #         # Email was sent for email address confirmation.
    #         assert len(outbox) == 1


# def init_common(app):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_views.py::test_init_common -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_init_common(app):
    result = init_common(app)
    app.config.update(
        USERPROFILES_EXTEND_SECURITY_FORMS=True
    )
    result = init_common(app)


# def init_ui(state)
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_views.py::test_init_ui -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_init_ui(app,mocker):
    mock_init = mocker.spy(weko_user_profiles.views,"init_common")
    
    app.register_blueprint(blueprint_ui_init)
    mock_init.assert_called_once()


def test_init_api(app,mocker):
    mock_init = mocker.spy(weko_user_profiles.views,"init_common")
    app.register_blueprint(blueprint_api_init)
    mock_init.assert_called_once()


def test_userprofile(db,users,user_profiles):

    result = userprofile(users[0]["id"])
    assert result._username == "sysadmin"


# def get_profile_info():
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_views.py::test_get_profile_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_get_profile_info(client,app,admin_app,register_bp,users,mocker,user_profiles):
    with patch("sqlalchemy.orm.scoping.scoped_session.remove", return_value=None):
        url = url_for("weko_user_profiles_api_init.get_profile_info")

        res = client.get(url)
        assert json.loads(res.data) == {"positions":"","results":"","error":"'AnonymousUser' object has no attribute 'id'"}

        current_app.config['WEKO_USERPROFILES_POSITION_LIST'] = [('', ''), ('Professor', 'Professor')]
        login(app,client,email=users[0]["email"],password='123456')
        profile_info = {
            "subitem_fullname":"test taro",
            "subitem_displayname":"sysadmin user",
            "subitem_user_name":"sysadmin",
            "subitem_university/institution":"test university",
            "subitem_affiliated_division/department":"test department",
            "subitem_position":"test position",
            "subitem_phone_number":"123-4567",
            "subitem_position(other)":"test other position",
            "subitem_affiliated_institution":[
                {"subitem_affiliated_institution_name":"test institute","subitem_affiliated_institution_position":"test institute position"},
                {"subitem_affiliated_institution_name":"test institute2","subitem_affiliated_institution_position":"test institute position2"},
            ],
            'subitem_mail_address': 'sysadmin@test.org',
        }
        test = {
            "results":profile_info,
            "positions":current_app.config['WEKO_USERPROFILES_POSITION_LIST'],
            "error":""
        }
        mocker.patch("weko_user_profiles.views.get_user_profile_info",return_value=profile_info)
        app.json_encoder = TestJSONEncoder
        res = client.get(url)
        assert json.loads(res.data) == json.loads(jsonify(test).data)


# def profile():
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_views.py::test_profile -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_profile(client,register_bp,users,mocker):
    with patch("sqlalchemy.orm.scoping.scoped_session.remove", return_value=None):
        url = url_for("weko_user_profiles.profile")
        # no login
        res = client.get(url)
        assert res.status_code == 302
        user = User.query.filter_by(email=users[0]["email"]).first()
        mocker.patch("invenio_accounts.models.User.get_id", return_value=users[0]["id"])
        login_user_via_session(client=client,user=user)

        mocker.patch("weko_user_profiles.views.profile_form_factory")
        mocker.patch("weko_user_profiles.views.render_template",return_value=make_response())
        mock_profile = mocker.patch("weko_user_profiles.views.handle_profile_form")
        mock_verification = mocker.patch("weko_user_profiles.views.handle_verification_form")

        # not submit
        client.post(url,data={})
        mock_profile.assert_not_called()
        mock_verification.assert_not_called()

        # submit is profile
        client.post(url,data={"submit":"profile"})
        mock_profile.assert_called_once()

        # submit is verification
        client.post(url,data={"submit":"verification"})
        mock_verification.assert_called_once()

        # check submenu, breadcrumbs
        assert current_menu.submenu("settings.profile").active == True
        assert current_menu.submenu("settings.profile").url == "/account/settings/profile/"
        assert current_menu.submenu("settings.profile").text == '<i class="fa fa-user fa-fw"></i> Profile'
        assert list(map(lambda x:x.url,list(current_breadcrumbs))) == ["#","#","#","/account/settings/profile/"]


# def profile_form_factory():
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_views.py::test_profile_form_factory -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_profile_form_factory(app,req_context,users,user_profiles):
    app.config.update({
        "USERPROFILES_EMAIL_ENABLED": True,
        "WEKO_USERPROFILES_CUSTOMIZE_ENABLED": False
    })
    with app.test_client():
        g.userprofile = user_profiles[0]
        login_user(users[0]["obj"])
        result = profile_form_factory()
        assert type(result) == EmailProfileForm
        assert result.department is None
        assert result.username.data == "sysadmin user"
        app.config.update({
            "USERPROFILES_EMAIL_ENABLED": False
        })
        result = profile_form_factory()
        assert type(result) == ProfileForm
        assert type(result.department) == StringField

    # Case: WEKO_USERPROFILES_CUSTOMIZE_ENABLED = True
    app.config.update({
        "USERPROFILES_EMAIL_ENABLED": True,
        "WEKO_USERPROFILES_CUSTOMIZE_ENABLED": True,
        "WEKO_USERPROFILES_DEFAULT_FIELDS_SETTINGS": {
            "fullname": {"format": "text", "label_name": "Full Name", "visible": True, "options": [''], "order": 1},
            "university": {"format": "text", "label_name": "University", "visible": True, "options": [''], "order": 2},
            "department": {"format": "select", "label_name": "Department", "visible": True, "options": ["test1", "test2"], "order": 3},
            "position": {"format": "text", "label_name": "Position", "visible": True, "options": [''], "order": 4},
        }
    })
    with app.test_client():
        result = profile_form_factory()
        assert type(result) == EmailProfileForm
        assert result.department is None
        assert result.username.data == "sysadmin user"
        app.config.update(
            USERPROFILES_EMAIL_ENABLED=False
        )
        result = profile_form_factory()
        assert type(result) == ProfileForm
        assert type(result.department) == SelectField
