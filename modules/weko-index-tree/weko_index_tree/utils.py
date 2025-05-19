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
import os
import sys
import traceback
from datetime import date, datetime
from functools import wraps
from operator import itemgetter

from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl.query import Bool, Exists, Q, QueryString
from flask import Markup, current_app, session, json, Flask
from flask_babelex import get_locale
from flask_babelex import gettext as _
from flask_babelex import to_user_timezone, to_utc
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import current_user
from invenio_cache import current_cache
from invenio_communities.models import Community
from invenio_db import db
from invenio_i18n.ext import current_i18n
from invenio_pidstore.models import PersistentIdentifier
from invenio_search import RecordsSearch
from simplekv.memory.redisstore import RedisStore
from weko_admin.utils import is_exists_key_in_redis
from weko_groups.models import Group
from weko_logging.activity_logger import UserActivityLogger
from weko_redis.redis import RedisConnection
from weko_schema_ui.models import PublishStatus

from .config import WEKO_INDEX_TREE_STATE_PREFIX
from .errors import IndexBaseRESTError, IndexDeletedRESTError
from .models import Index


def get_index_link_list(pid=0):
    """Get index link list."""
    def _get_index_link(res, tree):
        for node in tree:
            if node['index_link_enabled']:
                res.append((int(node['id']), node['link_name']))
            if node['children']:
                _get_index_link(res, node['children'])
    from .api import Indexes
    tree = Indexes.get_browsing_tree_ignore_more(pid)
    res = []
    _get_index_link(res, tree)
    return res


def is_index_tree_updated():
    """Return True if index tree has been updated."""
    return current_app.config['WEKO_INDEX_TREE_UPDATED']


