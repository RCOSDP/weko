# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Permissions for Search."""

from invenio_access import Permission, action_factory

action_search_access = action_factory('search-access')
search_permission = Permission(action_search_access)
