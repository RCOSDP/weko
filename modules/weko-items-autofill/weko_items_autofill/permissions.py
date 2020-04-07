# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Items-Autofill is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Permissions for schemas."""

from invenio_access import Permission, action_factory

action_auto_fill = action_factory('items-autofill')
auto_fill_permission = Permission(action_auto_fill)
