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

"""Permissions for Detail Page."""

from datetime import datetime as dt
from datetime import timedelta, timezone
import traceback
from typing import List, Optional

from flask import abort, current_app, request
from flask_babelex import get_locale, to_user_timezone, to_utc
from flask_security import current_user
from invenio_access import Permission, action_factory
from invenio_accounts.models import User
from invenio_db import db
from invenio_deposit.scopes import write_scope
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from weko_groups.api import Group, Membership, MembershipState
from weko_index_tree.utils import check_index_permissions, get_user_roles
from weko_records.api import ItemTypes
from weko_workflow.api import WorkActivity

from .ipaddr import check_site_license_permission
from .models import FilePermission

action_detail_page_access = action_factory('detail-page-access')
detail_page_permission = Permission(action_detail_page_access)

action_download_original_pdf_access = action_factory(
    'download-original-pdf-access')
download_original_pdf_permission = Permission(
    action_download_original_pdf_access)


def page_permission_factory(record, *args, **kwargs):
    """Page permission factory."""

    def can(self):
        is_ok = False

        # get user role info
        roles = get_user_roles()
        # person himself check
        is_himself = check_created_id(record)
        if roles[0] or is_himself:
            is_ok = True
        else:   # if not admin user and not creator
            # item publish status check
            is_pub = check_publish_status(record)
            if is_pub:
                # check the list of authorized indexes
                if check_index_permissions(record):
                    is_ok = True

        return is_ok

    return type('DetailPagePermissionChecker', (), {'can': can})()


def file_permission_factory(record, *args, **kwargs):
    """File permission factory."""

    @require_api_auth()
    @require_oauth_scopes(write_scope.id)
    def can_by_oauth(fjson):
        return check_file_download_permission(record, fjson)

    def can(self):
        is_ok = False
        fjson = kwargs.get('fjson')
        if request.headers and \
                request.headers.get(current_app.config['OAUTH2SERVER_JWT_AUTH_HEADER']):
            is_ok = can_by_oauth(fjson)
        else:
            item_type = kwargs.get('item_type', None)
            is_ok = check_file_download_permission(record, fjson, item_type)
        return is_ok

    return type('FileDownLoadPermissionChecker', (), {'can': can})()


