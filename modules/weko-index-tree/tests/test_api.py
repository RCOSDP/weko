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
from mock import patch
from elasticsearch.exceptions import NotFoundError
from invenio_access.models import Role
from invenio_communities.models import Community
from invenio_accounts.testutils import login_user_via_view, login_user_via_session
from invenio_i18n.ext import current_i18n

from weko_deposit.api import WekoDeposit
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index
from weko_index_tree import WekoIndexTree
from weko_groups.api import Group


def test_indexes(i18n_app, app, db, users, location, indices, esindex, client_rest, records, communities):
    index_one = indices["index_non_dict"]
    index_two = indices["index_non_dict_child"]

    with app.test_client() as client:
        login_user_via_session(client=client_rest, email=users[-1]['email'])
        # login_user_via_view(client=client, user=user)
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
        Indexes.get_browsing_tree_paths(33) # Additional

        app.config['WEKO_BUCKET_QUOTA_SIZE'] = 50 * 1024 * 1024 * 1024
        app.config['WEKO_MAX_FILE_SIZE'] = 50 * 1024 * 1024 * 1024
        app.config['FILES_REST_DEFAULT_STORAGE_CLASS'] = 'S'
        app.config['FILES_REST_STORAGE_CLASS_LIST'] = {
            'S': 'Standard',
            'A': 'Archive',
        }
        app.config['DEPOSIT_DEFAULT_JSONSCHEMA'] = 'deposits/'
        'deposit-v1.0.0.json'

        # Error - invenio_pidstore.errors.PIDAlreadyExists
        try:
            deposit = WekoDeposit.create({})
        except:
            pass
        
        db.session.commit()

        # Related to Error - invenio_pidstore.errors.PIDAlreadyExists
        try:
            Indexes.get_contribute_tree(deposit.pid.pid_value)
        except:
            Indexes.get_contribute_tree(1)

        Indexes.get_recursive_tree()
        Indexes.get_recursive_tree(33) # Additional

        Indexes.get_index_with_role(3)
        Indexes.get_index_with_role(33) # Additional
        Indexes.get_index(2)
        Indexes.get_index(33) # Additional
        Indexes.get_index(44) # Additional

        Indexes.get_index_by_name('test_name')

        Indexes.get_index_by_all_name()

        Indexes.get_root_index_count()

        Indexes.get_path_list([3])

        Indexes.get_path_name([3])

        Indexes.get_self_list(3)
        Indexes.get_self_list(33,community_id="comm1") # Additional

        Indexes.get_self_path(3)

        Indexes.get_child_list_recursive(1)

        Indexes.recs_reverse_query()

        Indexes.recs_query()

        Indexes.recs_tree_query()

        Indexes.recs_root_tree_query()
        # current_i18n.language = "en" # Additional
        # Indexes.recs_root_tree_query() # Additional
        
        paths = [Indexes.get_full_path(3)]
        Indexes.get_harvest_public_state(paths)
        Indexes.is_index(Indexes.get_full_path(3)) # Additional
        Indexes.is_public_state(paths)

        Indexes.is_public_state_and_not_in_future([3])

        Indexes.set_item_sort_custom(3, {})
        Indexes.set_item_sort_custom(33) # Additional

        Indexes.update_item_sort_custom_es(paths) # Additional

        Indexes.get_item_sort(3)
        Indexes.get_item_sort(33) # Additional
        
        # class Index has no "get_children" method instead it has "have_children"
        # Indexes.have_children(33) # Additional

        Indexes.get_coverpage_state([3])

        Indexes.set_coverpage_state_resc(1, True)

        #Indexes.set_public_state_resc(1, True, '220202')
        Indexes.set_public_state_resc(1, True, datetime.now())
        Indexes.set_contribute_role_resc(1, 'Admin')

        #Indexes.set_contribute_group_resc(1, [])
        Indexes.set_contribute_group_resc(1, "1")

        Indexes.set_browsing_role_resc(1, "1")

        Indexes.get_index_count()

        Indexes.get_child_list(33) # Additional

        Indexes.get_child_id_list()

        Indexes.get_list_path_publish(3)

        Indexes.get_public_indexes()

        Indexes.get_all_indexes()

        Indexes.get_all_parent_indexes(3)

        Indexes.get_full_path_reverse(33) # Additional

        Indexes.get_full_path(3)

        Indexes.get_harverted_index_list()

        # Indexes.update_set_info(index_one) # Additional

        # Indexes.delete_set_info(action="",index_id=33,id_list=[33]) # Additional

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


