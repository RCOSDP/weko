# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""Serializer class."""

from flask_login import current_user
from invenio_accounts.models import User
from weko_user_profiles.models import UserProfile


def file_uploaded_owner(created_user_id=0, updated_user_id=0):
    """Build upload file owners.

    :param created_user_id: The created user id. (Default: ``0``)
    :param updated_user_id: The updated user id. (Default: ``0``)
    :returns: A response with json data.
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
        show_created_user = True
        show_updated_user = True

        created_user = User.query.get_or_404(created_user_id)
        if created_user is not None:
            created_email = created_user.email
        created_userprofile = UserProfile.get_by_userid(created_user_id)
        if created_userprofile is not None:
            created_username = created_userprofile._username
            created_displayname = created_userprofile._displayname

        updated_user = User.query.get_or_404(updated_user_id)
        if updated_user is not None:
            updated_email = updated_user.email
        updated_userprofile = UserProfile.get_by_userid(updated_user_id)
        if updated_userprofile is not None:
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
