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
from flask_babelex import gettext as _
from flask_login import current_user, user_logged_in, user_logged_out
from flask_security.utils import hash_password, verify_password
from invenio_accounts.models import Role, User
from invenio_db import db
from sqlalchemy.exc import SQLAlchemyError
from weko_user_profiles.models import UserProfile
from werkzeug.local import LocalProxy

from .models import ShibbolethUser

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


class ShibUser(object):
    """Shibboleth User."""

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

    def _set_weko_user_role(self, roles):
        """
        Assign role for Shibboleth user.

        :param role_name:
        :return:

        """
        error = None
        roles = Role.query.filter(
            Role.name.in_(roles)).all()
        # fix https://redmine.devops.rcos.nii.ac.jp/issues/29921
        #roles = list(set(roles) - set(self.user.roles))

        try:
            with db.session.begin_nested():
                self.user.roles = list(
                    role for role in self.user.roles
                    if role not in self.shib_user.shib_roles)
                self.user.roles.clear()
                self.shib_user.shib_roles.clear()
                for role in roles:
                    if role not in self.user.roles:
                        _datastore.add_role_to_user(
                            self.user,
                            role)
                        self.shib_user.shib_roles.append(role)
        except Exception as ex:
            current_app.logger.error(ex)
            db.session.rollback()
            error = ex
        return error

    def _get_site_license(self):
        """
        Assign role for weko3 user.

        :param shib_role_auth:
        :return:

        """
        return self.shib_attr.get('shib_ip_range_flag', False)

    def _create_unknown_roles(self, role_names):
        """
        Create unknown roles.

        :param roles: Role names
        """
        allow_create_role = current_app.config[
            'WEKO_ACCOUNTS_SHIB_ALLOW_CREATE_GROUP_ROLE']
        if allow_create_role:
            exists_role_names = [role.name for role in Role.query.all()]
            unknown_roles = [i for i in role_names if i and i not in exists_role_names]
            if unknown_roles:
                # Add new roles
                try:
                    with db.session.begin_nested():
                        for new_role_name in unknown_roles:
                            new_role = Role(name=new_role_name)
                            db.session.add(new_role)
                    db.session.commit()
                except Exception as ex:
                    current_app.logger.error(ex)
                    db.session.rollback()

    def get_relation_info(self):
        """
        Get weko user info by Shibboleth user info.

        :return: ShibbolethUser if exists relation else None

        """
        shib_user = None
        shib_username_config = current_app.config[
            'WEKO_ACCOUNTS_SHIB_ALLOW_USERNAME_INST_EPPN']

        if self.shib_attr['shib_eppn']:
            shib_user = ShibbolethUser.query.filter_by(
                shib_eppn=self.shib_attr['shib_eppn']).one_or_none()
        if not shib_user and shib_username_config \
                and self.shib_attr.get('shib_user_name'):
            shib_user = ShibbolethUser.query.filter_by(
                shib_user_name=self.shib_attr['shib_user_name']).one_or_none()

        if shib_user and shib_user.weko_user:
            self.shib_user = shib_user
            if not self.user:
                self.user = shib_user.weko_user
        else:
            return None

        try:
            with db.session.begin_nested():
                if self.shib_attr['shib_mail']:
                    shib_user.shib_mail = self.shib_attr['shib_mail']
                    shib_user.weko_user.email = self.shib_attr['shib_mail']
                if self.shib_attr['shib_user_name']:
                    shib_user.shib_user_name = self.shib_attr['shib_user_name']
                if self.shib_attr['shib_role_authority_name']:
                    shib_user.shib_role_authority_name = self.shib_attr['shib_role_authority_name']
                if self.shib_attr['shib_page_name']:
                    shib_user.shib_page_name = self.shib_attr['shib_page_name']
                if self.shib_attr['shib_active_flag']:
                    shib_user.shib_active_flag = self.shib_attr['shib_active_flag']
                if self.shib_attr['shib_ip_range_flag']:
                    shib_user.shib_ip_range_flag = self.shib_attr['shib_ip_range_flag']
                if self.shib_attr['shib_organization']:
                    shib_user.shib_organization = self.shib_attr['shib_organization']
            db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.error("SQLAlchemyError: {}".format(ex))
            db.session.rollback()
            raise ex

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

        :return: ShibbolethUser instance

        """
        self.user = User.query.filter_by(email=account).first()
        shib_username_config = current_app.config[
            'WEKO_ACCOUNTS_SHIB_ALLOW_USERNAME_INST_EPPN']
        try:
            if not self.shib_attr['shib_eppn'] and shib_username_config:
                self.shib_attr['shib_eppn'] = self.shib_attr['shib_user_name']

            shib_user_count = ShibbolethUser.query.filter_by(weko_uid=self.user.id).count()
            if shib_user_count > 0:
                raise SQLAlchemyError("User already exists. (weko_uid={}, shib_eppn={})".format(self.user.id, self.shib_attr.get('shib_eppn')))
            
            self.user.email = self.shib_attr['shib_mail']
            self.shib_user = ShibbolethUser.create(
                self.user,
                **self.shib_attr
            )
            return self.shib_user
        except Exception as ex:
            current_app.logger.error(ex)
            db.session.rollback()
            return None

    def new_relation_info(self):
        """
        Create new relation info for shibboleth user when first login weko3.

        :return: ShibbolethUser instance

        """
        try:
            kwargs = dict(
                email=self.shib_attr.get('shib_mail'),
                password=hash_password(''),
                confirmed_at=datetime.utcnow(),
                active=True
            )

            user = _datastore.find_user(email=self.shib_attr.get('shib_mail'))
            if not user:
                self.user = _datastore.create_user(**kwargs)
            else:
                shib_user_count = ShibbolethUser.query.filter_by(weko_uid=user.id).count()
                if shib_user_count > 0:
                    raise SQLAlchemyError("User already exists. (weko_uid={}, shib_eppn={})".format(user.id, self.shib_attr.get('shib_eppn')))
                self.user = user

            shib_user = ShibbolethUser.create(
                self.user,
                **self.shib_attr)
            self.shib_user = shib_user
            self.new_shib_profile()

            return shib_user
        except SQLAlchemyError as ex:
            current_app.logger.error("SQLAlchemyError: {}".format(ex))
            db.session.rollback()
            raise ex

    def new_shib_profile(self):
        """
        Create new profile info for shibboleth user.

        :return: UserProfile instance

        """
        with db.session.begin_nested():
            userprofile = UserProfile.query.filter_by(user_id=self.user.id).one_or_none()
            if not userprofile:
                # create profile.
                userprofile = UserProfile(user_id=self.user.id,
                                        timezone=current_app.config[
                                            'USERPROFILES_TIMEZONE_DEFAULT'],
                                        language=current_app.config[
                                            'USERPROFILES_LANGUAGE_DEFAULT'])
                userprofile.username = self.shib_user.shib_user_name
                db.session.add(userprofile)
            else:
                # update profile.
                userprofile.username = self.shib_user.shib_user_name
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
        ret = ''
        _roles = []

        if not self.user:
            ret = _("Can't get relation Weko User.")
            return False, ret

        roles = self.shib_attr.get('shib_role_authority_name', '')
        # Splitting the value of shib_role_authority_name into multiple roles
        roles = [x.strip() for x in roles.split(';')]
        shib_roles = current_app.config['WEKO_ACCOUNTS_SHIB_ROLE_RELATION']

        if set(roles).issubset(set(shib_roles.keys())):
            _roles = [shib_roles[role] for role in roles]

        groups = self.shib_attr.get('shib_page_name', '')
        if groups:
            groups = [x.strip() for x in groups.split(';')]
            _roles.extend(groups)

        # Set roles for all login user
        shib_roles = current_app.config['WEKO_ACCOUNTS_SHIB_ROLE_ALL_USERS']
        if isinstance(shib_roles, list):
            _roles.extend(shib_roles)
        elif isinstance(shib_roles, str):
            _roles.append(shib_roles)

        if _roles:
            # If `_roles` has unknown name, create role.
            self._create_unknown_roles(_roles)

            ret = self._set_weko_user_role(_roles)

        if ret:
            return False, ret
        return True, ret

    def valid_site_license(self):
        """
        Get license from shib attr.

        :return:

        """
        if self._get_site_license():
            return True, ''
        else:
            return False, _('Failed to login.')

    def check_in(self):
        """
        Get and check-in Shibboleth attr data before login to system.

        :return:

        """
        check_role, error = self.assign_user_role()
        if not check_role:
            return error

        # ! NEED RELATION SHIB_ATTR
        # check_license, error = self.valid_site_license()
        # if not check_license:
        #     return error

        return None

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
