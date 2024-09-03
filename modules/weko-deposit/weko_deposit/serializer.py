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
"""Serializer class."""

from flask_login import current_user
from invenio_accounts.models import User
from weko_user_profiles.models import UserProfile

from .logger import weko_logger


def file_uploaded_owner(created_user_id=0, updated_user_id=0):
    """Build upload file owners.

    Args:
        created_user_id(int, Optional): The created user id. Defaults to `0`
        updated_user_id(int, Optional): The updated user id. Defaults to `0`

    Returns:
        dict: A dictionary with created_user and updated_user data.
            Each user data is dictionary that contains user_id, username,\
            displayname, email.
    """
    # created user.
    created_username = ''
    created_displayname = ''
    created_email = ''
    show_created_user = False

    # updated user.
    updated_username = ''
    updated_displayname = ''
    updated_email = ''
    show_updated_user = False

    if current_user.is_authenticated:
        weko_logger(key='WEKO_COMMON_IF_ENTER',
                    branch="current_user.is_authenticated is True")
        show_created_user = True
        show_updated_user = True

        created_user = User.query.get_or_404(created_user_id)
        if created_user is not None:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="created_user is not None")
            created_email = created_user.email

        created_userprofile = UserProfile.get_by_userid(created_user_id)

        if created_userprofile is not None:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="created_userprofile is not None")
            created_username = created_userprofile._username
            created_displayname = created_userprofile._displayname

        updated_user = User.query.get_or_404(updated_user_id)

        if updated_user is not None:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="updated_user is not None")
            updated_email = updated_user.email

        updated_userprofile = UserProfile.get_by_userid(updated_user_id)

        if updated_userprofile is not None:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="updated_userprofile is not None")
            updated_username = updated_userprofile._username
            updated_displayname = updated_userprofile._displayname

    return {
        'created_user': {
            'user_id': created_user_id if show_created_user else 0,
            'username': created_username,
            'displayname': created_displayname,
            'email': created_email,
        },
        'updated_user': {
            'user_id': updated_user_id if show_updated_user else 0,
            'username': updated_username,
            'displayname': updated_displayname,
            'email': updated_email,
        }
    }
