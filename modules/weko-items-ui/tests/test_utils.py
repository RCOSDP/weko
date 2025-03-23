import csv
import hashlib
import json
import os
from datetime import datetime, timedelta
from io import StringIO
from collections import OrderedDict
from unittest.mock import MagicMock
import copy
import tempfile
from uuid import UUID
from dictdiffer import diff, patch, swap, revert
from elasticsearch import exceptions as es_exceptions
import uuid

import pytest
from flask_security.utils import login_user
from invenio_stats.errors import UnknownQueryError
from weko_records_ui.errors import AvailableFilesNotFoundRESTError
from weko_redis.redis import RedisConnection
from invenio_accounts.testutils import login_user_via_session
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from jsonschema import SchemaError, ValidationError
from mock import patch
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_records.api import FeedbackMailList, ItemTypes, Mapping
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName
from weko_admin.models import ApiCertificate
from weko_workflow.api import WorkActivity
from weko_user_profiles.models import UserProfile
from weko_admin.models import SessionLifetime,RankingSettings
from weko_workflow.models import (
    Action,
    ActionStatus,
    ActionStatusPolicy,
    Activity,
    ActivityAction,
    FlowAction,
    FlowDefine,
    WorkFlow,
)
from weko_workflow.schema.marshmallow import ActivitySchema, ResponseMessageSchema

from weko_items_ui.utils import (
    __sanitize_string,
    _custom_export_metadata,
    _export_item,
    _get_max_export_items,
    check_approval_email,
    check_approval_email_in_flow,
    check_item_is_being_edit,
    check_item_is_deleted,
    check_item_type_name,
    export_items,
    find_hidden_items,
    get_permission_record,
    get_current_user,
    get_current_user_role,
    get_data_authors_affiliation_settings,
    get_data_authors_prefix_settings,
    get_excluded_sub_items,
    get_files_from_metadata,
    get_hide_list_by_schema_form,
    get_hide_parent_and_sub_keys,
    get_hide_parent_keys,
    get_ignore_item,
    get_ignore_item_from_mapping,
    get_item_from_option,
    get_key_title_in_item_type_mapping,
    get_list_email,
    get_list_file_by_record_id,
    get_list_username,
    get_mapping_name_item_type_by_key,
    get_mapping_name_item_type_by_sub_key,
    get_new_items_by_date,
    get_options_and_order_list,
    get_options_list,
    WekoQueryRankingHelper,
    get_ranking,
    get_title_in_request,
    get_user_info_by_email,
    get_user_info_by_username,
    get_user_information,
    get_user_permission,
    get_workflow_by_item_type_id,
    has_permission_edit_item,
    hide_form_items,
    hide_meta_data_for_role,
    hide_table_row,
    hide_thumbnail,
    is_need_to_show_agreement_page,
    is_schema_include_key,
    isExistKeyInDict,
    make_bibtex_data,
    make_stats_file,
    make_stats_file_with_permission,
    package_export_file,
    parse_node_str_to_json_schema,
    parse_ranking_new_items,
    parse_ranking_record,
    parse_ranking_results,
    permission_ranking,
    recursive_form,
    recursive_prepare_either_required_list,
    recursive_update_schema_form_with_condition,
    remove_excluded_items_in_json_schema,
    sanitize_input_data,
    save_title,
    set_multi_language_name,
    set_validation_message,
    to_files_js,
    translate_schema_form,
    translate_validation_message,
    update_action_handler,
    update_index_tree_for_record,
    update_json_schema_by_activity_id,
    update_json_schema_with_required_items,
    update_schema_form_by_activity_id,
    update_schema_remove_hidden_item,
    update_sub_items_by_user_role,
    validate_bibtex,
    validate_form_input_data,
    validate_user,
    validate_user_mail,
    validate_user_mail_and_index,
    write_bibtex_files,
    write_files,
    get_file_download_data,
    get_weko_link
    get_access_token,
    check_duplicate,
)
from weko_items_ui.config import WEKO_ITEMS_UI_DEFAULT_MAX_EXPORT_NUM,WEKO_ITEMS_UI_MAX_EXPORT_NUM_PER_ROLE
from invenio_indexer.api import RecordIndexer

# def get_list_username():
#  .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_list_username -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_list_username(app, client, users, db_userprofile):
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        assert get_list_username() == [
            "user",
            "comadmin",
            "repoadmin",
            "sysadmin",
            "generaluser",
            "originalroleuser",
            "originalroleuser2",
        ]


# def get_list_email():
#  .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_list_email -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_list_email(app, client, users, db_userprofile):
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        assert get_list_email() == [
            "user@test.org",
            "comadmin@test.org",
            "repoadmin@test.org",
            "sysadmin@test.org",
            "generaluser@test.org",
            "originalroleuser@test.org",
            "originalroleuser2@test.org",
        ]


# def get_user_info_by_username(username):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_user_info_by_username -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_user_info_by_username(users, db_userprofile):
    assert get_user_info_by_username(
        db_userprofile[users[0]["email"]].get_username
    ) == {
        "username": db_userprofile[users[0]["email"]].get_username,
        "user_id": users[0]["id"],
        "email": users[0]["email"],
    }

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_user_info_by_username_nouser -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_user_info_by_username_nouser():
    assert get_user_info_by_username("repoadmin@test.org")==None


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_user_info_by_username_exception -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_user_info_by_username_exception():
    with patch("weko_user_profiles.models.UserProfile.get_by_username", side_effect=Exception()):
        assert get_user_info_by_username("repoadmin@test.org")==None


# def validate_user(username, email):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_validate_user -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_validate_user(users, db_userprofile):
    assert validate_user(
        db_userprofile[users[0]["email"]].get_username, users[0]["email"]
    ) == {
        "results": {
            "username": "contributor",
            "user_id": 2,
            "email": "contributor@test.org",
        },
        "validation": True,
        "error": "",
    }
    assert validate_user(
        db_userprofile[users[0]["email"]].get_username, users[1]["email"]
    )=={'results': '', 'validation': False, 'error': ''}

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_validate_user_nodb -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_validate_user_nodb(app):
    with app.test_request_context():
        ret = validate_user("repoadmin@test.org","repoadmin@test.org")
        assert ret['error']
        assert ret['validation'] == False

# def get_user_info_by_email(email):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_user_info_by_email -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_user_info_by_email(users, db_userprofile):
    assert get_user_info_by_email(users[0]["email"]) == {
        "username": db_userprofile[users[0]["email"]].get_username,
        "user_id": users[0]["id"],
        "email": users[0]["email"],
    }

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_user_info_by_email_nodb -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_user_info_by_email_nodb():
    assert get_user_info_by_email("repoadmin@test.org") == None


# def get_user_information(user_id):
#  .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_user_information -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_user_information(users, db_userprofile):
    assert get_user_information(users[0]["id"]) == {
        "username": db_userprofile[users[0]["email"]].get_username,
        "fullname": db_userprofile[users[0]["email"]].fullname,
        "email": users[0]["email"],
    }

#  .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_user_information_nodb -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_user_information_nodb(db_userprofile):
    assert get_user_information(1) ==  {'email': '', 'fullname': '', 'username': ''}

# def get_user_permission(user_id):
#  .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_user_permission -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_user_permission(users):
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        assert get_user_permission(users[0]["id"]) == True
        assert get_user_permission(users[1]["id"]) == False


# def get_current_user():
#  .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_current_user(users):
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        assert get_current_user() == str(users[0]["id"])


# def find_hidden_items(item_id_list, idx_paths=None):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_find_hidden_items -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_find_hidden_items(app, users, db_records):
    depid0, recid0, parent0, doi0, record0, item0 = db_records[0]
    depid1, recid1, parent1, doi1, record1, item1 = db_records[2]
    assert record0['publish_status']=='0'
    assert record1['publish_status']=='1'
    with app.test_request_context():
        result = find_hidden_items([record0.id, record1.id],[1,2])
        target = [str(record0.id), str(record1.id)]
        for item in result:
            if item in target:
                i = target.index(item)
                target.pop(i)
        assert target == []

    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        with app.test_request_context():
            assert users[0]["email"] == "contributor@test.org"
            result = find_hidden_items([record0.id, record1.id],[1,2])
            target = [str(record0.id), str(record1.id)]
            for item in result:
                if item in target:
                    i = target.index(item)
                    target.pop(i)
            assert target == []

    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        with app.test_request_context():
            assert users[1]["email"] == "repoadmin@test.org"
            result = find_hidden_items([record0.id, record1.id],[1,2])
            target = [str(record0.id), str(record1.id)]
            for item in result:
                if item in target:
                    i = target.index(item)
                    target.pop(i)
            assert target == [str(record0.id), str(record1.id)]

    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        with app.test_request_context():
            assert users[1]["email"] == "repoadmin@test.org"
            result = find_hidden_items([record0.id, record1.id],[1,2], False)
            target = [str(record0.id), str(record1.id)]
            for item in result:
                if item in target:
                    i = target.index(item)
                    target.pop(i)
            assert target == [str(record0.id), str(record1.id)]

    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        with app.test_request_context():
            assert users[1]["email"] == "repoadmin@test.org"
            result = find_hidden_items([record0.id, record1.id], None, True)
            target = [str(record0.id), str(record1.id)]
            for item in result:
                if item in target:
                    i = target.index(item)
                    target.pop(i)
            assert target == [str(record0.id), str(record1.id)]

    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        with app.test_request_context():
            assert users[1]["email"] == "repoadmin@test.org"
            result = find_hidden_items([record0.id, record1.id],[1,2], False, [1, 2])
            target = [str(record0.id), str(record1.id)]
            for item in result:
                if item in target:
                    i = target.index(item)
                    target.pop(i)
            assert target == [str(record0.id), str(record1.id)]


# def get_permission_record(index_info,
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_permission_record -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_permission_record(app, users, db_itemtype, db_records):
    es_data = [
        {
            'key': '6',
            '_item_metadata': {
                'control_number': 6
            },
            'publish_date': '2022-09-02',
            'count': 1
        }
    ]

    with app.test_request_context():
        res = get_permission_record('most_reviewed_items', es_data, 1, [1])
        assert res == []

    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        with app.test_request_context():
            res = get_permission_record('most_downloaded_items', es_data, 1, [1])
            assert res == [{'rank': 1, 'key': '6', 'count': 1, 'title': 'title', 'url': '../records/6'}]

    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        with app.test_request_context():
            res = get_permission_record('new_items', es_data, 1, [1])
            assert res == [{'date': '2022-09-02', 'key': '6', 'title': 'title', 'url': '../records/6'}]



# def parse_ranking_results(index_info,
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_parse_ranking_results -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_parse_ranking_results(app, users):
    res = parse_ranking_results('most_searched_keywords', 'search_key', 2, 1)
    assert res == {'rank': 1, 'key': 'search_key', 'count': 2, 'title': 'search_key', 'url': '../search?page=1&size=20&search_type=1&q=search_key'}

    res = parse_ranking_results('created_most_items_user', 1, 2, 1)
    assert res == {'rank': 1, 'key': 1, 'count': 2, 'title': 'None', 'url': None}

    res = parse_ranking_results('created_most_items_user', None, 2, -1)
    assert res == {'key': None, 'title': 'None', 'url': None}

    with pytest.raises(Exception):
        parse_ranking_results('', None, 2, -1)


# def parse_ranking_new_items(result_data):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_parse_ranking_new_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_parse_ranking_new_items():
    results = {
        "took": 7,
        "timed_out": False,
        "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
        "hits": {
            "total": 2,
            "max_score": None,
            "hits": [
                {
                    "_index": "tenant1-weko-item-v1.0.0",
                    "_type": "item-v1.0.0",
                    "_id": "a64f4db8-b7d7-4cdf-a679-2b0e73f854c4",
                    "_score": None,
                    "_source": {
                        "_created": "2022-08-20T06:05:56.806896+00:00",
                        "_updated": "2022-08-20T06:06:24.602226+00:00",
                        "type": ["conference paper"],
                        "title": ["ff"],
                        "control_number": "3",
                        "_oai": {
                            "id": "oai:weko3.example.org:00000003",
                            "sets": ["1660555749031"],
                        },
                        "_item_metadata": {
                            "_oai": {
                                "id": "oai:weko3.example.org:00000003",
                                "sets": ["1660555749031"],
                            },
                            "path": ["1660555749031"],
                            "owner": "1",
                            "title": ["ff"],
                            "pubdate": {
                                "attribute_name": "PubDate",
                                "attribute_value": "2022-08-20",
                            },
                            "item_title": "ff",
                            "author_link": [],
                            "item_type_id": "15",
                            "publish_date": "2022-08-20",
                            "publish_status": "0",
                            "weko_shared_id": -1,
                            "item_1617186331708": {
                                "attribute_name": "Title",
                                "attribute_value_mlt": [
                                    {
                                        "subitem_1551255647225": "ff",
                                        "subitem_1551255648112": "ja",
                                    }
                                ],
                            },
                            "item_1617258105262": {
                                "attribute_name": "Resource Type",
                                "attribute_value_mlt": [
                                    {
                                        "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                                        "resourcetype": "conference paper",
                                    }
                                ],
                            },
                            "relation_version_is_last": True,
                            "control_number": "3",
                        },
                        "itemtype": "デフォルトアイテムタイプ（フル）",
                        "publish_date": "2022-08-20",
                        "author_link": [],
                        "weko_shared_id": -1,
                        "weko_creator_id": "1",
                        "relation_version_is_last": True,
                        "path": ["1660555749031"],
                        "publish_status": "0",
                    },
                    "sort": [1660953600000],
                },
                {
                    "_index": "tenant1-weko-item-v1.0.0",
                    "_type": "item-v1.0.0",
                    "_id": "3cc6099a-4208-4528-80ce-eee7fe4296b7",
                    "_score": None,
                    "_source": {
                        "_created": "2022-08-17T17:00:43.877778+00:00",
                        "_updated": "2022-08-17T17:01:08.615488+00:00",
                        "type": ["conference paper"],
                        "title": ["2"],
                        "control_number": "1",
                        "_oai": {
                            "id": "oai:weko3.example.org:00000001",
                            "sets": ["1660555749031"],
                        },
                        "_item_metadata": {
                            "_oai": {
                                "id": "oai:weko3.example.org:00000001",
                                "sets": ["1660555749031"],
                            },
                            "path": ["1660555749031"],
                            "owner": "1",
                            "title": ["2"],
                            "pubdate": {
                                "attribute_name": "PubDate",
                                "attribute_value": "2022-08-18",
                            },
                            "item_title": "2",
                            "author_link": [],
                            "item_type_id": "15",
                            "publish_date": "2022-08-18",
                            "publish_status": "0",
                            "weko_shared_id": -1,
                            "item_1617186331708": {
                                "attribute_name": "Title",
                                "attribute_value_mlt": [
                                    {
                                        "subitem_1551255647225": "2",
                                        "subitem_1551255648112": "ja",
                                    }
                                ],
                            },
                            "item_1617258105262": {
                                "attribute_name": "Resource Type",
                                "attribute_value_mlt": [
                                    {
                                        "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                                        "resourcetype": "conference paper",
                                    }
                                ],
                            },
                            "relation_version_is_last": True,
                            "control_number": "1",
                        },
                        "itemtype": "デフォルトアイテムタイプ（フル）",
                        "publish_date": "2022-08-18",
                        "author_link": [],
                        "weko_shared_id": -1,
                        "weko_creator_id": "1",
                        "relation_version_is_last": True,
                        "path": ["1660555749031"],
                        "publish_status": "0",
                    },
                    "sort": [1660780800000],
                },
            ],
        },
    }
    ret = [
        {
            "record_id": "a64f4db8-b7d7-4cdf-a679-2b0e73f854c4",
            "create_date": "2022-08-20",
            "pid_value": "3",
            "record_name": "ff",
        },
        {
            "record_id": "3cc6099a-4208-4528-80ce-eee7fe4296b7",
            "create_date": "2022-08-18",
            "pid_value": "1",
            "record_name": "2",
        },
    ]
    assert parse_ranking_new_items(results) == ret


# def parse_ranking_record(result_data):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_parse_ranking_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_parse_ranking_record():
    results = {
        "took": 7,
        "timed_out": False,
        "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
        "hits": {
            "total": 2,
            "max_score": None,
            "hits": [
                {
                    "_index": "tenant1-weko-item-v1.0.0",
                    "_type": "item-v1.0.0",
                    "_id": "a64f4db8-b7d7-4cdf-a679-2b0e73f854c4",
                    "_score": None,
                    "_source": {
                        "_created": "2022-08-20T06:05:56.806896+00:00",
                        "_updated": "2022-08-20T06:06:24.602226+00:00",
                        "type": ["conference paper"],
                        "title": ["ff"],
                        "control_number": "3",
                        "_oai": {
                            "id": "oai:weko3.example.org:00000003",
                            "sets": ["1660555749031"],
                        },
                        "_item_metadata": {
                            "_oai": {
                                "id": "oai:weko3.example.org:00000003",
                                "sets": ["1660555749031"],
                            },
                            "path": ["1660555749031"],
                            "owner": "1",
                            "title": ["ff"],
                            "pubdate": {
                                "attribute_name": "PubDate",
                                "attribute_value": "2022-08-20",
                            },
                            "item_title": "ff",
                            "author_link": [],
                            "item_type_id": "15",
                            "publish_date": "2022-08-20",
                            "publish_status": "0",
                            "weko_shared_id": -1,
                            "item_1617186331708": {
                                "attribute_name": "Title",
                                "attribute_value_mlt": [
                                    {
                                        "subitem_1551255647225": "ff",
                                        "subitem_1551255648112": "ja",
                                    }
                                ],
                            },
                            "item_1617258105262": {
                                "attribute_name": "Resource Type",
                                "attribute_value_mlt": [
                                    {
                                        "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                                        "resourcetype": "conference paper",
                                    }
                                ],
                            },
                            "relation_version_is_last": True,
                            "control_number": "3",
                        },
                        "itemtype": "デフォルトアイテムタイプ（フル）",
                        "publish_date": "2022-08-20",
                        "author_link": [],
                        "weko_shared_id": -1,
                        "weko_creator_id": "1",
                        "relation_version_is_last": True,
                        "path": ["1660555749031"],
                        "publish_status": "0",
                    },
                    "sort": [1660953600000],
                },
                {
                    "_index": "tenant1-weko-item-v1.0.0",
                    "_type": "item-v1.0.0",
                    "_id": "3cc6099a-4208-4528-80ce-eee7fe4296b7",
                    "_score": None,
                    "_source": {
                        "_created": "2022-08-17T17:00:43.877778+00:00",
                        "_updated": "2022-08-17T17:01:08.615488+00:00",
                        "type": ["conference paper"],
                        "title": ["2"],
                        "control_number": "1",
                        "_oai": {
                            "id": "oai:weko3.example.org:00000001",
                            "sets": ["1660555749031"],
                        },
                        "_item_metadata": {
                            "_oai": {
                                "id": "oai:weko3.example.org:00000001",
                                "sets": ["1660555749031"],
                            },
                            "path": ["1660555749031"],
                            "owner": "1",
                            "title": ["2"],
                            "pubdate": {
                                "attribute_name": "PubDate",
                                "attribute_value": "2022-08-18",
                            },
                            "item_title": "2",
                            "author_link": [],
                            "item_type_id": "15",
                            "publish_date": "2022-08-18",
                            "publish_status": "0",
                            "weko_shared_id": -1,
                            "item_1617186331708": {
                                "attribute_name": "Title",
                                "attribute_value_mlt": [
                                    {
                                        "subitem_1551255647225": "2",
                                        "subitem_1551255648112": "ja",
                                    }
                                ],
                            },
                            "item_1617258105262": {
                                "attribute_name": "Resource Type",
                                "attribute_value_mlt": [
                                    {
                                        "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                                        "resourcetype": "conference paper",
                                    }
                                ],
                            },
                            "relation_version_is_last": True,
                            "control_number": "1",
                        },
                        "itemtype": "デフォルトアイテムタイプ（フル）",
                        "publish_date": "2022-08-18",
                        "author_link": [],
                        "weko_shared_id": -1,
                        "weko_creator_id": "1",
                        "relation_version_is_last": True,
                        "path": ["1660555749031"],
                        "publish_status": "0",
                    },
                    "sort": [1660780800000],
                },
            ],
        },
    }

    assert parse_ranking_record(results) == ["3", "1"]


# def validate_form_input_data(
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_validate_form_input_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_validate_form_input_data(app, db_itemtype):
    result = {"is_valid": True, "error": ""}
    item_id = 1
    data = {
        "pubdate": "2022-08-22",
        "item_1617186331708": [
            {"subitem_1551255647225": "rrr", "subitem_1551255648112": "ja"}
        ],
        "item_1617186419668": [
            {
                "creatorAffiliations": [
                    {"affiliationNameIdentifiers": [{}], "affiliationNames": [{}]}
                ],
                "creatorAlternatives": [{}],
                "creatorMails": [{}],
                "creatorNames": [{}],
                "familyNames": [{}],
                "givenNames": [{}],
                "nameIdentifiers": [{}],
            }
        ],
        "item_1617186882738": [{"subitem_geolocation_place": [{}]}],
        "item_1617186901218": [
            {"subitem_1522399412622": [{}], "subitem_1522399651758": [{}]}
        ],
        "item_1617187187528": [
            {
                "subitem_1599711633003": [{}],
                "subitem_1599711660052": [{}],
                "subitem_1599711758470": [{}],
                "subitem_1599711788485": [{}],
            }
        ],
        "item_1617349709064": [
            {
                "contributorAffiliations": [
                    {
                        "contributorAffiliationNameIdentifiers": [{}],
                        "contributorAffiliationNames": [{}],
                    }
                ],
                "contributorAlternatives": [{}],
                "contributorMails": [{}],
                "contributorNames": [{}],
                "familyNames": [{}],
                "givenNames": [{}],
                "nameIdentifiers": [{}],
            }
        ],
        "item_1617353299429": [{"subitem_1523320863692": [{}]}],
        "item_1617610673286": [{"nameIdentifiers": [{}], "rightHolderNames": [{}]}],
        "item_1617944105607": [
            {"subitem_1551256015892": [{}], "subitem_1551256037922": [{}]}
        ],
        "item_1661099481373": [
            {
                "version_id": "2f2cb1ba-fb91-4768-8035-582bd24c56ed",
                "filename": "003.jpg",
                "filesize": [{"value": "576 KB"}],
                "format": "image/jpeg",
                "date": [{"dateValue": "2022-08-21", "dateType": "Available"}],
                "accessrole": "open_access",
                "url": {"url": "https://localhost:8443/record/11/files/003.jpg"},
                "displaytype": "preview",
                "licensetype": "license_12",
            }
        ],
        "item_1617187056579": {"bibliographic_titles": [{}]},
        "item_1661099407610": {
            "subitem_thumbnail": [
                {
                    "thumbnail_label": "001.jpg",
                    "thumbnail_url": "/api/files/d8699d40-ee1b-41ad-b719-bacd66be791d/001.jpg?versionId=6869d43e-f4e9-423c-a0a1-83fabe9ec4fe",
                }
            ]
        },
        "item_1617258105262": {
            "resourcetype": "conference paper",
            "resourceuri": "http://purl.org/coar/resource_type/c_5794",
        },
        "shared_user_id": -1,
        "$schema": "/items/jsonschema/1",
    }
    with app.test_request_context():
        validate_form_input_data(result, item_id, data)
        assert result == {"error": "", "is_valid": True}

    result = {"is_valid": True, "error": ""}
    with patch(
        "invenio_records.api.RecordBase.validate",
        side_effect=ValidationError("validation error"),
    ):
        with app.test_request_context():
            validate_form_input_data(result, item_id, data)
            assert result == {"error": "validation error", "is_valid": False}

    result = {"is_valid": True, "error": ""}
    with patch(
        "invenio_records.api.RecordBase.validate",
        side_effect=SchemaError("schema error"),
    ):
        with app.test_request_context():
            validate_form_input_data(result, item_id, data)
            assert result == {
                "error": "Schema Error:<br/><br/>schema error",
                "is_valid": False,
            }

    result = {"is_valid": True, "error": ""}
    with patch(
        "invenio_records.api.RecordBase.validate", side_effect=Exception("exception")
    ):
        with app.test_request_context():
            validate_form_input_data(result, item_id, data)
            assert result == {"error": "exception", "is_valid": False}


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_validate_form_input_data_2 -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_validate_form_input_data_2(app, db_itemtype_15):
    result = {"is_valid": True, "error": ""}
    item_id = 1
    data = {
        "item_1617186331708": [
            {"subitem_1551255647225": "test1", "subitem_1551255648112": "ja"},
            {"subitem_1551255647225": "test2", "subitem_1551255648112": "ja"},
        ],
        "item_1617186419668": [
            {
                "creatorAffiliations": [
                    {
                        "affiliationNameIdentifiers": [{}],
                        "affiliationNames": [
                            {"affiliationName": "test1", "affiliationNameLang": "ja"},
                            {"affiliationName": "test2", "affiliationNameLang": "en"},
                        ],
                    }
                ],
                "creatorAlternatives": [{}],
                "creatorMails": [{}],
                "creatorNames": [
                    {"creatorName": "test1", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "test1", "creatorNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "test1", "familyNameLang": "ja-Latn"},
                    {"familyName": "test2", "familyNameLang": "en"},
                ],
                "givenNames": [
                    {"givenName": "test1", "givenNameLang": "ja"},
                    {"givenName": "test2", "givenNameLang": "en"},
                ],
                "nameIdentifiers": [{}],
            }
        ],
        "item_1617186882738": [{"subitem_geolocation_place": [{}]}],
        "item_1617186901218": [
            {
                "subitem_1522399412622": [
                    {"subitem_1522399416691": "en", "subitem_1522737543681": "test1"},
                    {"subitem_1522399416691": "ja", "subitem_1522737543681": "test2"},
                ],
                "subitem_1522399651758": [
                    {"subitem_1522721910626": "ja", "subitem_1522721929892": "test1"},
                    {"subitem_1522721910626": "en", "subitem_1522721929892": "test2"},
                ],
            }
        ],
        "item_1617186941041": [
            {"subitem_1522650068558": "en", "subitem_1522650091861": "test1"},
            {"subitem_1522650068558": "ja", "subitem_1522650091861": "test2"},
        ],
        "item_1617187056579": {"bibliographic_titles": [{}]},
        "item_1617187112279": [
            {"subitem_1551256126428": "test1", "subitem_1551256129013": "en"},
            {"subitem_1551256126428": "test2", "subitem_1551256129013": "ja"},
        ],
        "item_1617187187528": [
            {
                "subitem_1599711633003": [
                    {
                        "subitem_1599711636923": "conference111",
                        "subitem_1599711645590": "ja",
                    },
                    {
                        "subitem_1599711636923": "conference222",
                        "subitem_1599711645590": "en",
                    },
                ],
                "subitem_1599711660052": [
                    {
                        "subitem_1599711680082": "conference333",
                        "subitem_1599711686511": "ja",
                    },
                    {
                        "subitem_1599711680082": "conference444",
                        "subitem_1599711686511": "en",
                    },
                ],
                "subitem_1599711699392": {
                    "subitem_1599711731891": "9999",
                    "subitem_1599711745532": "en",
                },
                "subitem_1599711758470": [
                    {
                        "subitem_1599711769260": "conference555",
                        "subitem_1599711775943": "en",
                    },
                    {
                        "subitem_1599711769260": "conference666",
                        "subitem_1599711775943": "ja",
                    },
                ],
                "subitem_1599711788485": [
                    {
                        "subitem_1599711798761": "conference777",
                        "subitem_1599711803382": "ja",
                    },
                    {
                        "subitem_1599711798761": "conference888",
                        "subitem_1599711803382": "en",
                    },
                ],
            },
            {
                "subitem_1599711633003": [{}],
                "subitem_1599711660052": [{}],
                "subitem_1599711699392": {
                    "subitem_1599711731891": "8888",
                    "subitem_1599711745532": "ja",
                },
                "subitem_1599711758470": [
                    {"subitem_1599711769260": "tets1", "subitem_1599711775943": "en"},
                    {"subitem_1599711769260": "test2", "subitem_1599711775943": "ja"},
                ],
                "subitem_1599711788485": [
                    {"subitem_1599711798761": "test3", "subitem_1599711803382": "en"},
                    {"subitem_1599711798761": "test4", "subitem_1599711803382": "ja"},
                ],
            },
        ],
        "item_1617258105262": {
            "resourcetype": "conference paper",
            "resourceuri": "http://purl.org/coar/resource_type/c_5794",
        },
        "item_1617349709064": [
            {
                "contributorAffiliations": [
                    {
                        "contributorAffiliationNameIdentifiers": [{}],
                        "contributorAffiliationNames": [
                            {
                                "contributorAffiliationName": "contributor-affiliation-name-test-2",
                                "contributorAffiliationNameLang": "ja",
                            },
                            {
                                "contributorAffiliationName": "test1",
                                "contributorAffiliationNameLang": "en",
                            },
                        ],
                    }
                ],
                "contributorAlternatives": [{}],
                "contributorMails": [{}],
                "contributorNames": [
                    {"contributorName": "contributor-name-test-2", "lang": "ja"},
                    {"contributorName": "test2", "lang": "en"},
                ],
                "familyNames": [
                    {"familyName": "contributor-family-test-2", "familyNameLang": "ja"},
                    {"familyName": "test1", "familyNameLang": "en"},
                ],
                "givenNames": [
                    {"givenName": "contributor-given-test-2", "givenNameLang": "ja"},
                    {"givenName": "test1", "givenNameLang": "en"},
                ],
                "nameIdentifiers": [{}],
            }
        ],
        "item_1617353299429": [
            {
                "subitem_1523320863692": [
                    {"subitem_1523320867455": "en", "subitem_1523320909613": "test1"},
                    {"subitem_1523320867455": "ja", "subitem_1523320909613": "test2"},
                ]
            }
        ],
        "item_1617605131499": [{"date": [{}], "fileDate": [{}], "filesize": [{}]}],
        "item_1617610673286": [{"nameIdentifiers": [{}], "rightHolderNames": [{}]}],
        "item_1617944105607": [
            {
                "subitem_1551256015892": [{}],
                "subitem_1551256037922": [
                    {"subitem_1551256042287": "test1", "subitem_1551256047619": "en"},
                    {"subitem_1551256042287": "test2", "subitem_1551256047619": "ja"},
                ],
            }
        ],
        "pubdate": "2023-06-27",
        "shared_user_id": -1,
        "$schema": "/items/jsonschema/15",
    }

    with app.test_request_context():
        # TITLE TEST
        result_for_title_use = {"is_valid": True, "error": ""}
        data_for_title_use = {
            "item_1617186331708": [
                {"subitem_1551255647225": "test1", "subitem_1551255648112": "ja"},
                {"subitem_1551255647225": "test2", "subitem_1551255648112": "en"},
            ],
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            },
            "pubdate": "2023-06-27",
            "shared_user_id": -1,
            "$schema": "/items/jsonschema/15",
        }
        validate_form_input_data(result_for_title_use, item_id, data_for_title_use)
        assert result_for_title_use["is_valid"] == True

        # TITLE TESTS
        data_for_title_use_copy = copy.deepcopy(data_for_title_use)
        data_for_title_use_copy["item_1617186331708"][0]["subitem_1551255648112"] = "en"
        validate_form_input_data(result_for_title_use, item_id, data_for_title_use_copy)
        if result_for_title_use["error"]:
            assert "duplicate" in result_for_title_use["error"]
            assert "Title" in result_for_title_use["error"]

        data_for_title_use_copy["item_1617186331708"][0]["subitem_1551255648112"] = "ja-Kana"
        validate_form_input_data(result_for_title_use, item_id, data_for_title_use_copy)
        if result_for_title_use["error"]:
            assert "ja-Kana" in result_for_title_use["error"]
            assert "Title" in result_for_title_use["error"]

        data_for_title_use_copy["item_1617186331708"][0]["subitem_1551255648112"] = "ja-Latn"
        validate_form_input_data(result_for_title_use, item_id, data_for_title_use_copy)
        if result_for_title_use["error"]:
            assert "ja-Latn" in result_for_title_use["error"]
            assert "Title" in result_for_title_use["error"]

        # ALTERNATIVE TITLE TEST
        result_for_alternative_title_use = {"is_valid": True, "error": ""}
        data_for_alternative_title_use = {
            "item_1617186331708": [
                {"subitem_1551255647225": "test1", "subitem_1551255648112": "ja"},
                {"subitem_1551255647225": "test2", "subitem_1551255648112": "en"},
            ],
            "item_1617186385884": [
                {"subitem_1551255720400": "test1", "subitem_1551255721061": "ja"},
                {"subitem_1551255720400": "test2", "subitem_1551255721061": "en"},
            ],
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            },
            "pubdate": "2023-06-27",
            "shared_user_id": -1,
            "$schema": "/items/jsonschema/15",
        }
        validate_form_input_data(result_for_alternative_title_use, item_id, data_for_alternative_title_use)
        assert result_for_alternative_title_use["is_valid"] == True

        data_for_alternative_title_use_copy = copy.deepcopy(data_for_alternative_title_use)
        data_for_alternative_title_use_copy["item_1617186385884"][0]["subitem_1551255721061"] = "ja-Kana"
        validate_form_input_data(result_for_alternative_title_use, item_id, data_for_alternative_title_use_copy)
        if result_for_alternative_title_use["error"]:
            assert "ja-Kana" in result_for_alternative_title_use["error"]
            assert "Alternative Title" in result_for_alternative_title_use["error"]

        data_for_alternative_title_use_copy["item_1617186385884"][0]["subitem_1551255721061"] = "ja-Latn"
        validate_form_input_data(result_for_alternative_title_use, item_id, data_for_alternative_title_use_copy)
        if result_for_alternative_title_use["error"]:
            assert "ja-Latn" in result_for_alternative_title_use["error"]
            assert "Alternative Title" in result_for_alternative_title_use["error"]

        # CREATOR TEST
        result_for_creator_use = {"is_valid": True, "error": ""}
        data_for_creator_use = {
            "item_1617186331708": [
                {"subitem_1551255647225": "test1", "subitem_1551255648112": "ja"},
                {"subitem_1551255647225": "test2", "subitem_1551255648112": "en"},
            ],
            "item_1617186419668": [
                {
                    "creatorAffiliations": [
                        {
                            "affiliationNameIdentifiers": [{}],
                            "affiliationNames": [
                                {"affiliationName": "test1", "affiliationNameLang": "ja"},
                                {"affiliationName": "test2", "affiliationNameLang": "en"},
                            ],
                        }
                    ],
                    "creatorAlternatives": [{}],
                    "creatorMails": [{}],
                    "creatorNames": [
                        {"creatorName": "test1", "creatorNameLang": "ja"},
                        {"creatorName": "test1", "creatorNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "test1", "familyNameLang": "ja"},
                        {"familyName": "test2", "familyNameLang": "en"},
                    ],
                    "givenNames": [
                        {"givenName": "test1", "givenNameLang": "ja"},
                        {"givenName": "test2", "givenNameLang": "en"},
                    ],
                    "nameIdentifiers": [{}],
                }
            ],
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            },
            "pubdate": "2023-06-27",
            "shared_user_id": -1,
            "$schema": "/items/jsonschema/15",
        }
        validate_form_input_data(result_for_creator_use, item_id, data_for_creator_use)
        assert result_for_creator_use["is_valid"] == True

        # CREATOR GIVEN NAME TESTS
        data_for_creator_given_name_use_copy = copy.deepcopy(data_for_creator_use)
        data_for_creator_given_name_use_copy["item_1617186419668"][0]["givenNames"][0]["givenNameLang"] = "en"
        validate_form_input_data(result_for_creator_use, item_id, data_for_creator_given_name_use_copy)
        if result_for_creator_use["error"]:
            assert "duplicate" in result_for_creator_use["error"]
            assert "Creator Given Name" in result_for_creator_use["error"]

        data_for_creator_given_name_use_copy["item_1617186419668"][0]["givenNames"][0]["givenNameLang"] = "ja-Kana"
        validate_form_input_data(result_for_creator_use, item_id, data_for_creator_given_name_use_copy)
        if result_for_creator_use["error"]:
            assert "ja-Kana" in result_for_creator_use["error"]
            assert "Creator Given Name" in result_for_creator_use["error"]

        data_for_creator_given_name_use_copy["item_1617186419668"][0]["givenNames"][0]["givenNameLang"] = "ja-Latn"
        validate_form_input_data(result_for_creator_use, item_id, data_for_creator_given_name_use_copy)
        if result_for_creator_use["error"]:
            assert "ja-Latn" in result_for_creator_use["error"]
            assert "Creator Given Name" in result_for_creator_use["error"]

        # CREATOR FAMILY NAME TESTS
        data_for_creator_family_name_use_copy = copy.deepcopy(data_for_creator_use)
        data_for_creator_family_name_use_copy["item_1617186419668"][0]["familyNames"][0]["familyNameLang"] = "en"
        validate_form_input_data(result_for_creator_use, item_id, data_for_creator_family_name_use_copy)
        if result_for_creator_use["error"]:
            assert "duplicate" in result_for_creator_use["error"]
            assert "Creator Family Name" in result_for_creator_use["error"]

        data_for_creator_family_name_use_copy["item_1617186419668"][0]["familyNames"][0]["familyNameLang"] = "ja-Kana"
        validate_form_input_data(result_for_creator_use, item_id, data_for_creator_family_name_use_copy)
        if result_for_creator_use["error"]:
            assert "ja-Kana" in result_for_creator_use["error"]
            assert "Creator Family Name" in result_for_creator_use["error"]

        data_for_creator_family_name_use_copy["item_1617186419668"][0]["familyNames"][0]["familyNameLang"] = "ja-Latn"
        validate_form_input_data(result_for_creator_use, item_id, data_for_creator_family_name_use_copy)
        if result_for_creator_use["error"]:
            assert "ja-Latn" in result_for_creator_use["error"]
            assert "Creator Family Name" in result_for_creator_use["error"]

         # CREATOR AFFILIATION NAME TESTS
        data_for_creator_affiliation_name_use_copy = copy.deepcopy(data_for_creator_use)
        data_for_creator_affiliation_name_use_copy["item_1617186419668"][0]["creatorAffiliations"][0]["affiliationNames"][0]["affiliationNameLang"] = "en"
        validate_form_input_data(result_for_creator_use, item_id, data_for_creator_affiliation_name_use_copy)
        if result_for_creator_use["error"]:
            assert "duplicate" in result_for_creator_use["error"]
            assert "Creator Affiliation Name" in result_for_creator_use["error"]

         # CREATOR NAME TESTS
        data_for_creator_name_use_copy = copy.deepcopy(data_for_creator_use)
        data_for_creator_name_use_copy["item_1617186419668"][0]["creatorNames"][0]["creatorNameLang"] = "en"
        validate_form_input_data(result_for_creator_use, item_id, data_for_creator_name_use_copy)
        if result_for_creator_use["error"]:
            assert "duplicate" in result_for_creator_use["error"]
            assert "Creator Name" in result_for_creator_use["error"]

        data_for_creator_name_use_copy["item_1617186419668"][0]["creatorNames"][0]["creatorNameLang"] = "ja-Kana"
        validate_form_input_data(result_for_creator_use, item_id, data_for_creator_name_use_copy)
        if result_for_creator_use["error"]:
            assert "ja-Kana" in result_for_creator_use["error"]
            assert "Creator Name" in result_for_creator_use["error"]

        data_for_creator_name_use_copy["item_1617186419668"][0]["creatorNames"][0]["creatorNameLang"] = "ja-Latn"
        validate_form_input_data(result_for_creator_use, item_id, data_for_creator_name_use_copy)
        if result_for_creator_use["error"]:
            assert "ja-Latn" in result_for_creator_use["error"]
            assert "Creator Name" in result_for_creator_use["error"]

        # CREATOR ALTERNATIVE NAME TESTS
        data_for_creator_alternative_name_use_copy = copy.deepcopy(data_for_creator_use)
        data_for_creator_alternative_name_use_copy["item_1617186419668"][0]["creatorAlternatives"][0]["creatorAlternativeLang"] = "ja-Kana"
        validate_form_input_data(result_for_creator_use, item_id, data_for_creator_alternative_name_use_copy)
        if result_for_creator_use["error"]:
            assert "ja-Kana" in result_for_creator_use["error"]
            assert "Creator Name" in result_for_creator_use["error"]

        data_for_creator_alternative_name_use_copy["item_1617186419668"][0]["creatorAlternatives"][0]["creatorAlternativeLang"] = "ja-Latn"
        validate_form_input_data(result_for_creator_use, item_id, data_for_creator_alternative_name_use_copy)
        if result_for_creator_use["error"]:
            assert "ja-Latn" in result_for_creator_use["error"]
            assert "Creator Name" in result_for_creator_use["error"]

        # CONTRIBUTOR TEST
        result_for_contributor_use = {"is_valid": True, "error": ""}
        data_for_contributor_use = {
            "item_1617186331708": [
                {"subitem_1551255647225": "test1", "subitem_1551255648112": "ja"},
                {"subitem_1551255647225": "test2", "subitem_1551255648112": "en"},
            ],
            "item_1617349709064": [
                {
                    "contributorAffiliations": [
                        {
                            "contributorAffiliationNameIdentifiers": [{}],
                            "contributorAffiliationNames": [
                                {
                                    "contributorAffiliationName": "test1",
                                    "contributorAffiliationNameLang": "ja",
                                },
                                {
                                    "contributorAffiliationName": "test2",
                                    "contributorAffiliationNameLang": "en",
                                },
                            ],
                        }
                    ],
                    "contributorAlternatives": [
                        {"contributorAlternative": "test1", "contributorAlternativeLang": "ja"},
                        {"contributorAlternative": "test2", "contributorAlternativeLang": "en"},
                    ],
                    "contributorMails": [{}],
                    "contributorNames": [
                        {"contributorName": "test1", "lang": "ja"},
                        {"contributorName": "test2", "lang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "test1", "familyNameLang": "ja"},
                        {"familyName": "test2", "familyNameLang": "en"},
                    ],
                    "givenNames": [
                        {"givenName": "test1", "givenNameLang": "ja"},
                        {"givenName": "test2", "givenNameLang": "en"},
                    ],
                    "nameIdentifiers": [{}],
                }
            ],
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            },
            "pubdate": "2023-06-27",
            "shared_user_id": -1,
            "$schema": "/items/jsonschema/15",
        }
        validate_form_input_data(result_for_contributor_use, item_id, data_for_contributor_use)
        assert result_for_contributor_use["is_valid"] == True

        # CONTRIBUTOR GIVEN NAME TESTS
        data_for_contributor_given_name_use_copy = copy.deepcopy(data_for_contributor_use)
        data_for_contributor_given_name_use_copy["item_1617349709064"][0]["givenNames"][0]["givenNameLang"] = "en"
        validate_form_input_data(result_for_contributor_use, item_id, data_for_contributor_given_name_use_copy)
        if result_for_contributor_use["error"]:
            assert "duplicate" in result_for_contributor_use["error"]
            assert "Contributor Given Name" in result_for_contributor_use["error"]

        data_for_contributor_given_name_use_copy["item_1617349709064"][0]["givenNames"][0]["givenNameLang"] = "ja-Kana"
        validate_form_input_data(result_for_contributor_use, item_id, data_for_contributor_given_name_use_copy)
        if result_for_contributor_use["error"]:
            assert "ja-Kana" in result_for_contributor_use["error"]
            assert "Contributor Given Name" in result_for_contributor_use["error"]

        data_for_contributor_given_name_use_copy["item_1617349709064"][0]["givenNames"][0]["givenNameLang"] = "ja-Latn"
        validate_form_input_data(result_for_contributor_use, item_id, data_for_contributor_given_name_use_copy)
        if result_for_contributor_use["error"]:
            assert "ja-Latn" in result_for_contributor_use["error"]
            assert "Contributor Given Name" in result_for_contributor_use["error"]

        # # CONTRIBUTOR FAMILY NAME TESTS
        data_for_contributor_family_name_use_copy = copy.deepcopy(data_for_contributor_use)
        data_for_contributor_family_name_use_copy["item_1617349709064"][0]["familyNames"][0]["familyNameLang"] = "en"
        validate_form_input_data(result_for_contributor_use, item_id, data_for_contributor_family_name_use_copy)
        if result_for_contributor_use["error"]:
            assert "duplicate" in result_for_contributor_use["error"]
            assert "Contributor Family Name" in result_for_contributor_use["error"]

        data_for_contributor_family_name_use_copy["item_1617349709064"][0]["familyNames"][0]["familyNameLang"] = "ja-Kana"
        validate_form_input_data(result_for_contributor_use, item_id, data_for_contributor_family_name_use_copy)
        if result_for_contributor_use["error"]:
            assert "ja-Kana" in result_for_contributor_use["error"]
            assert "Contributor Family Name" in result_for_contributor_use["error"]

        data_for_contributor_family_name_use_copy["item_1617349709064"][0]["familyNames"][0]["familyNameLang"] = "ja-Latn"
        validate_form_input_data(result_for_contributor_use, item_id, data_for_contributor_family_name_use_copy)
        if result_for_contributor_use["error"]:
            assert "ja-Latn" in result_for_contributor_use["error"]
            assert "Contributor Family Name" in result_for_contributor_use["error"]

        #  # CONTRIBUTOR AFFILIATION NAME TESTS
        data_for_contributor_affiliation_name_use_copy = copy.deepcopy(data_for_contributor_use)
        data_for_contributor_affiliation_name_use_copy["item_1617349709064"][0]["contributorAffiliations"][0]["contributorAffiliationNames"][0]["contributorAffiliationNameLang"] = "en"
        validate_form_input_data(result_for_contributor_use, item_id, data_for_contributor_affiliation_name_use_copy)
        if result_for_contributor_use["error"]:
            assert "duplicate" in result_for_contributor_use["error"]
            assert "Contributor Affiliation Name" in result_for_contributor_use["error"]

         # CONTRIBUTOR NAME TESTS
        data_for_contributor_name_use_copy = copy.deepcopy(data_for_contributor_use)
        data_for_contributor_name_use_copy["item_1617349709064"][0]["contributorNames"][0]["lang"] = "en"
        validate_form_input_data(result_for_contributor_use, item_id, data_for_contributor_name_use_copy)
        if result_for_contributor_use["error"]:
            assert "duplicate" in result_for_contributor_use["error"]
            assert "Contributor Name" in result_for_contributor_use["error"]

        data_for_contributor_name_use_copy["item_1617349709064"][0]["contributorNames"][0]["lang"] = "ja-Kana"
        validate_form_input_data(result_for_contributor_use, item_id, data_for_contributor_name_use_copy)
        if result_for_contributor_use["error"]:
            assert "ja-Kana" in result_for_contributor_use["error"]
            assert "Contributor Name" in result_for_contributor_use["error"]

        data_for_contributor_name_use_copy["item_1617349709064"][0]["contributorNames"][0]["lang"] = "ja-Latn"
        validate_form_input_data(result_for_contributor_use, item_id, data_for_contributor_name_use_copy)
        if result_for_contributor_use["error"]:
            assert "ja-Latn" in result_for_contributor_use["error"]
            assert "Contributor Name" in result_for_contributor_use["error"]

        # CONTRIBUTOR ALTERNATIVE NAME TESTS
        data_for_contributor_alternative_name_use_copy = copy.deepcopy(data_for_contributor_use)
        data_for_contributor_alternative_name_use_copy["item_1617349709064"][0]["contributorAlternatives"][0]["contributorAlternativeLang"] = "ja-Kana"
        validate_form_input_data(result_for_contributor_use, item_id, data_for_contributor_alternative_name_use_copy)
        if result_for_contributor_use["error"]:
            assert "ja-Kana" in result_for_contributor_use["error"]
            assert "Contributor Alternative Name" in result_for_contributor_use["error"]

        data_for_contributor_alternative_name_use_copy["item_1617349709064"][0]["contributorAlternatives"][0]["contributorAlternativeLang"] = "ja-Latn"
        validate_form_input_data(result_for_contributor_use, item_id, data_for_contributor_alternative_name_use_copy)
        if result_for_contributor_use["error"]:
            assert "ja-Latn" in result_for_contributor_use["error"]
            assert "Contributor Alternative Name" in result_for_contributor_use["error"]

        # RELATION TEST
        result_for_relation_use = {"is_valid": True, "error": ""}
        data_for_relation_use = {
            "item_1617186331708": [
                {"subitem_1551255647225": "test1", "subitem_1551255648112": "ja"},
                {"subitem_1551255647225": "test2", "subitem_1551255648112": "en"},
            ],
            "item_1617353299429": [
                {
                    "subitem_1523320863692": [
                        {"subitem_1523320867455": "ja", "subitem_1523320909613": "test1"},
                        {"subitem_1523320867455": "en", "subitem_1523320909613": "test2"},
                    ]
                }
            ],
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            },
            "pubdate": "2023-06-27",
            "shared_user_id": -1,
            "$schema": "/items/jsonschema/15",
        }
        validate_form_input_data(result_for_relation_use, item_id, data_for_relation_use)
        assert result_for_relation_use["is_valid"] == True

        # RELATION RELATED TITLE TEST
        data_for_related_title_use_copy = copy.deepcopy(data_for_relation_use)
        data_for_related_title_use_copy["item_1617353299429"][0]["subitem_1523320863692"][0]["subitem_1523320867455"] = "en"
        validate_form_input_data(result_for_relation_use, item_id, data_for_related_title_use_copy)
        if result_for_relation_use["error"]:
            assert "duplicate" in result_for_relation_use["error"]
            assert "Relation Related Title" in result_for_relation_use["error"]

        # FUNDING REFERENCE TESTS
        result_for_funding_reference_use = {"is_valid": True, "error": ""}
        data_for_funding_reference_use = {
            "item_1617186331708": [
                {"subitem_1551255647225": "test1", "subitem_1551255648112": "ja"},
                {"subitem_1551255647225": "test2", "subitem_1551255648112": "en"},
            ],
            "item_1617186901218": [
                {
                    "subitem_1522399412622": [
                        {"subitem_1522399416691": "ja", "subitem_1522737543681": "test1"},
                        {"subitem_1522399416691": "en", "subitem_1522737543681": "test2"},
                    ],
                    "subitem_1522399651758": [
                        {"subitem_1522721910626": "ja", "subitem_1522721929892": "test1"},
                        {"subitem_1522721910626": "en", "subitem_1522721929892": "test2"},
                    ],
                }
            ],
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            },
            "pubdate": "2023-06-27",
            "shared_user_id": -1,
            "$schema": "/items/jsonschema/15",
        }
        validate_form_input_data(result_for_funding_reference_use, item_id, data_for_funding_reference_use)
        assert result_for_funding_reference_use["is_valid"] == True

        # FUNDING REFERENCE FUNDER NAME TEST
        data_for_funding_reference_funder_name_use_copy = copy.deepcopy(data_for_funding_reference_use)
        data_for_funding_reference_funder_name_use_copy["item_1617186901218"][0]["subitem_1522399412622"][0]["subitem_1522399416691"] = "en"
        validate_form_input_data(result_for_funding_reference_use, item_id, data_for_funding_reference_funder_name_use_copy)
        if result_for_funding_reference_use["error"]:
            assert "duplicate" in result_for_funding_reference_use["error"]
            assert "Funding Reference Funder Name" in result_for_funding_reference_use["error"]

        # FUNDING REFERENCE AWARD TITLE TEST
        data_for_funding_reference_award_title_use_copy = copy.deepcopy(data_for_funding_reference_use)
        data_for_funding_reference_award_title_use_copy["item_1617186901218"][0]["subitem_1522399651758"][0]["subitem_1522721910626"] = "en"
        validate_form_input_data(result_for_funding_reference_use, item_id, data_for_funding_reference_award_title_use_copy)
        if result_for_funding_reference_use["error"]:
            assert "duplicate" in result_for_funding_reference_use["error"]
            assert "Funding Reference Award Title" in result_for_funding_reference_use["error"]

        # SOURCE TITLE TEST
        result_for_source_title_use = {"is_valid": True, "error": ""}
        data_for_source_title_use = {
            "item_1617186331708": [
                {"subitem_1551255647225": "test1", "subitem_1551255648112": "ja"},
                {"subitem_1551255647225": "test2", "subitem_1551255648112": "en"},
            ],
            "item_1617186941041": [
                {"subitem_1522650068558": "ja", "subitem_1522650091861": "test1"},
                {"subitem_1522650068558": "en", "subitem_1522650091861": "test2"},
            ],
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            },
            "pubdate": "2023-06-27",
            "shared_user_id": -1,
            "$schema": "/items/jsonschema/15",
        }
        validate_form_input_data(result_for_source_title_use, item_id, data_for_source_title_use)
        assert result_for_source_title_use["is_valid"] == True

        data_for_source_title_use_copy = copy.deepcopy(data_for_source_title_use)
        data_for_source_title_use_copy["item_1617186941041"][0]["subitem_1522650068558"] = "en"
        validate_form_input_data(result_for_source_title_use, item_id, data_for_source_title_use_copy)
        if result_for_source_title_use["error"]:
            assert "duplicate" in result_for_source_title_use["error"]
            assert "Source Title" in result_for_source_title_use["error"]

        # DEGREE NAME TEST
        result_for_degree_name_use = {"is_valid": True, "error": ""}
        data_for_degree_name_use = {
            "item_1617186331708": [
                {"subitem_1551255647225": "test1", "subitem_1551255648112": "ja"},
                {"subitem_1551255647225": "test2", "subitem_1551255648112": "en"},
            ],
            "item_1617187112279": [
                {"subitem_1551256126428": "test1", "subitem_1551256129013": "ja"},
                {"subitem_1551256126428": "test2", "subitem_1551256129013": "en"},
            ],
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            },
            "pubdate": "2023-06-27",
            "shared_user_id": -1,
            "$schema": "/items/jsonschema/15",
        }
        validate_form_input_data(result_for_degree_name_use, item_id, data_for_degree_name_use)
        assert result_for_degree_name_use["is_valid"] == True

        data_for_degree_name_use_copy = copy.deepcopy(data_for_degree_name_use)
        data_for_degree_name_use_copy["item_1617187112279"][0]["subitem_1551256129013"] = "en"
        validate_form_input_data(result_for_degree_name_use, item_id, data_for_degree_name_use_copy)
        if result_for_degree_name_use["error"]:
            assert "duplicate" in result_for_degree_name_use["error"]
            assert "Degree Name" in result_for_degree_name_use["error"]

        # DEGREE GRANTOR NAME TEST
        result_for_degree_grantor_use = {"is_valid": True, "error": ""}
        data_for_degree_grantor_use = {
            "item_1617186331708": [
                {"subitem_1551255647225": "test1", "subitem_1551255648112": "ja"},
                {"subitem_1551255647225": "test2", "subitem_1551255648112": "en"},
            ],
            "item_1617944105607": [
                {
                    "subitem_1551256015892": [{}],
                    "subitem_1551256037922": [
                        {"subitem_1551256042287": "test1", "subitem_1551256047619": "ja"},
                        {"subitem_1551256042287": "test2", "subitem_1551256047619": "en"},
                    ],
                }
            ],
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            },
            "pubdate": "2023-06-27",
            "shared_user_id": -1,
            "$schema": "/items/jsonschema/15",
        }
        validate_form_input_data(result_for_degree_grantor_use, item_id, data_for_degree_grantor_use)
        assert result_for_degree_grantor_use["is_valid"] == True

        data_for_degree_grantor_name_use_copy = copy.deepcopy(data_for_degree_grantor_use)
        data_for_degree_grantor_name_use_copy["item_1617944105607"][0]["subitem_1551256037922"][0]["subitem_1551256047619"] = "en"
        validate_form_input_data(result_for_degree_grantor_use, item_id, data_for_degree_grantor_name_use_copy)
        if result_for_degree_grantor_use["error"]:
            assert "duplicate" in result_for_degree_grantor_use["error"]
            assert "Degree Grantor Name" in result_for_degree_grantor_use["error"]

        # CONFERENCE TEST
        result_for_conference_use = {"is_valid": True, "error": ""}
        data_for_conference_use = {
            "item_1617186331708": [
                {"subitem_1551255647225": "test1", "subitem_1551255648112": "ja"},
                {"subitem_1551255647225": "test2", "subitem_1551255648112": "en"},
            ],
            "item_1617187187528": [
                {
                    "subitem_1599711633003": [
                        {
                            "subitem_1599711636923": "conference111",
                            "subitem_1599711645590": "ja",
                        },
                        {
                            "subitem_1599711636923": "conference222",
                            "subitem_1599711645590": "en",
                        },
                    ],
                    "subitem_1599711660052": [
                        {
                            "subitem_1599711680082": "conference333",
                            "subitem_1599711686511": "ja",
                        },
                        {
                            "subitem_1599711680082": "conference444",
                            "subitem_1599711686511": "en",
                        },
                    ],
                    "subitem_1599711699392": {
                        "subitem_1599711731891": "9999",
                        "subitem_1599711745532": "ja",
                    },
                    "subitem_1599711758470": [
                        {
                            "subitem_1599711769260": "conference555",
                            "subitem_1599711775943": "en",
                        },
                        {
                            "subitem_1599711769260": "conference666",
                            "subitem_1599711775943": "ja",
                        },
                    ],
                    "subitem_1599711788485": [
                        {
                            "subitem_1599711798761": "conference777",
                            "subitem_1599711803382": "ja",
                        },
                        {
                            "subitem_1599711798761": "conference888",
                            "subitem_1599711803382": "en",
                        },
                    ],
                },
                {
                    "subitem_1599711633003": [{}],
                    "subitem_1599711660052": [{}],
                    "subitem_1599711699392": {
                        "subitem_1599711731891": "8888",
                        "subitem_1599711745532": "en",
                    },
                    "subitem_1599711758470": [
                        {"subitem_1599711769260": "tets1", "subitem_1599711775943": "ja"},
                        {"subitem_1599711769260": "test2", "subitem_1599711775943": "en"},
                    ],
                    "subitem_1599711788485": [
                        {"subitem_1599711798761": "test3", "subitem_1599711803382": "en"},
                        {"subitem_1599711798761": "test4", "subitem_1599711803382": "ja"},
                    ],
                },
            ],
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            },
            "pubdate": "2023-06-27",
            "shared_user_id": -1,
            "$schema": "/items/jsonschema/15",
        }
        validate_form_input_data(result_for_conference_use, item_id, data_for_conference_use)
        assert result_for_conference_use["is_valid"] == True

        # CONFERENCE NAME TESTS
        data_for_conference_name_use_copy = copy.deepcopy(data_for_conference_use)
        data_for_conference_name_use_copy["item_1617187187528"][0]["subitem_1599711633003"][0]["subitem_1599711645590"] = "en"
        validate_form_input_data(result_for_conference_use, item_id, data_for_conference_name_use_copy)
        if result_for_conference_use["error"]:
            assert "duplicate" in result_for_conference_use["error"]
            assert "Conference Name" in result_for_conference_use["error"]

        # CONFERENCE PLACE TESTS
        data_for_conference_place_use_copy = copy.deepcopy(data_for_conference_use)
        data_for_conference_place_use_copy["item_1617187187528"][0]["subitem_1599711788485"][0]["subitem_1599711803382"] = "en"
        validate_form_input_data(result_for_conference_use, item_id, data_for_conference_place_use_copy)
        if result_for_conference_use["error"]:
            assert "duplicate" in result_for_conference_use["error"]
            assert "Conference Place" in result_for_conference_use["error"]

        # CONFERENCE VENUE TESTS
        data_for_conference_venue_use_copy = copy.deepcopy(data_for_conference_use)
        data_for_conference_venue_use_copy["item_1617187187528"][0]["subitem_1599711758470"][0]["subitem_1599711775943"] = "en"
        validate_form_input_data(result_for_conference_use, item_id, data_for_conference_venue_use_copy)
        if result_for_conference_use["error"]:
            assert "duplicate" in result_for_conference_use["error"]
            assert "Conference Venue" in result_for_conference_use["error"]

        # CONFERENCE SPONSOR TESTS
        data_for_conference_sponsor_use_copy = copy.deepcopy(data_for_conference_use)
        data_for_conference_sponsor_use_copy["item_1617187187528"][0]["subitem_1599711660052"][0]["subitem_1599711686511"] = "en"
        validate_form_input_data(result_for_conference_use, item_id, data_for_conference_sponsor_use_copy)
        if result_for_conference_use["error"]:
            assert "duplicate" in result_for_conference_use["error"]
            assert "Conference Sponsor" in result_for_conference_use["error"]

        # CONFERENCE DATE TESTS
        data_for_conference_date_use_copy = copy.deepcopy(data_for_conference_use)
        data_for_conference_date_use_copy["item_1617187187528"][0]["subitem_1599711699392"]["subitem_1599711745532"] = "en"
        validate_form_input_data(result_for_conference_use, item_id, data_for_conference_date_use_copy)
        if result_for_conference_use["error"]:
            assert "duplicate" in result_for_conference_use["error"]
            assert "Conference Date" in result_for_conference_use["error"]

        # For covering all conditions
        validate_form_input_data(result, item_id, data)
        assert result["is_valid"] == False

        with patch("invenio_records.api.RecordBase.validate", side_effect=ValidationError("required")):
            validate_form_input_data(result, item_id, data)

        with patch("invenio_records.api.RecordBase.validate", side_effect=ValidationError("pattern")):
            validate_form_input_data(result, item_id, data)

        with patch("invenio_records.api.RecordBase.validate", side_effect=SchemaError("Schema error")):
            validate_form_input_data(result, item_id, data)

        with patch("invenio_records.api.RecordBase.validate", side_effect=Exception):
            validate_form_input_data(result, item_id, data)


# def parse_node_str_to_json_schema(node_str: str):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_parse_node_str_to_json_schema -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_parse_node_str_to_json_schema():
    assert parse_node_str_to_json_schema("item.subitem.subsubitem") == {
        "item": "item",
        "child": {"item": "subitem", "child": {"item": "subsubitem"}},
    }


# def update_json_schema_with_required_items(node: dict, json_data: dict):
#     :param node: json schema return from def parse_node_str_to_json_schema
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_update_json_schema_with_required_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_update_json_schema_with_required_items(app):
    node = {
        "item": "item_1617186419668",
        "child": {"item": "givenNames", "child": {"item": "givenName"}},
    }
    json_data = {
        "type": "object",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "required": ["pubdate", "item_1617186331708", "item_1617258105262"],
        "properties": {
            "pubdate": {"type": "string", "title": "PubDate", "format": "datetime"},
            "system_file": {
                "type": "object",
                "title": "File Information",
                "format": "object",
                "properties": {
                    "subitem_systemfile_size": {
                        "type": "string",
                        "title": "SYSTEMFILE Size",
                        "format": "text",
                    },
                    "subitem_systemfile_version": {
                        "type": "string",
                        "title": "SYSTEMFILE Version",
                        "format": "text",
                    },
                    "subitem_systemfile_datetime": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "format": "object",
                            "properties": {
                                "subitem_systemfile_datetime_date": {
                                    "type": "string",
                                    "title": "SYSTEMFILE DateTime Date",
                                    "format": "datetime",
                                },
                                "subitem_systemfile_datetime_type": {
                                    "enum": [
                                        "Accepted",
                                        "Available",
                                        "Collected",
                                        "Copyrighted",
                                        "Created",
                                        "Issued",
                                        "Submitted",
                                        "Updated",
                                        "Valid",
                                    ],
                                    "type": "string",
                                    "title": "SYSTEMFILE DateTime Type",
                                    "format": "select",
                                },
                            },
                        },
                        "title": "SYSTEMFILE DateTime",
                        "format": "array",
                    },
                    "subitem_systemfile_filename": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "format": "object",
                            "properties": {
                                "subitem_systemfile_filename_uri": {
                                    "type": "string",
                                    "title": "SYSTEMFILE Filename URI",
                                    "format": "text",
                                },
                                "subitem_systemfile_filename_type": {
                                    "enum": [
                                        "Abstract",
                                        "Fulltext",
                                        "Summary",
                                        "Thumbnail",
                                        "Other",
                                    ],
                                    "type": "string",
                                    "title": "SYSTEMFILE Filename Type",
                                    "format": "select",
                                },
                                "subitem_systemfile_filename_label": {
                                    "type": "string",
                                    "title": "SYSTEMFILE Filename Label",
                                    "format": "text",
                                },
                            },
                        },
                        "title": "SYSTEMFILE Filename",
                        "format": "array",
                    },
                    "subitem_systemfile_mimetype": {
                        "type": "string",
                        "title": "SYSTEMFILE MimeType",
                        "format": "text",
                    },
                },
                "system_prop": True,
            },
            "item_1617186331708": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["subitem_1551255647225", "subitem_1551255648112"],
                    "properties": {
                        "subitem_1551255647225": {
                            "type": "string",
                            "title": "Title",
                            "format": "text",
                            "title_i18n": {"en": "Title", "ja": "タイトル"},
                            "title_i18n_temp": {"en": "Title", "ja": "タイトル"},
                        },
                        "subitem_1551255648112": {
                            "enum": [
                                None,
                                "ja",
                                "ja-Kana",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                            "type": ["null", "string"],
                            "title": "Language",
                            "format": "select",
                            "currentEnum": [
                                "ja",
                                "ja-Kana",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                        },
                    },
                },
                "title": "Title",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617186385884": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_1551255720400": {
                            "type": "string",
                            "title": "Alternative Title",
                            "format": "text",
                            "title_i18n": {"en": "Alternative Title", "ja": "その他のタイトル"},
                            "title_i18n_temp": {
                                "en": "Alternative Title",
                                "ja": "その他のタイトル",
                            },
                        },
                        "subitem_1551255721061": {
                            "enum": [
                                None,
                                "ja",
                                "ja-Kana",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                            "type": ["null", "string"],
                            "title": "Language",
                            "format": "select",
                            "currentEnum": [
                                "ja",
                                "ja-Kana",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                        },
                    },
                },
                "title": "Alternative Title",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617186419668": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "iscreator": {
                            "type": "string",
                            "title": "iscreator",
                            "format": "text",
                            "uniqueKey": "item_1617186419668_iscreator",
                            "title_i18n": {"en": "", "ja": ""},
                        },
                        "givenNames": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "givenName": {
                                        "type": "string",
                                        "title": "名",
                                        "format": "text",
                                        "title_i18n": {"en": "Given Name", "ja": "名"},
                                        "title_i18n_temp": {
                                            "en": "Given Name",
                                            "ja": "名",
                                        },
                                    },
                                    "givenNameLang": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "言語",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                },
                            },
                            "title": "作成者名",
                            "format": "array",
                        },
                        "familyNames": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "familyName": {
                                        "type": "string",
                                        "title": "姓",
                                        "format": "text",
                                        "title_i18n": {"en": "Family Name", "ja": "姓"},
                                        "title_i18n_temp": {
                                            "en": "Family Name",
                                            "ja": "姓",
                                        },
                                    },
                                    "familyNameLang": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "言語",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                },
                            },
                            "title": "作成者姓",
                            "format": "array",
                        },
                        "creatorMails": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "creatorMail": {
                                        "type": "string",
                                        "title": "メールアドレス",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Email Address",
                                            "ja": "メールアドレス",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Email Address",
                                            "ja": "メールアドレス",
                                        },
                                    }
                                },
                            },
                            "title": "作成者メールアドレス",
                            "format": "array",
                        },
                        "creatorNames": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "creatorName": {
                                        "type": "string",
                                        "title": "姓名",
                                        "format": "text",
                                        "title_i18n": {"en": "Name", "ja": "姓名"},
                                        "title_i18n_temp": {"en": "Name", "ja": "姓名"},
                                    },
                                    "creatorNameLang": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "言語",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                },
                            },
                            "title": "作成者姓名",
                            "format": "array",
                        },
                        "nameIdentifiers": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "nameIdentifier": {
                                        "type": "string",
                                        "title": "作成者識別子",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Creator Identifier",
                                            "ja": "作成者識別子",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Creator Identifier",
                                            "ja": "作成者識別子",
                                        },
                                    },
                                    "nameIdentifierURI": {
                                        "type": "string",
                                        "title": "作成者識別子URI",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Creator Identifier URI",
                                            "ja": "作成者識別子URI",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Creator Identifier URI",
                                            "ja": "作成者識別子URI",
                                        },
                                    },
                                    "nameIdentifierScheme": {
                                        "type": ["null", "string"],
                                        "title": "作成者識別子Scheme",
                                        "format": "select",
                                        "currentEnum": [],
                                    },
                                },
                            },
                            "title": "作成者識別子",
                            "format": "array",
                        },
                        "creatorAffiliations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "affiliationNames": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "format": "object",
                                            "properties": {
                                                "affiliationName": {
                                                    "type": "string",
                                                    "title": "所属機関名",
                                                    "format": "text",
                                                    "title_i18n": {
                                                        "en": "Affiliation Name",
                                                        "ja": "所属機関名",
                                                    },
                                                    "title_i18n_temp": {
                                                        "en": "Affiliation Name",
                                                        "ja": "所属機関名",
                                                    },
                                                },
                                                "affiliationNameLang": {
                                                    "enum": [
                                                        None,
                                                        "ja",
                                                        "ja-Kana",
                                                        "en",
                                                        "fr",
                                                        "it",
                                                        "de",
                                                        "es",
                                                        "zh-cn",
                                                        "zh-tw",
                                                        "ru",
                                                        "la",
                                                        "ms",
                                                        "eo",
                                                        "ar",
                                                        "el",
                                                        "ko",
                                                    ],
                                                    "type": ["null", "string"],
                                                    "title": "言語",
                                                    "format": "select",
                                                    "currentEnum": [
                                                        "ja",
                                                        "ja-Kana",
                                                        "en",
                                                        "fr",
                                                        "it",
                                                        "de",
                                                        "es",
                                                        "zh-cn",
                                                        "zh-tw",
                                                        "ru",
                                                        "la",
                                                        "ms",
                                                        "eo",
                                                        "ar",
                                                        "el",
                                                        "ko",
                                                    ],
                                                },
                                            },
                                        },
                                        "title": "所属機関名",
                                        "format": "array",
                                    },
                                    "affiliationNameIdentifiers": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "format": "object",
                                            "properties": {
                                                "affiliationNameIdentifier": {
                                                    "type": "string",
                                                    "title": "所属機関識別子",
                                                    "format": "text",
                                                    "title_i18n": {
                                                        "en": "Affiliation Name Identifier",
                                                        "ja": "所属機関識別子",
                                                    },
                                                    "title_i18n_temp": {
                                                        "en": "Affiliation Name Identifier",
                                                        "ja": "所属機関識別子",
                                                    },
                                                },
                                                "affiliationNameIdentifierURI": {
                                                    "type": "string",
                                                    "title": "所属機関識別子URI",
                                                    "format": "text",
                                                    "title_i18n": {
                                                        "en": "Affiliation Name Identifier URI",
                                                        "ja": "所属機関識別子URI",
                                                    },
                                                    "title_i18n_temp": {
                                                        "en": "Affiliation Name Identifier URI",
                                                        "ja": "所属機関識別子URI",
                                                    },
                                                },
                                                "affiliationNameIdentifierScheme": {
                                                    "enum": [
                                                        None,
                                                        "kakenhi",
                                                        "ISNI",
                                                        "Ringgold",
                                                        "GRID",
                                                    ],
                                                    "type": ["null", "string"],
                                                    "title": "所属機関識別子スキーマ",
                                                    "format": "select",
                                                    "currentEnum": [
                                                        "kakenhi",
                                                        "ISNI",
                                                        "Ringgold",
                                                        "GRID",
                                                    ],
                                                },
                                            },
                                        },
                                        "title": "所属機関識別子",
                                        "format": "array",
                                    },
                                },
                            },
                            "title": "作成者所属",
                            "format": "array",
                        },
                        "creatorAlternatives": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "creatorAlternative": {
                                        "type": "string",
                                        "title": "別名",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Alternative Name",
                                            "ja": "別名",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Alternative Name",
                                            "ja": "別名",
                                        },
                                    },
                                    "creatorAlternativeLang": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "言語",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                },
                            },
                            "title": "作成者別名",
                            "format": "array",
                        },
                    },
                },
                "title": "Creator",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617186476635": {
                "type": "object",
                "title": "Access Rights",
                "properties": {
                    "subitem_1522299639480": {
                        "enum": [
                            None,
                            "embargoed access",
                            "metadata only access",
                            "open access",
                            "restricted access",
                        ],
                        "type": ["null", "string"],
                        "title": "アクセス権",
                        "format": "select",
                        "currentEnum": [
                            "embargoed access",
                            "metadata only access",
                            "open access",
                            "restricted access",
                        ],
                    },
                    "subitem_1600958577026": {
                        "type": "string",
                        "title": "アクセス権URI",
                        "format": "text",
                        "title_i18n": {"en": "Access Rights URI", "ja": "アクセス権URI"},
                        "title_i18n_temp": {
                            "en": "Access Rights URI",
                            "ja": "アクセス権URI",
                        },
                    },
                },
            },
            "item_1617186499011": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_1522650717957": {
                            "enum": [
                                None,
                                "ja",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                            "type": ["null", "string"],
                            "title": "言語",
                            "format": "select",
                            "currentEnum": [
                                "ja",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                        },
                        "subitem_1522650727486": {
                            "type": "string",
                            "title": "権利情報Resource",
                            "format": "text",
                            "title_i18n": {
                                "en": "Rights Information Resource",
                                "ja": "権利情報Resource",
                            },
                            "title_i18n_temp": {
                                "en": "Rights Information Resource",
                                "ja": "権利情報Resource",
                            },
                        },
                        "subitem_1522651041219": {
                            "type": "string",
                            "title": "権利情報",
                            "format": "text",
                            "title_i18n": {"en": "Rights Information", "ja": "権利情報"},
                            "title_i18n_temp": {
                                "en": "Rights Information",
                                "ja": "権利情報",
                            },
                        },
                    },
                },
                "title": "Rights",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617186609386": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_1522299896455": {
                            "enum": [
                                None,
                                "ja",
                                "ja-Kana",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                            "type": ["null", "string"],
                            "title": "言語",
                            "format": "select",
                            "currentEnum": [
                                "ja",
                                "ja-Kana",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                        },
                        "subitem_1522300014469": {
                            "enum": [
                                None,
                                "BSH",
                                "DDC",
                                "LCC",
                                "LCSH",
                                "MeSH",
                                "NDC",
                                "NDLC",
                                "NDLSH",
                                "SciVal",
                                "UDC",
                                "Other",
                            ],
                            "type": ["null", "string"],
                            "title": "主題Scheme",
                            "format": "select",
                            "currentEnum": [
                                "BSH",
                                "DDC",
                                "LCC",
                                "LCSH",
                                "MeSH",
                                "NDC",
                                "NDLC",
                                "NDLSH",
                                "SciVal",
                                "UDC",
                                "Other",
                            ],
                        },
                        "subitem_1522300048512": {
                            "type": "string",
                            "title": "主題URI",
                            "format": "text",
                            "title_i18n": {"en": "Subject URI", "ja": "主題URI"},
                            "title_i18n_temp": {"en": "Subject URI", "ja": "主題URI"},
                        },
                        "subitem_1523261968819": {
                            "type": "string",
                            "title": "主題",
                            "format": "text",
                            "title_i18n": {"en": "Subject", "ja": "主題"},
                            "title_i18n_temp": {"en": "Subject", "ja": "主題"},
                        },
                    },
                },
                "title": "Subject",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617186626617": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_description": {
                            "type": "string",
                            "title": "内容記述",
                            "format": "textarea",
                            "title_i18n": {"en": "Description", "ja": "内容記述"},
                            "title_i18n_temp": {"en": "Description", "ja": "内容記述"},
                        },
                        "subitem_description_type": {
                            "enum": [
                                None,
                                "Abstract",
                                "Methods",
                                "TableOfContents",
                                "TechnicalInfo",
                                "Other",
                            ],
                            "type": ["null", "string"],
                            "title": "内容記述タイプ",
                            "format": "select",
                            "currentEnum": [
                                "Abstract",
                                "Methods",
                                "TableOfContents",
                                "TechnicalInfo",
                                "Other",
                            ],
                        },
                        "subitem_description_language": {
                            "enum": [
                                None,
                                "ja",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                            "type": ["null", "string"],
                            "title": "言語",
                            "format": "select",
                            "currentEnum": [
                                "ja",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                        },
                    },
                },
                "title": "Description",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617186643794": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_1522300295150": {
                            "enum": [
                                None,
                                "ja",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                            "type": ["null", "string"],
                            "title": "言語",
                            "format": "select",
                            "currentEnum": [
                                "ja",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                        },
                        "subitem_1522300316516": {
                            "type": "string",
                            "title": "出版者",
                            "format": "text",
                            "title_i18n": {"en": "Publisher", "ja": "出版者"},
                            "title_i18n_temp": {"en": "Publisher", "ja": "出版者"},
                        },
                    },
                },
                "title": "Publisher",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617186660861": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_1522300695726": {
                            "enum": [
                                None,
                                "Accepted",
                                "Available",
                                "Collected",
                                "Copyrighted",
                                "Created",
                                "Issued",
                                "Submitted",
                                "Updated",
                                "Valid",
                            ],
                            "type": ["null", "string"],
                            "title": "日付タイプ",
                            "format": "select",
                            "currentEnum": [
                                "Accepted",
                                "Available",
                                "Collected",
                                "Copyrighted",
                                "Created",
                                "Issued",
                                "Submitted",
                                "Updated",
                                "Valid",
                            ],
                        },
                        "subitem_1522300722591": {
                            "type": "string",
                            "title": "日付",
                            "format": "datetime",
                            "title_i18n": {"en": "Date", "ja": "日付"},
                            "title_i18n_temp": {"en": "Date", "ja": "日付"},
                        },
                    },
                },
                "title": "Date",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617186702042": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_1551255818386": {
                            "enum": [
                                None,
                                "jpn",
                                "eng",
                                "fra",
                                "ita",
                                "spa",
                                "zho",
                                "rus",
                                "lat",
                                "msa",
                                "epo",
                                "ara",
                                "ell",
                                "kor",
                            ],
                            "type": ["null", "string"],
                            "title": "Language",
                            "format": "select",
                            "currentEnum": [
                                "jpn",
                                "eng",
                                "fra",
                                "ita",
                                "spa",
                                "zho",
                                "rus",
                                "lat",
                                "msa",
                                "epo",
                                "ara",
                                "ell",
                                "kor",
                            ],
                        }
                    },
                },
                "title": "Language",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617186783814": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_identifier_uri": {
                            "type": "string",
                            "title": "識別子",
                            "format": "text",
                            "title_i18n": {"en": "Identifier", "ja": "識別子"},
                            "title_i18n_temp": {"en": "Identifier", "ja": "識別子"},
                        },
                        "subitem_identifier_type": {
                            "enum": [None, "DOI", "HDL", "URI"],
                            "type": ["null", "string"],
                            "title": "識別子タイプ",
                            "format": "select",
                            "currentEnum": ["DOI", "HDL", "URI"],
                        },
                    },
                },
                "title": "Identifier",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617186819068": {
                "type": "object",
                "title": "Identifier Registration",
                "properties": {
                    "subitem_identifier_reg_text": {
                        "type": "string",
                        "title": "ID登録",
                        "format": "text",
                        "title_i18n": {"en": "Identifier Registration", "ja": "ID登録"},
                        "title_i18n_temp": {
                            "en": "Identifier Registration",
                            "ja": "ID登録",
                        },
                    },
                    "subitem_identifier_reg_type": {
                        "enum": [None, "JaLC", "Crossref", "DataCite", "PMID"],
                        "type": ["null", "string"],
                        "title": "ID登録タイプ",
                        "format": "select",
                        "currentEnum": ["JaLC", "Crossref", "DataCite", "PMID"],
                    },
                },
            },
            "item_1617186859717": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_1522658018441": {
                            "enum": [
                                None,
                                "ja",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                            "type": ["null", "string"],
                            "title": "言語",
                            "format": "select",
                            "currentEnum": [
                                "ja",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                        },
                        "subitem_1522658031721": {
                            "type": "string",
                            "title": "時間的範囲",
                            "format": "text",
                            "title_i18n": {"en": "Temporal", "ja": "時間的範囲"},
                            "title_i18n_temp": {"en": "Temporal", "ja": "時間的範囲"},
                        },
                    },
                },
                "title": "Temporal",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617186882738": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_geolocation_box": {
                            "type": "object",
                            "title": "位置情報（空間）",
                            "format": "object",
                            "properties": {
                                "subitem_east_longitude": {
                                    "type": "string",
                                    "title": "東部経度",
                                    "format": "text",
                                    "title_i18n": {
                                        "en": "East Bound Longitude",
                                        "ja": "東部経度",
                                    },
                                    "title_i18n_temp": {
                                        "en": "East Bound Longitude",
                                        "ja": "東部経度",
                                    },
                                },
                                "subitem_north_latitude": {
                                    "type": "string",
                                    "title": "北部緯度",
                                    "format": "text",
                                    "title_i18n": {
                                        "en": "North Bound Latitude",
                                        "ja": "北部緯度",
                                    },
                                    "title_i18n_temp": {
                                        "en": "North Bound Latitude",
                                        "ja": "北部緯度",
                                    },
                                },
                                "subitem_south_latitude": {
                                    "type": "string",
                                    "title": "南部緯度",
                                    "format": "text",
                                    "title_i18n": {
                                        "en": "South Bound Latitude",
                                        "ja": "南部緯度",
                                    },
                                    "title_i18n_temp": {
                                        "en": "South Bound Latitude",
                                        "ja": "南部緯度",
                                    },
                                },
                                "subitem_west_longitude": {
                                    "type": "string",
                                    "title": "西部経度",
                                    "format": "text",
                                    "title_i18n": {
                                        "en": "West Bound Longitude",
                                        "ja": "西部経度",
                                    },
                                    "title_i18n_temp": {
                                        "en": "West Bound Longitude",
                                        "ja": "西部経度",
                                    },
                                },
                            },
                        },
                        "subitem_geolocation_place": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "subitem_geolocation_place_text": {
                                        "type": "string",
                                        "title": "位置情報（自由記述）",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Geo Location Place",
                                            "ja": "位置情報（自由記述）",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Geo Location Place",
                                            "ja": "位置情報（自由記述）",
                                        },
                                    }
                                },
                            },
                            "title": "位置情報（自由記述）",
                            "format": "array",
                        },
                        "subitem_geolocation_point": {
                            "type": "object",
                            "title": "位置情報（点）",
                            "format": "object",
                            "properties": {
                                "subitem_point_latitude": {
                                    "type": "string",
                                    "title": "緯度",
                                    "format": "text",
                                    "title_i18n": {"en": "Point Latitude", "ja": "緯度"},
                                    "title_i18n_temp": {
                                        "en": "Point Latitude",
                                        "ja": "緯度",
                                    },
                                },
                                "subitem_point_longitude": {
                                    "type": "string",
                                    "title": "経度",
                                    "format": "text",
                                    "title_i18n": {"en": "Point Longitude", "ja": "経度"},
                                    "title_i18n_temp": {
                                        "en": "Point Longitude",
                                        "ja": "経度",
                                    },
                                },
                            },
                        },
                    },
                },
                "title": "Geo Location",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617186901218": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_1522399143519": {
                            "type": "object",
                            "title": "助成機関識別子",
                            "format": "object",
                            "properties": {
                                "subitem_1522399281603": {
                                    "enum": [
                                        None,
                                        "Crossref Funder",
                                        "GRID",
                                        "ISNI",
                                        "Other",
                                        "kakenhi",
                                    ],
                                    "type": ["null", "string"],
                                    "title": "助成機関識別子タイプ",
                                    "format": "select",
                                    "currentEnum": [
                                        "Crossref Funder",
                                        "GRID",
                                        "ISNI",
                                        "Other",
                                        "kakenhi",
                                    ],
                                },
                                "subitem_1522399333375": {
                                    "type": "string",
                                    "title": "助成機関識別子",
                                    "format": "text",
                                    "title_i18n": {
                                        "en": "Funder Identifier",
                                        "ja": "助成機関識別子",
                                    },
                                    "title_i18n_temp": {
                                        "en": "Funder Identifier",
                                        "ja": "助成機関識別子",
                                    },
                                },
                            },
                        },
                        "subitem_1522399412622": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "subitem_1522399416691": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "言語",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                    "subitem_1522737543681": {
                                        "type": "string",
                                        "title": "助成機関名",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Funder Name",
                                            "ja": "助成機関名",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Funder Name",
                                            "ja": "助成機関名",
                                        },
                                    },
                                },
                            },
                            "title": "助成機関名",
                            "format": "array",
                        },
                        "subitem_1522399571623": {
                            "type": "object",
                            "title": "研究課題番号",
                            "format": "object",
                            "properties": {
                                "subitem_1522399585738": {
                                    "type": "string",
                                    "title": "研究課題URI",
                                    "format": "text",
                                    "title_i18n": {"en": "Award URI", "ja": "研究課題URI"},
                                    "title_i18n_temp": {
                                        "en": "Award URI",
                                        "ja": "研究課題URI",
                                    },
                                },
                                "subitem_1522399628911": {
                                    "type": "string",
                                    "title": "研究課題番号",
                                    "format": "text",
                                    "title_i18n": {
                                        "en": "Award Number",
                                        "ja": "研究課題番号",
                                    },
                                    "title_i18n_temp": {
                                        "en": "Award Number",
                                        "ja": "研究課題番号",
                                    },
                                },
                            },
                        },
                        "subitem_1522399651758": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "subitem_1522721910626": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "言語",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                    "subitem_1522721929892": {
                                        "type": "string",
                                        "title": "研究課題名",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Award Title",
                                            "ja": "研究課題名",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Award Title",
                                            "ja": "研究課題名",
                                        },
                                    },
                                },
                            },
                            "title": "研究課題名",
                            "format": "array",
                        },
                    },
                },
                "title": "Funding Reference",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617186920753": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_1522646500366": {
                            "enum": [None, "PISSN", "EISSN", "ISSN", "NCID"],
                            "type": ["null", "string"],
                            "title": "収録物識別子タイプ",
                            "format": "select",
                            "currentEnum": ["PISSN", "EISSN", "ISSN", "NCID"],
                        },
                        "subitem_1522646572813": {
                            "type": "string",
                            "title": "収録物識別子",
                            "format": "text",
                            "title_i18n": {"en": "Source Identifier", "ja": "収録物識別子"},
                            "title_i18n_temp": {
                                "en": "Source Identifier",
                                "ja": "収録物識別子",
                            },
                        },
                    },
                },
                "title": "Source Identifier",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617186941041": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_1522650068558": {
                            "enum": [
                                None,
                                "ja",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                            "type": ["null", "string"],
                            "title": "言語",
                            "format": "select",
                            "currentEnum": [
                                "ja",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                        },
                        "subitem_1522650091861": {
                            "type": "string",
                            "title": "収録物名",
                            "format": "text",
                            "title_i18n": {"en": "Source Title", "ja": "収録物名"},
                            "title_i18n_temp": {"en": "Source Title", "ja": "収録物名"},
                        },
                    },
                },
                "title": "Source Title",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617186959569": {
                "type": "object",
                "title": "Volume Number",
                "properties": {
                    "subitem_1551256328147": {
                        "type": "string",
                        "title": "Volume Number",
                        "format": "text",
                        "title_i18n": {"en": "Volume Number", "ja": "巻"},
                        "title_i18n_temp": {"en": "Volume Number", "ja": "巻"},
                    }
                },
            },
            "item_1617186981471": {
                "type": "object",
                "title": "Issue Number",
                "properties": {
                    "subitem_1551256294723": {
                        "type": "string",
                        "title": "Issue Number",
                        "format": "text",
                        "title_i18n": {"en": "Issue Number", "ja": "号"},
                        "title_i18n_temp": {"en": "Issue Number", "ja": "号"},
                    }
                },
            },
            "item_1617186994930": {
                "type": "object",
                "title": "Number of Pages",
                "properties": {
                    "subitem_1551256248092": {
                        "type": "string",
                        "title": "Number of Pages",
                        "format": "text",
                        "title_i18n": {"en": "Number of Pages", "ja": "ページ数"},
                        "title_i18n_temp": {"en": "Number of Pages", "ja": "ページ数"},
                    }
                },
            },
            "item_1617187024783": {
                "type": "object",
                "title": "Page Start",
                "properties": {
                    "subitem_1551256198917": {
                        "type": "string",
                        "title": "Page Start",
                        "format": "text",
                        "title_i18n": {"en": "Page Start", "ja": "開始ページ"},
                        "title_i18n_temp": {"en": "Page Start", "ja": "開始ページ"},
                    }
                },
            },
            "item_1617187045071": {
                "type": "object",
                "title": "Page End",
                "properties": {
                    "subitem_1551256185532": {
                        "type": "string",
                        "title": "Page End",
                        "format": "text",
                        "title_i18n": {"en": "Page End", "ja": "終了ページ"},
                        "title_i18n_temp": {"en": "Page End", "ja": "終了ページ"},
                    }
                },
            },
            "item_1617187056579": {
                "type": "object",
                "title": "Bibliographic Information",
                "properties": {
                    "bibliographicPageEnd": {
                        "type": "string",
                        "title": "終了ページ",
                        "format": "text",
                        "title_i18n": {"en": "Page End", "ja": "終了ページ"},
                        "title_i18n_temp": {"en": "Page End", "ja": "終了ページ"},
                    },
                    "bibliographic_titles": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "format": "object",
                            "properties": {
                                "bibliographic_title": {
                                    "type": "string",
                                    "title": "タイトル",
                                    "format": "text",
                                    "title_i18n": {"en": "Title", "ja": "タイトル"},
                                    "title_i18n_temp": {"en": "Title", "ja": "タイトル"},
                                },
                                "bibliographic_titleLang": {
                                    "enum": [
                                        None,
                                        "ja",
                                        "en",
                                        "fr",
                                        "it",
                                        "de",
                                        "es",
                                        "zh-cn",
                                        "zh-tw",
                                        "ru",
                                        "la",
                                        "ms",
                                        "eo",
                                        "ar",
                                        "el",
                                        "ko",
                                    ],
                                    "type": ["null", "string"],
                                    "title": "言語",
                                    "format": "select",
                                    "currentEnum": [
                                        "ja",
                                        "en",
                                        "fr",
                                        "it",
                                        "de",
                                        "es",
                                        "zh-cn",
                                        "zh-tw",
                                        "ru",
                                        "la",
                                        "ms",
                                        "eo",
                                        "ar",
                                        "el",
                                        "ko",
                                    ],
                                },
                            },
                        },
                        "title": "雑誌名",
                        "format": "array",
                    },
                    "bibliographicPageStart": {
                        "type": "string",
                        "title": "開始ページ",
                        "format": "text",
                        "title_i18n": {"en": "Page Start", "ja": "開始ページ"},
                        "title_i18n_temp": {"en": "Page Start", "ja": "開始ページ"},
                    },
                    "bibliographicIssueDates": {
                        "type": "object",
                        "title": "発行日",
                        "format": "object",
                        "properties": {
                            "bibliographicIssueDate": {
                                "type": "string",
                                "title": "日付",
                                "format": "datetime",
                                "title_i18n": {"en": "Date", "ja": "日付"},
                                "title_i18n_temp": {"en": "Date", "ja": "日付"},
                            },
                            "bibliographicIssueDateType": {
                                "enum": [None, "Issued"],
                                "type": ["null", "string"],
                                "title": "日付タイプ",
                                "format": "select",
                                "currentEnum": ["Issued"],
                            },
                        },
                    },
                    "bibliographicIssueNumber": {
                        "type": "string",
                        "title": "号",
                        "format": "text",
                        "title_i18n": {"en": "Issue Number", "ja": "号"},
                        "title_i18n_temp": {"en": "Issue Number", "ja": "号"},
                    },
                    "bibliographicVolumeNumber": {
                        "type": "string",
                        "title": "巻",
                        "format": "text",
                        "title_i18n": {"en": "Volume Number", "ja": "巻"},
                        "title_i18n_temp": {"en": "Volume Number", "ja": "巻"},
                    },
                    "bibliographicNumberOfPages": {
                        "type": "string",
                        "title": "ページ数",
                        "format": "text",
                        "title_i18n": {"en": "Number of Page", "ja": "ページ数"},
                        "title_i18n_temp": {"en": "Number of Page", "ja": "ページ数"},
                    },
                },
            },
            "item_1617187087799": {
                "type": "object",
                "title": "Dissertation Number",
                "properties": {
                    "subitem_1551256171004": {
                        "type": "string",
                        "title": "Dissertation Number",
                        "format": "text",
                        "title_i18n": {"en": "Dissertation Number", "ja": "学位授与番号"},
                        "title_i18n_temp": {
                            "en": "Dissertation Number",
                            "ja": "学位授与番号",
                        },
                    }
                },
            },
            "item_1617187112279": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_1551256126428": {
                            "type": "string",
                            "title": "Degree Name",
                            "format": "text",
                            "title_i18n": {"en": "Degree Name", "ja": "学位名"},
                            "title_i18n_temp": {"en": "Degree Name", "ja": "学位名"},
                        },
                        "subitem_1551256129013": {
                            "enum": [
                                None,
                                "ja",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                            "type": ["null", "string"],
                            "title": "Language",
                            "format": "select",
                            "currentEnum": [
                                "ja",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                        },
                    },
                },
                "title": "Degree Name",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617187136212": {
                "type": "object",
                "title": "Date Granted",
                "properties": {
                    "subitem_1551256096004": {
                        "type": "string",
                        "title": "Date Granted",
                        "format": "datetime",
                        "title_i18n": {"en": "Date Granted", "ja": "学位授与年月日"},
                        "title_i18n_temp": {"en": "Date Granted", "ja": "学位授与年月日"},
                    }
                },
            },
            "item_1617187187528": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_1599711633003": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "subitem_1599711636923": {
                                        "type": "string",
                                        "title": "Conference Name",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Conference Name",
                                            "ja": "会議名",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Conference Name",
                                            "ja": "会議名",
                                        },
                                    },
                                    "subitem_1599711645590": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "Language",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                },
                            },
                            "title": "Conference Name",
                            "format": "array",
                        },
                        "subitem_1599711655652": {
                            "type": "string",
                            "title": "Conference Sequence",
                            "format": "text",
                            "title_i18n": {"en": "Conference Sequence", "ja": "回次"},
                            "title_i18n_temp": {
                                "en": "Conference Sequence",
                                "ja": "回次",
                            },
                        },
                        "subitem_1599711660052": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "subitem_1599711680082": {
                                        "type": "string",
                                        "title": "Conference Sponsor",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Conference Sponsor",
                                            "ja": "主催機関",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Conference Sponsor",
                                            "ja": "主催機関",
                                        },
                                    },
                                    "subitem_1599711686511": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "Language",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                },
                            },
                            "title": "Conference Sponsor",
                            "format": "array",
                        },
                        "subitem_1599711699392": {
                            "type": "object",
                            "title": "Conference Date",
                            "format": "object",
                            "properties": {
                                "subitem_1599711704251": {
                                    "type": "string",
                                    "title": "Conference Date",
                                    "format": "text",
                                    "title_i18n": {
                                        "en": "Conference Date",
                                        "ja": "開催期間",
                                    },
                                    "title_i18n_temp": {
                                        "en": "Conference Date",
                                        "ja": "開催期間",
                                    },
                                },
                                "subitem_1599711712451": {
                                    "type": "string",
                                    "title": "Start Day",
                                    "format": "text",
                                    "title_i18n": {"en": "Start Day", "ja": "開始日"},
                                    "title_i18n_temp": {"en": "Start Day", "ja": "開始日"},
                                },
                                "subitem_1599711727603": {
                                    "type": "string",
                                    "title": "Start Month",
                                    "format": "text",
                                    "title_i18n": {"en": "Start Month", "ja": "開始月"},
                                    "title_i18n_temp": {
                                        "en": "Start Month",
                                        "ja": "開始月",
                                    },
                                },
                                "subitem_1599711731891": {
                                    "type": "string",
                                    "title": "Start Year",
                                    "format": "text",
                                    "title_i18n": {"en": "Start Year", "ja": "開始年"},
                                    "title_i18n_temp": {
                                        "en": "Start Year",
                                        "ja": "開始年",
                                    },
                                },
                                "subitem_1599711735410": {
                                    "type": "string",
                                    "title": "End Day",
                                    "format": "text",
                                    "title_i18n": {"en": "End Day", "ja": "終了日"},
                                    "title_i18n_temp": {"en": "End Day", "ja": "終了日"},
                                },
                                "subitem_1599711739022": {
                                    "type": "string",
                                    "title": "End Month",
                                    "format": "text",
                                    "title_i18n": {"en": "End Month", "ja": "終了月"},
                                    "title_i18n_temp": {"en": "End Month", "ja": "終了月"},
                                },
                                "subitem_1599711743722": {
                                    "type": "string",
                                    "title": "End Year",
                                    "format": "text",
                                    "title_i18n": {"en": "End Year", "ja": "終了年"},
                                    "title_i18n_temp": {"en": "End Year", "ja": "終了年"},
                                },
                                "subitem_1599711745532": {
                                    "enum": [
                                        None,
                                        "ja",
                                        "en",
                                        "fr",
                                        "it",
                                        "de",
                                        "es",
                                        "zh-cn",
                                        "zh-tw",
                                        "ru",
                                        "la",
                                        "ms",
                                        "eo",
                                        "ar",
                                        "el",
                                        "ko",
                                    ],
                                    "type": ["null", "string"],
                                    "title": "Language",
                                    "format": "select",
                                    "currentEnum": [
                                        "ja",
                                        "en",
                                        "fr",
                                        "it",
                                        "de",
                                        "es",
                                        "zh-cn",
                                        "zh-tw",
                                        "ru",
                                        "la",
                                        "ms",
                                        "eo",
                                        "ar",
                                        "el",
                                        "ko",
                                    ],
                                },
                            },
                        },
                        "subitem_1599711758470": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "subitem_1599711769260": {
                                        "type": "string",
                                        "title": "Conference Venue",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Conference Venue",
                                            "ja": "開催会場",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Conference Venue",
                                            "ja": "開催会場",
                                        },
                                    },
                                    "subitem_1599711775943": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "Language",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                },
                            },
                            "title": "Conference Venue",
                            "format": "array",
                        },
                        "subitem_1599711788485": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "subitem_1599711798761": {
                                        "type": "string",
                                        "title": "Conference Place",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Conference Place",
                                            "ja": "開催地",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Conference Place",
                                            "ja": "開催地",
                                        },
                                    },
                                    "subitem_1599711803382": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "Language",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                },
                            },
                            "title": "Conference Place",
                            "format": "array",
                        },
                        "subitem_1599711813532": {
                            "enum": [
                                None,
                                "JPN",
                                "ABW",
                                "AFG",
                                "AGO",
                                "AIA",
                                "ALA",
                                "ALB",
                                "AND",
                                "ARE",
                                "ARG",
                                "ARM",
                                "ASM",
                                "ATA",
                                "ATF",
                                "ATG",
                                "AUS",
                                "AUT",
                                "AZE",
                                "BDI",
                                "BEL",
                                "BEN",
                                "BES",
                                "BFA",
                                "BGD",
                                "BGR",
                                "BHR",
                                "BHS",
                                "BIH",
                                "BLM",
                                "BLR",
                                "BLZ",
                                "BMU",
                                "BOL",
                                "BRA",
                                "BRB",
                                "BRN",
                                "BTN",
                                "BVT",
                                "BWA",
                                "CAF",
                                "CAN",
                                "CCK",
                                "CHE",
                                "CHL",
                                "CHN",
                                "CIV",
                                "CMR",
                                "COD",
                                "COG",
                                "COK",
                                "COL",
                                "COM",
                                "CPV",
                                "CRI",
                                "CUB",
                                "CUW",
                                "CXR",
                                "CYM",
                                "CYP",
                                "CZE",
                                "DEU",
                                "DJI",
                                "DMA",
                                "DNK",
                                "DOM",
                                "DZA",
                                "ECU",
                                "EGY",
                                "ERI",
                                "ESH",
                                "ESP",
                                "EST",
                                "ETH",
                                "FIN",
                                "FJI",
                                "FLK",
                                "FRA",
                                "FRO",
                                "FSM",
                                "GAB",
                                "GBR",
                                "GEO",
                                "GGY",
                                "GHA",
                                "GIB",
                                "GIN",
                                "GLP",
                                "GMB",
                                "GNB",
                                "GNQ",
                                "GRC",
                                "GRD",
                                "GRL",
                                "GTM",
                                "GUF",
                                "GUM",
                                "GUY",
                                "HKG",
                                "HMD",
                                "HND",
                                "HRV",
                                "HTI",
                                "HUN",
                                "IDN",
                                "IMN",
                                "IND",
                                "IOT",
                                "IRL",
                                "IRN",
                                "IRQ",
                                "ISL",
                                "ISR",
                                "ITA",
                                "JAM",
                                "JEY",
                                "JOR",
                                "KAZ",
                                "KEN",
                                "KGZ",
                                "KHM",
                                "KIR",
                                "KNA",
                                "KOR",
                                "KWT",
                                "LAO",
                                "LBN",
                                "LBR",
                                "LBY",
                                "LCA",
                                "LIE",
                                "LKA",
                                "LSO",
                                "LTU",
                                "LUX",
                                "LVA",
                                "MAC",
                                "MAF",
                                "MAR",
                                "MCO",
                                "MDA",
                                "MDG",
                                "MDV",
                                "MEX",
                                "MHL",
                                "MKD",
                                "MLI",
                                "MLT",
                                "MMR",
                                "MNE",
                                "MNG",
                                "MNP",
                                "MOZ",
                                "MRT",
                                "MSR",
                                "MTQ",
                                "MUS",
                                "MWI",
                                "MYS",
                                "MYT",
                                "NAM",
                                "NCL",
                                "NER",
                                "NFK",
                                "NGA",
                                "NIC",
                                "NIU",
                                "NLD",
                                "NOR",
                                "NPL",
                                "NRU",
                                "NZL",
                                "OMN",
                                "PAK",
                                "PAN",
                                "PCN",
                                "PER",
                                "PHL",
                                "PLW",
                                "PNG",
                                "POL",
                                "PRI",
                                "PRK",
                                "PRT",
                                "PRY",
                                "PSE",
                                "PYF",
                                "QAT",
                                "REU",
                                "ROU",
                                "RUS",
                                "RWA",
                                "SAU",
                                "SDN",
                                "SEN",
                                "SGP",
                                "SGS",
                                "SHN",
                                "SJM",
                                "SLB",
                                "SLE",
                                "SLV",
                                "SMR",
                                "SOM",
                                "SPM",
                                "SRB",
                                "SSD",
                                "STP",
                                "SUR",
                                "SVK",
                                "SVN",
                                "SWE",
                                "SWZ",
                                "SXM",
                                "SYC",
                                "SYR",
                                "TCA",
                                "TCD",
                                "TGO",
                                "THA",
                                "TJK",
                                "TKL",
                                "TKM",
                                "TLS",
                                "TON",
                                "TTO",
                                "TUN",
                                "TUR",
                                "TUV",
                                "TWN",
                                "TZA",
                                "UGA",
                                "UKR",
                                "UMI",
                                "URY",
                                "USA",
                                "UZB",
                                "VAT",
                                "VCT",
                                "VEN",
                                "VGB",
                                "VIR",
                                "VNM",
                                "VUT",
                                "WLF",
                                "WSM",
                                "YEM",
                                "ZAF",
                                "ZMB",
                                "ZWE",
                            ],
                            "type": ["null", "string"],
                            "title": "Conference Country",
                            "format": "select",
                            "currentEnum": [
                                "JPN",
                                "ABW",
                                "AFG",
                                "AGO",
                                "AIA",
                                "ALA",
                                "ALB",
                                "AND",
                                "ARE",
                                "ARG",
                                "ARM",
                                "ASM",
                                "ATA",
                                "ATF",
                                "ATG",
                                "AUS",
                                "AUT",
                                "AZE",
                                "BDI",
                                "BEL",
                                "BEN",
                                "BES",
                                "BFA",
                                "BGD",
                                "BGR",
                                "BHR",
                                "BHS",
                                "BIH",
                                "BLM",
                                "BLR",
                                "BLZ",
                                "BMU",
                                "BOL",
                                "BRA",
                                "BRB",
                                "BRN",
                                "BTN",
                                "BVT",
                                "BWA",
                                "CAF",
                                "CAN",
                                "CCK",
                                "CHE",
                                "CHL",
                                "CHN",
                                "CIV",
                                "CMR",
                                "COD",
                                "COG",
                                "COK",
                                "COL",
                                "COM",
                                "CPV",
                                "CRI",
                                "CUB",
                                "CUW",
                                "CXR",
                                "CYM",
                                "CYP",
                                "CZE",
                                "DEU",
                                "DJI",
                                "DMA",
                                "DNK",
                                "DOM",
                                "DZA",
                                "ECU",
                                "EGY",
                                "ERI",
                                "ESH",
                                "ESP",
                                "EST",
                                "ETH",
                                "FIN",
                                "FJI",
                                "FLK",
                                "FRA",
                                "FRO",
                                "FSM",
                                "GAB",
                                "GBR",
                                "GEO",
                                "GGY",
                                "GHA",
                                "GIB",
                                "GIN",
                                "GLP",
                                "GMB",
                                "GNB",
                                "GNQ",
                                "GRC",
                                "GRD",
                                "GRL",
                                "GTM",
                                "GUF",
                                "GUM",
                                "GUY",
                                "HKG",
                                "HMD",
                                "HND",
                                "HRV",
                                "HTI",
                                "HUN",
                                "IDN",
                                "IMN",
                                "IND",
                                "IOT",
                                "IRL",
                                "IRN",
                                "IRQ",
                                "ISL",
                                "ISR",
                                "ITA",
                                "JAM",
                                "JEY",
                                "JOR",
                                "KAZ",
                                "KEN",
                                "KGZ",
                                "KHM",
                                "KIR",
                                "KNA",
                                "KOR",
                                "KWT",
                                "LAO",
                                "LBN",
                                "LBR",
                                "LBY",
                                "LCA",
                                "LIE",
                                "LKA",
                                "LSO",
                                "LTU",
                                "LUX",
                                "LVA",
                                "MAC",
                                "MAF",
                                "MAR",
                                "MCO",
                                "MDA",
                                "MDG",
                                "MDV",
                                "MEX",
                                "MHL",
                                "MKD",
                                "MLI",
                                "MLT",
                                "MMR",
                                "MNE",
                                "MNG",
                                "MNP",
                                "MOZ",
                                "MRT",
                                "MSR",
                                "MTQ",
                                "MUS",
                                "MWI",
                                "MYS",
                                "MYT",
                                "NAM",
                                "NCL",
                                "NER",
                                "NFK",
                                "NGA",
                                "NIC",
                                "NIU",
                                "NLD",
                                "NOR",
                                "NPL",
                                "NRU",
                                "NZL",
                                "OMN",
                                "PAK",
                                "PAN",
                                "PCN",
                                "PER",
                                "PHL",
                                "PLW",
                                "PNG",
                                "POL",
                                "PRI",
                                "PRK",
                                "PRT",
                                "PRY",
                                "PSE",
                                "PYF",
                                "QAT",
                                "REU",
                                "ROU",
                                "RUS",
                                "RWA",
                                "SAU",
                                "SDN",
                                "SEN",
                                "SGP",
                                "SGS",
                                "SHN",
                                "SJM",
                                "SLB",
                                "SLE",
                                "SLV",
                                "SMR",
                                "SOM",
                                "SPM",
                                "SRB",
                                "SSD",
                                "STP",
                                "SUR",
                                "SVK",
                                "SVN",
                                "SWE",
                                "SWZ",
                                "SXM",
                                "SYC",
                                "SYR",
                                "TCA",
                                "TCD",
                                "TGO",
                                "THA",
                                "TJK",
                                "TKL",
                                "TKM",
                                "TLS",
                                "TON",
                                "TTO",
                                "TUN",
                                "TUR",
                                "TUV",
                                "TWN",
                                "TZA",
                                "UGA",
                                "UKR",
                                "UMI",
                                "URY",
                                "USA",
                                "UZB",
                                "VAT",
                                "VCT",
                                "VEN",
                                "VGB",
                                "VIR",
                                "VNM",
                                "VUT",
                                "WLF",
                                "WSM",
                                "YEM",
                                "ZAF",
                                "ZMB",
                                "ZWE",
                            ],
                        },
                    },
                },
                "title": "Conference",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617258105262": {
                "type": "object",
                "title": "Resource Type",
                "required": ["resourceuri", "resourcetype"],
                "properties": {
                    "resourceuri": {
                        "type": "string",
                        "title": "資源タイプ識別子",
                        "format": "text",
                        "title_i18n": {
                            "en": "Resource Type Identifier",
                            "ja": "資源タイプ識別子",
                        },
                        "title_i18n_temp": {
                            "en": "Resource Type Identifier",
                            "ja": "資源タイプ識別子",
                        },
                    },
                    "resourcetype": {
                        "enum": [
                            None,
                            "conference paper",
                            "data paper",
                            "departmental bulletin paper",
                            "editorial",
                            "journal article",
                            "newspaper",
                            "periodical",
                            "review article",
                            "software paper",
                            "article",
                            "book",
                            "book part",
                            "cartographic material",
                            "map",
                            "conference object",
                            "conference proceedings",
                            "conference poster",
                            "dataset",
                            "interview",
                            "image",
                            "still image",
                            "moving image",
                            "video",
                            "lecture",
                            "patent",
                            "internal report",
                            "report",
                            "research report",
                            "technical report",
                            "policy report",
                            "report part",
                            "working paper",
                            "data management plan",
                            "sound",
                            "thesis",
                            "bachelor thesis",
                            "master thesis",
                            "doctoral thesis",
                            "interactive resource",
                            "learning object",
                            "manuscript",
                            "musical notation",
                            "research proposal",
                            "software",
                            "technical documentation",
                            "workflow",
                            "other",
                        ],
                        "type": ["null", "string"],
                        "title": "資源タイプ",
                        "format": "select",
                        "currentEnum": [
                            "conference paper",
                            "data paper",
                            "departmental bulletin paper",
                            "editorial",
                            "journal article",
                            "newspaper",
                            "periodical",
                            "review article",
                            "software paper",
                            "article",
                            "book",
                            "book part",
                            "cartographic material",
                            "map",
                            "conference object",
                            "conference proceedings",
                            "conference poster",
                            "dataset",
                            "interview",
                            "image",
                            "still image",
                            "moving image",
                            "video",
                            "lecture",
                            "patent",
                            "internal report",
                            "report",
                            "research report",
                            "technical report",
                            "policy report",
                            "report part",
                            "working paper",
                            "data management plan",
                            "sound",
                            "thesis",
                            "bachelor thesis",
                            "master thesis",
                            "doctoral thesis",
                            "interactive resource",
                            "learning object",
                            "manuscript",
                            "musical notation",
                            "research proposal",
                            "software",
                            "technical documentation",
                            "workflow",
                            "other",
                        ],
                    },
                },
            },
            "item_1617265215918": {
                "type": "object",
                "title": "Version Type",
                "properties": {
                    "subitem_1522305645492": {
                        "enum": [
                            None,
                            "AO",
                            "SMUR",
                            "AM",
                            "P",
                            "VoR",
                            "CVoR",
                            "EVoR",
                            "NA",
                        ],
                        "type": ["null", "string"],
                        "title": "出版タイプ",
                        "format": "select",
                        "currentEnum": [
                            "AO",
                            "SMUR",
                            "AM",
                            "P",
                            "VoR",
                            "CVoR",
                            "EVoR",
                            "NA",
                        ],
                    },
                    "subitem_1600292170262": {
                        "type": "string",
                        "title": "出版タイプResource",
                        "format": "text",
                        "title_i18n": {
                            "en": "Version Type Resource",
                            "ja": "出版タイプResource",
                        },
                        "title_i18n_temp": {
                            "en": "Version Type Resource",
                            "ja": "出版タイプResource",
                        },
                    },
                },
            },
            "item_1617349709064": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "givenNames": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "givenName": {
                                        "type": "string",
                                        "title": "名",
                                        "format": "text",
                                        "title_i18n": {"en": "Given Name", "ja": "名"},
                                        "title_i18n_temp": {
                                            "en": "Given Name",
                                            "ja": "名",
                                        },
                                    },
                                    "givenNameLang": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "言語",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                },
                            },
                            "title": "寄与者名",
                            "format": "array",
                        },
                        "familyNames": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "familyName": {
                                        "type": "string",
                                        "title": "姓",
                                        "format": "text",
                                        "title_i18n": {"en": "Family Name", "ja": "姓"},
                                        "title_i18n_temp": {
                                            "en": "Family Name",
                                            "ja": "姓",
                                        },
                                    },
                                    "familyNameLang": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "言語",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                },
                            },
                            "title": "寄与者姓",
                            "format": "array",
                        },
                        "contributorType": {
                            "enum": [
                                None,
                                "ContactPerson",
                                "DataCollector",
                                "DataCurator",
                                "DataManager",
                                "Distributor",
                                "Editor",
                                "HostingInstitution",
                                "Producer",
                                "ProjectLeader",
                                "ProjectManager",
                                "ProjectMember",
                                "RelatedPerson",
                                "Researcher",
                                "ResearchGroup",
                                "Sponsor",
                                "Supervisor",
                                "WorkPackageLeader",
                                "Other",
                            ],
                            "type": ["null", "string"],
                            "title": "寄与者タイプ",
                            "format": "select",
                            "currentEnum": [
                                "ContactPerson",
                                "DataCollector",
                                "DataCurator",
                                "DataManager",
                                "Distributor",
                                "Editor",
                                "HostingInstitution",
                                "Producer",
                                "ProjectLeader",
                                "ProjectManager",
                                "ProjectMember",
                                "RelatedPerson",
                                "Researcher",
                                "ResearchGroup",
                                "Sponsor",
                                "Supervisor",
                                "WorkPackageLeader",
                                "Other",
                            ],
                        },
                        "nameIdentifiers": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "nameIdentifier": {
                                        "type": "string",
                                        "title": "寄与者識別子",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Contributor Identifier",
                                            "ja": "寄与者識別子",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Contributor Identifier",
                                            "ja": "寄与者識別子",
                                        },
                                    },
                                    "nameIdentifierURI": {
                                        "type": "string",
                                        "title": "寄与者識別子URI",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Contributor Identifier URI",
                                            "ja": "寄与者識別子URI",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Contributor Identifier URI",
                                            "ja": "寄与者識別子URI",
                                        },
                                    },
                                    "nameIdentifierScheme": {
                                        "type": ["null", "string"],
                                        "title": "寄与者識別子Scheme",
                                        "format": "select",
                                        "currentEnum": [],
                                    },
                                },
                            },
                            "title": "寄与者識別子",
                            "format": "array",
                        },
                        "contributorMails": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "contributorMail": {
                                        "type": "string",
                                        "title": "メールアドレス",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Email Address",
                                            "ja": "メールアドレス",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Email Address",
                                            "ja": "メールアドレス",
                                        },
                                    }
                                },
                            },
                            "title": "寄与者メールアドレス",
                            "format": "array",
                        },
                        "contributorNames": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "lang": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "言語",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                    "contributorName": {
                                        "type": "string",
                                        "title": "姓名",
                                        "format": "text",
                                        "title_i18n": {"en": "Name", "ja": "姓名"},
                                        "title_i18n_temp": {"en": "Name", "ja": "姓名"},
                                    },
                                },
                            },
                            "title": "寄与者姓名",
                            "format": "array",
                        },
                        "contributorAffiliations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "contributorAffiliationNames": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "format": "object",
                                            "properties": {
                                                "contributorAffiliationName": {
                                                    "type": "string",
                                                    "title": "所属機関名",
                                                    "format": "text",
                                                    "title_i18n": {
                                                        "en": "Affiliation Name",
                                                        "ja": "所属機関名",
                                                    },
                                                    "title_i18n_temp": {
                                                        "en": "Affiliation Name",
                                                        "ja": "所属機関名",
                                                    },
                                                },
                                                "contributorAffiliationNameLang": {
                                                    "enum": [
                                                        None,
                                                        "ja",
                                                        "ja-Kana",
                                                        "en",
                                                        "fr",
                                                        "it",
                                                        "de",
                                                        "es",
                                                        "zh-cn",
                                                        "zh-tw",
                                                        "ru",
                                                        "la",
                                                        "ms",
                                                        "eo",
                                                        "ar",
                                                        "el",
                                                        "ko",
                                                    ],
                                                    "type": ["null", "string"],
                                                    "title": "言語",
                                                    "format": "select",
                                                    "currentEnum": [
                                                        "ja",
                                                        "ja-Kana",
                                                        "en",
                                                        "fr",
                                                        "it",
                                                        "de",
                                                        "es",
                                                        "zh-cn",
                                                        "zh-tw",
                                                        "ru",
                                                        "la",
                                                        "ms",
                                                        "eo",
                                                        "ar",
                                                        "el",
                                                        "ko",
                                                    ],
                                                },
                                            },
                                        },
                                        "title": "所属機関識別子",
                                        "format": "array",
                                    },
                                    "contributorAffiliationNameIdentifiers": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "format": "object",
                                            "properties": {
                                                "contributorAffiliationURI": {
                                                    "type": "string",
                                                    "title": "所属機関識別子URI",
                                                    "format": "text",
                                                    "title_i18n": {
                                                        "en": "Affiliation Name Identifier URI",
                                                        "ja": "所属機関識別子URI",
                                                    },
                                                    "title_i18n_temp": {
                                                        "en": "Affiliation Name Identifier URI",
                                                        "ja": "所属機関識別子URI",
                                                    },
                                                },
                                                "contributorAffiliationScheme": {
                                                    "enum": [
                                                        None,
                                                        "kakenhi",
                                                        "ISNI",
                                                        "Ringgold",
                                                        "GRID",
                                                    ],
                                                    "type": ["null", "string"],
                                                    "title": "所属機関識別子スキーマ",
                                                    "format": "select",
                                                    "currentEnum": [
                                                        "kakenhi",
                                                        "ISNI",
                                                        "Ringgold",
                                                        "GRID",
                                                    ],
                                                },
                                                "contributorAffiliationNameIdentifier": {
                                                    "type": "string",
                                                    "title": "所属機関識別子",
                                                    "format": "text",
                                                    "title_i18n": {
                                                        "en": "Affiliation Name Identifier",
                                                        "ja": "所属機関識別子",
                                                    },
                                                    "title_i18n_temp": {
                                                        "en": "Affiliation Name Identifier",
                                                        "ja": "所属機関識別子",
                                                    },
                                                },
                                            },
                                        },
                                        "title": "所属機関識別子",
                                        "format": "array",
                                    },
                                },
                            },
                            "title": "寄与者所属",
                            "format": "array",
                        },
                        "contributorAlternatives": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "contributorAlternative": {
                                        "type": "string",
                                        "title": "別名",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Alternative Name",
                                            "ja": "別名",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Alternative Name",
                                            "ja": "別名",
                                        },
                                    },
                                    "contributorAlternativeLang": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "言語",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                },
                            },
                            "title": "寄与者別名",
                            "format": "array",
                        },
                    },
                },
                "title": "Contributor",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617349808926": {
                "type": "object",
                "title": "Version",
                "properties": {
                    "subitem_1523263171732": {
                        "type": "string",
                        "title": "バージョン情報",
                        "format": "text",
                        "title_i18n": {"en": "Version", "ja": "バージョン情報"},
                        "title_i18n_temp": {"en": "Version", "ja": "バージョン情報"},
                    }
                },
            },
            "item_1617351524846": {
                "type": "object",
                "title": "APC",
                "properties": {
                    "subitem_1523260933860": {
                        "enum": [
                            None,
                            "Paid",
                            "Fully waived",
                            "Not required",
                            "Partially waived",
                            "Not charged",
                            "Unknown",
                        ],
                        "type": ["null", "string"],
                        "title": "APC",
                        "format": "select",
                        "currentEnum": [
                            "Paid",
                            "Fully waived",
                            "Not required",
                            "Partially waived",
                            "Not charged",
                            "Unknown",
                        ],
                    }
                },
            },
            "item_1617353299429": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_1522306207484": {
                            "enum": [
                                None,
                                "isVersionOf",
                                "hasVersion",
                                "isPartOf",
                                "hasPart",
                                "isReferencedBy",
                                "references",
                                "isFormatOf",
                                "hasFormat",
                                "isReplacedBy",
                                "replaces",
                                "isRequiredBy",
                                "requires",
                                "isSupplementTo",
                                "isSupplementedBy",
                                "isIdenticalTo",
                                "isDerivedFrom",
                                "isSourceOf",
                            ],
                            "type": ["null", "string"],
                            "title": "関連タイプ",
                            "format": "select",
                            "currentEnum": [
                                "isVersionOf",
                                "hasVersion",
                                "isPartOf",
                                "hasPart",
                                "isReferencedBy",
                                "references",
                                "isFormatOf",
                                "hasFormat",
                                "isReplacedBy",
                                "replaces",
                                "isRequiredBy",
                                "requires",
                                "isSupplementTo",
                                "isSupplementedBy",
                                "isIdenticalTo",
                                "isDerivedFrom",
                                "isSourceOf",
                            ],
                        },
                        "subitem_1522306287251": {
                            "type": "object",
                            "title": "関連識別子",
                            "format": "object",
                            "properties": {
                                "subitem_1522306382014": {
                                    "enum": [
                                        None,
                                        "ARK",
                                        "arXiv",
                                        "DOI",
                                        "HDL",
                                        "ICHUSHI",
                                        "ISBN",
                                        "J-GLOBAL",
                                        "Local",
                                        "PISSN",
                                        "EISSN",
                                        "ISSN（非推奨）",
                                        "NAID",
                                        "NCID",
                                        "PMID",
                                        "PURL",
                                        "SCOPUS",
                                        "URI",
                                        "WOS",
                                    ],
                                    "type": ["null", "string"],
                                    "title": "識別子タイプ",
                                    "format": "select",
                                    "currentEnum": [
                                        "ARK",
                                        "arXiv",
                                        "DOI",
                                        "HDL",
                                        "ICHUSHI",
                                        "ISBN",
                                        "J-GLOBAL",
                                        "Local",
                                        "PISSN",
                                        "EISSN",
                                        "ISSN（非推奨）",
                                        "NAID",
                                        "NCID",
                                        "PMID",
                                        "PURL",
                                        "SCOPUS",
                                        "URI",
                                        "WOS",
                                    ],
                                },
                                "subitem_1522306436033": {
                                    "type": "string",
                                    "title": "関連識別子",
                                    "format": "text",
                                    "title_i18n": {
                                        "en": "Relation Identifier",
                                        "ja": "関連識別子",
                                    },
                                    "title_i18n_temp": {
                                        "en": "Relation Identifier",
                                        "ja": "関連識別子",
                                    },
                                },
                            },
                        },
                        "subitem_1523320863692": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "subitem_1523320867455": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "言語",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                    "subitem_1523320909613": {
                                        "type": "string",
                                        "title": "関連名称",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Related Title",
                                            "ja": "関連名称",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Related Title",
                                            "ja": "関連名称",
                                        },
                                    },
                                },
                            },
                            "title": "関連名称",
                            "format": "array",
                        },
                    },
                },
                "title": "Relation",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617605131499": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "object",
                            "title": "本文URL",
                            "format": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "title": "本文URL",
                                    "format": "text",
                                    "title_i18n": {"en": "Text URL", "ja": "本文URL"},
                                    "title_i18n_temp": {
                                        "en": "Text URL",
                                        "ja": "本文URL",
                                    },
                                },
                                "label": {
                                    "type": "string",
                                    "title": "ラベル",
                                    "format": "text",
                                    "title_i18n": {"en": "Label", "ja": "ラベル"},
                                    "title_i18n_temp": {"en": "Label", "ja": "ラベル"},
                                },
                                "objectType": {
                                    "enum": [
                                        None,
                                        "abstract",
                                        "summary",
                                        "fulltext",
                                        "thumbnail",
                                        "other",
                                    ],
                                    "type": ["null", "string"],
                                    "title": "オブジェクトタイプ",
                                    "format": "select",
                                    "currentEnum": [
                                        "abstract",
                                        "summary",
                                        "fulltext",
                                        "thumbnail",
                                        "other",
                                    ],
                                },
                            },
                        },
                        "date": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "dateType": {
                                        "type": ["null", "string"],
                                        "title": "日付タイプ",
                                        "format": "select",
                                        "currentEnum": [],
                                    },
                                    "dateValue": {
                                        "type": "string",
                                        "title": "日付",
                                        "format": "datetime",
                                        "title_i18n": {"en": "", "ja": ""},
                                    },
                                },
                            },
                            "title": "オープンアクセスの日付",
                            "format": "array",
                        },
                        "format": {
                            "type": "string",
                            "title": "フォーマット",
                            "format": "text",
                            "title_i18n": {"en": "Format", "ja": "フォーマット"},
                            "title_i18n_temp": {"en": "Format", "ja": "フォーマット"},
                        },
                        "groups": {
                            "type": ["null", "string"],
                            "title": "グループ",
                            "format": "select",
                            "currentEnum": [],
                        },
                        "version": {
                            "type": "string",
                            "title": "バージョン情報",
                            "format": "text",
                            "title_i18n": {
                                "en": "Version Information",
                                "ja": "バージョン情報",
                            },
                            "title_i18n_temp": {
                                "en": "Version Information",
                                "ja": "バージョン情報",
                            },
                        },
                        "fileDate": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "fileDateType": {
                                        "enum": [
                                            None,
                                            "Accepted",
                                            "Collected",
                                            "Copyrighted",
                                            "Created",
                                            "Issued",
                                            "Submitted",
                                            "Updated",
                                            "Valid",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "日付タイプ",
                                        "format": "select",
                                        "currentEnum": [
                                            "Accepted",
                                            "Collected",
                                            "Copyrighted",
                                            "Created",
                                            "Issued",
                                            "Submitted",
                                            "Updated",
                                            "Valid",
                                        ],
                                    },
                                    "fileDateValue": {
                                        "type": "string",
                                        "title": "日付",
                                        "format": "datetime",
                                        "title_i18n": {"en": "Date", "ja": "日付"},
                                        "title_i18n_temp": {"en": "Date", "ja": "日付"},
                                    },
                                },
                            },
                            "title": "日付",
                            "format": "array",
                        },
                        "filename": {
                            "type": ["null", "string"],
                            "title": "表示名",
                            "format": "text",
                            "title_i18n": {"en": "FileName", "ja": "表示名"},
                            "title_i18n_temp": {"en": "FileName", "ja": "表示名"},
                        },
                        "filesize": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "value": {
                                        "type": "string",
                                        "title": "サイズ",
                                        "format": "text",
                                        "title_i18n": {"en": "Size", "ja": "サイズ"},
                                        "title_i18n_temp": {"en": "Size", "ja": "サイズ"},
                                    }
                                },
                            },
                            "title": "サイズ",
                            "format": "array",
                        },
                        "accessrole": {
                            "enum": [
                                "open_access",
                                "open_date",
                                "open_login",
                                "open_no",
                            ],
                            "type": ["null", "string"],
                            "title": "アクセス",
                            "format": "radios",
                        },
                        "displaytype": {
                            "enum": [None, "detail", "simple", "preview"],
                            "type": ["null", "string"],
                            "title": "表示形式",
                            "format": "select",
                            "currentEnum": ["detail", "simple", "preview"],
                        },
                        "licensefree": {
                            "type": "string",
                            "title": "自由ライセンス",
                            "format": "textarea",
                            "title_i18n": {"en": "自由ライセンス", "ja": "自由ライセンス"},
                        },
                        "licensetype": {
                            "type": ["null", "string"],
                            "title": "ライセンス",
                            "format": "select",
                            "currentEnum": [],
                        },
                    },
                },
                "title": "File",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617610673286": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "nameIdentifiers": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "nameIdentifier": {
                                        "type": "string",
                                        "title": "権利者識別子",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Right Holder Identifier",
                                            "ja": "権利者識別子",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Right Holder Identifier",
                                            "ja": "権利者識別子",
                                        },
                                    },
                                    "nameIdentifierURI": {
                                        "type": "string",
                                        "title": "権利者識別子URI",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Right Holder Identifier URI",
                                            "ja": "権利者識別子URI",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Right Holder Identifier URI",
                                            "ja": "権利者識別子URI",
                                        },
                                    },
                                    "nameIdentifierScheme": {
                                        "type": ["null", "string"],
                                        "title": "権利者識別子Scheme",
                                        "format": "select",
                                        "currentEnum": [],
                                    },
                                },
                            },
                            "title": "権利者識別子",
                            "format": "array",
                        },
                        "rightHolderNames": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "rightHolderName": {
                                        "type": "string",
                                        "title": "権利者名",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Right Holder Name",
                                            "ja": "権利者名",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Right Holder Name",
                                            "ja": "権利者名",
                                        },
                                    },
                                    "rightHolderLanguage": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "言語",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "ja-Kana",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                },
                            },
                            "title": "権利者名",
                            "format": "array",
                        },
                    },
                },
                "title": "Rights Holder",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617620223087": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_1565671149650": {
                            "enum": [
                                None,
                                "ja",
                                "ja-Kana",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                            "type": ["null", "string"],
                            "title": "Language",
                            "format": "select",
                            "currentEnum": [
                                "ja",
                                "ja-Kana",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko",
                            ],
                        },
                        "subitem_1565671169640": {
                            "type": "string",
                            "title": "Banner Headline",
                            "format": "text",
                            "title_i18n": {"en": "Banner Headline", "ja": "大見出し"},
                            "title_i18n_temp": {"en": "Banner Headline", "ja": "大見出し"},
                        },
                        "subitem_1565671178623": {
                            "type": "string",
                            "title": "Subheading",
                            "format": "text",
                            "title_i18n": {"en": "Subheading", "ja": "小見出し"},
                            "title_i18n_temp": {"en": "Subheading", "ja": "小見出し"},
                        },
                    },
                },
                "title": "Heading",
                "maxItems": 9999,
                "minItems": 1,
            },
            "item_1617944105607": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_1551256015892": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "subitem_1551256027296": {
                                        "type": "string",
                                        "title": "Degree Grantor Name Identifier",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Degree Grantor Name Identifier",
                                            "ja": "学位授与機関識別子",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Degree Grantor Name Identifier",
                                            "ja": "学位授与機関識別子",
                                        },
                                    },
                                    "subitem_1551256029891": {
                                        "enum": [None, "kakenhi"],
                                        "type": ["null", "string"],
                                        "title": "Degree Grantor Name Identifier Scheme",
                                        "format": "select",
                                        "currentEnum": ["kakenhi"],
                                    },
                                },
                            },
                            "title": "Degree Grantor Name Identifier",
                            "format": "array",
                        },
                        "subitem_1551256037922": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "format": "object",
                                "properties": {
                                    "subitem_1551256042287": {
                                        "type": "string",
                                        "title": "Degree Grantor Name",
                                        "format": "text",
                                        "title_i18n": {
                                            "en": "Degree Grantor Name",
                                            "ja": "学位授与機関名",
                                        },
                                        "title_i18n_temp": {
                                            "en": "Degree Grantor Name",
                                            "ja": "学位授与機関名",
                                        },
                                    },
                                    "subitem_1551256047619": {
                                        "enum": [
                                            None,
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                        "type": ["null", "string"],
                                        "title": "Language",
                                        "format": "select",
                                        "currentEnum": [
                                            "ja",
                                            "en",
                                            "fr",
                                            "it",
                                            "de",
                                            "es",
                                            "zh-cn",
                                            "zh-tw",
                                            "ru",
                                            "la",
                                            "ms",
                                            "eo",
                                            "ar",
                                            "el",
                                            "ko",
                                        ],
                                    },
                                },
                            },
                            "title": "Degree Grantor Name",
                            "format": "array",
                        },
                    },
                },
                "title": "Degree Grantor",
                "maxItems": 9999,
                "minItems": 1,
            },
            "system_identifier_doi": {
                "type": "object",
                "title": "Persistent Identifier(DOI)",
                "format": "object",
                "properties": {
                    "subitem_systemidt_identifier": {
                        "type": "string",
                        "title": "SYSTEMIDT Identifier",
                        "format": "text",
                    },
                    "subitem_systemidt_identifier_type": {
                        "enum": ["DOI", "HDL", "URI"],
                        "type": "string",
                        "title": "SYSTEMIDT Identifier Type",
                        "format": "select",
                    },
                },
                "system_prop": True,
            },
            "system_identifier_hdl": {
                "type": "object",
                "title": "Persistent Identifier(HDL)",
                "format": "object",
                "properties": {
                    "subitem_systemidt_identifier": {
                        "type": "string",
                        "title": "SYSTEMIDT Identifier",
                        "format": "text",
                    },
                    "subitem_systemidt_identifier_type": {
                        "enum": ["DOI", "HDL", "URI"],
                        "type": "string",
                        "title": "SYSTEMIDT Identifier Type",
                        "format": "select",
                    },
                },
                "system_prop": True,
            },
            "system_identifier_uri": {
                "type": "object",
                "title": "Persistent Identifier(URI)",
                "format": "object",
                "properties": {
                    "subitem_systemidt_identifier": {
                        "type": "string",
                        "title": "SYSTEMIDT Identifier",
                        "format": "text",
                    },
                    "subitem_systemidt_identifier_type": {
                        "enum": ["DOI", "HDL", "URI"],
                        "type": "string",
                        "title": "SYSTEMIDT Identifier Type",
                        "format": "select",
                    },
                },
                "system_prop": True,
            },
        },
        "description": "",
    }
    with app.test_request_context():
        node_pre = copy.deepcopy(node)
        json_data_pre = copy.deepcopy(json_data)
        update_json_schema_with_required_items(node, json_data)
        from dictdiffer import diff, patch, swap, revert
        node_diff = diff(node_pre,node)
        json_data_diff = diff(json_data_pre,json_data)
        assert list(node_diff)==[]
        assert list(json_data_diff) == [('add', 'properties.item_1617186419668.items.properties.givenNames.items', [('required', ['givenName'])])]


# def update_json_schema_by_activity_id(json_data, activity_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_update_json_schema_by_activity_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_update_json_schema_by_activity_id(app):
    with open("tests/data/json_data.json", "r") as f:
        json_data = json.load(f)
        with app.test_request_context():
            assert (
                update_json_schema_by_activity_id(json_data, "A-00000000-00000") == None
            )
            redis_connection = RedisConnection()
            sessionstore = redis_connection.connection(db=app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)
            error_list = {'required': ['item_1617186419668.givenNames.givenName', 'item_1617605131499.url.url'], 'required_key': ['jpcoar:URI', 'jpcoar:givenName'], 'pattern': [], 'either': [], 'either_key': [], 'mapping': []}
            sessionstore.put("update_json_schema_A-00000000-00000",(json.dumps(error_list)).encode('utf-8'))
            assert (
                update_json_schema_by_activity_id(json_data, "A-00000000-00000") == None
            )


# def update_schema_form_by_activity_id(schema_form, activity_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_update_schema_form_by_activity_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_update_schema_form_by_activity_id(app,db_itemtype):
    item_type = db_itemtype['item_type']
    with app.test_request_context():
        assert update_schema_form_by_activity_id(item_type.form, "A-00000000-00000")==None
        redis_connection = RedisConnection()
        sessionstore = redis_connection.connection(db=app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)
        error_list = {'required': ['item_1617186419668.givenNames.givenName', 'item_1617605131499.url.url'], 'required_key': ['jpcoar:URI', 'jpcoar:givenName'], 'pattern': [], 'either': [], 'either_key': [], 'mapping': []}
        sessionstore.put("update_json_schema_A-00000000-00000",(json.dumps(error_list)).encode('utf-8'))
        assert update_schema_form_by_activity_id(item_type.form, "A-00000000-00000")==None



# def recursive_prepare_either_required_list(schema_form, either_required_list):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_recursive_prepare_either_required_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_recursive_prepare_either_required_list(app,db_itemtype):
    item_type = db_itemtype['item_type']
    error_list = {'required': ['item_1617186419668.givenNames.givenName', 'item_1617605131499.url.url'], 'required_key': ['jpcoar:URI', 'jpcoar:givenName'], 'pattern': [], 'either': [], 'either_key': [], 'mapping': []}
    with app.test_request_context():
        assert recursive_prepare_either_required_list(item_type.form, error_list['either']) == None


# def recursive_update_schema_form_with_condition(
#     def prepare_either_condition_required(group_idx, key):
#     def set_on_change(elem):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_recursive_update_schema_form_with_condition -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_recursive_update_schema_form_with_condition(app,db_itemtype):
    item_type = db_itemtype['item_type']
    error_list = {'required': ['item_1617186419668.givenNames.givenName', 'item_1617605131499.url.url'], 'required_key': ['jpcoar:URI', 'jpcoar:givenName'], 'pattern': [], 'either': [], 'either_key': [], 'mapping': []}
    with app.test_request_context():
        assert recursive_update_schema_form_with_condition(item_type.form, error_list[ 'either']) == None


# def package_export_file(item_type_data):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_package_export_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_package_export_file(app):
    item_type_data = {
        "item_type_id": "15",
        "name": "デフォルトアイテムタイプ（フル）(15)",
        "root_url": "https://localhost:8443/",
        "jsonschema": "items/jsonschema/15",
        "keys": [
            "#.id",
            ".uri",
            ".metadata.path[0]",
            ".pos_index[0]",
            ".publish_status",
            ".feedback_mail[0]",
            ".cnri",
            ".doi_ra",
            ".doi",
            ".edit_mode",
            ".metadata.pubdate",
            ".metadata.item_1617186331708[0].subitem_1551255647225",
            ".metadata.item_1617186331708[0].subitem_1551255648112",
            ".metadata.item_1617186331708[1].subitem_1551255647225",
            ".metadata.item_1617186331708[1].subitem_1551255648112",
            ".metadata.item_1617186385884[0].subitem_1551255720400",
            ".metadata.item_1617186385884[0].subitem_1551255721061",
            ".metadata.item_1617186385884[1].subitem_1551255720400",
            ".metadata.item_1617186385884[1].subitem_1551255721061",
            ".metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifier",
            ".metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierScheme",
            ".metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierURI",
            ".metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNames[0].affiliationName",
            ".metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNames[0].affiliationNameLang",
            ".metadata.item_1617186419668[0].creatorAlternatives[0].creatorAlternative",
            ".metadata.item_1617186419668[0].creatorAlternatives[0].creatorAlternativeLang",
            ".metadata.item_1617186419668[0].creatorMails[0].creatorMail",
            ".metadata.item_1617186419668[0].creatorNames[0].creatorName",
            ".metadata.item_1617186419668[0].creatorNames[0].creatorNameLang",
            ".metadata.item_1617186419668[0].creatorNames[1].creatorName",
            ".metadata.item_1617186419668[0].creatorNames[1].creatorNameLang",
            ".metadata.item_1617186419668[0].creatorNames[2].creatorName",
            ".metadata.item_1617186419668[0].creatorNames[2].creatorNameLang",
            ".metadata.item_1617186419668[0].familyNames[0].familyName",
            ".metadata.item_1617186419668[0].familyNames[0].familyNameLang",
            ".metadata.item_1617186419668[0].familyNames[1].familyName",
            ".metadata.item_1617186419668[0].familyNames[1].familyNameLang",
            ".metadata.item_1617186419668[0].familyNames[2].familyName",
            ".metadata.item_1617186419668[0].familyNames[2].familyNameLang",
            ".metadata.item_1617186419668[0].givenNames[0].givenName",
            ".metadata.item_1617186419668[0].givenNames[0].givenNameLang",
            ".metadata.item_1617186419668[0].givenNames[1].givenName",
            ".metadata.item_1617186419668[0].givenNames[1].givenNameLang",
            ".metadata.item_1617186419668[0].givenNames[2].givenName",
            ".metadata.item_1617186419668[0].givenNames[2].givenNameLang",
            ".metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifier",
            ".metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierScheme",
            ".metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierURI",
            ".metadata.item_1617186419668[0].nameIdentifiers[1].nameIdentifier",
            ".metadata.item_1617186419668[0].nameIdentifiers[1].nameIdentifierScheme",
            ".metadata.item_1617186419668[0].nameIdentifiers[1].nameIdentifierURI",
            ".metadata.item_1617186419668[0].nameIdentifiers[2].nameIdentifier",
            ".metadata.item_1617186419668[0].nameIdentifiers[2].nameIdentifierScheme",
            ".metadata.item_1617186419668[0].nameIdentifiers[2].nameIdentifierURI",
            ".metadata.item_1617186419668[0].nameIdentifiers[3].nameIdentifier",
            ".metadata.item_1617186419668[0].nameIdentifiers[3].nameIdentifierScheme",
            ".metadata.item_1617186419668[0].nameIdentifiers[3].nameIdentifierURI",
            ".metadata.item_1617186419668[1].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifier",
            ".metadata.item_1617186419668[1].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierScheme",
            ".metadata.item_1617186419668[1].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierURI",
            ".metadata.item_1617186419668[1].creatorAffiliations[0].affiliationNames[0].affiliationName",
            ".metadata.item_1617186419668[1].creatorAffiliations[0].affiliationNames[0].affiliationNameLang",
            ".metadata.item_1617186419668[1].creatorAlternatives[0].creatorAlternative",
            ".metadata.item_1617186419668[1].creatorAlternatives[0].creatorAlternativeLang",
            ".metadata.item_1617186419668[1].creatorMails[0].creatorMail",
            ".metadata.item_1617186419668[1].creatorNames[0].creatorName",
            ".metadata.item_1617186419668[1].creatorNames[0].creatorNameLang",
            ".metadata.item_1617186419668[1].creatorNames[1].creatorName",
            ".metadata.item_1617186419668[1].creatorNames[1].creatorNameLang",
            ".metadata.item_1617186419668[1].creatorNames[2].creatorName",
            ".metadata.item_1617186419668[1].creatorNames[2].creatorNameLang",
            ".metadata.item_1617186419668[1].familyNames[0].familyName",
            ".metadata.item_1617186419668[1].familyNames[0].familyNameLang",
            ".metadata.item_1617186419668[1].familyNames[1].familyName",
            ".metadata.item_1617186419668[1].familyNames[1].familyNameLang",
            ".metadata.item_1617186419668[1].familyNames[2].familyName",
            ".metadata.item_1617186419668[1].familyNames[2].familyNameLang",
            ".metadata.item_1617186419668[1].givenNames[0].givenName",
            ".metadata.item_1617186419668[1].givenNames[0].givenNameLang",
            ".metadata.item_1617186419668[1].givenNames[1].givenName",
            ".metadata.item_1617186419668[1].givenNames[1].givenNameLang",
            ".metadata.item_1617186419668[1].givenNames[2].givenName",
            ".metadata.item_1617186419668[1].givenNames[2].givenNameLang",
            ".metadata.item_1617186419668[1].nameIdentifiers[0].nameIdentifier",
            ".metadata.item_1617186419668[1].nameIdentifiers[0].nameIdentifierScheme",
            ".metadata.item_1617186419668[1].nameIdentifiers[0].nameIdentifierURI",
            ".metadata.item_1617186419668[1].nameIdentifiers[1].nameIdentifier",
            ".metadata.item_1617186419668[1].nameIdentifiers[1].nameIdentifierScheme",
            ".metadata.item_1617186419668[1].nameIdentifiers[1].nameIdentifierURI",
            ".metadata.item_1617186419668[1].nameIdentifiers[2].nameIdentifier",
            ".metadata.item_1617186419668[1].nameIdentifiers[2].nameIdentifierScheme",
            ".metadata.item_1617186419668[1].nameIdentifiers[2].nameIdentifierURI",
            ".metadata.item_1617186419668[2].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifier",
            ".metadata.item_1617186419668[2].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierScheme",
            ".metadata.item_1617186419668[2].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierURI",
            ".metadata.item_1617186419668[2].creatorAffiliations[0].affiliationNames[0].affiliationName",
            ".metadata.item_1617186419668[2].creatorAffiliations[0].affiliationNames[0].affiliationNameLang",
            ".metadata.item_1617186419668[2].creatorAlternatives[0].creatorAlternative",
            ".metadata.item_1617186419668[2].creatorAlternatives[0].creatorAlternativeLang",
            ".metadata.item_1617186419668[2].creatorMails[0].creatorMail",
            ".metadata.item_1617186419668[2].creatorNames[0].creatorName",
            ".metadata.item_1617186419668[2].creatorNames[0].creatorNameLang",
            ".metadata.item_1617186419668[2].creatorNames[1].creatorName",
            ".metadata.item_1617186419668[2].creatorNames[1].creatorNameLang",
            ".metadata.item_1617186419668[2].creatorNames[2].creatorName",
            ".metadata.item_1617186419668[2].creatorNames[2].creatorNameLang",
            ".metadata.item_1617186419668[2].familyNames[0].familyName",
            ".metadata.item_1617186419668[2].familyNames[0].familyNameLang",
            ".metadata.item_1617186419668[2].familyNames[1].familyName",
            ".metadata.item_1617186419668[2].familyNames[1].familyNameLang",
            ".metadata.item_1617186419668[2].familyNames[2].familyName",
            ".metadata.item_1617186419668[2].familyNames[2].familyNameLang",
            ".metadata.item_1617186419668[2].givenNames[0].givenName",
            ".metadata.item_1617186419668[2].givenNames[0].givenNameLang",
            ".metadata.item_1617186419668[2].givenNames[1].givenName",
            ".metadata.item_1617186419668[2].givenNames[1].givenNameLang",
            ".metadata.item_1617186419668[2].givenNames[2].givenName",
            ".metadata.item_1617186419668[2].givenNames[2].givenNameLang",
            ".metadata.item_1617186419668[2].nameIdentifiers[0].nameIdentifier",
            ".metadata.item_1617186419668[2].nameIdentifiers[0].nameIdentifierScheme",
            ".metadata.item_1617186419668[2].nameIdentifiers[0].nameIdentifierURI",
            ".metadata.item_1617186419668[2].nameIdentifiers[1].nameIdentifier",
            ".metadata.item_1617186419668[2].nameIdentifiers[1].nameIdentifierScheme",
            ".metadata.item_1617186419668[2].nameIdentifiers[1].nameIdentifierURI",
            ".metadata.item_1617186419668[2].nameIdentifiers[2].nameIdentifier",
            ".metadata.item_1617186419668[2].nameIdentifiers[2].nameIdentifierScheme",
            ".metadata.item_1617186419668[2].nameIdentifiers[2].nameIdentifierURI",
            ".metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationNameIdentifier",
            ".metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationScheme",
            ".metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationURI",
            ".metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationName",
            ".metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationNameLang",
            ".metadata.item_1617349709064[0].contributorAlternatives[0].contributorAlternative",
            ".metadata.item_1617349709064[0].contributorAlternatives[0].contributorAlternativeLang",
            ".metadata.item_1617349709064[0].contributorMails[0].contributorMail",
            ".metadata.item_1617349709064[0].contributorNames[0].contributorName",
            ".metadata.item_1617349709064[0].contributorNames[0].lang",
            ".metadata.item_1617349709064[0].contributorNames[1].contributorName",
            ".metadata.item_1617349709064[0].contributorNames[1].lang",
            ".metadata.item_1617349709064[0].contributorNames[2].contributorName",
            ".metadata.item_1617349709064[0].contributorNames[2].lang",
            ".metadata.item_1617349709064[0].contributorType",
            ".metadata.item_1617349709064[0].familyNames[0].familyName",
            ".metadata.item_1617349709064[0].familyNames[0].familyNameLang",
            ".metadata.item_1617349709064[0].familyNames[1].familyName",
            ".metadata.item_1617349709064[0].familyNames[1].familyNameLang",
            ".metadata.item_1617349709064[0].familyNames[2].familyName",
            ".metadata.item_1617349709064[0].familyNames[2].familyNameLang",
            ".metadata.item_1617349709064[0].givenNames[0].givenName",
            ".metadata.item_1617349709064[0].givenNames[0].givenNameLang",
            ".metadata.item_1617349709064[0].givenNames[1].givenName",
            ".metadata.item_1617349709064[0].givenNames[1].givenNameLang",
            ".metadata.item_1617349709064[0].givenNames[2].givenName",
            ".metadata.item_1617349709064[0].givenNames[2].givenNameLang",
            ".metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifier",
            ".metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierScheme",
            ".metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierURI",
            ".metadata.item_1617349709064[0].nameIdentifiers[1].nameIdentifier",
            ".metadata.item_1617349709064[0].nameIdentifiers[1].nameIdentifierScheme",
            ".metadata.item_1617349709064[0].nameIdentifiers[1].nameIdentifierURI",
            ".metadata.item_1617349709064[0].nameIdentifiers[2].nameIdentifier",
            ".metadata.item_1617349709064[0].nameIdentifiers[2].nameIdentifierScheme",
            ".metadata.item_1617349709064[0].nameIdentifiers[2].nameIdentifierURI",
            ".metadata.item_1617186476635.subitem_1522299639480",
            ".metadata.item_1617186476635.subitem_1600958577026",
            ".metadata.item_1617351524846.subitem_1523260933860",
            ".metadata.item_1617186499011[0].subitem_1522650717957",
            ".metadata.item_1617186499011[0].subitem_1522650727486",
            ".metadata.item_1617186499011[0].subitem_1522651041219",
            ".metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifier",
            ".metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifierScheme",
            ".metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifierURI",
            ".metadata.item_1617610673286[0].rightHolderNames[0].rightHolderLanguage",
            ".metadata.item_1617610673286[0].rightHolderNames[0].rightHolderName",
            ".metadata.item_1617186609386[0].subitem_1522299896455",
            ".metadata.item_1617186609386[0].subitem_1522300014469",
            ".metadata.item_1617186609386[0].subitem_1522300048512",
            ".metadata.item_1617186609386[0].subitem_1523261968819",
            ".metadata.item_1617186626617[0].subitem_description",
            ".metadata.item_1617186626617[0].subitem_description_language",
            ".metadata.item_1617186626617[0].subitem_description_type",
            ".metadata.item_1617186626617[1].subitem_description",
            ".metadata.item_1617186626617[1].subitem_description_language",
            ".metadata.item_1617186626617[1].subitem_description_type",
            ".metadata.item_1617186643794[0].subitem_1522300295150",
            ".metadata.item_1617186643794[0].subitem_1522300316516",
            ".metadata.item_1617186660861[0].subitem_1522300695726",
            ".metadata.item_1617186660861[0].subitem_1522300722591",
            ".metadata.item_1617186702042[0].subitem_1551255818386",
            ".metadata.item_1617258105262.resourcetype",
            ".metadata.item_1617258105262.resourceuri",
            ".metadata.item_1617349808926.subitem_1523263171732",
            ".metadata.item_1617265215918.subitem_1522305645492",
            ".metadata.item_1617265215918.subitem_1600292170262",
            ".metadata.item_1617186783814[0].subitem_identifier_type",
            ".metadata.item_1617186783814[0].subitem_identifier_uri",
            ".metadata.item_1617186819068.subitem_identifier_reg_text",
            ".metadata.item_1617186819068.subitem_identifier_reg_type",
            ".metadata.item_1617353299429[0].subitem_1522306207484",
            ".metadata.item_1617353299429[0].subitem_1522306287251.subitem_1522306382014",
            ".metadata.item_1617353299429[0].subitem_1522306287251.subitem_1522306436033",
            ".metadata.item_1617353299429[0].subitem_1523320863692[0].subitem_1523320867455",
            ".metadata.item_1617353299429[0].subitem_1523320863692[0].subitem_1523320909613",
            ".metadata.item_1617186859717[0].subitem_1522658018441",
            ".metadata.item_1617186859717[0].subitem_1522658031721",
            ".metadata.item_1617186882738[0].subitem_geolocation_box.subitem_east_longitude",
            ".metadata.item_1617186882738[0].subitem_geolocation_box.subitem_north_latitude",
            ".metadata.item_1617186882738[0].subitem_geolocation_box.subitem_south_latitude",
            ".metadata.item_1617186882738[0].subitem_geolocation_box.subitem_west_longitude",
            ".metadata.item_1617186882738[0].subitem_geolocation_place[0].subitem_geolocation_place_text",
            ".metadata.item_1617186882738[0].subitem_geolocation_point.subitem_point_latitude",
            ".metadata.item_1617186882738[0].subitem_geolocation_point.subitem_point_longitude",
            ".metadata.item_1617186901218[0].subitem_1522399143519.subitem_1522399281603",
            ".metadata.item_1617186901218[0].subitem_1522399143519.subitem_1522399333375",
            ".metadata.item_1617186901218[0].subitem_1522399412622[0].subitem_1522399416691",
            ".metadata.item_1617186901218[0].subitem_1522399412622[0].subitem_1522737543681",
            ".metadata.item_1617186901218[0].subitem_1522399571623.subitem_1522399585738",
            ".metadata.item_1617186901218[0].subitem_1522399571623.subitem_1522399628911",
            ".metadata.item_1617186901218[0].subitem_1522399651758[0].subitem_1522721910626",
            ".metadata.item_1617186901218[0].subitem_1522399651758[0].subitem_1522721929892",
            ".metadata.item_1617186920753[0].subitem_1522646500366",
            ".metadata.item_1617186920753[0].subitem_1522646572813",
            ".metadata.item_1617186941041[0].subitem_1522650068558",
            ".metadata.item_1617186941041[0].subitem_1522650091861",
            ".metadata.item_1617186959569.subitem_1551256328147",
            ".metadata.item_1617186981471.subitem_1551256294723",
            ".metadata.item_1617186994930.subitem_1551256248092",
            ".metadata.item_1617187024783.subitem_1551256198917",
            ".metadata.item_1617187045071.subitem_1551256185532",
            ".metadata.item_1617187056579.bibliographicIssueDates.bibliographicIssueDate",
            ".metadata.item_1617187056579.bibliographicIssueDates.bibliographicIssueDateType",
            ".metadata.item_1617187056579.bibliographicIssueNumber",
            ".metadata.item_1617187056579.bibliographicNumberOfPages",
            ".metadata.item_1617187056579.bibliographicPageEnd",
            ".metadata.item_1617187056579.bibliographicPageStart",
            ".metadata.item_1617187056579.bibliographicVolumeNumber",
            ".metadata.item_1617187056579.bibliographic_titles[0].bibliographic_title",
            ".metadata.item_1617187056579.bibliographic_titles[0].bibliographic_titleLang",
            ".metadata.item_1617187087799.subitem_1551256171004",
            ".metadata.item_1617187112279[0].subitem_1551256126428",
            ".metadata.item_1617187112279[0].subitem_1551256129013",
            ".metadata.item_1617187136212.subitem_1551256096004",
            ".metadata.item_1617944105607[0].subitem_1551256015892[0].subitem_1551256027296",
            ".metadata.item_1617944105607[0].subitem_1551256015892[0].subitem_1551256029891",
            ".metadata.item_1617944105607[0].subitem_1551256037922[0].subitem_1551256042287",
            ".metadata.item_1617944105607[0].subitem_1551256037922[0].subitem_1551256047619",
            ".metadata.item_1617187187528[0].subitem_1599711633003[0].subitem_1599711636923",
            ".metadata.item_1617187187528[0].subitem_1599711633003[0].subitem_1599711645590",
            ".metadata.item_1617187187528[0].subitem_1599711655652",
            ".metadata.item_1617187187528[0].subitem_1599711660052[0].subitem_1599711680082",
            ".metadata.item_1617187187528[0].subitem_1599711660052[0].subitem_1599711686511",
            ".metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711704251",
            ".metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711712451",
            ".metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711727603",
            ".metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711731891",
            ".metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711735410",
            ".metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711739022",
            ".metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711743722",
            ".metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711745532",
            ".metadata.item_1617187187528[0].subitem_1599711758470[0].subitem_1599711769260",
            ".metadata.item_1617187187528[0].subitem_1599711758470[0].subitem_1599711775943",
            ".metadata.item_1617187187528[0].subitem_1599711788485[0].subitem_1599711798761",
            ".metadata.item_1617187187528[0].subitem_1599711788485[0].subitem_1599711803382",
            ".metadata.item_1617187187528[0].subitem_1599711813532",
            ".file_path[0]",
            ".metadata.item_1617605131499[0].accessrole",
            ".metadata.item_1617605131499[0].date[0].dateType",
            ".metadata.item_1617605131499[0].date[0].dateValue",
            ".metadata.item_1617605131499[0].displaytype",
            ".metadata.item_1617605131499[0].fileDate[0].fileDateType",
            ".metadata.item_1617605131499[0].fileDate[0].fileDateValue",
            ".metadata.item_1617605131499[0].filename",
            ".metadata.item_1617605131499[0].filesize[0].value",
            ".metadata.item_1617605131499[0].format",
            ".metadata.item_1617605131499[0].groups",
            ".metadata.item_1617605131499[0].licensefree",
            ".metadata.item_1617605131499[0].licensetype",
            ".metadata.item_1617605131499[0].url.label",
            ".metadata.item_1617605131499[0].url.objectType",
            ".metadata.item_1617605131499[0].url.url",
            ".metadata.item_1617605131499[0].version",
            ".metadata.item_1617620223087[0].subitem_1565671149650",
            ".metadata.item_1617620223087[0].subitem_1565671169640",
            ".metadata.item_1617620223087[0].subitem_1565671178623",
            ".metadata.item_1617620223087[1].subitem_1565671149650",
            ".metadata.item_1617620223087[1].subitem_1565671169640",
            ".metadata.item_1617620223087[1].subitem_1565671178623",
        ],
        "labels": [
            "#ID",
            "URI",
            ".IndexID[0]",
            ".POS_INDEX[0]",
            ".PUBLISH_STATUS",
            ".FEEDBACK_MAIL[0]",
            ".CNRI",
            ".DOI_RA",
            ".DOI",
            "Keep/Upgrade Version",
            "PubDate",
            "Title[0].Title",
            "Title[0].Language",
            "Title[1].Title",
            "Title[1].Language",
            "Alternative Title[0].Alternative Title",
            "Alternative Title[0].Language",
            "Alternative Title[1].Alternative Title",
            "Alternative Title[1].Language",
            "Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子",
            "Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子スキーマ",
            "Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子URI",
            "Creator[0].作成者所属[0].所属機関名[0].所属機関名",
            "Creator[0].作成者所属[0].所属機関名[0].言語",
            "Creator[0].作成者別名[0].別名",
            "Creator[0].作成者別名[0].言語",
            "Creator[0].作成者メールアドレス[0].メールアドレス",
            "Creator[0].作成者姓名[0].姓名",
            "Creator[0].作成者姓名[0].言語",
            "Creator[0].作成者姓名[1].姓名",
            "Creator[0].作成者姓名[1].言語",
            "Creator[0].作成者姓名[2].姓名",
            "Creator[0].作成者姓名[2].言語",
            "Creator[0].作成者姓[0].姓",
            "Creator[0].作成者姓[0].言語",
            "Creator[0].作成者姓[1].姓",
            "Creator[0].作成者姓[1].言語",
            "Creator[0].作成者姓[2].姓",
            "Creator[0].作成者姓[2].言語",
            "Creator[0].作成者名[0].名",
            "Creator[0].作成者名[0].言語",
            "Creator[0].作成者名[1].名",
            "Creator[0].作成者名[1].言語",
            "Creator[0].作成者名[2].名",
            "Creator[0].作成者名[2].言語",
            "Creator[0].作成者識別子[0].作成者識別子",
            "Creator[0].作成者識別子[0].作成者識別子Scheme",
            "Creator[0].作成者識別子[0].作成者識別子URI",
            "Creator[0].作成者識別子[1].作成者識別子",
            "Creator[0].作成者識別子[1].作成者識別子Scheme",
            "Creator[0].作成者識別子[1].作成者識別子URI",
            "Creator[0].作成者識別子[2].作成者識別子",
            "Creator[0].作成者識別子[2].作成者識別子Scheme",
            "Creator[0].作成者識別子[2].作成者識別子URI",
            "Creator[0].作成者識別子[3].作成者識別子",
            "Creator[0].作成者識別子[3].作成者識別子Scheme",
            "Creator[0].作成者識別子[3].作成者識別子URI",
            "Creator[1].作成者所属[0].所属機関識別子[0].所属機関識別子",
            "Creator[1].作成者所属[0].所属機関識別子[0].所属機関識別子スキーマ",
            "Creator[1].作成者所属[0].所属機関識別子[0].所属機関識別子URI",
            "Creator[1].作成者所属[0].所属機関名[0].所属機関名",
            "Creator[1].作成者所属[0].所属機関名[0].言語",
            "Creator[1].作成者別名[0].別名",
            "Creator[1].作成者別名[0].言語",
            "Creator[1].作成者メールアドレス[0].メールアドレス",
            "Creator[1].作成者姓名[0].姓名",
            "Creator[1].作成者姓名[0].言語",
            "Creator[1].作成者姓名[1].姓名",
            "Creator[1].作成者姓名[1].言語",
            "Creator[1].作成者姓名[2].姓名",
            "Creator[1].作成者姓名[2].言語",
            "Creator[1].作成者姓[0].姓",
            "Creator[1].作成者姓[0].言語",
            "Creator[1].作成者姓[1].姓",
            "Creator[1].作成者姓[1].言語",
            "Creator[1].作成者姓[2].姓",
            "Creator[1].作成者姓[2].言語",
            "Creator[1].作成者名[0].名",
            "Creator[1].作成者名[0].言語",
            "Creator[1].作成者名[1].名",
            "Creator[1].作成者名[1].言語",
            "Creator[1].作成者名[2].名",
            "Creator[1].作成者名[2].言語",
            "Creator[1].作成者識別子[0].作成者識別子",
            "Creator[1].作成者識別子[0].作成者識別子Scheme",
            "Creator[1].作成者識別子[0].作成者識別子URI",
            "Creator[1].作成者識別子[1].作成者識別子",
            "Creator[1].作成者識別子[1].作成者識別子Scheme",
            "Creator[1].作成者識別子[1].作成者識別子URI",
            "Creator[1].作成者識別子[2].作成者識別子",
            "Creator[1].作成者識別子[2].作成者識別子Scheme",
            "Creator[1].作成者識別子[2].作成者識別子URI",
            "Creator[2].作成者所属[0].所属機関識別子[0].所属機関識別子",
            "Creator[2].作成者所属[0].所属機関識別子[0].所属機関識別子スキーマ",
            "Creator[2].作成者所属[0].所属機関識別子[0].所属機関識別子URI",
            "Creator[2].作成者所属[0].所属機関名[0].所属機関名",
            "Creator[2].作成者所属[0].所属機関名[0].言語",
            "Creator[2].作成者別名[0].別名",
            "Creator[2].作成者別名[0].言語",
            "Creator[2].作成者メールアドレス[0].メールアドレス",
            "Creator[2].作成者姓名[0].姓名",
            "Creator[2].作成者姓名[0].言語",
            "Creator[2].作成者姓名[1].姓名",
            "Creator[2].作成者姓名[1].言語",
            "Creator[2].作成者姓名[2].姓名",
            "Creator[2].作成者姓名[2].言語",
            "Creator[2].作成者姓[0].姓",
            "Creator[2].作成者姓[0].言語",
            "Creator[2].作成者姓[1].姓",
            "Creator[2].作成者姓[1].言語",
            "Creator[2].作成者姓[2].姓",
            "Creator[2].作成者姓[2].言語",
            "Creator[2].作成者名[0].名",
            "Creator[2].作成者名[0].言語",
            "Creator[2].作成者名[1].名",
            "Creator[2].作成者名[1].言語",
            "Creator[2].作成者名[2].名",
            "Creator[2].作成者名[2].言語",
            "Creator[2].作成者識別子[0].作成者識別子",
            "Creator[2].作成者識別子[0].作成者識別子Scheme",
            "Creator[2].作成者識別子[0].作成者識別子URI",
            "Creator[2].作成者識別子[1].作成者識別子",
            "Creator[2].作成者識別子[1].作成者識別子Scheme",
            "Creator[2].作成者識別子[1].作成者識別子URI",
            "Creator[2].作成者識別子[2].作成者識別子",
            "Creator[2].作成者識別子[2].作成者識別子Scheme",
            "Creator[2].作成者識別子[2].作成者識別子URI",
            "Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子",
            "Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子スキーマ",
            "Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子URI",
            "Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関名",
            "Contributor[0].寄与者所属[0].所属機関識別子[0].言語",
            "Contributor[0].寄与者別名[0].別名",
            "Contributor[0].寄与者別名[0].言語",
            "Contributor[0].寄与者メールアドレス[0].メールアドレス",
            "Contributor[0].寄与者姓名[0].姓名",
            "Contributor[0].寄与者姓名[0].言語",
            "Contributor[0].寄与者姓名[1].姓名",
            "Contributor[0].寄与者姓名[1].言語",
            "Contributor[0].寄与者姓名[2].姓名",
            "Contributor[0].寄与者姓名[2].言語",
            "Contributor[0].寄与者タイプ",
            "Contributor[0].寄与者姓[0].姓",
            "Contributor[0].寄与者姓[0].言語",
            "Contributor[0].寄与者姓[1].姓",
            "Contributor[0].寄与者姓[1].言語",
            "Contributor[0].寄与者姓[2].姓",
            "Contributor[0].寄与者姓[2].言語",
            "Contributor[0].寄与者名[0].名",
            "Contributor[0].寄与者名[0].言語",
            "Contributor[0].寄与者名[1].名",
            "Contributor[0].寄与者名[1].言語",
            "Contributor[0].寄与者名[2].名",
            "Contributor[0].寄与者名[2].言語",
            "Contributor[0].寄与者識別子[0].寄与者識別子",
            "Contributor[0].寄与者識別子[0].寄与者識別子Scheme",
            "Contributor[0].寄与者識別子[0].寄与者識別子URI",
            "Contributor[0].寄与者識別子[1].寄与者識別子",
            "Contributor[0].寄与者識別子[1].寄与者識別子Scheme",
            "Contributor[0].寄与者識別子[1].寄与者識別子URI",
            "Contributor[0].寄与者識別子[2].寄与者識別子",
            "Contributor[0].寄与者識別子[2].寄与者識別子Scheme",
            "Contributor[0].寄与者識別子[2].寄与者識別子URI",
            "Access Rights.アクセス権",
            "Access Rights.アクセス権URI",
            "APC.APC",
            "Rights[0].言語",
            "Rights[0].権利情報Resource",
            "Rights[0].権利情報",
            "Rights Holder[0].権利者識別子[0].権利者識別子",
            "Rights Holder[0].権利者識別子[0].権利者識別子Scheme",
            "Rights Holder[0].権利者識別子[0].権利者識別子URI",
            "Rights Holder[0].権利者名[0].言語",
            "Rights Holder[0].権利者名[0].権利者名",
            "Subject[0].言語",
            "Subject[0].主題Scheme",
            "Subject[0].主題URI",
            "Subject[0].主題",
            "Description[0].内容記述",
            "Description[0].言語",
            "Description[0].内容記述タイプ",
            "Description[1].内容記述",
            "Description[1].言語",
            "Description[1].内容記述タイプ",
            "Publisher[0].言語",
            "Publisher[0].出版者",
            "Date[0].日付タイプ",
            "Date[0].日付",
            "Language[0].Language",
            "Resource Type.資源タイプ",
            "Resource Type.資源タイプ識別子",
            "Version.バージョン情報",
            "Version Type.出版タイプ",
            "Version Type.出版タイプResource",
            "Identifier[0].識別子タイプ",
            "Identifier[0].識別子",
            "Identifier Registration.ID登録",
            "Identifier Registration.ID登録タイプ",
            "Relation[0].関連タイプ",
            "Relation[0].関連識別子.識別子タイプ",
            "Relation[0].関連識別子.関連識別子",
            "Relation[0].関連名称[0].言語",
            "Relation[0].関連名称[0].関連名称",
            "Temporal[0].言語",
            "Temporal[0].時間的範囲",
            "Geo Location[0].位置情報（空間）.東部経度",
            "Geo Location[0].位置情報（空間）.北部緯度",
            "Geo Location[0].位置情報（空間）.南部緯度",
            "Geo Location[0].位置情報（空間）.西部経度",
            "Geo Location[0].位置情報（自由記述）[0].位置情報（自由記述）",
            "Geo Location[0].位置情報（点）.緯度",
            "Geo Location[0].位置情報（点）.経度",
            "Funding Reference[0].助成機関識別子.助成機関識別子タイプ",
            "Funding Reference[0].助成機関識別子.助成機関識別子",
            "Funding Reference[0].助成機関名[0].言語",
            "Funding Reference[0].助成機関名[0].助成機関名",
            "Funding Reference[0].研究課題番号.研究課題URI",
            "Funding Reference[0].研究課題番号.研究課題番号",
            "Funding Reference[0].研究課題名[0].言語",
            "Funding Reference[0].研究課題名[0].研究課題名",
            "Source Identifier[0].収録物識別子タイプ",
            "Source Identifier[0].収録物識別子",
            "Source Title[0].言語",
            "Source Title[0].収録物名",
            "Volume Number.Volume Number",
            "Issue Number.Issue Number",
            "Number of Pages.Number of Pages",
            "Page Start.Page Start",
            "Page End.Page End",
            "Bibliographic Information.発行日.日付",
            "Bibliographic Information.発行日.日付タイプ",
            "Bibliographic Information.号",
            "Bibliographic Information.ページ数",
            "Bibliographic Information.終了ページ",
            "Bibliographic Information.開始ページ",
            "Bibliographic Information.巻",
            "Bibliographic Information.雑誌名[0].タイトル",
            "Bibliographic Information.雑誌名[0].言語",
            "Dissertation Number.Dissertation Number",
            "Degree Name[0].Degree Name",
            "Degree Name[0].Language",
            "Date Granted.Date Granted",
            "Degree Grantor[0].Degree Grantor Name Identifier[0].Degree Grantor Name Identifier",
            "Degree Grantor[0].Degree Grantor Name Identifier[0].Degree Grantor Name Identifier Scheme",
            "Degree Grantor[0].Degree Grantor Name[0].Degree Grantor Name",
            "Degree Grantor[0].Degree Grantor Name[0].Language",
            "Conference[0].Conference Name[0].Conference Name",
            "Conference[0].Conference Name[0].Language",
            "Conference[0].Conference Sequence",
            "Conference[0].Conference Sponsor[0].Conference Sponsor",
            "Conference[0].Conference Sponsor[0].Language",
            "Conference[0].Conference Date.Conference Date",
            "Conference[0].Conference Date.Start Day",
            "Conference[0].Conference Date.Start Month",
            "Conference[0].Conference Date.Start Year",
            "Conference[0].Conference Date.End Day",
            "Conference[0].Conference Date.End Month",
            "Conference[0].Conference Date.End Year",
            "Conference[0].Conference Date.Language",
            "Conference[0].Conference Venue[0].Conference Venue",
            "Conference[0].Conference Venue[0].Language",
            "Conference[0].Conference Place[0].Conference Place",
            "Conference[0].Conference Place[0].Language",
            "Conference[0].Conference Country",
            ".ファイルパス[0]",
            "File[0].アクセス",
            "File[0].オープンアクセスの日付[0].日付タイプ",
            "File[0].オープンアクセスの日付[0].日付",
            "File[0].表示形式",
            "File[0].日付[0].日付タイプ",
            "File[0].日付[0].日付",
            "File[0].表示名",
            "File[0].サイズ[0].サイズ",
            "File[0].フォーマット",
            "File[0].グループ",
            "File[0].自由ライセンス",
            "File[0].ライセンス",
            "File[0].本文URL.ラベル",
            "File[0].本文URL.オブジェクトタイプ",
            "File[0].本文URL.本文URL",
            "File[0].バージョン情報",
            "Heading[0].Language",
            "Heading[0].Banner Headline",
            "Heading[0].Subheading",
            "Heading[1].Language",
            "Heading[1].Banner Headline",
            "Heading[1].Subheading",
        ],
        "recids": [1],
        "data": {
            1: [
                "1661432090216",
                "IndexB",
                "public",
                "wekosoftware@nii.ac.jp",
                "",
                "",
                "",
                "Keep",
                "2021-08-06",
                "ja_conference paperITEM00000001(public_open_access_open_access_simple)",
                "ja",
                "en_conference paperITEM00000001(public_open_access_simple)",
                "en",
                "Alternative Title",
                "en",
                "Alternative Title",
                "ja",
                "0000000121691048",
                "ISNI",
                "http://isni.org/isni/0000000121691048",
                "University",
                "en",
                "",
                "",
                "wekosoftware@nii.ac.jp",
                "情報, 太郎",
                "ja",
                "ジョウホウ, タロウ",
                "ja-Kana",
                "Joho, Taro",
                "en",
                "情報",
                "ja",
                "ジョウホウ",
                "ja-Kana",
                "Joho",
                "en",
                "太郎",
                "ja",
                "タロウ",
                "ja-Kana",
                "Taro",
                "en",
                "4",
                "WEKO",
                "",
                "xxxxxxx",
                "ORCID",
                "https://orcid.org/",
                "xxxxxxx",
                "CiNii",
                "https://ci.nii.ac.jp/",
                "zzzzzzz",
                "KAKEN2",
                "https://kaken.nii.ac.jp/",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "wekosoftware@nii.ac.jp",
                "情報, 太郎",
                "ja",
                "ジョウホウ, タロウ",
                "ja-Kana",
                "Joho, Taro",
                "en",
                "情報",
                "ja",
                "ジョウホウ",
                "ja-Kana",
                "Joho",
                "en",
                "太郎",
                "ja",
                "タロウ",
                "ja-Kana",
                "Taro",
                "en",
                "xxxxxxx",
                "ORCID",
                "https://orcid.org/",
                "xxxxxxx",
                "CiNii",
                "https://ci.nii.ac.jp/",
                "zzzzzzz",
                "KAKEN2",
                "https://kaken.nii.ac.jp/",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "wekosoftware@nii.ac.jp",
                "情報, 太郎",
                "ja",
                "ジョウホウ, タロウ",
                "ja-Kana",
                "Joho, Taro",
                "en",
                "情報",
                "ja",
                "ジョウホウ",
                "ja-Kana",
                "Joho",
                "en",
                "太郎",
                "ja",
                "タロウ",
                "ja-Kana",
                "Taro",
                "en",
                "xxxxxxx",
                "ORCID",
                "https://orcid.org/",
                "xxxxxxx",
                "CiNii",
                "https://ci.nii.ac.jp/",
                "zzzzzzz",
                "KAKEN2",
                "https://kaken.nii.ac.jp/",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "wekosoftware@nii.ac.jp",
                "情報, 太郎",
                "ja",
                "ジョウホウ, タロウ",
                "ja-Kana",
                "Joho, Taro",
                "en",
                "ContactPerson",
                "情報",
                "ja",
                "ジョウホウ",
                "ja-Kana",
                "Joho",
                "en",
                "太郎",
                "ja",
                "タロウ",
                "ja-Kana",
                "Taro",
                "en",
                "xxxxxxx",
                "ORCID",
                "https://orcid.org/",
                "xxxxxxx",
                "CiNii",
                "https://ci.nii.ac.jp/",
                "xxxxxxx",
                "KAKEN2",
                "https://kaken.nii.ac.jp/",
                "open access",
                "http://purl.org/coar/access_right/c_abf2",
                "Unknown",
                "ja",
                "http://localhost",
                "Rights Information",
                "xxxxxx",
                "ORCID",
                "https://orcid.org/",
                "ja",
                "Right Holder Name",
                "ja",
                "Other",
                "http://localhost/",
                "Sibject1",
                "Description<br/>Description<br/>Description",
                "en",
                "Abstract",
                "概要<br/>概要<br/>概要<br/>概要",
                "ja",
                "Abstract",
                "en",
                "Publisher",
                "Available",
                "2021-06-30",
                "jpn",
                "dataset",
                "http://purl.org/coar/resource_type/c_ddb1",
                "Version",
                "AO",
                "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                "URI",
                "http://localhost",
                "",
                "",
                "isVersionOf",
                "arXiv",
                "xxxxx",
                "en",
                "Related Title",
                "en",
                "Temporal",
                "",
                "",
                "",
                "",
                "Japan",
                "",
                "",
                "ISNI",
                "http://xxx",
                "en",
                "Funder Name",
                "Award URI",
                "Award Number",
                "en",
                "Award Title",
                "ISSN",
                "xxxx-xxxx-xxxx",
                "en",
                "Source Title",
                "1",
                "111",
                "12",
                "1",
                "3",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "Degree Name",
                "en",
                "2021-06-30",
                "xxxxxx",
                "kakenhi",
                "Degree Grantor Name",
                "en",
                "Conference Name",
                "ja",
                "1",
                "Sponsor",
                "ja",
                "2020/12/11",
                "1",
                "12",
                "2000",
                "1",
                "12",
                "2020",
                "ja",
                "Conference Venue",
                "ja",
                "Conference Place",
                "ja",
                "JPN",
                "",
                "open_access",
                "Available",
                "2021-07-12",
                "simple",
                "",
                "",
                "1KB.pdf",
                "1 KB",
                "text/plain",
                "",
                "",
                "",
                "",
                "",
                "https://weko3.example.org/record/1/files/1KB.pdf",
                "",
                "ja",
                "Banner Headline",
                "Subheading",
                "en",
                "Banner Headline",
                "Subheding",
            ]
        },
        "is_systems": [
            "#",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "System",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "System",
            "",
            "",
            "System",
            "",
            "",
            "System",
            "System",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ],
        "options": [
            "#",
            "",
            "Allow Multiple",
            "Allow Multiple",
            "Required",
            "Allow Multiple",
            "",
            "",
            "",
            "Required",
            "Required",
            "Required, Allow Multiple",
            "Required, Allow Multiple",
            "Required, Allow Multiple",
            "Required, Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "",
            "",
            "",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Required",
            "Required",
            "",
            "",
            "",
            "Allow Multiple",
            "Allow Multiple",
            "",
            "",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "Allow Multiple",
            "Allow Multiple",
            "",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
            "Allow Multiple",
        ],
    }
    strO = StringIO()
    with open("tests/data/export.tsv", "rb") as f:
        fileData = f.read()
        hash_expect = hashlib.md5(fileData).hexdigest()

    with app.test_request_context():
        ret = package_export_file(item_type_data)
        hash_result = hashlib.md5(ret.getvalue().encode("utf8")).hexdigest()
        assert hash_expect == hash_result


# def make_stats_file(item_type_id, recids, list_item_role):
#         def __init__(self, record_ids):
#         def get_max_ins(self, attr):
#         def get_max_ins_feedback_mail(self):
#         def get_max_items(self, item_attrs):
#         def get_subs_item(self,
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_make_stats_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_make_stats_file(app, users,db_itemtype, db_records,db_itemtype2,db_records2):
    app.config.update(
        EMAIL_DISPLAY_FLG=True,
        WEKO_RECORDS_UI_LICENSE_DICT=[
            {
                "name": "write your own license",
                "value": "license_free",
            },
            # version 0
            {
                "name": "Creative Commons CC0 1.0 Universal Public Domain Designation",
                "code": "CC0",
                "href_ja": "https://creativecommons.org/publicdomain/zero/1.0/deed.ja",
                "href_default": "https://creativecommons.org/publicdomain/zero/1.0/",
                "value": "license_12",
                "src": "88x31(0).png",
                "src_pdf": "cc-0.png",
                "href_pdf": "https://creativecommons.org/publicdomain/zero/1.0/"
                "deed.ja",
                "txt": "This work is licensed under a Public Domain Dedication "
                "International License.",
            },
            # version 3.0
            {
                "name": "Creative Commons Attribution 3.0 Unported (CC BY 3.0)",
                "code": "CC BY 3.0",
                "href_ja": "https://creativecommons.org/licenses/by/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by/3.0/",
                "value": "license_6",
                "src": "88x31(1).png",
                "src_pdf": "by.png",
                "href_pdf": "http://creativecommons.org/licenses/by/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                " 3.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-ShareAlike 3.0 Unported "
                "(CC BY-SA 3.0)",
                "code": "CC BY-SA 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-sa/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-sa/3.0/",
                "value": "license_7",
                "src": "88x31(2).png",
                "src_pdf": "by-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-sa/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-ShareAlike 3.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NoDerivs 3.0 Unported (CC BY-ND 3.0)",
                "code": "CC BY-ND 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nd/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nd/3.0/",
                "value": "license_8",
                "src": "88x31(3).png",
                "src_pdf": "by-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nd/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NoDerivatives 3.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial 3.0 Unported"
                " (CC BY-NC 3.0)",
                "code": "CC BY-NC 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc/3.0/",
                "value": "license_9",
                "src": "88x31(4).png",
                "src_pdf": "by-nc.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial 3.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial-ShareAlike 3.0 "
                "Unported (CC BY-NC-SA 3.0)",
                "code": "CC BY-NC-SA 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-sa/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-sa/3.0/",
                "value": "license_10",
                "src": "88x31(5).png",
                "src_pdf": "by-nc-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-sa/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 3.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial-NoDerivs "
                "3.0 Unported (CC BY-NC-ND 3.0)",
                "code": "CC BY-NC-ND 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-nd/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-nd/3.0/",
                "value": "license_11",
                "src": "88x31(6).png",
                "src_pdf": "by-nc-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-nd/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 3.0 International License.",
            },
            # version 4.0
            {
                "name": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
                "code": "CC BY 4.0",
                "href_ja": "https://creativecommons.org/licenses/by/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by/4.0/",
                "value": "license_0",
                "src": "88x31(1).png",
                "src_pdf": "by.png",
                "href_pdf": "http://creativecommons.org/licenses/by/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                " 4.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-ShareAlike 4.0 International "
                "(CC BY-SA 4.0)",
                "code": "CC BY-SA 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-sa/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-sa/4.0/",
                "value": "license_1",
                "src": "88x31(2).png",
                "src_pdf": "by-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-sa/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-ShareAlike 4.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NoDerivatives 4.0 International "
                "(CC BY-ND 4.0)",
                "code": "CC BY-ND 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nd/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nd/4.0/",
                "value": "license_2",
                "src": "88x31(3).png",
                "src_pdf": "by-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nd/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NoDerivatives 4.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial 4.0 International"
                " (CC BY-NC 4.0)",
                "code": "CC BY-NC 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc/4.0/",
                "value": "license_3",
                "src": "88x31(4).png",
                "src_pdf": "by-nc.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial 4.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0"
                " International (CC BY-NC-SA 4.0)",
                "code": "CC BY-NC-SA 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-sa/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
                "value": "license_4",
                "src": "88x31(5).png",
                "src_pdf": "by-nc-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 4.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 "
                "International (CC BY-NC-ND 4.0)",
                "code": "CC BY-NC-ND 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-nd/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
                "value": "license_5",
                "src": "88x31(6).png",
                "src_pdf": "by-nc-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-nd/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 4.0 International License.",
            },
        ],
    )
    item_types_data = {
        "1": {
            "item_type_id": "1",
            "name": "テストアイテムタイプ",
            "root_url": "https://localhost:8443/",
            "jsonschema": "items/jsonschema/1",
            "keys": [],
            "labels": [],
            "recids": [1],
            "data": {},
        }
    }
    item_type_id = 1
    list_item_role = {"1": {"weko_creator_id": "1", "weko_shared_id": -1}}

    with app.test_request_context():
        assert make_stats_file(item_type_id, [1], list_item_role) == ([['#.id', '.uri', '.metadata.path[0]', '.pos_index[0]', '.publish_status', '.feedback_mail[0]', '.request_mail[0]', '.cnri', '.doi_ra', '.doi', '.edit_mode', '.metadata.pubdate', '.metadata.item_1617186331708[0].subitem_1551255647225', '.metadata.item_1617186331708[0].subitem_1551255648112', '.metadata.item_1617186385884[0].subitem_1551255720400', '.metadata.item_1617186385884[0].subitem_1551255721061', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifier', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierScheme', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierURI', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNames[0].affiliationName', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNames[0].affiliationNameLang', '.metadata.item_1617186419668[0].creatorAlternatives[0].creatorAlternative', '.metadata.item_1617186419668[0].creatorAlternatives[0].creatorAlternativeLang', '.metadata.item_1617186419668[0].creatorMails[0].creatorMail', '.metadata.item_1617186419668[0].creatorNames[0].creatorName', '.metadata.item_1617186419668[0].creatorNames[0].creatorNameLang', '.metadata.item_1617186419668[0].familyNames[0].familyName', '.metadata.item_1617186419668[0].familyNames[0].familyNameLang', '.metadata.item_1617186419668[0].givenNames[0].givenName', '.metadata.item_1617186419668[0].givenNames[0].givenNameLang', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationNameIdentifier', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationScheme', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationURI', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationName', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationNameLang', '.metadata.item_1617349709064[0].contributorAlternatives[0].contributorAlternative', '.metadata.item_1617349709064[0].contributorAlternatives[0].contributorAlternativeLang', '.metadata.item_1617349709064[0].contributorMails[0].contributorMail', '.metadata.item_1617349709064[0].contributorNames[0].contributorName', '.metadata.item_1617349709064[0].contributorNames[0].lang', '.metadata.item_1617349709064[0].contributorType', '.metadata.item_1617349709064[0].familyNames[0].familyName', '.metadata.item_1617349709064[0].familyNames[0].familyNameLang', '.metadata.item_1617349709064[0].givenNames[0].givenName', '.metadata.item_1617349709064[0].givenNames[0].givenNameLang', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617186476635.subitem_1522299639480', '.metadata.item_1617186476635.subitem_1600958577026', '.metadata.item_1617351524846.subitem_1523260933860', '.metadata.item_1617186499011[0].subitem_1522650717957', '.metadata.item_1617186499011[0].subitem_1522650727486', '.metadata.item_1617186499011[0].subitem_1522651041219', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617610673286[0].rightHolderNames[0].rightHolderLanguage', '.metadata.item_1617610673286[0].rightHolderNames[0].rightHolderName', '.metadata.item_1617186609386[0].subitem_1522299896455', '.metadata.item_1617186609386[0].subitem_1522300014469', '.metadata.item_1617186609386[0].subitem_1522300048512', '.metadata.item_1617186609386[0].subitem_1523261968819', '.metadata.item_1617186626617[0].subitem_description', '.metadata.item_1617186626617[0].subitem_description_language', '.metadata.item_1617186626617[0].subitem_description_type', '.metadata.item_1617186643794[0].subitem_1522300295150', '.metadata.item_1617186643794[0].subitem_1522300316516', '.metadata.item_1617186660861[0].subitem_1522300695726', '.metadata.item_1617186660861[0].subitem_1522300722591', '.metadata.item_1617186702042[0].subitem_1551255818386', '.metadata.item_1617258105262.resourcetype', '.metadata.item_1617258105262.resourceuri', '.metadata.item_1617349808926.subitem_1523263171732', '.metadata.item_1617265215918.subitem_1522305645492', '.metadata.item_1617265215918.subitem_1600292170262', '.metadata.item_1617186783814[0].subitem_identifier_type', '.metadata.item_1617186783814[0].subitem_identifier_uri', '.metadata.item_1617186819068.subitem_identifier_reg_text', '.metadata.item_1617186819068.subitem_identifier_reg_type', '.metadata.item_1617353299429[0].subitem_1522306207484', '.metadata.item_1617353299429[0].subitem_1522306287251.subitem_1522306382014', '.metadata.item_1617353299429[0].subitem_1522306287251.subitem_1522306436033', '.metadata.item_1617353299429[0].subitem_1523320863692[0].subitem_1523320867455', '.metadata.item_1617353299429[0].subitem_1523320863692[0].subitem_1523320909613', '.metadata.item_1617186859717[0].subitem_1522658018441', '.metadata.item_1617186859717[0].subitem_1522658031721', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_east_longitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_north_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_south_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_west_longitude', '.metadata.item_1617186882738[0].subitem_geolocation_place[0].subitem_geolocation_place_text', '.metadata.item_1617186882738[0].subitem_geolocation_point.subitem_point_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_point.subitem_point_longitude', '.metadata.item_1617186901218[0].subitem_1522399143519.subitem_1522399281603', '.metadata.item_1617186901218[0].subitem_1522399143519.subitem_1522399333375', '.metadata.item_1617186901218[0].subitem_1522399412622[0].subitem_1522399416691', '.metadata.item_1617186901218[0].subitem_1522399412622[0].subitem_1522737543681', '.metadata.item_1617186901218[0].subitem_1522399571623.subitem_1522399585738', '.metadata.item_1617186901218[0].subitem_1522399571623.subitem_1522399628911', '.metadata.item_1617186901218[0].subitem_1522399651758[0].subitem_1522721910626', '.metadata.item_1617186901218[0].subitem_1522399651758[0].subitem_1522721929892', '.metadata.item_1617186920753[0].subitem_1522646500366', '.metadata.item_1617186920753[0].subitem_1522646572813', '.metadata.item_1617186941041[0].subitem_1522650068558', '.metadata.item_1617186941041[0].subitem_1522650091861', '.metadata.item_1617186959569.subitem_1551256328147', '.metadata.item_1617186981471.subitem_1551256294723', '.metadata.item_1617186994930.subitem_1551256248092', '.metadata.item_1617187024783.subitem_1551256198917', '.metadata.item_1617187045071.subitem_1551256185532', '.metadata.item_1617187056579.bibliographicIssueDates.bibliographicIssueDate', '.metadata.item_1617187056579.bibliographicIssueDates.bibliographicIssueDateType', '.metadata.item_1617187056579.bibliographicIssueNumber', '.metadata.item_1617187056579.bibliographicNumberOfPages', '.metadata.item_1617187056579.bibliographicPageEnd', '.metadata.item_1617187056579.bibliographicPageStart', '.metadata.item_1617187056579.bibliographicVolumeNumber', '.metadata.item_1617187056579.bibliographic_titles[0].bibliographic_title', '.metadata.item_1617187056579.bibliographic_titles[0].bibliographic_titleLang', '.metadata.item_1617187087799.subitem_1551256171004', '.metadata.item_1617187112279[0].subitem_1551256126428', '.metadata.item_1617187112279[0].subitem_1551256129013', '.metadata.item_1617187136212.subitem_1551256096004', '.metadata.item_1617944105607[0].subitem_1551256015892[0].subitem_1551256027296', '.metadata.item_1617944105607[0].subitem_1551256015892[0].subitem_1551256029891', '.metadata.item_1617944105607[0].subitem_1551256037922[0].subitem_1551256042287', '.metadata.item_1617944105607[0].subitem_1551256037922[0].subitem_1551256047619', '.metadata.item_1617187187528[0].subitem_1599711633003[0].subitem_1599711636923', '.metadata.item_1617187187528[0].subitem_1599711633003[0].subitem_1599711645590', '.metadata.item_1617187187528[0].subitem_1599711655652', '.metadata.item_1617187187528[0].subitem_1599711660052[0].subitem_1599711680082', '.metadata.item_1617187187528[0].subitem_1599711660052[0].subitem_1599711686511', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711704251', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711712451', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711727603', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711731891', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711735410', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711739022', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711743722', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711745532', '.metadata.item_1617187187528[0].subitem_1599711758470[0].subitem_1599711769260', '.metadata.item_1617187187528[0].subitem_1599711758470[0].subitem_1599711775943', '.metadata.item_1617187187528[0].subitem_1599711788485[0].subitem_1599711798761', '.metadata.item_1617187187528[0].subitem_1599711788485[0].subitem_1599711803382', '.metadata.item_1617187187528[0].subitem_1599711813532', '.file_path[0]', '.metadata.item_1617605131499[0].accessrole', '.metadata.item_1617605131499[0].date[0].dateType', '.metadata.item_1617605131499[0].date[0].dateValue', '.metadata.item_1617605131499[0].displaytype', '.metadata.item_1617605131499[0].fileDate[0].fileDateType', '.metadata.item_1617605131499[0].fileDate[0].fileDateValue', '.metadata.item_1617605131499[0].filename', '.metadata.item_1617605131499[0].filesize[0].value', '.metadata.item_1617605131499[0].format', '.metadata.item_1617605131499[0].groups', '.metadata.item_1617605131499[0].licensefree', '.metadata.item_1617605131499[0].licensetype', '.metadata.item_1617605131499[0].url.label', '.metadata.item_1617605131499[0].url.objectType', '.metadata.item_1617605131499[0].url.url', '.metadata.item_1617605131499[0].version', '.metadata.item_1617620223087[0].subitem_1565671149650', '.metadata.item_1617620223087[0].subitem_1565671169640', '.metadata.item_1617620223087[0].subitem_1565671178623', '.thumbnail_path[0]', '.metadata.item_1662046377046[0].subitem_thumbnail[0].thumbnail_label', '.metadata.item_1662046377046[0].subitem_thumbnail[0].thumbnail_url'], ['#ID', 'URI', '.IndexID[0]', '.POS_INDEX[0]', '.PUBLISH_STATUS', '.FEEDBACK_MAIL[0]', '.REQUEST_MAIL[0]', '.CNRI', '.DOI_RA', '.DOI', 'Keep/Upgrade Version', 'PubDate', 'Title[0].Title', 'Title[0].Language', 'Alternative Title[0].Alternative Title', 'Alternative Title[0].Language', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子URI', 'Creator[0].作成者所属[0].所属機関名[0].所属機関名', 'Creator[0].作成者所属[0].所属機関名[0].言語', 'Creator[0].作成者別名[0].別名', 'Creator[0].作成者別名[0].言語', 'Creator[0].作成者メールアドレス[0].メールアドレス', 'Creator[0].作成者姓名[0].姓名', 'Creator[0].作成者姓名[0].言語', 'Creator[0].作成者姓[0].姓', 'Creator[0].作成者姓[0].言語', 'Creator[0].作成者名[0].名', 'Creator[0].作成者名[0].言語', 'Creator[0].作成者識別子[0].作成者識別子', 'Creator[0].作成者識別子[0].作成者識別子Scheme', 'Creator[0].作成者識別子[0].作成者識別子URI', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子URI', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関名', 'Contributor[0].寄与者所属[0].所属機関識別子[0].言語', 'Contributor[0].寄与者別名[0].別名', 'Contributor[0].寄与者別名[0].言語', 'Contributor[0].寄与者メールアドレス[0].メールアドレス', 'Contributor[0].寄与者姓名[0].姓名', 'Contributor[0].寄与者姓名[0].言語', 'Contributor[0].寄与者タイプ', 'Contributor[0].寄与者姓[0].姓', 'Contributor[0].寄与者姓[0].言語', 'Contributor[0].寄与者名[0].名', 'Contributor[0].寄与者名[0].言語', 'Contributor[0].寄与者識別子[0].寄与者識別子', 'Contributor[0].寄与者識別子[0].寄与者識別子Scheme', 'Contributor[0].寄与者識別子[0].寄与者識別子URI', 'Access Rights.アクセス権', 'Access Rights.アクセス権URI', 'APC.APC', 'Rights[0].言語', 'Rights[0].権利情報Resource', 'Rights[0].権利情報', 'Rights Holder[0].権利者識別子[0].権利者識別子', 'Rights Holder[0].権利者識別子[0].権利者識別子Scheme', 'Rights Holder[0].権利者識別子[0].権利者識別子URI', 'Rights Holder[0].権利者名[0].言語', 'Rights Holder[0].権利者名[0].権利者名', 'Subject[0].言語', 'Subject[0].主題Scheme', 'Subject[0].主題URI', 'Subject[0].主題', 'Description[0].内容記述', 'Description[0].言語', 'Description[0].内容記述タイプ', 'Publisher[0].言語', 'Publisher[0].出版者', 'Date[0].日付タイプ', 'Date[0].日付', 'Language[0].Language', 'Resource Type.資源タイプ', 'Resource Type.資源タイプ識別子', 'Version.バージョン情報', 'Version Type.出版タイプ', 'Version Type.出版タイプResource', 'Identifier[0].識別子タイプ', 'Identifier[0].識別子', 'Identifier Registration.ID登録', 'Identifier Registration.ID登録タイプ', 'Relation[0].関連タイプ', 'Relation[0].関連識別子.識別子タイプ', 'Relation[0].関連識別子.関連識別子', 'Relation[0].関連名称[0].言語', 'Relation[0].関連名称[0].関連名称', 'Temporal[0].言語', 'Temporal[0].時間的範囲', 'Geo Location[0].位置情報（空間）.東部経度', 'Geo Location[0].位置情報（空間）.北部緯度', 'Geo Location[0].位置情報（空間）.南部緯度', 'Geo Location[0].位置情報（空間）.西部経度', 'Geo Location[0].位置情報（自由記述）[0].位置情報（自由記述）', 'Geo Location[0].位置情報（点）.緯度', 'Geo Location[0].位置情報（点）.経度', 'Funding Reference[0].助成機関識別子.助成機関識別子タイプ', 'Funding Reference[0].助成機関識別子.助成機関識別子', 'Funding Reference[0].助成機関名[0].言語', 'Funding Reference[0].助成機関名[0].助成機関名', 'Funding Reference[0].研究課題番号.研究課題URI', 'Funding Reference[0].研究課題番号.研究課題番号', 'Funding Reference[0].研究課題名[0].言語', 'Funding Reference[0].研究課題名[0].研究課題名', 'Source Identifier[0].収録物識別子タイプ', 'Source Identifier[0].収録物識別子', 'Source Title[0].言語', 'Source Title[0].収録物名', 'Volume Number.Volume Number', 'Issue Number.Issue Number', 'Number of Pages.Number of Pages', 'Page Start.Page Start', 'Page End.Page End', 'Bibliographic Information.発行日.日付', 'Bibliographic Information.発行日.日付タイプ', 'Bibliographic Information.号', 'Bibliographic Information.ページ数', 'Bibliographic Information.終了ページ', 'Bibliographic Information.開始ページ', 'Bibliographic Information.巻', 'Bibliographic Information.雑誌名[0].タイトル', 'Bibliographic Information.雑誌名[0].言語', 'Dissertation Number.Dissertation Number', 'Degree Name[0].Degree Name', 'Degree Name[0].Language', 'Date Granted.Date Granted', 'Degree Grantor[0].Degree Grantor Name Identifier[0].Degree Grantor Name Identifier', 'Degree Grantor[0].Degree Grantor Name Identifier[0].Degree Grantor Name Identifier Scheme', 'Degree Grantor[0].Degree Grantor Name[0].Degree Grantor Name', 'Degree Grantor[0].Degree Grantor Name[0].Language', 'Conference[0].Conference Name[0].Conference Name', 'Conference[0].Conference Name[0].Language', 'Conference[0].Conference Sequence', 'Conference[0].Conference Sponsor[0].Conference Sponsor', 'Conference[0].Conference Sponsor[0].Language', 'Conference[0].Conference Date.Conference Date', 'Conference[0].Conference Date.Start Day', 'Conference[0].Conference Date.Start Month', 'Conference[0].Conference Date.Start Year', 'Conference[0].Conference Date.End Day', 'Conference[0].Conference Date.End Month', 'Conference[0].Conference Date.End Year', 'Conference[0].Conference Date.Language', 'Conference[0].Conference Venue[0].Conference Venue', 'Conference[0].Conference Venue[0].Language', 'Conference[0].Conference Place[0].Conference Place', 'Conference[0].Conference Place[0].Language', 'Conference[0].Conference Country', '.ファイルパス[0]', 'File[0].アクセス', 'File[0].オープンアクセスの日付[0].日付タイプ', 'File[0].オープンアクセスの日付[0].日付', 'File[0].表示形式', 'File[0].日付[0].日付タイプ', 'File[0].日付[0].日付', 'File[0].表示名', 'File[0].サイズ[0].サイズ', 'File[0].フォーマット', 'File[0].グループ', 'File[0].自由ライセンス', 'File[0].ライセンス', 'File[0].本文URL.ラベル', 'File[0].本文URL.オブジェクトタイプ', 'File[0].本文URL.本文URL', 'File[0].バージョン情報', 'Heading[0].Language', 'Heading[0].Banner Headline', 'Heading[0].Subheading', '.サムネイルパス[0]', 'サムネイル[0].URI[0].ラベル', 'サムネイル[0].URI[0].URI'], ['#', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', '', '', 'System', '', '', 'System', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', 'System'], ['#', '', 'Allow Multiple', 'Allow Multiple', 'Required', 'Allow Multiple', 'Allow Multiple', '', '', '', 'Required', 'Required', 'Required, Allow Multiple', 'Required, Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Required', 'Required', '', '', '', 'Allow Multiple', 'Allow Multiple', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Allow Multiple', 'Allow Multiple', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple']], {1: [1, 'Index(public_state = True,harvest_public_state = True)', 'public', '', '', '', '', '', 'Keep', '2022-08-20', 'title', 'ja', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'conference paper', 'http://purl.org/coar/resource_type/c_5794', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']})

    with app.test_request_context():
        assert make_stats_file(item_type_id, [1,2,3], list_item_role) == ([['#.id', '.uri', '.metadata.path[0]', '.pos_index[0]', '.publish_status', '.feedback_mail[0]', '.request_mail[0]', '.cnri', '.doi_ra', '.doi', '.edit_mode', '.metadata.pubdate', '.metadata.item_1617186331708[0].subitem_1551255647225', '.metadata.item_1617186331708[0].subitem_1551255648112', '.metadata.item_1617186385884[0].subitem_1551255720400', '.metadata.item_1617186385884[0].subitem_1551255721061', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifier', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierScheme', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierURI', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNames[0].affiliationName', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNames[0].affiliationNameLang', '.metadata.item_1617186419668[0].creatorAlternatives[0].creatorAlternative', '.metadata.item_1617186419668[0].creatorAlternatives[0].creatorAlternativeLang', '.metadata.item_1617186419668[0].creatorMails[0].creatorMail', '.metadata.item_1617186419668[0].creatorNames[0].creatorName', '.metadata.item_1617186419668[0].creatorNames[0].creatorNameLang', '.metadata.item_1617186419668[0].familyNames[0].familyName', '.metadata.item_1617186419668[0].familyNames[0].familyNameLang', '.metadata.item_1617186419668[0].givenNames[0].givenName', '.metadata.item_1617186419668[0].givenNames[0].givenNameLang', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationNameIdentifier', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationScheme', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationURI', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationName', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationNameLang', '.metadata.item_1617349709064[0].contributorAlternatives[0].contributorAlternative', '.metadata.item_1617349709064[0].contributorAlternatives[0].contributorAlternativeLang', '.metadata.item_1617349709064[0].contributorMails[0].contributorMail', '.metadata.item_1617349709064[0].contributorNames[0].contributorName', '.metadata.item_1617349709064[0].contributorNames[0].lang', '.metadata.item_1617349709064[0].contributorType', '.metadata.item_1617349709064[0].familyNames[0].familyName', '.metadata.item_1617349709064[0].familyNames[0].familyNameLang', '.metadata.item_1617349709064[0].givenNames[0].givenName', '.metadata.item_1617349709064[0].givenNames[0].givenNameLang', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617186476635.subitem_1522299639480', '.metadata.item_1617186476635.subitem_1600958577026', '.metadata.item_1617351524846.subitem_1523260933860', '.metadata.item_1617186499011[0].subitem_1522650717957', '.metadata.item_1617186499011[0].subitem_1522650727486', '.metadata.item_1617186499011[0].subitem_1522651041219', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617610673286[0].rightHolderNames[0].rightHolderLanguage', '.metadata.item_1617610673286[0].rightHolderNames[0].rightHolderName', '.metadata.item_1617186609386[0].subitem_1522299896455', '.metadata.item_1617186609386[0].subitem_1522300014469', '.metadata.item_1617186609386[0].subitem_1522300048512', '.metadata.item_1617186609386[0].subitem_1523261968819', '.metadata.item_1617186626617[0].subitem_description', '.metadata.item_1617186626617[0].subitem_description_language', '.metadata.item_1617186626617[0].subitem_description_type', '.metadata.item_1617186643794[0].subitem_1522300295150', '.metadata.item_1617186643794[0].subitem_1522300316516', '.metadata.item_1617186660861[0].subitem_1522300695726', '.metadata.item_1617186660861[0].subitem_1522300722591', '.metadata.item_1617186702042[0].subitem_1551255818386', '.metadata.item_1617258105262.resourcetype', '.metadata.item_1617258105262.resourceuri', '.metadata.item_1617349808926.subitem_1523263171732', '.metadata.item_1617265215918.subitem_1522305645492', '.metadata.item_1617265215918.subitem_1600292170262', '.metadata.item_1617186783814[0].subitem_identifier_type', '.metadata.item_1617186783814[0].subitem_identifier_uri', '.metadata.item_1617186819068.subitem_identifier_reg_text', '.metadata.item_1617186819068.subitem_identifier_reg_type', '.metadata.item_1617353299429[0].subitem_1522306207484', '.metadata.item_1617353299429[0].subitem_1522306287251.subitem_1522306382014', '.metadata.item_1617353299429[0].subitem_1522306287251.subitem_1522306436033', '.metadata.item_1617353299429[0].subitem_1523320863692[0].subitem_1523320867455', '.metadata.item_1617353299429[0].subitem_1523320863692[0].subitem_1523320909613', '.metadata.item_1617186859717[0].subitem_1522658018441', '.metadata.item_1617186859717[0].subitem_1522658031721', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_east_longitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_north_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_south_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_west_longitude', '.metadata.item_1617186882738[0].subitem_geolocation_place[0].subitem_geolocation_place_text', '.metadata.item_1617186882738[0].subitem_geolocation_point.subitem_point_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_point.subitem_point_longitude', '.metadata.item_1617186901218[0].subitem_1522399143519.subitem_1522399281603', '.metadata.item_1617186901218[0].subitem_1522399143519.subitem_1522399333375', '.metadata.item_1617186901218[0].subitem_1522399412622[0].subitem_1522399416691', '.metadata.item_1617186901218[0].subitem_1522399412622[0].subitem_1522737543681', '.metadata.item_1617186901218[0].subitem_1522399571623.subitem_1522399585738', '.metadata.item_1617186901218[0].subitem_1522399571623.subitem_1522399628911', '.metadata.item_1617186901218[0].subitem_1522399651758[0].subitem_1522721910626', '.metadata.item_1617186901218[0].subitem_1522399651758[0].subitem_1522721929892', '.metadata.item_1617186920753[0].subitem_1522646500366', '.metadata.item_1617186920753[0].subitem_1522646572813', '.metadata.item_1617186941041[0].subitem_1522650068558', '.metadata.item_1617186941041[0].subitem_1522650091861', '.metadata.item_1617186959569.subitem_1551256328147', '.metadata.item_1617186981471.subitem_1551256294723', '.metadata.item_1617186994930.subitem_1551256248092', '.metadata.item_1617187024783.subitem_1551256198917', '.metadata.item_1617187045071.subitem_1551256185532', '.metadata.item_1617187056579.bibliographicIssueDates.bibliographicIssueDate', '.metadata.item_1617187056579.bibliographicIssueDates.bibliographicIssueDateType', '.metadata.item_1617187056579.bibliographicIssueNumber', '.metadata.item_1617187056579.bibliographicNumberOfPages', '.metadata.item_1617187056579.bibliographicPageEnd', '.metadata.item_1617187056579.bibliographicPageStart', '.metadata.item_1617187056579.bibliographicVolumeNumber', '.metadata.item_1617187056579.bibliographic_titles[0].bibliographic_title', '.metadata.item_1617187056579.bibliographic_titles[0].bibliographic_titleLang', '.metadata.item_1617187087799.subitem_1551256171004', '.metadata.item_1617187112279[0].subitem_1551256126428', '.metadata.item_1617187112279[0].subitem_1551256129013', '.metadata.item_1617187136212.subitem_1551256096004', '.metadata.item_1617944105607[0].subitem_1551256015892[0].subitem_1551256027296', '.metadata.item_1617944105607[0].subitem_1551256015892[0].subitem_1551256029891', '.metadata.item_1617944105607[0].subitem_1551256037922[0].subitem_1551256042287', '.metadata.item_1617944105607[0].subitem_1551256037922[0].subitem_1551256047619', '.metadata.item_1617187187528[0].subitem_1599711633003[0].subitem_1599711636923', '.metadata.item_1617187187528[0].subitem_1599711633003[0].subitem_1599711645590', '.metadata.item_1617187187528[0].subitem_1599711655652', '.metadata.item_1617187187528[0].subitem_1599711660052[0].subitem_1599711680082', '.metadata.item_1617187187528[0].subitem_1599711660052[0].subitem_1599711686511', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711704251', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711712451', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711727603', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711731891', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711735410', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711739022', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711743722', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711745532', '.metadata.item_1617187187528[0].subitem_1599711758470[0].subitem_1599711769260', '.metadata.item_1617187187528[0].subitem_1599711758470[0].subitem_1599711775943', '.metadata.item_1617187187528[0].subitem_1599711788485[0].subitem_1599711798761', '.metadata.item_1617187187528[0].subitem_1599711788485[0].subitem_1599711803382', '.metadata.item_1617187187528[0].subitem_1599711813532', '.file_path[0]', '.metadata.item_1617605131499[0].accessrole', '.metadata.item_1617605131499[0].date[0].dateType', '.metadata.item_1617605131499[0].date[0].dateValue', '.metadata.item_1617605131499[0].displaytype', '.metadata.item_1617605131499[0].fileDate[0].fileDateType', '.metadata.item_1617605131499[0].fileDate[0].fileDateValue', '.metadata.item_1617605131499[0].filename', '.metadata.item_1617605131499[0].filesize[0].value', '.metadata.item_1617605131499[0].format', '.metadata.item_1617605131499[0].groups', '.metadata.item_1617605131499[0].licensefree', '.metadata.item_1617605131499[0].licensetype', '.metadata.item_1617605131499[0].url.label', '.metadata.item_1617605131499[0].url.objectType', '.metadata.item_1617605131499[0].url.url', '.metadata.item_1617605131499[0].version', '.metadata.item_1617620223087[0].subitem_1565671149650', '.metadata.item_1617620223087[0].subitem_1565671169640', '.metadata.item_1617620223087[0].subitem_1565671178623', '.thumbnail_path[0]', '.metadata.item_1662046377046[0].subitem_thumbnail[0].thumbnail_label', '.metadata.item_1662046377046[0].subitem_thumbnail[0].thumbnail_url'], ['#ID', 'URI', '.IndexID[0]', '.POS_INDEX[0]', '.PUBLISH_STATUS', '.FEEDBACK_MAIL[0]', '.REQUEST_MAIL[0]', '.CNRI', '.DOI_RA', '.DOI', 'Keep/Upgrade Version', 'PubDate', 'Title[0].Title', 'Title[0].Language', 'Alternative Title[0].Alternative Title', 'Alternative Title[0].Language', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子URI', 'Creator[0].作成者所属[0].所属機関名[0].所属機関名', 'Creator[0].作成者所属[0].所属機関名[0].言語', 'Creator[0].作成者別名[0].別名', 'Creator[0].作成者別名[0].言語', 'Creator[0].作成者メールアドレス[0].メールアドレス', 'Creator[0].作成者姓名[0].姓名', 'Creator[0].作成者姓名[0].言語', 'Creator[0].作成者姓[0].姓', 'Creator[0].作成者姓[0].言語', 'Creator[0].作成者名[0].名', 'Creator[0].作成者名[0].言語', 'Creator[0].作成者識別子[0].作成者識別子', 'Creator[0].作成者識別子[0].作成者識別子Scheme', 'Creator[0].作成者識別子[0].作成者識別子URI', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子URI', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関名', 'Contributor[0].寄与者所属[0].所属機関識別子[0].言語', 'Contributor[0].寄与者別名[0].別名', 'Contributor[0].寄与者別名[0].言語', 'Contributor[0].寄与者メールアドレス[0].メールアドレス', 'Contributor[0].寄与者姓名[0].姓名', 'Contributor[0].寄与者姓名[0].言語', 'Contributor[0].寄与者タイプ', 'Contributor[0].寄与者姓[0].姓', 'Contributor[0].寄与者姓[0].言語', 'Contributor[0].寄与者名[0].名', 'Contributor[0].寄与者名[0].言語', 'Contributor[0].寄与者識別子[0].寄与者識別子', 'Contributor[0].寄与者識別子[0].寄与者識別子Scheme', 'Contributor[0].寄与者識別子[0].寄与者識別子URI', 'Access Rights.アクセス権', 'Access Rights.アクセス権URI', 'APC.APC', 'Rights[0].言語', 'Rights[0].権利情報Resource', 'Rights[0].権利情報', 'Rights Holder[0].権利者識別子[0].権利者識別子', 'Rights Holder[0].権利者識別子[0].権利者識別子Scheme', 'Rights Holder[0].権利者識別子[0].権利者識別子URI', 'Rights Holder[0].権利者名[0].言語', 'Rights Holder[0].権利者名[0].権利者名', 'Subject[0].言語', 'Subject[0].主題Scheme', 'Subject[0].主題URI', 'Subject[0].主題', 'Description[0].内容記述', 'Description[0].言語', 'Description[0].内容記述タイプ', 'Publisher[0].言語', 'Publisher[0].出版者', 'Date[0].日付タイプ', 'Date[0].日付', 'Language[0].Language', 'Resource Type.資源タイプ', 'Resource Type.資源タイプ識別子', 'Version.バージョン情報', 'Version Type.出版タイプ', 'Version Type.出版タイプResource', 'Identifier[0].識別子タイプ', 'Identifier[0].識別子', 'Identifier Registration.ID登録', 'Identifier Registration.ID登録タイプ', 'Relation[0].関連タイプ', 'Relation[0].関連識別子.識別子タイプ', 'Relation[0].関連識別子.関連識別子', 'Relation[0].関連名称[0].言語', 'Relation[0].関連名称[0].関連名称', 'Temporal[0].言語', 'Temporal[0].時間的範囲', 'Geo Location[0].位置情報（空間）.東部経度', 'Geo Location[0].位置情報（空間）.北部緯度', 'Geo Location[0].位置情報（空間）.南部緯度', 'Geo Location[0].位置情報（空間）.西部経度', 'Geo Location[0].位置情報（自由記述）[0].位置情報（自由記述）', 'Geo Location[0].位置情報（点）.緯度', 'Geo Location[0].位置情報（点）.経度', 'Funding Reference[0].助成機関識別子.助成機関識別子タイプ', 'Funding Reference[0].助成機関識別子.助成機関識別子', 'Funding Reference[0].助成機関名[0].言語', 'Funding Reference[0].助成機関名[0].助成機関名', 'Funding Reference[0].研究課題番号.研究課題URI', 'Funding Reference[0].研究課題番号.研究課題番号', 'Funding Reference[0].研究課題名[0].言語', 'Funding Reference[0].研究課題名[0].研究課題名', 'Source Identifier[0].収録物識別子タイプ', 'Source Identifier[0].収録物識別子', 'Source Title[0].言語', 'Source Title[0].収録物名', 'Volume Number.Volume Number', 'Issue Number.Issue Number', 'Number of Pages.Number of Pages', 'Page Start.Page Start', 'Page End.Page End', 'Bibliographic Information.発行日.日付', 'Bibliographic Information.発行日.日付タイプ', 'Bibliographic Information.号', 'Bibliographic Information.ページ数', 'Bibliographic Information.終了ページ', 'Bibliographic Information.開始ページ', 'Bibliographic Information.巻', 'Bibliographic Information.雑誌名[0].タイトル', 'Bibliographic Information.雑誌名[0].言語', 'Dissertation Number.Dissertation Number', 'Degree Name[0].Degree Name', 'Degree Name[0].Language', 'Date Granted.Date Granted', 'Degree Grantor[0].Degree Grantor Name Identifier[0].Degree Grantor Name Identifier', 'Degree Grantor[0].Degree Grantor Name Identifier[0].Degree Grantor Name Identifier Scheme', 'Degree Grantor[0].Degree Grantor Name[0].Degree Grantor Name', 'Degree Grantor[0].Degree Grantor Name[0].Language', 'Conference[0].Conference Name[0].Conference Name', 'Conference[0].Conference Name[0].Language', 'Conference[0].Conference Sequence', 'Conference[0].Conference Sponsor[0].Conference Sponsor', 'Conference[0].Conference Sponsor[0].Language', 'Conference[0].Conference Date.Conference Date', 'Conference[0].Conference Date.Start Day', 'Conference[0].Conference Date.Start Month', 'Conference[0].Conference Date.Start Year', 'Conference[0].Conference Date.End Day', 'Conference[0].Conference Date.End Month', 'Conference[0].Conference Date.End Year', 'Conference[0].Conference Date.Language', 'Conference[0].Conference Venue[0].Conference Venue', 'Conference[0].Conference Venue[0].Language', 'Conference[0].Conference Place[0].Conference Place', 'Conference[0].Conference Place[0].Language', 'Conference[0].Conference Country', '.ファイルパス[0]', 'File[0].アクセス', 'File[0].オープンアクセスの日付[0].日付タイプ', 'File[0].オープンアクセスの日付[0].日付', 'File[0].表示形式', 'File[0].日付[0].日付タイプ', 'File[0].日付[0].日付', 'File[0].表示名', 'File[0].サイズ[0].サイズ', 'File[0].フォーマット', 'File[0].グループ', 'File[0].自由ライセンス', 'File[0].ライセンス', 'File[0].本文URL.ラベル', 'File[0].本文URL.オブジェクトタイプ', 'File[0].本文URL.本文URL', 'File[0].バージョン情報', 'Heading[0].Language', 'Heading[0].Banner Headline', 'Heading[0].Subheading', '.サムネイルパス[0]', 'サムネイル[0].URI[0].ラベル', 'サムネイル[0].URI[0].URI'], ['#', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', '', '', 'System', '', '', 'System', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', 'System'], ['#', '', 'Allow Multiple', 'Allow Multiple', 'Required', 'Allow Multiple', 'Allow Multiple', '', '', '', 'Required', 'Required', 'Required, Allow Multiple', 'Required, Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Required', 'Required', '', '', '', 'Allow Multiple', 'Allow Multiple', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Allow Multiple', 'Allow Multiple', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple']], {1: [1, 'Index(public_state = True,harvest_public_state = True)', 'public', '', '', '', '', '', 'Keep', '2022-08-20', 'title', 'ja', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'conference paper', 'http://purl.org/coar/resource_type/c_5794', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''], 2: [2, 'Index(public_state = True,harvest_public_state = False)', 'private', '', '', '', '', '', 'Keep', '2022-08-20', 'title2', 'ja', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'conference paper', 'http://purl.org/coar/resource_type/c_5794', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''], 3: [2, 'Index(public_state = True,harvest_public_state = False)', 'public', '', '', '', '', '', 'Keep', '2022-08-20', 'title2', 'ja', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'conference paper', 'http://purl.org/coar/resource_type/c_5794', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']})

    itemtype = ItemTypes.get_by_id(item_type_id)
    meta_list = itemtype.render.get("meta_list")

    with app.test_request_context():
        login_user(users[2]["obj"])
        with patch("weko_items_ui.utils.get_item_from_option", return_value = meta_list.keys()):
            make_stats_file(item_type_id, [1,2,3], list_item_role)

        p = PersistentIdentifier.query.filter_by(id=1).first()
        with patch("weko_deposit.api.WekoRecord._get_pid", return_value = p):
            make_stats_file(item_type_id, [1,2,3], list_item_role)

        with patch("weko_workflow.utils.IdentifierHandle.get_idt_registration_data") as g:
            for i in range(len(app.config["WEKO_IMPORT_DOI_TYPE"])):
                g.return_value = ([app.config["IDENTIFIER_GRANT_LIST"][i+1][2]],[app.config["WEKO_IMPORT_DOI_TYPE"][i]])
                make_stats_file(item_type_id, [1,2,3], list_item_role)

        item_type_id = 2
        list_item_role = {"2": {"weko_creator_id": "1", "weko_shared_id": -1}}
        itemtype = ItemTypes.get_by_id(item_type_id)
        rec = WekoRecord.get_record_by_pid(8)
        meta_list = itemtype.render.get("meta_list")
        for meta in meta_list.keys():
            if meta == "item_1568286510993" :
                meta_list[meta]["option"]["hidden"] = False
                meta_list[meta]["option"]["multiple"] = True

        i = 0
        for key, v in sorted(itemtype.render["table_row_map"]["schema"]["properties"].items()):
            if v["type"] == "array":
                v["items"]["properties"]["subitem_1234567890123"] = {
                    "format": "checkboxes",
                    "title": "sample"
                }
                i += 1
                if i > 1: break

        with patch("weko_items_ui.utils.get_sub_item_option", return_value = "Hide"):
            with app.test_request_context():
                make_stats_file(item_type_id, [7,8], list_item_role)

    with patch("weko_items_ui.utils.RequestMailList.get_mail_list_by_item_id",return_value = [{"email":"contributor@test.org","author_id":""},{"email":"user@test.org","author_id":""}]):
        with patch("weko_items_ui.utils.check_created_id", return_value=True):
            with app.test_request_context():
                assert make_stats_file(item_type_id, [7,8], list_item_role) == ([['#.id', '.uri', '.metadata.path[0]', '.pos_index[0]', '.publish_status', '.feedback_mail[0]', '.request_mail[0]', '.request_mail[1]', '.cnri', '.doi_ra', '.doi', '.edit_mode', '.metadata.pubdate', '.metadata.item_1554883918421.subitem_1551255647225', '.metadata.item_1554883918421.subitem_1551255648112', '.metadata.item_1554883961001.subitem_1551255818386', '.metadata.item_1554884042490.subitem_1522299896455', '.metadata.item_1554884042490.subitem_1522300014469', '.metadata.item_1554884042490.subitem_1522300048512', '.metadata.item_1554884042490.subitem_1523261968819', '.metadata.item_1532070986701.creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifier', '.metadata.item_1532070986701.creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierScheme', '.metadata.item_1532070986701.creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierURI', '.metadata.item_1532070986701.creatorAffiliations[0].affiliationNames[0].affiliationName', '.metadata.item_1532070986701.creatorAffiliations[0].affiliationNames[0].affiliationNameLang', '.metadata.item_1532070986701.creatorAlternatives[0].creatorAlternative', '.metadata.item_1532070986701.creatorAlternatives[0].creatorAlternativeLang', '.metadata.item_1532070986701.creatorMails[0].creatorMail', '.metadata.item_1532070986701.creatorNames[0].creatorName', '.metadata.item_1532070986701.creatorNames[0].creatorNameLang', '.metadata.item_1532070986701.familyNames[0].familyName', '.metadata.item_1532070986701.familyNames[0].familyNameLang', '.metadata.item_1532070986701.givenNames[0].givenName', '.metadata.item_1532070986701.givenNames[0].givenNameLang', '.metadata.item_1532070986701.nameIdentifiers[0].nameIdentifier', '.metadata.item_1532070986701.nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1532070986701.nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1532071014836.contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationNameIdentifier', '.metadata.item_1532071014836.contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationScheme', '.metadata.item_1532071014836.contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationURI', '.metadata.item_1532071014836.contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationName', '.metadata.item_1532071014836.contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationNameLang', '.metadata.item_1532071014836.contributorAlternatives[0].contributorAlternative', '.metadata.item_1532071014836.contributorAlternatives[0].contributorAlternativeLang', '.metadata.item_1532071014836.contributorMails[0].contributorMail', '.metadata.item_1532071014836.contributorNames[0].contributorName', '.metadata.item_1532071014836.contributorNames[0].lang', '.metadata.item_1532071014836.contributorType', '.metadata.item_1532071014836.familyNames[0].familyName', '.metadata.item_1532071014836.familyNames[0].familyNameLang', '.metadata.item_1532071014836.givenNames[0].givenName', '.metadata.item_1532071014836.givenNames[0].givenNameLang', '.metadata.item_1532071014836.nameIdentifiers[0].nameIdentifier', '.metadata.item_1532071014836.nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1532071014836.nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1532071031458.subitem_1522299639480', '.metadata.item_1532071031458.subitem_1600958577026', '.metadata.item_1532071039842[0].subitem_1234567890123[0]', '.metadata.item_1532071039842[0].subitem_1522650717957', '.metadata.item_1532071039842[0].subitem_1522650727486', '.metadata.item_1532071039842[0].subitem_1522651041219', '.metadata.item_1532071057095[0].subitem_1234567890123[0]', '.metadata.item_1532071057095[0].subitem_1522299896455', '.metadata.item_1532071057095[0].subitem_1522300014469', '.metadata.item_1532071057095[0].subitem_1522300048512', '.metadata.item_1532071057095[0].subitem_1523261968819', '.metadata.item_1532071068215[0].subitem_1522657647525', '.metadata.item_1532071068215[0].subitem_1522657697257', '.metadata.item_1532071068215[0].subitem_1523262169140', '.metadata.item_1532071093517[0].subitem_1522300295150', '.metadata.item_1532071093517[0].subitem_1522300316516', '.metadata.item_1532071103206[0].subitem_1522300695726', '.metadata.item_1532071103206[0].subitem_1522300722591', '.metadata.item_1569380622649.resourcetype', '.metadata.item_1569380622649.resourceuri', '.metadata.item_1581493352241.subitem_1569224170590', '.metadata.item_1581493352241.subitem_1569224172438', '.metadata.item_1532071133483', '.metadata.item_1532071158138[0].subitem_1522306207484', '.metadata.item_1532071158138[0].subitem_1522306287251.subitem_1522306382014', '.metadata.item_1532071158138[0].subitem_1522306287251.subitem_1522306436033', '.metadata.item_1532071158138[0].subitem_1523320863692[0].subitem_1523320867455', '.metadata.item_1532071158138[0].subitem_1523320863692[0].subitem_1523320909613', '.metadata.item_1532071168802[0].subitem_1522658018441', '.metadata.item_1532071168802[0].subitem_1522658031721', '.metadata.item_1532071184504[0].subitem_1522658250154.subitem_1522658252485', '.metadata.item_1532071184504[0].subitem_1522658250154.subitem_1522658264346', '.metadata.item_1532071184504[0].subitem_1522658250154.subitem_1522658270105', '.metadata.item_1532071184504[0].subitem_1522658250154.subitem_1522658274386', '.metadata.item_1532071184504[0].subitem_1523321394401.subitem_1523321400758', '.metadata.item_1532071184504[0].subitem_1523321394401.subitem_1523321450098', '.metadata.item_1532071184504[0].subitem_1523321527273', '.metadata.item_1532071200841[0].subitem_1522399143519.subitem_1522399281603', '.metadata.item_1532071200841[0].subitem_1522399143519.subitem_1522399333375', '.metadata.item_1532071200841[0].subitem_1522399412622[0].subitem_1522399416691', '.metadata.item_1532071200841[0].subitem_1522399412622[0].subitem_1522737543681', '.metadata.item_1532071200841[0].subitem_1522399571623.subitem_1522399585738', '.metadata.item_1532071200841[0].subitem_1522399571623.subitem_1522399628911', '.metadata.item_1532071200841[0].subitem_1522399651758[0].subitem_1522721910626', '.metadata.item_1532071200841[0].subitem_1522399651758[0].subitem_1522721929892', '.metadata.item_1532071216312[0].subitem_1522652546580.subitem_1522652548920', '.metadata.item_1532071216312[0].subitem_1522652546580.subitem_1522652672693', '.metadata.item_1532071216312[0].subitem_1522652546580.subitem_1522652685531', '.metadata.item_1532071216312[0].subitem_1522652734962', '.metadata.item_1532071216312[0].subitem_1522652740098[0].subitem_1522722119299', '.metadata.item_1532071216312[0].subitem_1522652747880[0].subitem_1522722132466', '.metadata.item_1532071216312[0].subitem_1522652747880[0].subitem_1522739295711', '.metadata.item_1532071216312[0].subitem_1523325300505', '.thumbnail_path', '.metadata.item_1568286510993.subitem_thumbnail[0].thumbnail_label', '.metadata.item_1568286510993.subitem_thumbnail[0].thumbnail_url', '.file_path[0]', '.metadata.item_1600165182071[0].accessrole', '.metadata.item_1600165182071[0].date[0].dateType', '.metadata.item_1600165182071[0].date[0].dateValue', '.metadata.item_1600165182071[0].displaytype', '.metadata.item_1600165182071[0].filename', '.metadata.item_1600165182071[0].filesize[0].value', '.metadata.item_1600165182071[0].format', '.metadata.item_1600165182071[0].groupsprice[0].group', '.metadata.item_1600165182071[0].groupsprice[0].price', '.metadata.item_1600165182071[0].is_billing', '.metadata.item_1600165182071[0].licensefree', '.metadata.item_1600165182071[0].licensetype', '.metadata.item_1600165182071[0].url.label', '.metadata.item_1600165182071[0].url.objectType', '.metadata.item_1600165182071[0].url.url', '.metadata.item_1600165182071[0].version'], ['#ID', 'URI', '.IndexID[0]', '.POS_INDEX[0]', '.PUBLISH_STATUS', '.FEEDBACK_MAIL[0]', '.REQUEST_MAIL[0]', '.REQUEST_MAIL[1]', '.CNRI', '.DOI_RA', '.DOI', 'Keep/Upgrade Version', 'PubDate', 'Title.Title', 'Title.Language', 'Language.Language', 'Keyword.言語', 'Keyword.主題Scheme', 'Keyword.主題URI', 'Keyword.主題', 'Creator.作成者所属[0].所属機関識別子[0].所属機関識別子', 'Creator.作成者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Creator.作成者所属[0].所属機関識別子[0].所属機関識別子URI', 'Creator.作成者所属[0].所属機関名[0].所属機関名', 'Creator.作成者所属[0].所属機関名[0].言語', 'Creator.作成者別名[0].別名', 'Creator.作成者別名[0].言語', 'Creator.作成者メールアドレス[0].メールアドレス', 'Creator.作成者姓名[0].姓名', 'Creator.作成者姓名[0].言語', 'Creator.作成者姓[0].姓', 'Creator.作成者姓[0].言語', 'Creator.作成者名[0].名', 'Creator.作成者名[0].言語', 'Creator.作成者識別子[0].作成者識別子', 'Creator.作成者識別子[0].作成者識別子Scheme', 'Creator.作成者識別子[0].作成者識別子URI', 'Contributor.寄与者所属[0].所属機関識別子[0].所属機関識別子', 'Contributor.寄与者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Contributor.寄与者所属[0].所属機関識別子[0].所属機関識別子URI', 'Contributor.寄与者所属[0].所属機関識別子[0].所属機関名', 'Contributor.寄与者所属[0].所属機関識別子[0].言語', 'Contributor.寄与者別名[0].別名', 'Contributor.寄与者別名[0].言語', 'Contributor.寄与者メールアドレス[0].メールアドレス', 'Contributor.寄与者名[0].姓名', 'Contributor.寄与者名[0].言語', 'Contributor.寄与者タイプ', 'Contributor.寄与者姓[0].姓', 'Contributor.寄与者姓[0].言語', 'Contributor.寄与者名[0]. 名', 'Contributor.寄与者名[0].言語', 'Contributor.寄与者識別子[0].寄与者識別子', 'Contributor.寄与者識別子[0].寄与者識別子Scheme', 'Contributor.寄与者識別子[0].寄与者識別子URI', 'Access Rights.アクセス権', 'Access Rights.アクセス権URI', 'Rights Information[0].sample[0]', 'Rights Information[0].言語', 'Rights Information[0].権利情報Resource', 'Rights Information[0].権利情報', 'Subject[0].sample[0]', 'Subject[0].言語', 'Subject[0].主題Scheme', 'Subject[0].主題URI', 'Subject[0].主題', 'Content Description[0].内容記述タイプ', 'Content Description[0].内容記述', 'Content Description[0].言語', 'Publisher[0].言語', 'Publisher[0].出版者', 'Date[0].日付タイプ', 'Date[0].日付', 'Resource Type.Type', 'Resource Type.Resource', 'Identifier rRegistration.Identifier Registration', 'Identifier rRegistration.Identifier Registration Type', 'Version information', 'Related information[0].関連タイプ', 'Related information[0].関連識別子.識別子タイプ', 'Related information[0].関連識別子.関連識別子', 'Related information[0].関連名称[0].言語', 'Related information[0].関連名称[0].関連名称', 'Time Range[0].言語', 'Time Range[0].時間的範囲', 'Location Information[0].位置情報（空間）. 西部経度', 'Location Information[0].位置情報（空間）.東部経度', 'Location Information[0].位置情報（空間）.南部緯度', 'Location Information[0].位置情報（空間）.北部緯度', 'Location Information[0].位置情報（点）.経度', 'Location Information[0].位置情報（点）.緯度', 'Location Information[0].位置情報（自由記述）', 'Grant information[0].助成機関識別子.助成機関識別子タイプ', 'Grant information[0].助成機関識別子.助成機関識別子', 'Grant information[0].助成機関 名[0].言語', 'Grant information[0].助成機関 名[0].助成機関名', 'Grant information[0].研究課題番号.研究課題URI', 'Grant information[0].研究課題番号.研究課題番号', 'Grant information[0].研究課題名[0].言語', 'Grant information[0].研究課題名[0]. 研究課題名', 'File Information[0].本文URL.オブジェクトタイプ', 'File Information[0].本文URL.ラベル', 'File Information[0].本文URL.本文URL', 'File Information[0].フォーマット', 'File Information[0].サイズ[0].サイズ', 'File Information[0].日付[0].日付タイプ', 'File Information[0].日付[0].日付', 'File Information[0].バージョン情報', '.サムネイルパス', 'Thumbnail.URI[0].URI Label', 'Thumbnail.URI[0].URI', '.ファイルパス[0]', 'Billing File Information[0].アクセス', 'Billing File Information[0].日付[0].日付タイプ', 'Billing File Information[0].日付[0].日付', 'Billing File Information[0].表示形式', 'Billing File Information[0].表示名', 'Billing File Information[0].サイズ[0].サイズ', 'Billing File Information[0]. フォーマット', 'Billing File Information[0].グループ・価格[0].グループ', 'Billing File Information[0].グループ・価格[0].価格', 'Billing File Information[0].Is Billing', 'Billing File Information[0].自由ライセンス', 'Billing File Information[0].ライセンス', 'Billing File Information[0].本文URL.ラベル', 'Billing File Information[0].本文URL.オブジェクト タイプ', 'Billing File Information[0].本文URL.本文URL', 'Billing File Information[0].バージョン情報'], ['#', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', 'System', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''], ['#', '', 'Allow Multiple', 'Allow Multiple', 'Required', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', '', '', 'Required', 'Required', 'Required', 'Required', 'Required', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Required', 'Required', '', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple']], {7: [1, 'Index(public_state = True,harvest_public_state = True)', 'public', '', 'contributor@test.org', 'user@test.org', '', '', '', 'Keep', '2022-08-25', 'タイトル', 'ja', 'jpn', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'A大学', 'ja', '', '', 'repoadmin@test.org', '寄与者', 'ja', 'ContactPerson', '', '', '', '', '', '', '', 'open access', 'http://purl.org/coar/access_right/c_abf2', '', 'ja', 'CC0', '一定期間後に事業の実施上有益な者に対しての提供を開始する。但しデータのクレジット表記を条件とする。', '', 'ja', 'NDC', '', '複合化学', 'abstract', '概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要', 'ja', '', '', '', '', 'dataset', 'http://purl.org/coar/resource_type/c_ddb1', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Crossref Funder', 'https://dx.doi.org/10.13039/501100001863', 'ja', 'NEDO', '', '12345678', 'ja', 'プロジェクト', '', '', '', '', '1GB未満', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''], 8: [1, 'Index(public_state = True,harvest_public_state = True)', 'public', '', 'contributor@test.org', 'user@test.org', '', '', '', 'Keep', '2022-08-25', 'タイトル', 'ja', 'jpn', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'A大学', 'ja', '', '', 'repoadmin@test.org', '寄与者', 'ja', 'ContactPerson', '', '', '', '', '', '', '', 'open access', 'http://purl.org/coar/access_right/c_abf2', 'sample_value', '', '', '', '', 'ja', 'NDC', '', '複合化学', 'abstract', '概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要', 'ja', '', '', '', '', 'dataset', 'http://purl.org/coar/resource_type/c_ddb1', '', '', 100, '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Crossref Funder', 'https://dx.doi.org/10.13039/501100001863', 'ja', 'NEDO', '', '12345678', 'ja', 'プロジェクト', '', '', '', '', '1GB未満', '', '', '', 'recid_8/sample_thumbnail_label1', 'sample_thumbnail_label1', '', '', '', '', '', '', 'sample_file', '', '', '', '', '', '', '', '', '', '', '']})


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_make_stats_file_issue33432 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_make_stats_file_issue33432(app, users,db_itemtype, db_records,db_itemtype2,db_records2):
    app.config.update(
        EMAIL_DISPLAY_FLG=True,
        WEKO_RECORDS_UI_LICENSE_DICT=[
            {
                "name": "write your own license",
                "value": "license_free",
            },
            # version 0
            {
                "name": "Creative Commons CC0 1.0 Universal Public Domain Designation",
                "code": "CC0",
                "href_ja": "https://creativecommons.org/publicdomain/zero/1.0/deed.ja",
                "href_default": "https://creativecommons.org/publicdomain/zero/1.0/",
                "value": "license_12",
                "src": "88x31(0).png",
                "src_pdf": "cc-0.png",
                "href_pdf": "https://creativecommons.org/publicdomain/zero/1.0/"
                "deed.ja",
                "txt": "This work is licensed under a Public Domain Dedication "
                "International License.",
            },
            # version 3.0
            {
                "name": "Creative Commons Attribution 3.0 Unported (CC BY 3.0)",
                "code": "CC BY 3.0",
                "href_ja": "https://creativecommons.org/licenses/by/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by/3.0/",
                "value": "license_6",
                "src": "88x31(1).png",
                "src_pdf": "by.png",
                "href_pdf": "http://creativecommons.org/licenses/by/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                " 3.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-ShareAlike 3.0 Unported "
                "(CC BY-SA 3.0)",
                "code": "CC BY-SA 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-sa/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-sa/3.0/",
                "value": "license_7",
                "src": "88x31(2).png",
                "src_pdf": "by-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-sa/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-ShareAlike 3.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NoDerivs 3.0 Unported (CC BY-ND 3.0)",
                "code": "CC BY-ND 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nd/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nd/3.0/",
                "value": "license_8",
                "src": "88x31(3).png",
                "src_pdf": "by-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nd/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NoDerivatives 3.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial 3.0 Unported"
                " (CC BY-NC 3.0)",
                "code": "CC BY-NC 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc/3.0/",
                "value": "license_9",
                "src": "88x31(4).png",
                "src_pdf": "by-nc.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial 3.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial-ShareAlike 3.0 "
                "Unported (CC BY-NC-SA 3.0)",
                "code": "CC BY-NC-SA 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-sa/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-sa/3.0/",
                "value": "license_10",
                "src": "88x31(5).png",
                "src_pdf": "by-nc-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-sa/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 3.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial-NoDerivs "
                "3.0 Unported (CC BY-NC-ND 3.0)",
                "code": "CC BY-NC-ND 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-nd/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-nd/3.0/",
                "value": "license_11",
                "src": "88x31(6).png",
                "src_pdf": "by-nc-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-nd/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 3.0 International License.",
            },
            # version 4.0
            {
                "name": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
                "code": "CC BY 4.0",
                "href_ja": "https://creativecommons.org/licenses/by/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by/4.0/",
                "value": "license_0",
                "src": "88x31(1).png",
                "src_pdf": "by.png",
                "href_pdf": "http://creativecommons.org/licenses/by/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                " 4.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-ShareAlike 4.0 International "
                "(CC BY-SA 4.0)",
                "code": "CC BY-SA 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-sa/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-sa/4.0/",
                "value": "license_1",
                "src": "88x31(2).png",
                "src_pdf": "by-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-sa/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-ShareAlike 4.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NoDerivatives 4.0 International "
                "(CC BY-ND 4.0)",
                "code": "CC BY-ND 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nd/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nd/4.0/",
                "value": "license_2",
                "src": "88x31(3).png",
                "src_pdf": "by-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nd/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NoDerivatives 4.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial 4.0 International"
                " (CC BY-NC 4.0)",
                "code": "CC BY-NC 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc/4.0/",
                "value": "license_3",
                "src": "88x31(4).png",
                "src_pdf": "by-nc.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial 4.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0"
                " International (CC BY-NC-SA 4.0)",
                "code": "CC BY-NC-SA 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-sa/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
                "value": "license_4",
                "src": "88x31(5).png",
                "src_pdf": "by-nc-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 4.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 "
                "International (CC BY-NC-ND 4.0)",
                "code": "CC BY-NC-ND 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-nd/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
                "value": "license_5",
                "src": "88x31(6).png",
                "src_pdf": "by-nc-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-nd/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 4.0 International License.",
            },
        ],
    )
    item_types_data = {
        "2": {
            "item_type_id": "2",
            "name": "テストアイテムタイプ2",
            "root_url": "https://localhost:8443/",
            "jsonschema": "items/jsonschema/2",
            "keys": [],
            "labels": [],
            "recids": [7],
            "data": {},
        }
    }
    item_type_id = 2
    list_item_role = {"2": {"weko_creator_id": "1", "weko_shared_id": -1}}

    with app.test_request_context():
        assert make_stats_file(item_type_id, [7], list_item_role) == ([['#.id', '.uri', '.metadata.path[0]', '.pos_index[0]', '.publish_status', '.feedback_mail[0]', '.request_mail[0]', '.cnri', '.doi_ra', '.doi', '.edit_mode', '.metadata.pubdate', '.metadata.item_1554883918421.subitem_1551255647225', '.metadata.item_1554883918421.subitem_1551255648112', '.metadata.item_1554883961001.subitem_1551255818386', '.metadata.item_1554884042490.subitem_1522299896455', '.metadata.item_1554884042490.subitem_1522300014469', '.metadata.item_1554884042490.subitem_1522300048512', '.metadata.item_1554884042490.subitem_1523261968819', '.metadata.item_1532070986701.creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifier', '.metadata.item_1532070986701.creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierScheme', '.metadata.item_1532070986701.creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierURI', '.metadata.item_1532070986701.creatorAffiliations[0].affiliationNames[0].affiliationName', '.metadata.item_1532070986701.creatorAffiliations[0].affiliationNames[0].affiliationNameLang', '.metadata.item_1532070986701.creatorAlternatives[0].creatorAlternative', '.metadata.item_1532070986701.creatorAlternatives[0].creatorAlternativeLang', '.metadata.item_1532070986701.creatorMails[0].creatorMail', '.metadata.item_1532070986701.creatorNames[0].creatorName', '.metadata.item_1532070986701.creatorNames[0].creatorNameLang', '.metadata.item_1532070986701.familyNames[0].familyName', '.metadata.item_1532070986701.familyNames[0].familyNameLang', '.metadata.item_1532070986701.givenNames[0].givenName', '.metadata.item_1532070986701.givenNames[0].givenNameLang', '.metadata.item_1532070986701.nameIdentifiers[0].nameIdentifier', '.metadata.item_1532070986701.nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1532070986701.nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1532071014836.contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationNameIdentifier', '.metadata.item_1532071014836.contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationScheme', '.metadata.item_1532071014836.contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationURI', '.metadata.item_1532071014836.contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationName', '.metadata.item_1532071014836.contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationNameLang', '.metadata.item_1532071014836.contributorAlternatives[0].contributorAlternative', '.metadata.item_1532071014836.contributorAlternatives[0].contributorAlternativeLang', '.metadata.item_1532071014836.contributorMails[0].contributorMail', '.metadata.item_1532071014836.contributorNames[0].contributorName', '.metadata.item_1532071014836.contributorNames[0].lang', '.metadata.item_1532071014836.contributorType', '.metadata.item_1532071014836.familyNames[0].familyName', '.metadata.item_1532071014836.familyNames[0].familyNameLang', '.metadata.item_1532071014836.givenNames[0].givenName', '.metadata.item_1532071014836.givenNames[0].givenNameLang', '.metadata.item_1532071014836.nameIdentifiers[0].nameIdentifier', '.metadata.item_1532071014836.nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1532071014836.nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1532071031458.subitem_1522299639480', '.metadata.item_1532071031458.subitem_1600958577026', '.metadata.item_1532071039842[0].subitem_1522650717957', '.metadata.item_1532071039842[0].subitem_1522650727486', '.metadata.item_1532071039842[0].subitem_1522651041219', '.metadata.item_1532071057095[0].subitem_1522299896455', '.metadata.item_1532071057095[0].subitem_1522300014469', '.metadata.item_1532071057095[0].subitem_1522300048512', '.metadata.item_1532071057095[0].subitem_1523261968819', '.metadata.item_1532071068215[0].subitem_1522657647525', '.metadata.item_1532071068215[0].subitem_1522657697257', '.metadata.item_1532071068215[0].subitem_1523262169140', '.metadata.item_1532071093517[0].subitem_1522300295150', '.metadata.item_1532071093517[0].subitem_1522300316516', '.metadata.item_1532071103206[0].subitem_1522300695726', '.metadata.item_1532071103206[0].subitem_1522300722591', '.metadata.item_1569380622649.resourcetype', '.metadata.item_1569380622649.resourceuri', '.metadata.item_1581493352241.subitem_1569224170590', '.metadata.item_1581493352241.subitem_1569224172438', '.metadata.item_1532071133483', '.metadata.item_1532071158138[0].subitem_1522306207484', '.metadata.item_1532071158138[0].subitem_1522306287251.subitem_1522306382014', '.metadata.item_1532071158138[0].subitem_1522306287251.subitem_1522306436033', '.metadata.item_1532071158138[0].subitem_1523320863692[0].subitem_1523320867455', '.metadata.item_1532071158138[0].subitem_1523320863692[0].subitem_1523320909613', '.metadata.item_1532071168802[0].subitem_1522658018441', '.metadata.item_1532071168802[0].subitem_1522658031721', '.metadata.item_1532071184504[0].subitem_1522658250154.subitem_1522658252485', '.metadata.item_1532071184504[0].subitem_1522658250154.subitem_1522658264346', '.metadata.item_1532071184504[0].subitem_1522658250154.subitem_1522658270105', '.metadata.item_1532071184504[0].subitem_1522658250154.subitem_1522658274386', '.metadata.item_1532071184504[0].subitem_1523321394401.subitem_1523321400758', '.metadata.item_1532071184504[0].subitem_1523321394401.subitem_1523321450098', '.metadata.item_1532071184504[0].subitem_1523321527273', '.metadata.item_1532071200841[0].subitem_1522399143519.subitem_1522399281603', '.metadata.item_1532071200841[0].subitem_1522399143519.subitem_1522399333375', '.metadata.item_1532071200841[0].subitem_1522399412622[0].subitem_1522399416691', '.metadata.item_1532071200841[0].subitem_1522399412622[0].subitem_1522737543681', '.metadata.item_1532071200841[0].subitem_1522399571623.subitem_1522399585738', '.metadata.item_1532071200841[0].subitem_1522399571623.subitem_1522399628911', '.metadata.item_1532071200841[0].subitem_1522399651758[0].subitem_1522721910626', '.metadata.item_1532071200841[0].subitem_1522399651758[0].subitem_1522721929892', '.metadata.item_1532071216312[0].subitem_1522652546580.subitem_1522652548920', '.metadata.item_1532071216312[0].subitem_1522652546580.subitem_1522652672693', '.metadata.item_1532071216312[0].subitem_1522652546580.subitem_1522652685531', '.metadata.item_1532071216312[0].subitem_1522652734962', '.metadata.item_1532071216312[0].subitem_1522652740098[0].subitem_1522722119299', '.metadata.item_1532071216312[0].subitem_1522652747880[0].subitem_1522722132466', '.metadata.item_1532071216312[0].subitem_1522652747880[0].subitem_1522739295711', '.metadata.item_1532071216312[0].subitem_1523325300505', '.file_path[0]', '.metadata.item_1600165182071[0].accessrole', '.metadata.item_1600165182071[0].date[0].dateType', '.metadata.item_1600165182071[0].date[0].dateValue', '.metadata.item_1600165182071[0].displaytype', '.metadata.item_1600165182071[0].filename', '.metadata.item_1600165182071[0].filesize[0].value', '.metadata.item_1600165182071[0].format', '.metadata.item_1600165182071[0].groupsprice[0].group', '.metadata.item_1600165182071[0].groupsprice[0].price', '.metadata.item_1600165182071[0].is_billing', '.metadata.item_1600165182071[0].licensefree', '.metadata.item_1600165182071[0].licensetype', '.metadata.item_1600165182071[0].url.label', '.metadata.item_1600165182071[0].url.objectType', '.metadata.item_1600165182071[0].url.url', '.metadata.item_1600165182071[0].version'], ['#ID', 'URI', '.IndexID[0]', '.POS_INDEX[0]', '.PUBLISH_STATUS', '.FEEDBACK_MAIL[0]', '.REQUEST_MAIL[0]', '.CNRI', '.DOI_RA', '.DOI', 'Keep/Upgrade Version', 'PubDate', 'Title.Title', 'Title.Language', 'Language.Language', 'Keyword.言語', 'Keyword.主題Scheme', 'Keyword.主題URI', 'Keyword.主題', 'Creator.作成者所属[0].所属機関識別子[0].所属機関識別子', 'Creator.作成者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Creator.作成者所属[0].所属機関識別子[0].所属機関識別子URI', 'Creator.作成者所属[0].所属機関名[0].所属機関名', 'Creator.作成者所属[0].所属機関名[0].言語', 'Creator.作成者別名[0].別名', 'Creator.作成者別名[0].言語', 'Creator.作成者メールアドレス[0].メールアドレス', 'Creator.作成者姓名[0].姓名', 'Creator.作成者姓名[0].言語', 'Creator.作成者姓[0].姓', 'Creator.作成者姓[0].言語', 'Creator.作成者名[0].名', 'Creator.作成者名[0].言語', 'Creator.作成者識別子[0].作成者識別子', 'Creator.作成者識別子[0].作成者識別子Scheme', 'Creator.作成者識別子[0].作成者識別子URI', 'Contributor.寄与者所属[0].所属機関識別子[0].所属機関識別子', 'Contributor.寄与者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Contributor.寄与者所属[0].所属機関識別子[0].所属機関識別子URI', 'Contributor.寄与者所属[0].所属機関識別子[0].所属機関名', 'Contributor.寄与者所属[0].所属機関識別子[0].言語', 'Contributor.寄与者別名[0].別名', 'Contributor.寄与者別名[0].言語', 'Contributor.寄与者メールアドレス[0].メールアドレス', 'Contributor.寄与者名[0].姓名', 'Contributor.寄与者名[0].言語', 'Contributor.寄与者タイプ', 'Contributor.寄与者姓[0].姓', 'Contributor.寄与者姓[0].言語', 'Contributor.寄与者名[0]. 名', 'Contributor.寄与者名[0].言語', 'Contributor.寄与者識別子[0].寄与者識別子', 'Contributor.寄与者識別子[0].寄与者識別子Scheme', 'Contributor.寄与者識別子[0].寄与者識別子URI', 'Access Rights.アクセス権', 'Access Rights.アクセス権URI', 'Rights Information[0].言語', 'Rights Information[0].権利情報Resource', 'Rights Information[0].権利情報', 'Subject[0].言語', 'Subject[0].主題Scheme', 'Subject[0].主題URI', 'Subject[0].主題', 'Content Description[0].内容記述タイプ', 'Content Description[0].内容記述', 'Content Description[0].言語', 'Publisher[0].言語', 'Publisher[0].出版者', 'Date[0].日付タイプ', 'Date[0].日付', 'Resource Type.Type', 'Resource Type.Resource', 'Identifier rRegistration.Identifier Registration', 'Identifier rRegistration.Identifier Registration Type', 'Version information', 'Related information[0].関連タイプ', 'Related information[0].関連識別子.識別子タイプ', 'Related information[0].関連識別子.関連識別子', 'Related information[0].関連名称[0].言語', 'Related information[0].関連名称[0].関連名称', 'Time Range[0].言語', 'Time Range[0].時間的範囲', 'Location Information[0].位置情報（空間）. 西部経度', 'Location Information[0].位置情報（空間）.東部経度', 'Location Information[0].位置情報（空間）.南部緯度', 'Location Information[0].位置情報（空間）.北部緯度', 'Location Information[0].位置情報（点）.経度', 'Location Information[0].位置情報（点）.緯度', 'Location Information[0].位置情報（自由記述）', 'Grant information[0].助成機関識別子.助成機関識別子タイプ', 'Grant information[0].助成機関識別子.助成機関識別子', 'Grant information[0].助成機関 名[0].言語', 'Grant information[0].助成機関 名[0].助成機関名', 'Grant information[0].研究課題番号.研究課題URI', 'Grant information[0].研究課題番号.研究課題番号', 'Grant information[0].研究課題名[0].言語', 'Grant information[0].研究課題名[0]. 研究課題名', 'File Information[0].本文URL.オブジェクトタイプ', 'File Information[0].本文URL.ラベル', 'File Information[0].本文URL.本文URL', 'File Information[0].フォーマット', 'File Information[0].サイズ[0].サイズ', 'File Information[0].日付[0].日付タイプ', 'File Information[0].日付[0].日付', 'File Information[0].バージョン情報', '.ファイルパス[0]', 'Billing File Information[0].アクセス', 'Billing File Information[0].日付[0].日付タイプ', 'Billing File Information[0].日付[0].日付', 'Billing File Information[0].表示形式', 'Billing File Information[0].表示名', 'Billing File Information[0].サイズ[0].サイズ', 'Billing File Information[0]. フォーマット', 'Billing File Information[0].グループ・価格[0].グループ', 'Billing File Information[0].グループ・価格[0].価格', 'Billing File Information[0].Is Billing', 'Billing File Information[0].自由ライセンス', 'Billing File Information[0].ライセンス', 'Billing File Information[0].本文URL.ラベル', 'Billing File Information[0].本文URL.オブジェクト タイプ', 'Billing File Information[0].本文URL.本文URL', 'Billing File Information[0].バージョン情報'], ['#', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', 'System', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''], ['#', '', 'Allow Multiple', 'Allow Multiple', 'Required', 'Allow Multiple', 'Allow Multiple', '', '', '', 'Required', 'Required', 'Required', 'Required', 'Required', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Required', 'Required', '', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple']], {7: [1, 'Index(public_state = True,harvest_public_state = True)', 'public', '', '', '', '', '', 'Keep', '2022-08-25', 'タイトル', 'ja', 'jpn', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'A大学', 'ja', '', '', 'repoadmin@test.org', '寄与者', 'ja', 'ContactPerson', '', '', '', '', '', '', '', 'open access', 'http://purl.org/coar/access_right/c_abf2', 'ja', 'CC0', '一定期間後に事業の実施上有益な者に対しての提供を開始する。但しデータのクレジット表記を条件とする。', 'ja', 'NDC', '', '複合化学', 'abstract', '概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要', 'ja', '', '', '', '', 'dataset', 'http://purl.org/coar/resource_type/c_ddb1', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Crossref Funder', 'https://dx.doi.org/10.13039/501100001863', 'ja', 'NEDO', '', '12345678', 'ja', 'プロジェクト', '', '', '', '', '1GB未満', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']})

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_make_stats_file_issue36234 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_make_stats_file_issue36234(app, users,db_itemtype,db_records_file):
    app.config.update(
        EMAIL_DISPLAY_FLG=True,
        WEKO_RECORDS_UI_LICENSE_DICT=[
            {
                "name": "write your own license",
                "value": "license_free",
            },
            # version 0
            {
                "name": "Creative Commons CC0 1.0 Universal Public Domain Designation",
                "code": "CC0",
                "href_ja": "https://creativecommons.org/publicdomain/zero/1.0/deed.ja",
                "href_default": "https://creativecommons.org/publicdomain/zero/1.0/",
                "value": "license_12",
                "src": "88x31(0).png",
                "src_pdf": "cc-0.png",
                "href_pdf": "https://creativecommons.org/publicdomain/zero/1.0/"
                "deed.ja",
                "txt": "This work is licensed under a Public Domain Dedication "
                "International License.",
            },
            # version 3.0
            {
                "name": "Creative Commons Attribution 3.0 Unported (CC BY 3.0)",
                "code": "CC BY 3.0",
                "href_ja": "https://creativecommons.org/licenses/by/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by/3.0/",
                "value": "license_6",
                "src": "88x31(1).png",
                "src_pdf": "by.png",
                "href_pdf": "http://creativecommons.org/licenses/by/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                " 3.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-ShareAlike 3.0 Unported "
                "(CC BY-SA 3.0)",
                "code": "CC BY-SA 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-sa/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-sa/3.0/",
                "value": "license_7",
                "src": "88x31(2).png",
                "src_pdf": "by-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-sa/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-ShareAlike 3.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NoDerivs 3.0 Unported (CC BY-ND 3.0)",
                "code": "CC BY-ND 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nd/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nd/3.0/",
                "value": "license_8",
                "src": "88x31(3).png",
                "src_pdf": "by-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nd/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NoDerivatives 3.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial 3.0 Unported"
                " (CC BY-NC 3.0)",
                "code": "CC BY-NC 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc/3.0/",
                "value": "license_9",
                "src": "88x31(4).png",
                "src_pdf": "by-nc.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial 3.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial-ShareAlike 3.0 "
                "Unported (CC BY-NC-SA 3.0)",
                "code": "CC BY-NC-SA 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-sa/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-sa/3.0/",
                "value": "license_10",
                "src": "88x31(5).png",
                "src_pdf": "by-nc-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-sa/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 3.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial-NoDerivs "
                "3.0 Unported (CC BY-NC-ND 3.0)",
                "code": "CC BY-NC-ND 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-nd/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-nd/3.0/",
                "value": "license_11",
                "src": "88x31(6).png",
                "src_pdf": "by-nc-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-nd/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 3.0 International License.",
            },
            # version 4.0
            {
                "name": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
                "code": "CC BY 4.0",
                "href_ja": "https://creativecommons.org/licenses/by/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by/4.0/",
                "value": "license_0",
                "src": "88x31(1).png",
                "src_pdf": "by.png",
                "href_pdf": "http://creativecommons.org/licenses/by/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                " 4.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-ShareAlike 4.0 International "
                "(CC BY-SA 4.0)",
                "code": "CC BY-SA 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-sa/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-sa/4.0/",
                "value": "license_1",
                "src": "88x31(2).png",
                "src_pdf": "by-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-sa/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-ShareAlike 4.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NoDerivatives 4.0 International "
                "(CC BY-ND 4.0)",
                "code": "CC BY-ND 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nd/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nd/4.0/",
                "value": "license_2",
                "src": "88x31(3).png",
                "src_pdf": "by-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nd/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NoDerivatives 4.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial 4.0 International"
                " (CC BY-NC 4.0)",
                "code": "CC BY-NC 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc/4.0/",
                "value": "license_3",
                "src": "88x31(4).png",
                "src_pdf": "by-nc.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial 4.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0"
                " International (CC BY-NC-SA 4.0)",
                "code": "CC BY-NC-SA 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-sa/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
                "value": "license_4",
                "src": "88x31(5).png",
                "src_pdf": "by-nc-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 4.0 International License.",
            },
            {
                "name": "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 "
                "International (CC BY-NC-ND 4.0)",
                "code": "CC BY-NC-ND 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-nd/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
                "value": "license_5",
                "src": "88x31(6).png",
                "src_pdf": "by-nc-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-nd/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 4.0 International License.",
            },
        ],
    )

    temp_path = tempfile.TemporaryDirectory(
        prefix='weko_export_')
    export_path = temp_path.name + '/' + \
            datetime.utcnow().strftime("%Y%m%d%H%M%S")
    record_path = export_path + '/recid_' + str(1)
    os.makedirs(record_path, exist_ok=True)
    import shutil
    from os.path import dirname, join
    shutil.copyfile(join(dirname(__file__),"data/record_file/test1.txt"),record_path+"/test1.txt")

    item_type_id=1
    recids = [1]
    list_item_role = {"2": {"weko_creator_id": "1", "weko_shared_id": -1}}

    test = ([['#.id', '.uri', '.metadata.path[0]', '.pos_index[0]', '.publish_status', '.feedback_mail[0]', '.request_mail[0]', '.cnri', '.doi_ra', '.doi', '.edit_mode', '.metadata.pubdate', '.metadata.item_1617186331708[0].subitem_1551255647225', '.metadata.item_1617186331708[0].subitem_1551255648112', '.metadata.item_1617186385884[0].subitem_1551255720400', '.metadata.item_1617186385884[0].subitem_1551255721061', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifier', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierScheme', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierURI', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNames[0].affiliationName', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNames[0].affiliationNameLang', '.metadata.item_1617186419668[0].creatorAlternatives[0].creatorAlternative', '.metadata.item_1617186419668[0].creatorAlternatives[0].creatorAlternativeLang', '.metadata.item_1617186419668[0].creatorMails[0].creatorMail', '.metadata.item_1617186419668[0].creatorNames[0].creatorName', '.metadata.item_1617186419668[0].creatorNames[0].creatorNameLang', '.metadata.item_1617186419668[0].familyNames[0].familyName', '.metadata.item_1617186419668[0].familyNames[0].familyNameLang', '.metadata.item_1617186419668[0].givenNames[0].givenName', '.metadata.item_1617186419668[0].givenNames[0].givenNameLang', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationNameIdentifier', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationScheme', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationURI', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationName', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationNameLang', '.metadata.item_1617349709064[0].contributorAlternatives[0].contributorAlternative', '.metadata.item_1617349709064[0].contributorAlternatives[0].contributorAlternativeLang', '.metadata.item_1617349709064[0].contributorMails[0].contributorMail', '.metadata.item_1617349709064[0].contributorNames[0].contributorName', '.metadata.item_1617349709064[0].contributorNames[0].lang', '.metadata.item_1617349709064[0].contributorType', '.metadata.item_1617349709064[0].familyNames[0].familyName', '.metadata.item_1617349709064[0].familyNames[0].familyNameLang', '.metadata.item_1617349709064[0].givenNames[0].givenName', '.metadata.item_1617349709064[0].givenNames[0].givenNameLang', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617186476635.subitem_1522299639480', '.metadata.item_1617186476635.subitem_1600958577026', '.metadata.item_1617351524846.subitem_1523260933860', '.metadata.item_1617186499011[0].subitem_1522650717957', '.metadata.item_1617186499011[0].subitem_1522650727486', '.metadata.item_1617186499011[0].subitem_1522651041219', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617610673286[0].rightHolderNames[0].rightHolderLanguage', '.metadata.item_1617610673286[0].rightHolderNames[0].rightHolderName', '.metadata.item_1617186609386[0].subitem_1522299896455', '.metadata.item_1617186609386[0].subitem_1522300014469', '.metadata.item_1617186609386[0].subitem_1522300048512', '.metadata.item_1617186609386[0].subitem_1523261968819', '.metadata.item_1617186626617[0].subitem_description', '.metadata.item_1617186626617[0].subitem_description_language', '.metadata.item_1617186626617[0].subitem_description_type', '.metadata.item_1617186643794[0].subitem_1522300295150', '.metadata.item_1617186643794[0].subitem_1522300316516', '.metadata.item_1617186660861[0].subitem_1522300695726', '.metadata.item_1617186660861[0].subitem_1522300722591', '.metadata.item_1617186702042[0].subitem_1551255818386', '.metadata.item_1617258105262.resourcetype', '.metadata.item_1617258105262.resourceuri', '.metadata.item_1617349808926.subitem_1523263171732', '.metadata.item_1617265215918.subitem_1522305645492', '.metadata.item_1617265215918.subitem_1600292170262', '.metadata.item_1617186783814[0].subitem_identifier_type', '.metadata.item_1617186783814[0].subitem_identifier_uri', '.metadata.item_1617186819068.subitem_identifier_reg_text', '.metadata.item_1617186819068.subitem_identifier_reg_type', '.metadata.item_1617353299429[0].subitem_1522306207484', '.metadata.item_1617353299429[0].subitem_1522306287251.subitem_1522306382014', '.metadata.item_1617353299429[0].subitem_1522306287251.subitem_1522306436033', '.metadata.item_1617353299429[0].subitem_1523320863692[0].subitem_1523320867455', '.metadata.item_1617353299429[0].subitem_1523320863692[0].subitem_1523320909613', '.metadata.item_1617186859717[0].subitem_1522658018441', '.metadata.item_1617186859717[0].subitem_1522658031721', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_east_longitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_north_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_south_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_west_longitude', '.metadata.item_1617186882738[0].subitem_geolocation_place[0].subitem_geolocation_place_text', '.metadata.item_1617186882738[0].subitem_geolocation_point.subitem_point_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_point.subitem_point_longitude', '.metadata.item_1617186901218[0].subitem_1522399143519.subitem_1522399281603', '.metadata.item_1617186901218[0].subitem_1522399143519.subitem_1522399333375', '.metadata.item_1617186901218[0].subitem_1522399412622[0].subitem_1522399416691', '.metadata.item_1617186901218[0].subitem_1522399412622[0].subitem_1522737543681', '.metadata.item_1617186901218[0].subitem_1522399571623.subitem_1522399585738', '.metadata.item_1617186901218[0].subitem_1522399571623.subitem_1522399628911', '.metadata.item_1617186901218[0].subitem_1522399651758[0].subitem_1522721910626', '.metadata.item_1617186901218[0].subitem_1522399651758[0].subitem_1522721929892', '.metadata.item_1617186920753[0].subitem_1522646500366', '.metadata.item_1617186920753[0].subitem_1522646572813', '.metadata.item_1617186941041[0].subitem_1522650068558', '.metadata.item_1617186941041[0].subitem_1522650091861', '.metadata.item_1617186959569.subitem_1551256328147', '.metadata.item_1617186981471.subitem_1551256294723', '.metadata.item_1617186994930.subitem_1551256248092', '.metadata.item_1617187024783.subitem_1551256198917', '.metadata.item_1617187045071.subitem_1551256185532', '.metadata.item_1617187056579.bibliographicIssueDates.bibliographicIssueDate', '.metadata.item_1617187056579.bibliographicIssueDates.bibliographicIssueDateType', '.metadata.item_1617187056579.bibliographicIssueNumber', '.metadata.item_1617187056579.bibliographicNumberOfPages', '.metadata.item_1617187056579.bibliographicPageEnd', '.metadata.item_1617187056579.bibliographicPageStart', '.metadata.item_1617187056579.bibliographicVolumeNumber', '.metadata.item_1617187056579.bibliographic_titles[0].bibliographic_title', '.metadata.item_1617187056579.bibliographic_titles[0].bibliographic_titleLang', '.metadata.item_1617187087799.subitem_1551256171004', '.metadata.item_1617187112279[0].subitem_1551256126428', '.metadata.item_1617187112279[0].subitem_1551256129013', '.metadata.item_1617187136212.subitem_1551256096004', '.metadata.item_1617944105607[0].subitem_1551256015892[0].subitem_1551256027296', '.metadata.item_1617944105607[0].subitem_1551256015892[0].subitem_1551256029891', '.metadata.item_1617944105607[0].subitem_1551256037922[0].subitem_1551256042287', '.metadata.item_1617944105607[0].subitem_1551256037922[0].subitem_1551256047619', '.metadata.item_1617187187528[0].subitem_1599711633003[0].subitem_1599711636923', '.metadata.item_1617187187528[0].subitem_1599711633003[0].subitem_1599711645590', '.metadata.item_1617187187528[0].subitem_1599711655652', '.metadata.item_1617187187528[0].subitem_1599711660052[0].subitem_1599711680082', '.metadata.item_1617187187528[0].subitem_1599711660052[0].subitem_1599711686511', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711704251', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711712451', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711727603', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711731891', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711735410', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711739022', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711743722', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711745532', '.metadata.item_1617187187528[0].subitem_1599711758470[0].subitem_1599711769260', '.metadata.item_1617187187528[0].subitem_1599711758470[0].subitem_1599711775943', '.metadata.item_1617187187528[0].subitem_1599711788485[0].subitem_1599711798761', '.metadata.item_1617187187528[0].subitem_1599711788485[0].subitem_1599711803382', '.metadata.item_1617187187528[0].subitem_1599711813532', '.file_path[0]', '.metadata.item_1617605131499[0].accessrole', '.metadata.item_1617605131499[0].date[0].dateType', '.metadata.item_1617605131499[0].date[0].dateValue', '.metadata.item_1617605131499[0].displaytype', '.metadata.item_1617605131499[0].fileDate[0].fileDateType', '.metadata.item_1617605131499[0].fileDate[0].fileDateValue', '.metadata.item_1617605131499[0].filename', '.metadata.item_1617605131499[0].filesize[0].value', '.metadata.item_1617605131499[0].format', '.metadata.item_1617605131499[0].groups', '.metadata.item_1617605131499[0].licensefree', '.metadata.item_1617605131499[0].licensetype', '.metadata.item_1617605131499[0].url.label', '.metadata.item_1617605131499[0].url.objectType', '.metadata.item_1617605131499[0].url.url', '.metadata.item_1617605131499[0].version', '.file_path[1]', '.metadata.item_1617605131499[1].accessrole', '.metadata.item_1617605131499[1].date[0].dateType', '.metadata.item_1617605131499[1].date[0].dateValue', '.metadata.item_1617605131499[1].displaytype', '.metadata.item_1617605131499[1].fileDate[0].fileDateType', '.metadata.item_1617605131499[1].fileDate[0].fileDateValue', '.metadata.item_1617605131499[1].filename', '.metadata.item_1617605131499[1].filesize[0].value', '.metadata.item_1617605131499[1].format', '.metadata.item_1617605131499[1].groups', '.metadata.item_1617605131499[1].licensefree', '.metadata.item_1617605131499[1].licensetype', '.metadata.item_1617605131499[1].url.label', '.metadata.item_1617605131499[1].url.objectType', '.metadata.item_1617605131499[1].url.url', '.metadata.item_1617605131499[1].version', '.metadata.item_1617620223087[0].subitem_1565671149650', '.metadata.item_1617620223087[0].subitem_1565671169640', '.metadata.item_1617620223087[0].subitem_1565671178623', '.thumbnail_path[0]', '.metadata.item_1662046377046[0].subitem_thumbnail[0].thumbnail_label', '.metadata.item_1662046377046[0].subitem_thumbnail[0].thumbnail_url'], ['#ID', 'URI', '.IndexID[0]', '.POS_INDEX[0]', '.PUBLISH_STATUS', '.FEEDBACK_MAIL[0]', '.REQUEST_MAIL[0]', '.CNRI', '.DOI_RA', '.DOI', 'Keep/Upgrade Version', 'PubDate', 'Title[0].Title', 'Title[0].Language', 'Alternative Title[0].Alternative Title', 'Alternative Title[0].Language', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子URI', 'Creator[0].作成者所属[0].所属機関名[0].所属機関名', 'Creator[0].作成者所属[0].所属機関名[0].言語', 'Creator[0].作成者別名[0].別名', 'Creator[0].作成者別名[0].言語', 'Creator[0].作成者メールアドレス[0].メールアドレス', 'Creator[0].作成者姓名[0].姓名', 'Creator[0].作成者姓名[0].言語', 'Creator[0].作成者姓[0].姓', 'Creator[0].作成者姓[0].言語', 'Creator[0].作成者名[0].名', 'Creator[0].作成者名[0].言語', 'Creator[0].作成者識別子[0].作成者識別子', 'Creator[0].作成者識別子[0].作成者識別子Scheme', 'Creator[0].作成者識別子[0].作成者識別子URI', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子URI', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関名', 'Contributor[0].寄与者所属[0].所属機関識別子[0].言語', 'Contributor[0].寄与者別名[0].別名', 'Contributor[0].寄与者別名[0].言語', 'Contributor[0].寄与者メールアドレス[0].メールアドレス', 'Contributor[0].寄与者姓名[0].姓名', 'Contributor[0].寄与者姓名[0].言語', 'Contributor[0].寄与者タイプ', 'Contributor[0].寄与者姓[0].姓', 'Contributor[0].寄与者姓[0].言語', 'Contributor[0].寄与者名[0].名', 'Contributor[0].寄与者名[0].言語', 'Contributor[0].寄与者識別子[0].寄与者識別子', 'Contributor[0].寄与者識別子[0].寄与者識別子Scheme', 'Contributor[0].寄与者識別子[0].寄与者識別子URI', 'Access Rights.アクセス権', 'Access Rights.アクセス権URI', 'APC.APC', 'Rights[0].言語', 'Rights[0].権利情報Resource', 'Rights[0].権利情報', 'Rights Holder[0].権利者識別子[0].権利者識別子', 'Rights Holder[0].権利者識別子[0].権利者識別子Scheme', 'Rights Holder[0].権利者識別子[0].権利者識別子URI', 'Rights Holder[0].権利者名[0].言語', 'Rights Holder[0].権利者名[0].権利者名', 'Subject[0].言語', 'Subject[0].主題Scheme', 'Subject[0].主題URI', 'Subject[0].主題', 'Description[0].内容記述', 'Description[0].言語', 'Description[0].内容記述タイプ', 'Publisher[0].言語', 'Publisher[0].出版者', 'Date[0].日付タイプ', 'Date[0].日付', 'Language[0].Language', 'Resource Type.資源タイプ', 'Resource Type.資源タイプ識別子', 'Version.バージョン情報', 'Version Type.出版タイプ', 'Version Type.出版タイプResource', 'Identifier[0].識別子タイプ', 'Identifier[0].識別子', 'Identifier Registration.ID登録', 'Identifier Registration.ID登録タイプ', 'Relation[0].関連タイプ', 'Relation[0].関連識別子.識別子タイプ', 'Relation[0].関連識別子.関連識別子', 'Relation[0].関連名称[0].言語', 'Relation[0].関連名称[0].関連名称', 'Temporal[0].言語', 'Temporal[0].時間的範囲', 'Geo Location[0].位置情報（空間）.東部経度', 'Geo Location[0].位置情報（空間）.北部緯度', 'Geo Location[0].位置情報（空間）.南部緯度', 'Geo Location[0].位置情報（空間）.西部経度', 'Geo Location[0].位置情報（自由記述）[0].位置情報（自由記述）', 'Geo Location[0].位置情報（点）.緯度', 'Geo Location[0].位置情報（点）.経度', 'Funding Reference[0].助成機関識別子.助成機関識別子タイプ', 'Funding Reference[0].助成機関識別子.助成機関識別子', 'Funding Reference[0].助成機関名[0].言語', 'Funding Reference[0].助成機関名[0].助成機関名', 'Funding Reference[0].研究課題番号.研究課題URI', 'Funding Reference[0].研究課題番号.研究課題番号', 'Funding Reference[0].研究課題名[0].言語', 'Funding Reference[0].研究課題名[0].研究課題名', 'Source Identifier[0].収録物識別子タイプ', 'Source Identifier[0].収録物識別子', 'Source Title[0].言語', 'Source Title[0].収録物名', 'Volume Number.Volume Number', 'Issue Number.Issue Number', 'Number of Pages.Number of Pages', 'Page Start.Page Start', 'Page End.Page End', 'Bibliographic Information.発行日.日付', 'Bibliographic Information.発行日.日付タイプ', 'Bibliographic Information.号', 'Bibliographic Information.ページ数', 'Bibliographic Information.終了ページ', 'Bibliographic Information.開始ページ', 'Bibliographic Information.巻', 'Bibliographic Information.雑誌名[0].タイトル', 'Bibliographic Information.雑誌名[0].言語', 'Dissertation Number.Dissertation Number', 'Degree Name[0].Degree Name', 'Degree Name[0].Language', 'Date Granted.Date Granted', 'Degree Grantor[0].Degree Grantor Name Identifier[0].Degree Grantor Name Identifier', 'Degree Grantor[0].Degree Grantor Name Identifier[0].Degree Grantor Name Identifier Scheme', 'Degree Grantor[0].Degree Grantor Name[0].Degree Grantor Name', 'Degree Grantor[0].Degree Grantor Name[0].Language', 'Conference[0].Conference Name[0].Conference Name', 'Conference[0].Conference Name[0].Language', 'Conference[0].Conference Sequence', 'Conference[0].Conference Sponsor[0].Conference Sponsor', 'Conference[0].Conference Sponsor[0].Language', 'Conference[0].Conference Date.Conference Date', 'Conference[0].Conference Date.Start Day', 'Conference[0].Conference Date.Start Month', 'Conference[0].Conference Date.Start Year', 'Conference[0].Conference Date.End Day', 'Conference[0].Conference Date.End Month', 'Conference[0].Conference Date.End Year', 'Conference[0].Conference Date.Language', 'Conference[0].Conference Venue[0].Conference Venue', 'Conference[0].Conference Venue[0].Language', 'Conference[0].Conference Place[0].Conference Place', 'Conference[0].Conference Place[0].Language', 'Conference[0].Conference Country', '.ファイルパス[0]', 'File[0].アクセス', 'File[0].オープンアクセスの日付[0].日付タイプ', 'File[0].オープンアクセスの日付[0].日付', 'File[0].表示形式', 'File[0].日付[0].日付タイプ', 'File[0].日付[0].日付', 'File[0].表示名', 'File[0].サイズ[0].サイズ', 'File[0].フォーマット', 'File[0].グループ', 'File[0].自由ライセンス', 'File[0].ライセンス', 'File[0].本文URL.ラベル', 'File[0].本文URL.オブジェクトタイプ', 'File[0].本文URL.本文URL', 'File[0].バージョン情報', '.ファイルパス[1]', 'File[1].アクセス', 'File[1].オープンアクセスの日付[0].日付タイプ', 'File[1].オープンアクセスの日付[0].日付', 'File[1].表示形式', 'File[1].日付[0].日付タイプ', 'File[1].日付[0].日付', 'File[1].表示名', 'File[1].サイズ[0].サイズ', 'File[1].フォーマット', 'File[1].グループ', 'File[1].自由ライセンス', 'File[1].ライセンス', 'File[1].本文URL.ラベル', 'File[1].本文URL.オブジェクトタイプ', 'File[1].本文URL.本文URL', 'File[1].バージョン情報', 'Heading[0].Language', 'Heading[0].Banner Headline', 'Heading[0].Subheading', '.サムネイルパス[0]', 'サムネイル[0].URI[0].ラベル', 'サムネイル[0].URI[0].URI'], ['#', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', '', '', 'System', '', '', 'System', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', 'System'], ['#', '', 'Allow Multiple', 'Allow Multiple', 'Required', 'Allow Multiple', 'Allow Multiple', '', '', '', 'Required', 'Required', 'Required, Allow Multiple', 'Required, Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Required', 'Required', '', '', '', 'Allow Multiple', 'Allow Multiple', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Allow Multiple', 'Allow Multiple', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple']], {1: [1, 'Index(public_state = True,harvest_public_state = True)', 'public', '', '', '', '', '', 'Keep', '2023-02-28', 'only file item', 'ja', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'conference paper', 'http://purl.org/coar/resource_type/c_5794', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'recid_1/test1.txt', 'open_access', 'Available', '2023-02-28', '', '', '', 'test1.txt', '37 B', 'text/plain', '', '', '', '', '', 'https://localhost/record/1/files/test1.txt', '', '', 'open_access', 'Available', '2023-02-28', '', '', '', 'google', '', '', '', '', '', '', '', 'https://www.google.com/', '', '', '', '', '', '', '']})
    with app.test_request_context():
        result = make_stats_file(item_type_id, recids, list_item_role,export_path)
        assert result == test

# def get_list_file_by_record_id(recid):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_list_file_by_record_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_list_file_by_record_id(db_records,users,esindex):
    depid, recid, parent, doi, record, item = db_records[0]
    assert get_list_file_by_record_id(record.id) == []


# def c(item_types_data, export_path):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_write_bibtex_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_write_bibtex_files(db_oaischema):
    item_types_data = {
        "15": {
            "item_type_id": "15",
            "name": "デフォルトアイテムタイプ（フル）(15)",
            "root_url": "https://localhost:8443/",
            "jsonschema": "items/jsonschema/15",
            "keys": [],
            "labels": [],
            "recids": [1],
            "data": {},
        }
    }
    export_path = "/tmp/weko_export_agvb5jc9/20220827140620"
    assert write_bibtex_files(item_types_data, export_path)


# def write_files(item_types_data, export_path, list_item_role):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_write_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_write_files(app,db_itemtype,db_records,users):
    item_types_data = {'1': {'item_type_id': '1', 'name': 'itemtype', 'root_url': 'https://localhost:8443/', 'jsonschema': 'items/jsonschema/1', 'keys': [], 'labels': [], 'recids': [1], 'data': {}}}
    export_path= "./tests/"
    list_item_role={'1': {'weko_creator_id': '1', 'weko_shared_id': -1}}
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            write_files(item_types_data,export_path,list_item_role)
            assert os.path.exists("./tests/itemtype.tsv") == True
            os.remove("./tests/itemtype.tsv")
            assert os.path.exists("./tests/itemtype.tsv") == False


# def check_item_type_name(name):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_check_item_type_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_check_item_type_name():
    assert check_item_type_name("ab cd") == "ab_cd"
    assert check_item_type_name("ab:cd") == "ab_cd"
    assert check_item_type_name("ab/cd") == "ab_cd"
    assert check_item_type_name("ab*cd") == "ab_cd"
    assert check_item_type_name('ab"cd') == "ab_cd"
    assert check_item_type_name("ab<cd") == "ab_cd"
    assert check_item_type_name("ab>cd") == "ab_cd"


# def export_items(post_data):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_export_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_export_items(app,db_itemtype,db_records,users):
    post_data = {'export_file_contents_radio': 'False', 'export_format_radio': 'JSON', 'record_ids': '[1]', 'invalid_record_ids': '[]', 'record_metadata': '{"1":{"created":"2022-08-25T12:56:26.587349+00:00","id":1,"links":{"self":"https://localhost:8443/api/records/1"},"metadata":{"_comment":["en_conference paperITEM00000001(public_open_access_simple)","WEKO-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2","https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/","4-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz","Joho, Taro,Joho, Taro,Joho, Taro","Joho,Joho,Joho","Taro,Taro,Taro","0000000121691048","ISNI","http://isni.org/isni/0000000121691048","University,Source Title,1,111,12,1,3,Degree Name,2021-06-30,xxxxxx,kakenhi,Degree Grantor Name","Conference Name","1","JPN","Sponsor","2000","12","1","2020","12","2020/12/11","1","Conference Venue","Conference Place"],"_files_info":[{"extention":"pdf","label":"1KB.pdf","url":"https://weko3.example.org/record/1/files/1KB.pdf"}],"_item_metadata":{"_oai":{"id":"oai:weko3.example.org:00000001","sets":["1661432090216"]},"author_link":["4"],"control_number":"1","item_1617186331708":{"attribute_name":"Title","attribute_value_mlt":[{"subitem_1551255647225":"ja_conference paperITEM00000001(public_open_access_open_access_simple)","subitem_1551255648112":"ja"},{"subitem_1551255647225":"en_conference paperITEM00000001(public_open_access_simple)","subitem_1551255648112":"en"}]},"item_1617186385884":{"attribute_name":"Alternative Title","attribute_value_mlt":[{"subitem_1551255720400":"Alternative Title","subitem_1551255721061":"en"},{"subitem_1551255720400":"Alternative Title","subitem_1551255721061":"ja"}]},"item_1617186419668":{"attribute_name":"Creator","attribute_type":"creator","attribute_value_mlt":[{"creatorAffiliations":[{"affiliationNameIdentifiers":[{"affiliationNameIdentifier":"0000000121691048","affiliationNameIdentifierScheme":"ISNI","affiliationNameIdentifierURI":"http://isni.org/isni/0000000121691048"}],"affiliationNames":[{"affiliationName":"University","affiliationNameLang":"en"}]}],"creatorMails":[{"creatorMail":"wekosoftware@nii.ac.jp"}],"creatorNames":[{"creatorName":"情報, 太郎","creatorNameLang":"ja"},{"creatorName":"ジョウホウ, タロウ","creatorNameLang":"ja-Kana"},{"creatorName":"Joho, Taro","creatorNameLang":"en"}],"familyNames":[{"familyName":"情報","familyNameLang":"ja"},{"familyName":"ジョウホウ","familyNameLang":"ja-Kana"},{"familyName":"Joho","familyNameLang":"en"}],"givenNames":[{"givenName":"太郎","givenNameLang":"ja"},{"givenName":"タロウ","givenNameLang":"ja-Kana"},{"givenName":"Taro","givenNameLang":"en"}],"nameIdentifiers":[{"nameIdentifier":"4","nameIdentifierScheme":"WEKO"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"ORCID","nameIdentifierURI":"https://orcid.org/"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"CiNii","nameIdentifierURI":"https://ci.nii.ac.jp/"},{"nameIdentifier":"zzzzzzz","nameIdentifierScheme":"KAKEN2","nameIdentifierURI":"https://kaken.nii.ac.jp/"}]},{"creatorMails":[{"creatorMail":"wekosoftware@nii.ac.jp"}],"creatorNames":[{"creatorName":"情報, 太郎","creatorNameLang":"ja"},{"creatorName":"ジョウホウ, タロウ","creatorNameLang":"ja-Kana"},{"creatorName":"Joho, Taro","creatorNameLang":"en"}],"familyNames":[{"familyName":"情報","familyNameLang":"ja"},{"familyName":"ジョウホウ","familyNameLang":"ja-Kana"},{"familyName":"Joho","familyNameLang":"en"}],"givenNames":[{"givenName":"太郎","givenNameLang":"ja"},{"givenName":"タロウ","givenNameLang":"ja-Kana"},{"givenName":"Taro","givenNameLang":"en"}],"nameIdentifiers":[{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"ORCID","nameIdentifierURI":"https://orcid.org/"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"CiNii","nameIdentifierURI":"https://ci.nii.ac.jp/"},{"nameIdentifier":"zzzzzzz","nameIdentifierScheme":"KAKEN2","nameIdentifierURI":"https://kaken.nii.ac.jp/"}]},{"creatorMails":[{"creatorMail":"wekosoftware@nii.ac.jp"}],"creatorNames":[{"creatorName":"情報, 太郎","creatorNameLang":"ja"},{"creatorName":"ジョウホウ, タロウ","creatorNameLang":"ja-Kana"},{"creatorName":"Joho, Taro","creatorNameLang":"en"}],"familyNames":[{"familyName":"情報","familyNameLang":"ja"},{"familyName":"ジョウホウ","familyNameLang":"ja-Kana"},{"familyName":"Joho","familyNameLang":"en"}],"givenNames":[{"givenName":"太郎","givenNameLang":"ja"},{"givenName":"タロウ","givenNameLang":"ja-Kana"},{"givenName":"Taro","givenNameLang":"en"}],"nameIdentifiers":[{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"ORCID","nameIdentifierURI":"https://orcid.org/"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"CiNii","nameIdentifierURI":"https://ci.nii.ac.jp/"},{"nameIdentifier":"zzzzzzz","nameIdentifierScheme":"KAKEN2","nameIdentifierURI":"https://kaken.nii.ac.jp/"}]}]},"item_1617186476635":{"attribute_name":"Access Rights","attribute_value_mlt":[{"subitem_1522299639480":"open access","subitem_1600958577026":"http://purl.org/coar/access_right/c_abf2"}]},"item_1617186499011":{"attribute_name":"Rights","attribute_value_mlt":[{"subitem_1522650717957":"ja","subitem_1522650727486":"http://localhost","subitem_1522651041219":"Rights Information"}]},"item_1617186609386":{"attribute_name":"Subject","attribute_value_mlt":[{"subitem_1522299896455":"ja","subitem_1522300014469":"Other","subitem_1522300048512":"http://localhost/","subitem_1523261968819":"Sibject1"}]},"item_1617186626617":{"attribute_name":"Description","attribute_value_mlt":[{"subitem_description":"Description\\nDescription<br/>Description","subitem_description_language":"en","subitem_description_type":"Abstract"},{"subitem_description":"概要\\n概要\\n概要\\n概要","subitem_description_language":"ja","subitem_description_type":"Abstract"}]},"item_1617186643794":{"attribute_name":"Publisher","attribute_value_mlt":[{"subitem_1522300295150":"en","subitem_1522300316516":"Publisher"}]},"item_1617186660861":{"attribute_name":"Date","attribute_value_mlt":[{"subitem_1522300695726":"Available","subitem_1522300722591":"2021-06-30"}]},"item_1617186702042":{"attribute_name":"Language","attribute_value_mlt":[{"subitem_1551255818386":"jpn"}]},"item_1617186783814":{"attribute_name":"Identifier","attribute_value_mlt":[{"subitem_identifier_type":"URI","subitem_identifier_uri":"http://localhost"}]},"item_1617186859717":{"attribute_name":"Temporal","attribute_value_mlt":[{"subitem_1522658018441":"en","subitem_1522658031721":"Temporal"}]},"item_1617186882738":{"attribute_name":"Geo Location","attribute_value_mlt":[{"subitem_geolocation_place":[{"subitem_geolocation_place_text":"Japan"}]}]},"item_1617186901218":{"attribute_name":"Funding Reference","attribute_value_mlt":[{"subitem_1522399143519":{"subitem_1522399281603":"ISNI","subitem_1522399333375":"http://xxx"},"subitem_1522399412622":[{"subitem_1522399416691":"en","subitem_1522737543681":"Funder Name"}],"subitem_1522399571623":{"subitem_1522399585738":"Award URI","subitem_1522399628911":"Award Number"},"subitem_1522399651758":[{"subitem_1522721910626":"en","subitem_1522721929892":"Award Title"}]}]},"item_1617186920753":{"attribute_name":"Source Identifier","attribute_value_mlt":[{"subitem_1522646500366":"ISSN","subitem_1522646572813":"xxxx-xxxx-xxxx"}]},"item_1617186941041":{"attribute_name":"Source Title","attribute_value_mlt":[{"subitem_1522650068558":"en","subitem_1522650091861":"Source Title"}]},"item_1617186959569":{"attribute_name":"Volume Number","attribute_value_mlt":[{"subitem_1551256328147":"1"}]},"item_1617186981471":{"attribute_name":"Issue Number","attribute_value_mlt":[{"subitem_1551256294723":"111"}]},"item_1617186994930":{"attribute_name":"Number of Pages","attribute_value_mlt":[{"subitem_1551256248092":"12"}]},"item_1617187024783":{"attribute_name":"Page Start","attribute_value_mlt":[{"subitem_1551256198917":"1"}]},"item_1617187045071":{"attribute_name":"Page End","attribute_value_mlt":[{"subitem_1551256185532":"3"}]},"item_1617187112279":{"attribute_name":"Degree Name","attribute_value_mlt":[{"subitem_1551256126428":"Degree Name","subitem_1551256129013":"en"}]},"item_1617187136212":{"attribute_name":"Date Granted","attribute_value_mlt":[{"subitem_1551256096004":"2021-06-30"}]},"item_1617187187528":{"attribute_name":"Conference","attribute_value_mlt":[{"subitem_1599711633003":[{"subitem_1599711636923":"Conference Name","subitem_1599711645590":"ja"}],"subitem_1599711655652":"1","subitem_1599711660052":[{"subitem_1599711680082":"Sponsor","subitem_1599711686511":"ja"}],"subitem_1599711699392":{"subitem_1599711704251":"2020/12/11","subitem_1599711712451":"1","subitem_1599711727603":"12","subitem_1599711731891":"2000","subitem_1599711735410":"1","subitem_1599711739022":"12","subitem_1599711743722":"2020","subitem_1599711745532":"ja"},"subitem_1599711758470":[{"subitem_1599711769260":"Conference Venue","subitem_1599711775943":"ja"}],"subitem_1599711788485":[{"subitem_1599711798761":"Conference Place","subitem_1599711803382":"ja"}],"subitem_1599711813532":"JPN"}]},"item_1617258105262":{"attribute_name":"Resource Type","attribute_value_mlt":[{"resourcetype":"dataset","resourceuri":"http://purl.org/coar/resource_type/c_ddb1"}]},"item_1617265215918":{"attribute_name":"Version Type","attribute_value_mlt":[{"subitem_1522305645492":"AO","subitem_1600292170262":"http://purl.org/coar/version/c_b1a7d7d4d402bcce"}]},"item_1617349709064":{"attribute_name":"Contributor","attribute_value_mlt":[{"contributorMails":[{"contributorMail":"wekosoftware@nii.ac.jp"}],"contributorNames":[{"contributorName":"情報, 太郎","lang":"ja"},{"contributorName":"ジョウホウ, タロウ","lang":"ja-Kana"},{"contributorName":"Joho, Taro","lang":"en"}],"contributorType":"ContactPerson","familyNames":[{"familyName":"情報","familyNameLang":"ja"},{"familyName":"ジョウホウ","familyNameLang":"ja-Kana"},{"familyName":"Joho","familyNameLang":"en"}],"givenNames":[{"givenName":"太郎","givenNameLang":"ja"},{"givenName":"タロウ","givenNameLang":"ja-Kana"},{"givenName":"Taro","givenNameLang":"en"}],"nameIdentifiers":[{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"ORCID","nameIdentifierURI":"https://orcid.org/"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"CiNii","nameIdentifierURI":"https://ci.nii.ac.jp/"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"KAKEN2","nameIdentifierURI":"https://kaken.nii.ac.jp/"}]}]},"item_1617349808926":{"attribute_name":"Version","attribute_value_mlt":[{"subitem_1523263171732":"Version"}]},"item_1617351524846":{"attribute_name":"APC","attribute_value_mlt":[{"subitem_1523260933860":"Unknown"}]},"item_1617353299429":{"attribute_name":"Relation","attribute_value_mlt":[{"subitem_1522306207484":"isVersionOf","subitem_1522306287251":{"subitem_1522306382014":"arXiv","subitem_1522306436033":"xxxxx"},"subitem_1523320863692":[{"subitem_1523320867455":"en","subitem_1523320909613":"Related Title"}]}]},"item_1617605131499":{"attribute_name":"File","attribute_type":"file","attribute_value_mlt":[{"accessrole":"open_access","date":[{"dateType":"Available","dateValue":"2021-07-12"}],"displaytype":"simple","filename":"1KB.pdf","filesize":[{"value":"1 KB"}],"format":"text/plain","mimetype":"application/pdf","url":{"url":"https://weko3.example.org/record/1/files/1KB.pdf"},"version_id":"9008626e-cb32-48bd-8409-1204f03b8077"}]},"item_1617610673286":{"attribute_name":"Rights Holder","attribute_value_mlt":[{"nameIdentifiers":[{"nameIdentifier":"xxxxxx","nameIdentifierScheme":"ORCID","nameIdentifierURI":"https://orcid.org/"}],"rightHolderNames":[{"rightHolderLanguage":"ja","rightHolderName":"Right Holder Name"}]}]},"item_1617620223087":{"attribute_name":"Heading","attribute_value_mlt":[{"subitem_1565671149650":"ja","subitem_1565671169640":"Banner Headline","subitem_1565671178623":"Subheading"},{"subitem_1565671149650":"en","subitem_1565671169640":"Banner Headline","subitem_1565671178623":"Subheding"}]},"item_1617944105607":{"attribute_name":"Degree Grantor","attribute_value_mlt":[{"subitem_1551256015892":[{"subitem_1551256027296":"xxxxxx","subitem_1551256029891":"kakenhi"}],"subitem_1551256037922":[{"subitem_1551256042287":"Degree Grantor Name","subitem_1551256047619":"en"}]}]},"item_title":"ja_conference paperITEM00000001(public_open_access_open_access_simple)","item_type_id":"15","owner":"1","path":["1661432090216"],"pubdate":{"attribute_name":"PubDate","attribute_value":"2021-08-06"},"publish_date":"2021-08-06","publish_status":"0","relation_version_is_last":true,"title":["ja_conference paperITEM00000001(public_open_access_open_access_simple)"],"weko_creator_id":"1","weko_shared_id":-1},"_oai":{"id":"oai:weko3.example.org:00000001","sets":["1661432090216"]},"accessRights":["open access"],"alternative":["Alternative Title","Alternative Title"],"apc":["Unknown"],"author_link":["4"],"conference":{"conferenceCountry":["JPN"],"conferenceDate":["2020/12/11"],"conferenceName":["Conference Name"],"conferenceSequence":["1"],"conferenceSponsor":["Sponsor"],"conferenceVenue":["Conference Venue"]},"contributor":{"@attributes":{"contributorType":[["ContactPerson"]]},"affiliation":{"affiliationName":[],"nameIdentifier":[]},"contributorAlternative":[],"contributorName":["情報, 太郎","ジョウホウ, タロウ","Joho, Taro"],"familyName":["情報","ジョウホウ","Joho"],"givenName":["太郎","タロウ","Taro"],"nameIdentifier":["xxxxxxx","xxxxxxx","xxxxxxx"]},"control_number":"1","creator":{"affiliation":{"affiliationName":["University"],"nameIdentifier":["0000000121691048"]},"creatorAlternative":[],"creatorName":["情報, 太郎","ジョウホウ, タロウ","Joho, Taro","情報, 太郎","ジョウホウ, タロウ","Joho, Taro","情報, 太郎","ジョウホウ, タロウ","Joho, Taro"],"familyName":["情報","ジョウホウ","Joho","情報","ジョウホウ","Joho","情報","ジョウホウ","Joho"],"givenName":["太郎","タロウ","Taro","太郎","タロウ","Taro","太郎","タロウ","Taro"],"nameIdentifier":["4","xxxxxxx","xxxxxxx","zzzzzzz","xxxxxxx","xxxxxxx","zzzzzzz","xxxxxxx","xxxxxxx","zzzzzzz"]},"date":[{"dateType":"Available","value":"2021-06-30"}],"dateGranted":["2021-06-30"],"degreeGrantor":{"degreeGrantorName":["Degree Grantor Name"],"nameIdentifier":["xxxxxx"]},"degreeName":["Degree Name"],"description":[{"descriptionType":"Abstract","value":"Description\\nDescription<br/>Description"},{"descriptionType":"Abstract","value":"概要\\n概要\\n概要\\n概要"}],"feedback_mail_list":[{"author_id":"","email":"wekosoftware@nii.ac.jp"}],"fundingReference":{"awardNumber":["Award Number"],"awardTitle":["Award Title"],"funderIdentifier":["http://xxx"],"funderName":["Funder Name"]},"geoLocation":{"geoLocationPlace":["Japan"]},"identifier":[{"identifierType":"URI","value":"http://localhost"}],"issue":["111"],"itemtype":"デフォルトアイテムタイプ（フル）","language":["jpn"],"numPages":["12"],"pageEnd":["3"],"pageStart":["1"],"path":["1661432090216"],"publish_date":"2021-08-06","publish_status":"0","publisher":["Publisher"],"relation":{"@attributes":{"relationType":[["isVersionOf"]]},"relatedIdentifier":[{"identifierType":"arXiv","value":"xxxxx"}],"relatedTitle":["Related Title"]},"relation_version_is_last":true,"rights":["Rights Information"],"rightsHolder":{"nameIdentifier":["xxxxxx"],"rightsHolderName":["Right Holder Name"]},"sourceIdentifier":[{"identifierType":"ISSN","value":"xxxx-xxxx-xxxx"}],"sourceTitle":["Source Title"],"subject":[{"subjectScheme":"Other","value":"Sibject1"}],"temporal":["Temporal"],"title":["en_conference paperITEM00000001(public_open_access_simple)","ja_conference paperITEM00000001(public_open_access_open_access_simple)"],"type":["dataset"],"version":["Version"],"versiontype":["AO"],"volume":["1"],"weko_creator_id":"1","weko_shared_id":-1},"updated":"2022-08-26T12:57:36.376731+00:00"}}'}
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            res = export_items(post_data)
            assert res.status_code == 200



# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_export_items_issue32943 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_export_items_issue32943(app,db_itemtype,db_itemtype2,db_records,users,db_records2):
    post_data = {'export_file_contents_radio': 'False', 'export_format_radio': 'JSON', 'record_ids': '[1]', 'invalid_record_ids': '1', 'record_metadata': '{"1":{"created":"2022-08-25T12:56:26.587349+00:00","id":1,"links":{"self":"https://localhost:8443/api/records/1"},"metadata":{"_comment":["en_conference paperITEM00000001(public_open_access_simple)","WEKO-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2","https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/","4-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz","Joho, Taro,Joho, Taro,Joho, Taro","Joho,Joho,Joho","Taro,Taro,Taro","0000000121691048","ISNI","http://isni.org/isni/0000000121691048","University,Source Title,1,111,12,1,3,Degree Name,2021-06-30,xxxxxx,kakenhi,Degree Grantor Name","Conference Name","1","JPN","Sponsor","2000","12","1","2020","12","2020/12/11","1","Conference Venue","Conference Place"],"_files_info":[{"extention":"pdf","label":"1KB.pdf","url":"https://weko3.example.org/record/1/files/1KB.pdf"}],"_item_metadata":{"_oai":{"id":"oai:weko3.example.org:00000001","sets":["1661432090216"]},"author_link":["4"],"control_number":"1","item_1617186331708":{"attribute_name":"Title","attribute_value_mlt":[{"subitem_1551255647225":"ja_conference paperITEM00000001(public_open_access_open_access_simple)","subitem_1551255648112":"ja"},{"subitem_1551255647225":"en_conference paperITEM00000001(public_open_access_simple)","subitem_1551255648112":"en"}]},"item_1617186385884":{"attribute_name":"Alternative Title","attribute_value_mlt":[{"subitem_1551255720400":"Alternative Title","subitem_1551255721061":"en"},{"subitem_1551255720400":"Alternative Title","subitem_1551255721061":"ja"}]},"item_1617186419668":{"attribute_name":"Creator","attribute_type":"creator","attribute_value_mlt":[{"creatorAffiliations":[{"affiliationNameIdentifiers":[{"affiliationNameIdentifier":"0000000121691048","affiliationNameIdentifierScheme":"ISNI","affiliationNameIdentifierURI":"http://isni.org/isni/0000000121691048"}],"affiliationNames":[{"affiliationName":"University","affiliationNameLang":"en"}]}],"creatorMails":[{"creatorMail":"wekosoftware@nii.ac.jp"}],"creatorNames":[{"creatorName":"情報, 太郎","creatorNameLang":"ja"},{"creatorName":"ジョウホウ, タロウ","creatorNameLang":"ja-Kana"},{"creatorName":"Joho, Taro","creatorNameLang":"en"}],"familyNames":[{"familyName":"情報","familyNameLang":"ja"},{"familyName":"ジョウホウ","familyNameLang":"ja-Kana"},{"familyName":"Joho","familyNameLang":"en"}],"givenNames":[{"givenName":"太郎","givenNameLang":"ja"},{"givenName":"タロウ","givenNameLang":"ja-Kana"},{"givenName":"Taro","givenNameLang":"en"}],"nameIdentifiers":[{"nameIdentifier":"4","nameIdentifierScheme":"WEKO"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"ORCID","nameIdentifierURI":"https://orcid.org/"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"CiNii","nameIdentifierURI":"https://ci.nii.ac.jp/"},{"nameIdentifier":"zzzzzzz","nameIdentifierScheme":"KAKEN2","nameIdentifierURI":"https://kaken.nii.ac.jp/"}]},{"creatorMails":[{"creatorMail":"wekosoftware@nii.ac.jp"}],"creatorNames":[{"creatorName":"情報, 太郎","creatorNameLang":"ja"},{"creatorName":"ジョウホウ, タロウ","creatorNameLang":"ja-Kana"},{"creatorName":"Joho, Taro","creatorNameLang":"en"}],"familyNames":[{"familyName":"情報","familyNameLang":"ja"},{"familyName":"ジョウホウ","familyNameLang":"ja-Kana"},{"familyName":"Joho","familyNameLang":"en"}],"givenNames":[{"givenName":"太郎","givenNameLang":"ja"},{"givenName":"タロウ","givenNameLang":"ja-Kana"},{"givenName":"Taro","givenNameLang":"en"}],"nameIdentifiers":[{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"ORCID","nameIdentifierURI":"https://orcid.org/"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"CiNii","nameIdentifierURI":"https://ci.nii.ac.jp/"},{"nameIdentifier":"zzzzzzz","nameIdentifierScheme":"KAKEN2","nameIdentifierURI":"https://kaken.nii.ac.jp/"}]},{"creatorMails":[{"creatorMail":"wekosoftware@nii.ac.jp"}],"creatorNames":[{"creatorName":"情報, 太郎","creatorNameLang":"ja"},{"creatorName":"ジョウホウ, タロウ","creatorNameLang":"ja-Kana"},{"creatorName":"Joho, Taro","creatorNameLang":"en"}],"familyNames":[{"familyName":"情報","familyNameLang":"ja"},{"familyName":"ジョウホウ","familyNameLang":"ja-Kana"},{"familyName":"Joho","familyNameLang":"en"}],"givenNames":[{"givenName":"太郎","givenNameLang":"ja"},{"givenName":"タロウ","givenNameLang":"ja-Kana"},{"givenName":"Taro","givenNameLang":"en"}],"nameIdentifiers":[{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"ORCID","nameIdentifierURI":"https://orcid.org/"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"CiNii","nameIdentifierURI":"https://ci.nii.ac.jp/"},{"nameIdentifier":"zzzzzzz","nameIdentifierScheme":"KAKEN2","nameIdentifierURI":"https://kaken.nii.ac.jp/"}]}]},"item_1617186476635":{"attribute_name":"Access Rights","attribute_value_mlt":[{"subitem_1522299639480":"open access","subitem_1600958577026":"http://purl.org/coar/access_right/c_abf2"}]},"item_1617186499011":{"attribute_name":"Rights","attribute_value_mlt":[{"subitem_1522650717957":"ja","subitem_1522650727486":"http://localhost","subitem_1522651041219":"Rights Information"}]},"item_1617186609386":{"attribute_name":"Subject","attribute_value_mlt":[{"subitem_1522299896455":"ja","subitem_1522300014469":"Other","subitem_1522300048512":"http://localhost/","subitem_1523261968819":"Sibject1"}]},"item_1617186626617":{"attribute_name":"Description","attribute_value_mlt":[{"subitem_description":"Description\\nDescription<br/>Description","subitem_description_language":"en","subitem_description_type":"Abstract"},{"subitem_description":"概要\\n概要\\n概要\\n概要","subitem_description_language":"ja","subitem_description_type":"Abstract"}]},"item_1617186643794":{"attribute_name":"Publisher","attribute_value_mlt":[{"subitem_1522300295150":"en","subitem_1522300316516":"Publisher"}]},"item_1617186660861":{"attribute_name":"Date","attribute_value_mlt":[{"subitem_1522300695726":"Available","subitem_1522300722591":"2021-06-30"}]},"item_1617186702042":{"attribute_name":"Language","attribute_value_mlt":[{"subitem_1551255818386":"jpn"}]},"item_1617186783814":{"attribute_name":"Identifier","attribute_value_mlt":[{"subitem_identifier_type":"URI","subitem_identifier_uri":"http://localhost"}]},"item_1617186859717":{"attribute_name":"Temporal","attribute_value_mlt":[{"subitem_1522658018441":"en","subitem_1522658031721":"Temporal"}]},"item_1617186882738":{"attribute_name":"Geo Location","attribute_value_mlt":[{"subitem_geolocation_place":[{"subitem_geolocation_place_text":"Japan"}]}]},"item_1617186901218":{"attribute_name":"Funding Reference","attribute_value_mlt":[{"subitem_1522399143519":{"subitem_1522399281603":"ISNI","subitem_1522399333375":"http://xxx"},"subitem_1522399412622":[{"subitem_1522399416691":"en","subitem_1522737543681":"Funder Name"}],"subitem_1522399571623":{"subitem_1522399585738":"Award URI","subitem_1522399628911":"Award Number"},"subitem_1522399651758":[{"subitem_1522721910626":"en","subitem_1522721929892":"Award Title"}]}]},"item_1617186920753":{"attribute_name":"Source Identifier","attribute_value_mlt":[{"subitem_1522646500366":"ISSN","subitem_1522646572813":"xxxx-xxxx-xxxx"}]},"item_1617186941041":{"attribute_name":"Source Title","attribute_value_mlt":[{"subitem_1522650068558":"en","subitem_1522650091861":"Source Title"}]},"item_1617186959569":{"attribute_name":"Volume Number","attribute_value_mlt":[{"subitem_1551256328147":"1"}]},"item_1617186981471":{"attribute_name":"Issue Number","attribute_value_mlt":[{"subitem_1551256294723":"111"}]},"item_1617186994930":{"attribute_name":"Number of Pages","attribute_value_mlt":[{"subitem_1551256248092":"12"}]},"item_1617187024783":{"attribute_name":"Page Start","attribute_value_mlt":[{"subitem_1551256198917":"1"}]},"item_1617187045071":{"attribute_name":"Page End","attribute_value_mlt":[{"subitem_1551256185532":"3"}]},"item_1617187112279":{"attribute_name":"Degree Name","attribute_value_mlt":[{"subitem_1551256126428":"Degree Name","subitem_1551256129013":"en"}]},"item_1617187136212":{"attribute_name":"Date Granted","attribute_value_mlt":[{"subitem_1551256096004":"2021-06-30"}]},"item_1617187187528":{"attribute_name":"Conference","attribute_value_mlt":[{"subitem_1599711633003":[{"subitem_1599711636923":"Conference Name","subitem_1599711645590":"ja"}],"subitem_1599711655652":"1","subitem_1599711660052":[{"subitem_1599711680082":"Sponsor","subitem_1599711686511":"ja"}],"subitem_1599711699392":{"subitem_1599711704251":"2020/12/11","subitem_1599711712451":"1","subitem_1599711727603":"12","subitem_1599711731891":"2000","subitem_1599711735410":"1","subitem_1599711739022":"12","subitem_1599711743722":"2020","subitem_1599711745532":"ja"},"subitem_1599711758470":[{"subitem_1599711769260":"Conference Venue","subitem_1599711775943":"ja"}],"subitem_1599711788485":[{"subitem_1599711798761":"Conference Place","subitem_1599711803382":"ja"}],"subitem_1599711813532":"JPN"}]},"item_1617258105262":{"attribute_name":"Resource Type","attribute_value_mlt":[{"resourcetype":"dataset","resourceuri":"http://purl.org/coar/resource_type/c_ddb1"}]},"item_1617265215918":{"attribute_name":"Version Type","attribute_value_mlt":[{"subitem_1522305645492":"AO","subitem_1600292170262":"http://purl.org/coar/version/c_b1a7d7d4d402bcce"}]},"item_1617349709064":{"attribute_name":"Contributor","attribute_value_mlt":[{"contributorMails":[{"contributorMail":"wekosoftware@nii.ac.jp"}],"contributorNames":[{"contributorName":"情報, 太郎","lang":"ja"},{"contributorName":"ジョウホウ, タロウ","lang":"ja-Kana"},{"contributorName":"Joho, Taro","lang":"en"}],"contributorType":"ContactPerson","familyNames":[{"familyName":"情報","familyNameLang":"ja"},{"familyName":"ジョウホウ","familyNameLang":"ja-Kana"},{"familyName":"Joho","familyNameLang":"en"}],"givenNames":[{"givenName":"太郎","givenNameLang":"ja"},{"givenName":"タロウ","givenNameLang":"ja-Kana"},{"givenName":"Taro","givenNameLang":"en"}],"nameIdentifiers":[{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"ORCID","nameIdentifierURI":"https://orcid.org/"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"CiNii","nameIdentifierURI":"https://ci.nii.ac.jp/"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"KAKEN2","nameIdentifierURI":"https://kaken.nii.ac.jp/"}]}]},"item_1617349808926":{"attribute_name":"Version","attribute_value_mlt":[{"subitem_1523263171732":"Version"}]},"item_1617351524846":{"attribute_name":"APC","attribute_value_mlt":[{"subitem_1523260933860":"Unknown"}]},"item_1617353299429":{"attribute_name":"Relation","attribute_value_mlt":[{"subitem_1522306207484":"isVersionOf","subitem_1522306287251":{"subitem_1522306382014":"arXiv","subitem_1522306436033":"xxxxx"},"subitem_1523320863692":[{"subitem_1523320867455":"en","subitem_1523320909613":"Related Title"}]}]},"item_1617605131499":{"attribute_name":"File","attribute_type":"file","attribute_value_mlt":[{"accessrole":"open_access","date":[{"dateType":"Available","dateValue":"2021-07-12"}],"displaytype":"simple","filename":"1KB.pdf","filesize":[{"value":"1 KB"}],"format":"text/plain","mimetype":"application/pdf","url":{"url":"https://weko3.example.org/record/1/files/1KB.pdf"},"version_id":"9008626e-cb32-48bd-8409-1204f03b8077"}]},"item_1617610673286":{"attribute_name":"Rights Holder","attribute_value_mlt":[{"nameIdentifiers":[{"nameIdentifier":"xxxxxx","nameIdentifierScheme":"ORCID","nameIdentifierURI":"https://orcid.org/"}],"rightHolderNames":[{"rightHolderLanguage":"ja","rightHolderName":"Right Holder Name"}]}]},"item_1617620223087":{"attribute_name":"Heading","attribute_value_mlt":[{"subitem_1565671149650":"ja","subitem_1565671169640":"Banner Headline","subitem_1565671178623":"Subheading"},{"subitem_1565671149650":"en","subitem_1565671169640":"Banner Headline","subitem_1565671178623":"Subheding"}]},"item_1617944105607":{"attribute_name":"Degree Grantor","attribute_value_mlt":[{"subitem_1551256015892":[{"subitem_1551256027296":"xxxxxx","subitem_1551256029891":"kakenhi"}],"subitem_1551256037922":[{"subitem_1551256042287":"Degree Grantor Name","subitem_1551256047619":"en"}]}]},"item_title":"ja_conference paperITEM00000001(public_open_access_open_access_simple)","item_type_id":"15","owner":"1","path":["1661432090216"],"pubdate":{"attribute_name":"PubDate","attribute_value":"2021-08-06"},"publish_date":"2021-08-06","publish_status":"0","relation_version_is_last":true,"title":["ja_conference paperITEM00000001(public_open_access_open_access_simple)"],"weko_creator_id":"1","weko_shared_id":-1},"_oai":{"id":"oai:weko3.example.org:00000001","sets":["1661432090216"]},"accessRights":["open access"],"alternative":["Alternative Title","Alternative Title"],"apc":["Unknown"],"author_link":["4"],"conference":{"conferenceCountry":["JPN"],"conferenceDate":["2020/12/11"],"conferenceName":["Conference Name"],"conferenceSequence":["1"],"conferenceSponsor":["Sponsor"],"conferenceVenue":["Conference Venue"]},"contributor":{"@attributes":{"contributorType":[["ContactPerson"]]},"affiliation":{"affiliationName":[],"nameIdentifier":[]},"contributorAlternative":[],"contributorName":["情報, 太郎","ジョウホウ, タロウ","Joho, Taro"],"familyName":["情報","ジョウホウ","Joho"],"givenName":["太郎","タロウ","Taro"],"nameIdentifier":["xxxxxxx","xxxxxxx","xxxxxxx"]},"control_number":"1","creator":{"affiliation":{"affiliationName":["University"],"nameIdentifier":["0000000121691048"]},"creatorAlternative":[],"creatorName":["情報, 太郎","ジョウホウ, タロウ","Joho, Taro","情報, 太郎","ジョウホウ, タロウ","Joho, Taro","情報, 太郎","ジョウホウ, タロウ","Joho, Taro"],"familyName":["情報","ジョウホウ","Joho","情報","ジョウホウ","Joho","情報","ジョウホウ","Joho"],"givenName":["太郎","タロウ","Taro","太郎","タロウ","Taro","太郎","タロウ","Taro"],"nameIdentifier":["4","xxxxxxx","xxxxxxx","zzzzzzz","xxxxxxx","xxxxxxx","zzzzzzz","xxxxxxx","xxxxxxx","zzzzzzz"]},"date":[{"dateType":"Available","value":"2021-06-30"}],"dateGranted":["2021-06-30"],"degreeGrantor":{"degreeGrantorName":["Degree Grantor Name"],"nameIdentifier":["xxxxxx"]},"degreeName":["Degree Name"],"description":[{"descriptionType":"Abstract","value":"Description\\nDescription<br/>Description"},{"descriptionType":"Abstract","value":"概要\\n概要\\n概要\\n概要"}],"feedback_mail_list":[{"author_id":"","email":"wekosoftware@nii.ac.jp"}],"fundingReference":{"awardNumber":["Award Number"],"awardTitle":["Award Title"],"funderIdentifier":["http://xxx"],"funderName":["Funder Name"]},"geoLocation":{"geoLocationPlace":["Japan"]},"identifier":[{"identifierType":"URI","value":"http://localhost"}],"issue":["111"],"itemtype":"デフォルトアイテムタイプ（フル）","language":["jpn"],"numPages":["12"],"pageEnd":["3"],"pageStart":["1"],"path":["1661432090216"],"publish_date":"2021-08-06","publish_status":"0","publisher":["Publisher"],"relation":{"@attributes":{"relationType":[["isVersionOf"]]},"relatedIdentifier":[{"identifierType":"arXiv","value":"xxxxx"}],"relatedTitle":["Related Title"]},"relation_version_is_last":true,"rights":["Rights Information"],"rightsHolder":{"nameIdentifier":["xxxxxx"],"rightsHolderName":["Right Holder Name"]},"sourceIdentifier":[{"identifierType":"ISSN","value":"xxxx-xxxx-xxxx"}],"sourceTitle":["Source Title"],"subject":[{"subjectScheme":"Other","value":"Sibject1"}],"temporal":["Temporal"],"title":["en_conference paperITEM00000001(public_open_access_simple)","ja_conference paperITEM00000001(public_open_access_open_access_simple)"],"type":["dataset"],"version":["Version"],"versiontype":["AO"],"volume":["1"],"weko_creator_id":"1","weko_shared_id":-1},"updated":"2022-08-26T12:57:36.376731+00:00"}}'}
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            res = export_items(post_data)
            assert res == ('',204)

    post_data = {'export_file_contents_radio': 'False', 'export_format_radio': 'JSON', 'record_ids': '[1,2]', 'invalid_record_ids': '1', 'record_metadata': '{"1":{"created":"2022-08-25T12:56:26.587349+00:00","id":1,"links":{"self":"https://localhost:8443/api/records/1"},"metadata":{"_comment":["en_conference paperITEM00000001(public_open_access_simple)","WEKO-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2","https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/","4-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz","Joho, Taro,Joho, Taro,Joho, Taro","Joho,Joho,Joho","Taro,Taro,Taro","0000000121691048","ISNI","http://isni.org/isni/0000000121691048","University,Source Title,1,111,12,1,3,Degree Name,2021-06-30,xxxxxx,kakenhi,Degree Grantor Name","Conference Name","1","JPN","Sponsor","2000","12","1","2020","12","2020/12/11","1","Conference Venue","Conference Place"],"_files_info":[{"extention":"pdf","label":"1KB.pdf","url":"https://weko3.example.org/record/1/files/1KB.pdf"}],"_item_metadata":{"_oai":{"id":"oai:weko3.example.org:00000001","sets":["1661432090216"]},"author_link":["4"],"control_number":"1","item_1617186331708":{"attribute_name":"Title","attribute_value_mlt":[{"subitem_1551255647225":"ja_conference paperITEM00000001(public_open_access_open_access_simple)","subitem_1551255648112":"ja"},{"subitem_1551255647225":"en_conference paperITEM00000001(public_open_access_simple)","subitem_1551255648112":"en"}]},"item_1617186385884":{"attribute_name":"Alternative Title","attribute_value_mlt":[{"subitem_1551255720400":"Alternative Title","subitem_1551255721061":"en"},{"subitem_1551255720400":"Alternative Title","subitem_1551255721061":"ja"}]},"item_1617186419668":{"attribute_name":"Creator","attribute_type":"creator","attribute_value_mlt":[{"creatorAffiliations":[{"affiliationNameIdentifiers":[{"affiliationNameIdentifier":"0000000121691048","affiliationNameIdentifierScheme":"ISNI","affiliationNameIdentifierURI":"http://isni.org/isni/0000000121691048"}],"affiliationNames":[{"affiliationName":"University","affiliationNameLang":"en"}]}],"creatorMails":[{"creatorMail":"wekosoftware@nii.ac.jp"}],"creatorNames":[{"creatorName":"情報, 太郎","creatorNameLang":"ja"},{"creatorName":"ジョウホウ, タロウ","creatorNameLang":"ja-Kana"},{"creatorName":"Joho, Taro","creatorNameLang":"en"}],"familyNames":[{"familyName":"情報","familyNameLang":"ja"},{"familyName":"ジョウホウ","familyNameLang":"ja-Kana"},{"familyName":"Joho","familyNameLang":"en"}],"givenNames":[{"givenName":"太郎","givenNameLang":"ja"},{"givenName":"タロウ","givenNameLang":"ja-Kana"},{"givenName":"Taro","givenNameLang":"en"}],"nameIdentifiers":[{"nameIdentifier":"4","nameIdentifierScheme":"WEKO"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"ORCID","nameIdentifierURI":"https://orcid.org/"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"CiNii","nameIdentifierURI":"https://ci.nii.ac.jp/"},{"nameIdentifier":"zzzzzzz","nameIdentifierScheme":"KAKEN2","nameIdentifierURI":"https://kaken.nii.ac.jp/"}]},{"creatorMails":[{"creatorMail":"wekosoftware@nii.ac.jp"}],"creatorNames":[{"creatorName":"情報, 太郎","creatorNameLang":"ja"},{"creatorName":"ジョウホウ, タロウ","creatorNameLang":"ja-Kana"},{"creatorName":"Joho, Taro","creatorNameLang":"en"}],"familyNames":[{"familyName":"情報","familyNameLang":"ja"},{"familyName":"ジョウホウ","familyNameLang":"ja-Kana"},{"familyName":"Joho","familyNameLang":"en"}],"givenNames":[{"givenName":"太郎","givenNameLang":"ja"},{"givenName":"タロウ","givenNameLang":"ja-Kana"},{"givenName":"Taro","givenNameLang":"en"}],"nameIdentifiers":[{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"ORCID","nameIdentifierURI":"https://orcid.org/"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"CiNii","nameIdentifierURI":"https://ci.nii.ac.jp/"},{"nameIdentifier":"zzzzzzz","nameIdentifierScheme":"KAKEN2","nameIdentifierURI":"https://kaken.nii.ac.jp/"}]},{"creatorMails":[{"creatorMail":"wekosoftware@nii.ac.jp"}],"creatorNames":[{"creatorName":"情報, 太郎","creatorNameLang":"ja"},{"creatorName":"ジョウホウ, タロウ","creatorNameLang":"ja-Kana"},{"creatorName":"Joho, Taro","creatorNameLang":"en"}],"familyNames":[{"familyName":"情報","familyNameLang":"ja"},{"familyName":"ジョウホウ","familyNameLang":"ja-Kana"},{"familyName":"Joho","familyNameLang":"en"}],"givenNames":[{"givenName":"太郎","givenNameLang":"ja"},{"givenName":"タロウ","givenNameLang":"ja-Kana"},{"givenName":"Taro","givenNameLang":"en"}],"nameIdentifiers":[{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"ORCID","nameIdentifierURI":"https://orcid.org/"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"CiNii","nameIdentifierURI":"https://ci.nii.ac.jp/"},{"nameIdentifier":"zzzzzzz","nameIdentifierScheme":"KAKEN2","nameIdentifierURI":"https://kaken.nii.ac.jp/"}]}]},"item_1617186476635":{"attribute_name":"Access Rights","attribute_value_mlt":[{"subitem_1522299639480":"open access","subitem_1600958577026":"http://purl.org/coar/access_right/c_abf2"}]},"item_1617186499011":{"attribute_name":"Rights","attribute_value_mlt":[{"subitem_1522650717957":"ja","subitem_1522650727486":"http://localhost","subitem_1522651041219":"Rights Information"}]},"item_1617186609386":{"attribute_name":"Subject","attribute_value_mlt":[{"subitem_1522299896455":"ja","subitem_1522300014469":"Other","subitem_1522300048512":"http://localhost/","subitem_1523261968819":"Sibject1"}]},"item_1617186626617":{"attribute_name":"Description","attribute_value_mlt":[{"subitem_description":"Description\\nDescription<br/>Description","subitem_description_language":"en","subitem_description_type":"Abstract"},{"subitem_description":"概要\\n概要\\n概要\\n概要","subitem_description_language":"ja","subitem_description_type":"Abstract"}]},"item_1617186643794":{"attribute_name":"Publisher","attribute_value_mlt":[{"subitem_1522300295150":"en","subitem_1522300316516":"Publisher"}]},"item_1617186660861":{"attribute_name":"Date","attribute_value_mlt":[{"subitem_1522300695726":"Available","subitem_1522300722591":"2021-06-30"}]},"item_1617186702042":{"attribute_name":"Language","attribute_value_mlt":[{"subitem_1551255818386":"jpn"}]},"item_1617186783814":{"attribute_name":"Identifier","attribute_value_mlt":[{"subitem_identifier_type":"URI","subitem_identifier_uri":"http://localhost"}]},"item_1617186859717":{"attribute_name":"Temporal","attribute_value_mlt":[{"subitem_1522658018441":"en","subitem_1522658031721":"Temporal"}]},"item_1617186882738":{"attribute_name":"Geo Location","attribute_value_mlt":[{"subitem_geolocation_place":[{"subitem_geolocation_place_text":"Japan"}]}]},"item_1617186901218":{"attribute_name":"Funding Reference","attribute_value_mlt":[{"subitem_1522399143519":{"subitem_1522399281603":"ISNI","subitem_1522399333375":"http://xxx"},"subitem_1522399412622":[{"subitem_1522399416691":"en","subitem_1522737543681":"Funder Name"}],"subitem_1522399571623":{"subitem_1522399585738":"Award URI","subitem_1522399628911":"Award Number"},"subitem_1522399651758":[{"subitem_1522721910626":"en","subitem_1522721929892":"Award Title"}]}]},"item_1617186920753":{"attribute_name":"Source Identifier","attribute_value_mlt":[{"subitem_1522646500366":"ISSN","subitem_1522646572813":"xxxx-xxxx-xxxx"}]},"item_1617186941041":{"attribute_name":"Source Title","attribute_value_mlt":[{"subitem_1522650068558":"en","subitem_1522650091861":"Source Title"}]},"item_1617186959569":{"attribute_name":"Volume Number","attribute_value_mlt":[{"subitem_1551256328147":"1"}]},"item_1617186981471":{"attribute_name":"Issue Number","attribute_value_mlt":[{"subitem_1551256294723":"111"}]},"item_1617186994930":{"attribute_name":"Number of Pages","attribute_value_mlt":[{"subitem_1551256248092":"12"}]},"item_1617187024783":{"attribute_name":"Page Start","attribute_value_mlt":[{"subitem_1551256198917":"1"}]},"item_1617187045071":{"attribute_name":"Page End","attribute_value_mlt":[{"subitem_1551256185532":"3"}]},"item_1617187112279":{"attribute_name":"Degree Name","attribute_value_mlt":[{"subitem_1551256126428":"Degree Name","subitem_1551256129013":"en"}]},"item_1617187136212":{"attribute_name":"Date Granted","attribute_value_mlt":[{"subitem_1551256096004":"2021-06-30"}]},"item_1617187187528":{"attribute_name":"Conference","attribute_value_mlt":[{"subitem_1599711633003":[{"subitem_1599711636923":"Conference Name","subitem_1599711645590":"ja"}],"subitem_1599711655652":"1","subitem_1599711660052":[{"subitem_1599711680082":"Sponsor","subitem_1599711686511":"ja"}],"subitem_1599711699392":{"subitem_1599711704251":"2020/12/11","subitem_1599711712451":"1","subitem_1599711727603":"12","subitem_1599711731891":"2000","subitem_1599711735410":"1","subitem_1599711739022":"12","subitem_1599711743722":"2020","subitem_1599711745532":"ja"},"subitem_1599711758470":[{"subitem_1599711769260":"Conference Venue","subitem_1599711775943":"ja"}],"subitem_1599711788485":[{"subitem_1599711798761":"Conference Place","subitem_1599711803382":"ja"}],"subitem_1599711813532":"JPN"}]},"item_1617258105262":{"attribute_name":"Resource Type","attribute_value_mlt":[{"resourcetype":"dataset","resourceuri":"http://purl.org/coar/resource_type/c_ddb1"}]},"item_1617265215918":{"attribute_name":"Version Type","attribute_value_mlt":[{"subitem_1522305645492":"AO","subitem_1600292170262":"http://purl.org/coar/version/c_b1a7d7d4d402bcce"}]},"item_1617349709064":{"attribute_name":"Contributor","attribute_value_mlt":[{"contributorMails":[{"contributorMail":"wekosoftware@nii.ac.jp"}],"contributorNames":[{"contributorName":"情報, 太郎","lang":"ja"},{"contributorName":"ジョウホウ, タロウ","lang":"ja-Kana"},{"contributorName":"Joho, Taro","lang":"en"}],"contributorType":"ContactPerson","familyNames":[{"familyName":"情報","familyNameLang":"ja"},{"familyName":"ジョウホウ","familyNameLang":"ja-Kana"},{"familyName":"Joho","familyNameLang":"en"}],"givenNames":[{"givenName":"太郎","givenNameLang":"ja"},{"givenName":"タロウ","givenNameLang":"ja-Kana"},{"givenName":"Taro","givenNameLang":"en"}],"nameIdentifiers":[{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"ORCID","nameIdentifierURI":"https://orcid.org/"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"CiNii","nameIdentifierURI":"https://ci.nii.ac.jp/"},{"nameIdentifier":"xxxxxxx","nameIdentifierScheme":"KAKEN2","nameIdentifierURI":"https://kaken.nii.ac.jp/"}]}]},"item_1617349808926":{"attribute_name":"Version","attribute_value_mlt":[{"subitem_1523263171732":"Version"}]},"item_1617351524846":{"attribute_name":"APC","attribute_value_mlt":[{"subitem_1523260933860":"Unknown"}]},"item_1617353299429":{"attribute_name":"Relation","attribute_value_mlt":[{"subitem_1522306207484":"isVersionOf","subitem_1522306287251":{"subitem_1522306382014":"arXiv","subitem_1522306436033":"xxxxx"},"subitem_1523320863692":[{"subitem_1523320867455":"en","subitem_1523320909613":"Related Title"}]}]},"item_1617605131499":{"attribute_name":"File","attribute_type":"file","attribute_value_mlt":[{"accessrole":"open_access","date":[{"dateType":"Available","dateValue":"2021-07-12"}],"displaytype":"simple","filename":"1KB.pdf","filesize":[{"value":"1 KB"}],"format":"text/plain","mimetype":"application/pdf","url":{"url":"https://weko3.example.org/record/1/files/1KB.pdf"},"version_id":"9008626e-cb32-48bd-8409-1204f03b8077"}]},"item_1617610673286":{"attribute_name":"Rights Holder","attribute_value_mlt":[{"nameIdentifiers":[{"nameIdentifier":"xxxxxx","nameIdentifierScheme":"ORCID","nameIdentifierURI":"https://orcid.org/"}],"rightHolderNames":[{"rightHolderLanguage":"ja","rightHolderName":"Right Holder Name"}]}]},"item_1617620223087":{"attribute_name":"Heading","attribute_value_mlt":[{"subitem_1565671149650":"ja","subitem_1565671169640":"Banner Headline","subitem_1565671178623":"Subheading"},{"subitem_1565671149650":"en","subitem_1565671169640":"Banner Headline","subitem_1565671178623":"Subheding"}]},"item_1617944105607":{"attribute_name":"Degree Grantor","attribute_value_mlt":[{"subitem_1551256015892":[{"subitem_1551256027296":"xxxxxx","subitem_1551256029891":"kakenhi"}],"subitem_1551256037922":[{"subitem_1551256042287":"Degree Grantor Name","subitem_1551256047619":"en"}]}]},"item_title":"ja_conference paperITEM00000001(public_open_access_open_access_simple)","item_type_id":"15","owner":"1","path":["1661432090216"],"pubdate":{"attribute_name":"PubDate","attribute_value":"2021-08-06"},"publish_date":"2021-08-06","publish_status":"0","relation_version_is_last":true,"title":["ja_conference paperITEM00000001(public_open_access_open_access_simple)"],"weko_creator_id":"1","weko_shared_id":-1},"_oai":{"id":"oai:weko3.example.org:00000001","sets":["1661432090216"]},"accessRights":["open access"],"alternative":["Alternative Title","Alternative Title"],"apc":["Unknown"],"author_link":["4"],"conference":{"conferenceCountry":["JPN"],"conferenceDate":["2020/12/11"],"conferenceName":["Conference Name"],"conferenceSequence":["1"],"conferenceSponsor":["Sponsor"],"conferenceVenue":["Conference Venue"]},"contributor":{"@attributes":{"contributorType":[["ContactPerson"]]},"affiliation":{"affiliationName":[],"nameIdentifier":[]},"contributorAlternative":[],"contributorName":["情報, 太郎","ジョウホウ, タロウ","Joho, Taro"],"familyName":["情報","ジョウホウ","Joho"],"givenName":["太郎","タロウ","Taro"],"nameIdentifier":["xxxxxxx","xxxxxxx","xxxxxxx"]},"control_number":"1","creator":{"affiliation":{"affiliationName":["University"],"nameIdentifier":["0000000121691048"]},"creatorAlternative":[],"creatorName":["情報, 太郎","ジョウホウ, タロウ","Joho, Taro","情報, 太郎","ジョウホウ, タロウ","Joho, Taro","情報, 太郎","ジョウホウ, タロウ","Joho, Taro"],"familyName":["情報","ジョウホウ","Joho","情報","ジョウホウ","Joho","情報","ジョウホウ","Joho"],"givenName":["太郎","タロウ","Taro","太郎","タロウ","Taro","太郎","タロウ","Taro"],"nameIdentifier":["4","xxxxxxx","xxxxxxx","zzzzzzz","xxxxxxx","xxxxxxx","zzzzzzz","xxxxxxx","xxxxxxx","zzzzzzz"]},"date":[{"dateType":"Available","value":"2021-06-30"}],"dateGranted":["2021-06-30"],"degreeGrantor":{"degreeGrantorName":["Degree Grantor Name"],"nameIdentifier":["xxxxxx"]},"degreeName":["Degree Name"],"description":[{"descriptionType":"Abstract","value":"Description\\nDescription<br/>Description"},{"descriptionType":"Abstract","value":"概要\\n概要\\n概要\\n概要"}],"feedback_mail_list":[{"author_id":"","email":"wekosoftware@nii.ac.jp"}],"fundingReference":{"awardNumber":["Award Number"],"awardTitle":["Award Title"],"funderIdentifier":["http://xxx"],"funderName":["Funder Name"]},"geoLocation":{"geoLocationPlace":["Japan"]},"identifier":[{"identifierType":"URI","value":"http://localhost"}],"issue":["111"],"itemtype":"デフォルトアイテムタイプ（フル）","language":["jpn"],"numPages":["12"],"pageEnd":["3"],"pageStart":["1"],"path":["1661432090216"],"publish_date":"2021-08-06","publish_status":"0","publisher":["Publisher"],"relation":{"@attributes":{"relationType":[["isVersionOf"]]},"relatedIdentifier":[{"identifierType":"arXiv","value":"xxxxx"}],"relatedTitle":["Related Title"]},"relation_version_is_last":true,"rights":["Rights Information"],"rightsHolder":{"nameIdentifier":["xxxxxx"],"rightsHolderName":["Right Holder Name"]},"sourceIdentifier":[{"identifierType":"ISSN","value":"xxxx-xxxx-xxxx"}],"sourceTitle":["Source Title"],"subject":[{"subjectScheme":"Other","value":"Sibject1"}],"temporal":["Temporal"],"title":["en_conference paperITEM00000001(public_open_access_simple)","ja_conference paperITEM00000001(public_open_access_open_access_simple)"],"type":["dataset"],"version":["Version"],"versiontype":["AO"],"volume":["1"],"weko_creator_id":"1","weko_shared_id":-1},"updated":"2022-08-26T12:57:36.376731+00:00"}}'}
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            res = export_items(post_data)
            assert res.status_code == 200


# def _get_max_export_items():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test__get_max_export_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test__get_max_export_items(app,users):
    with app.test_request_context():
        assert _get_max_export_items() == WEKO_ITEMS_UI_DEFAULT_MAX_EXPORT_NUM

    with app.test_request_context(headers=[("Accept-Language", "en")]):
        with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
            size = WEKO_ITEMS_UI_MAX_EXPORT_NUM_PER_ROLE[users[2]['obj'].roles[0].name]
            assert _get_max_export_items() == size


# def _export_item(record_id,
#     def del_hide_sub_metadata(keys, metadata):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test__export_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test__export_item(app,users,db_records,db_itemtype):
    depid, recid, parent, doi, record, item = db_records[0]
    records_data={'created': '2022-08-25T12:56:26.587349+00:00', 'id': 1, 'links': {'self': 'https://localhost:8443/api/records/1'}, 'metadata': {'_comment': ['en_conference paperITEM00000001(public_open_access_simple)', 'WEKO-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2', 'https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/', '4-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz', 'Joho, Taro,Joho, Taro,Joho, Taro', 'Joho,Joho,Joho', 'Taro,Taro,Taro', '0000000121691048', 'ISNI', 'http://isni.org/isni/0000000121691048', 'University,Source Title,1,111,12,1,3,Degree Name,2021-06-30,xxxxxx,kakenhi,Degree Grantor Name', 'Conference Name', '1', 'JPN', 'Sponsor', '2000', '12', '1', '2020', '12', '2020/12/11', '1', 'Conference Venue', 'Conference Place'], '_files_info': [{'extention': 'pdf', 'label': '1KB.pdf', 'url': 'https://weko3.example.org/record/1/files/1KB.pdf'}], '_item_metadata': {'_oai': {'id': 'oai:weko3.example.org:00000001', 'sets': ['1661432090216']}, 'author_link': ['4'], 'control_number': '1', 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000001(public_open_access_simple)', 'subitem_1551255648112': 'en'}]}, 'item_1617186385884': {'attribute_name': 'Alternative Title', 'attribute_value_mlt': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}]}, 'item_1617186419668': {'attribute_name': 'Creator', 'attribute_type': 'creator', 'attribute_value_mlt': [{'creatorAffiliations': [{'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048'}], 'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}]}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '4', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}]}, 'item_1617186476635': {'attribute_name': 'Access Rights', 'attribute_value_mlt': [{'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}]}, 'item_1617186499011': {'attribute_name': 'Rights', 'attribute_value_mlt': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}]}, 'item_1617186609386': {'attribute_name': 'Subject', 'attribute_value_mlt': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}]}, 'item_1617186626617': {'attribute_name': 'Description', 'attribute_value_mlt': [{'subitem_description': 'Description\nDescription<br/>Description', 'subitem_description_language': 'en', 'subitem_description_type': 'Abstract'}, {'subitem_description': '概要\n概要\n概要\n概要', 'subitem_description_language': 'ja', 'subitem_description_type': 'Abstract'}]}, 'item_1617186643794': {'attribute_name': 'Publisher', 'attribute_value_mlt': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}]}, 'item_1617186660861': {'attribute_name': 'Date', 'attribute_value_mlt': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}]}, 'item_1617186702042': {'attribute_name': 'Language', 'attribute_value_mlt': [{'subitem_1551255818386': 'jpn'}]}, 'item_1617186783814': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_identifier_type': 'URI', 'subitem_identifier_uri': 'http://localhost'}]}, 'item_1617186859717': {'attribute_name': 'Temporal', 'attribute_value_mlt': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}]}, 'item_1617186882738': {'attribute_name': 'Geo Location', 'attribute_value_mlt': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}]}, 'item_1617186901218': {'attribute_name': 'Funding Reference', 'attribute_value_mlt': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}]}, 'item_1617186920753': {'attribute_name': 'Source Identifier', 'attribute_value_mlt': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}]}, 'item_1617186941041': {'attribute_name': 'Source Title', 'attribute_value_mlt': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}]}, 'item_1617186959569': {'attribute_name': 'Volume Number', 'attribute_value_mlt': [{'subitem_1551256328147': '1'}]}, 'item_1617186981471': {'attribute_name': 'Issue Number', 'attribute_value_mlt': [{'subitem_1551256294723': '111'}]}, 'item_1617186994930': {'attribute_name': 'Number of Pages', 'attribute_value_mlt': [{'subitem_1551256248092': '12'}]}, 'item_1617187024783': {'attribute_name': 'Page Start', 'attribute_value_mlt': [{'subitem_1551256198917': '1'}]}, 'item_1617187045071': {'attribute_name': 'Page End', 'attribute_value_mlt': [{'subitem_1551256185532': '3'}]}, 'item_1617187112279': {'attribute_name': 'Degree Name', 'attribute_value_mlt': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}]}, 'item_1617187136212': {'attribute_name': 'Date Granted', 'attribute_value_mlt': [{'subitem_1551256096004': '2021-06-30'}]}, 'item_1617187187528': {'attribute_name': 'Conference', 'attribute_value_mlt': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourcetype': 'dataset', 'resourceuri': 'http://purl.org/coar/resource_type/c_ddb1'}]}, 'item_1617265215918': {'attribute_name': 'Version Type', 'attribute_value_mlt': [{'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}]}, 'item_1617349709064': {'attribute_name': 'Contributor', 'attribute_value_mlt': [{'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'contributorName': '情報, 太郎', 'lang': 'ja'}, {'contributorName': 'ジョウホウ, タロウ', 'lang': 'ja-Kana'}, {'contributorName': 'Joho, Taro', 'lang': 'en'}], 'contributorType': 'ContactPerson', 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}]}, 'item_1617349808926': {'attribute_name': 'Version', 'attribute_value_mlt': [{'subitem_1523263171732': 'Version'}]}, 'item_1617351524846': {'attribute_name': 'APC', 'attribute_value_mlt': [{'subitem_1523260933860': 'Unknown'}]}, 'item_1617353299429': {'attribute_name': 'Relation', 'attribute_value_mlt': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}]}, 'item_1617605131499': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [{'accessrole': 'open_access', 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'displaytype': 'simple', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'format': 'text/plain', 'mimetype': 'application/pdf', 'url': {'url': 'https://weko3.example.org/record/1/files/1KB.pdf'}, 'version_id': '9008626e-cb32-48bd-8409-1204f03b8077'}]}, 'item_1617610673286': {'attribute_name': 'Rights Holder', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}], 'rightHolderNames': [{'rightHolderLanguage': 'ja', 'rightHolderName': 'Right Holder Name'}]}]}, 'item_1617620223087': {'attribute_name': 'Heading', 'attribute_value_mlt': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}]}, 'item_1617944105607': {'attribute_name': 'Degree Grantor', 'attribute_value_mlt': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}]}, 'item_title': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'item_type_id': '15', 'owner': '1', 'path': ['1661432090216'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2021-08-06'}, 'publish_date': '2021-08-06', 'publish_status': '0', 'relation_version_is_last': True, 'title': ['ja_conference paperITEM00000001(public_open_access_open_access_simple)'], 'weko_creator_id': '1', 'weko_shared_id': -1}, '_oai': {'id': 'oai:weko3.example.org:00000001', 'sets': ['1661432090216']}, 'accessRights': ['open access'], 'alternative': ['Alternative Title', 'Alternative Title'], 'apc': ['Unknown'], 'author_link': ['4'], 'conference': {'conferenceCountry': ['JPN'], 'conferenceDate': ['2020/12/11'], 'conferenceName': ['Conference Name'], 'conferenceSequence': ['1'], 'conferenceSponsor': ['Sponsor'], 'conferenceVenue': ['Conference Venue']}, 'contributor': {'@attributes': {'contributorType': [['ContactPerson']]}, 'affiliation': {'affiliationName': [], 'nameIdentifier': []}, 'contributorAlternative': [], 'contributorName': ['情報, 太郎', 'ジョウホウ, タロウ', 'Joho, Taro'], 'familyName': ['情報', 'ジョウホウ', 'Joho'], 'givenName': ['太郎', 'タロウ', 'Taro'], 'nameIdentifier': ['xxxxxxx', 'xxxxxxx', 'xxxxxxx']}, 'control_number': '1', 'creator': {'affiliation': {'affiliationName': ['University'], 'nameIdentifier': ['0000000121691048']}, 'creatorAlternative': [], 'creatorName': ['情報, 太郎', 'ジョウホウ, タロウ', 'Joho, Taro', '情報, 太郎', 'ジョウホウ, タロウ', 'Joho, Taro', '情報, 太郎', 'ジョウホウ, タロウ', 'Joho, Taro'], 'familyName': ['情報', 'ジョウホウ', 'Joho', '情報', 'ジョウホウ', 'Joho', '情報', 'ジョウホウ', 'Joho'], 'givenName': ['太郎', 'タロウ', 'Taro', '太郎', 'タロウ', 'Taro', '太郎', 'タロウ', 'Taro'], 'nameIdentifier': ['4', 'xxxxxxx', 'xxxxxxx', 'zzzzzzz', 'xxxxxxx', 'xxxxxxx', 'zzzzzzz', 'xxxxxxx', 'xxxxxxx', 'zzzzzzz']}, 'date': [{'dateType': 'Available', 'value': '2021-06-30'}], 'dateGranted': ['2021-06-30'], 'degreeGrantor': {'degreeGrantorName': ['Degree Grantor Name'], 'nameIdentifier': ['xxxxxx']}, 'degreeName': ['Degree Name'], 'description': [{'descriptionType': 'Abstract', 'value': 'Description\nDescription<br/>Description'}, {'descriptionType': 'Abstract', 'value': '概要\n概要\n概要\n概要'}], 'feedback_mail_list': [{'author_id': '', 'email': 'wekosoftware@nii.ac.jp'}], 'fundingReference': {'awardNumber': ['Award Number'], 'awardTitle': ['Award Title'], 'funderIdentifier': ['http://xxx'], 'funderName': ['Funder Name']}, 'geoLocation': {'geoLocationPlace': ['Japan']}, 'identifier': [{'identifierType': 'URI', 'value': 'http://localhost'}], 'issue': ['111'], 'itemtype': 'デフォルトアイテムタイプ（フル）', 'language': ['jpn'], 'numPages': ['12'], 'pageEnd': ['3'], 'pageStart': ['1'], 'path': ['1661432090216'], 'publish_date': '2021-08-06', 'publish_status': '0', 'publisher': ['Publisher'], 'relation': {'@attributes': {'relationType': [['isVersionOf']]}, 'relatedIdentifier': [{'identifierType': 'arXiv', 'value': 'xxxxx'}], 'relatedTitle': ['Related Title']}, 'relation_version_is_last': True, 'rights': ['Rights Information'], 'rightsHolder': {'nameIdentifier': ['xxxxxx'], 'rightsHolderName': ['Right Holder Name']}, 'sourceIdentifier': [{'identifierType': 'ISSN', 'value': 'xxxx-xxxx-xxxx'}], 'sourceTitle': ['Source Title'], 'subject': [{'subjectScheme': 'Other', 'value': 'Sibject1'}], 'temporal': ['Temporal'], 'title': ['en_conference paperITEM00000001(public_open_access_simple)', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)'], 'type': ['dataset'], 'version': ['Version'], 'versiontype': ['AO'], 'volume': ['1'], 'weko_creator_id': '1', 'weko_shared_id': -1}, 'updated': '2022-08-26T12:57:36.376731+00:00'}
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
            assert _export_item(1,'JSON',False,'./tests/data/',records_data) == ({'files': [],'item_type_id': '1','name': 'recid_1','path': 'recid_1','record_id': record.id }, {'1': {'weko_creator_id': '1', 'weko_shared_id': -1}})


# def _custom_export_metadata(record_metadata: dict, hide_item: bool = True,
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test__custom_export_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test__custom_export_metadata(app,db_itemtype,users):
    meta_data = {'_oai': {'id': 'oai:weko3.example.org:00000001', 'sets': ['1661432090216']}, 'path': ['1661432090216'], 'owner': '1', 'recid': '1', 'title': ['ja_conference paperITEM00000001(public_open_access_open_access_simple)'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2021-08-06'}, '_buckets': {'deposit': 'e6990773-b40b-4527-88d3-e175e01da5cd'}, '_deposit': {'id': '1', 'pid': {'type': 'depid', 'value': '1', 'revision_id': 0}, 'owners': [1], 'status': 'published'}, 'item_title': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'author_link': ['4'], 'item_type_id': '1', 'publish_date': '2021-08-06', 'control_number': '1', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000001(public_open_access_simple)', 'subitem_1551255648112': 'en'}]}, 'item_1617186385884': {'attribute_name': 'Alternative Title', 'attribute_value_mlt': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}]}, 'item_1617186419668': {'attribute_name': 'Creator', 'attribute_type': 'creator', 'attribute_value_mlt': [{'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '4', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'creatorAffiliations': [{'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}], 'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI'}]}]}, {'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}]}, {'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}]}]}, 'item_1617186476635': {'attribute_name': 'Access Rights', 'attribute_value_mlt': [{'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}]}, 'item_1617186499011': {'attribute_name': 'Rights', 'attribute_value_mlt': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}]}, 'item_1617186609386': {'attribute_name': 'Subject', 'attribute_value_mlt': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}]}, 'item_1617186626617': {'attribute_name': 'Description', 'attribute_value_mlt': [{'subitem_description': 'Description\nDescription<br/>Description', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'en'}, {'subitem_description': '概要\n概要\n概要\n概要', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'ja'}]}, 'item_1617186643794': {'attribute_name': 'Publisher', 'attribute_value_mlt': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}]}, 'item_1617186660861': {'attribute_name': 'Date', 'attribute_value_mlt': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}]}, 'item_1617186702042': {'attribute_name': 'Language', 'attribute_value_mlt': [{'subitem_1551255818386': 'jpn'}]}, 'item_1617186783814': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_identifier_uri': 'http://localhost', 'subitem_identifier_type': 'URI'}]}, 'item_1617186859717': {'attribute_name': 'Temporal', 'attribute_value_mlt': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}]}, 'item_1617186882738': {'attribute_name': 'Geo Location', 'attribute_value_mlt': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}]}, 'item_1617186901218': {'attribute_name': 'Funding Reference', 'attribute_value_mlt': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}]}, 'item_1617186920753': {'attribute_name': 'Source Identifier', 'attribute_value_mlt': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}]}, 'item_1617186941041': {'attribute_name': 'Source Title', 'attribute_value_mlt': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}]}, 'item_1617186959569': {'attribute_name': 'Volume Number', 'attribute_value_mlt': [{'subitem_1551256328147': '1'}]}, 'item_1617186981471': {'attribute_name': 'Issue Number', 'attribute_value_mlt': [{'subitem_1551256294723': '111'}]}, 'item_1617186994930': {'attribute_name': 'Number of Pages', 'attribute_value_mlt': [{'subitem_1551256248092': '12'}]}, 'item_1617187024783': {'attribute_name': 'Page Start', 'attribute_value_mlt': [{'subitem_1551256198917': '1'}]}, 'item_1617187045071': {'attribute_name': 'Page End', 'attribute_value_mlt': [{'subitem_1551256185532': '3'}]}, 'item_1617187112279': {'attribute_name': 'Degree Name', 'attribute_value_mlt': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}]}, 'item_1617187136212': {'attribute_name': 'Date Granted', 'attribute_value_mlt': [{'subitem_1551256096004': '2021-06-30'}]}, 'item_1617187187528': {'attribute_name': 'Conference', 'attribute_value_mlt': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_ddb1', 'resourcetype': 'dataset'}]}, 'item_1617265215918': {'attribute_name': 'Version Type', 'attribute_value_mlt': [{'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}]}, 'item_1617349709064': {'attribute_name': 'Contributor', 'attribute_value_mlt': [{'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'contributorType': 'ContactPerson', 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'lang': 'ja', 'contributorName': '情報, 太郎'}, {'lang': 'ja-Kana', 'contributorName': 'ジョウホウ, タロウ'}, {'lang': 'en', 'contributorName': 'Joho, Taro'}]}]}, 'item_1617349808926': {'attribute_name': 'Version', 'attribute_value_mlt': [{'subitem_1523263171732': 'Version'}]}, 'item_1617351524846': {'attribute_name': 'APC', 'attribute_value_mlt': [{'subitem_1523260933860': 'Unknown'}]}, 'item_1617353299429': {'attribute_name': 'Relation', 'attribute_value_mlt': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}]}, 'item_1617605131499': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [{'url': {'url': 'https://weko3.example.org/record/1/files/1KB.pdf'}, 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'format': 'text/plain', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'mimetype': 'application/pdf', 'accessrole': 'open_access', 'version_id': '9008626e-cb32-48bd-8409-1204f03b8077', 'displaytype': 'simple'}]}, 'item_1617610673286': {'attribute_name': 'Rights Holder', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}], 'rightHolderNames': [{'rightHolderName': 'Right Holder Name', 'rightHolderLanguage': 'ja'}]}]}, 'item_1617620223087': {'attribute_name': 'Heading', 'attribute_value_mlt': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}]}, 'item_1617944105607': {'attribute_name': 'Degree Grantor', 'attribute_value_mlt': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}]}, 'relation_version_is_last': True}
    meta_data_pre = copy.deepcopy(meta_data)

    with app.test_request_context():
        _custom_export_metadata(meta_data)
        meta_diff = diff(meta_data_pre,meta_data)
        assert list(meta_diff) == [('change', ['item_1617605131499', 'attribute_value_mlt', 0, 'url', 'url'], ('https://weko3.example.org/record/1/files/1KB.pdf', 'https://localhost/record/1/files/1KB.pdf')), ('add', '', [('weko_creator_id', '1')])]

        meta_data = copy.deepcopy(meta_data_pre)
        _custom_export_metadata(meta_data,True)
        meta_diff = diff(meta_data_pre,meta_data)
        assert list(meta_diff) ==[('change',  ['item_1617605131499', 'attribute_value_mlt', 0, 'url', 'url'], ('https://weko3.example.org/record/1/files/1KB.pdf',   'https://localhost/record/1/files/1KB.pdf')), ('add', '', [('weko_creator_id', '1')])]

        meta_data = copy.deepcopy(meta_data_pre)
        _custom_export_metadata(meta_data,False,True)
        meta_diff = diff(meta_data_pre,meta_data)
        assert list(meta_diff) == [('change',  ['item_1617605131499', 'attribute_value_mlt', 0, 'url', 'url'], ('https://weko3.example.org/record/1/files/1KB.pdf',   'https://localhost/record/1/files/1KB.pdf'))]

        meta_data = copy.deepcopy(meta_data_pre)
        _custom_export_metadata(meta_data,True,True)
        meta_diff = diff(meta_data_pre,meta_data)
        assert list(meta_diff) == [('change',  ['item_1617605131499', 'attribute_value_mlt', 0, 'url', 'url'], ('https://weko3.example.org/record/1/files/1KB.pdf',   'https://localhost/record/1/files/1KB.pdf')), ('add', '', [('weko_creator_id', '1')])]

    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
            meta_data = copy.deepcopy(meta_data_pre)
            _custom_export_metadata(meta_data)
            meta_diff = diff(meta_data_pre,meta_data)
            assert list(meta_diff) == [('change', ['item_1617605131499', 'attribute_value_mlt', 0, 'url', 'url'], ('https://weko3.example.org/record/1/files/1KB.pdf', 'https://localhost/record/1/files/1KB.pdf'))]

        with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
            meta_data = copy.deepcopy(meta_data_pre)
            _custom_export_metadata(meta_data,True)
            meta_diff = diff(meta_data_pre,meta_data)
            assert list(meta_diff) == [('change', ['item_1617605131499', 'attribute_value_mlt', 0, 'url', 'url'], ('https://weko3.example.org/record/1/files/1KB.pdf', 'https://localhost/record/1/files/1KB.pdf'))]

        with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
            meta_data = copy.deepcopy(meta_data_pre)
            _custom_export_metadata(meta_data,False,True)
            meta_diff = diff(meta_data_pre,meta_data)
            assert list(meta_diff) ==  [('change', ['item_1617605131499', 'attribute_value_mlt', 0, 'url', 'url'], ('https://weko3.example.org/record/1/files/1KB.pdf', 'https://localhost/record/1/files/1KB.pdf'))]

        with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
            meta_data = copy.deepcopy(meta_data_pre)
            _custom_export_metadata(meta_data,True,True)
            meta_diff = diff(meta_data_pre,meta_data)
            assert list(meta_diff) ==  [('change', ['item_1617605131499', 'attribute_value_mlt', 0, 'url', 'url'], ('https://weko3.example.org/record/1/files/1KB.pdf', 'https://localhost/record/1/files/1KB.pdf'))]



# def get_new_items_by_date(start_date: str, end_date: str, ranking=False) -> dict:
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_new_items_by_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_new_items_by_date(app,db_records):
    assert get_new_items_by_date("1900-01-01","2023-01-01",False) == {}
    assert get_new_items_by_date("1900-01-01","2023-01-01",True) == {}



# def update_schema_remove_hidden_item(schema, render, items_name):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_update_schema_remove_hidden_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_update_schema_remove_hidden_item(db_itemtype):
    item_type = db_itemtype["item_type"]
    system_properties = [
        "subitem_systemidt_identifier",
        "subitem_systemfile_datetime",
        "subitem_systemfile_filename",
        "subitem_system_id_rg_doi",
        "subitem_system_date_type",
        "subitem_system_date",
        "subitem_system_identifier_type",
        "subitem_system_identifier",
        "subitem_system_text",
    ]
    hidden_items = [
        item_type.form.index(form)
        for form in item_type.form
        if form.get("items")
        and form["items"][0]["key"].split(".")[1] == "subitem_systemidt_identifier"
    ]

    assert (
        update_schema_remove_hidden_item(
            item_type.schema, item_type.render, hidden_items
        )
        == ""
    )


# def get_files_from_metadata(record):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_files_from_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_files_from_metadata(app, db_records):

    depid, recid, parent, doi, record, item = db_records[0]
    with app.test_request_context():
        app.config.update(WEKO_BUCKET_QUOTA_SIZE=50 * 1024 * 1024 * 1024)
        assert get_files_from_metadata(record) == OrderedDict()


# def to_files_js(record):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_to_files_js -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_to_files_js(app, db_records):
    depid, recid, parent, doi, record, item = db_records[0]
    record = WekoDeposit(record.model.json, record.model)
    with app.test_request_context():
        assert to_files_js(record) == []


# def update_sub_items_by_user_role(item_type_id, schema_form):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_update_sub_items_by_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_update_sub_items_by_user_role(db_itemtype):
    item_type = db_itemtype["item_type"]
    form = copy.deepcopy(item_type.form)
    update_sub_items_by_user_role(item_type.id, form)
    assert form == item_type.form


# def remove_excluded_items_in_json_schema(item_id, json_schema):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_remove_excluded_items_in_json_schema -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_remove_excluded_items_in_json_schema(db_records,db_itemtype):
    depid, recid, parent, doi, record, item = db_records[0]
    item_type = db_itemtype["item_type"]
    schema = copy.deepcopy(item_type.schema)
    remove_excluded_items_in_json_schema(record.pid.pid_value, schema)
    assert schema == item_type.schema


# def get_excluded_sub_items(item_type_name):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_excluded_sub_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_excluded_sub_items(db_itemtype):
    item_type_name = db_itemtype["item_type_name"]
    assert get_excluded_sub_items(item_type_name.name) == []


# def get_current_user_role():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_current_user_role(app, users):
    app.config.update(
        WEKO_USERPROFILES_ROLES=["System Administrator", "Repository Administrator"]
    )
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert get_current_user_role() in users[1]["obj"].roles

    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        assert get_current_user_role() == ""


# def is_need_to_show_agreement_page(item_type_name):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_is_need_to_show_agreement_page -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
    ],
)
def test_is_need_to_show_agreement_page(db_itemtype,users,id,result):
    item_type_name = db_itemtype["item_type_name"]
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        assert is_need_to_show_agreement_page(item_type_name) == result


# def update_index_tree_for_record(pid_value, index_tree_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_update_index_tree_for_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_update_index_tree_for_record(app, db_itemtype, db_records, users, esindex):
    depid, recid, parent, doi, record, item = db_records[0]
    record['$schema'] = "/items/jsonschema/1"
    redis_connection = RedisConnection()
    datastore = redis_connection.connection(db=app.config['CACHE_REDIS_DB'], kv = True)
    datastore.put(
        app.config['WEKO_DEPOSIT_ITEMS_CACHE_PREFIX'].format(pid_value=recid.pid_value),
        (json.dumps(record)).encode('utf-8'))
    with patch("weko_deposit.api.WekoIndexer.upload_metadata", return_value=True):
        res = WekoRecord.get_record(recid.object_uuid)
        assert res["path"] == ['1']
        update_index_tree_for_record(recid.pid_value, 2)
        res = WekoRecord.get_record(recid.object_uuid)
        assert res["path"] == ['2']


# def validate_user_mail(users, activity_id, request_data, keys, result):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_validate_user_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_validate_user_mail(app, db, db_workflow):
    request_data={'activity_id': 'A-00000000-00000', 'user_to_check': ['user_b'], 'user_key_to_check': ['bbb'], 'auto_set_index_action': 'True'}
    users = ['user_a', 'user_c']
    keys = request_data.get('user_key_to_check', [])
    auto_set_index_action = request_data.get('auto_set_index_action', False)
    activity_id = request_data.get('activity_id')
    result = {
        "index": True
    }
    assert validate_user_mail(users, activity_id, request_data, keys, result)=={'index': True, 'validate_map_flow_and_item_type': False, 'validate_register_in_system': [], 'validate_required_email': ['bbb']}

    request_data={'user_a': 'test_a@test.com', 'activity_id': 'A-00000000-00000', 'user_to_check': [], 'user_key_to_check': [], 'auto_set_index_action': 'True'}
    activity_id = 'A-00000000-00000'
    users = ['user_a']
    keys = ['aaa']
    result = {
        "index": True
    }
    assert validate_user_mail(users, activity_id, request_data, keys, result)=={'index': True, 'validate_map_flow_and_item_type': False, 'validate_register_in_system': ['aaa'], 'validate_required_email': []}

    activity_action = ActivityAction(
        activity_id="A-00000000-00000",
        action_id=4,
        action_status="M",
        action_comment="test comment",
        action_handler=-1,
        action_order=1
    )
    db.session.add(activity_action)
    db.session.commit()
    request_data={'user_b': 'user@test.org', 'activity_id': 'A-00000000-00000', 'user_to_check': [], 'user_key_to_check': [], 'auto_set_index_action': 'True'}
    activity_id = 'A-00000000-00000'
    users = ['user_b']
    keys = ['ccc']
    result = {
        "index": True
    }
    res = ActivityAction.query.first()
    assert res.action_handler == -1
    assert validate_user_mail(users, activity_id, request_data, keys, result)=={'index': True, 'validate_map_flow_and_item_type': False, 'validate_register_in_system': [], 'validate_required_email': []}
    res = ActivityAction.query.first()
    assert res.action_handler == 1

# def check_approval_email(activity_id, user):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_check_approval_email -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_check_approval_email(users,db_workflow):
    activity = db_workflow['activity']
    assert check_approval_email(activity.activity_id,users[0]['obj'].email)==None


# def check_approval_email_in_flow(activity_id, users):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_check_approval_email_in_flow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_check_approval_email_in_flow(users,db_workflow):
    activity = db_workflow['activity']
    assert check_approval_email_in_flow(activity.activity_id,users[0]['obj'].email)==True



# def update_action_handler(activity_id, action_order, user_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_update_action_handler -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_update_action_handler(users,db_workflow):
    activity = db_workflow['activity']
    # Todo should change
    assert update_action_handler(activity.activity_id,None,users[0]['obj'].id)==None


# def validate_user_mail_and_index(request_data):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_validate_user_mail_and_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_validate_user_mail_and_index(app, db, db_workflow):
    activity_action = ActivityAction(
        activity_id="A-00000000-00000",
        action_id=4,
        action_status="M",
        action_comment="test comment",
        action_handler=-1,
        action_order=1
    )
    db.session.add(activity_action)
    db.session.commit()
    res = ActivityAction.query.first()
    assert res.action_handler == -1

    request_data={'user_b': 'user@test.org', 'activity_id': 'A-00000000-00000', 'user_to_check': ['user_b'], 'user_key_to_check': ['ccc'], 'auto_set_index_action': False}
    assert validate_user_mail_and_index(request_data)=={'index': True, 'validate_map_flow_and_item_type': False, 'validate_required_email': [], 'validate_register_in_system': []}
    res = ActivityAction.query.first()
    assert res.action_handler == 1

    request_data={'user_b': 'contributor@test.org', 'activity_id': 'A-00000000-00000', 'user_to_check': ['user_b'], 'user_key_to_check': ['ccc'], 'auto_set_index_action': True}
    assert validate_user_mail_and_index(request_data)=={'index': False, 'validate_map_flow_and_item_type': False, 'validate_required_email': [], 'validate_register_in_system': []}
    res = ActivityAction.query.first()
    assert res.action_handler == 2

    request_data={'user_b': 'contributor@test.org', 'activity_id': 'A-00000000-00000', 'user_to_check': ['user_b'], 'user_key_to_check': ['ccc'], 'auto_set_index_action': True}
    with patch("weko_items_ui.utils.db.session.commit", side_effect=Exception('')):
        assert validate_user_mail_and_index(request_data)=={'error': '', 'index': False, 'validate_map_flow_and_item_type': False, 'validate_required_email': [], 'validate_register_in_system': [], 'validation': False}
        res = ActivityAction.query.first()
        assert res.action_handler == 2


# def recursive_form(schema_form):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_recursive_form -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_recursive_form(db_itemtype):
    item_type = db_itemtype['item_type']
    assert recursive_form(item_type.form)==None


# def set_multi_language_name(item, cur_lang):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_set_multi_language_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_set_multi_language_name(db_itemtype):
    item_type = db_itemtype['item_type']
    item = item_type.form[1]['items'][1]
    item_pre = copy.deepcopy(item)
    set_multi_language_name(item,"ja")
    assert item_pre == item


# def get_data_authors_prefix_settings():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_data_authors_prefix_settings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_data_authors_prefix_settings(app,db_author):
    author_prefix = db_author["author_prefix"]
    with app.test_request_context():
        assert get_data_authors_prefix_settings()==author_prefix


# def get_data_authors_affiliation_settings():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_data_authors_affiliation_settings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_data_authors_affiliation_settings(app,db_author):
    affiliation_prefix = db_author["affiliation_prefix"]
    with app.test_request_context():
        assert get_data_authors_affiliation_settings()==affiliation_prefix


# def hide_meta_data_for_role(record):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_hide_meta_data_for_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, True),
        (1, False),
        (2, False),
        (3, False),
        (4, False),
        (5, True),
        (6, False),
        (7, True),
    ],
)
def test_hide_meta_data_for_role(users,db_records,id,result):
    depid, recid, parent, doi, record, item = db_records[0]
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        assert hide_meta_data_for_role(record) == result


# def get_ignore_item_from_mapping(_item_type_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_ignore_item_from_mapping -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_ignore_item_from_mapping(users,db):
    with open("tests/data/item_type_hide/schema.json") as f:
        schema = json.load(f)
    with open("tests/data/item_type_hide/form.json") as f:
        form = json.load(f)
    with open("tests/data/item_type_hide/render.json") as f:
        render = json.load(f)
    with open("tests/data/item_type_hide/mapping.json") as f:
        mapping = json.load(f)

    itemtype_name = ItemTypeName(id=10, name="test_itemtype_hide", has_site_license=True, is_active=True)
    itemtype = ItemType(id=10,name_id=10, schema=schema, form=form, render=render, tag=1)
    itemtype_mapping = ItemTypeMapping(id=10,item_type_id=10,mapping=mapping)

    with db.session.begin_nested():
        db.session.add(itemtype_name)
        db.session.add(itemtype)
        db.session.add(itemtype_mapping)
    db.session.commit()

    result =  get_ignore_item_from_mapping(10)
    test = ['title', 'contributor', 'type',  ['date'], ['creator', 'creatorName'], ['contributor', 'contributorName']]
    assert result == test


# def get_ignore_item_from_mapping(_item_type_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_ignore_item_from_mapping_with_item_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_ignore_item_from_mapping_with_item_type(users,db, db_itemtype):
    with open("tests/data/item_type_hide/schema.json") as f:
        schema = json.load(f)
    with open("tests/data/item_type_hide/form.json") as f:
        form = json.load(f)
    with open("tests/data/item_type_hide/render.json") as f:
        render = json.load(f)
    with open("tests/data/item_type_hide/mapping.json") as f:
        mapping = json.load(f)

    itemtype_name = ItemTypeName(id=20, name="test_itemtype_hide", has_site_license=True, is_active=True)
    itemtype = ItemType(id=20,name_id=20, schema=schema, form=form, render=render, tag=1)
    itemtype_mapping = ItemTypeMapping(id=20,item_type_id=20,mapping=mapping)

    with db.session.begin_nested():
        db.session.add(itemtype_name)
        db.session.add(itemtype)
        db.session.add(itemtype_mapping)
    db.session.commit()

    result =  get_ignore_item_from_mapping(20, item_type=itemtype)
    test = ['title', 'contributor', 'type',  ['date'], ['creator', 'creatorName'], ['contributor', 'contributorName']]
    assert result == test


# def get_mapping_name_item_type_by_key(key, item_type_mapping):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_mapping_name_item_type_by_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_mapping_name_item_type_by_key(users,db_itemtype):
    key = {'pubdate': {'title': 'PubDate', 'option': {'crtf': False, 'hidden': False, 'multiple': False, 'required': True, 'showlist': False}, 'input_type': 'datetime', 'title_i18n': {'en': 'PubDate', 'ja': '公開日'}, 'input_value': ''}}
    item_type_mapping = db_itemtype['item_type_mapping']
    assert get_mapping_name_item_type_by_key(key,item_type_mapping.mapping) == {'pubdate': {'title': 'PubDate', 'option': {'crtf': False, 'hidden': False, 'multiple': False, 'required': True, 'showlist': False}, 'input_type': 'datetime', 'title_i18n': {'en': 'PubDate', 'ja': '公開日'}, 'input_value': ''}}


# def get_mapping_name_item_type_by_sub_key(key, item_type_mapping):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_mapping_name_item_type_by_sub_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_mapping_name_item_type_by_sub_key(db):
    mapping = {
        "test1":{
            "test1_1":{
                "@value": "test1_1.path",
                "@attributes":{
                    "test1_1_1": "test1_1_1.path",
                    "test1_1_2": "test1_1_2.path"
                }
            },
            "test1_2":{
                "@value": "test1_2.path",
                "@attributes":{
                    "test1_2_1": "test1_2_1.path",
                    "test1_2_2": "test1_2_2.path"
                }
            },
            "@attributes":{"test1_3": "test1_3.path"},
        },
        "test2":{
            "test2_1":"test2_1.path"
        }
    }

    key = "test1_1.path"
    test = ["test1", "test1_1"]
    assert get_mapping_name_item_type_by_sub_key(key, mapping) == test

    key = "test1_1_1.path"
    test = ["test1", "test1_1", "test1_1_1"]
    assert get_mapping_name_item_type_by_sub_key(key, mapping) == test

    key = "not_exist_key"
    test = None
    assert get_mapping_name_item_type_by_sub_key(key, mapping) == test



# def get_hide_list_by_schema_form(item_type_id=None, schemaform=None):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_hide_list_by_schema_form -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_hide_list_by_schema_form(db_itemtype):
    item_type = db_itemtype['item_type']
    assert get_hide_list_by_schema_form(item_type,item_type.form) == []
    assert get_hide_list_by_schema_form(item_type) == []



# def get_hide_parent_keys(item_type_id=None, meta_list=None):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_hide_parent_keys -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_hide_parent_keys(db_itemtype):
    item_type = db_itemtype['item_type']
    meta_list = item_type.render.get('meta_list', {})
    assert get_hide_parent_keys(item_type,meta_list) == []


# def get_hide_parent_and_sub_keys(item_type):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_hide_parent_and_sub_keys -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_hide_parent_and_sub_keys(db_itemtype):
    item_type = db_itemtype['item_type']
    assert get_hide_parent_and_sub_keys(item_type) ==  ([], [])


# def get_item_from_option(_item_type_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_item_from_option -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_item_from_option(app,db_itemtype):
    with app.test_request_context():
        assert get_item_from_option(1) == []


# def get_item_from_option(_item_type_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_item_from_option_with_item_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_item_from_option_with_item_type(app,db_itemtype):
    item_type = db_itemtype['item_type']
    with app.test_request_context():
        assert get_item_from_option(1, item_type=ItemTypes(item_type.schema, model=item_type)) == []


# def get_options_list(item_type_id, json_item=None):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_options_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_options_list(app,db_itemtype):
    ret = {'pubdate': {'title': 'PubDate', 'option': {'crtf': False, 'hidden': False, 'multiple': False, 'required': True, 'showlist': False}, 'input_type': 'datetime', 'title_i18n': {'en': 'PubDate', 'ja': '公開日'}, 'input_value': ''}, 'item_1617186331708': {'title': 'Title', 'option': {'crtf': True, 'hidden': False, 'oneline': False, 'multiple': True, 'required': True, 'showlist': True}, 'input_type': 'cus_67', 'title_i18n': {'en': 'Title', 'ja': 'タイトル'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186385884': {'title': 'Alternative Title', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_69', 'title_i18n': {'en': 'Alternative Title', 'ja': 'その他のタイトル'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186419668': {'title': 'Creator', 'option': {'crtf': True, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_60', 'title_i18n': {'en': 'Creator', 'ja': '作成者'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186476635': {'title': 'Access Rights', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_4', 'title_i18n': {'en': 'Access Rights', 'ja': 'アクセス権'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186499011': {'title': 'Rights', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_14', 'title_i18n': {'en': 'Rights', 'ja': '権利情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186609386': {'title': 'Subject', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_6', 'title_i18n': {'en': 'Subject', 'ja': '主題'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186626617': {'title': 'Description', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_17', 'title_i18n': {'en': 'Description', 'ja': '内容記述'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186643794': {'title': 'Publisher', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_5', 'title_i18n': {'en': 'Publisher', 'ja': '出版者'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186660861': {'title': 'Date', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_11', 'title_i18n': {'en': 'Date', 'ja': '日付'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186702042': {'title': 'Language', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_71', 'title_i18n': {'en': 'Language', 'ja': '言語'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186783814': {'title': 'Identifier', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_176', 'title_i18n': {'en': 'Identifier', 'ja': '識別子'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186819068': {'title': 'Identifier Registration', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_16', 'title_i18n': {'en': 'Identifier Registration', 'ja': 'ID登録'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186859717': {'title': 'Temporal', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_18', 'title_i18n': {'en': 'Temporal', 'ja': '時間的範囲'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186882738': {'title': 'Geo Location', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_19', 'title_i18n': {'en': 'Geo Location', 'ja': '位置情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186901218': {'title': 'Funding Reference', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_21', 'title_i18n': {'en': 'Funding Reference', 'ja': '助成情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186920753': {'title': 'Source Identifier', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_10', 'title_i18n': {'en': 'Source Identifier', 'ja': '収録物識別子'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186941041': {'title': 'Source Title', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_13', 'title_i18n': {'en': 'Source Title', 'ja': '収録物名'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186959569': {'title': 'Volume Number', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_88', 'title_i18n': {'en': 'Volume Number', 'ja': '巻'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186981471': {'title': 'Issue Number', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_87', 'title_i18n': {'en': 'Issue Number', 'ja': '号'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186994930': {'title': 'Number of Pages', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_85', 'title_i18n': {'en': 'Number of Pages', 'ja': 'ページ数'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187024783': {'title': 'Page Start', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_84', 'title_i18n': {'en': 'Page Start', 'ja': '開始ページ'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187045071': {'title': 'Page End', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_83', 'title_i18n': {'en': 'Page End', 'ja': '終了ページ'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187056579': {'title': 'Bibliographic Information', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_102', 'title_i18n': {'en': 'Bibliographic Information', 'ja': '書誌情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187087799': {'title': 'Dissertation Number', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_82', 'title_i18n': {'en': 'Dissertation Number', 'ja': '学位授与番号'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187112279': {'title': 'Degree Name', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_80', 'title_i18n': {'en': 'Degree Name', 'ja': '学位名'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187136212': {'title': 'Date Granted', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_79', 'title_i18n': {'en': 'Date Granted', 'ja': '学位授与年月日'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187187528': {'title': 'Conference', 'option': {'crtf': True, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_75', 'title_i18n': {'en': 'Conference', 'ja': '会議記述'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617258105262': {'title': 'Resource Type', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': True, 'showlist': False}, 'input_type': 'cus_8', 'title_i18n': {'en': 'Resource Type', 'ja': '資源タイプ'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617265215918': {'title': 'Version Type', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_9', 'title_i18n': {'en': 'Version Type', 'ja': '出版タイプ'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617349709064': {'title': 'Contributor', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_62', 'title_i18n': {'en': 'Contributor', 'ja': '寄与者'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617349808926': {'title': 'Version', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_28', 'title_i18n': {'en': 'Version', 'ja': 'バージョン情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617351524846': {'title': 'APC', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_27', 'title_i18n': {'en': 'APC', 'ja': 'APC'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617353299429': {'title': 'Relation', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_12', 'title_i18n': {'en': 'Relation', 'ja': '関連情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617605131499': {'title': 'File', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_65', 'title_i18n': {'en': 'File', 'ja': 'ファイル情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617610673286': {'title': 'Rights Holder', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_3', 'title_i18n': {'en': 'Rights Holder', 'ja': '権利者情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617620223087': {'title': 'Heading', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_119', 'title_i18n': {'en': 'Heading', 'ja': '見出し'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617944105607': {'title': 'Degree Grantor', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_78', 'title_i18n': {'en': 'Degree Grantor', 'ja': '学位授与機関'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1662046377046': {'title': 'サムネイル', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_1037', 'title_i18n': {'en': 'thumbnail', 'ja': 'サムネイル'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}}
    with app.test_request_context():
        assert get_options_list(1) == ret


# def get_options_and_order_list(item_type_id, item_type_mapping=None,
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_options_and_order_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_options_and_order_list(db_itemtype):
    item_type = db_itemtype['item_type']
    ret = ({'pubdate': {'title': 'PubDate', 'option': {'crtf': False, 'hidden': False, 'multiple': False, 'required': True, 'showlist': False}, 'input_type': 'datetime', 'title_i18n': {'en': 'PubDate', 'ja': '公開日'}, 'input_value': ''}, 'item_1617186331708': {'title': 'Title', 'option': {'crtf': True, 'hidden': False, 'oneline': False, 'multiple': True, 'required': True, 'showlist': True}, 'input_type': 'cus_67', 'title_i18n': {'en': 'Title', 'ja': 'タイトル'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186385884': {'title': 'Alternative Title', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_69', 'title_i18n': {'en': 'Alternative Title', 'ja': 'その他のタイトル'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186419668': {'title': 'Creator', 'option': {'crtf': True, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_60', 'title_i18n': {'en': 'Creator', 'ja': '作成者'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186476635': {'title': 'Access Rights', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_4', 'title_i18n': {'en': 'Access Rights', 'ja': 'アクセス権'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186499011': {'title': 'Rights', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_14', 'title_i18n': {'en': 'Rights', 'ja': '権利情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186609386': {'title': 'Subject', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_6', 'title_i18n': {'en': 'Subject', 'ja': '主題'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186626617': {'title': 'Description', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_17', 'title_i18n': {'en': 'Description', 'ja': '内容記述'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186643794': {'title': 'Publisher', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_5', 'title_i18n': {'en': 'Publisher', 'ja': '出版者'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186660861': {'title': 'Date', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_11', 'title_i18n': {'en': 'Date', 'ja': '日付'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186702042': {'title': 'Language', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_71', 'title_i18n': {'en': 'Language', 'ja': '言語'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186783814': {'title': 'Identifier', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_176', 'title_i18n': {'en': 'Identifier', 'ja': '識別子'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186819068': {'title': 'Identifier Registration', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_16', 'title_i18n': {'en': 'Identifier Registration', 'ja': 'ID登録'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186859717': {'title': 'Temporal', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_18', 'title_i18n': {'en': 'Temporal', 'ja': '時間的範囲'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186882738': {'title': 'Geo Location', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_19', 'title_i18n': {'en': 'Geo Location', 'ja': '位置情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186901218': {'title': 'Funding Reference', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_21', 'title_i18n': {'en': 'Funding Reference', 'ja': '助成情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186920753': {'title': 'Source Identifier', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_10', 'title_i18n': {'en': 'Source Identifier', 'ja': '収録物識別子'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186941041': {'title': 'Source Title', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_13', 'title_i18n': {'en': 'Source Title', 'ja': '収録物名'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186959569': {'title': 'Volume Number', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_88', 'title_i18n': {'en': 'Volume Number', 'ja': '巻'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186981471': {'title': 'Issue Number', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_87', 'title_i18n': {'en': 'Issue Number', 'ja': '号'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186994930': {'title': 'Number of Pages', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_85', 'title_i18n': {'en': 'Number of Pages', 'ja': 'ページ数'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187024783': {'title': 'Page Start', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_84', 'title_i18n': {'en': 'Page Start', 'ja': '開始ページ'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187045071': {'title': 'Page End', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_83', 'title_i18n': {'en': 'Page End', 'ja': '終了ページ'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187056579': {'title': 'Bibliographic Information', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_102', 'title_i18n': {'en': 'Bibliographic Information', 'ja': '書誌情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187087799': {'title': 'Dissertation Number', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_82', 'title_i18n': {'en': 'Dissertation Number', 'ja': '学位授与番号'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187112279': {'title': 'Degree Name', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_80', 'title_i18n': {'en': 'Degree Name', 'ja': '学位名'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187136212': {'title': 'Date Granted', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_79', 'title_i18n': {'en': 'Date Granted', 'ja': '学位授与年月日'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187187528': {'title': 'Conference', 'option': {'crtf': True, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_75', 'title_i18n': {'en': 'Conference', 'ja': '会議記述'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617258105262': {'title': 'Resource Type', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': True, 'showlist': False}, 'input_type': 'cus_8', 'title_i18n': {'en': 'Resource Type', 'ja': '資源タイプ'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617265215918': {'title': 'Version Type', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_9', 'title_i18n': {'en': 'Version Type', 'ja': '出版タイプ'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617349709064': {'title': 'Contributor', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_62', 'title_i18n': {'en': 'Contributor', 'ja': '寄与者'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617349808926': {'title': 'Version', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_28', 'title_i18n': {'en': 'Version', 'ja': 'バージョン情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617351524846': {'title': 'APC', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_27', 'title_i18n': {'en': 'APC', 'ja': 'APC'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617353299429': {'title': 'Relation', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_12', 'title_i18n': {'en': 'Relation', 'ja': '関連情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617605131499': {'title': 'File', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_65', 'title_i18n': {'en': 'File', 'ja': 'ファイル情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617610673286': {'title': 'Rights Holder', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_3', 'title_i18n': {'en': 'Rights Holder', 'ja': '権利者情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617620223087': {'title': 'Heading', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_119', 'title_i18n': {'en': 'Heading', 'ja': '見出し'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617944105607': {'title': 'Degree Grantor', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_78', 'title_i18n': {'en': 'Degree Grantor', 'ja': '学位授与機関'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1662046377046': {'title': 'サムネイル', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_1037', 'title_i18n': {'en': 'thumbnail', 'ja': 'サムネイル'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}}, {'pubdate': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': '', 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': ''}, 'system_file': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'system_file': {'URI': {'@value': 'subitem_systemfile_filename_uri', '@attributes': {'label': 'subitem_systemfile_filename_label', 'objectType': 'subitem_systemfile_filename_type'}}, 'date': {'@value': 'subitem_systemfile_datetime_date', '@attributes': {'dateType': 'subitem_systemfile_datetime_type'}}, 'extent': {'@value': 'subitem_systemfile_size'}, 'version': {'@value': 'subitem_systemfile_version'}, 'mimeType': {'@value': 'subitem_systemfile_mimetype'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'system_file': {'URI': {'@value': 'subitem_systemfile_filename_uri', '@attributes': {'label': 'subitem_systemfile_filename_label', 'objectType': 'subitem_systemfile_filename_type'}}, 'date': {'@value': 'subitem_systemfile_datetime_date', '@attributes': {'dateType': 'subitem_systemfile_datetime_type'}}, 'extent': {'@value': 'subitem_systemfile_size'}, 'version': {'@value': 'subitem_systemfile_version'}, 'mimeType': {'@value': 'subitem_systemfile_mimetype'}}}}, 'item_1617186331708': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'title': {'@value': 'subitem_1551255647225', '@attributes': {'xml:lang': 'subitem_1551255648112'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'title': {'@value': 'subitem_1551255647225'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'title': {'@value': 'subitem_1551255647225', '@attributes': {'xml:lang': 'subitem_1551255648112'}}}}, 'item_1617186385884': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'alternative': {'@value': 'subitem_1551255720400', '@attributes': {'xml:lang': 'subitem_1551255721061'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'title': {'@value': 'subitem_1551255720400'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'alternative': {'@value': 'subitem_1551255720400', '@attributes': {'xml:lang': 'subitem_1551255721061'}}}}, 'item_1617186419668': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'creator': {'givenName': {'@value': 'givenNames.givenName', '@attributes': {'xml:lang': 'givenNames.givenNameLang'}}, 'familyName': {'@value': 'familyNames.familyName', '@attributes': {'xml:lang': 'familyNames.familyNameLang'}}, 'affiliation': {'nameIdentifier': {'@value': 'creatorAffiliations.affiliationNameIdentifiers.affiliationNameIdentifier', '@attributes': {'nameIdentifierURI': 'creatorAffiliations.affiliationNameIdentifiers.affiliationNameIdentifierURI', 'nameIdentifierScheme': 'creatorAffiliations.affiliationNameIdentifiers.affiliationNameIdentifierScheme'}}, 'affiliationName': {'@value': 'creatorAffiliations.affiliationNames.affiliationName', '@attributes': {'xml:lang': 'creatorAffiliations.affiliationNames.affiliationNameLang'}}}, 'creatorName': {'@value': 'creatorNames.creatorName', '@attributes': {'xml:lang': 'creatorNames.creatorNameLang'}}, 'nameIdentifier': {'@value': 'nameIdentifiers.nameIdentifier', '@attributes': {'nameIdentifierURI': 'nameIdentifiers.nameIdentifierURI', 'nameIdentifierScheme': 'nameIdentifiers.nameIdentifierScheme'}}, 'creatorAlternative': {'@value': 'creatorAlternatives.creatorAlternative', '@attributes': {'xml:lang': 'creatorAlternatives.creatorAlternativeLang'}}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'creator': {'@value': 'creatorNames.creatorName,nameIdentifiers.nameIdentifier'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'creator': {'givenName': {'@value': 'givenNames.givenName', '@attributes': {'xml:lang': 'givenNames.givenNameLang'}}, 'familyName': {'@value': 'familyNames.familyName', '@attributes': {'xml:lang': 'familyNames.familyNameLang'}}, 'affiliation': {'nameIdentifier': {'@value': 'creatorAffiliations.affiliationNameIdentifiers.affiliationNameIdentifier', '@attributes': {'nameIdentifierURI': 'creatorAffiliations.affiliationNameIdentifiers.affiliationNameIdentifierURI', 'nameIdentifierScheme': 'creatorAffiliations.affiliationNameIdentifiers.affiliationNameIdentifierScheme'}}, 'affiliationName': {'@value': 'creatorAffiliations.affiliationNames.affiliationName', '@attributes': {'xml:lang': 'creatorAffiliations.affiliationNames.affiliationNameLang'}}}, 'creatorName': {'@value': 'creatorNames.creatorName', '@attributes': {'xml:lang': 'creatorNames.creatorNameLang'}}, 'nameIdentifier': {'@value': 'nameIdentifiers.nameIdentifier', '@attributes': {'nameIdentifierURI': 'nameIdentifiers.nameIdentifierURI', 'nameIdentifierScheme': 'nameIdentifiers.nameIdentifierScheme'}}, 'creatorAlternative': {'@value': 'creatorAlternatives.creatorAlternative', '@attributes': {'xml:lang': 'creatorAlternatives.creatorAlternativeLang'}}}}}, 'item_1617186476635': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'accessRights': {'@value': 'subitem_1522299639480', '@attributes': {'rdf:resource': 'subitem_1600958577026'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'rights': {'@value': 'subitem_1522299639480'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'accessRights': {'@value': 'subitem_1522299639480', '@attributes': {'rdf:resource': 'subitem_1600958577026'}}}}, 'item_1617186499011': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'rights': {'@value': 'subitem_1522651041219', '@attributes': {'xml:lang': 'subitem_1522650717957', 'rdf:resource': 'subitem_1522650727486'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'rights': {'@value': 'subitem_1522651041219'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'rights': {'@value': 'subitem_1522651041219', '@attributes': {'xml:lang': 'subitem_1522650717957', 'rdf:resource': 'subitem_1522650727486'}}}}, 'item_1617186609386': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'subject': {'@value': 'subitem_1523261968819', '@attributes': {'xml:lang': 'subitem_1522299896455', 'subjectURI': 'subitem_1522300048512', 'subjectScheme': 'subitem_1522300014469'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'subject': {'@value': 'subitem_1523261968819'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'subject': {'@value': 'subitem_1523261968819', '@attributes': {'xml:lang': 'subitem_1522299896455', 'subjectURI': 'subitem_1522300048512', 'subjectScheme': 'subitem_1522300014469'}}}}, 'item_1617186626617': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'description': {'@value': 'subitem_description', '@attributes': {'xml:lang': 'subitem_description_language', 'descriptionType': 'subitem_description_type'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'description': {'@value': 'subitem_description'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'description': {'@value': 'subitem_description', '@attributes': {'xml:lang': 'subitem_description_language', 'descriptionType': 'subitem_description_type'}}}}, 'item_1617186643794': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'publisher': {'@value': 'subitem_1522300316516', '@attributes': {'xml:lang': 'subitem_1522300295150'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'publisher': {'@value': 'subitem_1522300316516'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'publisher': {'@value': 'subitem_1522300316516', '@attributes': {'xml:lang': 'subitem_1522300295150'}}}}, 'item_1617186660861': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'date': {'@value': 'subitem_1522300722591', '@attributes': {'dateType': 'subitem_1522300695726'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'date': {'@value': 'subitem_1522300722591'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'date': {'@value': 'subitem_1522300722591', '@attributes': {'dateType': 'subitem_1522300695726'}}}}, 'item_1617186702042': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'language': {'@value': 'subitem_1551255818386'}}, 'junii2_mapping': '', 'oai_dc_mapping': {'language': {'@value': 'subitem_1551255818386'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'language': {'@value': 'subitem_1551255818386'}}}, 'item_1617186783814': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'identifier': {'@value': 'subitem_identifier_uri', '@attributes': {'identifierType': 'subitem_identifier_type'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'identifier': {'@value': 'subitem_identifier_uri'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'identifier': {'@value': 'subitem_identifier_uri', '@attributes': {'identifierType': 'subitem_identifier_type'}}}}, 'item_1617186819068': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'identifierRegistration': {'@value': 'subitem_identifier_reg_text', '@attributes': {'identifierType': 'subitem_identifier_reg_type'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'identifierRegistration': {'@value': 'subitem_identifier_reg_text', '@attributes': {'identifierType': 'subitem_identifier_reg_type'}}}}, 'item_1617186859717': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'temporal': {'@value': 'subitem_1522658031721', '@attributes': {'xml:lang': 'subitem_1522658018441'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'coverage': {'@value': 'subitem_1522658031721'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'temporal': {'@value': 'subitem_1522658031721', '@attributes': {'xml:lang': 'subitem_1522658018441'}}}}, 'item_1617186882738': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'geoLocation': {'geoLocationBox': {'eastBoundLongitude': {'@value': 'subitem_geolocation_box.subitem_east_longitude'}, 'northBoundLatitude': {'@value': 'subitem_geolocation_box.subitem_north_latitude'}, 'southBoundLatitude': {'@value': 'subitem_geolocation_box.subitem_south_latitude'}, 'westBoundLongitude': {'@value': 'subitem_geolocation_box.subitem_west_longitude'}}, 'geoLocationPlace': {'@value': 'subitem_geolocation_place.subitem_geolocation_place_text'}, 'geoLocationPoint': {'pointLatitude': {'@value': 'subitem_geolocation_point.subitem_point_latitude'}, 'pointLongitude': {'@value': 'subitem_geolocation_point.subitem_point_longitude'}}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'coverage': {'@value': 'subitem_geolocation_place.subitem_geolocation_place_text'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'geoLocation': {'geoLocationBox': {'eastBoundLongitude': {'@value': 'subitem_geolocation_box.subitem_east_longitude'}, 'northBoundLatitude': {'@value': 'subitem_geolocation_box.subitem_north_latitude'}, 'southBoundLatitude': {'@value': 'subitem_geolocation_box.subitem_south_latitude'}, 'westBoundLongitude': {'@value': 'subitem_geolocation_box.subitem_west_longitude'}}, 'geoLocationPlace': {'@value': 'subitem_geolocation_place.subitem_geolocation_place_text'}, 'geoLocationPoint': {'pointLatitude': {'@value': 'subitem_geolocation_point.subitem_point_latitude'}, 'pointLongitude': {'@value': 'subitem_geolocation_point.subitem_point_longitude'}}}}}, 'item_1617186901218': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'fundingReference': {'awardTitle': {'@value': 'subitem_1522399651758.subitem_1522721929892', '@attributes': {'xml:lang': 'subitem_1522399651758.subitem_1522721910626'}}, 'funderName': {'@value': 'subitem_1522399412622.subitem_1522737543681', '@attributes': {'xml:lang': 'subitem_1522399412622.subitem_1522399416691'}}, 'awardNumber': {'@value': 'subitem_1522399571623.subitem_1522399628911', '@attributes': {'awardURI': 'subitem_1522399571623.subitem_1522399585738'}}, 'funderIdentifier': {'@value': 'subitem_1522399143519.subitem_1522399333375', '@attributes': {'funderIdentifierType': 'subitem_1522399143519.subitem_1522399281603'}}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'fundingReference': {'awardTitle': {'@value': 'subitem_1522399651758.subitem_1522721929892', '@attributes': {'xml:lang': 'subitem_1522399651758.subitem_1522721910626'}}, 'funderName': {'@value': 'subitem_1522399412622.subitem_1522737543681', '@attributes': {'xml:lang': 'subitem_1522399412622.subitem_1522399416691'}}, 'awardNumber': {'@value': 'subitem_1522399571623.subitem_1522399628911', '@attributes': {'awardURI': 'subitem_1522399571623.subitem_1522399585738'}}, 'funderIdentifier': {'@value': 'subitem_1522399143519.subitem_1522399333375', '@attributes': {'funderIdentifierType': 'subitem_1522399143519.subitem_1522399281603'}}}}}, 'item_1617186920753': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'sourceIdentifier': {'@value': 'subitem_1522646572813', '@attributes': {'identifierType': 'subitem_1522646500366'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'identifier': {'@value': 'subitem_1522646572813'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'sourceIdentifier': {'@value': 'subitem_1522646572813', '@attributes': {'identifierType': 'subitem_1522646500366'}}}}, 'item_1617186941041': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'sourceTitle': {'@value': 'subitem_1522650091861', '@attributes': {'xml:lang': 'subitem_1522650068558'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'identifier': {'@value': 'subitem_1522650091861'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'sourceTitle': {'@value': 'subitem_1522650091861', '@attributes': {'xml:lang': 'subitem_1522650068558'}}}}, 'item_1617186959569': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'volume': {'@value': 'subitem_1551256328147'}}, 'junii2_mapping': '', 'oai_dc_mapping': {'identifier': {'@value': 'subitem_1551256328147'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'volume': {'@value': 'subitem_1551256328147'}}}, 'item_1617186981471': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'issue': {'@value': 'subitem_1551256294723'}}, 'junii2_mapping': '', 'oai_dc_mapping': {'identifier': {'@value': 'subitem_1551256294723'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'issue': {'@value': 'subitem_1551256294723'}}}, 'item_1617186994930': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'numPages': {'@value': 'subitem_1551256248092'}}, 'junii2_mapping': '', 'oai_dc_mapping': {'identifier': {'@value': 'subitem_1551256248092'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'numPages': {'@value': 'subitem_1551256248092'}}}, 'item_1617187024783': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'pageStart': {'@value': 'subitem_1551256198917'}}, 'junii2_mapping': '', 'oai_dc_mapping': {'identifier': {'@value': 'subitem_1551256198917'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'pageStart': {'@value': 'subitem_1551256198917'}}}, 'item_1617187045071': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'pageEnd': {'@value': 'subitem_1551256185532'}}, 'junii2_mapping': '', 'oai_dc_mapping': {'identifier': {'@value': 'subitem_1551256185532'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'pageEnd': {'@value': 'subitem_1551256185532'}}}, 'item_1617187056579': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'date': {'@value': 'bibliographicIssueDates.bibliographicIssueDate', '@attributes': {'dateType': 'bibliographicIssueDates.bibliographicIssueDateType'}}, 'issue': {'@value': 'bibliographicIssueNumber'}, 'volume': {'@value': 'bibliographicVolumeNumber'}, 'pageEnd': {'@value': 'bibliographicPageEnd'}, 'numPages': {'@value': 'bibliographicNumberOfPages'}, 'pageStart': {'@value': 'bibliographicPageStart'}, 'sourceTitle': {'@value': 'bibliographic_titles.bibliographic_title', '@attributes': {'xml:lang': 'bibliographic_titles.bibliographic_titleLang'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'date': {'@value': 'bibliographicIssueDates.bibliographicIssueDate'}, 'identifier': {'@value': 'bibliographic_titles.bibliographic_title,bibliographicIssueNumber,bibliographicVolumeNumber,bibliographicPageEnd,bibliographicPageStart'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'date': {'@value': 'bibliographicIssueDates.bibliographicIssueDate', '@attributes': {'dateType': 'bibliographicIssueDates.bibliographicIssueDateType'}}, 'issue': {'@value': 'bibliographicIssueNumber'}, 'volume': {'@value': 'bibliographicVolumeNumber'}, 'pageEnd': {'@value': 'bibliographicPageEnd'}, 'numPages': {'@value': 'bibliographicNumberOfPages'}, 'pageStart': {'@value': 'bibliographicPageStart'}, 'sourceTitle': {'@value': 'bibliographic_titles.bibliographic_title', '@attributes': {'xml:lang': 'bibliographic_titles.bibliographic_titleLang'}}}}, 'item_1617187087799': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'dissertationNumber': {'@value': 'subitem_1551256171004'}}, 'junii2_mapping': '', 'oai_dc_mapping': {'identifier': {'@value': 'subitem_1551256171004'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'dissertationNumber': {'@value': 'subitem_1551256171004'}}}, 'item_1617187112279': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'degreeName': {'@value': 'subitem_1551256126428', '@attributes': {'xml:lang': 'subitem_1551256129013'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'description': {'@value': 'subitem_1551256126428'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'degreeName': {'@value': 'subitem_1551256126428', '@attributes': {'xml:lang': 'subitem_1551256129013'}}}}, 'item_1617187136212': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'dateGranted': {'@value': 'subitem_1551256096004'}}, 'junii2_mapping': '', 'oai_dc_mapping': {'date': {'@value': 'subitem_1551256096004'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'dateGranted': {'@value': 'subitem_1551256096004'}}}, 'item_1617187187528': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'conference': {'conferenceDate': {'@value': 'subitem_1599711699392.subitem_1599711704251', '@attributes': {'endDay': 'subitem_1599711699392.subitem_1599711735410', 'endYear': 'subitem_1599711699392.subitem_1599711743722', 'endMonth': 'subitem_1599711699392.subitem_1599711739022', 'startDay': 'subitem_1599711699392.subitem_1599711712451', 'xml:lang': 'subitem_1599711699392.subitem_1599711745532', 'startYear': 'subitem_1599711699392.subitem_1599711731891', 'startMonth': 'subitem_1599711699392.subitem_1599711727603'}}, 'conferenceName': {'@value': 'subitem_1599711633003.subitem_1599711636923', '@attributes': {'xml:lang': 'subitem_1599711633003.subitem_1599711645590'}}, 'conferenceVenue': {'@value': 'subitem_1599711758470.subitem_1599711769260', '@attributes': {'xml:lang': 'subitem_1599711758470.subitem_1599711775943'}}, 'conferenceCountry': {'@value': 'subitem_1599711813532'}, 'conferenceSponsor': {'@value': 'subitem_1599711660052.subitem_1599711680082', '@attributes': {'xml:lang': 'subitem_1599711660052.subitem_1599711686511'}}, 'conferenceSequence': {'@value': 'subitem_1599711655652'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'conference': {'conferenceDate': {'@value': 'subitem_1599711699392.subitem_1599711704251', '@attributes': {'endDay': 'subitem_1599711699392.subitem_1599711735410', 'endYear': 'subitem_1599711699392.subitem_1599711743722', 'endMonth': 'subitem_1599711699392.subitem_1599711739022', 'startDay': 'subitem_1599711699392.subitem_1599711712451', 'xml:lang': 'subitem_1599711699392.subitem_1599711745532', 'startYear': 'subitem_1599711699392.subitem_1599711731891', 'startMonth': 'subitem_1599711699392.subitem_1599711727603'}}, 'conferenceName': {'@value': 'subitem_1599711633003.subitem_1599711636923', '@attributes': {'xml:lang': 'subitem_1599711633003.subitem_1599711645590'}}, 'conferenceVenue': {'@value': 'subitem_1599711758470.subitem_1599711769260', '@attributes': {'xml:lang': 'subitem_1599711758470.subitem_1599711775943'}}, 'conferenceCountry': {'@value': 'subitem_1599711813532'}, 'conferenceSponsor': {'@value': 'subitem_1599711660052.subitem_1599711680082', '@attributes': {'xml:lang': 'subitem_1599711660052.subitem_1599711686511'}}, 'conferenceSequence': {'@value': 'subitem_1599711655652'}}}}, 'item_1617258105262': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'type': {'@value': 'resourcetype', '@attributes': {'rdf:resource': 'resourceuri'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'description': {'@value': 'resourceuri'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'type': {'@value': 'resourcetype', '@attributes': {'rdf:resource': 'resourceuri'}}}}, 'item_1617265215918': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'versiontype': {'@value': 'subitem_1522305645492', '@attributes': {'rdf:resource': 'subitem_1600292170262'}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'type': {'@value': 'subitem_1522305645492'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'versiontype': {'@value': 'subitem_1522305645492', '@attributes': {'rdf:resource': 'subitem_1600292170262'}}}}, 'item_1617349709064': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'contributor': {'givenName': {'@value': 'givenNames.givenName', '@attributes': {'xml:lang': 'givenNames.givenNameLang'}}, 'familyName': {'@value': 'familyNames.familyName', '@attributes': {'xml:lang': 'familyNames.familyNameLang'}}, '@attributes': {'contributorType': 'contributorType'}, 'affiliation': {'nameIdentifier': {'@value': 'contributorAffiliations.contributorAffiliationNameIdentifiers.contributorAffiliationNameIdentifier', '@attributes': {'nameIdentifierURI': 'contributorAffiliations.contributorAffiliationNameIdentifiers.contributorAffiliationURI', 'nameIdentifierScheme': 'contributorAffiliations.contributorAffiliationNameIdentifiers.contributorAffiliationScheme'}}, 'affiliationName': {'@value': 'contributorAffiliations.contributorAffiliationNames.contributorAffiliationName', '@attributes': {'xml:lang': 'contributorAffiliations.contributorAffiliationNames.contributorAffiliationNameLang'}}}, 'nameIdentifier': {'@value': 'nameIdentifiers.nameIdentifier', '@attributes': {'nameIdentifierURI': 'nameIdentifiers.nameIdentifierURI', 'nameIdentifierScheme': 'nameIdentifiers.nameIdentifierScheme'}}, 'contributorName': {'@value': 'contributorNames.contributorName', '@attributes': {'xml:lang': 'contributorNames.lang'}}, 'contributorAlternative': {'@value': 'contributorAlternatives.contributorAlternative', '@attributes': {'xml:lang': 'contributorAlternatives.contributorAlternativeLang'}}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'contributor': {'@value': 'contributorNames.contributorName,nameIdentifiers.nameIdentifier'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'contributor': {'givenName': {'@value': 'givenNames.givenName', '@attributes': {'xml:lang': 'givenNames.givenNameLang'}}, 'familyName': {'@value': 'familyNames.familyName', '@attributes': {'xml:lang': 'familyNames.familyNameLang'}}, '@attributes': {'contributorType': 'contributorType'}, 'affiliation': {'nameIdentifier': {'@value': 'contributorAffiliations.contributorAffiliationNameIdentifiers.contributorAffiliationNameIdentifier', '@attributes': {'nameIdentifierURI': 'contributorAffiliations.contributorAffiliationNameIdentifiers.contributorAffiliationURI', 'nameIdentifierScheme': 'contributorAffiliations.contributorAffiliationNameIdentifiers.contributorAffiliationScheme'}}, 'affiliationName': {'@value': 'contributorAffiliations.contributorAffiliationNames.contributorAffiliationName', '@attributes': {'xml:lang': 'contributorAffiliations.contributorAffiliationNames.contributorAffiliationNameLang'}}}, 'nameIdentifier': {'@value': 'nameIdentifiers.nameIdentifier', '@attributes': {'nameIdentifierURI': 'nameIdentifiers.nameIdentifierURI', 'nameIdentifierScheme': 'nameIdentifiers.nameIdentifierScheme'}}, 'contributorName': {'@value': 'contributorNames.contributorName', '@attributes': {'xml:lang': 'contributorNames.lang'}}, 'contributorAlternative': {'@value': 'contributorAlternatives.contributorAlternative', '@attributes': {'xml:lang': 'contributorAlternatives.contributorAlternativeLang'}}}}}, 'item_1617349808926': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'version': {'@value': 'subitem_1523263171732'}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'version': {'@value': 'subitem_1523263171732'}}}, 'item_1617351524846': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'apc': {'@value': 'subitem_1523260933860'}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'apc': {'@value': 'subitem_1523260933860'}}}, 'item_1617353299429': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'relation': {'@attributes': {'relationType': 'subitem_1522306207484'}, 'relatedTitle': {'@value': 'subitem_1523320863692.subitem_1523320909613', '@attributes': {'xml:lang': 'subitem_1523320863692.subitem_1523320867455'}}, 'relatedIdentifier': {'@value': 'subitem_1522306287251.subitem_1522306436033', '@attributes': {'identifierType': 'subitem_1522306287251.subitem_1522306382014'}}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'relation': {'@value': 'subitem_1522306287251.subitem_1522306436033,subitem_1523320863692.subitem_1523320909613'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'relation': {'@attributes': {'relationType': 'subitem_1522306207484'}, 'relatedTitle': {'@value': 'subitem_1523320863692.subitem_1523320909613', '@attributes': {'xml:lang': 'subitem_1523320863692.subitem_1523320867455'}}, 'relatedIdentifier': {'@value': 'subitem_1522306287251.subitem_1522306436033', '@attributes': {'identifierType': 'subitem_1522306287251.subitem_1522306382014'}}}}}, 'item_1617605131499': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'file': {'URI': {'@value': 'url.url', '@attributes': {'label': 'url.label', 'objectType': 'url.objectType'}}, 'date': {'@value': 'fileDate.fileDateValue', '@attributes': {'dateType': 'fileDate.fileDateType'}}, 'extent': {'@value': 'filesize.value'}, 'version': {'@value': 'version'}, 'mimeType': {'@value': 'format'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'file': {'URI': {'@value': 'url.url', '@attributes': {'label': 'url.label', 'objectType': 'url.objectType'}}, 'date': {'@value': 'fileDate.fileDateValue', '@attributes': {'dateType': 'fileDate.fileDateType'}}, 'extent': {'@value': 'filesize.value'}, 'version': {'@value': 'version'}, 'mimeType': {'@value': 'format'}}}}, 'item_1617610673286': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'rightsHolder': {'nameIdentifier': {'@value': 'nameIdentifiers.nameIdentifier', '@attributes': {'nameIdentifierURI': 'nameIdentifiers.nameIdentifierURI', 'nameIdentifierScheme': 'nameIdentifiers.nameIdentifierScheme'}}, 'rightsHolderName': {'@value': 'rightHolderNames.rightHolderName', '@attributes': {'xml:lang': 'rightHolderNames.rightHolderLanguage'}}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'rightsHolder': {'nameIdentifier': {'@value': 'nameIdentifiers.nameIdentifier', '@attributes': {'nameIdentifierURI': 'nameIdentifiers.nameIdentifierURI', 'nameIdentifierScheme': 'nameIdentifiers.nameIdentifierScheme'}}, 'rightsHolderName': {'@value': 'rightHolderNames.rightHolderName', '@attributes': {'xml:lang': 'rightHolderNames.rightHolderLanguage'}}}}}, 'item_1617620223087': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': '', 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': ''}, 'item_1617944105607': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'degreeGrantor': {'nameIdentifier': {'@value': 'subitem_1551256015892.subitem_1551256027296', '@attributes': {'nameIdentifierScheme': 'subitem_1551256015892.subitem_1551256029891'}}, 'degreeGrantorName': {'@value': 'subitem_1551256037922.subitem_1551256042287', '@attributes': {'xml:lang': 'subitem_1551256037922.subitem_1551256047619'}}}}, 'junii2_mapping': '', 'oai_dc_mapping': {'description': {'@value': 'subitem_1551256037922.subitem_1551256042287'}}, 'display_lang_type': '', 'jpcoar_v1_mapping': {'degreeGrantor': {'nameIdentifier': {'@value': 'subitem_1551256015892.subitem_1551256027296', '@attributes': {'nameIdentifierScheme': 'subitem_1551256015892.subitem_1551256029891'}}, 'degreeGrantorName': {'@value': 'subitem_1551256037922.subitem_1551256042287', '@attributes': {'xml:lang': 'subitem_1551256037922.subitem_1551256047619'}}}}}, 'system_identifier_doi': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'identifier': {'@value': 'subitem_systemidt_identifier', '@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'identifier': {'@value': 'subitem_systemidt_identifier', '@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}}}}, 'system_identifier_hdl': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'identifier': {'@value': 'subitem_systemidt_identifier', '@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'identifier': {'@value': 'subitem_systemidt_identifier', '@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}}}}, 'system_identifier_uri': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'identifier': {'@value': 'subitem_systemidt_identifier', '@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'identifier': {'@value': 'subitem_systemidt_identifier', '@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}}}}})
    assert get_options_and_order_list(item_type.id) == ret
    assert get_options_and_order_list(item_type.id, item_type_data=ItemTypes(item_type.schema, model=item_type)) == ret
    assert get_options_and_order_list(item_type.id, mapping_flag=False) == ret[0]


# def hide_table_row(table_row, hide_key):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_hide_table_row -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_hide_table_row(db_itemtype):
    item_type = db_itemtype['item_type']
    render = item_type.render
    assert hide_table_row(render.get('table_row'), [])==['item_1617186331708', 'item_1617186385884', 'item_1617186419668', 'item_1617349709064', 'item_1617186476635', 'item_1617351524846', 'item_1617186499011', 'item_1617610673286', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617258105262', 'item_1617349808926', 'item_1617265215918', 'item_1617186783814', 'item_1617186819068', 'item_1617353299429', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617186959569', 'item_1617186981471', 'item_1617186994930', 'item_1617187024783', 'item_1617187045071', 'item_1617187056579', 'item_1617187087799', 'item_1617187112279', 'item_1617187136212', 'item_1617944105607', 'item_1617187187528', 'item_1617605131499', 'item_1617620223087', 'item_1662046377046']


# def is_schema_include_key(schema):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_is_schema_include_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_is_schema_include_key():
    with open("tests/data/itemtype_schema.json", "r") as f:
        schema = json.load(f)

    assert is_schema_include_key(schema) == (True, False)


# def isExistKeyInDict(_key, _dict):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_isExistKeyInDict -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_isExistKeyInDict():
    assert isExistKeyInDict("a", {"a": {"value":"valueA"}})==True
    assert isExistKeyInDict("c", {"a": "valueA"})==False
    assert isExistKeyInDict("a", {"a": "valueA"})==False


# def set_validation_message(item, cur_lang):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_set_validation_message -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_set_validation_message(app):
    item = {
        "type": "string",
        "title": "Degree Grantor Name",
        "format": "text",
        "title_i18n": {"en": "Degree Grantor Name", "ja": "学位授与機関名"},
        "title_i18n_temp": {"en": "Degree Grantor Name", "ja": "学位授与機関名"},
    }
    cur_lang = "en"
    item2 = {
        "type": "string",
        "title": "Degree Grantor Name",
        "format": "text",
        "title_i18n": {"en": "Degree Grantor Name", "ja": "学位授与機関名"},
        "title_i18n_temp": {"en": "Degree Grantor Name", "ja": "学位授与機関名"},
    }

    with app.test_request_context():
        set_validation_message(item, cur_lang)
        assert item2 == item


# def translate_validation_message(item_property, cur_lang):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_translate_validation_message -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_translate_validation_message():
    cur_lang = "en"
    item_property = {
        "type": "string",
        "title": "Degree Grantor Name",
        "format": "text",
        "title_i18n": {"en": "Degree Grantor Name", "ja": "学位授与機関名"},
        "title_i18n_temp": {"en": "Degree Grantor Name", "ja": "学位授与機関名"},
    }
    item_property2 = {
        "type": "string",
        "title": "Degree Grantor Name",
        "format": "text",
        "title_i18n": {"en": "Degree Grantor Name", "ja": "学位授与機関名"},
        "title_i18n_temp": {"en": "Degree Grantor Name", "ja": "学位授与機関名"},
    }
    translate_validation_message(item_property, cur_lang)
    assert item_property == item_property2


# def get_workflow_by_item_type_id(item_type_name_id, item_type_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_workflow_by_item_type_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_workflow_by_item_type_id(app, db_workflow, db_itemtype):
    with app.test_request_context():
        assert get_workflow_by_item_type_id(1, 1) == db_workflow["workflow"]


# def validate_bibtex(record_ids):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_validate_bibtex -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_validate_bibtex(app, db, db_records, db_itemtype, db_oaischema):
    app.config.update(OAISERVER_XSL_URL=None)
    assert validate_bibtex([1]) == ""


# def make_bibtex_data(record_ids):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_make_bibtex_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_make_bibtex_data(db_records):
    assert make_bibtex_data([1])==""


# def translate_schema_form(form_element, cur_lang):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_translate_schema_form -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_translate_schema_form(db_itemtype):
    item_type = db_itemtype["item_type"]
    form_element = item_type.form[1]
    form_element_pre = copy.deepcopy(form_element)
    translate_schema_form(form_element, "ja")
    _diff = diff(form_element_pre,form_element)
    assert list(_diff)==[('change', ['items', 0, 'title'], ('Title', 'タイトル')), ('change', ['items', 1, 'title'], ('Language', '言語')), ('change', 'title', ('Title', 'タイトル'))]
    form_element = item_type.form[1]
    translate_schema_form(form_element, "en")
    _diff = diff(form_element_pre,form_element)
    assert list(_diff)==[]
    translate_schema_form(form_element, "fr")
    _diff = diff(form_element_pre,form_element)
    assert list(_diff)==[]

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_WekoQueryRankingHelper_get -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_WekoQueryRankingHelper_get(app, users, db_records,esindex,mocker):
    user = users[2]
    # add data to record_view
    view_data = [
        {"rec_index":0,"count":1,"date":"2023-08-24"}, # recid:1
        {"rec_index":1,"count":3,"date": "2023-08-23"}, # recid:1.1
        {"rec_index":6,"count":2,"date": "2023-08-25"}, # recid: 4
        {"rec_index":4,"count":5,"date": "2023-08-25"}, # recid: 3
        {"rec_index":0,"count":5,"date": "2022-08-25"} # recid: 1
    ]
    for data in view_data:
        _record=db_records[data["rec_index"]]
        pid = _record[1]
        record=_record[4]
        es_id = uuid.uuid4()
        body = {
            "timestamp":datetime.strptime(data["date"],"%Y-%m-%d"),"unique_id":str(es_id),"count":data["count"],"unique_count":data["count"],"country":None,"hostname":"None","remote_attr":"111.111.11.1","record_id":pid.object_uuid,"record_name":record["item_title"],"record_index_names":"test_index","pid_type":pid.pid_type,"pid_value":pid.pid_value,"cur_user_id":user["id"],"site_license_name":"","site_license_flag":False
        }
        esindex.index(index="test-stats-record-view",doc_type="record-view-day-aggregation",id=str(es_id),body=body)
    esindex.indices.flush(index="test-*")

    result = WekoQueryRankingHelper.get(
            start_date="2023-08-19",
            end_date="2023-09-01",
            agg_size=110,
            event_type='record-view',
            group_field='pid_value',
            count_field='count',
            ranking_type='most_view_ranking'
        )
    assert result == [{'key': '3', 'count': 5}, {'key': '1', 'count': 4}, {'key': '4', 'count': 2}]
    # raise Exception
    with patch("weko_items_ui.utils.json.loads",side_effect=Exception("test_error")):
        result = WekoQueryRankingHelper.get(
            start_date="2023-08-19",
            end_date="2023-09-01",
            agg_size=110,
            event_type='record-view',
            group_field='pid_value',
            count_field='count',
            ranking_type='most_view_ranking'
        )
        assert result == []

    # raise NotFoundError
    with patch("invenio_stats.queries.ESWekoRankingQuery.run",side_effect=es_exceptions.NotFoundError(404,"test_error")):
        result = WekoQueryRankingHelper.get(
            start_date="2023-08-19",
            end_date="2023-09-01",
            agg_size=110,
            event_type='record-view',
            group_field='pid_value',
            count_field='count',
            ranking_type='most_view_ranking'
        )
        assert result == []

# def get_ranking(settings):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_ranking -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_ranking(app, users, db_records, db_ranking, esindex,mocker):
    user = users[2]
    # add data to record_view
    today = datetime.today()
    view_data = [
        {"rec_index":0,"count":1,"date":today+timedelta(days=-2)}, # recid:1
        {"rec_index":1,"count":3,"date":today+timedelta(days=-2)}, # recid:1.1
        {"rec_index":6,"count":2,"date":today+timedelta(days=-2)}, # recid: 4
        {"rec_index":4,"count":5,"date":today+timedelta(days=-2)}, # recid: 3
        {"rec_index":0,"count":5,"date":today+timedelta(days=-370)} # recid: 1
    ]
    for data in view_data:
        _record=db_records[data["rec_index"]]
        pid = _record[1]
        record=_record[4]
        es_id = uuid.uuid4()
        body = {
            "timestamp":data["date"],"unique_id":str(es_id),"count":data["count"],"unique_count":data["count"],"country":None,"hostname":"None","remote_attr":"111.111.11.1","record_id":pid.object_uuid,"record_name":record["item_title"],"record_index_names":"test_index","pid_type":pid.pid_type,"pid_value":pid.pid_value,"cur_user_id":user["id"],"site_license_name":"","site_license_flag":False
        }
        esindex.index(index="test-stats-record-view",doc_type="record-view-day-aggregation",id=str(es_id),body=body)
    esindex.indices.flush(index="test-*")

    index_json = [
        {"children":[],"cid":1,"pid":0,"name":"Index(public_state = True,harvest_public_state = True)","id":"1"},
        {"children":[],"cid":2,"pid":0,"name":"Index(public_state = True,harvest_public_state = False)","id":"2"},
        {"children":[],"cid":3,"pid":0,"name":"Index(public_state = False,harvest_public_state = True)","id":"3"},
        {"children":[],"cid":4,"pid":0,"name":"Index(public_state = False,harvest_public_state = False)","id":"4"}
    ]
    mocker.patch("weko_items_ui.utils.Indexes.get_browsing_tree_ignore_more",return_value=index_json)
    title_mapping = {"item_1617186331708":{"jpcoar_mapping":{"title":{"@value":"subitem_1551255647225","@attributes":{"xml:lang":"subitem_1551255648112"}}}}}
    mocker.patch("weko_deposit.api.Mapping.get_record",return_value=title_mapping)
    settings = db_ranking['settings']
    with app.test_request_context():
        # get all ranking
        result = get_ranking(settings)
        test = {'most_reviewed_items': [{'key': '3', 'rank': 1, 'count': 5, 'title': 'title2', 'url': '../records/3'}, {'key': '1', 'rank': 2, 'count': 4, 'title': 'title', 'url': '../records/1'}, {'key': '4', 'rank': 3, 'count': 2, 'title': 'title2', 'url': '../records/4'}], 'most_downloaded_items': [], 'created_most_items_user': [], 'most_searched_keywords': [], 'new_items': []}
        assert result == test

        # get no ranking
        ranking_settings = RankingSettings(is_show=True,new_item_period=12,statistical_period=365,display_rank=10,rankings={"new_items": False, "most_reviewed_items": False, "most_downloaded_items": False, "most_searched_keywords": False, "created_most_items_user": False})
        result = get_ranking(ranking_settings)
        assert result == {}

# def __sanitize_string(s: str):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test___sanitize_string -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test___sanitize_string():
    # if ord(i) in [9, 10, 13] or (31 < ord(i) != 127):
    data = "hoge\x00hoge\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x7fhoge"
    assert __sanitize_string(data) == "hogehoge\t\n\rhoge"


# def sanitize_input_data(data):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_sanitize_input_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_sanitize_input_data():
    source_dict = {
        "metainfo": {
            "pubdate": "2022-08-19",
            "item_1617186331708": [
                {
                    "subitem_1551255647225": "hoge\x00hoge\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x7fhoge",
                    "subitem_1551255648112": "ja",
                }
            ],
            "item_1617186385884": [{}],
            "item_1617186419668": [
                {
                    "creatorAffiliations": [
                        {"affiliationNameIdentifiers": [{}], "affiliationNames": [{}]}
                    ],
                    "creatorAlternatives": [{}],
                    "creatorMails": [{}],
                    "creatorNames": [{}],
                    "familyNames": [{}],
                    "givenNames": [{}],
                    "nameIdentifiers": [{}],
                }
            ],
            "item_1617186499011": [{}],
            "item_1617186609386": [{}],
            "item_1617186626617": [{}],
            "item_1617186643794": [{}],
            "item_1617186660861": [{}],
            "item_1617186702042": [{}],
            "item_1617186783814": [{}],
            "item_1617186859717": [{}],
            "item_1617186882738": [{"subitem_geolocation_place": [{}]}],
            "item_1617186901218": [
                {"subitem_1522399412622": [{}], "subitem_1522399651758": [{}]}
            ],
            "item_1617186920753": [{}],
            "item_1617186941041": [{}],
            "item_1617187112279": [{}],
            "item_1617187187528": [
                {
                    "subitem_1599711633003": [{}],
                    "subitem_1599711660052": [{}],
                    "subitem_1599711758470": [{}],
                    "subitem_1599711788485": [{}],
                }
            ],
            "item_1617349709064": [
                {
                    "contributorAffiliations": [
                        {
                            "contributorAffiliationNameIdentifiers": [{}],
                            "contributorAffiliationNames": [{}],
                        }
                    ],
                    "contributorAlternatives": [{}],
                    "contributorMails": [{}],
                    "contributorNames": [{}],
                    "familyNames": [{}],
                    "givenNames": [{}],
                    "nameIdentifiers": [{}],
                }
            ],
            "item_1617353299429": [{"subitem_1523320863692": [{}]}],
            "item_1617605131499": [{"date": [{}], "fileDate": [{}], "filesize": [{}]}],
            "item_1617610673286": [{"nameIdentifiers": [{}], "rightHolderNames": [{}]}],
            "item_1617620223087": [{}],
            "item_1617944105607": [
                {"subitem_1551256015892": [{}], "subitem_1551256037922": [{}]}
            ],
            "item_1617187056579": {"bibliographic_titles": [{}]},
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            },
            "shared_user_id": -1,
        },
        "files": [],
        "endpoints": {"initialization": "/api/deposits/items"},
    }
    dest_dict = {
        "metainfo": {
            "pubdate": "2022-08-19",
            "item_1617186331708": [
                {
                    "subitem_1551255647225": "hogehoge\t\n\rhoge",
                    "subitem_1551255648112": "ja",
                }
            ],
            "item_1617186385884": [{}],
            "item_1617186419668": [
                {
                    "creatorAffiliations": [
                        {"affiliationNameIdentifiers": [{}], "affiliationNames": [{}]}
                    ],
                    "creatorAlternatives": [{}],
                    "creatorMails": [{}],
                    "creatorNames": [{}],
                    "familyNames": [{}],
                    "givenNames": [{}],
                    "nameIdentifiers": [{}],
                }
            ],
            "item_1617186499011": [{}],
            "item_1617186609386": [{}],
            "item_1617186626617": [{}],
            "item_1617186643794": [{}],
            "item_1617186660861": [{}],
            "item_1617186702042": [{}],
            "item_1617186783814": [{}],
            "item_1617186859717": [{}],
            "item_1617186882738": [{"subitem_geolocation_place": [{}]}],
            "item_1617186901218": [
                {"subitem_1522399412622": [{}], "subitem_1522399651758": [{}]}
            ],
            "item_1617186920753": [{}],
            "item_1617186941041": [{}],
            "item_1617187112279": [{}],
            "item_1617187187528": [
                {
                    "subitem_1599711633003": [{}],
                    "subitem_1599711660052": [{}],
                    "subitem_1599711758470": [{}],
                    "subitem_1599711788485": [{}],
                }
            ],
            "item_1617349709064": [
                {
                    "contributorAffiliations": [
                        {
                            "contributorAffiliationNameIdentifiers": [{}],
                            "contributorAffiliationNames": [{}],
                        }
                    ],
                    "contributorAlternatives": [{}],
                    "contributorMails": [{}],
                    "contributorNames": [{}],
                    "familyNames": [{}],
                    "givenNames": [{}],
                    "nameIdentifiers": [{}],
                }
            ],
            "item_1617353299429": [{"subitem_1523320863692": [{}]}],
            "item_1617605131499": [{"date": [{}], "fileDate": [{}], "filesize": [{}]}],
            "item_1617610673286": [{"nameIdentifiers": [{}], "rightHolderNames": [{}]}],
            "item_1617620223087": [{}],
            "item_1617944105607": [
                {"subitem_1551256015892": [{}], "subitem_1551256037922": [{}]}
            ],
            "item_1617187056579": {"bibliographic_titles": [{}]},
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            },
            "shared_user_id": -1,
        },
        "files": [],
        "endpoints": {"initialization": "/api/deposits/items"},
    }
    sanitize_input_data(source_dict)
    assert all((k, v) in source_dict.items() for (k, v) in dest_dict.items())

    source_list = [
        {
            "metainfo": {
                "pubdate": "2022-08-19",
                "item_1617186331708": [
                    {
                        "subitem_1551255647225": "hoge\x00hoge\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x7fhoge",
                        "subitem_1551255648112": "ja",
                    }
                ],
                "item_1617186385884": [{}],
                "item_1617186419668": [
                    {
                        "creatorAffiliations": [
                            {
                                "affiliationNameIdentifiers": [{}],
                                "affiliationNames": [{}],
                            }
                        ],
                        "creatorAlternatives": [{}],
                        "creatorMails": [{}],
                        "creatorNames": [{}],
                        "familyNames": [{}],
                        "givenNames": [{}],
                        "nameIdentifiers": [{}],
                    }
                ],
                "item_1617186499011": [{}],
                "item_1617186609386": [{}],
                "item_1617186626617": [{}],
                "item_1617186643794": [{}],
                "item_1617186660861": [{}],
                "item_1617186702042": [{}],
                "item_1617186783814": [{}],
                "item_1617186859717": [{}],
                "item_1617186882738": [{"subitem_geolocation_place": [{}]}],
                "item_1617186901218": [
                    {"subitem_1522399412622": [{}], "subitem_1522399651758": [{}]}
                ],
                "item_1617186920753": [{}],
                "item_1617186941041": [{}],
                "item_1617187112279": [{}],
                "item_1617187187528": [
                    {
                        "subitem_1599711633003": [{}],
                        "subitem_1599711660052": [{}],
                        "subitem_1599711758470": [{}],
                        "subitem_1599711788485": [{}],
                    }
                ],
                "item_1617349709064": [
                    {
                        "contributorAffiliations": [
                            {
                                "contributorAffiliationNameIdentifiers": [{}],
                                "contributorAffiliationNames": [{}],
                            }
                        ],
                        "contributorAlternatives": [{}],
                        "contributorMails": [{}],
                        "contributorNames": [{}],
                        "familyNames": [{}],
                        "givenNames": [{}],
                        "nameIdentifiers": [{}],
                    }
                ],
                "item_1617353299429": [{"subitem_1523320863692": [{}]}],
                "item_1617605131499": [
                    {"date": [{}], "fileDate": [{}], "filesize": [{}]}
                ],
                "item_1617610673286": [
                    {"nameIdentifiers": [{}], "rightHolderNames": [{}]}
                ],
                "item_1617620223087": [{}],
                "item_1617944105607": [
                    {"subitem_1551256015892": [{}], "subitem_1551256037922": [{}]}
                ],
                "item_1617187056579": {"bibliographic_titles": [{}]},
                "item_1617258105262": {
                    "resourcetype": "conference paper",
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                },
                "shared_user_id": -1,
            },
            "files": [],
            "endpoints": {"initialization": "/api/deposits/items"},
        }
    ]
    dest_list = [
        {
            "metainfo": {
                "pubdate": "2022-08-19",
                "item_1617186331708": [
                    {
                        "subitem_1551255647225": "hogehoge\t\n\rhoge",
                        "subitem_1551255648112": "ja",
                    }
                ],
                "item_1617186385884": [{}],
                "item_1617186419668": [
                    {
                        "creatorAffiliations": [
                            {
                                "affiliationNameIdentifiers": [{}],
                                "affiliationNames": [{}],
                            }
                        ],
                        "creatorAlternatives": [{}],
                        "creatorMails": [{}],
                        "creatorNames": [{}],
                        "familyNames": [{}],
                        "givenNames": [{}],
                        "nameIdentifiers": [{}],
                    }
                ],
                "item_1617186499011": [{}],
                "item_1617186609386": [{}],
                "item_1617186626617": [{}],
                "item_1617186643794": [{}],
                "item_1617186660861": [{}],
                "item_1617186702042": [{}],
                "item_1617186783814": [{}],
                "item_1617186859717": [{}],
                "item_1617186882738": [{"subitem_geolocation_place": [{}]}],
                "item_1617186901218": [
                    {"subitem_1522399412622": [{}], "subitem_1522399651758": [{}]}
                ],
                "item_1617186920753": [{}],
                "item_1617186941041": [{}],
                "item_1617187112279": [{}],
                "item_1617187187528": [
                    {
                        "subitem_1599711633003": [{}],
                        "subitem_1599711660052": [{}],
                        "subitem_1599711758470": [{}],
                        "subitem_1599711788485": [{}],
                    }
                ],
                "item_1617349709064": [
                    {
                        "contributorAffiliations": [
                            {
                                "contributorAffiliationNameIdentifiers": [{}],
                                "contributorAffiliationNames": [{}],
                            }
                        ],
                        "contributorAlternatives": [{}],
                        "contributorMails": [{}],
                        "contributorNames": [{}],
                        "familyNames": [{}],
                        "givenNames": [{}],
                        "nameIdentifiers": [{}],
                    }
                ],
                "item_1617353299429": [{"subitem_1523320863692": [{}]}],
                "item_1617605131499": [
                    {"date": [{}], "fileDate": [{}], "filesize": [{}]}
                ],
                "item_1617610673286": [
                    {"nameIdentifiers": [{}], "rightHolderNames": [{}]}
                ],
                "item_1617620223087": [{}],
                "item_1617944105607": [
                    {"subitem_1551256015892": [{}], "subitem_1551256037922": [{}]}
                ],
                "item_1617187056579": {"bibliographic_titles": [{}]},
                "item_1617258105262": {
                    "resourcetype": "conference paper",
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                },
                "shared_user_id": -1,
            },
            "files": [],
            "endpoints": {"initialization": "/api/deposits/items"},
        }
    ]
    sanitize_input_data(source_list)
    assert source_list == dest_list


# def save_title(activity_id, request_data):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_save_title -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_save_title(app, db_itemtype, db_workflow, db_records, users):
    request_data = {
        "metainfo": {
            "$schema": "1",
            "item_1617186331708": [
                {
                    "subitem_1551255647225": "ja_conference paperITEM00000001(public_open_access_open_access_simple)",
                    "subitem_1551255648112": "ja",
                },
                {
                    "subitem_1551255647225": "en_conference paperITEM00000001(public_open_access_simple)",
                    "subitem_1551255648112": "en",
                },
            ],
            "item_1617186385884": [
                {
                    "subitem_1551255720400": "Alternative Title",
                    "subitem_1551255721061": "en",
                },
                {
                    "subitem_1551255720400": "Alternative Title",
                    "subitem_1551255721061": "ja",
                },
            ],
            "item_1617186419668": [
                {
                    "creatorAffiliations": [
                        {
                            "affiliationNameIdentifiers": [
                                {
                                    "affiliationNameIdentifier": "0000000121691048",
                                    "affiliationNameIdentifierScheme": "ISNI",
                                    "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                }
                            ],
                            "affiliationNames": [
                                {
                                    "affiliationName": "University",
                                    "affiliationNameLang": "en",
                                }
                            ],
                        }
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "ORCID",
                            "nameIdentifierURI": "https://orcid.org/",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "CiNii",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierScheme": "KAKEN2",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        },
                    ],
                    "creatorAlternatives": [{}],
                },
                {
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "ORCID",
                            "nameIdentifierURI": "https://orcid.org/",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "CiNii",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierScheme": "KAKEN2",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        },
                    ],
                    "creatorAlternatives": [{}],
                    "creatorAffiliations": [
                        {"affiliationNameIdentifiers": [{}], "affiliationNames": [{}]}
                    ],
                },
                {
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "ORCID",
                            "nameIdentifierURI": "https://orcid.org/",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "CiNii",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierScheme": "KAKEN2",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        },
                    ],
                    "creatorAlternatives": [{}],
                    "creatorAffiliations": [
                        {"affiliationNameIdentifiers": [{}], "affiliationNames": [{}]}
                    ],
                },
            ],
            "item_1617186476635": {
                "subitem_1522299639480": "open access",
                "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
            },
            "item_1617186499011": [
                {
                    "subitem_1522650717957": "ja",
                    "subitem_1522650727486": "http://localhost",
                    "subitem_1522651041219": "Rights Information",
                }
            ],
            "item_1617186609386": [
                {
                    "subitem_1522299896455": "ja",
                    "subitem_1522300014469": "Other",
                    "subitem_1522300048512": "http://localhost/",
                    "subitem_1523261968819": "Sibject1",
                }
            ],
            "item_1617186626617": [
                {
                    "subitem_description": "Description\nDescription<br/>Description",
                    "subitem_description_language": "en",
                    "subitem_description_type": "Abstract",
                },
                {
                    "subitem_description": "概要\n概要\n概要\n概要",
                    "subitem_description_language": "ja",
                    "subitem_description_type": "Abstract",
                },
            ],
            "item_1617186643794": [
                {"subitem_1522300295150": "en", "subitem_1522300316516": "Publisher"}
            ],
            "item_1617186660861": [
                {
                    "subitem_1522300695726": "Available",
                    "subitem_1522300722591": "2021-06-30",
                }
            ],
            "item_1617186702042": [{"subitem_1551255818386": "jpn"}],
            "item_1617186783814": [
                {
                    "subitem_identifier_type": "URI",
                    "subitem_identifier_uri": "http://localhost",
                }
            ],
            "item_1617186859717": [
                {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
            ],
            "item_1617186882738": [
                {
                    "subitem_geolocation_place": [
                        {"subitem_geolocation_place_text": "Japan"}
                    ]
                }
            ],
            "item_1617186901218": [
                {
                    "subitem_1522399143519": {
                        "subitem_1522399281603": "ISNI",
                        "subitem_1522399333375": "http://xxx",
                    },
                    "subitem_1522399412622": [
                        {
                            "subitem_1522399416691": "en",
                            "subitem_1522737543681": "Funder Name",
                        }
                    ],
                    "subitem_1522399571623": {
                        "subitem_1522399585738": "Award URI",
                        "subitem_1522399628911": "Award Number",
                    },
                    "subitem_1522399651758": [
                        {
                            "subitem_1522721910626": "en",
                            "subitem_1522721929892": "Award Title",
                        }
                    ],
                }
            ],
            "item_1617186920753": [
                {
                    "subitem_1522646500366": "ISSN",
                    "subitem_1522646572813": "xxxx-xxxx-xxxx",
                }
            ],
            "item_1617186941041": [
                {"subitem_1522650068558": "en", "subitem_1522650091861": "Source Title"}
            ],
            "item_1617186959569": {"subitem_1551256328147": "1"},
            "item_1617186981471": {"subitem_1551256294723": "111"},
            "item_1617186994930": {"subitem_1551256248092": "12"},
            "item_1617187024783": {"subitem_1551256198917": "1"},
            "item_1617187045071": {"subitem_1551256185532": "3"},
            "item_1617187112279": [
                {"subitem_1551256126428": "Degree Name", "subitem_1551256129013": "en"}
            ],
            "item_1617187136212": {"subitem_1551256096004": "2021-06-30"},
            "item_1617187187528": [
                {
                    "subitem_1599711633003": [
                        {
                            "subitem_1599711636923": "Conference Name",
                            "subitem_1599711645590": "ja",
                        }
                    ],
                    "subitem_1599711655652": "1",
                    "subitem_1599711660052": [
                        {
                            "subitem_1599711680082": "Sponsor",
                            "subitem_1599711686511": "ja",
                        }
                    ],
                    "subitem_1599711699392": {
                        "subitem_1599711704251": "2020/12/11",
                        "subitem_1599711712451": "1",
                        "subitem_1599711727603": "12",
                        "subitem_1599711731891": "2000",
                        "subitem_1599711735410": "1",
                        "subitem_1599711739022": "12",
                        "subitem_1599711743722": "2020",
                        "subitem_1599711745532": "ja",
                    },
                    "subitem_1599711758470": [
                        {
                            "subitem_1599711769260": "Conference Venue",
                            "subitem_1599711775943": "ja",
                        }
                    ],
                    "subitem_1599711788485": [
                        {
                            "subitem_1599711798761": "Conference Place",
                            "subitem_1599711803382": "ja",
                        }
                    ],
                    "subitem_1599711813532": "JPN",
                }
            ],
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            },
            "item_1617265215918": {
                "subitem_1522305645492": "AO",
                "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
            },
            "item_1617349709064": [
                {
                    "contributorMails": [{"contributorMail": "wekosoftware@nii.ac.jp"}],
                    "contributorNames": [
                        {"contributorName": "情報, 太郎", "lang": "ja"},
                        {"contributorName": "ジョウホウ, タロウ", "lang": "ja-Kana"},
                        {"contributorName": "Joho, Taro", "lang": "en"},
                    ],
                    "contributorType": "ContactPerson",
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "ORCID",
                            "nameIdentifierURI": "https://orcid.org/",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "CiNii",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "KAKEN2",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        },
                    ],
                    "contributorAlternatives": [{}],
                    "contributorAffiliations": [
                        {
                            "contributorAffiliationNameIdentifiers": [{}],
                            "contributorAffiliationNames": [{}],
                        }
                    ],
                }
            ],
            "item_1617349808926": {"subitem_1523263171732": "Version"},
            "item_1617351524846": {"subitem_1523260933860": "Unknown"},
            "item_1617353299429": [
                {
                    "subitem_1522306207484": "isVersionOf",
                    "subitem_1522306287251": {
                        "subitem_1522306382014": "arXiv",
                        "subitem_1522306436033": "xxxxx",
                    },
                    "subitem_1523320863692": [
                        {
                            "subitem_1523320867455": "en",
                            "subitem_1523320909613": "Related Title",
                        }
                    ],
                }
            ],
            "item_1617605131499": [
                {
                    "accessrole": "open_access",
                    "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                    "displaytype": "simple",
                    "filename": "1KB.pdf",
                    "filesize": [{"value": "1 KB"}],
                    "format": "text/plain",
                    "mimetype": "application/pdf",
                    "url": {"url": "https://weko3.example.org/record/1/files/1KB.pdf"},
                    "version_id": "427e7fc6-3586-4987-ab63-76a3416ee3db",
                    "fileDate": [{}],
                    "provide": [{}],
                }
            ],
            "item_1617610673286": [
                {
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxx",
                            "nameIdentifierScheme": "ORCID",
                            "nameIdentifierURI": "https://orcid.org/",
                        }
                    ],
                    "rightHolderNames": [
                        {
                            "rightHolderLanguage": "ja",
                            "rightHolderName": "Right Holder Name",
                        }
                    ],
                }
            ],
            "item_1617620223087": [
                {
                    "subitem_1565671149650": "ja",
                    "subitem_1565671169640": "Banner Headline",
                    "subitem_1565671178623": "Subheading",
                },
                {
                    "subitem_1565671149650": "en",
                    "subitem_1565671169640": "Banner Headline",
                    "subitem_1565671178623": "Subheding",
                },
            ],
            "item_1617944105607": [
                {
                    "subitem_1551256015892": [
                        {
                            "subitem_1551256027296": "xxxxxx",
                            "subitem_1551256029891": "kakenhi",
                        }
                    ],
                    "subitem_1551256037922": [
                        {
                            "subitem_1551256042287": "Degree Grantor Name",
                            "subitem_1551256047619": "en",
                        }
                    ],
                }
            ],
            "owner": "1",
            "pubdate": "2021-08-06",
            "title": "ja_conference paperITEM00000001(public_open_access_open_access_simple)",
            "weko_shared_id": -1,
            "item_1617187056579": {"bibliographic_titles": [{}]},
            "shared_user_id": -1,
        },
        "files": [
            {
                "checksum": "sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef",
                "completed": True,
                "displaytype": "simple",
                "filename": "1KB.pdf",
                "is_show": False,
                "is_thumbnail": False,
                "key": "1KB.pdf",
                "licensetype": None,
                "links": {
                    "self": "/api/files/bbd13a3e-d6c0-41c1-8f92-abb50ba3e85b/1KB.pdf?versionId=427e7fc6-3586-4987-ab63-76a3416ee3db"
                },
                "mimetype": "application/pdf",
                "progress": 100,
                "size": 1024,
                "version_id": "427e7fc6-3586-4987-ab63-76a3416ee3db",
            }
        ],
        "endpoints": {"initialization": "/api/deposits/redirect/1.0"},
    }
    save_title("A-00000000-00000", request_data)
    activity = WorkActivity()
    db_activity = activity.get_activity_detail("A-00000000-00000")
    assert (
        db_activity.title
        == "ja_conference paperITEM00000001(public_open_access_open_access_simple)"
    )


# def get_key_title_in_item_type_mapping(item_type_mapping):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_key_title_in_item_type_mapping -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_key_title_in_item_type_mapping(db_itemtype):
    mapping = db_itemtype['item_type_mapping'].mapping
    assert get_key_title_in_item_type_mapping(mapping) ==  ('item_1617186331708', 'subitem_1551255647225')


# def get_title_in_request(request_data, key, key_child):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_title_in_request -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_title_in_request():
    request_data = {
        "metainfo": {
            "$schema": "1",
            "item_1617186331708": [
                {
                    "subitem_1551255647225": "ja_conference paperITEM00000001(public_open_access_open_access_simple)",
                    "subitem_1551255648112": "ja",
                },
                {
                    "subitem_1551255647225": "en_conference paperITEM00000001(public_open_access_simple)",
                    "subitem_1551255648112": "en",
                },
            ],
            "item_1617186385884": [
                {
                    "subitem_1551255720400": "Alternative Title",
                    "subitem_1551255721061": "en",
                },
                {
                    "subitem_1551255720400": "Alternative Title",
                    "subitem_1551255721061": "ja",
                },
            ],
            "item_1617186419668": [
                {
                    "creatorAffiliations": [
                        {
                            "affiliationNameIdentifiers": [
                                {
                                    "affiliationNameIdentifier": "0000000121691048",
                                    "affiliationNameIdentifierScheme": "ISNI",
                                    "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                }
                            ],
                            "affiliationNames": [
                                {
                                    "affiliationName": "University",
                                    "affiliationNameLang": "en",
                                }
                            ],
                        }
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "ORCID",
                            "nameIdentifierURI": "https://orcid.org/",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "CiNii",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierScheme": "KAKEN2",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        },
                    ],
                    "creatorAlternatives": [{}],
                },
                {
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "ORCID",
                            "nameIdentifierURI": "https://orcid.org/",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "CiNii",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierScheme": "KAKEN2",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        },
                    ],
                    "creatorAlternatives": [{}],
                    "creatorAffiliations": [
                        {"affiliationNameIdentifiers": [{}], "affiliationNames": [{}]}
                    ],
                },
                {
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "ORCID",
                            "nameIdentifierURI": "https://orcid.org/",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "CiNii",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierScheme": "KAKEN2",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        },
                    ],
                    "creatorAlternatives": [{}],
                    "creatorAffiliations": [
                        {"affiliationNameIdentifiers": [{}], "affiliationNames": [{}]}
                    ],
                },
            ],
            "item_1617186476635": {
                "subitem_1522299639480": "open access",
                "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
            },
            "item_1617186499011": [
                {
                    "subitem_1522650717957": "ja",
                    "subitem_1522650727486": "http://localhost",
                    "subitem_1522651041219": "Rights Information",
                }
            ],
            "item_1617186609386": [
                {
                    "subitem_1522299896455": "ja",
                    "subitem_1522300014469": "Other",
                    "subitem_1522300048512": "http://localhost/",
                    "subitem_1523261968819": "Sibject1",
                }
            ],
            "item_1617186626617": [
                {
                    "subitem_description": "Description\nDescription<br/>Description",
                    "subitem_description_language": "en",
                    "subitem_description_type": "Abstract",
                },
                {
                    "subitem_description": "概要\n概要\n概要\n概要",
                    "subitem_description_language": "ja",
                    "subitem_description_type": "Abstract",
                },
            ],
            "item_1617186643794": [
                {"subitem_1522300295150": "en", "subitem_1522300316516": "Publisher"}
            ],
            "item_1617186660861": [
                {
                    "subitem_1522300695726": "Available",
                    "subitem_1522300722591": "2021-06-30",
                }
            ],
            "item_1617186702042": [{"subitem_1551255818386": "jpn"}],
            "item_1617186783814": [
                {
                    "subitem_identifier_type": "URI",
                    "subitem_identifier_uri": "http://localhost",
                }
            ],
            "item_1617186859717": [
                {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
            ],
            "item_1617186882738": [
                {
                    "subitem_geolocation_place": [
                        {"subitem_geolocation_place_text": "Japan"}
                    ]
                }
            ],
            "item_1617186901218": [
                {
                    "subitem_1522399143519": {
                        "subitem_1522399281603": "ISNI",
                        "subitem_1522399333375": "http://xxx",
                    },
                    "subitem_1522399412622": [
                        {
                            "subitem_1522399416691": "en",
                            "subitem_1522737543681": "Funder Name",
                        }
                    ],
                    "subitem_1522399571623": {
                        "subitem_1522399585738": "Award URI",
                        "subitem_1522399628911": "Award Number",
                    },
                    "subitem_1522399651758": [
                        {
                            "subitem_1522721910626": "en",
                            "subitem_1522721929892": "Award Title",
                        }
                    ],
                }
            ],
            "item_1617186920753": [
                {
                    "subitem_1522646500366": "ISSN",
                    "subitem_1522646572813": "xxxx-xxxx-xxxx",
                }
            ],
            "item_1617186941041": [
                {"subitem_1522650068558": "en", "subitem_1522650091861": "Source Title"}
            ],
            "item_1617186959569": {"subitem_1551256328147": "1"},
            "item_1617186981471": {"subitem_1551256294723": "111"},
            "item_1617186994930": {"subitem_1551256248092": "12"},
            "item_1617187024783": {"subitem_1551256198917": "1"},
            "item_1617187045071": {"subitem_1551256185532": "3"},
            "item_1617187112279": [
                {"subitem_1551256126428": "Degree Name", "subitem_1551256129013": "en"}
            ],
            "item_1617187136212": {"subitem_1551256096004": "2021-06-30"},
            "item_1617187187528": [
                {
                    "subitem_1599711633003": [
                        {
                            "subitem_1599711636923": "Conference Name",
                            "subitem_1599711645590": "ja",
                        }
                    ],
                    "subitem_1599711655652": "1",
                    "subitem_1599711660052": [
                        {
                            "subitem_1599711680082": "Sponsor",
                            "subitem_1599711686511": "ja",
                        }
                    ],
                    "subitem_1599711699392": {
                        "subitem_1599711704251": "2020/12/11",
                        "subitem_1599711712451": "1",
                        "subitem_1599711727603": "12",
                        "subitem_1599711731891": "2000",
                        "subitem_1599711735410": "1",
                        "subitem_1599711739022": "12",
                        "subitem_1599711743722": "2020",
                        "subitem_1599711745532": "ja",
                    },
                    "subitem_1599711758470": [
                        {
                            "subitem_1599711769260": "Conference Venue",
                            "subitem_1599711775943": "ja",
                        }
                    ],
                    "subitem_1599711788485": [
                        {
                            "subitem_1599711798761": "Conference Place",
                            "subitem_1599711803382": "ja",
                        }
                    ],
                    "subitem_1599711813532": "JPN",
                }
            ],
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            },
            "item_1617265215918": {
                "subitem_1522305645492": "AO",
                "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
            },
            "item_1617349709064": [
                {
                    "contributorMails": [{"contributorMail": "wekosoftware@nii.ac.jp"}],
                    "contributorNames": [
                        {"contributorName": "情報, 太郎", "lang": "ja"},
                        {"contributorName": "ジョウホウ, タロウ", "lang": "ja-Kana"},
                        {"contributorName": "Joho, Taro", "lang": "en"},
                    ],
                    "contributorType": "ContactPerson",
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "ORCID",
                            "nameIdentifierURI": "https://orcid.org/",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "CiNii",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierScheme": "KAKEN2",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        },
                    ],
                    "contributorAlternatives": [{}],
                    "contributorAffiliations": [
                        {
                            "contributorAffiliationNameIdentifiers": [{}],
                            "contributorAffiliationNames": [{}],
                        }
                    ],
                }
            ],
            "item_1617349808926": {"subitem_1523263171732": "Version"},
            "item_1617351524846": {"subitem_1523260933860": "Unknown"},
            "item_1617353299429": [
                {
                    "subitem_1522306207484": "isVersionOf",
                    "subitem_1522306287251": {
                        "subitem_1522306382014": "arXiv",
                        "subitem_1522306436033": "xxxxx",
                    },
                    "subitem_1523320863692": [
                        {
                            "subitem_1523320867455": "en",
                            "subitem_1523320909613": "Related Title",
                        }
                    ],
                }
            ],
            "item_1617605131499": [
                {
                    "accessrole": "open_access",
                    "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                    "displaytype": "simple",
                    "filename": "1KB.pdf",
                    "filesize": [{"value": "1 KB"}],
                    "format": "text/plain",
                    "mimetype": "application/pdf",
                    "url": {"url": "https://weko3.example.org/record/1/files/1KB.pdf"},
                    "version_id": "427e7fc6-3586-4987-ab63-76a3416ee3db",
                    "fileDate": [{}],
                    "provide": [{}],
                }
            ],
            "item_1617610673286": [
                {
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxx",
                            "nameIdentifierScheme": "ORCID",
                            "nameIdentifierURI": "https://orcid.org/",
                        }
                    ],
                    "rightHolderNames": [
                        {
                            "rightHolderLanguage": "ja",
                            "rightHolderName": "Right Holder Name",
                        }
                    ],
                }
            ],
            "item_1617620223087": [
                {
                    "subitem_1565671149650": "ja",
                    "subitem_1565671169640": "Banner Headline",
                    "subitem_1565671178623": "Subheading",
                },
                {
                    "subitem_1565671149650": "en",
                    "subitem_1565671169640": "Banner Headline",
                    "subitem_1565671178623": "Subheding",
                },
            ],
            "item_1617944105607": [
                {
                    "subitem_1551256015892": [
                        {
                            "subitem_1551256027296": "xxxxxx",
                            "subitem_1551256029891": "kakenhi",
                        }
                    ],
                    "subitem_1551256037922": [
                        {
                            "subitem_1551256042287": "Degree Grantor Name",
                            "subitem_1551256047619": "en",
                        }
                    ],
                }
            ],
            "owner": "1",
            "pubdate": "2021-08-06",
            "title": "ja_conference paperITEM00000001(public_open_access_open_access_simple)",
            "weko_shared_id": -1,
            "item_1617187056579": {"bibliographic_titles": [{}]},
            "shared_user_id": -1,
        },
        "files": [
            {
                "checksum": "sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef",
                "completed": True,
                "displaytype": "simple",
                "filename": "1KB.pdf",
                "is_show": False,
                "is_thumbnail": False,
                "key": "1KB.pdf",
                "licensetype": None,
                "links": {
                    "self": "/api/files/bbd13a3e-d6c0-41c1-8f92-abb50ba3e85b/1KB.pdf?versionId=427e7fc6-3586-4987-ab63-76a3416ee3db"
                },
                "mimetype": "application/pdf",
                "progress": 100,
                "size": 1024,
                "version_id": "427e7fc6-3586-4987-ab63-76a3416ee3db",
            }
        ],
        "endpoints": {"initialization": "/api/deposits/redirect/1.0"},
    }

    assert get_title_in_request(request_data,'item_1617186331708', 'subitem_1551255647225')=='ja_conference paperITEM00000001(public_open_access_open_access_simple)'


# def hide_form_items(item_type, schema_form):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_hide_form_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_hide_form_items(db_itemtype):
    item_type = db_itemtype["item_type"]
    form = item_type.form
    form_pre = copy.deepcopy(form)
    res = hide_form_items(item_type, form)
    _diff = diff(form,res)
    assert list(_diff)==[]


# def hide_thumbnail(schema_form):
#     def is_thumbnail(items):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_hide_thumbnail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_hide_thumbnail(db_itemtype):
    itemtype = db_itemtype["item_type"]
    assert hide_thumbnail(itemtype.form) == None


# def get_ignore_item(_item_type_id,
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_ignore_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_ignore_item(db_itemtype):
    itemtype = db_itemtype["item_type"]
    item_type_mapping = db_itemtype["item_type_mapping"]
    itemtype2 = ItemTypes.get_record(1)
    assert get_ignore_item(itemtype.id, item_type_data=itemtype2) == []


# def make_stats_csv_with_permission(item_type_id, recids,
#     def _get_root_item_option(item_id, item, sub_form={'title_i18n': {}}):
#         def __init__(self, record_ids, records_metadata):
#             def hide_metadata_email(record):
#         def get_max_ins(self, attr):
#         def get_max_ins_feedback_mail(self):
#         def get_max_items(self, item_attrs):
#         def get_subs_item(self,
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_make_stats_file_with_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_make_stats_file_with_permission(app, users,db_itemtype,db_itemtype2,db_records,db_records2):
    item_type_id = 1
    recids = ["1", "2"]
    record0 = WekoRecord.get_record_by_pid(1)
    record1 = WekoRecord.get_record_by_pid(2)
    records_metadata = {"1": record0, "2": record1}
    permissions = dict(
        permission_show_hide=lambda a: True,
        check_created_id=lambda a: True,
        hide_meta_data_for_role=lambda a: True,
        current_language=lambda: True,
    )

    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
            assert (
                make_stats_file_with_permission(
                    item_type_id, recids, records_metadata, permissions
                )
                == ([['#.id', '.uri', '.metadata.path[0]', '.pos_index[0]', '.publish_status', '.feedback_mail[0]', '.request_mail[0]', '.cnri', '.doi_ra', '.doi', '.edit_mode', '.metadata.pubdate', '.metadata.item_1617186331708[0].subitem_1551255647225', '.metadata.item_1617186331708[0].subitem_1551255648112', '.metadata.item_1617186385884[0].subitem_1551255720400', '.metadata.item_1617186385884[0].subitem_1551255721061', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifier', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierScheme', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierURI', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNames[0].affiliationName', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNames[0].affiliationNameLang', '.metadata.item_1617186419668[0].creatorAlternatives[0].creatorAlternative', '.metadata.item_1617186419668[0].creatorAlternatives[0].creatorAlternativeLang', '.metadata.item_1617186419668[0].creatorMails[0].creatorMail', '.metadata.item_1617186419668[0].creatorNames[0].creatorName', '.metadata.item_1617186419668[0].creatorNames[0].creatorNameLang', '.metadata.item_1617186419668[0].familyNames[0].familyName', '.metadata.item_1617186419668[0].familyNames[0].familyNameLang', '.metadata.item_1617186419668[0].givenNames[0].givenName', '.metadata.item_1617186419668[0].givenNames[0].givenNameLang', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationNameIdentifier', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationScheme', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationURI', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationName', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationNameLang', '.metadata.item_1617349709064[0].contributorAlternatives[0].contributorAlternative', '.metadata.item_1617349709064[0].contributorAlternatives[0].contributorAlternativeLang', '.metadata.item_1617349709064[0].contributorMails[0].contributorMail', '.metadata.item_1617349709064[0].contributorNames[0].contributorName', '.metadata.item_1617349709064[0].contributorNames[0].lang', '.metadata.item_1617349709064[0].contributorType', '.metadata.item_1617349709064[0].familyNames[0].familyName', '.metadata.item_1617349709064[0].familyNames[0].familyNameLang', '.metadata.item_1617349709064[0].givenNames[0].givenName', '.metadata.item_1617349709064[0].givenNames[0].givenNameLang', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617186476635.subitem_1522299639480', '.metadata.item_1617186476635.subitem_1600958577026', '.metadata.item_1617351524846.subitem_1523260933860', '.metadata.item_1617186499011[0].subitem_1522650717957', '.metadata.item_1617186499011[0].subitem_1522650727486', '.metadata.item_1617186499011[0].subitem_1522651041219', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617610673286[0].rightHolderNames[0].rightHolderLanguage', '.metadata.item_1617610673286[0].rightHolderNames[0].rightHolderName', '.metadata.item_1617186609386[0].subitem_1522299896455', '.metadata.item_1617186609386[0].subitem_1522300014469', '.metadata.item_1617186609386[0].subitem_1522300048512', '.metadata.item_1617186609386[0].subitem_1523261968819', '.metadata.item_1617186626617[0].subitem_description', '.metadata.item_1617186626617[0].subitem_description_language', '.metadata.item_1617186626617[0].subitem_description_type', '.metadata.item_1617186643794[0].subitem_1522300295150', '.metadata.item_1617186643794[0].subitem_1522300316516', '.metadata.item_1617186660861[0].subitem_1522300695726', '.metadata.item_1617186660861[0].subitem_1522300722591', '.metadata.item_1617186702042[0].subitem_1551255818386', '.metadata.item_1617258105262.resourcetype', '.metadata.item_1617258105262.resourceuri', '.metadata.item_1617349808926.subitem_1523263171732', '.metadata.item_1617265215918.subitem_1522305645492', '.metadata.item_1617265215918.subitem_1600292170262', '.metadata.item_1617186783814[0].subitem_identifier_type', '.metadata.item_1617186783814[0].subitem_identifier_uri', '.metadata.item_1617186819068.subitem_identifier_reg_text', '.metadata.item_1617186819068.subitem_identifier_reg_type', '.metadata.item_1617353299429[0].subitem_1522306207484', '.metadata.item_1617353299429[0].subitem_1522306287251.subitem_1522306382014', '.metadata.item_1617353299429[0].subitem_1522306287251.subitem_1522306436033', '.metadata.item_1617353299429[0].subitem_1523320863692[0].subitem_1523320867455', '.metadata.item_1617353299429[0].subitem_1523320863692[0].subitem_1523320909613', '.metadata.item_1617186859717[0].subitem_1522658018441', '.metadata.item_1617186859717[0].subitem_1522658031721', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_east_longitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_north_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_south_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_west_longitude', '.metadata.item_1617186882738[0].subitem_geolocation_place[0].subitem_geolocation_place_text', '.metadata.item_1617186882738[0].subitem_geolocation_point.subitem_point_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_point.subitem_point_longitude', '.metadata.item_1617186901218[0].subitem_1522399143519.subitem_1522399281603', '.metadata.item_1617186901218[0].subitem_1522399143519.subitem_1522399333375', '.metadata.item_1617186901218[0].subitem_1522399412622[0].subitem_1522399416691', '.metadata.item_1617186901218[0].subitem_1522399412622[0].subitem_1522737543681', '.metadata.item_1617186901218[0].subitem_1522399571623.subitem_1522399585738', '.metadata.item_1617186901218[0].subitem_1522399571623.subitem_1522399628911', '.metadata.item_1617186901218[0].subitem_1522399651758[0].subitem_1522721910626', '.metadata.item_1617186901218[0].subitem_1522399651758[0].subitem_1522721929892', '.metadata.item_1617186920753[0].subitem_1522646500366', '.metadata.item_1617186920753[0].subitem_1522646572813', '.metadata.item_1617186941041[0].subitem_1522650068558', '.metadata.item_1617186941041[0].subitem_1522650091861', '.metadata.item_1617186959569.subitem_1551256328147', '.metadata.item_1617186981471.subitem_1551256294723', '.metadata.item_1617186994930.subitem_1551256248092', '.metadata.item_1617187024783.subitem_1551256198917', '.metadata.item_1617187045071.subitem_1551256185532', '.metadata.item_1617187056579.bibliographicIssueDates.bibliographicIssueDate', '.metadata.item_1617187056579.bibliographicIssueDates.bibliographicIssueDateType', '.metadata.item_1617187056579.bibliographicIssueNumber', '.metadata.item_1617187056579.bibliographicNumberOfPages', '.metadata.item_1617187056579.bibliographicPageEnd', '.metadata.item_1617187056579.bibliographicPageStart', '.metadata.item_1617187056579.bibliographicVolumeNumber', '.metadata.item_1617187056579.bibliographic_titles[0].bibliographic_title', '.metadata.item_1617187056579.bibliographic_titles[0].bibliographic_titleLang', '.metadata.item_1617187087799.subitem_1551256171004', '.metadata.item_1617187112279[0].subitem_1551256126428', '.metadata.item_1617187112279[0].subitem_1551256129013', '.metadata.item_1617187136212.subitem_1551256096004', '.metadata.item_1617944105607[0].subitem_1551256015892[0].subitem_1551256027296', '.metadata.item_1617944105607[0].subitem_1551256015892[0].subitem_1551256029891', '.metadata.item_1617944105607[0].subitem_1551256037922[0].subitem_1551256042287', '.metadata.item_1617944105607[0].subitem_1551256037922[0].subitem_1551256047619', '.metadata.item_1617187187528[0].subitem_1599711633003[0].subitem_1599711636923', '.metadata.item_1617187187528[0].subitem_1599711633003[0].subitem_1599711645590', '.metadata.item_1617187187528[0].subitem_1599711655652', '.metadata.item_1617187187528[0].subitem_1599711660052[0].subitem_1599711680082', '.metadata.item_1617187187528[0].subitem_1599711660052[0].subitem_1599711686511', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711704251', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711712451', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711727603', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711731891', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711735410', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711739022', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711743722', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711745532', '.metadata.item_1617187187528[0].subitem_1599711758470[0].subitem_1599711769260', '.metadata.item_1617187187528[0].subitem_1599711758470[0].subitem_1599711775943', '.metadata.item_1617187187528[0].subitem_1599711788485[0].subitem_1599711798761', '.metadata.item_1617187187528[0].subitem_1599711788485[0].subitem_1599711803382', '.metadata.item_1617187187528[0].subitem_1599711813532', '.file_path[0]', '.metadata.item_1617605131499[0].accessrole', '.metadata.item_1617605131499[0].date[0].dateType', '.metadata.item_1617605131499[0].date[0].dateValue', '.metadata.item_1617605131499[0].displaytype', '.metadata.item_1617605131499[0].fileDate[0].fileDateType', '.metadata.item_1617605131499[0].fileDate[0].fileDateValue', '.metadata.item_1617605131499[0].filename', '.metadata.item_1617605131499[0].filesize[0].value', '.metadata.item_1617605131499[0].format', '.metadata.item_1617605131499[0].groups', '.metadata.item_1617605131499[0].licensefree', '.metadata.item_1617605131499[0].licensetype', '.metadata.item_1617605131499[0].url.label', '.metadata.item_1617605131499[0].url.objectType', '.metadata.item_1617605131499[0].url.url', '.metadata.item_1617605131499[0].version', '.metadata.item_1617620223087[0].subitem_1565671149650', '.metadata.item_1617620223087[0].subitem_1565671169640', '.metadata.item_1617620223087[0].subitem_1565671178623', '.thumbnail_path[0]', '.metadata.item_1662046377046[0].subitem_thumbnail[0].thumbnail_label', '.metadata.item_1662046377046[0].subitem_thumbnail[0].thumbnail_url'], ['#ID', 'URI', '.IndexID[0]', '.POS_INDEX[0]', '.PUBLISH_STATUS', '.FEEDBACK_MAIL[0]', '.REQUEST_MAIL[0]', '.CNRI', '.DOI_RA', '.DOI', 'Keep/Upgrade Version', 'PubDate', 'Title[0].Title', 'Title[0].Language', 'Alternative Title[0].Alternative Title', 'Alternative Title[0].Language', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子URI', 'Creator[0].作成者所属[0].所属機関名[0].所属機関名', 'Creator[0].作成者所属[0].所属機関名[0].言語', 'Creator[0].作成者別名[0].別名', 'Creator[0].作成者別名[0].言語', 'Creator[0].作成者メールアドレス[0].メールアドレス', 'Creator[0].作成者姓名[0].姓名', 'Creator[0].作成者姓名[0].言語', 'Creator[0].作成者姓[0].姓', 'Creator[0].作成者姓[0].言語', 'Creator[0].作成者名[0].名', 'Creator[0].作成者名[0].言語', 'Creator[0].作成者識別子[0].作成者識別子', 'Creator[0].作成者識別子[0].作成者識別子Scheme', 'Creator[0].作成者識別子[0].作成者識別子URI', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子URI', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関名', 'Contributor[0].寄与者所属[0].所属機関識別子[0].言語', 'Contributor[0].寄与者別名[0].別名', 'Contributor[0].寄与者別名[0].言語', 'Contributor[0].寄与者メールアドレス[0].メールアドレス', 'Contributor[0].寄与者姓名[0].姓名', 'Contributor[0].寄与者姓名[0].言語', 'Contributor[0].寄与者タイプ', 'Contributor[0].寄与者姓[0].姓', 'Contributor[0].寄与者姓[0].言語', 'Contributor[0].寄与者名[0].名', 'Contributor[0].寄与者名[0].言語', 'Contributor[0].寄与者識別子[0].寄与者識別子', 'Contributor[0].寄与者識別子[0].寄与者識別子Scheme', 'Contributor[0].寄与者識別子[0].寄与者識別子URI', 'Access Rights.アクセス権', 'Access Rights.アクセス権URI', 'APC.APC', 'Rights[0].言語', 'Rights[0].権利情報Resource', 'Rights[0].権利情報', 'Rights Holder[0].権利者識別子[0].権利者識別子', 'Rights Holder[0].権利者識別子[0].権利者識別子Scheme', 'Rights Holder[0].権利者識別子[0].権利者識別子URI', 'Rights Holder[0].権利者名[0].言語', 'Rights Holder[0].権利者名[0].権利者名', 'Subject[0].言語', 'Subject[0].主題Scheme', 'Subject[0].主題URI', 'Subject[0].主題', 'Description[0].内容記述', 'Description[0].言語', 'Description[0].内容記述タイプ', 'Publisher[0].言語', 'Publisher[0].出版者', 'Date[0].日付タイプ', 'Date[0].日付', 'Language[0].Language', 'Resource Type.資源タイプ', 'Resource Type.資源タイプ識別子', 'Version.バージョン情報', 'Version Type.出版タイプ', 'Version Type.出版タイプResource', 'Identifier[0].識別子タイプ', 'Identifier[0].識別子', 'Identifier Registration.ID登録', 'Identifier Registration.ID登録タイプ', 'Relation[0].関連タイプ', 'Relation[0].関連識別子.識別子タイプ', 'Relation[0].関連識別子.関連識別子', 'Relation[0].関連名称[0].言語', 'Relation[0].関連名称[0].関連名称', 'Temporal[0].言語', 'Temporal[0].時間的範囲', 'Geo Location[0].位置情報（空間）.東部経度', 'Geo Location[0].位置情報（空間）.北部緯度', 'Geo Location[0].位置情報（空間）.南部緯度', 'Geo Location[0].位置情報（空間）.西部経度', 'Geo Location[0].位置情報（自由記述）[0].位置情報（自由記述）', 'Geo Location[0].位置情報（点）.緯度', 'Geo Location[0].位置情報（点）.経度', 'Funding Reference[0].助成機関識別子.助成機関識別子タイプ', 'Funding Reference[0].助成機関識別子.助成機関識別子', 'Funding Reference[0].助成機関名[0].言語', 'Funding Reference[0].助成機関名[0].助成機関名', 'Funding Reference[0].研究課題番号.研究課題URI', 'Funding Reference[0].研究課題番号.研究課題番号', 'Funding Reference[0].研究課題名[0].言語', 'Funding Reference[0].研究課題名[0].研究課題名', 'Source Identifier[0].収録物識別子タイプ', 'Source Identifier[0].収録物識別子', 'Source Title[0].言語', 'Source Title[0].収録物名', 'Volume Number.Volume Number', 'Issue Number.Issue Number', 'Number of Pages.Number of Pages', 'Page Start.Page Start', 'Page End.Page End', 'Bibliographic Information.発行日.日付', 'Bibliographic Information.発行日.日付タイプ', 'Bibliographic Information.号', 'Bibliographic Information.ページ数', 'Bibliographic Information.終了ページ', 'Bibliographic Information.開始ページ', 'Bibliographic Information.巻', 'Bibliographic Information.雑誌名[0].タイトル', 'Bibliographic Information.雑誌名[0].言語', 'Dissertation Number.Dissertation Number', 'Degree Name[0].Degree Name', 'Degree Name[0].Language', 'Date Granted.Date Granted', 'Degree Grantor[0].Degree Grantor Name Identifier[0].Degree Grantor Name Identifier', 'Degree Grantor[0].Degree Grantor Name Identifier[0].Degree Grantor Name Identifier Scheme', 'Degree Grantor[0].Degree Grantor Name[0].Degree Grantor Name', 'Degree Grantor[0].Degree Grantor Name[0].Language', 'Conference[0].Conference Name[0].Conference Name', 'Conference[0].Conference Name[0].Language', 'Conference[0].Conference Sequence', 'Conference[0].Conference Sponsor[0].Conference Sponsor', 'Conference[0].Conference Sponsor[0].Language', 'Conference[0].Conference Date.Conference Date', 'Conference[0].Conference Date.Start Day', 'Conference[0].Conference Date.Start Month', 'Conference[0].Conference Date.Start Year', 'Conference[0].Conference Date.End Day', 'Conference[0].Conference Date.End Month', 'Conference[0].Conference Date.End Year', 'Conference[0].Conference Date.Language', 'Conference[0].Conference Venue[0].Conference Venue', 'Conference[0].Conference Venue[0].Language', 'Conference[0].Conference Place[0].Conference Place', 'Conference[0].Conference Place[0].Language', 'Conference[0].Conference Country', '.ファイルパス[0]', 'File[0].アクセス', 'File[0].オープンアクセスの日付[0].日付タイプ', 'File[0].オープンアクセスの日付[0].日付', 'File[0].表示形式', 'File[0].日付[0].日付タイプ', 'File[0].日付[0].日付', 'File[0].表示名', 'File[0].サイズ[0].サイズ', 'File[0].フォーマット', 'File[0].グループ', 'File[0].自由ライセンス', 'File[0].ライセンス', 'File[0].本文URL.ラベル', 'File[0].本文URL.オブジェクトタイプ', 'File[0].本文URL.本文URL', 'File[0].バージョン情報', 'Heading[0].Language', 'Heading[0].Banner Headline', 'Heading[0].Subheading', '.サムネイルパス[0]', 'サムネイル[0].URI[0].ラベル', 'サムネイル[0].URI[0].URI'], ['#', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', '', '', 'System', '', '', 'System', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', 'System'], ['#', '', 'Allow Multiple', 'Allow Multiple', 'Required', 'Allow Multiple', 'Allow Multiple', '', '', '', 'Required', 'Required', 'Required, Allow Multiple', 'Required, Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Required', 'Required', '', '', '', 'Allow Multiple', 'Allow Multiple', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Allow Multiple', 'Allow Multiple', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple']], {'1': [1, 'Index(public_state = True,harvest_public_state = True)', 'public', '', '', '', '', '', 'Keep', '2022-08-20', 'title', 'ja', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'conference paper', 'http://purl.org/coar/resource_type/c_5794', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''], '2': [2, 'Index(public_state = True,harvest_public_state = False)', 'private', '', '', '', '', '', 'Keep', '2022-08-20', 'title2', 'ja', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'conference paper', 'http://purl.org/coar/resource_type/c_5794', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']})
            )

            itemtype = ItemTypes.get_by_id(2)
            meta_list = itemtype.render.get("meta_list")
            record7 = WekoRecord.get_record_by_pid(7)
            record8 = WekoRecord.get_record_by_pid(8)
            with patch("weko_items_ui.utils.get_item_from_option", return_value = meta_list.keys()):
                make_stats_file_with_permission(2, [7,8], {7: record7,8: record8}, permissions)

            p = PersistentIdentifier.query.filter_by(id=1).first()
            with patch("weko_deposit.api.WekoRecord._get_pid", return_value = p):
                make_stats_file_with_permission(2, [7], {7: record7}, permissions)

            with patch("weko_workflow.utils.IdentifierHandle.get_idt_registration_data") as g:
                for i in range(len(app.config["WEKO_IMPORT_DOI_TYPE"])):
                    g.return_value = ([app.config["IDENTIFIER_GRANT_LIST"][i+1][2]],[app.config["WEKO_IMPORT_DOI_TYPE"][i]])
                    make_stats_file_with_permission(2, [7], {7: record7}, permissions)

            i = 0
            for key, v in sorted(itemtype.render["table_row_map"]["schema"]["properties"].items()):
                if v["type"] == "array":
                    v["items"]["properties"]["subitem_1234567890123"] = {
                        "format": "checkboxes",
                        "title": "sample"
                    }
                    i += 1
                    if i > 1: break
            # with patch("weko_items_ui.utils.get_sub_item_option", return_value = "Hide"):
            with app.test_request_context():
                    make_stats_file_with_permission(2, [7,8], {7: record7, 8: record8}, permissions)
            with patch("weko_items_ui.utils.RequestMailList.get_mail_list_by_item_id",return_value = [{"email":"contributor@test.org","author_id":""},{"email":"user@test.org","author_id":""}]):
                with app.test_request_context():
                    assert make_stats_file_with_permission(item_type_id, [7,8], {7: record7, 8: record8}, permissions) == ([['#.id', '.uri', '.metadata.path[0]', '.pos_index[0]', '.publish_status', '.feedback_mail[0]', '.request_mail[0]', '.request_mail[1]', '.cnri', '.doi_ra', '.doi', '.edit_mode', '.metadata.pubdate', '.metadata.item_1617186331708[0].subitem_1551255647225', '.metadata.item_1617186331708[0].subitem_1551255648112', '.metadata.item_1617186385884[0].subitem_1551255720400', '.metadata.item_1617186385884[0].subitem_1551255721061', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifier', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierScheme', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierURI', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNames[0].affiliationName', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNames[0].affiliationNameLang', '.metadata.item_1617186419668[0].creatorAlternatives[0].creatorAlternative', '.metadata.item_1617186419668[0].creatorAlternatives[0].creatorAlternativeLang', '.metadata.item_1617186419668[0].creatorMails[0].creatorMail', '.metadata.item_1617186419668[0].creatorNames[0].creatorName', '.metadata.item_1617186419668[0].creatorNames[0].creatorNameLang', '.metadata.item_1617186419668[0].familyNames[0].familyName', '.metadata.item_1617186419668[0].familyNames[0].familyNameLang', '.metadata.item_1617186419668[0].givenNames[0].givenName', '.metadata.item_1617186419668[0].givenNames[0].givenNameLang', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationNameIdentifier', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationScheme', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationURI', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationName', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationNameLang', '.metadata.item_1617349709064[0].contributorAlternatives[0].contributorAlternative', '.metadata.item_1617349709064[0].contributorAlternatives[0].contributorAlternativeLang', '.metadata.item_1617349709064[0].contributorMails[0].contributorMail', '.metadata.item_1617349709064[0].contributorNames[0].contributorName', '.metadata.item_1617349709064[0].contributorNames[0].lang', '.metadata.item_1617349709064[0].contributorType', '.metadata.item_1617349709064[0].familyNames[0].familyName', '.metadata.item_1617349709064[0].familyNames[0].familyNameLang', '.metadata.item_1617349709064[0].givenNames[0].givenName', '.metadata.item_1617349709064[0].givenNames[0].givenNameLang', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617186476635.subitem_1522299639480', '.metadata.item_1617186476635.subitem_1600958577026', '.metadata.item_1617351524846.subitem_1523260933860', '.metadata.item_1617186499011[0].subitem_1522650717957', '.metadata.item_1617186499011[0].subitem_1522650727486', '.metadata.item_1617186499011[0].subitem_1522651041219', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617610673286[0].rightHolderNames[0].rightHolderLanguage', '.metadata.item_1617610673286[0].rightHolderNames[0].rightHolderName', '.metadata.item_1617186609386[0].subitem_1522299896455', '.metadata.item_1617186609386[0].subitem_1522300014469', '.metadata.item_1617186609386[0].subitem_1522300048512', '.metadata.item_1617186609386[0].subitem_1523261968819', '.metadata.item_1617186626617[0].subitem_description', '.metadata.item_1617186626617[0].subitem_description_language', '.metadata.item_1617186626617[0].subitem_description_type', '.metadata.item_1617186643794[0].subitem_1522300295150', '.metadata.item_1617186643794[0].subitem_1522300316516', '.metadata.item_1617186660861[0].subitem_1522300695726', '.metadata.item_1617186660861[0].subitem_1522300722591', '.metadata.item_1617186702042[0].subitem_1551255818386', '.metadata.item_1617258105262.resourcetype', '.metadata.item_1617258105262.resourceuri', '.metadata.item_1617349808926.subitem_1523263171732', '.metadata.item_1617265215918.subitem_1522305645492', '.metadata.item_1617265215918.subitem_1600292170262', '.metadata.item_1617186783814[0].subitem_identifier_type', '.metadata.item_1617186783814[0].subitem_identifier_uri', '.metadata.item_1617186819068.subitem_identifier_reg_text', '.metadata.item_1617186819068.subitem_identifier_reg_type', '.metadata.item_1617353299429[0].subitem_1522306207484', '.metadata.item_1617353299429[0].subitem_1522306287251.subitem_1522306382014', '.metadata.item_1617353299429[0].subitem_1522306287251.subitem_1522306436033', '.metadata.item_1617353299429[0].subitem_1523320863692[0].subitem_1523320867455', '.metadata.item_1617353299429[0].subitem_1523320863692[0].subitem_1523320909613', '.metadata.item_1617186859717[0].subitem_1522658018441', '.metadata.item_1617186859717[0].subitem_1522658031721', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_east_longitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_north_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_south_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_west_longitude', '.metadata.item_1617186882738[0].subitem_geolocation_place[0].subitem_geolocation_place_text', '.metadata.item_1617186882738[0].subitem_geolocation_point.subitem_point_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_point.subitem_point_longitude', '.metadata.item_1617186901218[0].subitem_1522399143519.subitem_1522399281603', '.metadata.item_1617186901218[0].subitem_1522399143519.subitem_1522399333375', '.metadata.item_1617186901218[0].subitem_1522399412622[0].subitem_1522399416691', '.metadata.item_1617186901218[0].subitem_1522399412622[0].subitem_1522737543681', '.metadata.item_1617186901218[0].subitem_1522399571623.subitem_1522399585738', '.metadata.item_1617186901218[0].subitem_1522399571623.subitem_1522399628911', '.metadata.item_1617186901218[0].subitem_1522399651758[0].subitem_1522721910626', '.metadata.item_1617186901218[0].subitem_1522399651758[0].subitem_1522721929892', '.metadata.item_1617186920753[0].subitem_1522646500366', '.metadata.item_1617186920753[0].subitem_1522646572813', '.metadata.item_1617186941041[0].subitem_1522650068558', '.metadata.item_1617186941041[0].subitem_1522650091861', '.metadata.item_1617186959569.subitem_1551256328147', '.metadata.item_1617186981471.subitem_1551256294723', '.metadata.item_1617186994930.subitem_1551256248092', '.metadata.item_1617187024783.subitem_1551256198917', '.metadata.item_1617187045071.subitem_1551256185532', '.metadata.item_1617187056579.bibliographicIssueDates.bibliographicIssueDate', '.metadata.item_1617187056579.bibliographicIssueDates.bibliographicIssueDateType', '.metadata.item_1617187056579.bibliographicIssueNumber', '.metadata.item_1617187056579.bibliographicNumberOfPages', '.metadata.item_1617187056579.bibliographicPageEnd', '.metadata.item_1617187056579.bibliographicPageStart', '.metadata.item_1617187056579.bibliographicVolumeNumber', '.metadata.item_1617187056579.bibliographic_titles[0].bibliographic_title', '.metadata.item_1617187056579.bibliographic_titles[0].bibliographic_titleLang', '.metadata.item_1617187087799.subitem_1551256171004', '.metadata.item_1617187112279[0].subitem_1551256126428', '.metadata.item_1617187112279[0].subitem_1551256129013', '.metadata.item_1617187136212.subitem_1551256096004', '.metadata.item_1617944105607[0].subitem_1551256015892[0].subitem_1551256027296', '.metadata.item_1617944105607[0].subitem_1551256015892[0].subitem_1551256029891', '.metadata.item_1617944105607[0].subitem_1551256037922[0].subitem_1551256042287', '.metadata.item_1617944105607[0].subitem_1551256037922[0].subitem_1551256047619', '.metadata.item_1617187187528[0].subitem_1599711633003[0].subitem_1599711636923', '.metadata.item_1617187187528[0].subitem_1599711633003[0].subitem_1599711645590', '.metadata.item_1617187187528[0].subitem_1599711655652', '.metadata.item_1617187187528[0].subitem_1599711660052[0].subitem_1599711680082', '.metadata.item_1617187187528[0].subitem_1599711660052[0].subitem_1599711686511', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711704251', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711712451', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711727603', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711731891', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711735410', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711739022', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711743722', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711745532', '.metadata.item_1617187187528[0].subitem_1599711758470[0].subitem_1599711769260', '.metadata.item_1617187187528[0].subitem_1599711758470[0].subitem_1599711775943', '.metadata.item_1617187187528[0].subitem_1599711788485[0].subitem_1599711798761', '.metadata.item_1617187187528[0].subitem_1599711788485[0].subitem_1599711803382', '.metadata.item_1617187187528[0].subitem_1599711813532', '.file_path[0]', '.metadata.item_1617605131499[0].accessrole', '.metadata.item_1617605131499[0].date[0].dateType', '.metadata.item_1617605131499[0].date[0].dateValue', '.metadata.item_1617605131499[0].displaytype', '.metadata.item_1617605131499[0].fileDate[0].fileDateType', '.metadata.item_1617605131499[0].fileDate[0].fileDateValue', '.metadata.item_1617605131499[0].filename', '.metadata.item_1617605131499[0].filesize[0].value', '.metadata.item_1617605131499[0].format', '.metadata.item_1617605131499[0].groups', '.metadata.item_1617605131499[0].licensefree', '.metadata.item_1617605131499[0].licensetype', '.metadata.item_1617605131499[0].url.label', '.metadata.item_1617605131499[0].url.objectType', '.metadata.item_1617605131499[0].url.url', '.metadata.item_1617605131499[0].version', '.metadata.item_1617620223087[0].subitem_1565671149650', '.metadata.item_1617620223087[0].subitem_1565671169640', '.metadata.item_1617620223087[0].subitem_1565671178623', '.thumbnail_path[0]', '.metadata.item_1662046377046[0].subitem_thumbnail[0].thumbnail_label', '.metadata.item_1662046377046[0].subitem_thumbnail[0].thumbnail_url'], ['#ID', 'URI', '.IndexID[0]', '.POS_INDEX[0]', '.PUBLISH_STATUS', '.FEEDBACK_MAIL[0]', '.REQUEST_MAIL[0]', '.REQUEST_MAIL[1]', '.CNRI', '.DOI_RA', '.DOI', 'Keep/Upgrade Version', 'PubDate', 'Title[0].Title', 'Title[0].Language', 'Alternative Title[0].Alternative Title', 'Alternative Title[0].Language', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子URI', 'Creator[0].作成者所属[0].所属機関名[0].所属機関名', 'Creator[0].作成者所属[0].所属機関名[0].言語', 'Creator[0].作成者別名[0].別名', 'Creator[0].作成者別名[0].言語', 'Creator[0].作成者メールアドレス[0].メールアドレス', 'Creator[0].作成者姓名[0].姓名', 'Creator[0].作成者姓名[0].言語', 'Creator[0].作成者姓[0].姓', 'Creator[0].作成者姓[0].言語', 'Creator[0].作成者名[0].名', 'Creator[0].作成者名[0].言語', 'Creator[0].作成者識別子[0].作成者識別子', 'Creator[0].作成者識別子[0].作成者識別子Scheme', 'Creator[0].作成者識別子[0].作成者識別子URI', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子URI', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関名', 'Contributor[0].寄与者所属[0].所属機関識別子[0].言語', 'Contributor[0].寄与者別名[0].別名', 'Contributor[0].寄与者別名[0].言語', 'Contributor[0].寄与者メールアドレス[0].メールアドレス', 'Contributor[0].寄与者姓名[0].姓名', 'Contributor[0].寄与者姓名[0].言語', 'Contributor[0].寄与者タイプ', 'Contributor[0].寄与者姓[0].姓', 'Contributor[0].寄与者姓[0].言語', 'Contributor[0].寄与者名[0].名', 'Contributor[0].寄与者名[0].言語', 'Contributor[0].寄与者識別子[0].寄与者識別子', 'Contributor[0].寄与者識別子[0].寄与者識別子Scheme', 'Contributor[0].寄与者識別子[0].寄与者識別子URI', 'Access Rights.アクセス権', 'Access Rights.アクセス権URI', 'APC.APC', 'Rights[0].言語', 'Rights[0].権利情報Resource', 'Rights[0].権利情報', 'Rights Holder[0].権利者識別子[0].権利者識別子', 'Rights Holder[0].権利者識別子[0].権利者識別子Scheme', 'Rights Holder[0].権利者識別子[0].権利者識別子URI', 'Rights Holder[0].権利者名[0].言語', 'Rights Holder[0].権利者名[0].権利者名', 'Subject[0].言語', 'Subject[0].主題Scheme', 'Subject[0].主題URI', 'Subject[0].主題', 'Description[0].内容記述', 'Description[0].言語', 'Description[0].内容記述タイプ', 'Publisher[0].言語', 'Publisher[0].出版者', 'Date[0].日付タイプ', 'Date[0].日付', 'Language[0].Language', 'Resource Type.資源タイプ', 'Resource Type.資源タイプ識別子', 'Version.バージョン情報', 'Version Type.出版タイプ', 'Version Type.出版タイプResource', 'Identifier[0].識別子タイプ', 'Identifier[0].識別子', 'Identifier Registration.ID登録', 'Identifier Registration.ID登録タイプ', 'Relation[0].関連タイプ', 'Relation[0].関連識別子.識別子タイプ', 'Relation[0].関連識別子.関連識別子', 'Relation[0].関連名称[0].言語', 'Relation[0].関連名称[0].関連名称', 'Temporal[0].言語', 'Temporal[0].時間的範囲', 'Geo Location[0].位置情報（空間）.東部経度', 'Geo Location[0].位置情報（空間）.北部緯度', 'Geo Location[0].位置情報（空間）.南部緯度', 'Geo Location[0].位置情報（空間）.西部経度', 'Geo Location[0].位置情報（自由記述）[0].位置情報（自由記述）', 'Geo Location[0].位置情報（点）.緯度', 'Geo Location[0].位置情報（点）.経度', 'Funding Reference[0].助成機関識別子.助成機関識別子タイプ', 'Funding Reference[0].助成機関識別子.助成機関識別子', 'Funding Reference[0].助成機関名[0].言語', 'Funding Reference[0].助成機関名[0].助成機関名', 'Funding Reference[0].研究課題番号.研究課題URI', 'Funding Reference[0].研究課題番号.研究課題番号', 'Funding Reference[0].研究課題名[0].言語', 'Funding Reference[0].研究課題名[0].研究課題名', 'Source Identifier[0].収録物識別子タイプ', 'Source Identifier[0].収録物識別子', 'Source Title[0].言語', 'Source Title[0].収録物名', 'Volume Number.Volume Number', 'Issue Number.Issue Number', 'Number of Pages.Number of Pages', 'Page Start.Page Start', 'Page End.Page End', 'Bibliographic Information.発行日.日付', 'Bibliographic Information.発行日.日付タイプ', 'Bibliographic Information.号', 'Bibliographic Information.ページ数', 'Bibliographic Information.終了ページ', 'Bibliographic Information.開始ページ', 'Bibliographic Information.巻', 'Bibliographic Information.雑誌名[0].タイトル', 'Bibliographic Information.雑誌名[0].言語', 'Dissertation Number.Dissertation Number', 'Degree Name[0].Degree Name', 'Degree Name[0].Language', 'Date Granted.Date Granted', 'Degree Grantor[0].Degree Grantor Name Identifier[0].Degree Grantor Name Identifier', 'Degree Grantor[0].Degree Grantor Name Identifier[0].Degree Grantor Name Identifier Scheme', 'Degree Grantor[0].Degree Grantor Name[0].Degree Grantor Name', 'Degree Grantor[0].Degree Grantor Name[0].Language', 'Conference[0].Conference Name[0].Conference Name', 'Conference[0].Conference Name[0].Language', 'Conference[0].Conference Sequence', 'Conference[0].Conference Sponsor[0].Conference Sponsor', 'Conference[0].Conference Sponsor[0].Language', 'Conference[0].Conference Date.Conference Date', 'Conference[0].Conference Date.Start Day', 'Conference[0].Conference Date.Start Month', 'Conference[0].Conference Date.Start Year', 'Conference[0].Conference Date.End Day', 'Conference[0].Conference Date.End Month', 'Conference[0].Conference Date.End Year', 'Conference[0].Conference Date.Language', 'Conference[0].Conference Venue[0].Conference Venue', 'Conference[0].Conference Venue[0].Language', 'Conference[0].Conference Place[0].Conference Place', 'Conference[0].Conference Place[0].Language', 'Conference[0].Conference Country', '.ファイルパス[0]', 'File[0].アクセス', 'File[0].オープンアクセスの日付[0].日付タイプ', 'File[0].オープンアクセスの日付[0].日付', 'File[0].表示形式', 'File[0].日付[0].日付タイプ', 'File[0].日付[0].日付', 'File[0].表示名', 'File[0].サイズ[0].サイズ', 'File[0].フォーマット', 'File[0].グループ', 'File[0].自由ライセンス', 'File[0].ライセンス', 'File[0].本文URL.ラベル', 'File[0].本文URL.オブジェクトタイプ', 'File[0].本文URL.本文URL', 'File[0].バージョン情報', 'Heading[0].Language', 'Heading[0].Banner Headline', 'Heading[0].Subheading', '.サムネイルパス[0]', 'サムネイル[0].URI[0].ラベル', 'サムネイル[0].URI[0].URI'], ['#', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', '', '', 'System', '', '', 'System', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', 'System'], ['#', '', 'Allow Multiple', 'Allow Multiple', 'Required', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', '', '', 'Required', 'Required', 'Required, Allow Multiple', 'Required, Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Required', 'Required', '', '', '', 'Allow Multiple', 'Allow Multiple', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Allow Multiple', 'Allow Multiple', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple']], {7: [1, 'Index(public_state = True,harvest_public_state = True)', 'public', '', 'contributor@test.org', 'user@test.org', '', '', '', 'Keep', '2022-08-25', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''], 8: [1, 'Index(public_state = True,harvest_public_state = True)', 'public', '', 'contributor@test.org', 'user@test.org', '', '', '', 'Keep', '2022-08-25', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']})

            permissions['check_created_id'] = lambda a: False
            make_stats_file_with_permission(item_type_id, recids, records_metadata, permissions)


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_make_stats_file_with_permission_issue33432 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_make_stats_file_with_permission_issue33432(app, users,db_itemtype,db_records,db_itemtype2,db_records2):
    item_type_id = 2
    recids = ["7"]
    record0 = WekoRecord.get_record_by_pid(7)
    records_metadata = {"7": record0}
    permissions = dict(
        permission_show_hide=lambda a: True,
        check_created_id=lambda a: True,
        hide_meta_data_for_role=lambda a: True,
        current_language=lambda: True,
    )

    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
            assert (
                make_stats_file_with_permission(
                    item_type_id, recids, records_metadata, permissions
                )
                ==([['#.id', '.uri', '.metadata.path[0]', '.pos_index[0]', '.publish_status', '.feedback_mail[0]', '.request_mail[0]', '.cnri', '.doi_ra', '.doi', '.edit_mode', '.metadata.pubdate', '.metadata.item_1554883918421.subitem_1551255647225', '.metadata.item_1554883918421.subitem_1551255648112', '.metadata.item_1554883961001.subitem_1551255818386', '.metadata.item_1554884042490.subitem_1522299896455', '.metadata.item_1554884042490.subitem_1522300014469', '.metadata.item_1554884042490.subitem_1522300048512', '.metadata.item_1554884042490.subitem_1523261968819', '.metadata.item_1532070986701.creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifier', '.metadata.item_1532070986701.creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierScheme', '.metadata.item_1532070986701.creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierURI', '.metadata.item_1532070986701.creatorAffiliations[0].affiliationNames[0].affiliationName', '.metadata.item_1532070986701.creatorAffiliations[0].affiliationNames[0].affiliationNameLang', '.metadata.item_1532070986701.creatorAlternatives[0].creatorAlternative', '.metadata.item_1532070986701.creatorAlternatives[0].creatorAlternativeLang', '.metadata.item_1532070986701.creatorMails[0].creatorMail', '.metadata.item_1532070986701.creatorNames[0].creatorName', '.metadata.item_1532070986701.creatorNames[0].creatorNameLang', '.metadata.item_1532070986701.familyNames[0].familyName', '.metadata.item_1532070986701.familyNames[0].familyNameLang', '.metadata.item_1532070986701.givenNames[0].givenName', '.metadata.item_1532070986701.givenNames[0].givenNameLang', '.metadata.item_1532070986701.nameIdentifiers[0].nameIdentifier', '.metadata.item_1532070986701.nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1532070986701.nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1532071014836.contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationNameIdentifier', '.metadata.item_1532071014836.contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationScheme', '.metadata.item_1532071014836.contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationURI', '.metadata.item_1532071014836.contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationName', '.metadata.item_1532071014836.contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationNameLang', '.metadata.item_1532071014836.contributorAlternatives[0].contributorAlternative', '.metadata.item_1532071014836.contributorAlternatives[0].contributorAlternativeLang', '.metadata.item_1532071014836.contributorMails[0].contributorMail', '.metadata.item_1532071014836.contributorNames[0].contributorName', '.metadata.item_1532071014836.contributorNames[0].lang', '.metadata.item_1532071014836.contributorType', '.metadata.item_1532071014836.familyNames[0].familyName', '.metadata.item_1532071014836.familyNames[0].familyNameLang', '.metadata.item_1532071014836.givenNames[0].givenName', '.metadata.item_1532071014836.givenNames[0].givenNameLang', '.metadata.item_1532071014836.nameIdentifiers[0].nameIdentifier', '.metadata.item_1532071014836.nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1532071014836.nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1532071031458.subitem_1522299639480', '.metadata.item_1532071031458.subitem_1600958577026', '.metadata.item_1532071039842[0].subitem_1522650717957', '.metadata.item_1532071039842[0].subitem_1522650727486', '.metadata.item_1532071039842[0].subitem_1522651041219', '.metadata.item_1532071057095[0].subitem_1522299896455', '.metadata.item_1532071057095[0].subitem_1522300014469', '.metadata.item_1532071057095[0].subitem_1522300048512', '.metadata.item_1532071057095[0].subitem_1523261968819', '.metadata.item_1532071068215[0].subitem_1522657647525', '.metadata.item_1532071068215[0].subitem_1522657697257', '.metadata.item_1532071068215[0].subitem_1523262169140', '.metadata.item_1532071093517[0].subitem_1522300295150', '.metadata.item_1532071093517[0].subitem_1522300316516', '.metadata.item_1532071103206[0].subitem_1522300695726', '.metadata.item_1532071103206[0].subitem_1522300722591', '.metadata.item_1569380622649.resourcetype', '.metadata.item_1569380622649.resourceuri', '.metadata.item_1581493352241.subitem_1569224170590', '.metadata.item_1581493352241.subitem_1569224172438', '.metadata.item_1532071133483', '.metadata.item_1532071158138[0].subitem_1522306207484', '.metadata.item_1532071158138[0].subitem_1522306287251.subitem_1522306382014', '.metadata.item_1532071158138[0].subitem_1522306287251.subitem_1522306436033', '.metadata.item_1532071158138[0].subitem_1523320863692[0].subitem_1523320867455', '.metadata.item_1532071158138[0].subitem_1523320863692[0].subitem_1523320909613', '.metadata.item_1532071168802[0].subitem_1522658018441', '.metadata.item_1532071168802[0].subitem_1522658031721', '.metadata.item_1532071184504[0].subitem_1522658250154.subitem_1522658252485', '.metadata.item_1532071184504[0].subitem_1522658250154.subitem_1522658264346', '.metadata.item_1532071184504[0].subitem_1522658250154.subitem_1522658270105', '.metadata.item_1532071184504[0].subitem_1522658250154.subitem_1522658274386', '.metadata.item_1532071184504[0].subitem_1523321394401.subitem_1523321400758', '.metadata.item_1532071184504[0].subitem_1523321394401.subitem_1523321450098', '.metadata.item_1532071184504[0].subitem_1523321527273', '.metadata.item_1532071200841[0].subitem_1522399143519.subitem_1522399281603', '.metadata.item_1532071200841[0].subitem_1522399143519.subitem_1522399333375', '.metadata.item_1532071200841[0].subitem_1522399412622[0].subitem_1522399416691', '.metadata.item_1532071200841[0].subitem_1522399412622[0].subitem_1522737543681', '.metadata.item_1532071200841[0].subitem_1522399571623.subitem_1522399585738', '.metadata.item_1532071200841[0].subitem_1522399571623.subitem_1522399628911', '.metadata.item_1532071200841[0].subitem_1522399651758[0].subitem_1522721910626', '.metadata.item_1532071200841[0].subitem_1522399651758[0].subitem_1522721929892', '.metadata.item_1532071216312[0].subitem_1522652546580.subitem_1522652548920', '.metadata.item_1532071216312[0].subitem_1522652546580.subitem_1522652672693', '.metadata.item_1532071216312[0].subitem_1522652546580.subitem_1522652685531', '.metadata.item_1532071216312[0].subitem_1522652734962', '.metadata.item_1532071216312[0].subitem_1522652740098[0].subitem_1522722119299', '.metadata.item_1532071216312[0].subitem_1522652747880[0].subitem_1522722132466', '.metadata.item_1532071216312[0].subitem_1522652747880[0].subitem_1522739295711', '.metadata.item_1532071216312[0].subitem_1523325300505', '.thumbnail_path', '.metadata.item_1568286510993.subitem_thumbnail[0].thumbnail_label', '.metadata.item_1568286510993.subitem_thumbnail[0].thumbnail_url', '.file_path[0]', '.metadata.item_1600165182071[0].accessrole', '.metadata.item_1600165182071[0].date[0].dateType', '.metadata.item_1600165182071[0].date[0].dateValue', '.metadata.item_1600165182071[0].displaytype', '.metadata.item_1600165182071[0].filename', '.metadata.item_1600165182071[0].filesize[0].value', '.metadata.item_1600165182071[0].format', '.metadata.item_1600165182071[0].groupsprice[0].group', '.metadata.item_1600165182071[0].groupsprice[0].price', '.metadata.item_1600165182071[0].is_billing', '.metadata.item_1600165182071[0].licensefree', '.metadata.item_1600165182071[0].licensetype', '.metadata.item_1600165182071[0].url.label', '.metadata.item_1600165182071[0].url.objectType', '.metadata.item_1600165182071[0].url.url', '.metadata.item_1600165182071[0].version'], ['#ID', 'URI', '.IndexID[0]', '.POS_INDEX[0]', '.PUBLISH_STATUS', '.FEEDBACK_MAIL[0]', '.REQUEST_MAIL[0]', '.CNRI', '.DOI_RA', '.DOI', 'Keep/Upgrade Version', 'PubDate', 'Title.Title', 'Title.Language', 'Language.Language', 'Keyword.言語', 'Keyword.主題Scheme', 'Keyword.主題URI', 'Keyword.主題', 'Creator.作成者所属[0].所属機関識別子[0].所属機関識別子', 'Creator.作成者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Creator.作成者所属[0].所属機関識別子[0].所属機関識別子URI', 'Creator.作成者所属[0].所属機関名[0].所属機関名', 'Creator.作成者所属[0].所属機関名[0].言語', 'Creator.作成者別名[0].別名', 'Creator.作成者別名[0].言語', 'Creator.作成者メールアドレス[0].メールアドレス', 'Creator.作成者姓名[0].姓名', 'Creator.作成者姓名[0].言語', 'Creator.作成者姓[0].姓', 'Creator.作成者姓[0].言語', 'Creator.作成者名[0].名', 'Creator.作成者名[0].言語', 'Creator.作成者識別子[0].作成者識別子', 'Creator.作成者識別子[0].作成者識別子Scheme', 'Creator.作成者識別子[0].作成者識別子URI', 'Contributor.寄与者所属[0].所属機関識別子[0].所属機関識別子', 'Contributor.寄与者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Contributor.寄与者所属[0].所属機関識別子[0].所属機関識別子URI', 'Contributor.寄与者所属[0].所属機関識別子[0].所属機関名', 'Contributor.寄与者所属[0].所属機関識別子[0].言語', 'Contributor.寄与者別名[0].別名', 'Contributor.寄与者別名[0].言語', 'Contributor.寄与者メールアドレス[0].メールアドレス', 'Contributor.寄与者名[0].姓名', 'Contributor.寄与者名[0].言語', 'Contributor.寄与者タイプ', 'Contributor.寄与者姓[0].姓', 'Contributor.寄与者姓[0].言語', 'Contributor.寄与者名[0]. 名', 'Contributor.寄与者名[0].言語', 'Contributor.寄与者識別子[0].寄与者識別子', 'Contributor.寄与者識別子[0].寄与者識別子Scheme', 'Contributor.寄与者識別子[0].寄与者識別子URI', 'Access Rights.アクセス権', 'Access Rights.アクセス権URI', 'Rights Information[0].言語', 'Rights Information[0].権利情報Resource', 'Rights Information[0].権利情報', 'Subject[0].言語', 'Subject[0].主題Scheme', 'Subject[0].主題URI', 'Subject[0].主題', 'Content Description[0].内容記述タイプ', 'Content Description[0].内容記述', 'Content Description[0].言語', 'Publisher[0].言語', 'Publisher[0].出版者', 'Date[0].日付タイプ', 'Date[0].日付', 'Resource Type.Type', 'Resource Type.Resource', 'Identifier rRegistration.Identifier Registration', 'Identifier rRegistration.Identifier Registration Type', 'Version information', 'Related information[0].関連タイプ', 'Related information[0].関連識別子.識別子タイプ', 'Related information[0].関連識別子.関連識別子', 'Related information[0].関連名称[0].言語', 'Related information[0].関連名称[0].関連名称', 'Time Range[0].言語', 'Time Range[0].時間的範囲', 'Location Information[0].位置情報（空間）. 西部経度', 'Location Information[0].位置情報（空間）.東部経度', 'Location Information[0].位置情報（空間）.南部緯度', 'Location Information[0].位置情報（空間）.北部緯度', 'Location Information[0].位置情報（点）.経度', 'Location Information[0].位置情報（点）.緯度', 'Location Information[0].位置情報（自由記述）', 'Grant information[0].助成機関識別子.助成機関識別子タイプ', 'Grant information[0].助成機関識別子.助成機関識別子', 'Grant information[0].助成機関 名[0].言語', 'Grant information[0].助成機関 名[0].助成機関名', 'Grant information[0].研究課題番号.研究課題URI', 'Grant information[0].研究課題番号.研究課題番号', 'Grant information[0].研究課題名[0].言語', 'Grant information[0].研究課題名[0]. 研究課題名', 'File Information[0].本文URL.オブジェクトタイプ', 'File Information[0].本文URL.ラベル', 'File Information[0].本文URL.本文URL', 'File Information[0].フォーマット', 'File Information[0].サイズ[0].サイズ', 'File Information[0].日付[0].日付タイプ', 'File Information[0].日付[0].日付', 'File Information[0].バージョン情報', '.サムネイルパス', 'Thumbnail.URI[0].URI Label', 'Thumbnail.URI[0].URI', '.ファイルパス[0]', 'Billing File Information[0].アクセス', 'Billing File Information[0].日付[0].日付タイプ', 'Billing File Information[0].日付[0].日付', 'Billing File Information[0].表示形式', 'Billing File Information[0].表示名', 'Billing File Information[0].サイズ[0].サイズ', 'Billing File Information[0]. フォーマット', 'Billing File Information[0].グループ・価格[0].グループ', 'Billing File Information[0].グループ・価格[0].価格', 'Billing File Information[0].Is Billing', 'Billing File Information[0].自由ライセンス', 'Billing File Information[0].ライセンス', 'Billing File Information[0].本文URL.ラベル', 'Billing File Information[0].本文URL.オブジェクト タイプ', 'Billing File Information[0].本文URL.本文URL', 'Billing File Information[0].バージョン情報'], ['#', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', 'System', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''], ['#', '', 'Allow Multiple', 'Allow Multiple', 'Required', 'Allow Multiple', 'Allow Multiple', '', '', '', 'Required', 'Required', 'Required', 'Required', 'Required', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Required', 'Required', '', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', 'Hide', 'Hide', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple']], {'7': [1, 'Index(public_state = True,harvest_public_state = True)', 'public', '', '', '', '', '', 'Keep', '2022-08-25', 'タイトル', 'ja', 'jpn', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'A大学', 'ja', '', '', 'repoadmin@test.org', '寄与者', 'ja', 'ContactPerson', '', '', '', '', '', '', '', 'open access', 'http://purl.org/coar/access_right/c_abf2', 'ja', 'CC0', '一定期間後に事業の実施上有益な者に対しての提供を開始する。但しデータのクレジット表記を条件とする。', 'ja', 'NDC', '', '複合化学', 'abstract', '概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要概要', 'ja', '', '', '', '', 'dataset', 'http://purl.org/coar/resource_type/c_ddb1', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Crossref Funder', 'https://dx.doi.org/10.13039/501100001863', 'ja', 'NEDO', '', '12345678', 'ja', 'プロジェクト', '', '', '', '', '1GB未満', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']})
            )

# def check_item_is_being_edit(
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_check_item_is_being_edit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_check_item_is_being_edit(db, db_records, db_workflow, db_activity):
    workflow = db_workflow["workflow"]
    depid, recid, parent, doi, record, item = db_records[1]
    assert check_item_is_being_edit(recid) == False

    post_workflow = Activity()
    post_workflow.action_status = ActionStatusPolicy.ACTION_DOING
    assert check_item_is_being_edit(recid, post_workflow) == True

    depid, recid, parent, doi, record, item = db_records[0]
    assert check_item_is_being_edit(recid) == True


# def check_item_is_deleted(recid):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_check_item_is_deleted -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_check_item_is_deleted(db_records):
    depid, recid, parent, doi, record, item = db_records[0]
    id = str(recid.pid_value)
    assert check_item_is_deleted(id) == False
    id = str(recid.object_uuid)
    assert check_item_is_deleted(id) == False
    recid.status = PIDStatus.DELETED
    id = str(recid.pid_value)
    assert check_item_is_deleted(recid.pid_value) == True
    id = str(recid.object_uuid)
    assert check_item_is_deleted(recid.pid_value) == True


# def permission_ranking(result, pid_value_permissions, display_rank, list_name,
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_permission_ranking -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_permission_ranking():
    result = {
        "date": "",
        "all": [
            {
                "record_id": "36eb0ad8-d961-46a5-900b-e7787560094d",
                "record_name": "ja_conference paperITEM00000001(public_open_access_open_access_simple)",
                "index_names": "IndexA",
                "total_all": 4,
                "pid_value": "1",
                "total_not_login": 1,
                "same_title": True,
            },
            {
                "record_id": "e36a3cee-6e44-4c4e-8181-bbad60d35f41",
                "record_name": "ja_conference paperITEM00000002(public_open_access_open_access_simple)",
                "index_names": "IndexA",
                "total_all": 4,
                "pid_value": "12",
                "total_not_login": 0,
                "same_title": True,
            },
            {
                "record_id": "2b4a0689-a1f0-40c4-a7e2-a46e96511072",
                "record_name": "あああ",
                "index_names": "IndexA",
                "total_all": 1,
                "pid_value": "11",
                "total_not_login": 0,
                "same_title": True,
            },
        ],
    }
    pid_value_permissions = ["11"]
    display_rank = 10
    list_name = "all"
    pid_value = "pid_value"
    permission_ranking(
        result, pid_value_permissions, display_rank, list_name, pid_value
    )
    assert result == {
        "all": [
            {
                "index_names": "IndexA",
                "pid_value": "11",
                "record_id": "2b4a0689-a1f0-40c4-a7e2-a46e96511072",
                "record_name": "あああ",
                "same_title": True,
                "total_all": 1,
                "total_not_login": 0,
            }
        ],
        "date": "",
    }

    result = {"num_page": 0, "page": 1, "data": []}
    pid_value_permissions = ["11"]
    display_rank = 10
    list_name = "data"
    pid_value = "col1"
    permission_ranking(
        result, pid_value_permissions, display_rank, list_name, pid_value
    )
    assert result == {"data": [], "num_page": 0, "page": 1}


# def has_permission_edit_item(record, recid):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_has_permission_edit_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_has_permission_edit_item(app, client, users, db_records):
    with app.test_request_context():
        depid, recid, parent, doi, record, item = db_records[0]
        assert has_permission_edit_item(record, record.pid.pid_value) == False

    with app.test_request_context():
        login_user(users[0]['obj'])
        assert users[0]["email"] == "contributor@test.org"
        depid, recid, parent, doi, record, item = db_records[0]
        assert has_permission_edit_item(record, record.pid.pid_value) == False

    with app.test_request_context():
        login_user(users[1]["obj"])
        assert users[1]["email"] == "repoadmin@test.org"
        depid, recid, parent, doi, record, item = db_records[0]
        assert has_permission_edit_item(record, record.pid.pid_value) == True

    with app.test_request_context():
        login_user(users[2]["obj"])
        assert users[2]["email"] == "sysadmin@test.org"
        depid, recid, parent, doi, record, item = db_records[0]
        assert has_permission_edit_item(record, record.pid.pid_value) == True

    with app.test_request_context():
        login_user(users[3]["obj"])
        assert users[3]["email"] == "comadmin@test.org"
        depid, recid, parent, doi, record, item = db_records[0]
        assert has_permission_edit_item(record, record.pid.pid_value) == False

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_has_permission_edit_item2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_has_permission_edit_item2(app, client, users, db_records):
    with app.test_request_context():
        login_user(users[4]["obj"])
        assert users[4]["email"] == "generaluser@test.org"
        depid, recid, parent, doi, record, item = db_records[0]
        assert has_permission_edit_item(record, record.pid.pid_value) == True

    with app.test_request_context():
        login_user(users[5]["obj"])
        assert users[5]["email"] == "originalroleuser@test.org"
        depid, recid, parent, doi, record, item = db_records[0]
        assert has_permission_edit_item(record, record.pid.pid_value) == False

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_has_permission_edit_item3 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_has_permission_edit_item3(app, client, users, db_records):
    with app.test_request_context():
        login_user(users[6]["obj"])
        assert users[6]["email"] == "originalroleuser2@test.org"
        depid, recid, parent, doi, record, item = db_records[0]
        assert has_permission_edit_item(record, record.pid.pid_value) == True

    with app.test_request_context():
        login_user(users[7]["obj"])
        assert users[7]["email"] == "user@test.org"
        depid, recid, parent, doi, record, item = db_records[0]
        assert has_permission_edit_item(record, record.pid.pid_value) == True


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_file_download_data -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_file_download_data(app, client, records):
    indexer, results = records

    with app.test_request_context():
        # 12 Can sort download_total
        record = results[1]["record"]
        filenames = ["helloworld.pdf", "helloworld.docx"]
        for file in record.files:
            file["accessrole"] = "open_access"
            file["filename"] = file["key"]
        return_value = {
            'download_ranking': {
                'doc_count_error_upper_bound': 0,
                'sum_other_doc_count': 0,
                'buckets': [
                    {
                        'key': filenames[1],
                        'doc_count': 3
                    },
                    {
                        'key': filenames[0],
                        'doc_count': 5
                    },
                ]
            }
        }
        with patch("invenio_stats.queries.ESWekoFileRankingQuery.run", return_value=return_value):
            res = get_file_download_data(record.id, record, filenames)
            assert res["ranking"][0]["download_total"] == 5
            assert res["ranking"][1]["download_total"] == 3

        # 13 Both accessrole
        record = results[3]["record"]
        filenames = ["helloworld.pdf", "helloworld.txt"]
        accessrole_list = ["open_access", "open_no"]
        for file, accessrole in zip(record.files, accessrole_list):
            file["accessrole"] = accessrole
            file["filename"] = file["key"]
        return_value = {
            'download_ranking': {
                'doc_count_error_upper_bound': 0,
                'sum_other_doc_count': 0,
                'buckets': [
                    {
                        'key': filenames[0],
                        'doc_count': 5
                    },
                    {
                        'key': filenames[1],
                        'doc_count': 3
                    },
                ]
            }
        }
        with patch("invenio_stats.queries.ESWekoFileRankingQuery.run", return_value=return_value):
            res = get_file_download_data(record.id, record, filenames)
            assert len(res["ranking"]) == 1
            assert res["ranking"][0]["filename"] == "helloworld.pdf"

        # 14 Set date
        with patch("invenio_stats.queries.ESWekoFileRankingQuery.run", return_value=return_value) as test_mock:
            res = get_file_download_data(record.id, record, filenames, "2024-01")
            assert test_mock.call_args[1]["start_date"] == "2024-01-01"
            assert test_mock.call_args[1]["end_date"] == "2024-01-31T23:59:59"

        # 15 Set size
        record = results[1]["record"]
        filenames = ["helloworld.pdf", "helloworld.docx"]
        for file in record.files:
            file["accessrole"] = "open_access"
            file["filename"] = file["key"]
        return_value = {
            'download_ranking': {
                'doc_count_error_upper_bound': 0,
                'sum_other_doc_count': 0,
                'buckets': [
                    {
                        'key': filenames[0],
                        'doc_count': 3
                    },
                    {
                        'key': filenames[1],
                        'doc_count': 5
                    },
                ]
            }
        }
        with patch("invenio_stats.queries.ESWekoFileRankingQuery.run", return_value=return_value):
            res = get_file_download_data(record.id, record, filenames, size=1)
            assert len(res["ranking"]) == 1
            assert res["ranking"][0]["download_total"] == 5

        # 16 Exeption in running query
        with patch("invenio_stats.queries.ESWekoFileRankingQuery.run", side_effect=Exception):
            res = get_file_download_data(record.id, record, filenames)
            assert res["ranking"][0]["download_total"] \
                    == res["ranking"][1]["download_total"] \
                    == 0

        with patch("invenio_stats.queries.ESWekoFileRankingQuery.run", return_value=Exception):
            res = get_file_download_data(record.id, record, filenames)
            assert res["ranking"][0]["download_total"] \
                    == res["ranking"][1]["download_total"] \
                    == 0

        # 17 Only unavailable file
        record = results[4]["record"]
        filenames = ["helloworld.pdf"]
        for file in record.files:
            file["accessrole"] = "open_no"
            file["filename"] = file["key"]
        with pytest.raises(AvailableFilesNotFoundRESTError):
            get_file_download_data(record.id, record, filenames)

        # 18 Not exist file
        record = results[5]["record"]
        with pytest.raises(AvailableFilesNotFoundRESTError):
            get_file_download_data(record.id, record, filenames)
            
# def get_weko_link(metadata):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_weko_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_weko_link(app, client, users, db_records, mocker):
    mocker.patch("weko_items_ui.utils.WekoAuthors.get_pk_id_by_weko_id",side_effect=["2","0"])
    res = get_weko_link(
        {
            "metainfo": {
                "item_30002_creator2": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "8",
                                "nameIdentifierScheme": "WEKO",
                                "nameIdentifierURI": "",
                            }
                        ]
                    }
                ],
                "item_30003_creator2": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "8",
                                "nameIdentifierScheme": "WEKO",
                                "nameIdentifierURI": "",
                            }
                        ]
                    }
                ],
                "item_30004_creator2": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "12",
                                "nameIdentifierScheme": "WEKO",
                                "nameIdentifierURI": "",
                            }
                        ]
                    }
                ]
            },
            "files": [],
            "endpoints": {"initialization": "/api/deposits/items"},
        }
    )
    assert res == {"2": "8"}
    res = get_weko_link(
        {
            "metainfo": {
                "item_30002_creator2": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "8",
                                "nameIdentifierScheme": "OTHER",
                                "nameIdentifierURI": "",
                            }
                        ]
                    }
                ]
            },
            "files": [],
            "endpoints": {"initialization": "/api/deposits/items"},
        }
    )
    assert res == {}
    
    # not isinstance(x, list) is true
    res = get_weko_link({"metainfo": {"field1": "string_value"}})
    assert res == {}
    
    # not isinstance(y, dict) is true
    res = get_weko_link({"metainfo": {"field1": ["string_value"]}})
    assert res == {}
    
    # not key == "nameIdentifiers" is true
    res = get_weko_link({"metainfo": {"field1": [{"field2": {}}]}})
    assert res == {}

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_access_token -vv -s --cov-branch --cov-report=xml --cov-report=html --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_access_token(app, mock_certificate):
    """get_access_tokenの全シナリオ（正常系と異常系）をテスト"""
    with app.test_request_context():

        # 1. api_codeが空の場合 (400)
        result, status = get_access_token(None)
        assert status == 400, "api_codeが空の場合、400が返るべき"
        assert result == {"error": "invalid_request", "message": "Required API Code"}

        # 2. 無効なapi_codeの場合 (401)
        with patch.object(ApiCertificate, "select_by_api_code", return_value=None):
            result, status = get_access_token("invalid_code")
            assert status == 401, "無効なapi_codeの場合、401が返るべき"
            assert result == {"error": "invalid_client"}

        # 3. 有効な既存トークンが存在する場合 (200相当)
        with patch.object(ApiCertificate, "select_by_api_code", return_value=mock_certificate):
            result = get_access_token("valid_code")
            assert "access_token" in result, "有効なトークンが返るべき"
            assert result["access_token"] == "valid_token"
            assert result["token_type"] == "Bearer"
            assert isinstance(result["expires_in"], int)
            assert result["expires_in"] > 0

        # 4. 期限切れのトークンの場合 (新しいトークン発行)
        expired_certificate = {
            "cert_data": {
                "token": "expired_token",
                "expires_at": (datetime.now() - timedelta(seconds=3600)).strftime("%Y-%m-%dT%H:%M:%S")
            }
        }
        with patch.object(ApiCertificate, "select_by_api_code", return_value=expired_certificate):
            result = get_access_token("expired_code")
            assert "access_token" in result, "新しいトークンが発行されるべき"
            assert result["access_token"] != "expired_token"
            assert result["token_type"] == "Bearer"
            assert result["expires_in"] == 3600

        # 5. 証明書にトークンがない場合 (新しいトークン発行)
        no_token_certificate = {"cert_data": {}}
        with patch.object(ApiCertificate, "select_by_api_code", return_value=no_token_certificate):
            result = get_access_token("no_token_code")
            assert "access_token" in result, "トークンがない場合、新しいトークンが発行されるべき"
            assert len(result["access_token"]) == 54  # secrets.token_urlsafe(40)の長さ
            assert result["token_type"] == "Bearer"
            assert result["expires_in"] == 3600

        # 6. 例外が発生した場合 (500)
        with patch.object(ApiCertificate, "select_by_api_code", side_effect=Exception("テストエラー")):
            result, status = get_access_token("error_code")
            assert status == 500, "例外が発生した場合、500が返るべき"
            assert result == {"error": "Internal server error"}
# def check_duplicate(data, is_item=True):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_check_duplicate -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_check_duplicate(app, users,db_records3):
    # JSON format NG
    res, [], [] =  check_duplicate('',True)
    assert res == False

    # data dict NG
    res, [], [] =  check_duplicate(1,True)
    assert res == False

    # metadata format NG
    res, [], [] =  check_duplicate({"metainfo":123},False)
    assert res == False
    
    # first_item not dict
    res, [], [] =  check_duplicate({"subitem_identifier_uri":[{"subitem_identifier_uri"}]},True)
    assert res == False
    
    # subitem_identifier_uri NG
    res, [], [] =  check_duplicate({"subitem_identifier_uri":[{"subitem_identifier_uri":"noexists"}]},True)
    assert res == False
    
    # subitem_identifier_uri OK
    res, recid_list, item_links =  check_duplicate({"subitem_identifier_uri":[{"subitem_identifier_uri":"http://localhost"}]},True)
    assert recid_list[0] == 8
    
    # subitem_title NG
    res, [], [] =  check_duplicate({"subitem_title":[{"subitem_title":"title"}]},True)
    assert res == False
    
    # subitem_title:T  resource_type:T
    res, [], [] =  check_duplicate({"subitem_title":[{"subitem_title":"タイトル"}],"resourcetype":{"resourcetype":"Resource Type"}},True)
    assert res == False
    
    # creatorNames NG
    res, [], [] =  check_duplicate({"creatorNames":[{"creatorNames":[{"creatorName":"test"}]}]},True)
    assert res == False

    # creatorNames OK
    res, recid_list, item_links =  check_duplicate({"creatorNames":[{"creatorNames":[{"creatorName":"情報, 太郎"}]}]},True)
    assert recid_list[0] == 8

    # resourcetype
    res, [], [] =  check_duplicate({"resourcetype":{"resourcetype":"test"}},True)
    assert res == False
