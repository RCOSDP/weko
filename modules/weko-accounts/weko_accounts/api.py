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
from invenio_accounts.models import Role, User, userrole
from invenio_db import db
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
        #ログインユーザーのロールをクリアする
        self.user.roles.clear()
        check_role, error = self.assign_user_role()
        if not check_role:
            return error

        roles_add = self._get_roles_to_add()
        if roles_add is None:
            return "Error getting roles to add"

        error = self._assign_roles_to_user(roles_add)
        if error:
            return error

        return None

    def _get_roles_to_add(self):
        """
        Get roles to add based on Shibboleth attributes.

        Shibboleth属性に基づいて追加するロールを取得します。
        具体的には、WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS設定がTrueの場合に、
        WEKO_SHIB_ATTR_IS_MEMBER_OF属性またはWEKO_ACCOUNTS_IDP_ENTITY_ID属性に基づいて
        追加するロールを決定します。

        :return: Set of roles to add
        """
        roles_add = set()

        if current_app.config['WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS']:
            try:
                # Shibboleth属性からWEKO_SHIB_ATTR_IS_MEMBER_OFを取得
                shib_attr_is_member_of = self.shib_attr.get('WEKO_SHIB_ATTR_IS_MEMBER_OF', [])
                if shib_attr_is_member_of:
                    # WEKO_SHIB_ATTR_IS_MEMBER_OFの情報を取得
                    member_of_list = shib_attr_is_member_of.split(';')

                    # 現在のユーザーのロールを取得
                    current_user_roles = [role.name for role in self.user.roles]
                else:
                    # IDPのEntityIDを取得
                    idp_entity_id = self.shib_attr.get('WEKO_ACCOUNTS_IDP_ENTITY_ID')
                    if not idp_entity_id:
                        raise KeyError('WEKO_ACCOUNTS_IDP_ENTITY_ID is missing in shib_attr')

                    # 設定値の辞書からそのEntityIDに対応するロールを取得
                    mapping_roles = current_app.config['WEKO_ACCOUNTS_GAKUNIN_DEFAULT_GROUP_MAPPING'].get(idp_entity_id, [])
                    if not mapping_roles:
                        raise KeyError(f'No roles found for IDP Entity ID: {idp_entity_id}')

                    # 現在のユーザーのロール
                    current_user_roles = [role.name for role in self.user.roles]
            except KeyError as ke:
                # キーエラー
                current_app.logger.error(f"Missing key in shib_attr: {ke}")
                return []
            except Exception as ex:
                # その他の例外
                current_app.logger.error(f"Unexpected error: {ex}")
            return []

        return current_user_roles

    def _assign_roles_to_user(self, roles_add):
        try:
            # WEKO_ACCOUNTS_GAKUNIN_GROUP_PATTERN_DICT設定を取得
            config = current_app.config['WEKO_ACCOUNTS_GAKUNIN_GROUP_PATTERN_DICT']
            prefix = config['prefix']
            role_mapping = config['role_mapping']

            with db.session.begin_nested():
                # roles_addに含まれる各ロール名について処理を行う
                for role_name in roles_add:
                    # ロール名が指定されたプレフィックスで始まるか確認
                    if role_name.startswith(prefix):
                        # プレフィックスを除いた部分を使用してロール名をマッピング
                        mapped_role_name = role_mapping.get(role_name[len(prefix) + 1:], role_name)
                        # マッピングされたロール名をデータベースでロールを確認
                        role = Role.query.filter_by(name=mapped_role_name).first()
                        # ロールが存在し、かつユーザーにまだそのロールが割り当てられていない場合
                        if role and role not in self.user.roles:
                            # ユーザーにロールを追加
                            _datastore.add_role_to_user(self.user, role)
                            # Shibbolethユーザーのロールリストに追加
                            self.shib_user.shib_roles.append(role)
                db.session.commit()
        except Exception as ex:
            current_app.logger.error(f"Error assigning roles: {ex}")
            db.session.rollback()
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
