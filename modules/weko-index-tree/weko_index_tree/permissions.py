# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Permissions for index tree."""

from invenio_access import Permission, action_factory

action_index_tree_access = action_factory('index-tree-access')
index_tree_permission = Permission(action_index_tree_access)
