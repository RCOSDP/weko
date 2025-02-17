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
from weko_user_profiles.models import UserProfile
from werkzeug.local import LocalProxy

from .models import ShibbolethUser,Role

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
                if self.shib_attr['shib_user_name']:
                    shib_user.shib_user_name = self.shib_attr['shib_user_name']
                if self.shib_attr['shib_role_authority_name']:
                    shib_user.shib_role_authority_name = self.shib_attr[
                        'shib_role_authority_name']
            db.session.commit()
        except Exception as ex:
            current_app.logger.error(ex)
            db.session.rollback()
            return None

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
        try:
            self.user = User.query.filter_by(email=account).first()
            shib_username_config = current_app.config[
                'WEKO_ACCOUNTS_SHIB_ALLOW_USERNAME_INST_EPPN']
            
            with db.session.begin_nested():
                self.user.email = self.shib_attr['shib_mail']

            if not self.shib_attr['shib_eppn'] and shib_username_config:
                self.shib_attr['shib_eppn'] = self.shib_attr['shib_user_name']
            self.shib_user = ShibbolethUser.create(
                self.user,
                **self.shib_attr
            )
            res = self.shib_user
            db.session.commit()
        except Exception as e:
            res = None
            db.session.rollback()
            current_app.logger.error(e)

        return res

    def new_relation_info(self):
        """
        Create new relation info for shibboleth user when first login weko3.

        :return: ShibbolethUser instance

        """
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
            self.user = user

        shib_user = ShibbolethUser.create(
            self.user,
            **self.shib_attr)
        self.shib_user = shib_user
        self.new_shib_profile()

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

        if not self.user:
            ret = _("Can't get relation Weko User.")
            return False, ret

        roles = self.shib_attr.get('shib_role_authority_name', '')
        # Splitting the value of shib_role_authority_name into multiple roles
        roles = [x.strip() for x in roles.split(';')]
        shib_roles = current_app.config['WEKO_ACCOUNTS_SHIB_ROLE_RELATION']

        if set(roles).issubset(set(shib_roles.keys())):
            _roles = [shib_roles[role] for role in roles]
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

        # WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPSがTrueのときSHIB_ATTR_IS_MEMBER_OFの情報に合わせる
        if current_app.config['WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS']:
            try:
                shib_attr_is_member_of = self.shib_attr.get('SHIB_ATTR_IS_MEMBER_OF', [])
                if shib_attr_is_member_of:
                    # SHIB_ATTR_IS_MEMBER_OFの情報を取得
                    member_of_list = shib_attr_is_member_of.split(';')
                    print("SHIB_ATTR_IS_MEMBER_OF:", member_of_list)

                    # accounts_roleテーブルの情報を取得
                    existing_roles = {role.name for role in Role.query.all()}
                    print("Existing roles in accounts_role table:", existing_roles)

                    # 差異があった場合に更新
                    if set(member_of_list) != existing_roles:
                        try:
                            with db.session.begin_nested():
                                # 設定辞書を取得
                                config = current_app.config['WEKO_ACCOUNTS_GAKUNIN_GROUP_PATTERN_DICT']
                                prefix = config['prefix']
                                role_mapping = config['role_mapping']

                                # 既存のロールを更新または追加
                                for role_name in member_of_list:
                                    # ロール名を変換
                                    mapped_role_name = role_mapping.get(role_name[len(prefix) + 1:], role_name)
                                    role = Role.query.filter_by(name=mapped_role_name).first()
                                    if role:
                                        role.description = ""  # 必要に応じて説明を更新
                                    else:
                                        db.session.add(Role(name=mapped_role_name, description=""))

                                # 不要なロールを削除
                                for role_name in existing_roles:
                                    if role_name not in member_of_list:
                                        role_to_remove = Role.query.filter_by(name=role_name).one()
                                        db.session.delete(role_to_remove)

                                db.session.commit()
                        except Exception as ex:
                            current_app.logger.error(ex)
                            db.session.rollback()
                            return str(ex)
                else:
                    # TODO: IDPのEntityIDを取得し、設定値の辞書からそのEntityIDに対応するロールを取得し、そのロールを割り当てる
                    try:
                        # IDPのEntityIDを取得
                        idp_entity_id = self.shib_attr.get('WEKO_ACCOUNTS_IDP_ENTITY_ID')
                        if not idp_entity_id:
                            raise KeyError('WEKO_ACCOUNTS_IDP_ENTITY_ID is missing in shib_attr')

                        # 設定値の辞書からそのEntityIDに対応するロールを取得
                        default_roles = current_app.config['WEKO_ACCOUNTS_GAKUNIN_DEFAULT_GROUP_MAPPING'].get(idp_entity_id, [])
                        if not default_roles:
                            raise KeyError(f'No roles found for IDP Entity ID: {idp_entity_id}')

                        # 取得したロールを割り当てる
                        with db.session.begin_nested():
                            for role_name in default_roles:
                                role = Role.query.filter_by(name=role_name).first()
                                if role:
                                    role.description = ""  # 必要に応じて説明を更新
                                else:
                                    db.session.add(Role(name=role_name, description=""))
                            db.session.commit()
                    except KeyError as ke:
                        current_app.logger.error(f"Missing key in shib_attr: {ke}")
                        return str(ke)
                    except Exception as ex:
                        current_app.logger.error(f"Unexpected error: {ex}")
                        return str(ex)
            except KeyError as ke:
                current_app.logger.error(f"Missing key in shib_attr: {ke}")
                return str(ke)
            except Exception as ex:
                current_app.logger.error(f"Unexpected error: {ex}")
                return str(ex)

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