def cached_index_tree_json(timeout=50, key_prefix='index_tree_json'):
    """Cache index tree json."""
    def caching(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_fun = current_cache.cached(
                timeout=timeout, key_prefix=key_prefix + current_i18n.language,
                forced_update=is_index_tree_updated)
            return cache_fun(f)(*args, **kwargs)
        return wrapper
    return caching


def reset_tree(tree, path=None, more_ids=None, ignore_more=False):
    """
    Reset the state of checked.

    :param tree:
    :param path:
    :param more_ids:
    :return: The dict of index tree.
    """
    if more_ids is None:
        more_ids = []
    roles = get_user_roles(is_super_role=False)
    groups = get_user_groups()
    if path is not None:
        id_tp = []
        if not isinstance(path, list):
            id_tp = [path]
        else:
            id_tp = path

        reduce_index_by_role(tree, roles, groups, False, id_tp)
    else:
        if not roles[0]:
            # for browsing role check
            reduce_index_by_role(tree, roles, groups)
        if not ignore_more:
            reduce_index_by_more(tree=tree, more_ids=more_ids)

def can_user_access_index(lst):
    """Check if the specified user has access to the index item.

    This function determines access permissions based on the user's roles and groups.
    It checks whether the user has viewing or editing rights for the index item.
    It also considers the public state and public date of the index to evaluate accessibility.

    Args:
        lst (dict): Dictionary representing the index item.

    Returns:
        bool: True if the user has access, False otherwise.
    """
    from weko_records_ui.utils import is_future

    result, roles = get_user_roles(is_super_role=True)

    groups = get_user_groups()

    brw_role = lst.get('browsing_role', [])
    brw_group = lst.get('browsing_group', [])
    contribute_role = lst.get('contribute_role', [])
    contribute_group = lst.get('contribute_group', [])
    public_state = lst.get('public_state', False)
    public_date = lst.get('public_date', None)

    if not result:
        if isinstance(public_date, str):
            public_date = str_to_datetime(public_date, "%Y-%m-%dT%H:%M:%S")

        if check_roles(roles, brw_role) or check_groups(groups, brw_group):
            if public_state and (public_date is None or not is_future(public_date)):
                result = True

        if check_roles(roles, contribute_role) or check_groups(groups, contribute_group):
            result = True

    return result

def can_admin_access_index(lst):
    """Check if the specified user with admin role has access to the index item.

    This function determines access permissions based on the user's admin roles.
    It checks whether the user has administrative privileges directly on the index item,
    or indirectly through one of its parent indexes.

    Args:
        lst (dict): Dictionary representing the index item.

    Returns:
        bool: True if the user has admin access to the index, False otherwise.
    """
    from .api import Indexes

    result, roles = get_user_roles(is_super_role=False)

    if not result:
        if check_comadmin(roles, lst.get('id')):
            result = True
        else:
            parent_id = lst.get('parent', 0)
            while parent_id and parent_id != '0':
                parent = Indexes.get_index(parent_id)
                if parent and check_comadmin(roles, parent.id):
                    result = True
                    break
                parent_id = parent.parent if parent else None

    return result

def get_tree_json(index_list, root_id):
    """Get Tree Json.

    :param index_list:
    :param root_id:
    :return:
    """
    index_relation = {
    }  # index_relation[parent_index_id] = [child_index_id, ...]
    index_position = {}  # index_position[index_id] = position_in_index_list

    for position, index_element in enumerate(index_list):
        if index_element.pid not in index_relation:
            index_relation[index_element.pid] = []
        index_relation[index_element.pid].append(index_element.cid)
        index_position[index_element.cid] = position

    def get_user_list_expand():
        """Get list index expand."""
        key = current_app.config.get(
            "WEKO_INDEX_TREE_STATE_PREFIX",
            WEKO_INDEX_TREE_STATE_PREFIX
        )
        return session.get(key, [])

    def generate_index_dict(index_element, is_root):
        """Formats an index_element, which is a tuple, into a nicely formatted dictionary."""
        index_dict = index_element._asdict()
        index_name = str(index_element.name).replace("&EMPTY&", "")
        index_name = Markup.escape(index_name)
        index_name = index_name.replace("\n", r"<br\>")

        index_link_name = str(index_element.link_name).replace("&EMPTY&", "")
        index_link_name = index_link_name.replace("\n", r"<br\>")

        if not is_root:
            pid = str(index_element.pid)
            parent = index_list[index_position[index_element.pid]]
            while parent.pid and parent.cid != root_id:
                pid = '{}/{}'.format(parent.pid, pid)
                parent = index_list[index_position[parent.pid]]
            index_dict.update({'parent': pid})

        list_index_expand = get_user_list_expand()
        is_expand_on_init = str(index_element.cid) in list_index_expand
        index_dict.update({
            'id': str(index_element.cid),
            'value': index_name,
            'name': index_name,
            'link_name': index_link_name,
            'index_link_enabled': index_element.index_link_enabled,
            'position': index_element.position,
            'emitLoadNextLevel': False,
            'settings': {
                'isCollapsedOnInit': not is_expand_on_init,
                'checked': False
            }
        })
        for attr in [
            'public_state',
            'public_date',
            'browsing_role',
            'contribute_role',
            'browsing_group',
            'contribute_group',
            'more_check',
            'display_no',
            'coverpage_state'
        ]:
            if hasattr(index_element, attr):
                index_dict.update({attr: getattr(index_element, attr)})
        return index_dict

    def get_children(parent_index_id):
        """Recursively gets all children of a given index id."""
        child_list = []
        for child_index_id in index_relation.get(parent_index_id, []):
            child_index = index_list[index_position[child_index_id]]
            child_index_dict = generate_index_dict(
                child_index, parent_index_id == 0)

            # Recursively get grandchildren
            child_index_dict['children'] = get_children(child_index_id)

            child_list.append(child_index_dict)

        child_list.sort(key=itemgetter('position'))
        return child_list

    if root_id == 0:
        index_tree = get_children(root_id)
    else:
        root_index = index_list[index_position[root_id]]
        root_index_dict = generate_index_dict(root_index, True)
        root_index_dict['children'] = get_children(root_id)
        index_tree = [root_index_dict]

    return index_tree


def get_user_roles(is_super_role=False):
    """Get user roles."""
    def _check_admin():
        result = False
        for lst in list(current_user.roles or []):
            # if is administrator
            admin_roles = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] + \
                (current_app.config["WEKO_PERMISSION_ROLE_COMMUNITY"] if is_super_role else [])
            if lst.name in admin_roles:
                result = True
        return result

    user_id = current_user.get_id() \
        if current_user and current_user.is_authenticated else None
    if user_id:
        return _check_admin(), [x.id for x in current_user.roles]
    return False, None