def check_file_download_permission(record, fjson, is_display_file_info=False, item_type=None):
    """Check file download."""
    def site_license_check(item_type):
        # site license permission check
        if not item_type:
            item_type = ItemTypes.get_by_id(record.get('item_type_id'))
        if item_type.item_type_name.has_site_license:
            return check_site_license_permission(
            ) | check_user_group_permission(fjson.get('groups'))
        return False

    def get_email_list_by_ids(user_id_list):
        """Get user email list by user id list.

        :param user_id_list: list id of users in table accounts_user.
        :return: list email.
        """
        with db.session.no_autoflush:
            users = User.query.filter(User.id.in_(user_id_list)).all()
            emails = [x.email for x in users]
        return emails

    def __check_user_permission(user_id_list):
        """Check user permission.

        :return: True if the login user is allowed to display file metadata.
        """
        is_ok = False
        # Check guest user
        if not current_user.is_authenticated:
            return is_ok
        # Check registered user
        elif current_user and current_user.id in user_id_list:
            is_ok = True
        # Check super users
        else:
            super_users = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] + \
                current_app.config['WEKO_PERMISSION_ROLE_COMMUNITY']
            for role in list(current_user.roles or []):
                if role.name in super_users:
                    is_ok = True
                    break
        return is_ok

    if fjson:
        is_can = True
        acsrole = fjson.get('accessrole', '')
        # Get email of login user.
        is_has_email = hasattr(current_user, "email")
        current_user_email = current_user.email if is_has_email else ''

        # Get email list of created workflow user.
        user_id_list = [int(record['owner'])] if record.get('owner') else []
        if record.get('weko_shared_ids'):
            user_id_list.extend(record.get('weko_shared_ids'))
        created_user_email_list = get_email_list_by_ids(user_id_list)

        # Registered user
        if current_user and \
                current_user.is_authenticated and \
                current_user.id in user_id_list:
            return is_can

        # Super users
        supers = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] + \
            current_app.config['WEKO_PERMISSION_ROLE_COMMUNITY']
        for role in list(current_user.roles or []):
            if role.name in supers:
                return is_can

        try:
            from .utils import is_future
            # can access
            if 'open_access' in acsrole:
                if is_display_file_info:
                    # Always display the file info area in 'Detail' screen.
                    is_can = True
                else:
                    date = fjson.get('date')
                    if date and isinstance(date, list) and date[0]:
                        adt = date[0].get('dateValue')
                        if adt:
                            is_can = not is_future(adt)
                        else:
                            is_can = True
            # access with open date
            elif 'open_date' in acsrole:
                if is_display_file_info:
                    # Always display the file info area in 'Detail' screen.
                    is_can = True
                else:
                    try:
                        # contents accessdate
                        c_is_can = False
                        access_date = fjson.get('accessdate',None)
                        if access_date:
                            c_is_can = not is_future(access_date)
                        else:
                            # get date list and check dateValue is future 
                            date_list = fjson.get('date')
                            if date_list and isinstance(date_list, list) and date_list[0]:
                                adt = date_list[0].get('dateValue')
                                c_is_can = not is_future(adt)

                        # publish date
                        idt = record.get('publish_date')
                        p_is_can = not is_future(idt)

                        # roles check
                        role_is_can = False
                        roles = fjson.get('roles')
                        if c_is_can and p_is_can:
                            role_is_can = True
                        elif roles and isinstance(roles, list) and len(roles)>0:
                            for lst in list(current_user.roles or []):
                                for role_value in [ role.get('role') for role in roles ]:
                                    if __isint(role_value):
                                        if lst.id == int(role_value):
                                            role_is_can = True
                                            if role_is_can:
                                                c_is_can = True
                                            break
                                    else:
                                        if lst.name == role_value:
                                            role_is_can = True
                                            if role_is_can:
                                                c_is_can = True
                                            break
                            # ログインユーザーに権限なしの場合でも、コンテンツで「非ログインユーザー」指定した場合OK
                            # if len(list(current_user.roles))==0:
                            #     if 'none_loggin' in [ role.get('role') for role in roles ]:
                            #         role_is_can = True
                        else:
                            role_is_can = True

                        is_can = c_is_can and p_is_can and role_is_can

                    except BaseException:
                        is_can = False

                    if not is_can:
                        # site license permission check
                        is_can = site_license_check(item_type)

            # access with login user
            elif 'open_login' in acsrole:
                if is_display_file_info:
                    # Always display the file info area in 'Detail' screen.
                    is_can = True
                else:
                    # ログインユーザーか
                    is_login_user = current_user.is_authenticated

                    # rolesで指定されたユーザーロールか
                    is_role_can = False
                    roles = fjson.get('roles')
                    if roles and isinstance(roles, list) and len(roles)>0:
                        for lst in list(current_user.roles or []):
                            for role_value in [ role.get('role') for role in roles ]:
                                if __isint(role_value):
                                    if lst.id == int(role_value):
                                        is_role_can = True
                                        break
                                else:
                                    if lst.name == role_value:
                                        is_role_can = True
                                        break
                        # ログインユーザーに権限なしの場合でも、コンテンツで「非ログインユーザー」指定した場合OK
                        # if 'none_loggin' in [ role.get('role') for role in roles ]:
                        #     is_role_can = True

                    else:
                        is_role_can = True

                    # Billing file permission check
                    is_billing_can = False
                    if fjson.get('groupsprice'):
                        is_user_group_permission = False
                        groups = fjson.get('groupsprice')
                        for group in list(groups or []):
                            group_id = group.get('group')
                            if check_user_group_permission(group_id):
                                is_user_group_permission = check_user_group_permission(group_id)
                                break
                        is_billing_can = is_user_group_permission
                    else:
                        if current_user.is_authenticated:
                            if fjson.get('groups'):
                                is_billing_can = check_user_group_permission(fjson.get('groups'))
                            else:
                                is_billing_can = True
                        if not is_billing_can:
                            # site license permission check
                            is_billing_can = site_license_check(item_type)

                    is_can = is_login_user and is_role_can and is_billing_can

            #  can not access
            elif 'open_no' in acsrole:
                if is_display_file_info:
                    # Allow display the file info area in 'Detail' screen.
                    is_can = True
                    is_permission_user = __check_user_permission(
                        user_id_list)
                    if not current_user.is_authenticated or \
                            not is_permission_user or site_license_check(item_type):
                        is_can = False
                else:
                    if current_user_email in created_user_email_list:
                        # Allow created workflow user view file.
                        is_can = True
                    else:
                        is_can = False
            elif 'open_restricted' in acsrole:
                is_can = check_open_restricted_permission(record, fjson)
        except BaseException:
            abort(500)
        return is_can


