from weko_index_tree.utils import \
get_index_link_list, \
is_index_tree_updated, \
get_user_roles, \
get_user_groups, \
check_roles, \
check_groups, \
filter_index_list_by_role, \
get_index_id_list, \
get_publish_index_id_list, \
get_admin_coverpage_setting, \
get_elasticsearch_records_data_by_indexes, \
get_index_id, \
count_items, \
check_doi_in_index_and_child_index, \
__get_redis_store, \
lock_all_child_index, \
unlock_index, \
is_index_locked


from invenio_accounts.testutils import login_user_via_session, client_authenticated
######
import json
import pytest

from datetime import date, datetime, timedelta
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
from flask_login import current_user, login_user, LoginManager
from invenio_cache import current_cache
from invenio_i18n.ext import current_i18n
from invenio_pidstore.models import PersistentIdentifier
from invenio_search import RecordsSearch
from simplekv.memory.redisstore import RedisStore
from invenio_accounts.testutils import login_user_via_session, login_user_via_view
from invenio_records.models import RecordMetadata

from weko_index_tree.models import Index
from weko_workflow.models import Activity, ActionStatus, Action, WorkFlow, FlowDefine, FlowAction
from weko_admin.utils import is_exists_key_in_redis
from weko_groups.models import Group
from weko_redis.redis import RedisConnection


# from .config import WEKO_INDEX_TREE_STATE_PREFIX
# from .errors import IndexBaseRESTError, IndexDeletedRESTError
# from .models import Index


#*** def get_index_link_list(pid=0):
#     def _get_index_link(res, tree):
# Needs pid
# def test_get_index_link_list(i18n_app, records):
    
#     assert not get_index_link_list(records['records'][0]['record'].json['_deposit']['pid']['value'])
        

#+++ def is_index_tree_updated():
def test_is_index_tree_updated(app):

    assert is_index_tree_updated()


# def cached_index_tree_json(timeout=50, key_prefix='index_tree_json'):
#     def caching(f):
#         def wrapper(*args, **kwargs):
# def reset_tree(tree, path=None, more_ids=None, ignore_more=False):
# def get_tree_json(index_list, root_id):
#     def get_user_list_expand():
#     def generate_index_dict(index_element, is_root):
#     def get_children(parent_index_id):


#*** def get_user_roles():
#     def _check_admin():
# Needs current_user
def test_get_user_roles(i18n_app, client_rest, users):
    login_user_via_session(client=client_rest, email=users[0]['email'])

    # User not authenticated
    assert get_user_roles()[0] == False


#*** def get_user_groups():
# Needs current_user
def test_get_user_groups(i18n_app, client_rest, users):
    login_user_via_session(client=client_rest, email=users[6]['email'])

    # User not authenticated
    assert len(get_user_groups()) == 0


#*** def check_roles(user_role, roles):
# Needs current_user
def test_check_roles(users):
    user_role = [role.name for role in users[-1]['obj'].roles]
    roles = (',').join(user_role)

    assert check_roles(user_role, roles)


#*** def check_groups(user_group, groups):
# Needs current_user
def test_check_groups(i18n_app, users, db):
    from weko_groups.models import Group
    g1 = Group.create(name="group_test1").add_member(users[-1]['obj'])
    g2 = Group.create(name="group_test2").add_member(users[-1]['obj'])

    db.session.add(g1)
    db.session.add(g2)

    user_group = ["group_test1", "group_test2"]
    groups = [v for k,v in Group.get_group_list().items()]

    assert check_groups(user_group, groups) == False


#*** def filter_index_list_by_role(index_list):
#     def _check(index_data, roles, groups):
# Needs current_user
def test_filter_index_list_by_role(i18n_app, indices, users, db):
    # Create test group
    from weko_groups.models import Group
    g1 = Group.create(name="group_test1").add_member(users[-1]['obj'])
    g2 = Group.create(name="group_test2").add_member(users[-1]['obj'])

    db.session.add(g1)
    db.session.add(g2)

    assert len(filter_index_list_by_role([indices['index_non_dict']])) == 0


