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
from datetime import timedelta

from flask import abort, current_app
from flask_security import current_user
from invenio_access import Permission, action_factory
from invenio_accounts.models import User
from invenio_db import db
from weko_groups.api import Group, Membership, MembershipState
from weko_index_tree.utils import check_index_permissions, get_user_roles
from weko_records.api import ItemTypes
from weko_workflow.api import WorkActivity, WorkFlow

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
    def can(self):
        fjson = kwargs.get('fjson')
        return check_file_download_permission(record, fjson)

    return type('FileDownLoadPermissionChecker', (), {'can': can})()


def check_file_download_permission(record, fjson, is_display_file_info=False):
    """Check file download."""
    def site_license_check():
        # site license permission check
        obj = ItemTypes.get_by_id(record.get('item_type_id'))
        if obj.item_type_name.has_site_license:
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
            super_users = current_app.config[
                'WEKO_PERMISSION_SUPER_ROLE_USER'] + (
                current_app.config[
                    'WEKO_PERMISSION_ROLE_COMMUNITY'],)
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
        user_id_list = [int(record.get('owner'))]
        if record.get('weko_shared_id'):
            user_id_list.append(record.get('weko_shared_id'))
        created_user_email_list = get_email_list_by_ids(user_id_list)

        # Registered user
        if current_user and \
                current_user.is_authenticated and \
                current_user.id in user_id_list:
            return is_can

        # Super users
        supers = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] + (
            current_app.config['WEKO_PERMISSION_ROLE_COMMUNITY'],)
        for role in list(current_user.roles or []):
            if role.name in supers:
                return is_can

        try:
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
                            pdt = dt.strptime(adt, '%Y-%m-%d')
                            is_can = True if dt.today() >= pdt else False
                        else:
                            is_can = True
            # access with open date
            elif 'open_date' in acsrole:
                if is_display_file_info:
                    # Always display the file info area in 'Detail' screen.
                    is_can = True
                else:
                    try:
                        date = fjson.get('date')
                        if date and isinstance(date, list) and date[0]:
                            adt = date[0].get('dateValue')
                            pdt = dt.strptime(adt, '%Y-%m-%d')
                            is_can = True if dt.today() >= pdt else False
                    except BaseException:
                        is_can = False

                    if not is_can:
                        # site license permission check
                        is_can = site_license_check()

            # access with login user
            elif 'open_login' in acsrole:
                if is_display_file_info:
                    # Always display the file info area in 'Detail' screen.
                    is_can = True
                else:
                    is_can = False
                    users = current_app.config['WEKO_PERMISSION_ROLE_USER']
                    for lst in list(current_user.roles or []):
                        if lst.name in users:
                            is_can = True
                            break

                    # Billing file permission check
                    if fjson.get('groupsprice'):
                        is_user_group_permission = False
                        groups = fjson.get('groupsprice')
                        for group in list(groups or []):
                            group_id = group.get('group')
                            if check_user_group_permission(group_id):
                                is_user_group_permission = \
                                    check_user_group_permission(group_id)
                                break
                        is_can = is_can & is_user_group_permission
                    else:
                        if current_user.is_authenticated:
                            if fjson.get('groups'):
                                is_can = check_user_group_permission(
                                    fjson.get('groups'))
                            else:
                                is_can = True
                        if not is_can:
                            # site license permission check
                            is_can = site_license_check()

            #  can not access
            elif 'open_no' in acsrole:
                if is_display_file_info:
                    # Allow display the file info area in 'Detail' screen.
                    is_can = True
                    is_permission_user = __check_user_permission(
                        user_id_list)
                    if not current_user.is_authenticated or \
                            not is_permission_user or site_license_check():
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


def check_content_clickable(record, fjson):
    """Check if content file is clickable."""
    if not is_open_restricted(fjson):
        return False
    record_id = record.get('recid')
    file_name = fjson.get('filename')
    list_permission = __get_file_permission(record_id, file_name)
    # can click if user have not log in
    if list_permission:
        permission = list_permission[0]
        if permission.status == 0:
            return False
        else:
            return True
    else:
        return True


def check_permission_period(permission):
    """Check download permission."""
    if permission.status == 1:
        return True
    else:
        return False


def get_permission(record, fjson):
    """Get download file permission.

    @param record:
    @param fjson:
    @return:
    """
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
    :return: result
    """
    result = False
    pst = record.get('publish_status')
    pdt = record.get('pubdate', {}).get('attribute_value')
    try:
        pdt = dt.strptime(pdt, '%Y-%m-%d')
        pdt = True if dt.today() >= pdt else False
    except BaseException:
        pdt = False
    # if it's publish
    if pst and '0' in pst and pdt:
        result = True
    return result


def check_created_id(record):
    """Check Created id.

    :param record:
    :return: result
    """
    is_himself = False
    users = current_app.config['WEKO_PERMISSION_ROLE_USER']
    # Super users
    supers = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']
    user_id = current_user.get_id() \
        if current_user and current_user.is_authenticated else None
    created_id = record.get('_deposit', {}).get('created_by')
    from weko_records.serializers.utils import get_item_type_name
    item_type_id = record.get('item_type_id', '')
    item_type_name = get_item_type_name(item_type_id)
    for lst in list(current_user.roles or []):
        # In case of supper user,it's always have permission
        if lst.name in supers:
            is_himself = True
            break
        if lst.name in users:
            is_himself = True
            data_registration = current_app.config.get(
                'WEKO_ITEMS_UI_DATA_REGISTRATION')
            application_item_type_list = current_app.config.get(
                'WEKO_ITEMS_UI_APPLICATION_ITEM_TYPES_LIST')
            if item_type_name and data_registration \
                    and application_item_type_list and (
                    item_type_name == data_registration
                    or item_type_name in application_item_type_list):
                if user_id and user_id == str(created_id):
                    is_himself = True
                else:
                    is_himself = False
                break
            if lst.name == users[2]:
                is_himself = False
                shared_id = record.get('weko_shared_id')
                if user_id and created_id and user_id == str(created_id):
                    is_himself = True
                elif user_id and shared_id and user_id == str(shared_id):
                    is_himself = True
            elif lst.name == users[3]:
                is_himself = False
    return is_himself


def check_usage_report_in_permission(permission):
    """Check usage report in permission."""
    if permission.usage_report_activity_id is None:
        return True
    else:
        return False


def check_create_usage_report(record, file_json):
    """Check create usage report.

    @param record:
    @param file_json:
    @return:
    """
    record_id = record.get('recid')
    file_name = file_json.get('filename')
    list_permission = __get_file_permission(record_id, file_name)
    if list_permission:
        permission = list_permission[0]
        if check_usage_report_in_permission(permission):
            return permission
        else:
            return None


def __get_file_permission(record_id, file_name):
    """Get file permission."""
    user_id = current_user.get_id()
    current_time = dt.now()
    duration = current_time - timedelta(
        days=current_app.config['WEKO_RECORDS_UI_DOWNLOAD_DAYS'])
    list_permission = FilePermission.find_list_permission_by_date(
        user_id, record_id, file_name, duration)
    return list_permission