def get_user_groups():
    """Get user groups."""
    grps = []
    groups = Group.query_by_user(current_user, eager=False)
    for group in groups:
        grps.append(group.id)

    return grps


def check_roles(user_role, roles):
    """Check roles."""
    is_can = True
    if isinstance(roles, str):
        roles = roles.split(',')
    if not user_role[0]:
        if current_user.is_authenticated:
            self_role = user_role[1] or ['-98']
            for role in self_role:
                if str(role) not in (roles or []):
                    is_can = False
                    break
        elif roles and "-99" not in roles:
            is_can = False
    return is_can


def check_groups(user_group, groups):
    """Check groups."""
    is_can = False
    if current_user.is_authenticated:
        group = [x for x in user_group if str(x) in (groups or [])]
        if group:
            is_can = True

    return is_can


def filter_index_list_by_role(index_list):
    """Filter index list by role."""
    def _check(index_data, roles, groups):
        """Check index data by role."""
        from weko_records_ui.utils import is_future
        can_view = False
        if roles[0]:
            can_view = True
        else:
            if check_roles(roles, index_data.browsing_role) \
                    or check_groups(groups, index_data.browsing_group):
                if index_data.public_state \
                        and (index_data.public_date is None
                             or not is_future(index_data.public_date)):
                    can_view = True
        return can_view

    result_list = []
    roles = get_user_roles(is_super_role=True)
    groups = get_user_groups()
    for i in index_list:
        if _check(i, roles, groups):
            result_list.append(i)
    return result_list


def reduce_index_by_role(tree, roles, groups, browsing_role=True, plst=None):
    """Reduce index by."""
    from weko_records_ui.utils import is_future
    if isinstance(tree, list):
        i = 0
        while i < len(tree):
            lst = tree[i]

            if isinstance(lst, dict):
                if check_comadmin(roles[1], lst.get('id')):
                    i += 1
                    continue

                contribute_role = lst.pop('contribute_role')
                public_state = lst.pop('public_state')
                public_date = lst.pop('public_date')
                if isinstance(public_date, str):
                    public_date = str_to_datetime(public_date, "%Y-%m-%dT%H:%M:%S")
                brw_role = lst.pop('browsing_role')

                contribute_group = lst.pop('contribute_group')
                brw_group = lst.pop('browsing_group')

                children = lst.get('children')

                # browsing role and group check
                if browsing_role:
                    if check_roles(roles, brw_role) \
                            or check_groups(groups, brw_group):

                        if public_state and \
                                (public_date is None
                                 or not is_future(public_date)):
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
                    if check_roles(roles, contribute_role) or \
                            check_groups(groups, contribute_group):
                        lst['disabled'] = False

                        plst = plst or []
                        tree_id = lst.get('id', '')
                        if tree_id in plst:
                            settings = lst.get('settings')
                            if isinstance(settings, dict) and settings.get(
                                    'checked') is not None:
                                settings['checked'] = True
                                plst.remove(tree_id)

                        reduce_index_by_role(
                            children, roles, groups, False, plst)
                        i += 1

                    else:
                        children.clear()
                        tree.pop(i)
            else:
                tree.pop(i)


def get_index_id_list(indexes, id_list=None):
    """Get index id list."""
    if id_list is None:
        id_list = []
    if isinstance(indexes, list):
        for index in indexes:
            if isinstance(index, dict):
                if index.get('id', '') == 'more':
                    continue

                parent = index.get('parent', '')
                if parent != '' and parent != '0':
                    id_list.append(parent + '/' + index.get('id', ''))
                else:
                    id_list.append(index.get('id', ''))

                children = index.get('children')
                get_index_id_list(children, id_list)

    return id_list