# class Indexes(object):
#     def create(cls, pid=None, indexes=None):
#     def update(cls, index_id, **data):
#     def delete(cls, index_id, del_self=False):
#     def delete_by_action(cls, action, index_id):

# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_api.py::test_indexes_delete_by_action -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
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

#     def move(cls, index_id, **data):
#         def _update_index(new_position, parent=None):
#         def _swap_position(i, index_tree, next_index_tree):
#         def _re_order_tree(new_position):
#     def get_index_tree(cls, pid=0):
#     def get_browsing_info(cls):
#     def get_browsing_tree(cls, pid=0):
#     def get_more_browsing_tree(cls, pid=0, more_ids=[]):
#     def get_browsing_tree_ignore_more(cls, pid=0):
#     def get_browsing_tree_paths(cls, index_id: int = 0):
#     def get_contribute_tree(cls, pid, root_node_id=0):
#     def get_recursive_tree(cls, pid: int = 0):
#     def get_index_with_role(cls, index_id):
#         def _get_allow_deny(allow, role, browse_flag=False):
#         def _get_group_allow_deny(allow_group_id=[], groups=[]):

def test_indexes_get_index_with_role(app, db, user, location):
    with app.test_client() as client:
        login_user_via_view(client=client, user=user)

        WekoIndexTree(app)
        index_metadata = {
            'id': 1,
            'parent': 0,
            'value': 'test_name',
        }
        Indexes.create(0, index_metadata)
        index = Indexes.update(1,
                       public_date="20220101",
                       browsing_group="1,2",
                       contribute_group="4,5",
                       browsing_role="",
                       contribute_role=""
                       )
        group=Group(id=1,name="test group1")
        role_test=Role(id=999,name="test role")
        role_admin = Role(id=0,name="Administrator")
        
        with db.session.begin_nested():
            db.session.add(group)
            db.session.add(role_test)
            db.session.add(role_admin)
        Indexes.get_index_with_role(1)


        with patch("weko_index_tree.api.Indexes.get_account_role",return_value="test role"):
            Indexes.get_index_with_role(1)


#     def get_index(cls, index_id, with_count=False):
#     def get_index_by_name(cls, index_name="", pid=0):
#     def get_index_by_all_name(cls, index_name=""):
#     def get_root_index_count(cls):
#     def get_account_role(cls):
#         def _get_dict(x):
#     def get_path_list(cls, node_lst):
#     def get_path_name(cls, index_ids):
#     def get_self_list(cls, index_id, community_id=None):
#     def get_self_path(cls, node_id):
#     def get_child_list_recursive(cls, pid):
#         def recursive_p():
#     def recs_reverse_query(cls, pid=0):
#     def recs_query(cls, pid=0):
#     def recs_tree_query(cls, pid=0, ):
#     def recs_root_tree_query(cls, pid=0):
#     def get_harvest_public_state(cls, paths):
#         def _query(path):
#     def is_index(cls, path):
#     def is_public_state(cls, paths):
#         def _query(path):
#     def is_public_state_and_not_in_future(cls, ids):
#         def _query(_id):
#     def set_item_sort_custom(cls, index_id, sort_json={}):
#     def update_item_sort_custom_es(cls, index_path, sort_json=[]):
#     def get_item_sort(cls, index_id):
#     def have_children(cls, index_id):
#     def get_coverpage_state(cls, indexes: list):
#     def set_coverpage_state_resc(cls, index_id, state):
#     def set_public_state_resc(cls, index_id, state, date):
#     def set_contribute_role_resc(cls, index_id, contribute_role):
#     def set_contribute_group_resc(cls, index_id, contribute_group):
#     def set_browsing_role_resc(cls, index_id, browsing_role):
#     def set_browsing_group_resc(cls, index_id, browsing_group):
#     def set_online_issn_resc(cls, index_id, online_issn):
#     def get_index_count(cls):
#     def get_child_list(cls, index_id):
#     def get_child_id_list(cls, index_id=0):
#     def get_list_path_publish(cls, index_id):
#     def get_public_indexes(cls):
#     def get_all_indexes(cls):
#     def get_all_parent_indexes(cls, index_id) -> list:
#     def get_full_path_reverse(cls, index_id=0):
#     def get_full_path(cls, index_id=0):
#     def get_harverted_index_list(cls):
#     def update_set_info(cls, index):
#     def delete_set_info(cls, action, index_id, id_list):
#     def get_public_indexes_list(cls):
