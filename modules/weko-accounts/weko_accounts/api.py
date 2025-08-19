# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Shibboleth User API."""

import re
import traceback
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

import urllib.parse
import requests


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

        self.is_member_of = []
        if 'shib_is_member_of' in shib_attr:
            is_member_of = shib_attr.get('shib_is_member_of', [])
            if isinstance(is_member_of, str):
                if is_member_of.find(';') != -1:
                    is_member_of = is_member_of.split(';')
                elif is_member_of:
                    is_member_of = [is_member_of]
                else:
                    is_member_of = []
            self.is_member_of = is_member_of
            del shib_attr['shib_is_member_of']

        self.organizations = []
        if 'shib_organization' in shib_attr:
            organizations = shib_attr.get('shib_organization', [])
            if isinstance(organizations, str):
                if organizations.find(';') != -1:
                    organizations = organizations.split(';')
                elif organizations:
                    organizations = [organizations]
                else:
                    organizations = []
            self.organizations = organizations
            del shib_attr['shib_organization']

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
                if not self._find_organization_name():
                    self._assign_roles_to_user(roles_add)
        except Exception as ex:
            traceback.print_exc()
            return str(ex)

        return None

    def _get_roles_to_add(self):
        """Get roles to add based on Shibboleth attributes.

        Gets the roles to add based on Shibboleth attributes.
        Specifically, if the WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS setting
        is True, it determines the roles to add based on the
        WEKO_SHIB_ATTR_IS_MEMBER_OF or WEKO_ACCOUNTS_IDP_ENTITY_ID attribute.

        Returns:
            list: List of roles to add.
        """
        shib_attr_is_member_of = []

        if current_app.config['WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS']:
            try:
                # get shibboleth attributes (isMemberOf)
                shib_attr_is_member_of = self.is_member_of

                # check isMemberOf is a list
                if not isinstance(shib_attr_is_member_of, list):
                    raise ValueError('isMemberOf is not a list')

                # check isMemberOf is empty
                if not shib_attr_is_member_of:
                    idp_entity_id = current_app.config['WEKO_ACCOUNTS_IDP_ENTITY_ID']
                    if not idp_entity_id:
                        raise KeyError(
                            'WEKO_ACCOUNTS_IDP_ENTITY_ID is missing in config'
                    )

                    shib_attr_is_member_of = current_app.config[
                        'WEKO_ACCOUNTS_GAKUNIN_DEFAULT_GROUP_MAPPING'
                    ].get(idp_entity_id, [])
            except Exception as ex:
                current_app.logger.error(f"Unexpected error: {ex}")
                raise ex

        return shib_attr_is_member_of

    def _find_organization_name(self):
        """
        If organization_name has been registered for each role beforehand,
        that role will be assigned.

        Args:
            None
        """
        try:
            with db.session.begin_nested():
                organization_name = set(self.organizations) if self.organizations else set()

                setting_role = []
                if bool(organization_name & set(current_app.config["WEKO_ACCOUNTS_GAKUNIN_ROLE"]["organizationName"])):
                    setting_role.append(current_app.config["WEKO_ACCOUNTS_GAKUNIN_ROLE"]["defaultRole"])
                if bool(organization_name & set(current_app.config["WEKO_ACCOUNTS_ORTHROS_INSIDE_ROLE"]["organizationName"])):
                    setting_role.append(current_app.config["WEKO_ACCOUNTS_ORTHROS_INSIDE_ROLE"]["defaultRole"])
                if bool(organization_name & set(current_app.config["WEKO_ACCOUNTS_ORTHROS_OUTSIDE_ROLE"]["organizationName"])):
                    setting_role.append(current_app.config["WEKO_ACCOUNTS_ORTHROS_OUTSIDE_ROLE"]["defaultRole"])
                if bool(organization_name & set(current_app.config["WEKO_ACCOUNTS_EXTRA_ROLE"]["organizationName"])):
                    setting_role.append(current_app.config["WEKO_ACCOUNTS_EXTRA_ROLE"]["defaultRole"])
                if setting_role:
                    for role in setting_role:
                        role = Role.query.filter_by(name=role).one_or_none()
                        if role and role not in self.user.roles:
                            _datastore.add_role_to_user(self.user, role)
                            self.shib_user.shib_roles.append(role)
                    return True

            db.session.commit()
            return False
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(f"Error assigning roles: {ex}")
            raise


    def _assign_roles_to_user(self, map_group_names):
        try:
            # WEKO_ACCOUNTS_GAKUNIN_GROUP_PATTERN_DICT設定を取得
            config = current_app.config['WEKO_ACCOUNTS_GAKUNIN_GROUP_PATTERN_DICT']
            prefix = config['prefix']
            role_keyword = config['role_keyword']
            role_mapping = config['role_mapping']
            fqdn = create_fqdn_from_entity_id()

            with db.session.begin_nested():
                for map_group_name in map_group_names:
                    if map_group_name.find('/sp/') != -1 or map_group_name.endswith('/admin'):
                        # Skip if the group name contains '/sp/' or ends with '/admin'
                        continue
                    # ロール名が指定されたプレフィックスで始まるか確認
                    group_name = map_group_name.split('/')[-1]
                    pattern = prefix + f'_{fqdn}_' + role_keyword + r'_[A-Za-z_]+'
                    if re.match(pattern, group_name):
                        # The map_group_name matches the pattern
                        suffix = group_name.split(role_keyword + "_")[-1]
                        weko_role_name = role_mapping.get(suffix)
                        if weko_role_name:
                            role = Role.query.filter_by(name=weko_role_name).one_or_none()
                            if role and role not in self.user.roles:
                                _datastore.add_role_to_user(self.user, role)
                                self.shib_user.shib_roles.append(role)
                    elif group_name == config["sysadm_group"]:
                        # システム管理者のロールを追加
                        sysadm_name = current_app.config['WEKO_ADMIN_PERMISSION_ROLE_SYSTEM']
                        role = Role.query.filter_by(name=sysadm_name).one()
                        if role and role not in self.user.roles:
                            _datastore.add_role_to_user(self.user, role)
                            self.shib_user.shib_roles.append(role)

                    # マッピングされたロール名をデータベースでロールを確認
                    role = Role.query.filter_by(name=group_name).one_or_none()
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

    def get_organization_from_api(self, group_id):
        """Get organization name from API using group_id.

        Args:
            group_id (str): Group ID to search for.
        Returns:
            str: Organization name.
        Raises:
            ValueError: If the API response is not as expected.
        """
        url = f"{current_app.config['WEKO_ACCOUNTS_GAKUNIN_MAP_BASE_URL']}/api/people/@me/{group_id}"
        headers = {
            'Content-Type': 'application/json',
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            entries = data.get("entry", [])
            for entry in entries:
                organizations = entry.get("organizations", [])
                for organization in organizations:
                    if organization.get("type") == "organization":
                        return organization.get("value", {}).get("name")
            raise ValueError(f"Organization not found in response: {data}")
        else:
            raise ValueError(f"API returned error: {response.status_code}")



    # ! NEED RELATION SHIB_ATTR
    # check_license, error = self.valid_site_license()
    # if not check_license:
    #     return error


    @classmethod
    def shib_user_logout(cls):
        """Remove login info for shibboleth user."""
        user_logged_out.send(current_app._get_current_object(),
                             user=current_user)


def get_user_info_by_role_name(role_name):
    """Get user info by role name.

    Args:
        role_name (str): Role name to filter users by.

    Returns:
        list: List of users associated with the specified role name.
    """
    role = Role.query.filter_by(name=role_name).first()
    return User.query.filter(User.roles.contains(role)).all()


def sync_shib_gakunin_map_groups():
    """Handle SHIB_BIND_GAKUNIN_MAP_GROUPS logic."""
    try:
        # Entity ID → Redisのキーに変換
        fqdn = create_fqdn_from_entity_id()
        suffix = current_app.config.get('WEKO_ACCOUNTS_GAKUNIN_GROUP_SUFFIX', '')

        # create Redis key
        redis_key = fqdn + suffix
        datastore = RedisConnection().connection(db=current_app.config['GROUP_INFO_REDIS_DB'])
        map_group_list = set(id.decode('utf-8') for id in datastore.lrange(redis_key, 0, -1))

        # get roles
        roles = Role.query.all()
        role_names = set({role.name for role in roles})

        if map_group_list != role_names:
            update_roles(map_group_list, roles)
    except KeyError as ke:
        current_app.logger.error(f"Missing key in request headers: {ke}")
        raise
    except redis.ConnectionError as rce:
        current_app.logger.error(f"Redis connection error: {rce}")
        raise
    except Exception as ex:
        current_app.logger.error(f"Unexpected error: {ex}")
        raise


def update_roles(map_group_list, roles, indices=[]):
    """Update roles based on map group list."""
    role_names = set({role.name for role in roles})

    new_role_names = [role_name for role_name in map_group_list if role_name and role_name not in role_names]
    roles_to_remove = [role_name for role_name in role_names if role_name not in map_group_list and role_name.startswith('jc_')]

    
    new_roles = []
    remove_role_ids = []
    try:
        with db.session.begin_nested():
            for new_role_name in new_role_names:
                # add new roles to the database
                role = Role(name=new_role_name, description="")
                db.session.add(role)
                db.session.flush()
                new_roles.append(role)
            for role_name in roles_to_remove:
                # remove roles that are not in map_group_list
                role_to_remove = Role.query.filter_by(name=role_name).one()
                remove_role_ids.append(role_to_remove.id)
                db.session.delete(role_to_remove)
        db.session.commit()
    except Exception as ex:
        current_app.logger.error(f"Error adding new roles: {ex}")
        db.session.rollback()
        raise

    # bind new roles to indices
    bind_roles_to_indices(indices, new_roles, remove_role_ids)

def bind_roles_to_indices(indices=[], new_roles=[], remove_role_ids=[]):
    """Bind roles to indices."""
    try:
        with db.session.begin_nested():
            if not indices:
                indices = Index.query.all()
            for index in indices:
                browsing_roles = set()
                if index.browsing_role:
                    browsing_roles = set(int(x) for x in index.browsing_role.split(','))
                # unbind roles from indices removed from the database
                for role_id in remove_role_ids:
                    if role_id in browsing_roles:
                        browsing_roles.remove(role_id)
            
                # bind new roles
                browsing_default_permission = current_app.config.get('WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION', False)
                for role in new_roles:
                    if role.id not in browsing_roles and browsing_default_permission:
                        browsing_roles.add(role.id)
                sorted_browsing_roles = sorted(browsing_roles)
                index.browsing_role = ','.join(str(x) for x in sorted_browsing_roles)

                contributing_roles = set()
                if index.contribute_role:
                    contributing_roles = set(int(x) for x in index.contribute_role.split(','))
                # unbind roles from indices removed from the database
                for role_id in remove_role_ids:
                    if role_id in contributing_roles:
                        contributing_roles.remove(role_id)

                # bind new roles
                contribute_default_permission = current_app.config.get('WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION', False)
                for role in new_roles:
                    if role.id not in contributing_roles and contribute_default_permission:
                        contributing_roles.add(role.id)
                sorted_contributing_roles = sorted(contributing_roles)
                index.contribute_role = ','.join(str(x) for x in sorted_contributing_roles)
        db.session.commit()
    except Exception as ex:
        current_app.logger.error(f"Error binding roles to indices: {ex}")
        db.session.rollback()
        raise

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

def create_fqdn_from_entity_id():
    """Create a fully qualified domain name (FQDN) from the entity ID.
    
    Returns:
        str: FQDN derived from the entity ID.
    """
    idp_entity_id = current_app.config.get('WEKO_ACCOUNTS_IDP_ENTITY_ID')
    if not idp_entity_id:
        raise KeyError('WEKO_ACCOUNTS_IDP_ENTITY_ID is missing in config')

    parsed_url = urlparse(idp_entity_id)
    fqdn = parsed_url.netloc.split(":")[0].replace('.', '_').replace('-', '_')
    return fqdn
