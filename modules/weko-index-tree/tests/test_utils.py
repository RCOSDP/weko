import copy
import os

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
    generate_path,
    save_index_trees_to_redis,
    str_to_datetime
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
from weko_index_tree.errors import IndexBaseRESTError
from weko_workflow.models import Activity, ActionStatus, Action, WorkFlow, FlowDefine, FlowAction
from weko_admin.utils import is_exists_key_in_redis
from weko_groups.models import Group
from weko_redis.redis import RedisConnection


# from .config import WEKO_INDEX_TREE_STATE_PREFIX
# from .errors import IndexBaseRESTError, IndexDeletedRESTError
# from .models import Index

# def get_index_link_list
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_get_index_link_list -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_get_index_link_list(app, db, users):
    tree = [{
        "id": "10",
        "link_name": "Index link 10",
        "index_link_enabled": True,
        "children": [
            {
                "id": "11",
                "link_name": "Index link 11",
                "index_link_enabled": True,
                "children": []
            },
            {
                "id": "12",
                "link_name": "Index link 12",
                "index_link_enabled": False,
                "children": []
            }
        ]
    }]
    with patch("weko_index_tree.api.Indexes.get_browsing_tree_ignore_more", return_value=tree):
        assert get_index_link_list(10)==[(10, 'Index link 10'), (11, 'Index link 11')]
        

#+++ def is_index_tree_updated():
def test_is_index_tree_updated(app):
    assert is_index_tree_updated()


#+++ def cached_index_tree_json(timeout=50, key_prefix='index_tree_json'):
def test_cached_index_tree_json(i18n_app):
    assert cached_index_tree_json()


# def reset_tree(tree, path=None, more_ids=None, ignore_more=False):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_get_index_link_list -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_reset_tree(app, db, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        with app.test_request_context(headers=[("Accept-Language", "en")]):
            tree = []
            reset_tree(tree)
            assert tree==[]

            tree = []
            reset_tree(tree, ignore_more=True)
            assert tree==[]

            tree = []
            reset_tree(tree, "10")
            assert tree==[]

    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        with app.test_request_context(headers=[("Accept-Language", "en")]):
            tree = []
            reset_tree(tree, ignore_more=True)
            assert tree==[]

            tree = []
            reset_tree(tree, ["10"], more_ids=["10"])
            assert tree==[]


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

    assert len(filter_index_list_by_role([indices['index_non_dict']])) == 1