def check_open_restricted_permission(record, fjson):
    """Check 'open_restricted' file permission."""
    record_id = record.get('recid')
    file_name = fjson.get('filename')
    list_permission = __get_file_permission(record_id, file_name)
    if list_permission:
        permission = list_permission[0]
        return check_permission_period(permission)
    else:
        return False


def is_open_restricted(file_data):
    """Check open restricted.

    @param file_data:
    @return:
    """
    result = False
    if file_data:
        access_role = file_data.get('accessrole', '')
        if 'open_restricted' in access_role:
            result = True
    return result

def check_content_clickable(record:dict, fjson:dict) -> bool:
    """Check if content file is Applyable.
        Args
            record: the records metadata
            fjson: file object json

        Returns
            bool: is content Applyable
    """
    if not is_open_restricted(fjson):
        return False
    return not check_open_restricted_permission(record, fjson)


def check_permission_period(permission : FilePermission) -> bool :
    """Check download permission.
        Args
            FilePermission:permission
        Returns 
            bool:is the user has access rights or not
    """

    from weko_records_ui.utils import get_valid_onetime_download
    from weko_items_ui.utils import get_user_information

    if permission.status == 1:
        res = get_valid_onetime_download(permission.file_name ,permission.record_id , get_user_information(permission.user_id)[0]['email'])
        current_app.logger.info(res)
        return res is not None
    else:
        return False


def get_permission(record:dict, fjson:dict) -> Optional[FilePermission]:
    """Get download file permission.
    Args
        record: the records metadata
        fjson: file object json
    Returns
        FilePermission or None
    """
    # current_app.logger.debug("fjson: {}".format(fjson))
    if not check_file_download_permission(record, fjson):
        return None
    record_id = record.get('recid')
    file_name = fjson.get('filename')
    list_permission = __get_file_permission(record_id, file_name)
    if list_permission:
        permission = list_permission[0]
        if permission.status == 1:
            return permission
        else:
            activity_id = permission.usage_application_activity_id
            activity = WorkActivity()
            steps = activity.get_activity_steps(activity_id)
            if steps:
                for step in steps:
                    if step and step['Status'] == 'action_canceled':
                        return None
            return permission
    else:
        return None


def check_original_pdf_download_permission(record):
    """Check original pdf."""
    is_ok = True
    # item publish status check
    is_pub = check_publish_status(record)
    # role permission
    is_can = download_original_pdf_permission.can()
    # person himself check
    is_himself = check_created_id(record)
    # Only allow to download original pdf if one of
    # the following condition is matched
    # - is_himself
    # - record is published and user (not is_himself) has the permission
    if not is_himself:
        if is_pub:
            if not is_can:
                is_ok = False
        else:
            is_ok = False
    return is_ok


def check_user_group_permission(group_id):
    """Check user group  permission.

    :param group_id: Group_id
    """
    user_id = current_user.get_id()
    is_ok = False
    if group_id:
        try:
            group_id = int(group_id)
        except ValueError:
            return is_ok
        if user_id:
            query = Group.query.filter_by(id=group_id).join(Membership) \
                .filter_by(user_id=user_id, state=MembershipState.ACTIVE)
            if query.count() > 0:
                is_ok = True
    return is_ok


def check_publish_status(record):
    """Check Publish Status.

    :param record:
    :return: record is public
    """
    from .utils import is_future
    pst = record.get('publish_status')
    pdt = record.get('pubdate', {}).get('attribute_value')
    return pst and '0' in pst and not is_future(pdt)


