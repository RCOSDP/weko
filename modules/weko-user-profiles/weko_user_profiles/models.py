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

"""Database models for user profiles."""

from invenio_accounts.models import User
from invenio_db import db
from sqlalchemy import event
from sqlalchemy.ext.hybrid import hybrid_property

from weko_admin.models import AdminSettings

from .validators import validate_username


class AnonymousUserProfile:
    """Anonymous user profile."""

    @property
    def is_anonymous(self):
        """Return whether this UserProfile is anonymous."""
        return True


class UserProfile(db.Model):
    """User profile model.

    Stores a username, display name (case sensitive version of username) and a
    full name for a user.
    """

    __tablename__ = 'userprofiles_userprofile'

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(User.id),
        primary_key=True
    )
    """Foreign key to :class:`~invenio_accounts.models.User`."""

    user = db.relationship(
        User, backref=db.backref(
            'profile', uselist=False, cascade='all, delete-orphan')
    )
    """User relationship."""

    _username = db.Column('username', db.String(255), unique=True)
    """Lower-case version of username to assert uniqueness."""

    _displayname = db.Column('displayname', db.String(255))
    """Case preserving version of username."""

    fullname = db.Column(db.String(100), nullable=False, default='')
    """Full name of person."""

    timezone = db.Column(db.String(255), nullable=False, default='')
    """Selected timezone."""

    language = db.Column(db.String(255), nullable=False, default='')
    """Selected language."""

    """University / Institution"""
    university = db.Column('university', db.String(100))

    """Affiliation department / Department"""
    department = db.Column('department', db.String(100))

    """Position"""
    position = db.Column('position', db.String(100))

    """Position"""
    item1 = db.Column('otherPosition', db.String(100))

    """Phone number"""
    item2 = db.Column('phoneNumber', db.String(15))

    """Affiliation institute name 1"""
    """Affiliation institute name (n)"""
    item3 = db.Column('instituteName', db.String(100))

    """Affiliation institute position (n)"""
    item4 = db.Column('institutePosition', db.String(255))

    """Affiliation institute name 2"""
    """Affiliation institute name (n)"""
    item5 = db.Column('instituteName2', db.String(100))

    """Affiliation institute position (n)"""
    item6 = db.Column('institutePosition2', db.String(255))

    """Affiliation institute name 3"""
    """Affiliation institute name (n)"""
    item7 = db.Column('instituteName3', db.String(100))

    """Affiliation institute position (n)"""
    item8 = db.Column('institutePosition3', db.String(255))

    """Affiliation institute name 4"""
    """Affiliation institute name (n)"""
    item9 = db.Column('instituteName4', db.String(100))

    """Affiliation institute position (n)"""
    item10 = db.Column('institutePosition4', db.String(255))

    """Affiliation institute name 5"""
    """Affiliation institute name (n)"""
    item11 = db.Column('instituteName5', db.String(100))

    """Affiliation institute position (n)"""
    item12 = db.Column('institutePosition5', db.String(255))

    item13 = db.Column('item13', db.String(255))

    item14 = db.Column('item14', db.String(255))

    item15 = db.Column('item15', db.String(255))

    item16 = db.Column('item16', db.String(255))

    """s3_endpoint_url"""
    s3_endpoint_url = db.Column('s3_endpoint_url', db.String(128))

    """s3_region_name"""
    s3_region_name = db.Column('s3_region_name', db.String(128))

    """access_key"""
    access_key = db.Column('access_key', db.String(128))

    """secret_key"""
    secret_key = db.Column('secret_key', db.String(128))

    @hybrid_property
    def username(self):
        """Get username."""
        return self._displayname

    @hybrid_property
    def get_username(self):
        """Get username."""
        return self._username

    @username.setter
    def username(self, username):
        """Set username.

        .. note:: The username will be converted to lowercase. The display name
            will contain the original version.
        """
        self._displayname = username

    @classmethod
    def get_by_username(cls, username):
        """Get profile by username.

        :param username: A username to query for (case insensitive).
        """
        return cls.query.filter(
            UserProfile._username == username.lower()
        ).one()

    @classmethod
    def get_by_displayname(cls, username):
        """Get profile by username.

        :param username: A username to query for (case insensitive).
        """
        return cls.query.filter(
            UserProfile._displayname == username.lower()
        ).first()

    @classmethod
    def get_by_userid(cls, user_id):
        """Get profile by user identifier.

        Args:
            user_id (int): user id.

        Returns:
            UserProfile: user profile object. If not found, return None.
        """
        obj = cls.query.filter_by(user_id=user_id).one_or_none()
        return obj if isinstance(obj, UserProfile) else None

    @property
    def is_anonymous(self):
        """Return whether this UserProfile is anonymous."""
        return False

    def get_institute_data(self):
        """Get institute data.
        Returns:
            list: list of dict which contains affiliated institution name and position.
        """

        # get setting from admin settings
        profile_setting = AdminSettings.get('profiles_items_settings', dict_to_object=False)
        if not profile_setting:
            profile_setting = current_app.config.get("WEKO_USERPROFILES_DEFAULT_FIELDS_SETTINGS", {})

        item_field_settings = [
            profile_setting.get("item"+ str(i), {}).get("visible", False)  for i in range(3, 17)]
        institute_dict = [
            {"subitem_affiliated_institution_name": self.item3 if item_field_settings[0] else "",
            'subitem_affiliated_institution_position': self.item4 if item_field_settings[1] else ""},
            {'subitem_affiliated_institution_name': self.item5 if item_field_settings[2] else "",
            'subitem_affiliated_institution_position': self.item6 if item_field_settings[3] else ""},
            {'subitem_affiliated_institution_name': self.item7 if item_field_settings[4] else "",
            'subitem_affiliated_institution_position':self.item8 if item_field_settings[5] else ""},
            {'subitem_affiliated_institution_name': self.item9 if item_field_settings[6] else "",
            'subitem_affiliated_institution_position': self.item10 if item_field_settings[7] else ""},
            {'subitem_affiliated_institution_name': self.item11 if item_field_settings[8] else "",
            'subitem_affiliated_institution_position': self.item12 if item_field_settings[9] else ""}
        ]
        return institute_dict


@event.listens_for(User, 'init')
def on_user_init(target, args, kwargs):
    """Provide hook on :class:`~invenio_accounts.models.User` initialization.

    Automatically convert a dict to a
    :class:`~.UserProfile` instance. This is needed
    during e.g. user registration where Flask-Security will initialize a
    user model with all the form data (which when Invenio-UserProfiles is
    enabled includes a ``profile`` key). This will make the user creation fail
    unless we convert the profile dict into a :class:`~.UserProfile` instance.
    """
    profile = kwargs.pop('profile', None)
    if profile is not None and not isinstance(profile, UserProfile):
        profile = UserProfile(**profile)
        if kwargs.get('id'):
            profile.user_id = kwargs['id']
        kwargs['profile'] = profile