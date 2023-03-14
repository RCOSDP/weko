from weko_index_tree.utils import (
    get_index_link_list,
    is_index_tree_updated,
    get_user_roles,
    get_user_groups,
    check_roles,
    check_groups,
    filter_index_list_by_role,
    get_index_id_list,
    get_publish_index_id_list,
    get_admin_coverpage_setting,
    get_elasticsearch_records_data_by_indexes,
    get_index_id,
    count_items,
    check_doi_in_index_and_child_index,
    __get_redis_store,
    lock_all_child_index,
    unlock_index,
    is_index_locked,
    validate_before_delete_index,
    perform_delete_index,
    get_doi_items_in_index,
    cached_index_tree_json,
    reset_tree,
    get_tree_json,
    get_editing_items_in_index,
    reduce_index_by_more,
    reduce_index_by_role,
    recorrect_private_items_count,
    sanitize,
    check_doi_in_index,
    get_record_in_es_of_index,
    check_doi_in_list_record_es,
    check_restrict_doi_with_indexes,
    check_has_any_item_in_index_is_locked,
    check_index_permissions,
    generate_path
)

from invenio_accounts.testutils import login_user_via_session, client_authenticated
######
import json
import pytest
from mock import patch
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
from invenio_deposit.api import Deposit

from weko_index_tree.api import Indexes
from weko_index_tree.models import Index
from weko_workflow.models import Activity, ActionStatus, Action, WorkFlow, FlowDefine, FlowAction
from weko_admin.utils import is_exists_key_in_redis
from weko_groups.models import Group
from weko_redis.redis import RedisConnection


# from .config import WEKO_INDEX_TREE_STATE_PREFIX
# from .errors import IndexBaseRESTError, IndexDeletedRESTError
# from .models import Index


#*** def get_index_link_list(pid=0):
def test_get_index_link_list(i18n_app, users, indices, esindex):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        pid = 44
        tree = Indexes.get_browsing_tree_ignore_more(pid)
        
        # Test 1
        assert not get_index_link_list()

        # Test 2
        assert get_index_link_list(pid)
        

#+++ def is_index_tree_updated():
def test_is_index_tree_updated(app):
    assert is_index_tree_updated()


#+++ def cached_index_tree_json(timeout=50, key_prefix='index_tree_json'):
def test_cached_index_tree_json(i18n_app):
    assert cached_index_tree_json()


#+++ def reset_tree(tree, path=None, more_ids=None, ignore_more=False):
def test_reset_tree(i18n_app, users, indices, records):
    pid = 44    
    tree = Indexes.get_browsing_tree_ignore_more(pid)
    
    # Doesn't return anything and will pass if there are no errors
    assert reset_tree(tree) == None


#*** def get_tree_json(index_list, root_id):
# def test_get_tree_json(i18n_app, db_records, indices, esindex):
#     assert get_tree_json([indices['index_non_dict']], 0)


