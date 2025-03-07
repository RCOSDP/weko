# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Shibboleth User API."""

import re
from datetime import datetime
from urllib.parse import urlparse

import redis
from flask import current_app, request, session
from flask_babelex import gettext as _
from flask_login import current_user, user_logged_in, user_logged_out
from flask_security.utils import hash_password, verify_password

from invenio_accounts.models import Role, User
from invenio_db import db
from weko_redis.redis import RedisConnection
from weko_user_profiles.models import UserProfile
from werkzeug.local import LocalProxy

from .models import ShibbolethUser
from weko_index_tree.models import Index

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

        try:
            if current_app.config['WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS']:
                roles_add = self._get_roles_to_add()
                self._assign_roles_to_user(roles_add)
        except Exception as ex:
            return str(ex)

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
        shib_attr_is_member_of = []

        if current_app.config['WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS']:
            try:
                # get shibboleth attributes (isMemberOf)
                shib_attr_is_member_of = self.shib_attr.get('isMemberOf', [])

                # check isMemberOf is a list
                if not isinstance(shib_attr_is_member_of, list):
                    raise ValueError('isMemberOf is not a list')

                # check isMemberOf is empty
                if not shib_attr_is_member_of:
                    idp_entity_id = current_app.config['WEKO_ACCOUNTS_IDP_ENTITY_ID']
                    if not idp_entity_id:
                        raise KeyError('WEKO_ACCOUNTS_IDP_ENTITY_ID is missing in config')

                    shib_attr_is_member_of = current_app.config['WEKO_ACCOUNTS_GAKUNIN_DEFAULT_GROUP_MAPPING'].get(idp_entity_id, [])
            except Exception as ex:
                current_app.logger.error(f"Unexpected error: {ex}")
                raise ex

        return shib_attr_is_member_of

    def _assign_roles_to_user(self, map_group_names):
        try:
            # WEKO_ACCOUNTS_GAKUNIN_GROUP_PATTERN_DICT設定を取得
            config = current_app.config['WEKO_ACCOUNTS_GAKUNIN_GROUP_PATTERN_DICT']
            prefix = config['prefix']
            role_keyword = config['role_keyword']
            role_mapping = config['role_mapping']

            with db.session.begin_nested():
                for map_group_name in map_group_names:
                    # ロール名が指定されたプレフィックスで始まるか確認
                    pattern = prefix + r'_[A-Za-z_]_' + role_keyword + r'_[A-Za-z_]+'
                    if re.match(pattern, map_group_name):
                        # The map_group_name matches the pattern
                        suffix = map_group_name.split(role_keyword + "_")[-1]
                        weko_role_name = role_mapping.get(suffix)
                        if weko_role_name:
                            role = Role.query.filter_by(name=weko_role_name).one_or_none()
                            if role and role not in self.user.roles:
                                _datastore.add_role_to_user(self.user, role)
                                self.shib_user.shib_roles.append(role)
                    elif map_group_name == config["sysadm_group"]:
                        # システム管理者のロールを追加
                        sysadm_name = current_app.config['WEKO_ADMIN_PERMISSION_ROLE_SYSTEM']
                        role = Role.query.filter_by(name=sysadm_name).one()
                        if role and role not in self.user.roles:
                            _datastore.add_role_to_user(self.user, role)
                            self.shib_user.shib_roles.append(role)

                    # マッピングされたロール名をデータベースでロールを確認
                    role = Role.query.filter_by(name=map_group_name).one_or_none()
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
            raise ex

    # ! NEED RELATION SHIB_ATTR
    # check_license, error = self.valid_site_license()
    # if not check_license:
    #     return error


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


