import json
import pytest

from datetime import date, datetime
from functools import wraps
from operator import itemgetter

import redis
from redis import sentinel
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl.query import Bool, Exists, Q, QueryString
from flask import Markup, current_app, session
from flask_babelex import get_locale
from flask_babelex import gettext as _
from flask_babelex import to_user_timezone, to_utc
from flask_login import current_user
from invenio_cache import current_cache
from invenio_i18n.ext import current_i18n
from invenio_pidstore.models import PersistentIdentifier
from invenio_search import RecordsSearch
from simplekv.memory.redisstore import RedisStore
from weko_admin.utils import is_exists_key_in_redis
from weko_groups.models import Group
from weko_redis.redis import RedisConnection
from invenio_accounts.testutils import login_user_via_session

# from .config import WEKO_INDEX_TREE_STATE_PREFIX
# from .errors import IndexBaseRESTError, IndexDeletedRESTError
# from .models import Index


# def get_index_link_list(pid=0):
#     def _get_index_link(res, tree):
# def is_index_tree_updated():
# def cached_index_tree_json(timeout=50, key_prefix='index_tree_json'):
#     def caching(f):
#         def wrapper(*args, **kwargs):
# def reset_tree(tree, path=None, more_ids=None, ignore_more=False):
# def get_tree_json(index_list, root_id):
#     def get_user_list_expand():
#     def generate_index_dict(index_element, is_root):
#     def get_children(parent_index_id):


# def get_user_roles():
#     def _check_admin():
def test_get_user_roles(users):
    for user in users:
        def _check_admin():
            result = True
            for role in user['obj'].roles:
                if 'Administrator' not in str(role):
                    result = False
            return result
        assert user['isAdmin'] == _check_admin()


# def get_user_groups():
def test_get_user_groups(users):
    for user in users:
        if user['obj'].groups:
            assert len(user['obj'].groups) != 0
        else:
            assert len(user['obj'].groups) == 0



# def check_roles(user_role, roles):
def test_check_roles(users):
    testKeyWordEmail = "noroleuser@test.org"
    for user in users:
        if user['obj'].roles:
            assert user['email'] != testKeyWordEmail
        else:
            assert user['email'] == testKeyWordEmail


# def check_groups(user_group, groups):
def test_check_groups(users):
    for user in users:
        if user['hasGroup']:
            assert len(user['obj'].groups) > 0
        else:
            assert len(user['obj'].groups) == 0


# def filter_index_list_by_role(index_list):
#     def _check(index_data, roles, groups):
def test_filter_index_list_by_role(indices, users):
    for user in users:
        canView = False
        if user['obj'].roles:
                canView = True
        else:
            for index in indices:
                if index.browsing_role or index.browsing_group:
                    if index.public_state and (
                            index.public_date is None
                            or (isinstance(index.public_date, datetime)
                                    and date.today() >= index.public_date.date()
                            )):
                        canView = True
            assert canView


# def reduce_index_by_role(tree, roles, groups, browsing_role=True, plst=None):
# def get_index_id_list(indexes, id_list=None):
# def get_publish_index_id_list(indexes, id_list=None):
# def reduce_index_by_more(tree, more_ids=None):
#                              "value": '<a href="#" class="more">more...</a>'}
# def get_admin_coverpage_setting():
# def get_elasticsearch_records_data_by_indexes(index_ids, start_date, end_date):
# def generate_path(index_ids):
# def get_index_id(activity_id):
# def sanitize(s):
# def count_items(indexes_aggr):
# def recorrect_private_items_count(agp):
# def check_doi_in_index(index_id):
# def get_record_in_es_of_index(index_id, recursively=True):
# def check_doi_in_list_record_es(index_id):
# def check_restrict_doi_with_indexes(index_ids):
# def check_has_any_item_in_index_is_locked(index_id):
# def check_index_permissions(record=None, index_id=None, index_path_list=None,
#     def _check_index_permission(index_data) -> bool:
#     def _check_index_permission_for_doi(index_data) -> bool:
#     def _check_for_index_groups(_index_groups):
#     def _convert_index_path(list_index):
#     def _get_record_index_list():
#     def _get_parent_lst():
# def check_doi_in_index_and_child_index(index_id, recursively=True):
# def __get_redis_store():
# def lock_all_child_index(index_id: str, value: str):
# def unlock_index(index_key):
# def validate_before_delete_index(index_id):
# def is_index_locked(index_id):
# def perform_delete_index(index_id, record_class, action: str):
#         record_class (Indexes): Record object.
#             res = record_class.get_self_path(index_id)
#                 result = record_class. \


# def get_doi_items_in_index(index_id, recursively=False):
    """Check if any item in the index is locked by import process.

    @param index_id:
    @return:
    """

# def get_editing_items_in_index(index_id, recursively=False):