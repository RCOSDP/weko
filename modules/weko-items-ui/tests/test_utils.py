import csv
import hashlib
import json
from datetime import datetime
from io import StringIO
from unittest.mock import MagicMock

import pytest
from flask_security.utils import login_user
from invenio_accounts.testutils import login_user_via_session
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from jsonschema import SchemaError, ValidationError
from mock import patch
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_records.api import FeedbackMailList, ItemTypes, Mapping
from weko_workflow.api import WorkActivity
from weko_workflow.models import (
    Action,
    ActionStatus,
    ActionStatusPolicy,
    Activity,
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
)


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


# def get_user_info_by_email(email):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_user_info_by_email -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_user_info_by_email(users, db_userprofile):
    assert get_user_info_by_email(users[0]["email"]) == {
        "username": db_userprofile[users[0]["email"]].get_username,
        "user_id": users[0]["id"],
        "email": users[0]["email"],
    }


# def get_user_information(user_id):
#  .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_user_information -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_user_information(users, db_userprofile):
    assert get_user_information(users[0]["id"]) == {
        "username": db_userprofile[users[0]["email"]].get_username,
        "fullname": db_userprofile[users[0]["email"]].fullname,
        "email": users[0]["email"],
    }


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
            assert target == []


# def parse_ranking_results(index_info,
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_parse_ranking_results -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_parse_ranking_results(app, db_itemtype, db_records):
    depid0, recid0, parent0, doi0, record0, item0 = db_records[0]
    depid1, recid1, parent1, doi1, record1, item1 = db_records[1]
    depid2, recid2, parent2, doi2, record2, item2 = db_records[2]
    depid3, recid3, parent3, doi3, record3, item3 = db_records[3]
    index_info = {
        "1": {
            "index_name": "IndexA",
            "parent": "0",
            "public_date": None,
            "harvest_public_state": True,
            "browsing_role": ["3", "-98", "-99"],
        }
    }
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
                    "_id": str(record0.id),
                    "_score": None,
                    "_source": {
                        "_created": "2022-08-20T06:05:56.806896+00:00",
                        "_updated": "2022-08-20T06:06:24.602226+00:00",
                        "type": ["conference paper"],
                        "title": ["ff"],
                        "control_number": "1",
                        "_oai": {
                            "id": "oai:weko3.example.org:00000003",
                            "sets": ["1"],
                        },
                        "_item_metadata": {
                            "_oai": {
                                "id": "oai:weko3.example.org:00000003",
                                "sets": ["1"],
                            },
                            "path": ["1"],
                            "owner": "1",
                            "title": ["ff"],
                            "pubdate": {
                                "attribute_name": "PubDate",
                                "attribute_value": "2022-08-20",
                            },
                            "item_title": "ff",
                            "author_link": [],
                            "item_type_id": "1",
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
                            "control_number": "1",
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
                    "_id": str(record2.id),
                    "_score": None,
                    "_source": {
                        "_created": "2022-08-17T17:00:43.877778+00:00",
                        "_updated": "2022-08-17T17:01:08.615488+00:00",
                        "type": ["conference paper"],
                        "title": ["2"],
                        "control_number": "2",
                        "_oai": {
                            "id": "oai:weko3.example.org:00000001",
                            "sets": ["1"],
                        },
                        "_item_metadata": {
                            "_oai": {
                                "id": "oai:weko3.example.org:00000001",
                                "sets": ["1"],
                            },
                            "path": ["1"],
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
                        "path": ["1"],
                        "publish_status": "0",
                    },
                    "sort": [1660780800000],
                },
            ],
        },
    }
    display_rank = 10
    list_name = "all"
    title_key = "record_name"
    count_key = None
    pid_key = "pid_value"
    search_key = None
    date_key = "create_date"
    ranking_list = [
        {"date": "2022-08-20", "title": "title", "url": "../records/1"},
        {"date": "2022-08-18", "title": "title2", "url": "../records/2"},
    ]
    with app.test_request_context():
        assert (
            parse_ranking_results(
                index_info,
                results,
                display_rank,
                list_name,
                title_key,
                count_key,
                pid_key,
                search_key,
                date_key,
            )
            == ranking_list
        )


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
        assert update_json_schema_with_required_items(node, json_data) == {}


# def update_json_schema_by_activity_id(json_data, activity_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_update_json_schema_by_activity_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_update_json_schema_by_activity_id(app):
    with open("tests/data/json_data.json", "r") as f:
        json_data = json.load(f)
        with app.test_request_context():
            assert (
                update_json_schema_by_activity_id(json_data, "A-00000000-00000") == ""
            )


