# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Permissions for item types."""

from invenio_access import Permission, action_factory

action_item_type_access = action_factory('item-type-access')
item_type_permission = Permission(action_item_type_access)