# def reduce_index_by_role
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_reduce_index_by_role -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_reduce_index_by_role(app, db, users):
    """with db.session.begin_nested():
        db.session.add(_base_index(100, 0, 1))
        db.session.add(_base_index(110, 100, 1, public_date=datetime(2022, 1, 1), group="group_test1", browsing_role=None, contribute_role="1,2,3,4,-99"))
    db.session.commit()"""

    g1 = Group.create(name="group_test1").add_member(users[3]['obj'])
    db.session.add(g1)
    groups = [v for k,v in Group.get_group_list().items()]

    admin_roles = (True, ["1"])
    user_roles = (False, ["-98"])
    #roles.append('contribute_role')
    assert not reduce_index_by_role({}, admin_roles, groups)
    assert not reduce_index_by_role([[]], admin_roles, groups)

    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        with app.test_request_context(headers=[("Accept-Language", "en")]):
            tree = [{
                "id": "10",
                "contribute_role": "1,2,3,4,-98,-99",
                "public_state": True,
                "public_date": datetime(2022, 1, 1, 0, 0),
                "browsing_role": "3,-98,-99",
                "contribute_group": "",
                "browsing_group": "",
                "children": [
                    {
                        "id": "11",
                        "contribute_role": "1,2,3,4,-98,-99",
                        "public_state": True,
                        "public_date": datetime(2022, 1, 1, 0, 0),
                        "browsing_role": "3,-98,-99",
                        "contribute_group": "group_test1",
                        "browsing_group": "group_test1",
                        "children": [],
                        "settings": []
                    },
                    {
                        "id": "12",
                        "contribute_role": "",
                        "public_state": True,
                        "public_date": "2022-01-01T00:00:00",
                        "browsing_role": "",
                        "contribute_group": "group_test1",
                        "browsing_group": "group_test1",
                        "children": [],
                        "settings": []
                    },
                    {
                        "id": "13",
                        "contribute_role": "1,2,3,4,-98,-99",
                        "public_state": True,
                        "public_date": datetime(datetime.today().year + 1, 1, 1, 0, 0),
                        "browsing_role": "3,-98,-99",
                        "contribute_group": "group_test1",
                        "browsing_group": "group_test1",
                        "children": [],
                        "settings": []
                    }
                ],
                "settings": {
                    "checked": False
                }
            }]
            new_tree = copy.deepcopy(tree)
            reduce_index_by_role(new_tree, admin_roles, groups, True)
            assert new_tree==[{'id': '10', 'children': [{'id': '11', 'children': [], 'settings': []}, {'id': '12', 'children': [], 'settings': []}], 'settings': {'checked': False}}]

            new_tree = copy.deepcopy(tree)
            reduce_index_by_role(new_tree, user_roles, groups, True)
            assert new_tree==[{'id': '10', 'children': [{'id': '11', 'children': [], 'settings': []}, {'id': '12', 'children': [], 'settings': []}], 'settings': {'checked': False}}]

            new_tree = copy.deepcopy(tree)
            reduce_index_by_role(new_tree, user_roles, [], True)
            assert new_tree==[{'id': '10', 'children': [{'id': '11', 'children': [], 'settings': []}], 'settings': {'checked': False}}]

            new_tree = copy.deepcopy(tree)
            reduce_index_by_role(new_tree, admin_roles, groups, False)
            assert new_tree==[{'id': '10', 'children': [{'id': '11', 'children': [], 'settings': [], 'disabled': False}, {'id': '12', 'children': [], 'settings': [], 'disabled': False}, {'id': '13', 'children': [], 'settings': [], 'disabled': False}], 'settings': {'checked': False}, 'disabled': False}]

            new_tree = copy.deepcopy(tree)
            reduce_index_by_role(new_tree, user_roles, groups, False)
            assert new_tree==[{'id': '10', 'children': [{'id': '11', 'children': [], 'settings': [], 'disabled': False}, {'id': '12', 'children': [], 'settings': [], 'disabled': False}, {'id': '13', 'children': [], 'settings': [], 'disabled': False}], 'settings': {'checked': False}, 'disabled': False}]

            new_tree = copy.deepcopy(tree)
            reduce_index_by_role(new_tree, user_roles, [], False, ["10", "12"])
            assert new_tree==[{'id': '10', 'children': [{'id': '11', 'children': [], 'settings': [], 'disabled': False}, {'id': '13', 'children': [], 'settings': [], 'disabled': False}], 'settings': {'checked': True}, 'disabled': False}]


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


# def reduce_index_by_more
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_reduce_index_by_more -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_reduce_index_by_more(app, db, users):
    tree = [{
        "id": "10",
        "more_check": True,
        "display_no": 2,
        "children": [
            {
                "id": "11",
                "more_check": True,
                "display_no": 2,
                "children": [[]]
            },
            {
                "id": "12",
                "more_check": False,
                "display_no": 2,
                "children": []
            },
            {
                "id": "13",
                "more_check": False,
                "display_no": 2,
                "children": []
            }
        ],
        "settings": {
            "checked": False
        }
    }]

    reduce_index_by_more(tree)
    assert tree==[{'id': '10', 'more_check': True, 'display_no': 2, 'children': [{'id': '11', 'more_check': True, 'display_no': 2, 'children': [[]]}, {'id': '12', 'more_check': False, 'display_no': 2, 'children': []}, {'id': 'more', 'value': '<a href="#" class="more">more...</a>'}], 'settings': {'checked': False}}]


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


# def check_doi_in_list_record_es(index_id):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_check_doi_in_list_record_es -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_check_doi_in_list_record_es(app, db, users):
    _data1 = [
        {
            "_source": {"control_number": "0", "path": ["1"]}
        }
    ]
    _data2 = [
        {
            "_source": {"control_number": "1", "path": ["1", "2"]}
        }
    ]
    with patch("weko_index_tree.utils.check_doi_in_index_and_child_index", return_value=[]):
        assert check_doi_in_list_record_es(1)==False
    with patch("weko_index_tree.utils.check_doi_in_index_and_child_index", return_value=_data1):
        assert check_doi_in_list_record_es(1)==True
    with patch("weko_index_tree.utils.check_doi_in_index_and_child_index", return_value=_data2):
        with patch("weko_index_tree.utils.check_index_permissions", return_value=True):
            assert check_doi_in_list_record_es(1)==False
        with patch("weko_index_tree.utils.check_index_permissions", return_value=False):
            assert check_doi_in_list_record_es(1)==True


#+++ def check_restrict_doi_with_indexes(index_ids):
def test_check_restrict_doi_with_indexes(i18n_app, indices, db_records):
    assert check_restrict_doi_with_indexes([33,44])


