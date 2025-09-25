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
    delete_index_trees_from_redis,
    str_to_datetime,
    get_descendant_index_names,
    get_item_ids_in_index,
    get_all_records_in_index,
)

from invenio_accounts.testutils import login_user_via_session, client_authenticated
######
import json
import pytest
from mock import patch, MagicMock
from datetime import date, datetime, timedelta
from functools import wraps
from operator import itemgetter

import redis
from redis import sentinel
from elasticsearch import helpers
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl.query import Bool, Exists, Q, QueryString
from flask import Markup, current_app, session
from flask_babelex import get_locale
from flask_babelex import gettext as _
from flask_babelex import to_user_timezone, to_utc
from flask_login import current_user, login_user, LoginManager
from invenio_cache import current_cache
from invenio_communities.models import Community
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

# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_get_user_roles -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
#+++ def get_user_roles():
def test_get_user_roles(i18n_app, client_rest, users):
    # sysadmin
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        result = get_user_roles(is_super_role=True)
        assert result[0] == True
        assert result[1] == [1]

        result = get_user_roles(is_super_role=False)
        assert result[0] == True
        assert result[1] == [1]

    # comadmin
    with patch("flask_login.utils._get_user", return_value=users[4]['obj']):
        result = get_user_roles(is_super_role=True)
        assert result[0] == True
        assert result[1] == [4]

        result = get_user_roles(is_super_role=False)
        assert result[0] == False
        assert result[1] == [4]


    # not admin user
    with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
        result = get_user_roles(is_super_role=True)
        assert result[0] == False
        assert result[1] == [3]

        result = get_user_roles(is_super_role=False)
        assert result[0] == False
        assert result[1] == [3]

    # User not authenticated
    result = get_user_roles()
    assert result[0] == False
    assert result[1] == None



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

# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_check_roles -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
#+++ def check_roles(user_role, roles):
def test_check_roles(i18n_app, users):
    # admin user
    user_role = (True, [])
    roles = ["1","2"]
    check_roles(user_role, roles)

    # not admin user
    ## not login
    ### not allow -99
    user_role = (False,[])
    roles = "1,2"
    assert check_roles(user_role, roles) == False
    ### allow -99
    user_role = (False,[])
    roles = "1,2,-99"
    assert check_roles(user_role, roles) == True
    ## login
    with patch("flask_login.utils._get_user", return_value=users[-1]['obj']):
    ### all allow
        user_role = (False,["1", "2"])
        roles = "1,2"
        assert check_roles(user_role, roles) == True
    ### exist deny
        user_role = (False,["1", "2", "3"])
        roles = "1,2"
        assert check_roles(user_role, roles) == False

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
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_get_elasticsearch_records_data_by_indexes -vv -s --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp --full-trace
def test_get_elasticsearch_records_data_by_indexes(i18n_app, indices, db_records, esindex):
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
#*** def check_doi_in_index_and_child_index(index_id, recursively=True):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_get_record_in_es_of_index -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_get_record_in_es_of_index(i18n_app, indices, db_records, esindex):
    # Test 1
    assert not get_record_in_es_of_index(44, recursively=False)
    assert not check_doi_in_index_and_child_index(44, recursively=False)

    # Test 2
    # assert get_record_in_es_of_index(33)

    def _generate_es_data(num, start_datetime=datetime.now()):
        for i in range(num):
            doc = {
                "_index": i18n_app.config['INDEXER_DEFAULT_INDEX'],
                "_type": "item-v1.0.0",
                "_id": f"2d1a2520-9080-437f-a304-230adc8{i:05d}",
                "_source": {
                    "_item_metadata": {
                        "title": [f"test_title_{i}"],
                    },
                    "relation_version_is_last": True,
                    "path": ["66"],
                    "control_number": f"{i:05d}",
                    "_created": (start_datetime + timedelta(seconds=i)).isoformat(),
                    "publish_status": "0",
                },
            }
            if i % 2 == 0:
                doc["_source"]["identifierRegistration"] = {
                    "identifierType": "DOI",
                    "value": f"10.9999/test_doi_{i:05d}",
                }
            yield doc

    generate_data_num = 30002
    helpers.bulk(esindex.client, _generate_es_data(generate_data_num), refresh='true')

    # result over 10000
    assert len(get_record_in_es_of_index(66)) == generate_data_num
    assert len(check_doi_in_index_and_child_index(66)) == int(generate_data_num / 2)


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
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_check_restrict_doi_with_indexes -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_check_restrict_doi_with_indexes(i18n_app, indices, db_records):
    assert not check_restrict_doi_with_indexes([33,44])
    assert check_restrict_doi_with_indexes([1000])
    assert not check_restrict_doi_with_indexes([33,1000])


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

    # comadmin
    with patch("flask_login.utils._get_user", return_value=users[4]['obj']):
        with app.test_request_context(headers=[("Accept-Language", "en")]):
            community = Community(root_node_id=1)
            with patch('weko_index_tree.utils.Community.get_repositories_by_user', return_value=[community]):
                assert check_index_permissions()==False
                assert check_index_permissions(record={"path": "1"})==True
                assert check_index_permissions(index_id="1")==True
                assert check_index_permissions(index_path_list=["1", "2"], is_check_doi=True)==True
            with patch('weko_index_tree.utils.Community.get_repositories_by_user', return_value=[]):
                assert check_index_permissions()==False
                assert check_index_permissions(record={"path": "1"})==False
                assert check_index_permissions(index_id="1")==False
                assert check_index_permissions(index_path_list=["1", "2"], is_check_doi=True)==True


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
# .tox/c1/bin/pytest --cov=weko-index-tree tests/test_utils.py::test_validate_before_delete_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_validate_before_delete_index(i18n_app, indices, mocker):
    """
    Test validate_before_delete_index when return validation success.
    Args:
        i18n_app (fixture): language setting
        indices (fixture): index data
        mocker (fixture): mocker
    """
    index_id = indices['index_non_dict'].id

    mocker.patch("weko_index_tree.utils.is_index_locked", return_value=False)
    mocker.patch('weko_index_tree.utils.lock_all_child_index', return_value=(True, ['lock_index_1', 'lock_index_2']))
    mocker.patch('weko_index_tree.utils.check_doi_in_index', return_value=False)
    mocker.patch('weko_index_tree.utils.get_editing_items_in_index', return_value=False)
    mocker.patch('weko_index_tree.utils.check_has_any_harvest_settings_in_index_is_locked', return_value=False)

    is_unlock, errors, locked_key = validate_before_delete_index(index_id)
    # 51994 case.05(validate_before_delete_index)
    assert is_unlock == True
    assert errors == []
    assert locked_key != []


