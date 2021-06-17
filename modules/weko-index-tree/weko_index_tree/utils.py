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
import json
from datetime import date, datetime
from functools import wraps
from operator import itemgetter

from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl.query import Bool, Exists, Prefix, Q, QueryString
from flask import Markup, current_app, session
from flask_login import current_user
from invenio_cache import current_cache
from invenio_db import db
from invenio_i18n.ext import current_i18n
from invenio_search import RecordsSearch
from sqlalchemy import MetaData, Table, text
from weko_groups.models import Group

from .config import WEKO_INDEX_TREE_STATE_PREFIX
from .models import Index


def get_index_link_list(lang='en'):
    """Get index link list."""
    visables = Index.query.filter_by(
        index_link_enabled=True, public_state=True).all()
    if lang == 'jp':
        res = []
        for i in visables:
            if i.index_link_name:
                res.append((i.id, i.index_link_name))
            else:
                res.append((i.id, i.index_link_name_english))
        return res
    return [(i.id, i.index_link_name_english) for i in visables]


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
        if not roles[0]:
            # for browsing role check
            reduce_index_by_role(tree, roles, groups)
        if not ignore_more:
            reduce_index_by_more(tree=tree, more_ids=more_ids)


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


def get_user_roles():
    """Get user roles."""
    def _check_admin():
        result = False
        users = current_app.config['WEKO_PERMISSION_ROLE_USER']
        for lst in list(current_user.roles or []):
            # if is administrator
            if 'Administrator' in lst.name:
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
    if isinstance(roles, type("")):
        roles = roles.split(',')
    if not user_role[0]:
        if current_user.is_authenticated:
            role = [x for x in (user_role[1] or ['-98'])
                    if str(x) in (roles or [])]
            if not role and (user_role[1] or "-98" not in roles):
                is_can = False
        elif "-99" not in roles:
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
        can_view = False
        if roles[0]:
            can_view = True
        else:
            if check_roles(roles, index_data.browsing_role) \
                    or check_groups(groups, index_data.browsing_group):
                if index_data.public_state \
                        and (index_data.public_date is None
                             or (isinstance(index_data.public_date, datetime)
                                 and date.today() >= index_data.public_date.date())):
                    can_view = True
        return can_view

    result_list = []
    roles = get_user_roles()
    groups = get_user_groups()
    for i in index_list:
        if _check(i, roles, groups):
            result_list.append(i)
    return result_list


def reduce_index_by_role(tree, roles, groups, browsing_role=True, plst=None):
    """Reduce index by."""
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
                    if check_roles(roles, brw_role) \
                            or check_groups(groups, brw_group):

                        if public_state and \
                                (public_date is None
                                 or (isinstance(public_date, datetime)
                                     and date.today() >= public_date.date())):
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
    avail = 'disable'
    try:
        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        table_name = 'pdfcoverpage_set'

        pdfcoverpage_table = Table(table_name, metadata)
        record = db.session.query(pdfcoverpage_table)

        avail = record.first()[1]
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


def count_items(target_check_key, indexes_aggr, all_indexes):
    """
    Count public and private items of a target index based on index state.

    :param target_check_key: id of target index
    :param indexes_aggr: indexes aggregation returned from ES
    :param all_indexes:
    :return:
    """
    def get_child_agg_by_key():
        """Get all child indexes of target index."""
        lst_result = []
        for index_aggr in indexes_aggr:
            if index_aggr['key'].startswith(target_check_key + '/') \
                    or index_aggr['key'] == target_check_key:
                lst_result.append(index_aggr)
        return lst_result

    def set_private_index_count(target_index, lst_deleted):
        """Set private count of index based on index and parent index state.

        :param target_index: in of target index
        :param lst_deleted: lst deleted indexes
        :return:
        """
        temp = target_index.copy()
        list_parent_key = temp['key'].split('/')
        is_parent_private = False
        while list_parent_key:
            nearest_parent_key = list_parent_key.pop()
            if lst_indexes_state.get(nearest_parent_key) is None:
                lst_deleted.add(nearest_parent_key)
                current_app.logger.warning(
                    "Index {} is existed in ElasticSearch but not "
                    "in DataBase".format(str(nearest_parent_key)))
                continue
            if lst_indexes_state[nearest_parent_key] is False:
                is_parent_private = True
                break
        if is_parent_private:
            target_index['no_available'] = target_index['doc_count']

    def get_indexes_state():
        """Get indexes state."""
        lst_result = {}
        for index in all_indexes:
            lst_result[str(index.id)] = index.public_state
        return lst_result

    pub_items_count = 0
    pri_items_count = 0
    lst_child_agg = get_child_agg_by_key()
    lst_indexes_state = get_indexes_state()
    # list indexes existed in ES but deleted in DB
    lst_indexes_deleted = set()
    # Modify counts of index based on index and parent indexes state
    for agg in lst_child_agg:
        set_private_index_count(agg, lst_indexes_deleted)
    for agg in lst_child_agg:
        for index_deleted in lst_indexes_deleted:
            if str(agg['key']).endswith(str(index_deleted)):
                agg['no_available'] = 0
                agg['doc_count'] = 0
        pri_items_count += agg['no_available']
        pub_items_count += agg['doc_count'] - agg['no_available']
    return pri_items_count, pub_items_count


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
    except Exception as e:
        return True


