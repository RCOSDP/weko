# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Permissions for communities."""

from __future__ import absolute_import, print_function

import humanize

from datetime import datetime, timedelta

from flask import current_app
from flask_login import current_user
from flask_principal import ActionNeed
from invenio_access.permissions import Permission

from invenio_communities.utils import get_user_role_ids


class _Permission(object):
    """Temporary solution to permissions.

    Grant access to owners of community or admin.
    TODO: Use fine-grained permissions.
    """

    def __init__(self, community, action):
        """Initialize."""
        self.community = community
        self.action = action

    def can(self):
        """Grant permission if owner or admin."""
        role_ids = get_user_role_ids()
        return int(self.community.id_role) in role_ids or \
            Permission(ActionNeed('admin-access')).can()


def permission_factory(community, action):
    """Permission factory for the actions on Bucket and ObjectVersion items.

    :param community: Community object to be accessed.
    :type community: `invenio_communities.models.Community`
    :param action: Action name for access.
    :type action: str
    """
    return _Permission(community, action)


def can_user_create_community(user):
    """Checks it the user can create community."""
    current_date = datetime.now()
    confirmed_date = getattr(user, 'confirmed_at', None)
    community_user_confirmed_since = \
        current_app.config['COMMUNITIES_USER_CONFIRMED_SINCE']

    if confirmed_date is None:
        return False, 'You have not yet confirmed your account.'

    delta = current_date - confirmed_date

    if delta < community_user_confirmed_since:
        return False, 'To create a community your account must be verified ' \
           'for at least {}. If you want to speed up the process, you ' \
           'can contact our support team describing your case.' \
               .format(humanize.naturaldelta(
               current_app.config['COMMUNITIES_USER_CONFIRMED_SINCE']))

    return True, ''