# .tox/c1/bin/pytest --cov=weko-index-tree tests/test_utils.py::test_validate_before_delete_index_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
@pytest.mark.parametrize('validate', [
    'is_index_locked',
    'check_doi_in_index',
    'get_editing_items_in_index',
    'check_has_any_harvest_settings_in_index_is_locked'
])
def test_validate_before_delete_index_error(i18n_app, indices, validate, mocker):
    """
    Test validate_before_delete_index when return validation error.

    Args:
        i18n_app (fixture): language setting
        indices (fixture): index data
        validate (fixture): validation list
        mocker (fixture): mocker
    """
    index_id = indices['index_non_dict'].id
    # is_index_locked is True
    if validate == 'is_index_locked':
        mocker.patch("weko_index_tree.utils.is_index_locked", return_value=True)

        is_unlock, errors, locked_key = validate_before_delete_index(index_id)
        # 51994 case.01(validate_before_delete_index)
        assert is_unlock == False
        assert errors == [_('Index Delete is in progress on another device.')]
        assert locked_key == []
    else:
        # is_index_locked is False
        mocker.patch("weko_index_tree.utils.is_index_locked", return_value=False)
        mocker.patch('weko_index_tree.utils.lock_all_child_index', return_value=(True, ['lock_index_1', 'lock_index_2']))
        # check_doi_in_index is True
        if validate == 'check_doi_in_index':
            mocker.patch('weko_index_tree.utils.check_doi_in_index', return_value=True)
            mocker.patch('weko_index_tree.utils.get_editing_items_in_index', return_value=False)
            mocker.patch('weko_index_tree.utils.check_has_any_harvest_settings_in_index_is_locked', return_value=False)

            is_unlock, errors, locked_key = validate_before_delete_index(index_id)
            # 51994 case.02(validate_before_delete_index)
            assert is_unlock == True
            assert errors == [_('The index cannot be deleted because there is a link from an item that has a DOI.')]
        # get_editing_items_in_index is True
        elif validate == 'get_editing_items_in_index':
            mocker.patch('weko_index_tree.utils.check_doi_in_index', return_value=False)
            mocker.patch('weko_index_tree.utils.get_editing_items_in_index', return_value=True)
            mocker.patch('weko_index_tree.utils.check_has_any_harvest_settings_in_index_is_locked', return_value=False)

            is_unlock, errors, locked_key = validate_before_delete_index(index_id)
            # 51994 case.03(validate_before_delete_index)
            assert is_unlock == True
            assert errors == [_('This index cannot be deleted because the item belonging to this index is being edited.')]
        # check_has_any_harvest_settings_in_index_is_locked is True
        elif validate == 'check_has_any_harvest_settings_in_index_is_locked':
            mocker.patch('weko_index_tree.utils.check_doi_in_index', return_value=False)
            mocker.patch('weko_index_tree.utils.get_editing_items_in_index', return_value=False)
            mocker.patch('weko_index_tree.utils.check_has_any_harvest_settings_in_index_is_locked', return_value=True)

            is_unlock, errors, locked_key = validate_before_delete_index(index_id)
            # 51994 case.04(validate_before_delete_index)
            assert is_unlock == True
            assert errors == [_('The index cannot be deleted becase the index in harvester settings.')]


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
                with patch("weko_index_tree.utils.get_editing_items_in_index", return_value=["0"]):
                    assert perform_delete_index(1, Indexes, "move")==('', ['This index cannot be deleted because the item belonging to this index is being edited.'])
                with patch("weko_index_tree.utils.get_editing_items_in_index", return_value=[]):
                    with patch("weko_index_tree.api.Indexes.delete_by_action", return_value=None):
                        assert perform_delete_index(1, Indexes, "move")==('Failed to delete index.', [])
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
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_get_editing_items_in_index -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
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
                with patch("weko_workflow.utils.bulk_check_an_item_is_locked", return_value=["1", "2"]):
                    res = get_editing_items_in_index(0)
                    assert res == ["1", "2"]

        with patch("weko_items_ui.utils.check_item_is_being_edit", return_value=False):
            with patch("invenio_pidstore.models.PersistentIdentifier.get", return_value=True):
                with patch("weko_workflow.utils.bulk_check_an_item_is_locked", return_value=["1"]):
                    res = get_editing_items_in_index(0)
                    assert res == ["1"]

                with patch("weko_workflow.utils.bulk_check_an_item_is_locked", return_value=[]):
                    res = get_editing_items_in_index(0)
                    assert res == []


# def save_index_trees_to_redis(tree):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_save_index_trees_to_redis -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_save_index_trees_to_redis(app, redis_connect,caplog):
    tree = [{"id": "1"}]
    os.environ['INVENIO_WEB_HOST_NAME'] = "test"
    caplog.set_level(40) # set logging level to ERROR
    with app.test_request_context(headers=[('Accept-Language','en')]):
        # lang is None
        save_index_trees_to_redis(tree)
        assert json.loads(redis_connect.get("index_tree_view_test_en")) == [{"id":"1"}]

        # lang is not None
        save_index_trees_to_redis(tree, lang="ja")
        assert json.loads(redis_connect.get("index_tree_view_test_ja")) == [{"id":"1"}]

        # except ConnectionError
        with patch("simplekv.memory.redisstore.RedisStore.put",side_effect=ConnectionError("test_error")):
            save_index_trees_to_redis(tree, lang="ja")
            assert caplog.record_tuples == [('testapp', 40, 'Fail save index_tree to redis')]
    redis_connect.delete("index_tree_view_test_en")
    redis_connect.delete("index_tree_view_test_ja")