def get_publish_index_id_list(indexes, id_list=None):
    """Get index id list."""
    if id_list is None:
        id_list = []
    if isinstance(indexes, list):
        for index in indexes:
            if isinstance(index, dict):
                if index.get('id', '') == 'more':
                    continue

                parent = index.get('parent', '')
                if index.get('public_state'):
                    if parent != '' and parent != '0':
                        id_list.append(parent + '/' + index.get('id', ''))
                    else:
                        id_list.append(index.get('id', ''))

                children = index.get('children')
                get_publish_index_id_list(children, id_list)

    return id_list


def reduce_index_by_more(tree, more_ids=None):
    """Reduce index by more."""
    if more_ids is None:
        more_ids = []
    for node in tree:
        if isinstance(node, dict):
            index_id = node.get('id')
            children = node.get('children')
            more_check = node.get('more_check')
            display_no = node.get('display_no')

            if more_check and \
                    len(children) > display_no and \
                    (len(more_ids) == 0 or index_id not in more_ids):

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


def get_admin_coverpage_setting():
    """Get 'avail' value from pdfcoverpage_set table."""
    from weko_records_ui.models import PDFCoverPageSettings
    avail = 'disable'
    try:
        setting = PDFCoverPageSettings.find(1)

        if setting:
            avail = setting.avail
    except Exception as ex:
        current_app.logger.debug(ex)
    return avail == 'enable'


def get_elasticsearch_records_data_by_indexes(index_ids, start_date, end_date):
    """Get data from elastic search.

    Arguments:
        index_ids -- index tree identifier list

    Returns:
        dictionary -- elastic search data

    """
    records_search = RecordsSearch()
    records_search = records_search.with_preference_param().\
        params(version=False)
    records_search._index[0] = current_app.config['SEARCH_UI_SEARCH_INDEX']
    result = None
    try:
        from weko_search_ui.query import item_search_factory

        search_instance, _qs_kwargs = item_search_factory(
            None,
            records_search,
            start_date,
            end_date,
            index_ids,
            True
        )
        search_result = search_instance.execute()
        result = search_result.to_dict()
    except NotFoundError:
        current_app.logger.debug('Indexes do not exist yet!')

    return result


def generate_path(index_ids):
    """Get data from elastic search.

    Arguments:
        index_ids -- index tree identifier

    Returns:
        dictionary -- elastic search data

    """
    from .api import Indexes
    path = dict()
    result = []
    for index in index_ids:
        parent_path = path.get(str(index.pid)) or \
            (Indexes.get_full_path(index.pid) if index.pid > 0 else "")
        path[str(index.cid)] = (parent_path + "/" + str(index.cid)) \
            if parent_path != "" else "" + str(index.cid)
        result.append(path[str(index.cid)])

    return result


def get_index_id(activity_id):
    """Get index ID base on activity id.

    :param activity_id:
    :return:
    """
    from weko_workflow.api import WorkActivity, WorkFlow
    activity = WorkActivity()
    activity_detail = activity.get_activity_detail(activity_id)
    workflow = WorkFlow()
    workflow_detail = workflow.get_workflow_by_id(
        activity_detail.workflow_id)
    index_tree_id = workflow_detail.index_tree_id
    if index_tree_id:
        from .api import Indexes
        index_result = Indexes.get_index(index_tree_id)
        if not index_result:
            index_tree_id = None
    else:
        index_tree_id = None
    return index_tree_id


def sanitize(s):
    """Sanitize input string."""
    s = s.strip()
    esc_str = ""
    for i in s:
        if ord(i) in [9, 10, 13] or (31 < ord(i) != 127):
            esc_str += i
    return esc_str


def count_items(indexes_aggr):
    """
    Count public and private items of a target index based on index state.

    Args:
        indexes_aggr ([type]): [description]

    Returns:
        [type]: [description]

    """
    pub_items = 0
    pri_items = 0

    for agg in indexes_aggr:
        if agg.get('public_state'):
            pub_items += agg['doc_count'] - agg['no_available']
            pri_items += agg['no_available']
        else:
            pri_items += agg['doc_count']

    return pri_items, pub_items