def get_record_in_es_of_index(index_id):
    """Check doi in index.

    @param index_id:
    @return:
    """
    from .api import Indexes
    query_q = {
        "_source": {
            "excludes": [
                "content"
            ]
        },
        "query": {
            "bool": {
                "must": [
                    {
                        "prefix": {
                            "path.tree": "@index"
                        }
                    },
                    {
                        "match": {
                            "relation_version_is_last": "true"
                        }
                    }
                ]
            }
        }
    }
    fp = Indexes.get_self_path(index_id)
    query_q = json.dumps(query_q).replace("@index", fp.path)
    query_q = json.loads(query_q)
    result = []
    search = RecordsSearch(index=current_app.config['SEARCH_UI_SEARCH_INDEX'])
    search = search.update_from_dict(query_q)
    search_result = search.execute().to_dict()
    result = search_result.get('hits', {}).get('hits', [])
    return result


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


def check_restrict_doi_with_indexes(other_index_ids):
    """Check doi in index.

    @param index_id:
    @return:
    """
    from .api import Indexes
    for index_id in other_index_ids:
        idx = Indexes.get_index(index_id.split('/')[-1])
        if not idx or (idx.public_state and idx.harvest_public_state):
            return False
    return True


def check_has_any_item_in_index_is_locked(index_id):
    """Check if any item in the index is locked by import process.

    @param index_id:
    @return:
    """
    list_records_in_es = get_record_in_es_of_index(index_id)
    for record in list_records_in_es:
        from weko_workflow.utils import check_an_item_is_locked
        item_id = record.get('_source', {}).get(
            '_item_metadata', {}).get('control_number')
        if check_an_item_is_locked(int(item_id)):
            return True
    return False


def check_index_permissions(record, index_id=None, index_path_list=None,
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
        can_view = False
        if roles[0]:
            # In case admin role.
            can_view = True
        elif index_data.public_state:
            check_user_role = check_roles(roles, index_data.browsing_role) or \
                check_groups(groups, index_data.browsing_group)
            check_public_date = \
                isinstance(index_data.public_date, datetime) and \
                date.today() >= index_data.public_date.date() \
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
        if public_state and isinstance(index_data.public_date, datetime):
            public_state = date.today() >= index_data.public_date.date()

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
            _indexes = str(_index).split('/')
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
        roles = get_user_roles()
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


def check_doi_in_index_and_child_index(index_id):
    """Check DOI in index and child index.

    Args:
        index_id (list): Record list.
    """
    from .api import Indexes
    tree_path = Indexes.get_full_path(index_id)
    query_string = "relation_version_is_last:true AND publish_status:0"
    search = RecordsSearch(
        index=current_app.config['SEARCH_UI_SEARCH_INDEX'])
    must_query = [
        QueryString(query=query_string),
        Prefix(**{"path.tree": tree_path}),
        Q("nested", path="identifierRegistration",
          query=Exists(field="identifierRegistration"))
    ]
    search = search.query(
        Bool(filter=must_query)
    )
    records = search.execute().to_dict().get('hits', {}).get('hits', [])

    return records
