# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Permissions for schemas."""

from invenio_access import Permission, action_factory

action_schema_access = action_factory('schema-access')
schema_permission = Permission(action_schema_access)