def recorrect_private_items_count(agp):
    """Re-correct private item count in case of unpublished items.

    :param agp: aggregation returned from ES
    :return:
    """
    for agg in agp:
        date_range = agg["date_range"]
        bkt = date_range['available']['buckets']
        for bk in bkt:
            if bk.get("from"):
                agg["no_available"]["doc_count"] += bk.get("doc_count")


def check_doi_in_index(index_id):
    """Check doi in index.

    @param index_id:
    @return:
    """
    try:
        if check_doi_in_list_record_es(index_id):
            return True
        return False
    except Exception:
        return True


def get_record_in_es_of_index(index_id, recursively=True):
    """Get all records belong to Index ID.

    @param index_id:
    @return:
    """
    from .api import Indexes
    if recursively:
        child_idx = Indexes.get_child_list_recursive(index_id)
    else:
        child_idx = [index_id]

    query_string = "relation_version_is_last:true"
    search = RecordsSearch(
        index=current_app.config['SEARCH_UI_SEARCH_INDEX'])
    must_query = [
        QueryString(query=query_string),
        Q("terms", path=child_idx),
        Q("terms", publish_status=[
            PublishStatus.PUBLIC.value,
            PublishStatus.PRIVATE.value
        ])
    ]
    search = search.query(
        Bool(filter=must_query)
    )
    records = search.execute().to_dict().get('hits', {}).get('hits', [])

    return records


def check_doi_in_list_record_es(index_id):
    """Check doi in index.

    @param index_id:
    @return: True if the index do not update the index state to private.

    """
    list_records_in_es = check_doi_in_index_and_child_index(index_id)
    list_path = []
    for record in list_records_in_es:
        # If a record has only an index,
        # do not update the index state to private.
        if len(record.get('_source', {}).get('path', [])) <= 1:
            return True

        list_path.append(list(
            filter(lambda x: not x.endswith(str(index_id)),
                   record.get('_source', {}).get('path'))
        ))
    # Check index permissions
    for path in list_path:
        if not check_index_permissions(record={}, index_path_list=path,
                                       is_check_doi=True):
            return True
    return False


def check_restrict_doi_with_indexes(index_ids):
    """Check doi in index.

    @param index_ids:
    @return:
    """
    from .api import Indexes
    full_path_index_ids = [Indexes.get_full_path(_id) for _id in index_ids]
    full_path_index_ids = [idx for idx in full_path_index_ids if idx != '']
    is_public = Indexes.is_public_state(full_path_index_ids)
    is_harvest_public = Indexes.get_harvest_public_state(full_path_index_ids)
    return not (is_public and is_harvest_public)


def check_has_any_item_in_index_is_locked(index_id):
    """Check if any item in the index is locked by import process.

    @param index_id:
    @return:
    """
    from weko_workflow.utils import check_an_item_is_locked

    list_records_in_es = get_record_in_es_of_index(index_id)
    for record in list_records_in_es:
        item_id = record.get('_source', {}).get(
            '_item_metadata', {}).get('control_number')
        if check_an_item_is_locked(int(item_id)):
            return True
    return False

def check_has_any_harvest_settings_in_index_is_locked(index_id):
    """Check if any harvest settings in the index is locked.

    @param index_id:
    @return:
    """
    from invenio_oaiharvester.models import HarvestSettings

    res = HarvestSettings.query.all()
    indexes = [str(s.index_id) for s in res]
    if str(index_id) in indexes:
        return True
    return False


