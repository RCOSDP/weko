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
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_api.py -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp


import pytest
import copy
from datetime import datetime
from mock import patch, Mock, MagicMock

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


# class Indexes(object):
#     def create(cls, pid=None, indexes=None):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_api.py::test_indexes_create -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_indexes_create(app, db, users, test_indices):
    app.config['WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER'] = 5
    with app.test_client() as client:
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            res = Indexes.create(0, {
                'id': 4,
                'parent': 3,
                'value': 'Create index test1',
            })
            assert res==True
            res = Indexes.create(1, {
                'id': 12,
                'parent': 1,
                'value': 'Create index test2',
            })
            assert res==True
            res = Indexes.create(2, {
                'id': 23,
                'parent': 3,
                'value': 'Create index test3',
            })
            assert res==True
            res = Indexes.create(2, {
                'id': 23,
                'parent': 3,
                'value': 'Create index test3',
            })
            assert res==False
            res = Indexes.create(0)
            assert res==None
            res = Indexes.create(0, {'id': None})
            assert res==None


# class Indexes(object):
#     def update(cls, index_id, **data):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_api.py::test_indexes_update -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_indexes_update(app, db, users, test_indices):
    index_metadata = {
        "biblio_flag": False,
        "browsing_group": {
            "allow": [],
            "deny": []
        },
        "browsing_role": {
            "allow": [
            {
                "id": 3,
                "name": "Contributor"
            },
            {
                "id": -98,
                "name": "Authenticated User"
            },
            {
                "id": -99,
                "name": "Guest"
            }
            ],
            "deny": []
        },
        "can_edit": True,
        "comment": "",
        "contribute_group": {
            "allow": [],
            "deny": []
        },
        "contribute_role": {
            "allow": [
            {
                "id": 1,
                "name": "System Administrator"
            },
            {
                "id": 2,
                "name": "Repository Administrator"
            },
            {
                "id": 3,
                "name": "Contributor"
            },
            {
                "id": 4,
                "name": "Community Administrator"
            },
            {
                "id": -98,
                "name": "Authenticated User"
            },
            {
                "id": -99,
                "name": "Guest"
            }
            ],
            "deny": []
        },
        "coverpage_state": False,
        "display_format": "1",
        "display_no": 5,
        "harvest_public_state": True,
        "harvest_spec": "",
        "have_children": False,
        "id": 1,
        "image_name": "",
        "index_link_enabled": False,
        "index_link_name": "Test index 1 new",
        "index_link_name_english": "Test index 1 new",
        "index_name": "Test index 1 new",
        "index_name_english": "Test index 1 new",
        "more_check": False,
        "online_issn": "",
        "owner_user_id": 3,
        "parent": 0,
        "position": 0,
        "public_date": "20220201",
        "public_state": True,
        "recursive_browsing_group": True,
        "recursive_browsing_role": True,
        "recursive_contribute_group": True,
        "recursive_contribute_role": True,
        "recursive_coverpage_check": False,
        "recursive_public_state": True,
        "rss_status": True
    }
    with app.test_client() as client:
        login_user_via_session(client=client, email=users[3]['email'])
        # need to fix
        with pytest.raises(Exception) as e:
            Indexes.update(2)
        assert e.type==AttributeError
        res = Indexes.update(0)
        assert res==None
        with pytest.raises(Exception) as e:
            Indexes.update(1, **index_metadata)
        assert e.type==AttributeError


# class Indexes(object):
#     def delete(cls, index_id, del_self=False):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_api.py::test_indexes_delete -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_indexes_delete(app, db, users, test_indices):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        res = Indexes.delete(11, True)
        assert res==None
    # need to fix
    res = Indexes.delete(10)
    assert res==0


# class Indexes(object):
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

    res = Indexes.delete_by_action('move', 2)
    assert res==None
    res = Indexes.delete_by_action('delete', 1)
    assert res==0