# def reduce_index_by_role(tree, roles, groups, browsing_role=True, plst=None):


#+++ def get_index_id_list(indexes, id_list=None):
def test_get_index_id_list(indices, db):
    index_list = [indices['index_dict']]
    str_id = str(index_list[0]['id'])
    index_list[0]['id'] = str_id

    assert get_index_id_list(index_list)
    
    index_list[0]['id'] = 'more'

    assert not get_index_id_list(index_list)


#+++ def get_publish_index_id_list(indexes, id_list=None):
def test_get_publish_index_id_list(indices, db):
    index_list = [indices['index_dict']]
    str_id = str(index_list[0]['id'])
    index_list[0]['id'] = str_id

    assert get_publish_index_id_list(index_list)
    
    index_list[0]['id'] = 'more'

    assert not get_publish_index_id_list(index_list)


# def reduce_index_by_more(tree, more_ids=None):


#+++ def get_admin_coverpage_setting():
def test_get_admin_coverpage_setting(pdfcoverpage):
    assert get_admin_coverpage_setting()


#*** def get_elasticsearch_records_data_by_indexes(index_ids, start_date, end_date):
def test_get_elasticsearch_records_data_by_indexes(i18n_app, records, indices):
    from weko_index_tree.api import Indexes
    
    idx_tree_ids = [idx.cid for idx in Indexes.get_recursive_tree(indices['index_non_dict'].id)]
    current_date = date.today()
    start_date = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = current_date.strftime("%Y-%m-%d")

    assert get_elasticsearch_records_data_by_indexes(idx_tree_ids, start_date, end_date) is None
    

# def generate_path(index_ids):


#+++ def get_index_id(activity_id):
def test_get_index_id(i18n_app, users, db_register):
    activity_id = db_register['activity'].activity_id

    assert get_index_id(activity_id)


# def sanitize(s):


#+++ def count_items(indexes_aggr):
def test_count_items(count_json_data):
    indexes_aggr = count_json_data

    assert count_items(indexes_aggr)



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


#*** def check_doi_in_index_and_child_index(index_id, recursively=True):
def test_check_doi_in_index_and_child_index(i18n_app, indices, mock_execute):
    index_id = indices['index_dict']['id']

    assert len(check_doi_in_index_and_child_index(index_id, recursively=False)) == 0


#+++ def __get_redis_store():
def test___get_redis_store(i18n_app):
    assert __get_redis_store()


#+++ def lock_all_child_index(index_id: str, value: str):
def test_lock_all_child_index(i18n_app, indices):
    index_id = indices['index_non_dict'].id
    value = indices['index_non_dict'].index_name

    assert lock_all_child_index(index_id, value)
    

#+++ def unlock_index(index_key):
def test_unlock_index(i18n_app, indices):
    datastore = __get_redis_store()
    locked_key_dict = f"lock_index_{indices['index_dict']['index_name']}_dict"
    locked_key_non_dict = f"lock_index_{indices['index_non_dict'].index_name}_non_dict"
    datastore.put(locked_key_dict, json.dumps({'1':'a'}).encode('utf-8'), ttl_secs=30)
    datastore.put(locked_key_non_dict, json.dumps({'1':'a'}).encode('utf-8'), ttl_secs=30)
    
    unlock_index(locked_key_dict)
    unlock_index([locked_key_non_dict])

    assert datastore.redis.exists(locked_key_dict) == False
    assert datastore.redis.exists(locked_key_non_dict) == False


# def validate_before_delete_index(index_id):


#+++ def is_index_locked(index_id):
def test_is_index_locked(i18n_app, indices, redis_connect):
    datastore = redis_connect
    
    locked_key_dict = f"lock_index_{indices['index_dict']['index_name']}_dict"
    key = f"{indices['index_dict']['index_name']}_dict"
    datastore.put(locked_key_dict, json.dumps({'1':'a'}).encode('utf-8'), ttl_secs=30)

    assert is_index_locked(key)


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