def check_index_permissions(record=None, index_id=None, index_path_list=None,
                            is_check_doi=False) -> bool:
    """Check indexes of record is private.

    :param record:Record data.
    :param index_id:Index id.
    :param index_path_list:Index id list.
    :param is_check_doi: Check DOI flag.

    Returns:
        [bool]: False if the record has indexes(or parent indexes)
        which is private.

    """
    def _check_index_permission(index_data) -> bool:
        """Check index data by role.

        Args:
            index_data ():

        Returns:
            [bool]: True if the user can access index.

        """
        from weko_records_ui.utils import is_future
        can_view = False
        if roles[0]:
            # In case admin role.
            can_view = True
        elif index_data.public_state:
            check_user_role = check_roles(roles, index_data.browsing_role) or \
                check_groups(groups, index_data.browsing_group)
            check_public_date = \
                not is_future(index_data.public_date) \
                if index_data.public_date else True
            if check_user_role and check_public_date:
                can_view = True
        return can_view

    def _check_index_permission_for_doi(index_data) -> bool:
        """Check index permission for DOI.

        Args:
            index_data ():

        Returns:
            [bool]: True if the index is public.

        """
        public_state = index_data.public_state and \
            index_data.harvest_public_state

        return public_state

    def _check_for_index_groups(_index_groups):
        """Check for index groups.

        Args:
            _index_groups (list):Index groups.

        Returns:
            [bool]: True if the user can access index groups of record.

        """
        for _index in _index_groups:
            if _index and index_roles.get(str(_index)) is False:
                return False
        return True

    def _convert_index_path(list_index):
        """Convert index from the path to index identifier.

        Args:
            list_index (list): Index path list.
        """
        for _index in list_index:
            _indexes = Indexes.get_full_path(int(_index)).split('/')
            index_lst.extend(_indexes)
            index_groups.append(_indexes)

    def _get_record_index_list():
        """Get index list of record."""
        list_index = record.get("path")
        _convert_index_path(list_index)

    def _get_parent_lst():
        """Get parent list of index."""
        parent_lst = Indexes.get_all_parent_indexes(index_id)
        for _index in parent_lst:
            index_lst.append(_index.id)
        index_groups.append(index_lst)

    index_lst = []
    index_groups = []
    from .api import Indexes
    if record and record.get("path"):
        _get_record_index_list()
    elif index_id is not None:
        _get_parent_lst()
    elif index_path_list is not None:
        _convert_index_path(index_path_list)
    indexes = Indexes.get_path_list(index_lst)

    if not is_check_doi:
        # Get user roles and user groups.
        roles = get_user_roles(is_super_role=True)
        groups = get_user_groups()
        check_index_method = _check_index_permission
    else:
        check_index_method = _check_index_permission_for_doi

    index_roles = {}
    # Check index status.
    for index in indexes:
        index_roles.update({
            str(index.cid): check_index_method(index)
        })

    for index in index_groups:
        if _check_for_index_groups(index):
            return True
    return False


def check_doi_in_index_and_child_index(index_id, recursively=True):
    """Check DOI in index and child index.

    Args:
        index_id (list): Record list.
    """
    from .api import Indexes

    if recursively:
        child_idx = Indexes.get_child_list_recursive(index_id)
    else:
        child_idx = [index_id]
    query_string = "relation_version_is_last:true AND publish_status: {}".format(PublishStatus.PUBLIC.value)
    search = RecordsSearch(
        index=current_app.config['SEARCH_UI_SEARCH_INDEX'])
    must_query = [
        QueryString(query=query_string),
        Q("terms", path=child_idx),
        Q("nested", path="identifierRegistration",
          query=Exists(field="identifierRegistration"))
    ]
    search = search.query(
        Bool(filter=must_query)
    )
    records = search.execute().to_dict().get('hits', {}).get('hits', [])
    return records


def __get_redis_store():
    """Get redis store.

    Returns:
        Redis store.

    """
    redis_connection = RedisConnection()
    return redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)


def lock_all_child_index(index_id: str, value: str):
    """Lock index.

    Args:
        index_id (str): index identifier.
        value (str): Lock value.

    Returns:
        bool: True if the index is locked.

    """
    locked_key = []
    try:
        from .api import Indexes
        redis_store = __get_redis_store()
        key_prefix = current_app.config['WEKO_INDEX_TREE_INDEX_LOCK_KEY_PREFIX']
        child_list = Indexes.get_recursive_tree(index_id)
        for c_index in child_list:
            redis_store.put(key_prefix + str(c_index.cid),
                            value.encode('utf-8'))
            locked_key.append(key_prefix + str(c_index.cid))
    except Exception as e:
        current_app.logger.error('Could not lock index:', e)
        return False, locked_key
    return True, locked_key


