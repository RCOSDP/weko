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
from datetime import date, datetime

from flask import current_app
from flask_login import current_user
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


def reset_tree(tree, path=None):
    """
    Reset the state of checked.

    :param path:
    :param tree:
    :return: The dict of index tree.
    """
    roles = get_user_roles()
    if path is not None:
        id_tp = []
        if isinstance(path, list):
            for lp in path:
                index_id = lp.split('/')[-1]
                id_tp.append(index_id)
        else:
            index_id = path.split('/')[-1]
            id_tp.append(index_id)

        reduce_index_by_role(tree, roles, False, id_tp)
    else:
        # for browsing role check
        reduce_index_by_role(tree, roles)


def get_tree_json(obj):
    """
    Get Tree Json
    :param obj:
    :return:
    """

    def get_settings():
        return dict(emitLoadNextLevel=False,
                    settings=dict(isCollapsedOnInit=False, checked=False))

    def set_node(plst):
        if isinstance(plst, list):
            attr = ['public_state', 'public_date',
                    'browsing_role', 'contribute_role']
            for lst in plst:
                lst['children'] = []
                if isinstance(lst, dict):
                    key = lst.get('id')
                    while ntree and str(ntree[0].pid) == key:
                        index_obj = ntree.pop(0)
                        if isinstance(index_obj, tuple):
                            cid = str(index_obj.cid)
                            name = index_obj.name
                            dc = get_settings()
                            dc.update(dict(position=index_obj.position))
                            dc.update(dict(id=cid, value=name))
                            for x in attr:
                                if hasattr(index_obj, x):
                                    dc.update({x: getattr(index_obj, x)})
                            lst['children'].append(dc)
                if not lst['children'] and lst.get('settings'):
                    lst['settings']['isCollapsedOnInit'] = True
            for lst in plst:
                set_node(lst['children'])
                lst['children'] = sorted(lst['children'],
                                         key=lambda j: j["position"])

    def remove_keys(lst):
        lst = lst._asdict()
        lst.update(get_settings())
        lst.update(dict(value=lst.pop('name'),
                        id=str(lst.pop('cid'))))
        lst.pop('pid')
        return lst

    parent = [remove_keys(x) for x in filter(lambda node: node.pid == 0, obj)]
    ntree = obj[len(parent):]
    set_node(parent)

    parent = sorted(parent, key=lambda x: x["position"])

    current_app.config['WEKO_INDEX_TREE_UPDATED'] = False
    return parent


def get_user_roles():

    def _check_admin():
        result = False
        users = current_app.config['WEKO_PERMISSION_ROLE_USER']
        for lst in list(current_user.roles or []):
            # if is administrator
            if lst.name in users[0:2]:
                result = True
        return result

    user_id = current_user.get_id() \
        if current_user and current_user.is_authenticated else None
    if user_id:
        return _check_admin(), [x.id for x in current_user.roles]
    return False, None


def check_roles(user_role, roles):
    is_can = True
    if not user_role[0]:
        if current_user.is_authenticated:
            role = [x for x in (user_role[1] or []) if str(x) in (roles or [])]
            if not role:
                is_can = False
        elif "99" not in roles:
            is_can = False
    return is_can


def reduce_index_by_role(tree, roles, browsing_role=True, plst=None):
    if isinstance(tree, list):
        i = 0
        while i < len(tree):
            lst = tree[i]
            if isinstance(lst, dict):
                contribute_role = lst.pop('contribute_role')
                public_state = lst.pop('public_state')
                public_date = lst.pop('public_date')
                brw_role = lst.pop('browsing_role')

                children = lst.get('children')

                if browsing_role:
                    if roles[0] or check_roles(roles, brw_role):
                        if public_state or (isinstance(public_date, datetime)
                                            and date.today() >= public_date.date()):
                            reduce_index_by_role(children, roles)
                            i += 1
                        else:
                            children.clear()
                            tree.pop(i)
                    else:
                        children.clear()
                        tree.pop(i)
                # contribute role check
                else:
                    lst['disabled'] = False \
                        if roles[0] or check_roles(roles, contribute_role) \
                        else True

                    plst = plst or []
                    tree_id = lst.get('id', '')
                    if tree_id in plst:
                        settings = lst.get('settings')
                        if isinstance(settings, dict) and settings.get(
                                'checked') is not None:
                            settings['checked'] = True
                            plst.remove(tree_id)

                    reduce_index_by_role(children, roles, False, plst)
                    i += 1
