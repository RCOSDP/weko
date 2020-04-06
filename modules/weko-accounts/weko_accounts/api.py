# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Shibboleth User API."""

from datetime import datetime

from flask import current_app, session
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

    def get_relation_info(self):
        """
        Get weko user info by shibboleth user info.

        :return: ShibbolethUser if exists relation else None

        """
        shib_user = None
        if self.shib_attr['shib_eppn'] is not None and len(
                self.shib_attr['shib_eppn']) > 0:
            shib_user = ShibbolethUser.query.filter_by(
                shib_eppn=self.shib_attr['shib_eppn']).one_or_none()
        if shib_user is None:
            """First login for Weko"""
            return None
            # check email info on account_user
            # weko_user = User.query.filter_by(
            #     email=self.shib_attr['shib_mail']).one_or_none()
            # if weko_user is not None:
            #     # need check weko user info for the same email address
            #     return 'chk'
            # new shibboleth user login
            # shib_user = self.new_relation_info()

        if shib_user is not None:
            self.shib_user = shib_user
            if self.user is None:
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
