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


def _get_all_children(tree_json, parent=0, child_list={}, parent_info={}):
    """
    Parse the json data.

    :param tree_json: The index tree info.
    :param parent: The parent id.
    :param child_list: The children info.
    :param parent_info: The parent info.
    :return:Type of dict which contains the children and the parent info.
    """
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
        """Set the state of the index

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
