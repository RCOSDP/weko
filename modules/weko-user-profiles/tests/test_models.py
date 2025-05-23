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

"""Tests for user profile models."""

from invenio_accounts.models import User

from weko_user_profiles import UserProfile, WekoUserProfiles

from tests.test_validators import test_usernames

def test_userprofiles(app):
    """Test UserProfile model."""
    profile = UserProfile()

    # Check the username validator works on the model
    profile.username = test_usernames['valid']
    # with pytest.raises(ValueError):
    #     profile.username = test_usernames['invalid_characters']
    # with pytest.raises(ValueError):
    #     profile.username = test_usernames['invalid_begins_with_number']

    # # Test non-validated attributes
    # profile.first_name = 'Test'
    # profile.last_name = 'User'
    # assert profile.first_name == 'Test'
    # assert profile.last_name == 'User'


def test_profile_updating(base_app,db):
    """Test profile updating."""
    base_app.config.update(USERPROFILES_EXTEND_SECURITY_FORMS=True)
    WekoUserProfiles(base_app)
    app = base_app

    with app.app_context():
        user = User(email='lollorosso', password='test_password')
        db.session.add(user)
        db.session.commit()

        assert user.profile is None

        # profile = UserProfile(
        #     username='Test_User',
        #     full_name='Test T. User'
        # )
        # user.profile = profile
        # user.profile.username = 'Different_Name'
        # assert user.profile.username == 'Different_Name'
        # assert profile.username == 'Different_Name'


def test_case_insensitive_username(app,db):
    """Test case-insensitive uniqueness."""
    with app.app_context():
        with db.session.begin_nested():
            u1 = User(email='test@example.org')
            u2 = User(email='test2@example.org')
            db.session.add(u1, u2)
        profile1 = UserProfile(user=u1, username="INFO")
        profile2 = UserProfile(user=u2, username="info")
        db.session.add(profile1)
        db.session.add(profile2)
        # pytest.raises(IntegrityError, db.session.commit)


def test_case_preserving_username(app,db):
    """Test that username preserves the case."""
    with app.app_context():
        with db.session.begin_nested():
            u1 = User(email='test@example.org')
            db.session.add(u1)
        db.session.add(UserProfile(user=u1, username="InFo"))
        db.session.commit()
        # profile = UserProfile.get_by_username('info')
        # assert profile.username == 'InFo'


def test_delete_cascade(app,db):
    """Test that deletion of user, also removes profile."""
    with app.app_context():
        with db.session.begin_nested():
            u = User(email='test@example.org')
            db.session.add(u)
        p = UserProfile(user=u, username="InFo")
        db.session.add(p)
        db.session.commit()

        assert UserProfile.get_by_userid(u.id) is not None
        db.session.delete(u)
        db.session.commit()

        assert UserProfile.get_by_userid(u.id) is None

# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_models.py::test_create_profile -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_create_profile(app,db):
    """Test that userprofile can be patched using UserAccount constructor."""
    with app.app_context():
        user = User(
            email='test@example.org',
        )
        db.session.add(user)
        db.session.commit()

        user_id = user.id

        profile = UserProfile(user=user, username="test_username")
        # set displayname
        profile.username = "test_displayname"
        db.session.add(profile)
        db.session.commit()

        assert "test_displayname" == UserProfile.get_by_displayname("test_displayname").username
        # patch_user = User(
        #     id=user_id,
        #     email='updated_test@example.org',
        #     profile={'full_name': 'updated_full_name'}
        # )
        # db.session.merge(patch_user)
        # db.session.commit()

        # patch_user = User(
        #     id=user_id,
        #     profile={'username': 'test_username'}
        # )
        # db.session.merge(patch_user)
        # db.session.commit()

        # user = User.query.filter(User.id == user_id).one()
        # assert user.profile.full_name == 'updated_full_name'
        # assert user.email == 'updated_test@example.org'
        # assert user.profile.username == 'test_username'


def test_create_profile_with_null(app,db):
    """Test that creation with empty profile."""
    with app.app_context():
        user = User(
            email='test@example.org',
        )
        db.session.add(user)
        db.session.commit()

        assert user.profile is None
        user_id = user.id

        user = User(
            id=user_id,
            profile=None,
        )
        db.session.merge(user)
        db.session.commit()

        user = User.query.get(user_id)
        assert user.profile is None