# def update_schema_form_by_activity_id(schema_form, activity_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_update_schema_form_by_activity_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_update_schema_form_by_activity_id(app):
    with app.test_request_context():
        assert update_schema_form_by_activity_id({}, "A-00000000-00000")


# def recursive_prepare_either_required_list(schema_form, either_required_list):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_recursive_prepare_either_required_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_recursive_prepare_either_required_list(app):
    with app.test_request_context():
        assert recursive_prepare_either_required_list({}, []) == None


# def recursive_update_schema_form_with_condition(
#     def prepare_either_condition_required(group_idx, key):
#     def set_on_change(elem):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_recursive_update_schema_form_with_condition -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_recursive_update_schema_form_with_condition():
    assert recursive_update_schema_form_with_condition({}, []) == None


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
def test_make_stats_file(app, db_itemtype, db_records):
    item_types_data = {
        "1": {
            "item_type_id": "1",
            "name": "デフォルトアイテムタイプ（フル）(15)",
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
    with app.test_request_context():
        assert make_stats_file(item_type_id, [1], list_item_role) == (
            [
                [
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
                    ".metadata.item_1617186385884[0].subitem_1551255720400",
                    ".metadata.item_1617186385884[0].subitem_1551255721061",
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
                    ".metadata.item_1617186419668[0].familyNames[0].familyName",
                    ".metadata.item_1617186419668[0].familyNames[0].familyNameLang",
                    ".metadata.item_1617186419668[0].givenNames[0].givenName",
                    ".metadata.item_1617186419668[0].givenNames[0].givenNameLang",
                    ".metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifier",
                    ".metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierScheme",
                    ".metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierURI",
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
                    ".metadata.item_1617349709064[0].contributorType",
                    ".metadata.item_1617349709064[0].familyNames[0].familyName",
                    ".metadata.item_1617349709064[0].familyNames[0].familyNameLang",
                    ".metadata.item_1617349709064[0].givenNames[0].givenName",
                    ".metadata.item_1617349709064[0].givenNames[0].givenNameLang",
                    ".metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifier",
                    ".metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierScheme",
                    ".metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierURI",
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
                ],
                [
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
                    "Alternative Title[0].Alternative Title",
                    "Alternative Title[0].Language",
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
                    "Creator[0].作成者姓[0].姓",
                    "Creator[0].作成者姓[0].言語",
                    "Creator[0].作成者名[0].名",
                    "Creator[0].作成者名[0].言語",
                    "Creator[0].作成者識別子[0].作成者識別子",
                    "Creator[0].作成者識別子[0].作成者識別子Scheme",
                    "Creator[0].作成者識別子[0].作成者識別子URI",
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
                    "Contributor[0].寄与者タイプ",
                    "Contributor[0].寄与者姓[0].姓",
                    "Contributor[0].寄与者姓[0].言語",
                    "Contributor[0].寄与者名[0].名",
                    "Contributor[0].寄与者名[0].言語",
                    "Contributor[0].寄与者識別子[0].寄与者識別子",
                    "Contributor[0].寄与者識別子[0].寄与者識別子Scheme",
                    "Contributor[0].寄与者識別子[0].寄与者識別子URI",
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
                ],
                [
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
                ],
                [
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
                ],
            ],
            {
                1: [
                    "1",
                    "",
                    "public",
                    "",
                    "",
                    "",
                    "",
                    "Keep",
                    "2022-08-20",
                    "title",
                    "ja",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "conference paper",
                    "http://purl.org/coar/resource_type/c_5794",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            },
        )


# def get_list_file_by_record_id(recid):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_list_file_by_record_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_list_file_by_record_id(db_records):
    assert get_list_file_by_record_id(1) == []


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
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_files_from_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_write_files():
    assert write_files() == ""


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
def test_export_items():
    assert export_items({}) == ""


# def _get_max_export_items():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_files_from_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test__get_max_export_items():
    assert _get_max_export_items() == ""


# def _export_item(record_id,
#     def del_hide_sub_metadata(keys, metadata):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_files_from_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test__export_item():
    assert _export_item() == ""


# def _custom_export_metadata(record_metadata: dict, hide_item: bool = True,
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_files_from_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test__custom_export_metadata():
    assert _custom_export_metadata() == ""


# def get_new_items_by_date(start_date: str, end_date: str, ranking=False) -> dict:
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_files_from_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_new_items_by_date():
    assert get_new_items_by_date() == ""


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
    print(hidden_items)
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
    print(record.files)
    with app.test_request_context():
        app.config.update(WEKO_BUCKET_QUOTA_SIZE=50 * 1024 * 1024 * 1024)
        assert get_files_from_metadata(record) == ""


# def to_files_js(record):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_to_files_js -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_to_files_js(app, db_records):
    depid, recid, parent, doi, record, item = db_records[0]
    record = WekoDeposit(record.model.json, record.model)
    with app.test_request_context():
        assert to_files_js(record) == ""


# def update_sub_items_by_user_role(item_type_id, schema_form):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_update_sub_items_by_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_update_sub_items_by_user_role(db_itemtype):
    item_type = db_itemtype["item_type"]
    assert update_sub_items_by_user_role(item_type.id, item_type.form) == ""


# def remove_excluded_items_in_json_schema(item_id, json_schema):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_remove_excluded_items_in_json_schema -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_remove_excluded_items_in_json_schema(db_itemtype):
    item_type = db_itemtype["item_type"]
    assert remove_excluded_items_in_json_schema(item_type.id, item_type.schema) == ""


# def get_excluded_sub_items(item_type_name):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_excluded_sub_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_excluded_sub_items(db_itemtype):
    item_type_name = db_itemtype["item_type_name"]
    assert get_excluded_sub_items(item_type_name.name) == ""


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
def test_is_need_to_show_agreement_page(db_itemtype):
    item_type_name = db_itemtype["item_type_name"]
    assert is_need_to_show_agreement_page(item_type_name) == ""


# def update_index_tree_for_record(pid_value, index_tree_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_update_index_tree_for_record(db_records):
    assert update_index_tree_for_record(1, 1) == ""


# def validate_user_mail(users, activity_id, request_data, keys, result):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_validate_user_mail():
    assert validate_user_mail()


# def check_approval_email(activity_id, user):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_check_approval_email():
    assert check_approval_email()


# def check_approval_email_in_flow(activity_id, users):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_check_approval_email_in_flow():
    assert check_approval_email_in_flow()


# def update_action_handler(activity_id, action_order, user_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_update_action_handler():
    assert update_action_handler()


# def validate_user_mail_and_index(request_data):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_validate_user_mail_and_index():
    assert validate_user_mail_and_index()


# def recursive_form(schema_form):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_recursive_form():
    assert recursive_form()


# def set_multi_language_name(item, cur_lang):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_set_multi_language_name():
    assert set_multi_language_name()


# def get_data_authors_prefix_settings():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_data_authors_prefix_settings():
    assert get_data_authors_prefix_settings()


# def get_data_authors_affiliation_settings():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_data_authors_affiliation_settings():
    assert get_data_authors_affiliation_settings()


# def hide_meta_data_for_role(record):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_hide_meta_data_for_role():
    assert hide_meta_data_for_role({}) == ""


# def get_ignore_item_from_mapping(_item_type_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_ignore_item_from_mapping():
    assert get_ignore_item_from_mapping(1) == ""


# def get_mapping_name_item_type_by_key(key, item_type_mapping):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_mapping_name_item_type_by_key():
    assert get_mapping_name_item_type_by_key() == ""


# def get_mapping_name_item_type_by_sub_key(key, item_type_mapping):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_mapping_name_item_type_by_sub_key():
    assert get_mapping_name_item_type_by_sub_key() == ""


# def get_hide_list_by_schema_form(item_type_id=None, schemaform=None):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_hide_list_by_schema_form():
    assert get_hide_list_by_schema_form() == ""


# def get_hide_parent_keys(item_type_id=None, meta_list=None):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_hide_parent_keys():
    assert get_hide_parent_keys() == ""


# def get_hide_parent_and_sub_keys(item_type):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_hide_parent_and_sub_keys():
    assert get_hide_parent_and_sub_keys(1) == ""


# def get_item_from_option(_item_type_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_item_from_option():
    assert get_item_from_option(1) == ""


# def get_options_list(item_type_id, json_item=None):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_options_list():
    assert get_options_list(1) == ""


# def get_options_and_order_list(item_type_id, item_type_mapping=None,
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_options_and_order_list():
    assert get_options_and_order_list(1) == ""


# def hide_table_row(table_row, hide_key):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_current_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_hide_table_row():
    assert hide_table_row([], [])


# def is_schema_include_key(schema):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_is_schema_include_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_is_schema_include_key():
    with open("tests/data/itemtype_schema.json", "r") as f:
        schema = json.dumps(json.load(f))

    assert is_schema_include_key(schema) == ""


# def isExistKeyInDict(_key, _dict):
def test_isExistKeyInDict():
    assert isExistKeyInDict("a", {"a": "valueA", "b": "valueB"})


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
    assert make_bibtex_data([1])


# def translate_schema_form(form_element, cur_lang):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_translate_schema_form -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_translate_schema_form(db_itemtype):
    item_type = db_itemtype["item_type"]
    assert translate_schema_form(item_type.form[1], "en")


# def get_ranking(settings):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_ranking -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_ranking(app, db_records):
    with app.test_request_context():
        assert get_ranking({})


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
    assert get_key_title_in_item_type_mapping([]) == None


# def get_title_in_request(request_data, key, key_child):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_title_in_request -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_title_in_request():
    assert get_title_in_request([], "", [])


# def hide_form_items(item_type, schema_form):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_hide_form_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_hide_form_items(db_itemtype):
    item_type = db_itemtype["item_type"]
    res = hide_form_items(item_type, item_type.form)
    print(res)


# def hide_thumbnail(schema_form):
#     def is_thumbnail(items):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_hide_thumbnail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_hide_thumbnail(db_itemtype):
    itemtype = db_itemtype["item_type"]
    assert hide_thumbnail(itemtype.form) == None


# def get_ignore_item(_item_type_id, item_type_mapping=None,
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_ignore_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_ignore_item(db_itemtype):
    itemtype = db_itemtype["item_type"]
    item_type_mapping = db_itemtype["item_type_mapping"]
    itemtype2 = ItemTypes.get_record(1)
    assert get_ignore_item(itemtype.id, item_type_mapping, itemtype2) == []


# def make_stats_csv_with_permission(item_type_id, recids,
#     def _get_root_item_option(item_id, item, sub_form={'title_i18n': {}}):
#         def __init__(self, record_ids, records_metadata):
#             def hide_metadata_email(record):
#         def get_max_ins(self, attr):
#         def get_max_ins_feedback_mail(self):
#         def get_max_items(self, item_attrs):
#         def get_subs_item(self,
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_make_stats_file_with_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_make_stats_file_with_permission(app, db_itemtype):
    item_type_id = 1
    recids = ["1", "2"]
    records_metadata = {
        "1": {
            "_oai": {"id": "oai:weko3.example.org:00000001", "sets": ["1661432090216"]},
            "path": ["1661432090216"],
            "owner": "1",
            "recid": "1",
            "title": [
                "ja_conference paperITEM00000001(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "e6990773-b40b-4527-88d3-e175e01da5cd"},
            "_deposit": {
                "id": "1",
                "pid": {"type": "depid", "value": "1", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000001(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "control_number": "1",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000001(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000001(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            },
            "item_1617258105262": {
                "attribute_name": "Resource Type",
                "attribute_value_mlt": [
                    {
                        "resourceuri": "http://purl.org/coar/resource_type/c_ddb1",
                        "resourcetype": "dataset",
                    }
                ],
            },
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/1/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "9008626e-cb32-48bd-8409-1204f03b8077",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "2": {
            "_oai": {"id": "oai:weko3.example.org:00000002", "sets": ["1661432090216"]},
            "path": ["1661432090216"],
            "owner": "1",
            "recid": "2",
            "title": [
                "ja_conference paperITEM00000002(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "7ad0f6e6-964b-49b2-bdf6-2dbd6a5e0c3b"},
            "_deposit": {
                "id": "2",
                "pid": {"type": "depid", "value": "2", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000002(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000002(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000002(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/2/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "03c96857-3f59-4427-9bab-56a7a073131a",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "3": {
            "_oai": {"id": "oai:weko3.example.org:00000003", "sets": ["1661432090216"]},
            "path": ["1661432090216"],
            "owner": "1",
            "recid": "3",
            "title": [
                "ja_conference paperITEM00000003(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "3e7a5a3a-eced-41a1-a347-ec408cf0b15d"},
            "_deposit": {
                "id": "3",
                "pid": {"type": "depid", "value": "3", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000003(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000003(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000003(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/3/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "d058be3b-e965-4a6c-948d-d567f9406685",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "4": {
            "_oai": {"id": "oai:weko3.example.org:00000004", "sets": ["1661432090216"]},
            "path": ["1661432090216"],
            "owner": "1",
            "recid": "4",
            "title": [
                "ja_conference paperITEM00000004(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "c2d86253-7677-454e-b752-a44d3488d368"},
            "_deposit": {
                "id": "4",
                "pid": {"type": "depid", "value": "4", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000004(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000004(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000004(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/4/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "d49ff7e7-5fc2-4d55-b5f0-2fbf9f2e2ee2",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "5": {
            "_oai": {"id": "oai:weko3.example.org:00000005", "sets": ["1661432090216"]},
            "path": ["1661432090216"],
            "owner": "1",
            "recid": "5",
            "title": [
                "ja_conference paperITEM00000005(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "e8ca5ccc-aff4-4fa9-ba33-e40097a1499a"},
            "_deposit": {
                "id": "5",
                "pid": {"type": "depid", "value": "5", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000005(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000005(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000005(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/5/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "e8479d9f-8a14-44f6-85af-b0cb86b03134",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "6": {
            "_oai": {"id": "oai:weko3.example.org:00000006", "sets": ["1661432090216"]},
            "path": ["1661432090216"],
            "owner": "1",
            "recid": "6",
            "title": [
                "ja_conference paperITEM00000006(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "5c140d58-f7af-4ec5-b16a-275f9e27e2d2"},
            "_deposit": {
                "id": "6",
                "pid": {"type": "depid", "value": "6", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000006(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000006(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000006(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/6/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "6b8efdb6-c507-4a6f-a5bb-280c9681a397",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "7": {
            "_oai": {"id": "oai:weko3.example.org:00000007", "sets": ["1661432090216"]},
            "path": ["1661432090216"],
            "owner": "1",
            "recid": "7",
            "title": [
                "ja_conference paperITEM00000007(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "be89fdb3-ed51-446a-bb33-e1599f7e42fe"},
            "_deposit": {
                "id": "7",
                "pid": {"type": "depid", "value": "7", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000007(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000007(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000007(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/7/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "69a584eb-2737-4728-8cd7-12aae17233a1",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "8": {
            "_oai": {"id": "oai:weko3.example.org:00000008", "sets": ["1661432090216"]},
            "path": ["1661432090216"],
            "owner": "1",
            "recid": "8",
            "title": [
                "ja_conference paperITEM00000008(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "eeaf2c2f-fd5e-4088-829e-b4f04be73e7a"},
            "_deposit": {
                "id": "8",
                "pid": {"type": "depid", "value": "8", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000008(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000008(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000008(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/8/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "ff7a7fee-3e88-458f-b1bc-142c371ab467",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "9": {
            "_oai": {"id": "oai:weko3.example.org:00000009", "sets": ["1661432090216"]},
            "path": ["1661432090216"],
            "owner": "1",
            "recid": "9",
            "title": [
                "ja_conference paperITEM00000009(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "89e7994f-f6b9-48f0-9bf9-70d319ac312f"},
            "_deposit": {
                "id": "9",
                "pid": {"type": "depid", "value": "9", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000009(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/9/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "fcc9b6e7-765c-4545-b974-aad23d1550f4",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "10": {
            "_oai": {"id": "oai:weko3.example.org:00000010", "sets": ["1661432090216"]},
            "path": ["1661432090216"],
            "owner": "1",
            "recid": "10",
            "title": [
                "ja_conference paperITEM00000010(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "2362dfc3-1e10-403d-8f4a-7ee90bad0f9e"},
            "_deposit": {
                "id": "10",
                "pid": {"type": "depid", "value": "10", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000010(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000010(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000010(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/10/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "ea368cb1-c017-4b4a-85ea-ec642ba6df97",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "11": {
            "_oai": {"id": "oai:weko3.example.org:00000011", "sets": ["1661432090216"]},
            "path": ["1661432090216"],
            "owner": "1",
            "recid": "11",
            "title": ["あああ"],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2022-08-26"},
            "_buckets": {"deposit": "a65a042d-477a-483c-a402-b02dcb283cae"},
            "_deposit": {
                "id": "11",
                "pid": {"type": "depid", "value": "11", "revision_id": 0},
                "owner": "1",
                "owners": [1],
                "status": "published",
                "created_by": 1,
                "owners_ext": {
                    "email": "wekosoftware@nii.ac.jp",
                    "username": "",
                    "displayname": "",
                },
            },
            "item_title": "あああ",
            "author_link": [],
            "item_type_id": "1",
            "publish_date": "2022-08-26",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {"subitem_1551255647225": "あああ", "subitem_1551255648112": "ja"}
                ],
            },
            "item_1617258105262": {
                "attribute_name": "Resource Type",
                "attribute_value_mlt": [
                    {
                        "resourceuri": "http://purl.org/coar/resource_type/c_ddb1",
                        "resourcetype": "dataset",
                    }
                ],
            },
            "relation_version_is_last": True,
        },
        "12": {
            "_oai": {"id": "oai:weko3.example.org:00000012", "sets": ["1661517684078"]},
            "path": ["1661517684078"],
            "owner": "1",
            "recid": "12",
            "title": [
                "ja_conference paperITEM00000002(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "dc4b4811-905f-4247-b261-a1562719c78c"},
            "_deposit": {
                "id": "12",
                "pid": {"type": "depid", "value": "12", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000002(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000002(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000002(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/12/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "8e174e8b-5432-41e4-82f2-77b6d2c24acb",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "13": {
            "_oai": {"id": "oai:weko3.example.org:00000013", "sets": ["1661517684078"]},
            "path": ["1661517684078"],
            "owner": "1",
            "recid": "13",
            "title": [
                "ja_conference paperITEM00000001(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "753ff0d7-0659-4460-9b1a-fd1ef38467f2"},
            "_deposit": {
                "id": "13",
                "pid": {"type": "depid", "value": "13", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000001(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000001(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000001(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/13/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "04419b61-9305-4343-848e-328a0b77c3d6",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "14": {
            "_oai": {"id": "oai:weko3.example.org:00000014", "sets": ["1661517684078"]},
            "path": ["1661517684078"],
            "owner": "1",
            "recid": "14",
            "title": [
                "ja_conference paperITEM00000003(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "a45d8374-3e11-44ea-9f30-56827f884d69"},
            "_deposit": {
                "id": "14",
                "pid": {"type": "depid", "value": "14", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000003(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000003(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000003(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/14/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "61dd63d4-b34a-43fe-affd-7dff16f8116c",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "15": {
            "_oai": {"id": "oai:weko3.example.org:00000015", "sets": ["1661517684078"]},
            "path": ["1661517684078"],
            "owner": "1",
            "recid": "15",
            "title": [
                "ja_conference paperITEM00000004(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "b3e11da3-1f8f-4e1f-b422-abb1922eb918"},
            "_deposit": {
                "id": "15",
                "pid": {"type": "depid", "value": "15", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000004(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000004(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000004(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/15/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "830d62a0-1ec0-4ecb-9fa1-1b018646f468",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "16": {
            "_oai": {"id": "oai:weko3.example.org:00000016", "sets": ["1661517684078"]},
            "path": ["1661517684078"],
            "owner": "1",
            "recid": "16",
            "title": [
                "ja_conference paperITEM00000005(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "9230d18b-c254-437c-98ab-376a78541a31"},
            "_deposit": {
                "id": "16",
                "pid": {"type": "depid", "value": "16", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000005(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000005(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000005(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/16/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "4065aeb4-64bb-49ce-b6e4-b0eafde7d370",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "17": {
            "_oai": {"id": "oai:weko3.example.org:00000017", "sets": ["1661517684078"]},
            "path": ["1661517684078"],
            "owner": "1",
            "recid": "17",
            "title": [
                "ja_conference paperITEM00000006(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "4c38ef14-566a-4f63-87fc-936b91e6d9e6"},
            "_deposit": {
                "id": "17",
                "pid": {"type": "depid", "value": "17", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000006(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000006(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000006(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/17/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "2f201374-bbce-41d2-aba3-e4e08d05a941",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "18": {
            "_oai": {"id": "oai:weko3.example.org:00000018", "sets": ["1661517684078"]},
            "path": ["1661517684078"],
            "owner": "1",
            "recid": "18",
            "title": [
                "ja_conference paperITEM00000007(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "fac197c8-1184-48ad-a948-391cd11d10be"},
            "_deposit": {
                "id": "18",
                "pid": {"type": "depid", "value": "18", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000007(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000007(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000007(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/18/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "22f1c324-fa11-4ecd-a089-e43a33c2e399",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "19": {
            "_oai": {"id": "oai:weko3.example.org:00000019", "sets": ["1661517684078"]},
            "path": ["1661517684078"],
            "owner": "1",
            "recid": "19",
            "title": [
                "ja_conference paperITEM00000008(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "97c8bd33-f992-4b31-90ce-b98dd7710e9c"},
            "_deposit": {
                "id": "19",
                "pid": {"type": "depid", "value": "19", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000008(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000008(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000008(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/19/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "85c71b6d-9e81-4343-97ca-3ac92d0c73a0",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "20": {
            "_oai": {"id": "oai:weko3.example.org:00000020", "sets": ["1661517684078"]},
            "path": ["1661517684078"],
            "owner": "1",
            "recid": "20",
            "title": [
                "ja_conference paperITEM00000009(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "a255855d-9e7e-457c-a98c-494bb53dd99e"},
            "_deposit": {
                "id": "20",
                "pid": {"type": "depid", "value": "20", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000009(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/20/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "d05cd37d-1b99-4003-a939-7cd87478d583",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
        "21": {
            "_oai": {"id": "oai:weko3.example.org:00000021", "sets": ["1661517684078"]},
            "path": ["1661517684078"],
            "owner": "1",
            "recid": "21",
            "title": [
                "ja_conference paperITEM00000010(public_open_access_open_access_simple)"
            ],
            "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
            "_buckets": {"deposit": "aa1bf766-93a4-4eb2-b314-51aff4c231db"},
            "_deposit": {
                "id": "21",
                "pid": {"type": "depid", "value": "21", "revision_id": 0},
                "owners": [1],
                "status": "published",
            },
            "item_title": "ja_conference paperITEM00000010(public_open_access_open_access_simple)",
            "author_link": ["4"],
            "item_type_id": "1",
            "publish_date": "2021-08-06",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255647225": "ja_conference paperITEM00000010(public_open_access_open_access_simple)",
                        "subitem_1551255648112": "ja",
                    },
                    {
                        "subitem_1551255647225": "en_conference paperITEM00000010(public_open_access_simple)",
                        "subitem_1551255648112": "en",
                    },
                ],
            },
            "item_1617186385884": {
                "attribute_name": "Alternative Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "en",
                    },
                    {
                        "subitem_1551255720400": "Alternative Title",
                        "subitem_1551255721061": "ja",
                    },
                ],
            },
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "creatorAffiliations": [
                            {
                                "affiliationNames": [
                                    {
                                        "affiliationName": "University",
                                        "affiliationNameLang": "en",
                                    }
                                ],
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000000121691048",
                                        "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                        "affiliationNameIdentifierScheme": "ISNI",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                        "creatorNames": [
                            {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                            {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                            {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                        ],
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "zzzzzzz",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                    },
                ],
            },
            "item_1617186476635": {
                "attribute_name": "Access Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299639480": "open access",
                        "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                    }
                ],
            },
            "item_1617186499011": {
                "attribute_name": "Rights",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650717957": "ja",
                        "subitem_1522650727486": "http://localhost",
                        "subitem_1522651041219": "Rights Information",
                    }
                ],
            },
            "item_1617186609386": {
                "attribute_name": "Subject",
                "attribute_value_mlt": [
                    {
                        "subitem_1522299896455": "ja",
                        "subitem_1522300014469": "Other",
                        "subitem_1522300048512": "http://localhost/",
                        "subitem_1523261968819": "Sibject1",
                    }
                ],
            },
            "item_1617186626617": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_description": "Description\nDescription<br/>Description",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "en",
                    },
                    {
                        "subitem_description": "概要\n概要\n概要\n概要",
                        "subitem_description_type": "Abstract",
                        "subitem_description_language": "ja",
                    },
                ],
            },
            "item_1617186643794": {
                "attribute_name": "Publisher",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300295150": "en",
                        "subitem_1522300316516": "Publisher",
                    }
                ],
            },
            "item_1617186660861": {
                "attribute_name": "Date",
                "attribute_value_mlt": [
                    {
                        "subitem_1522300695726": "Available",
                        "subitem_1522300722591": "2021-06-30",
                    }
                ],
            },
            "item_1617186702042": {
                "attribute_name": "Language",
                "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
            },
            "item_1617186783814": {
                "attribute_name": "Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_uri": "http://localhost",
                        "subitem_identifier_type": "URI",
                    }
                ],
            },
            "item_1617186859717": {
                "attribute_name": "Temporal",
                "attribute_value_mlt": [
                    {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
                ],
            },
            "item_1617186882738": {
                "attribute_name": "Geo Location",
                "attribute_value_mlt": [
                    {
                        "subitem_geolocation_place": [
                            {"subitem_geolocation_place_text": "Japan"}
                        ]
                    }
                ],
            },
            "item_1617186901218": {
                "attribute_name": "Funding Reference",
                "attribute_value_mlt": [
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
            },
            "item_1617186920753": {
                "attribute_name": "Source Identifier",
                "attribute_value_mlt": [
                    {
                        "subitem_1522646500366": "ISSN",
                        "subitem_1522646572813": "xxxx-xxxx-xxxx",
                    }
                ],
            },
            "item_1617186941041": {
                "attribute_name": "Source Title",
                "attribute_value_mlt": [
                    {
                        "subitem_1522650068558": "en",
                        "subitem_1522650091861": "Source Title",
                    }
                ],
            },
            "item_1617186959569": {
                "attribute_name": "Volume Number",
                "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
            },
            "item_1617186981471": {
                "attribute_name": "Issue Number",
                "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
            },
            "item_1617186994930": {
                "attribute_name": "Number of Pages",
                "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
            },
            "item_1617187024783": {
                "attribute_name": "Page Start",
                "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
            },
            "item_1617187045071": {
                "attribute_name": "Page End",
                "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
            },
            "item_1617187112279": {
                "attribute_name": "Degree Name",
                "attribute_value_mlt": [
                    {
                        "subitem_1551256126428": "Degree Name",
                        "subitem_1551256129013": "en",
                    }
                ],
            },
            "item_1617187136212": {
                "attribute_name": "Date Granted",
                "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
            },
            "item_1617187187528": {
                "attribute_name": "Conference",
                "attribute_value_mlt": [
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
            "item_1617265215918": {
                "attribute_name": "Version Type",
                "attribute_value_mlt": [
                    {
                        "subitem_1522305645492": "AO",
                        "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                    }
                ],
            },
            "item_1617349709064": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "givenNames": [
                            {"givenName": "太郎", "givenNameLang": "ja"},
                            {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                            {"givenName": "Taro", "givenNameLang": "en"},
                        ],
                        "familyNames": [
                            {"familyName": "情報", "familyNameLang": "ja"},
                            {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                            {"familyName": "Joho", "familyNameLang": "en"},
                        ],
                        "contributorType": "ContactPerson",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://ci.nii.ac.jp/",
                                "nameIdentifierScheme": "CiNii",
                            },
                            {
                                "nameIdentifier": "xxxxxxx",
                                "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                                "nameIdentifierScheme": "KAKEN2",
                            },
                        ],
                        "contributorMails": [
                            {"contributorMail": "wekosoftware@nii.ac.jp"}
                        ],
                        "contributorNames": [
                            {"lang": "ja", "contributorName": "情報, 太郎"},
                            {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                            {"lang": "en", "contributorName": "Joho, Taro"},
                        ],
                    }
                ],
            },
            "item_1617349808926": {
                "attribute_name": "Version",
                "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
            },
            "item_1617351524846": {
                "attribute_name": "APC",
                "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
            },
            "item_1617353299429": {
                "attribute_name": "Relation",
                "attribute_value_mlt": [
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
            },
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "url": {
                            "url": "https://weko3.example.org/record/21/files/1KB.pdf"
                        },
                        "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                        "format": "text/plain",
                        "filename": "1KB.pdf",
                        "filesize": [{"value": "1 KB"}],
                        "mimetype": "application/pdf",
                        "accessrole": "open_access",
                        "version_id": "64452e44-1e70-4fa9-bd9c-492ae8a9e570",
                        "displaytype": "simple",
                    }
                ],
            },
            "item_1617610673286": {
                "attribute_name": "Rights Holder",
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "xxxxxx",
                                "nameIdentifierURI": "https://orcid.org/",
                                "nameIdentifierScheme": "ORCID",
                            }
                        ],
                        "rightHolderNames": [
                            {
                                "rightHolderName": "Right Holder Name",
                                "rightHolderLanguage": "ja",
                            }
                        ],
                    }
                ],
            },
            "item_1617620223087": {
                "attribute_name": "Heading",
                "attribute_value_mlt": [
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
            },
            "item_1617944105607": {
                "attribute_name": "Degree Grantor",
                "attribute_value_mlt": [
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
            },
            "relation_version_is_last": True,
        },
    }
    permissions = dict(
        permission_show_hide=lambda a: True,
        check_created_id=lambda a: True,
        hide_meta_data_for_role=lambda a: True,
        current_language=lambda: True,
    )

    with app.test_request_context():
        assert (
            make_stats_file_with_permission(
                item_type_id, recids, records_metadata, permissions
            )
            == ""
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