def unlock_index(index_key):
    """Unlock index.

    Args:
        index_key (str|list): index key.
    """
    try:
        redis_store = __get_redis_store()
        if isinstance(index_key, str):
            redis_store.delete(index_key)
        elif isinstance(index_key, list):
            for key in index_key:
                redis_store.delete(key)
    except Exception as e:
        current_app.logger.error('Could not unlock index:', e)


def validate_before_delete_index(index_id):
    """Validate index data before deleting the index.

    Args:
        index_id (str|int): Index identifier.

    Returns:
        (boolean, list, list): unlock flag and error list and locked keys list

    """
    is_unlock = False
    locked_key = []
    errors = []
    if is_index_locked(index_id):
        errors.append(
            _('Index Delete is in progress on another device.'))
    else:
        is_unlock, locked_key = lock_all_child_index(index_id,
                                                     str(current_user.get_id()))
        if check_doi_in_index(index_id):
            errors.append(
                _('The index cannot be deleted because there is'
                  ' a link from an item that has a DOI.')
            )
        elif check_has_any_item_in_index_is_locked(index_id):
            errors.append(_('This index cannot be deleted because '
                            'the item belonging to this index is '
                            'being edited by the import function.'))
        elif check_has_any_harvest_settings_in_index_is_locked(index_id):
            errors.append(_('The index cannot be deleted becase '
                            'the index in harvester settings.'))

    return is_unlock, errors, locked_key


def is_index_locked(index_id):
    """Check locked index.

    Args:
        index_id (str|int): Index identifier.

    Returns:
        boolean: True if the index is locked.

    """
    if is_exists_key_in_redis(
        current_app.config['WEKO_INDEX_TREE_INDEX_LOCK_KEY_PREFIX'] + str(
            index_id)):
        return True
    return False