#*** def check_has_any_item_in_index_is_locked(index_id):
def test_check_has_any_item_in_index_is_locked(i18n_app, indices, records, esindex):
    # Test 1
    assert not check_has_any_item_in_index_is_locked(33)

    # Test 2
    # assert check_has_any_item_in_index_is_locked(33)


# def check_index_permissions(record=None, index_id=None, index_path_list=None, is_check_doi=False) -> bool
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_check_index_permissions -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_check_index_permissions(app, db, users, test_indices, db_records):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        with app.test_request_context(headers=[("Accept-Language", "en")]):
            assert check_index_permissions()==False
            assert check_index_permissions(record={"path": "1"})==True
            assert check_index_permissions(index_id="1")==True
            assert check_index_permissions(index_path_list=["1", "2"], is_check_doi=True)==True

    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        with app.test_request_context(headers=[("Accept-Language", "en")]):
            assert check_index_permissions()==False
            assert check_index_permissions(record={"path": "1"})==False
            assert check_index_permissions(index_id="1")==False
            assert check_index_permissions(index_path_list=["1", "2"], is_check_doi=True)==True


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


# def perform_delete_index(index_id, record_class, action: str):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_perform_delete_index -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_perform_delete_index(app, db, test_indices, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        with app.test_request_context(headers=[("Accept-Language", "en")]):
            with patch("weko_index_tree.utils.is_index_locked", return_value=False):
                assert perform_delete_index(1, Indexes, "move")==('', ['The index cannot be deleted because there is a link from an item that has a DOI.'])
            with patch("weko_index_tree.utils.check_doi_in_index", return_value=False):
                _data = [
                    {
                        "_source": {"_item_metadata": {"control_number": "0"}}
                    },
                    {
                        "_source": {"_item_metadata": {"control_number": "1"}}
                    }
                ]
                with patch("weko_index_tree.utils.get_record_in_es_of_index", return_value=_data):
                    with patch("weko_workflow.utils.check_an_item_is_locked", return_value=True):
                        assert perform_delete_index(1, Indexes, "move")==('', ['This index cannot be deleted because the item belonging to this index is being edited by the import function.'])
                    with patch("weko_workflow.utils.check_an_item_is_locked", return_value=False):
                        with pytest.raises(IndexBaseRESTError) as e:
                            perform_delete_index(1, Indexes, "move")
                        assert e.value.code == 400
                        assert perform_delete_index(1, Indexes, "delete")==('Index deleted successfully.', [])


# def get_doi_items_in_index(index_id, recursively=False):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_save_index_trees_to_redis -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_get_doi_items_in_index(app):
    _data = [
        {
            "_source": {"control_number": "0", "path": ["1"]}
        },
        {
            "_source": {"control_number": "1", "path": []}
        }
    ]
    with patch("weko_index_tree.utils.check_doi_in_index_and_child_index", return_value=_data):
        res = get_doi_items_in_index("1")
        assert res==["0"]


# def get_editing_items_in_index(index_id, recursively=False):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_save_index_trees_to_redis -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_get_editing_items_in_index(app):
    _es_data = [
        {
            "_source": {
                "_item_metadata": {"control_number": "1"}
            }
        },
        {
            "_source": {
                "_item_metadata": {"control_number": "2"}
            }
        }
    ]
    with patch("weko_index_tree.utils.get_record_in_es_of_index", return_value=_es_data):
        with patch("weko_items_ui.utils.check_item_is_being_edit", return_value=True):
            with patch("invenio_pidstore.models.PersistentIdentifier.get", return_value=True):
                res = get_editing_items_in_index(0)
                assert res == ["1", "2"]
        
        with patch("weko_items_ui.utils.check_item_is_being_edit", return_value=False):
            with patch("invenio_pidstore.models.PersistentIdentifier.get", return_value=True):
                with patch("weko_workflow.utils.check_an_item_is_locked", return_value=False):
                    res = get_editing_items_in_index(0)
                    assert res == []


# def save_index_trees_to_redis(tree):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_save_index_trees_to_redis -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_save_index_trees_to_redis(app, redis_connect):
    tree = [{"id": "1"}]
    os.environ['INVENIO_WEB_HOST_NAME'] = "test"
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        assert not save_index_trees_to_redis(tree)


# def str_to_datetime(str_dt, format):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_str_to_datetime -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_str_to_datetime():
    date_str = "2022-01-01"
    date_format1 = "%Y-%m-%d"
    date_format2 = "%Y-%m-%dT%H:%M:%S"
    assert str_to_datetime(date_str, date_format1)==datetime(2022, 1, 1)
    assert str_to_datetime(date_str, date_format2)==None
