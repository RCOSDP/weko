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

"""Module of weko-index-tree utils."""

from functools import wraps

from flask import current_app
from invenio_cache import current_cache


def is_index_tree_updated():
    """Return True if index tree has been updated."""
    return current_app.config['WEKO_INDEX_TREE_UPDATED']


def cached_index_tree_json(timeout=50, key_prefix='index_tree_json'):
    """Cache index tree json."""
    def caching(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_fun = current_cache.cached(
                timeout=timeout, key_prefix=key_prefix,
                forced_update=is_index_tree_updated)
            return cache_fun(f)(*args, **kwargs)
        return wrapper
    return caching


def get_all_children(tree_json):
    """
    Get children and parent for the index tree.

    :param tree_json: Json data that updated by front page.
    :return: list(dict): [{
                        "id": index_id,
                        "parent": parent_id,
                        "children": decendants_id
                    },]
    """
    result = []
    child_list = {}
    parent_info = {}
    _get_all_children(
        tree_json, parent=0,
        child_list=child_list, parent_info=parent_info)
    for key in parent_info.keys():
        child = ''
        if key in child_list:
            child = ','.join(child_list.get(key))
        tmp = {
            'id': key,
            'parent': parent_info.get(key),
            'children': child
        }
        result.append(tmp)
    return result


def _get_all_children(tree_json, parent=0, child_list=None, parent_info=None):
    """
    Parse the json data.

    :param tree_json: The index tree info.
    :param parent: The parent id.
    :param child_list: The children info.
    :param parent_info: The parent info.
    :return:Type of dict which contains the children and the parent info.
    """
    if parent_info is None:
        parent_info = {}
    if child_list is None:
        child_list = {}
    children = []
    for tree in tree_json:
        if len(tree['children']) > 0:
            # contains children
            children.append(str(tree.get('id')))
            children.extend(
                _get_all_children(
                    tree.get('children'), tree.get('id'),
                    child_list, parent_info))
        else:
            children.append(str(tree.get('id')))
        parent_info[tree.get('id')] = str(parent)
    child_list[parent] = children
    return children


def reset_tree(path, tree):
    """
    Reset the state of checked.

    :param path:
    :param tree:
    :return: The dict of index tree.
    """

    def set_checked(id_tp, tree):
        """Set the state of the index.

        :param id_tp: Reset tree info.
        :param tree: The index tree info for reset.
        """
        if len(id_tp) == 0:
            return

        if isinstance(tree, list):
            for lst in tree:
                if isinstance(lst, dict):
                    tree_id = lst.get('id', '')
                    if tree_id in id_tp:
                        settings = lst.get('settings')
                        if isinstance(settings, dict) and settings.get(
                                'checked') is not None:
                            settings['checked'] = True
                            id_tp.remove(tree_id)
                            break
                    else:
                        set_checked(id_tp, lst.get('children', []))

    if path:
        id_tp = []
        if isinstance(path, list):
            for lp in path:
                index_id = lp.split('/')[-1]
                id_tp.append(index_id)
        else:
            index_id = path.split('/')[-1]
            id_tp.append(index_id)

        set_checked(id_tp, tree)


@cached_index_tree_json()
def get_tree_json(obj):
    """
    Get Tree Json
    :param obj:
    :return:
    """

    def get_settings():
        return dict(emitLoadNextLevel=False,
                    settings=dict(isCollapsedOnInit=False,checked=False))

    def set_node(plst):
        if isinstance(plst, list):
            for lst in plst:
                lst['children'] = []
                if isinstance(lst, dict):
                    key = lst.get('id')
                    while ntree and str(ntree[0].pid) == key:
                        index_obj = ntree.pop(0)
                        if isinstance(index_obj, tuple):
                            id = str(index_obj.cid)
                            value = index_obj.name
                            dc = get_settings()
                            dc.update(dict(id=id, value=value))
                            lst['children'].append(dc)
                if not lst['children'] and lst.get('settings'):
                    lst['settings']['isCollapsedOnInit'] = True
            for lst in plst:
                set_node(lst['children'])

    def remove_keys(lst):
        lst = lst._asdict()
        lst.update(dict(value=lst.pop('name'),
                        id=str(lst.pop('cid'))))
        lst.pop('pid')
        lst.pop('lev')
        lst.pop('path')
        return lst

    parent = [remove_keys(x) for x in filter(lambda node: node.pid == 0, obj)]
    ntree = obj[len(parent):]
    set_node(parent)

    current_app.config['WEKO_INDEX_TREE_UPDATED'] = False
    return parent

