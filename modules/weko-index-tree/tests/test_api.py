# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Module tests."""

import pytest
from datetime import datetime
from elasticsearch.exceptions import NotFoundError
from invenio_access.models import Role
from weko_deposit.api import WekoDeposit

from weko_index_tree.api import Indexes
from weko_index_tree.models import Index
from weko_index_tree import WekoIndexTree

def test_indexes(app, db, user, location):
    WekoIndexTree(app)
    index_metadata = {
        'id': 1,
        'parent': 0,
        'value': 'test_name',
    }

    Indexes.create(0, index_metadata)
    Indexes.create(1, {
        'id': 2,
        'parent': 1,
        'value': 'test_name',
    })
    Indexes.create(2, {
        'id': 3,
        'parent': 2,
        'value': 'test_name',
    })
    Indexes.create(1, {
        'id': 4,
        'parent': 1,
        'value': 'test_name',
    })

    Indexes.update(2)

    data = {
        'pre_parent': 2,
        'parent': 4,
        'position': 0
    }
    Indexes.move(3, **data)
    Indexes.create(4, {
        'id': 5,
        'parent': 4,
        'value': 'test_name',
    })
    data = {
        'pre_parent': 4,
        'parent': 4,
        'position': 5
    }
    Indexes.move(3, **data)

    Indexes.get_index_tree()

    Indexes.get_browsing_info()

    Indexes.get_browsing_tree()

    Indexes.get_more_browsing_tree()

    Indexes.get_browsing_tree_ignore_more()

    Indexes.get_browsing_tree_paths()

    app.config['WEKO_BUCKET_QUOTA_SIZE'] = 50 * 1024 * 1024 * 1024
    app.config['WEKO_MAX_FILE_SIZE'] = 50 * 1024 * 1024 * 1024
    app.config['FILES_REST_DEFAULT_STORAGE_CLASS'] = 'S'
    app.config['FILES_REST_STORAGE_CLASS_LIST'] = {
        'S': 'Standard',
        'A': 'Archive',
    }
    app.config['DEPOSIT_DEFAULT_JSONSCHEMA'] = 'deposits/'
    'deposit-v1.0.0.json'
    deposit = WekoDeposit.create({})
    db.session.commit()

    Indexes.get_contribute_tree(deposit.pid.pid_value)

    Indexes.get_recursive_tree()

    Indexes.get_index_with_role(3)

    Indexes.get_index(2)

    Indexes.get_index_by_name('test_name')

    Indexes.get_index_by_all_name()

    Indexes.get_root_index_count()

    Indexes.get_path_list([3])

    Indexes.get_path_name([3])

    Indexes.get_self_list(3)

    Indexes.get_self_path(3)

    Indexes.get_child_list_recursive(1)

    Indexes.recs_reverse_query()

    Indexes.recs_query()

    Indexes.recs_tree_query()

    Indexes.recs_root_tree_query()

    paths = [Indexes.get_full_path(3)]
    Indexes.get_harvest_public_state(paths)
    Indexes.is_public_state(paths)

    Indexes.is_public_state_and_not_in_future([3])

    Indexes.set_item_sort_custom(3, {})

    Indexes.get_item_sort(3)

    Indexes.get_coverpage_state([3])

    Indexes.set_coverpage_state_resc(1, True)

    #Indexes.set_public_state_resc(1, True, '220202')
    Indexes.set_public_state_resc(1, True, datetime.now())
    Indexes.set_contribute_role_resc(1, 'Admin')

    #Indexes.set_contribute_group_resc(1, [])
    Indexes.set_contribute_group_resc(1, "1")

    Indexes.set_browsing_role_resc(1, "1")

    Indexes.get_index_count()

    Indexes.get_child_id_list()

    Indexes.get_list_path_publish(3)

    Indexes.get_public_indexes()

    Indexes.get_all_indexes()

    Indexes.get_all_parent_indexes(3)

    Indexes.get_full_path(3)

    Indexes.get_harverted_index_list()

    Indexes.get_public_indexes_list()


def test_indexes_delete(app, db):
    WekoIndexTree(app)
    index_metadata = {
        'id': 1,
        'parent': 0,
        'value': 'test_name',
    }

    parent = Indexes.create(0, index_metadata)
    child = Indexes.create(1, {
        'id': 2,
        'parent': 1,
        'value': 'test_name',
    })

    Indexes.delete(2, True)
    Indexes.delete(1)


def test_indexes_delete_by_action(app, db, user):
    WekoIndexTree(app)
    index_metadata = {
        'id': 1,
        'parent': 0,
        'value': 'test_name',
    }

    index = Indexes.create(0, index_metadata)
    child = Indexes.create(1, {
        'id': 2,
        'parent': 1,
        'value': 'test_name',
    })

    Indexes.delete_by_action('move', 2)
    with pytest.raises(NotFoundError):
        Indexes.delete_by_action('delete', 1)
