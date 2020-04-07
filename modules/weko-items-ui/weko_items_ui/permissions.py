# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Permissions for items."""

from invenio_access import Permission, action_factory
from weko_records_ui.permissions import page_permission_factory

action_item_access = action_factory('item-access')
item_permission = Permission(action_item_access)


def edit_permission_factory(record, **kwargs):
    """Edit permission factory."""
    def can(self):
        return page_permission_factory(record, flg='Edit').can()
    return type('EditPermissionChecker', (), {'can': can})()
