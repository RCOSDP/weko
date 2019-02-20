# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Indextree-Journal is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of weko-indextree-journal."""

# TODO: This is an example file. Remove it if your package does not use any
# extra configuration variables.
WEKO_INDEXTREE_JOURNAL_DEFAULT_VALUE = 'foobar'
"""Default value for the application."""

WEKO_INDEXTREE_JOURNAL_BASE_TEMPLATE = 'weko_indextree_journal/base.html'
"""Default base template for the indextree journal page."""

WEKO_INDEXTREE_JOURNAL_INDEX_TEMPLATE = 'weko_indextree_journal/index.html'
"""Index template for the indextree journal page."""

WEKO_INDEXTREE_JOURNAL_CONTENT_TEMPLATE = 'weko_indextree_journal/journal.html'
"""Index template for the indextree journal page."""

WEKO_INDEXTREE_JOURNAL_API = "/api/indextree/journal"

WEKO_INDEXTREE_JOURNAL_LIST_API = "/api/journal"

_IID = 'iid(tid,record_class="weko_indextree_journal.api:Journals")'

WEKO_INDEXTREE_JOURNAL_REST_ENDPOINTS = dict(
    tid=dict(
        record_class='weko_indextree_journal.api:Journals',
        indextree_journal_route='/indextree/journal/<int:journal_id>',
        journal_route='/indextree/journal',
        # item_tree_journal_route='/tree/journal/<int:pid_value>',
        # journal_move_route='/tree/journal/move/<int:index_id>',
        default_media_type='application/json',
        create_permission_factory_imp=
        'weko_indextree_journal.permissions:indextree_journal_permission',
        read_permission_factory_imp=
        'weko_indextree_journal.permissions:indextree_journal_permission',
        update_permission_factory_imp=
        'weko_indextree_journal.permissions:indextree_journal_permission',
        delete_permission_factory_imp=
        'weko_indextree_journal.permissions:indextree_journal_permission',
    )
)

WEKO_INDEXTREE_JOURNAL_UPDATED = True
"""For index tree cache."""