#+++ def get_user_roles():
def test_get_user_roles(i18n_app, client_rest, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_user_roles()[0]

    # User not authenticated
    assert get_user_roles()[0] == False


#+++ def get_user_groups():
def test_get_user_groups(i18n_app, client_rest, users, db):
    with patch("flask_login.utils._get_user", return_value=users[-1]['obj']):
        from weko_groups.models import Group

        g1 = Group.create(name="group_test1").add_member(users[-1]['obj'])
        g2 = Group.create(name="group_test2").add_member(users[-1]['obj'])
        db.session.add(g1)
        db.session.add(g2)

        assert get_user_groups()
    # User not authenticated
    assert len(get_user_groups()) == 0


#+++ def check_roles(user_role, roles):
def test_check_roles(users):
    with patch("flask_login.utils._get_user", return_value=users[-1]['obj']):
    
        user_role = [role.name for role in users[-1]['obj'].roles]
        roles = (',').join(user_role)

        assert check_roles(user_role, roles)


#+++ def check_groups(user_group, groups):
def test_check_groups(i18n_app, users, db):
    g1 = Group.create(name="group_test1").add_member(users[-1]['obj'])
    g2 = Group.create(name="group_test2").add_member(users[-1]['obj'])

    db.session.add(g1)
    db.session.add(g2)

    user_group = ["group_test1", "group_test2"]
    groups = [v for k,v in Group.get_group_list().items()]
    
    with patch("flask_login.utils._get_user", return_value=users[-1]['obj']):
        assert check_groups(user_group, groups)

    assert check_groups(user_group, groups) == False


#+++ def filter_index_list_by_role(index_list):
#     def _check(index_data, roles, groups):
def test_filter_index_list_by_role(i18n_app, indices, users, db):
    with patch("flask_login.utils._get_user", return_value=users[-1]['obj']):
        from weko_groups.models import Group
        g1 = Group.create(name="group_test1").add_member(users[-1]['obj'])
        g2 = Group.create(name="group_test2").add_member(users[-1]['obj'])

        db.session.add(g1)
        db.session.add(g2)

        assert len(filter_index_list_by_role([indices['index_non_dict']])) > 0

    assert len(filter_index_list_by_role([indices['index_non_dict']])) == 0


#+++ def reduce_index_by_role(tree, roles, groups, browsing_role=True, plst=None):
def test_reduce_index_by_role(i18n_app, indices, users, db_records, db):
    g1 = Group.create(name="group_test1").add_member(users[-1]['obj'])
    g2 = Group.create(name="group_test2").add_member(users[-1]['obj'])
    db.session.add(g1)
    db.session.add(g2)
    groups = [v for k,v in Group.get_group_list().items()]

    roles = [role.name for role in users[-1]['obj'].roles]
    roles.append('contribute_role')

    tree = Indexes.get_browsing_tree_ignore_more(33)

    # Doesn't return anything and will pass if there are no errors
    assert not reduce_index_by_role(tree, roles, groups)


#+++ def get_index_id_list(indexes, id_list=None):
def test_get_index_id_list(indices, db):
    index_list = [indices['index_dict']]
    str_id = str(index_list[0]['id'])
    index_list[0]['id'] = str_id
    index_list[0]['parent'] = str(index_list[0]['parent'])

    assert get_index_id_list(index_list)
    
    index_list[0]['id'] = 'more'

    assert not get_index_id_list(index_list)


#+++ def get_publish_index_id_list(indexes, id_list=None):
def test_get_publish_index_id_list(indices, db):
    index_list = [indices['index_dict']]
    str_id = str(index_list[0]['id'])
    index_list[0]['id'] = str_id
    index_list[0]['parent'] = str(index_list[0]['parent'])

    assert get_publish_index_id_list(index_list)
    
    index_list[0]['id'] = 'more'

    assert not get_publish_index_id_list(index_list)


#+++ def reduce_index_by_more(tree, more_ids=None):
def test_reduce_index_by_more(i18n_app, db_records, indices):
    tree = Indexes.get_browsing_tree_ignore_more(44)

    # Doesn't return anything and will pass if there are no errors
    assert not reduce_index_by_more(tree)


#+++ def get_admin_coverpage_setting():
def test_get_admin_coverpage_setting(pdfcoverpage):
    assert get_admin_coverpage_setting()


#+++ def get_elasticsearch_records_data_by_indexes(index_ids, start_date, end_date):
def test_get_elasticsearch_records_data_by_indexes(i18n_app, db_records, indices, esindex):
    idx_tree_ids = [idx.cid for idx in Indexes.get_recursive_tree(indices['index_non_dict'].id)]
    current_date = date.today()
    start_date = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = current_date.strftime("%Y-%m-%d")

    assert get_elasticsearch_records_data_by_indexes(idx_tree_ids, start_date, end_date)
    

#+++ def generate_path(index_ids):
def test_generate_path(i18n_app, indices, esindex):
    assert generate_path(Indexes.get_recursive_tree(33))


#+++ def get_index_id(activity_id):
def test_get_index_id(i18n_app, users, db_register):
    activity_id = db_register['activity'].activity_id

    assert get_index_id(activity_id)


#+++ def sanitize(s):
def test_sanitize():
    assert sanitize("abc\n")


#+++ def count_items(indexes_aggr):
def test_count_items(count_json_data):
    indexes_aggr = count_json_data

    assert count_items(indexes_aggr)


#+++  def recorrect_private_items_count(agp):
def test_recorrect_private_items_count(i18n_app, records):
    agp = records['aggregations']['path']['buckets']

    # Doesn't return anything and will pass if there are no errors
    assert not recorrect_private_items_count(agp)


#+++ def check_doi_in_index(index_id):
def test_check_doi_in_index(i18n_app, indices, db_records):
    assert check_doi_in_index(33)


#*** def get_record_in_es_of_index(index_id, recursively=True):
def test_get_record_in_es_of_index(i18n_app, indices, db_records, esindex):
    # Test 1
    assert not get_record_in_es_of_index(44, recursively=False)

    # Test 2
    # assert get_record_in_es_of_index(33)


#*** def check_doi_in_list_record_es(index_id):
def test_check_doi_in_list_record_es(i18n_app, indices, esindex):
    # Test 1
   assert not check_doi_in_list_record_es(33)


#+++ def check_restrict_doi_with_indexes(index_ids):
def test_check_restrict_doi_with_indexes(i18n_app, indices, db_records):
    assert check_restrict_doi_with_indexes([33,44])


#*** def check_has_any_item_in_index_is_locked(index_id):
def test_check_has_any_item_in_index_is_locked(i18n_app, indices, records, esindex):
    # Test 1
    assert not check_has_any_item_in_index_is_locked(33)

    # Test 2
    # assert check_has_any_item_in_index_is_locked(33)


#+++ def check_index_permissions(record=None, index_id=None, index_path_list=None, is_check_doi=False) -> bool
def test_check_index_permissions(i18n_app, indices, db_records):
    # for depid, recid, parent, doi, record, item in db_records:
    record = db_records[0][4]
    index_id = 33
    index_path_list = [33]
    
    # Test 1
    assert not check_index_permissions()

    # Test 2
    assert check_index_permissions(
        record=record,
        index_id=index_id,
        index_path_list=index_path_list
    )


# *** def check_doi_in_index_and_child_index(index_id, recursively=True):
# def test_check_doi_in_index_and_child_index(i18n_app, indices, esindex, db_records, records2):
def test_check_doi_in_index_and_child_index(i18n_app, users, indices, esindex):
    # Test 1
    assert len(check_doi_in_index_and_child_index(33, recursively=True)) == 0

    # Test 2
    # assert len(check_doi_in_index_and_child_index(33, recursively=True)) > 0


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


#+++ def validate_before_delete_index(index_id):
def test_validate_before_delete_index(i18n_app, indices):
    index_id = indices['index_non_dict'].id

    assert validate_before_delete_index(index_id)


#+++ def is_index_locked(index_id):
def test_is_index_locked(i18n_app, indices, redis_connect):
    datastore = redis_connect
    
    locked_key_dict = f"lock_index_{indices['index_dict']['index_name']}_dict"
    key = f"{indices['index_dict']['index_name']}_dict"
    datastore.put(locked_key_dict, json.dumps({'1':'a'}).encode('utf-8'), ttl_secs=30)

    assert is_index_locked(key)


#+++ def perform_delete_index(index_id, record_class, action: str):
def test_perform_delete_index(i18n_app, indices, records):
    record_list = RecordMetadata.query.all()
    index_id = indices['index_non_dict'].id
    
    assert perform_delete_index(index_id, record_list[0], "all")


#*** def get_doi_items_in_index(index_id, recursively=False):
def test_get_doi_items_in_index(i18n_app, users, indices, esindex, records):
    # Test 1
    assert not get_doi_items_in_index(44, recursively=False)

    # Test 2
    # with patch("flask_login.utils._get_user", return_value=users[-1]['obj']):
    #     assert get_doi_items_in_index(44, recursively=False)


#*** def test_get_editing_items_in_index(index_id, recursively=False):
def test_get_editing_items_in_index(i18n_app, users, indices, esindex, db_records, records):
    # Test 1
    assert not get_editing_items_in_index(44)

    # Test 2
    # with patch("flask_login.utils._get_user", return_value=users[-1]['obj']):
    #     assert get_doi_items_in_index(44)