def sync_shib_gakunin_map_groups():
    """Handle SHIB_BIND_GAKUNIN_MAP_GROUPS logic."""
    try:
        # Entity ID → Redisのキーに変換
        idp_entity_id = request.form.get('WEKO_ACCOUNTS_IDP_ENTITY_ID')
        if not idp_entity_id:
            raise KeyError('WEKO_ACCOUNTS_IDP_ENTITY_ID is missing in config')

        parsed_url = urlparse(idp_entity_id)
        fqdn = parsed_url.netloc.split(":")[0].replace('.', '_').replace('-', '_')
        suffix = current_app.config.get('WEKO_ACCOUNTS_GAKUNIN_GROUP_SUFFIX', '')

        # create Redis key
        redis_key = fqdn + suffix
        datastore = RedisConnection().connection(db=current_app.config['CACHE_REDIS_DB'], kv=True)
        map_group_list = set(datastore.lrange(redis_key, 0, -1))

        # get roles
        roles = Role.query.all()
        role_names = set({role.name for role in Role.query.all()})

        if map_group_list != role_names:
            update_roles(map_group_list, roles)
    except KeyError as ke:
        current_app.logger.error(f"Missing key in request headers: {ke}")
        raise ke
    except redis.ConnectionError as rce:
        current_app.logger.error(f"Redis connection error: {rce}")
        raise rce
    except Exception as ex:
        current_app.logger.error(f"Unexpected error: {ex}")
        raise ex


def update_roles(map_group_list, roles):
    """Update roles based on map group list."""
    role_names = set({role.name for role in roles})

    with db.session.begin_nested():
        # add new roles
        for map_group_name in map_group_list:
            if not map_group_name or map_group_name in role_names:
                continue
            new_role = Role(name=map_group_name, description="")
            db.session.add(new_role)
            db.session.flush()  # new_role.idを取得するためにフラッシュ

            # WEKO_INNDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSIONがTrueの場合、Indexクラスのbrowsing_roleに追加
            if current_app.config.get('WEKO_INNDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION', False):
                index = Index.query.filter_by(id=new_role.id).one_or_none()
                if index:
                    update_browsing_role(new_role.id)
                    db.session.add(index)

            # WEKO_INNDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSIONがTrueの場合、Indexクラスのcontribute_roleに追加
            if current_app.config.get('WEKO_INNDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION', False):
                index = Index.query.filter_by(id=new_role.id).one_or_none()
                if index:
                    update_contribute_role(new_role.id)
                    db.session.add(index)


        # delete roles that are not in map_group_list
        for role_name in role_names:
            if role_name in map_group_list:
                continue
            role_to_remove = Role.query.filter_by(name=role_name).one()
            db.session.delete(role_to_remove)

            # WEKO_INNDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSIONがTrueの場合、Indexクラスのbrowsing_roleから削除
            if current_app.config.get('WEKO_INNDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION', False):
                index = Index.query.filter_by(id=role_to_remove.id).one_or_none()
                if index:
                    remove_browsing_role(index,role_to_remove.id)
                    db.session.add(index)

            # WEKO_INNDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSIONがTrueの場合、Indexクラスのcontribute_roleから削除
            if current_app.config.get('WEKO_INNDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION', False):
                index = Index.query.filter_by(id=role_to_remove.id).one_or_none()
                if index:
                    remove_contribute_role(index,role_to_remove.id)
                    db.session.add(index)

    db.session.commit()

def update_browsing_role(self, role_id):
        """Update browsing_role with the given role_id."""
        if self.browsing_role:
            browsing_roles = set(self.browsing_role.split(','))
        else:
            browsing_roles = set()

        # Add the new role_id
        browsing_roles.add(str(role_id))

        # Update the browsing_role column
        self.browsing_role = ','.join(browsing_roles)

def remove_browsing_role(self, role_id):
    """Remove the given role_id from browsing_role."""
    if self.browsing_role:
        browsing_roles = set(self.browsing_role.split(','))
        if str(role_id) in browsing_roles:
            browsing_roles.remove(str(role_id))
            self.browsing_role = ','.join(browsing_roles)

def update_contribute_role(self, role_id):
        """Update contribute_role with the given role_id."""
        if self.contribute_role:
            contribute_roles = set(self.contribute_role.split(','))
        else:
            contribute_roles = set()

        # Add the new role_id
        contribute_roles.add(str(role_id))

        # Update the contribute_role column
        self.contribute_role = ','.join(contribute_roles)

def remove_contribute_role(self, role_id):
    """Remove the given role_id from contribute_role."""
    if self.contribute_role:
        contribute_roles = set(self.contribute_role.split(','))
        if str(role_id) in contribute_roles:
            contribute_roles.remove(str(role_id))
            self.contribute_role = ','.join(contribute_roles)