# def check_created_id(record):
#     """Check Created id.
#      :param record:
#      :return: result
#     """
#     is_himself = False
#     users = current_app.config['WEKO_PERMISSION_ROLE_USER']
#     # Super users
#     supers = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']
#     user_id = current_user.get_id() \
#         if current_user and current_user.is_authenticated else None
#     created_id = record.get('_deposit', {}).get('created_by')
#     from weko_records.serializers.utils import get_item_type_name
#     item_type_id = record.get('item_type_id', '')
#     item_type_name = get_item_type_name(item_type_id)
#     for lst in list(current_user.roles or []):
#         # In case of supper user,it's always have permission
#         if lst.name in supers:
#             is_himself = True
#             break
#         if lst.name in users:
#             is_himself = True
#             data_registration = current_app.config.get(
#                 'WEKO_ITEMS_UI_DATA_REGISTRATION')
#             application_item_type_list = current_app.config.get(
#                 'WEKO_ITEMS_UI_APPLICATION_ITEM_TYPES_LIST')
#             if item_type_name and data_registration \
#                     and application_item_type_list and (
#                     item_type_name == data_registration
#                     or item_type_name in application_item_type_list):
#                 if user_id and user_id == str(created_id):
#                     is_himself = True
#                 else:
#                     is_himself = False
#                 break
#             if lst.name == users[2]:
#                 is_himself = False
#                 shared_ids = record.get('weko_shared_ids')
#                 if user_id and created_id and user_id == str(created_id):
#                     is_himself = True
#                 elif user_id and shared_ids and str(user_id) in shared_ids:
#                     is_himself = True
#             elif lst.name == users[3]:
#                 is_himself = False
#     return is_himself

def check_created_id(record):
    """Check edit permission to the record for the current user

    Args:
        record (dict): the record to check edit permission.
        example: {'_oai': {'id': 'oai:weko3.example.org:00000001', 'sets': ['1657555088462']}, 'path': ['1657555088462'], 'owner': '1', 'recid': '1', 'title': ['a'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-07-12'}, '_buckets': {'deposit': '35004d51-8938-4e77-87d7-0c9e176b8e7b'}, '_deposit': {'id': '1', 'pid': {'type': 'depid', 'value': '1', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'a', 'author_link': [], 'item_type_id': '15', 'publish_date': '2022-07-12', 'publish_status': '0', 'weko_shared_ids': [], 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'a', 'subitem_1551255648112': 'ja'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True}

    Returns:
        bool: True is the current user has the edit permission.
    """    
    is_himself = False
    # Super users
    supers = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']
    user_id = current_user.get_id() \
            if current_user and current_user.is_authenticated else None
    if user_id is not None:
        created_id = record.get('_deposit', {}).get('created_by')
        shared_ids = record.get('weko_shared_ids')
        if user_id and created_id and user_id == str(created_id):
            is_himself = True
        elif user_id and len(shared_ids)>0 and int(user_id) in shared_ids:
            is_himself = True
        for lst in list(current_user.roles or []):
            # In case of supper user,it's always have permission
            if lst.name in supers:
                is_himself = True
    return is_himself


def check_usage_report_in_permission(permission):
    """Check usage report in permission."""
    if permission.usage_report_activity_id is None:
        return True
    else:
        return False


def check_create_usage_report(record, file_json , user_id=None):
    """Check create usage report.

    @param record:
    @param file_json:
    @return:
    """
    record_id = record.get('recid')
    file_name = file_json.get('filename')
    list_permission = __get_file_permission(record_id, file_name ,user_id)
    for permission in list_permission:
        if check_usage_report_in_permission(permission):
            return permission
    return None

def is_owners_or_superusers(record) -> bool:
    """ 
    return true if the user can download the record's contents unconditionally

    Args
        record: The record metadata.

    Returns
        bool: is owners or superusers
    """
    # Get email list of created workflow user.
    user_id_list = [int(record['owner'])] if record.get('owner') else []
    if record.get('weko_shared_ids'):
        user_id_list.extend(record.get('weko_shared_ids'))

    # Registered user
    if current_user and \
            current_user.is_authenticated and \
            current_user.id in user_id_list:
        return True

    # Super users
    supers = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] + \
        current_app.config['WEKO_PERMISSION_ROLE_COMMUNITY']
    for role in list(current_user.roles or []):
        if role.name in supers:
            return True
    
    return False


def __get_file_permission(record_id:str, file_name:str ,user_id = None) -> List[FilePermission]:
    """Get file permission.
        Args
            str:record_id
            str:file_name
        Returns
            List[FilePermission]
    """
    user_id = user_id or current_user.get_id()
    list_permission = FilePermission.find_list_permission_approved(
        user_id, record_id, file_name)
    return list_permission

def __isint(str):
    try:
        int(str, 10)
    except ValueError:
        return False
    else:
        return True