def perform_delete_index(index_id, record_class, action: str):
    """Perform delete index.

    Args:
        index_id (str|int): Index identifier
        record_class (Indexes): Record object.
        action (str): Action.

    Raises:
        IndexDeletedRESTError: [description]
        IndexBaseRESTError: [description]
        InvalidDataRESTError: [description]

    Returns:
        tuple(str, list): delete message and error list

    """
    is_unlock = True
    locked_key = []
    try:
        msg = ''
        is_unlock, errors, locked_key = validate_before_delete_index(index_id)
        if len(errors) == 0:
            res = record_class.get_self_path(index_id)
            if not res:
                raise IndexDeletedRESTError()
            if action in ('move', 'all'):
                result = record_class. \
                    delete_by_action(action, index_id)
                if not result:
                    raise IndexBaseRESTError(
                        description='Could not delete data.')
            msg = 'Index deleted successfully.'
        db.session.commit()
        UserActivityLogger.info(
            operation="INDEX_DELETE",
            target_key=index_id
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        exec_info = sys.exc_info()
        tb_info = traceback.format_tb(exec_info[2])
        UserActivityLogger.error(
            operation="INDEX_DELETE",
            target_key=index_id,
            remarks=tb_info[0]
        )
        msg = 'Failed to delete index.'
    finally:
        if is_unlock:
            unlock_index(locked_key)
    return msg, errors


def get_doi_items_in_index(index_id, recursively=False):
    """Check if any item in the index is locked by import process.

    @param index_id:
    @return:
    """
    records = check_doi_in_index_and_child_index(index_id, recursively)
    result = []
    for record in records:
        item_id = record.get('_source', {}).get('control_number', 0)
        if len(record.get('_source', {}).get('path', [])):
            result.append(item_id)

    return result


def get_editing_items_in_index(index_id, recursively=False):
    """Check if any item in the index is locked or being edited.

    @param index_id:
    @return:
    """
    from weko_items_ui.utils import check_item_is_being_edit
    from weko_workflow.utils import check_an_item_is_locked

    result = []
    records = get_record_in_es_of_index(index_id, recursively)
    for record in records:
        item_id = record.get('_source', {}).get(
            '_item_metadata', {}).get('control_number')
        if check_item_is_being_edit(
            PersistentIdentifier.get('recid', item_id)) or \
                check_an_item_is_locked(int(item_id)):
            result.append(item_id)

    return result

def save_index_trees_to_redis(tree, lang=None):
    """save inde_tree to redis for roles

    """
    def default(o):
        if hasattr(o, "isoformat"):
            return o.isoformat()
        else:
            return str(o)
    redis = __get_redis_store()
    if lang is None:
        lang = current_i18n.language
    try:
        v = bytes(json.dumps(tree, default=default), encoding='utf-8')

        redis.put("index_tree_view_" + os.environ.get('INVENIO_WEB_HOST_NAME') + "_" + lang,v)
    except ConnectionError:
        current_app.logger.error("Fail save index_tree to redis")

def delete_index_trees_from_redis(lang):
    """delete index_tree from redis
    """
    redis = __get_redis_store()
    key = "index_tree_view_" + os.environ.get('INVENIO_WEB_HOST_NAME') + "_" + lang
    if redis.redis.exists(key):
        redis.delete(key)

def str_to_datetime(str_dt, format):
    try:
        return datetime.strptime(str_dt, format)
    except ValueError:
        return None

def get_descendant_index_names(index_id):
    """Retrieve all indexes under the specified index_id
        in the format of parent_index_name-/-child_index_name-/-grandchild_index_name.
    """
    def build_full_name(index):
        """Retrieve the `full_index_name` of the specified index"""
        names = []
        current = index
        while current:
            names.append(current.index_name)
            current = Index.query.get(current.parent) if current.parent else None
        return "-/-".join(reversed(names))

    def get_descendants(index):
        """Retrieve all indexes under the specified index"""
        descendants = []
        children = db.session.query(Index).filter_by(parent=index.id).all()
        for child in children:
            descendants.append(build_full_name(child))
            descendants.extend(get_descendants(child))
        return descendants

    root_index = Index.query.get(index_id)
    if not root_index:
        return []

    result = [build_full_name(root_index)]
    result.extend(get_descendants(root_index))
    return result

def get_item_ids_in_index(index_id):
    """Retrieve all items under the specified index_id"""
    records = get_all_records_in_index(index_id)
    result = []
    for record in records:
        item_id = record.get('_source', {}).get('control_number')
        if item_id:
            result.append(item_id)
    return result

def get_all_records_in_index(index_id):
    """Retrieve all records under the specified index_id"""
    from .api import Indexes
    child_idx = Indexes.get_child_list_recursive(index_id)
    query_string = "relation_version_is_last:true"
    size = 10000
    search = RecordsSearch(
        index=current_app.config['SEARCH_UI_SEARCH_INDEX']
    ).query(
        Bool(filter=[
            QueryString(query=query_string),
            Q("terms", path=child_idx),
            Q("terms", publish_status=[
                PublishStatus.PUBLIC.value,
                PublishStatus.PRIVATE.value
            ])
        ])
    ).sort('_doc').params(size=size)
    # Use search_after to retrieve all records
    records = []
    page = search.execute().to_dict()
    while page.get('hits', {}).get('hits', []):
        records.extend(page.get('hits', {}).get('hits', []))
        if len(page.get('hits', {}).get('hits', [])) < size:
            break
        search = search.extra(search_after=page.get('hits', {}).get('hits', [])[-1].get('sort'))
        page = search.execute().to_dict()
    return records

def check_comadmin(roles, index_id):
    """Check if the user is a community admin based on roles and group_id."""
    if roles is not None and any(
            role.name == current_app.config.get("WEKO_ADMIN_PERMISSION_ROLE_COMMUNITY")
            for role in current_user.roles
    ):
        com_list = Community.get_by_root_node_id(index_id)
        if any(com.group_id and com.group_id in roles for com in com_list):
            return True
    return False
