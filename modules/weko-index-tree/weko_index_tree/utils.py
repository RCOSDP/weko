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
from invenio_i18n.ext import current_i18n
from weko_groups.models import Group



def is_index_tree_updated():
    """Return True if index tree has been updated."""
    return current_app.config['WEKO_INDEX_TREE_UPDATED']


def cached_index_tree_json(timeout=50, key_prefix='index_tree_json'):
    """Cache index tree json."""
    def caching(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_fun = current_cache.cached(
                timeout=timeout, key_prefix=key_prefix+current_i18n.language,
                forced_update=is_index_tree_updated)
            return cache_fun(f)(*args, **kwargs)
        return wrapper
    return caching


def reset_tree(tree, path=None, more_ids=[]):
    """
    Reset the state of checked.

    :param path:
    :param tree:
    :return: The dict of index tree.
    """
    roles = get_user_roles()
    groups = get_user_groups()
    if path is not None:
        id_tp = []
        if isinstance(path, list):
            for lp in path:
                index_id = lp.split('/')[-1]
                id_tp.append(index_id)
        else:
            index_id = path.split('/')[-1]
            id_tp.append(index_id)

        reduce_index_by_role(tree, roles, groups, False, id_tp)
    else:
        # for browsing role check
        reduce_index_by_role(tree, roles, groups)
        reduce_index_by_more(tree=tree, more_ids=more_ids)


def get_tree_json(obj, pid=0):
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
                    'browsing_role', 'contribute_role',
                    'browsing_group', 'contribute_group',
                    'more_check', 'display_no']
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

    # update by ryuu for invenio community start
    # parent = [remove_keys(x) for x in filter(lambda node: node.pid == 0, obj)]
    if pid != 0:
        parent = [remove_keys(x) for x in filter(lambda node: node.cid == pid, obj)]
    else:
        parent = [remove_keys(x) for x in filter(lambda node: node.pid == pid, obj)]
    # update by ryuu for invenio community end
    ntree = obj[len(parent):]
    set_node(parent)

    parent = sorted(parent, key=lambda x: x["position"])
    current_app.config['WEKO_INDEX_TREE_UPDATED'] = True

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

def get_user_groups():
    grps = []
    groups = Group.query_by_user(current_user, eager=False)
    for group in groups:
        grps.append(group.id)

    return grps

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

def check_groups(user_group, groups):
    is_can = True
    if current_user.is_authenticated:
        group = [x for x in user_group if str(x) in (groups or [])]
        if not group:
            is_can = False

    return is_can

def reduce_index_by_role(tree, roles, groups, browsing_role=True, plst=None):
    if isinstance(tree, list):
        i = 0
        while i < len(tree):
            lst = tree[i]

            if isinstance(lst, dict):
                contribute_role = lst.pop('contribute_role')
                public_state = lst.pop('public_state')
                public_date = lst.pop('public_date')
                brw_role = lst.pop('browsing_role')

                contribute_group = lst.pop('contribute_group')
                brw_group = lst.pop('browsing_group')

                children = lst.get('children')

                # browsing role and group check
                if browsing_role:
                    if roles[0] or (check_roles(roles, brw_role) and
                                    check_groups(groups, brw_group)):

                        if public_state or (isinstance(public_date, datetime)
                                            and date.today() >= public_date.date()):
                            reduce_index_by_role(children, roles, groups)
                            i += 1
                        else:
                            children.clear()
                            tree.pop(i)
                    else:
                        children.clear()
                        tree.pop(i)
                # contribute role and group check
                else:
                    if roles[0] or (check_roles(roles, contribute_role) and
                                    check_groups(groups, contribute_group)):
                        lst['disabled'] = False

                        plst = plst or []
                        tree_id = lst.get('id', '')
                        if tree_id in plst:
                            settings = lst.get('settings')
                            if isinstance(settings, dict) and settings.get(
                                    'checked') is not None:
                                settings['checked'] = True
                                plst.remove(tree_id)

                        reduce_index_by_role(children, roles, groups, False, plst)
                        i += 1

                    else:
                        children.clear()
                        tree.pop(i)

def get_index_id_list(indexes, id_list = []):
    if isinstance(indexes, list):
        for index in indexes:
            if isinstance(index, dict):
                if index.get('id', '') == 'more':
                    continue

                id_list.append(index.get('id', ''))

                children = index.get('children')
                get_index_id_list(children, id_list)

    return id_list

def reduce_index_by_more(tree, more_ids=[]):

    for node in tree:
        if isinstance(node, dict):
            id = node.get('id')
            children = node.get('children')
            more_check = node.get('more_check')
            display_no = node.get('display_no')

            if more_check and \
                len(children) > display_no and \
                (len(more_ids) == 0 or id not in more_ids):

                # Delete child node
                i = display_no
                while i < len(children):
                    children.pop(i)
                reduce_index_by_more(tree=children, more_ids=more_ids)

                # Add more node
                more_node = {"id": "more",
                             "value": '<a href="#" class="more">more...</a>'}
                children.insert(len(children), more_node)

            else:
                reduce_index_by_more(tree=children, more_ids=more_ids)
