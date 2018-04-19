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

"""Shibboleth User API."""

from datetime import datetime

from flask import current_app
from flask_login import current_user, user_logged_in, user_logged_out
from flask_security.utils import hash_password
from invenio_db import db
from werkzeug.local import LocalProxy
from weko_user_profiles.models import UserProfile

from .models import ShibbolethUser

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


class ShibUser(object):
    def __init__(self, shib_attr=None):
        """
        Class ShibUser initialization.

        :param shib_attr: passed attribute for shibboleth user
        """
        self.shib_attr = shib_attr
        self.user = None
        """The :class:`invenio_accounts.models.User` instance."""
        self.shib_user = None
        """The :class:`.models.ShibbolethUser` instance."""

    def get_relation_info(self):
        """
        get weko user info by shibboleth user info
        :return: ShibbolethUser if exists relation else None
        """
        shib_user = ShibbolethUser.query.filter_by(
            shib_uid=self.shib_attr['shib_uid']).one_or_none()
        if shib_user is None:
            # new shibboleth user login
            shib_user = self.new_relation_info()

        if shib_user is not None:
            self.shib_user = shib_user
            if self.user is None:
                self.user = shib_user.weko_user
        return shib_user

    def new_relation_info(self):
        """
        create new relation info for shibboleth user when first login weko3
        :return: ShibbolethUser instance
        """
        kwargs = dict(email=self.shib_attr.get('shib_mail'), password='',
                      active=True)
        kwargs['password'] = hash_password(kwargs['password'])
        kwargs['confirmed_at'] = datetime.utcnow()
        self.user = _datastore.create_user(**kwargs)
        shib_user = ShibbolethUser.create(self.user, **self.shib_attr)
        self.shib_user = shib_user
        self.new_shib_profile()
        return shib_user

    def new_shib_profile(self):
        """
        create new profile info for shibboleth user
        :return: UserProfile instance
        """
        with db.session.begin_nested():
            # create profile.
            userprofile = UserProfile(user_id=self.user.id,
                                      timezone=current_app.config[
                                          'USERPROFILES_TIMEZONE_DEFAULT'],
                                      language=current_app.config[
                                          'USERPROFILES_LANGUAGE_DEFAULT'])
            userprofile.username = self.shib_user.shib_user_name
            db.session.add(userprofile)
        db.session.commit()
        return userprofile

    def shib_user_login(self):
        """
        create login info for shibboleth user
        :return:
        """
        user_logged_in.send(current_app._get_current_object(), user=self.user)
        pass

    @classmethod
    def shib_user_logout(cls):
        """
        remove login info for shibboleth user
        :return:
        """
        user_logged_out.send(current_app._get_current_object(),
                             user=current_user)
        pass
