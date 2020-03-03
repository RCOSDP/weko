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

from flask import current_app, session
from flask_babelex import gettext as _
from flask_login import current_user, user_logged_in, user_logged_out
from flask_security.utils import hash_password, verify_password
from invenio_accounts.models import Role, User
from invenio_db import db
from weko_user_profiles.models import UserProfile
from werkzeug.local import LocalProxy

from .models import ShibbolethUser

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


class ShibUser(object):
    """Shibuser."""

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

    def _set_weko_user_role(self, role_name):
        """
        Assign role for weko3 user.

        :param shib_role_auth:
        :return:

        """
        ret = True
        try:
            user_role = Role.query.filter_by(name=role_name).first()
            if user_role in self.user.roles:
                current_app.logger.debug('{} had been assigned to this User!',
                                         role_name)
                return ret
            with db.session.begin_nested():
                ret = _datastore.add_role_to_user(self.user, user_role)
            db.session.commit()
        except Exception as ex:
            current_app.logger.debug("An error occurred when trying to add "
                                     "Role: {} to this User!", ex)
            db.session.rollback()
            ret = False
        return ret

    def _get_site_license(self):
        """
        Assign role for weko3 user.

        :param shib_role_auth:
        :return:

        """
        return self.shib_attr.get('wekoSiteUserWithinIpRange', False)

    def get_relation_info(self):
        """
        Get weko user info by Shibboleth user info.

        :return: ShibbolethUser if exists relation else None

        """
        shib_user = None
        if self.shib_attr['shib_eppn']:
            shib_user = ShibbolethUser.query.filter_by(
                shib_eppn=self.shib_attr['shib_eppn']).one_or_none()

        if shib_user:
            self.shib_user = shib_user
            if not self.user:
                self.user = shib_user.weko_user

        return shib_user

    def check_weko_user(self, account, pwd):
        """
        Check weko user info.

        :param account:
        :param pwd:
        :return: Boolean

        """
        weko_user = _datastore.find_user(email=account)
        if weko_user is None:
            return False
        if not verify_password(pwd, weko_user.password):
            return False
        return True

    def bind_relation_info(self, account):
        """
        Create new relation info with the user who belong with the email.

        :return: ShibbolenUser instance

        """
        self.user = User.query.filter_by(email=account).one_or_none()
        shib_user = ShibbolethUser.create(self.user, **self.shib_attr)
        self.shib_user = shib_user
        return shib_user

    def new_relation_info(self):
        """
        Create new relation info for shibboleth user when first login weko3.

        :return: ShibbolethUser instance

        """
        kwargs = dict(email=self.shib_attr.get('shib_eppn'), password='',
                      active=True)
        kwargs['password'] = hash_password(kwargs['password'])
        kwargs['confirmed_at'] = datetime.utcnow()
        self.user = _datastore.create_user(**kwargs)
        shib_user = ShibbolethUser.create(self.user, **self.shib_attr)
        self.shib_user = shib_user
        # self.new_shib_profile()
        return shib_user

    def new_shib_profile(self):
        """
        Create new profile info for shibboleth user.

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
        Create login info for shibboleth user.

        :return:

        """
        session['user_id'] = self.user.id
        session['user_src'] = 'Shib'
        user_logged_in.send(current_app._get_current_object(), user=self.user)

    def assign_user_role(self):
        """
        Check and set relation role for Weko3 user by wekoSocietyAffiliation.

        :return:

        """
        error = ''

        if not self.user:
            error = _('Can\'t get relation Weko User.')
            return False, error
        # TODO: check GakuNin User
        if self.shib_user:
            return self._set_weko_user_role(current_app.config[
                                            'WEKO_GENERAL_ROLE'])

        shib_role_auth = self.shib_attr.get('wekoSocietyAffiliation', None)
        if not shib_role_auth:
            error = _('Failed to get attribute.')
            return False, error

        shib_role_config = current_app.config['SHIB_ACCOUNTS_ROLE_RELATION']
        if shib_role_auth in shib_role_config.keys():
            return self._set_weko_user_role(shib_role_config[shib_role_auth])
        else:
            error = _('Invalid attribute.')

        return False, error

    def valid_site_license(self):
        """
        Check and set relation role for Weko3 user by wekoSocietyAffiliation.

        :return:

        """
        if self._get_site_license():
            return True, ''
        else:
            return False, _('Invalid Site License.')

    def check_in(self):
        """
        Get and check-in Shibboleth attr data before login to system.

        :return:

        """
        check_role, error = self.assign_user_role()
        if not check_role:
            return error

        check_license, error = self.valid_site_license()
        if not check_license:
            return error

        return True

    @classmethod
    def shib_user_logout(cls):
        """
        Remove login info for shibboleth user.

        :return:

        """
        user_logged_out.send(current_app._get_current_object(),
                             user=current_user)


def get_user_info_by_role_name(role_name):
    """Get user info by role name."""
    role = Role.query.filter_by(name=role_name).first()
    return User.query.filter(User.roles.contains(role)).all()
