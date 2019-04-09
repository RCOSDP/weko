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

from flask import abort, current_app
from flask_security import current_user
from invenio_access import Permission, action_factory
from weko_groups.api import Group, Membership, MembershipState
from weko_records.api import ItemTypes

from .ipaddr import check_site_license_permission

action_detail_page_access = action_factory('detail-page-access')
detail_page_permission = Permission(action_detail_page_access)

action_download_original_pdf_access = action_factory('download-original-pdf-access')
download_original_pdf_permission = Permission(action_download_original_pdf_access)

def page_permission_factory(record, *args, **kwargs):
    def can(self):
        is_ok = True
        # item publish status check
        is_pub = check_publish_status(record)
        # role permission
        is_can = detail_page_permission.can()
        # person himself check
        is_himself = check_created_id(record)
        if not is_pub:
            if not is_can or (is_can and not is_himself):
                is_ok = False
        else:
            if kwargs.get('flg'):
                if not is_can or (is_can and not is_himself):
                    is_ok = False
        return is_ok

    return type('DetailPagePermissionChecker', (), {'can': can})()


def file_permission_factory(record, *args, **kwargs):
    def can(self):
        fjson = kwargs.get('fjson')
        return check_file_download_permission(record, fjson)

    return type('FileDownLoadPermissionChecker', (), {'can': can})()


def check_file_download_permission(record, fjson):

    def site_license_check():
        # site license permission check
        obj = ItemTypes.get_by_id(record.get('item_type_id'))
        if obj.item_type_name.has_site_license:
            return check_site_license_permission() | check_user_group_permission(
                    fjson.get('groups'))
        return False

    if fjson:
        is_can = True
        acsrole = fjson.get('accessrole', '')

        # Super users
        supers = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']
        for role in list(current_user.roles or []):
            if role.name in supers:
                return is_can

        try:
            # can access
            if 'open_access' in acsrole:
                pass
            # access with open date
            elif 'open_date' in acsrole:
                try:
                    adt = fjson.get('accessdate')
                    pdt = dt.strptime(adt, '%Y-%m-%d')
                    is_can = True if dt.today() >= pdt else False
                except:
                    is_can = False

                if not is_can:
                    # site license permission check
                    is_can = site_license_check()

            # access with login user
            elif 'open_login' in acsrole:
                is_can = False
                users = current_app.config['WEKO_PERMISSION_ROLE_USER']
                for lst in list(current_user.roles or []):
                    if lst.name in users:
                        is_can = True
                        break

                is_can = is_can & check_user_group_permission(
                    fjson.get('groups'))

            #  can not access
            elif 'open_no' in acsrole:
                # site license permission check
                is_can = site_license_check()
        except:
            abort(500)
        return is_can


def check_original_pdf_download_permission(record):
    is_ok = True
    # item publish status check
    is_pub = check_publish_status(record)
    # role permission
    is_can = download_original_pdf_permission.can()
    # person himself check
    is_himself = check_created_id(record)
    # Only allow to download original pdf if one of the following condition is matched
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
    for lst in list(current_user.roles or []):
        if lst.name in users:
            is_himself = True
            if lst.name == users[2]:
                is_himself = False
                user_id = current_user.get_id() \
                    if current_user and current_user.is_authenticated else None
                created_id = record.get('_deposit', {}).get('created_by')
                if user_id and created_id and user_id == str(created_id):
                    is_himself = True
            elif lst.name == users[3]:
                is_himself = False
    return is_himself