# def delete_index_trees_from_redis(lang):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_delete_index_trees_from_redis -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_delete_index_trees_from_redis(app, redis_connect):
    os.environ['INVENIO_WEB_HOST_NAME'] = "test"
    redis_connect.put("index_tree_view_test_ja","test_ja_cache".encode("UTF-8"),ttl_secs=30)
    delete_index_trees_from_redis("ja")
    assert redis_connect.redis.exists("index_tree_view_test_ja") == False
    delete_index_trees_from_redis("ja")

# def str_to_datetime(str_dt, format):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_str_to_datetime -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_str_to_datetime():
    date_str = "2022-01-01"
    date_format1 = "%Y-%m-%d"
    date_format2 = "%Y-%m-%dT%H:%M:%S"
    assert str_to_datetime(date_str, date_format1)==datetime(2022, 1, 1)
    assert str_to_datetime(date_str, date_format2)==None

# def get_descendant_index_names(index_id):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_get_descendant_index_names -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_get_descendant_index_names(app, db, test_indices):
    result = get_descendant_index_names(1)
    assert result[0] == "テストインデックス 1"
    assert result[1] == "テストインデックス 1-/-テストインデックス 11"

    result = get_descendant_index_names(11)
    assert result[0] == "テストインデックス 1-/-テストインデックス 11"

    result = get_descendant_index_names(999)
    assert result == []

# def get_item_ids_in_index(index_id):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_get_item_ids_in_index -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_get_item_ids_in_index():
    return_value = [{'_source': {'control_number': 123}}, {'_source': {'control_number': 456}}]
    with patch("weko_index_tree.utils.get_all_records_in_index", return_value=return_value):
        assert get_item_ids_in_index(1)==[123, 456]

    return_value = []
    with patch("weko_index_tree.utils.get_all_records_in_index", return_value=return_value):
        assert get_item_ids_in_index(1)==[]

    return_value = [{'key': 'value'}]
    with patch("weko_index_tree.utils.get_all_records_in_index", return_value=return_value):
        assert get_item_ids_in_index(1)==[]

# def get_all_records_in_index(index_id):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_utils.py::test_get_all_records_in_index -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_get_all_records_in_index(app, db, test_indices, mocker):
    first_page = {
        "hits": {
            "hits": [
                {'_source': {'control_number': 123}, 'sort': [1]},
                {'_source': {'control_number': 456}, 'sort': [2]}
            ]
        }
    }
    mock_search_instance = MagicMock()
    mock_search_instance.query.return_value.sort.return_value.params.return_value.execute.return_value.to_dict.return_value = first_page
    mocker.patch("weko_index_tree.utils.RecordsSearch", return_value=mock_search_instance)

    index_id = 1
    result = get_all_records_in_index(index_id)
    assert result == [
        {'_source': {'control_number': 123}, 'sort': [1]},
        {'_source': {'control_number': 456}, 'sort': [2]}
    ]

    first_page = {
        "hits": {
            "hits": [
                {'_source': {'control_number': i}, 'sort': [i]} for i in range(10000)
            ]
        }
    }
    second_page = {
    }
    mock_search_instance.query.return_value.sort.return_value.params.return_value.execute.return_value.to_dict.side_effect = [first_page, second_page]
    result = get_all_records_in_index(index_id)
    assert len(result) == 10000
    assert mock_search_instance.query.return_value.sort.return_value.params.return_value.execute.call_count == 2
