# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Permissions for deposit."""

import pkg_resources
from flask_principal import ActionNeed

action_admin_access = ActionNeed('deposit-admin-access')


def admin_permission_factory():
    """Factory for creating a permission for an admin `deposit-admin-access`.

    If `invenio-access` module is installed, it returns a
    :class:`invenio_access.permissions.Permission` object.
    Otherwise, it returns a :class:`flask_principal.Permission` object.

    :returns: Permission instance.
    """
    try:
        pkg_resources.get_distribution('invenio-access')
        from invenio_access.permissions import Permission
    except pkg_resources.DistributionNotFound:
        from flask_principal import Permission

    return Permission(action_admin_access)