# class Indexes(object):
#     def move(cls, index_id, **data):
#         def _update_index(new_position, parent=None):
#         def _swap_position(i, index_tree, next_index_tree):
#         def _re_order_tree(new_position):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_api.py::test_indexes_move -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_indexes_move(app, db, users, test_indices):
    with app.test_request_context(
        headers=[('Accept-Language','en')]):
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            _data = {
                'pre_parent': 2,
                'parent': None,
                'position': 1
            }
            res = Indexes.move(22, **_data)
            assert res['is_ok']==False
            assert res['msg']=='Select an index to move.'

            _data = {
                'pre_parent': 2,
                'parent': 22,
                'position': 1
            }
            res = Indexes.move(22, **_data)
            assert res['is_ok']==False
            assert res['msg']=='Fail move an index.'
                        
            _data = {
                'pre_parent': 2,
                'parent': 1,
                'position': 1
            }
            res = Indexes.move(22, **_data)
            assert res['is_ok']==False
            assert res['msg']=="The index cannot be kept private because there are links from items that have a DOI."
            
            _index = dict(Indexes.get_index(1))
            
            assert _index["parent"] == 0
            assert _index["position"] == 0
            
            _data = {
                'pre_parent': "0",
                'parent': "0",
                'position': 3
            }
            res = Indexes.move(1, **_data)
            assert res['is_ok']==True
            assert res['msg']==''
            
            _index = dict(Indexes.get_index(1))
            assert _index["parent"] == 0
            assert _index["position"] == 4

            _data = {
                'pre_parent': 0,
                'parent': 0,
                'position': 2
            }
            res = Indexes.move(1, **_data)
            assert res['is_ok']==False
            assert res['msg']=='Select an index to move.'
            
            _index = dict(Indexes.get_index(1))
            assert _index["parent"] == 0
            assert _index["position"] == 4
            
            
            _data = {
                'pre_parent': 0,
                'parent': 0,
                'position': 4
            }
            res = Indexes.move(1, **_data)
            assert res['is_ok']==False
            assert res['msg']=='Select an index to move.'
            
            _index = dict(Indexes.get_index(1))
            assert _index["parent"] == 0
            assert _index["position"] == 4


# class Indexes(object):
#     def get_index_tree(cls, pid=0):
#     def get_browsing_info(cls):
#     def get_browsing_tree(cls, pid=0):
#     def get_more_browsing_tree(cls, pid=0, more_ids=[]):
#     def get_browsing_tree_ignore_more(cls, pid=0):
#     def get_browsing_tree_paths(cls, index_id: int = 0):
#     def get_recursive_tree(cls, pid: int = 0):
#     def get_index_with_role(cls, index_id):
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
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_api.py::test_update_set_info -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_update_set_info(i18n_app, db, users, test_indices):
    _tmp = Indexes.get_index(1)
    index_info = copy.deepcopy(dict(_tmp))
    assert index_info["index_name"]=="Test index 1"
    index_info["index_name"] = "TEST"
    with patch("weko_index_tree.tasks.update_oaiset_setting.delay",side_effect = MagicMock()):
        Indexes.update_set_info(index_info)
    
    
