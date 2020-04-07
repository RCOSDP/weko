# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Indextree-Journal is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Permissions for index tree."""

from invenio_access import Permission, action_factory

action_indextree_journal_access = action_factory('indextree-journal-access')
indextree_journal_permission = Permission(action_indextree_journal_access)