#     def delete_set_info(cls, action, index_id, id_list):
#     def get_public_indexes_list(cls):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_api.py::test_indexes_get_index_tree -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_indexes_get_index_tree(i18n_app, db, users, test_indices):
    with i18n_app.test_client() as client:
        # get_index_tree
        res = Indexes.get_index_tree()
        assert len(res)==3

        # get_browsing_info
        res = Indexes.get_browsing_info()
        assert res["1"]["browsing_role"]==['3', '-98', '-99']
        assert res["1"]["index_name"]=="Test index 1"
        assert res["1"]["parent"]=="0"
        assert res["1"]["public_date"]==datetime(2022, 1, 1)
        assert res["1"]["harvest_public_state"]==True

        # get_browsing_tree
        res = Indexes.get_browsing_tree(1)
        assert len(res)==1

        # get_more_browsing_tree
        res = Indexes.get_more_browsing_tree()
        assert len(res)==3

        # get_browsing_tree_ignore_more
        res = Indexes.get_browsing_tree_ignore_more(1)
        assert len(res)==1

        # get_browsing_tree_paths
        res = Indexes.get_browsing_tree_paths(11)
        assert res==['11']

        # get_recursive_tree
        res = Indexes.get_recursive_tree()
        assert len(res)==6
        res = Indexes.get_recursive_tree(11)
        assert res==[(1, 11, 0, 'Test index 11', 'Test index link 11', False, True, None, '3,-98,-99', '1,2,3,4,-98,-99', 'g1,g2', 'g1,g2', False, 0, False, False)]

        # get_index_with_role
        res = Indexes.get_index_with_role(1)
        assert res=={'biblio_flag': False, 'browsing_group': {'allow': [], 'deny': []}, 'browsing_role': {'allow': [{'id': 3, 'name': 'Contributor'}, {'id': -98, 'name': 'Authenticated User'}, {'id': -99, 'name': 'Guest'}], 'deny': [{'id': 5, 'name': 'General'}, {'id': 6, 'name': 'Original Role'}]}, 'comment': '', 'contribute_group': {'allow': [], 'deny': []}, 'contribute_role': {'allow': [{'id': 1, 'name': 'System Administrator'}, {'id': 2, 'name': 'Repository Administrator'}, {'id': 3, 'name': 'Contributor'}, {'id': 4, 'name': 'Community Administrator'}, {'id': -98, 'name': 'Authenticated User'}, {'id': -99, 'name': 'Guest'}], 'deny': [{'id': 5, 'name': 'General'}, {'id': 6, 'name': 'Original Role'}]}, 'coverpage_state': True, 'display_format': '1', 'display_no': 0, 'harvest_public_state': True, 'harvest_spec': '', 'id': 1, 'image_name': '', 'index_link_enabled': False, 'index_link_name': 'Test index link 1', 'index_link_name_english': 'Test index link 1', 'index_name': 'Test index 1', 'index_name_english': 'Test index 1', 'more_check': False, 'online_issn': '1234-5678', 'owner_user_id': 0, 'parent': 0, 'position': 0, 'public_date': '20220101', 'public_state': True, 'recursive_browsing_group': True, 'recursive_browsing_role': True, 'recursive_contribute_group': True, 'recursive_contribute_role': True, 'recursive_coverpage_check': True, 'recursive_public_state': False, 'rss_status': False}
        res = Indexes.get_index_with_role(22)
        assert res=={'biblio_flag': True, 'browsing_group': {'allow': [], 'deny': []}, 'browsing_role': {'allow': [{'id': 3, 'name': 'Contributor'}, {'id': -98, 'name': 'Authenticated User'}, {'id': -99, 'name': 'Guest'}], 'deny': [{'id': 5, 'name': 'General'}, {'id': 6, 'name': 'Original Role'}]}, 'comment': '', 'contribute_group': {'allow': [], 'deny': []}, 'contribute_role': {'allow': [{'id': 1, 'name': 'System Administrator'}, {'id': 2, 'name': 'Repository Administrator'}, {'id': 3, 'name': 'Contributor'}, {'id': 4, 'name': 'Community Administrator'}, {'id': -98, 'name': 'Authenticated User'}, {'id': -99, 'name': 'Guest'}], 'deny': [{'id': 5, 'name': 'General'},  {'id': 6, 'name': 'Original Role'}]}, 'coverpage_state': False, 'display_format': '1', 'display_no': 1, 'harvest_public_state': True, 'harvest_spec': '', 'id': 22, 'image_name': '', 'index_link_enabled': False, 'index_link_name': 'Test index link 22', 'index_link_name_english': 'Test index link 22', 'index_name': 'Test index 22', 'index_name_english': 'Test index 22', 'more_check': False, 'online_issn': '', 'owner_user_id': 0, 'parent': 2, 'position': 1, 'public_date': '', 'public_state': True, 'recursive_browsing_group': False, 'recursive_browsing_role': False, 'recursive_contribute_group': False, 'recursive_contribute_role': False, 'recursive_coverpage_check': False, 'recursive_public_state': True, 'rss_status': False}

        # get_index
        res = Indexes.get_index(2)
        assert res.id==2
        assert res.index_name=='Test index 2'
        res = Indexes.get_index(2, True)
        assert res[0].id==2
        assert res[0].index_name=='Test index 2'
        assert res[1]==1

        # get_index_by_name
        res = Indexes.get_index_by_name('Test index 2')
        assert res.id==2
        assert res.index_name=='Test index 2'
        res = Indexes.get_index_by_name('Test index 22', 2)
        assert res.id==22
        assert res.index_name=='Test index 22'

        # get_index_by_all_name
        res = Indexes.get_index_by_all_name()
        assert res==None
        res = Indexes.get_index_by_all_name("Test index 1")
        assert res.id==1
        assert res.index_name=='Test index 1'

        # get_root_index_count
        res = Indexes.get_root_index_count()
        assert res.parent==0
        assert res.position_max==2

        # get_path_list
        res = Indexes.get_path_list([3])
        assert res==[(0, 3, '3', 'Test index 3', 'Test index 3', 1, True, None, '', '3,-98,-99', 'g1,g2', True)]

        # get_path_name
        res = Indexes.get_path_name([3])
        assert res==[(0, 3, '3', 'Test index 3', 'Test index 3', 1, True, None, '', '3,-98,-99', 'g1,g2', True)]

        # get_self_list
        res = Indexes.get_self_list(3)
        assert res==[(0, 3, '3', 'Test index 3', 'Test index 3', 1, True, None, '', '3,-98,-99', 'g1,g2', True)]

        # get_self_path
        res = Indexes.get_self_path(3)
        assert res==(0, 3, '3', 'Test index 3', 'Test index 3', 1, True, None, '', '3,-98,-99', 'g1,g2', True)

        # is_index
        res = Indexes.is_index('1:11')
        assert res==True
        res = Indexes.is_index('3')
        assert res==True
        res = Indexes.is_index('4')
        assert res==False
        res = Indexes.is_index('a')
        assert res==False

        # is_public_state_and_not_in_future
        res = Indexes.is_public_state_and_not_in_future([3])
        assert res==False

        # set_item_sort_custom
        res = Indexes.set_item_sort_custom(3, {1: 1, 2: 2})
        assert res.id==3
        assert res.item_custom_sort=={'1': 1, '2': 2}

        # get_item_sort
        res = Indexes.get_item_sort(3)
        assert res=={'1': 1, '2': 2}

        # get_coverpage_state
        res = Indexes.get_coverpage_state([1])
        assert res==True
        res = Indexes.get_coverpage_state([2])
        assert res==False

        # set_coverpage_state_resc
        Indexes.set_coverpage_state_resc(2, True)
        res = Indexes.get_coverpage_state([21])
        assert res==True

        # get_index_count
        res = Indexes.get_index_count()
        assert res==6

        # get_child_list
        res = Indexes.get_child_list(1)
        assert res==[(0, 1, '1', 'Test index 1', 'Test index 1', 1, True, datetime(2022, 1, 1, 0, 0), '', '3,-98,-99', 'g1,g2', True),(1, 11, '1/11', 'Test index 1-/-Test index 11', 'Test index 1-/-Test index 11', 2, True, None, '', '3,-98,-99', 'g1,g2', True)]

        # get_child_id_list
        res = Indexes.get_child_id_list()
        assert res==[1, 2, 3]

        # get_list_path_publish
        res = Indexes.get_list_path_publish(11)
        assert res==['11']

        # get_all_indexes
        res = Indexes.get_all_indexes()
        assert len(res)==6

        # get_all_parent_indexes
        res = Indexes.get_all_parent_indexes(11)
        assert len(res)==2

        # get_harverted_index_list
        res = Indexes.get_harverted_index_list()
        assert res==['1', '2', '3', '11', '21', '22']

        # get_public_indexes_list
        res = Indexes.get_public_indexes_list()
        assert res==['1', '2', '3', '11', '21', '22']

#     def get_contribute_tree(cls, pid, root_node_id=0):
