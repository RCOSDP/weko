from weko_items_ui.utils import (
    sanitize_input_data,
    __sanitize_string,
    is_schema_include_key,
    get_list_username,
    get_list_email,
    get_user_info_by_username,
    validate_user,
    get_user_info_by_email,
    get_user_information,
    get_user_permission,
    get_current_user,
    find_hidden_items,
    parse_ranking_results,
    parse_ranking_new_items,
    parse_ranking_record,
    validate_form_input_data,
    make_stats_csv,
    save_title,
    to_files_js,
    get_files_from_metadata
)
from invenio_accounts.testutils import login_user_via_session
import pytest
from mock import patch
from unittest.mock import MagicMock
from jsonschema import SchemaError, ValidationError
import json
from weko_workflow.api import WorkActivity
from weko_deposit.api import WekoDeposit, WekoRecord

# def get_list_username():
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
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_find_hidden_items -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_find_hidden_items(db_records):
    assert find_hidden_items(range(1, 2), range(1)) == ""


# def parse_ranking_results(index_info,
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_parse_ranking_results -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_parse_ranking_results(app, db_register, db_records):
    index_info = {
        "1660555749031": {
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
    display_rank = 10
    list_name = "all"
    title_key = "record_name"
    count_key = None
    pid_key = "pid_value"
    search_key = None
    date_key = "create_date"
    ranking_list = [
        {"date": "2022-08-20", "title": "title2", "url": "../records/3"},
        {"date": "2022-08-18", "title": "title", "url": "../records/1"},
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
def test_validate_form_input_data(app, db_register):
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
# def update_json_schema_with_required_items(node: dict, json_data: dict):
#     :param node: json schema return from def parse_node_str_to_json_schema
# def update_json_schema_by_activity_id(json_data, activity_id):
# def update_schema_form_by_activity_id(schema_form, activity_id):
# def recursive_prepare_either_required_list(schema_form, either_required_list):
# def recursive_update_schema_form_with_condition(
#     def prepare_either_condition_required(group_idx, key):
#     def set_on_change(elem):
# def package_export_file(item_type_data):
# def make_stats_csv(item_type_id, recids, list_item_role):
#         def __init__(self, record_ids):
#         def get_max_ins(self, attr):
#         def get_max_ins_feedback_mail(self):
#         def get_max_items(self, item_attrs):
#         def get_subs_item(self,
def test_make_stats_csv(app, db_register, db_records):
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
                "name":"Creative Commons CC0 1.0 Universal Public Domain Designation",
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
                "name":
                    "Creative Commons Attribution-NoDerivs 3.0 Unported (CC BY-ND 3.0)"
                ,
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
                "name": 
                    "Creative Commons Attribution-NonCommercial 3.0 Unported"
                    " (CC BY-NC 3.0)"
                ,
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
                "name": 
                    "Creative Commons Attribution-NonCommercial-ShareAlike 3.0 "
                    "Unported (CC BY-NC-SA 3.0)"
                ,
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
                "name":
                    "Creative Commons Attribution-NonCommercial-NoDerivs "
                    "3.0 Unported (CC BY-NC-ND 3.0)"
                ,
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
                "name": 
                    "Creative Commons Attribution-ShareAlike 4.0 International "
                    "(CC BY-SA 4.0)"
                ,
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
                "name": 
                    "Creative Commons Attribution-NoDerivatives 4.0 International "
                    "(CC BY-ND 4.0)"
                ,
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
                "name": 
                    "Creative Commons Attribution-NonCommercial 4.0 International"
                    " (CC BY-NC 4.0)"
                ,
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
                "name": 
                    "Creative Commons Attribution-NonCommercial-ShareAlike 4.0"
                    " International (CC BY-NC-SA 4.0)"
                ,
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
                "name": 
                    "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 "
                    "International (CC BY-NC-ND 4.0)"
                ,
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
        assert make_stats_csv(item_type_id, [1], list_item_role) == ([['#.id', '.uri', '.metadata.path[0]', '.pos_index[0]', '.publish_status', '.feedback_mail[0]', '.cnri', '.doi_ra', '.doi', '.edit_mode', '.metadata.pubdate', '.metadata.item_1617186331708[0].subitem_1551255647225', '.metadata.item_1617186331708[0].subitem_1551255648112', '.metadata.item_1617186385884[0].subitem_1551255720400', '.metadata.item_1617186385884[0].subitem_1551255721061', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifier', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierScheme', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNameIdentifiers[0].affiliationNameIdentifierURI', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNames[0].affiliationName', '.metadata.item_1617186419668[0].creatorAffiliations[0].affiliationNames[0].affiliationNameLang', '.metadata.item_1617186419668[0].creatorAlternatives[0].creatorAlternative', '.metadata.item_1617186419668[0].creatorAlternatives[0].creatorAlternativeLang', '.metadata.item_1617186419668[0].creatorMails[0].creatorMail', '.metadata.item_1617186419668[0].creatorNames[0].creatorName', '.metadata.item_1617186419668[0].creatorNames[0].creatorNameLang', '.metadata.item_1617186419668[0].familyNames[0].familyName', '.metadata.item_1617186419668[0].familyNames[0].familyNameLang', '.metadata.item_1617186419668[0].givenNames[0].givenName', '.metadata.item_1617186419668[0].givenNames[0].givenNameLang', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617186419668[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationNameIdentifier', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationScheme', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNameIdentifiers[0].contributorAffiliationURI', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationName', '.metadata.item_1617349709064[0].contributorAffiliations[0].contributorAffiliationNames[0].contributorAffiliationNameLang', '.metadata.item_1617349709064[0].contributorAlternatives[0].contributorAlternative', '.metadata.item_1617349709064[0].contributorAlternatives[0].contributorAlternativeLang', '.metadata.item_1617349709064[0].contributorMails[0].contributorMail', '.metadata.item_1617349709064[0].contributorNames[0].contributorName', '.metadata.item_1617349709064[0].contributorNames[0].lang', '.metadata.item_1617349709064[0].contributorType', '.metadata.item_1617349709064[0].familyNames[0].familyName', '.metadata.item_1617349709064[0].familyNames[0].familyNameLang', '.metadata.item_1617349709064[0].givenNames[0].givenName', '.metadata.item_1617349709064[0].givenNames[0].givenNameLang', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617349709064[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617186476635.subitem_1522299639480', '.metadata.item_1617186476635.subitem_1600958577026', '.metadata.item_1617351524846.subitem_1523260933860', '.metadata.item_1617186499011[0].subitem_1522650717957', '.metadata.item_1617186499011[0].subitem_1522650727486', '.metadata.item_1617186499011[0].subitem_1522651041219', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifier', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifierScheme', '.metadata.item_1617610673286[0].nameIdentifiers[0].nameIdentifierURI', '.metadata.item_1617610673286[0].rightHolderNames[0].rightHolderLanguage', '.metadata.item_1617610673286[0].rightHolderNames[0].rightHolderName', '.metadata.item_1617186609386[0].subitem_1522299896455', '.metadata.item_1617186609386[0].subitem_1522300014469', '.metadata.item_1617186609386[0].subitem_1522300048512', '.metadata.item_1617186609386[0].subitem_1523261968819', '.metadata.item_1617186626617[0].subitem_description', '.metadata.item_1617186626617[0].subitem_description_language', '.metadata.item_1617186626617[0].subitem_description_type', '.metadata.item_1617186643794[0].subitem_1522300295150', '.metadata.item_1617186643794[0].subitem_1522300316516', '.metadata.item_1617186660861[0].subitem_1522300695726', '.metadata.item_1617186660861[0].subitem_1522300722591', '.metadata.item_1617186702042[0].subitem_1551255818386', '.metadata.item_1617258105262.resourcetype', '.metadata.item_1617258105262.resourceuri', '.metadata.item_1617349808926.subitem_1523263171732', '.metadata.item_1617265215918.subitem_1522305645492', '.metadata.item_1617265215918.subitem_1600292170262', '.metadata.item_1617186783814[0].subitem_identifier_type', '.metadata.item_1617186783814[0].subitem_identifier_uri', '.metadata.item_1617186819068.subitem_identifier_reg_text', '.metadata.item_1617186819068.subitem_identifier_reg_type', '.metadata.item_1617353299429[0].subitem_1522306207484', '.metadata.item_1617353299429[0].subitem_1522306287251.subitem_1522306382014', '.metadata.item_1617353299429[0].subitem_1522306287251.subitem_1522306436033', '.metadata.item_1617353299429[0].subitem_1523320863692[0].subitem_1523320867455', '.metadata.item_1617353299429[0].subitem_1523320863692[0].subitem_1523320909613', '.metadata.item_1617186859717[0].subitem_1522658018441', '.metadata.item_1617186859717[0].subitem_1522658031721', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_east_longitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_north_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_south_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_box.subitem_west_longitude', '.metadata.item_1617186882738[0].subitem_geolocation_place[0].subitem_geolocation_place_text', '.metadata.item_1617186882738[0].subitem_geolocation_point.subitem_point_latitude', '.metadata.item_1617186882738[0].subitem_geolocation_point.subitem_point_longitude', '.metadata.item_1617186901218[0].subitem_1522399143519.subitem_1522399281603', '.metadata.item_1617186901218[0].subitem_1522399143519.subitem_1522399333375', '.metadata.item_1617186901218[0].subitem_1522399412622[0].subitem_1522399416691', '.metadata.item_1617186901218[0].subitem_1522399412622[0].subitem_1522737543681', '.metadata.item_1617186901218[0].subitem_1522399571623.subitem_1522399585738', '.metadata.item_1617186901218[0].subitem_1522399571623.subitem_1522399628911', '.metadata.item_1617186901218[0].subitem_1522399651758[0].subitem_1522721910626', '.metadata.item_1617186901218[0].subitem_1522399651758[0].subitem_1522721929892', '.metadata.item_1617186920753[0].subitem_1522646500366', '.metadata.item_1617186920753[0].subitem_1522646572813', '.metadata.item_1617186941041[0].subitem_1522650068558', '.metadata.item_1617186941041[0].subitem_1522650091861', '.metadata.item_1617186959569.subitem_1551256328147', '.metadata.item_1617186981471.subitem_1551256294723', '.metadata.item_1617186994930.subitem_1551256248092', '.metadata.item_1617187024783.subitem_1551256198917', '.metadata.item_1617187045071.subitem_1551256185532', '.metadata.item_1617187056579.bibliographicIssueDates.bibliographicIssueDate', '.metadata.item_1617187056579.bibliographicIssueDates.bibliographicIssueDateType', '.metadata.item_1617187056579.bibliographicIssueNumber', '.metadata.item_1617187056579.bibliographicNumberOfPages', '.metadata.item_1617187056579.bibliographicPageEnd', '.metadata.item_1617187056579.bibliographicPageStart', '.metadata.item_1617187056579.bibliographicVolumeNumber', '.metadata.item_1617187056579.bibliographic_titles[0].bibliographic_title', '.metadata.item_1617187056579.bibliographic_titles[0].bibliographic_titleLang', '.metadata.item_1617187087799.subitem_1551256171004', '.metadata.item_1617187112279[0].subitem_1551256126428', '.metadata.item_1617187112279[0].subitem_1551256129013', '.metadata.item_1617187136212.subitem_1551256096004', '.metadata.item_1617944105607[0].subitem_1551256015892[0].subitem_1551256027296', '.metadata.item_1617944105607[0].subitem_1551256015892[0].subitem_1551256029891', '.metadata.item_1617944105607[0].subitem_1551256037922[0].subitem_1551256042287', '.metadata.item_1617944105607[0].subitem_1551256037922[0].subitem_1551256047619', '.metadata.item_1617187187528[0].subitem_1599711633003[0].subitem_1599711636923', '.metadata.item_1617187187528[0].subitem_1599711633003[0].subitem_1599711645590', '.metadata.item_1617187187528[0].subitem_1599711655652', '.metadata.item_1617187187528[0].subitem_1599711660052[0].subitem_1599711680082', '.metadata.item_1617187187528[0].subitem_1599711660052[0].subitem_1599711686511', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711704251', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711712451', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711727603', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711731891', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711735410', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711739022', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711743722', '.metadata.item_1617187187528[0].subitem_1599711699392.subitem_1599711745532', '.metadata.item_1617187187528[0].subitem_1599711758470[0].subitem_1599711769260', '.metadata.item_1617187187528[0].subitem_1599711758470[0].subitem_1599711775943', '.metadata.item_1617187187528[0].subitem_1599711788485[0].subitem_1599711798761', '.metadata.item_1617187187528[0].subitem_1599711788485[0].subitem_1599711803382', '.metadata.item_1617187187528[0].subitem_1599711813532', '.file_path[0]', '.metadata.item_1617605131499[0].accessrole', '.metadata.item_1617605131499[0].date[0].dateType', '.metadata.item_1617605131499[0].date[0].dateValue', '.metadata.item_1617605131499[0].displaytype', '.metadata.item_1617605131499[0].fileDate[0].fileDateType', '.metadata.item_1617605131499[0].fileDate[0].fileDateValue', '.metadata.item_1617605131499[0].filename', '.metadata.item_1617605131499[0].filesize[0].value', '.metadata.item_1617605131499[0].format', '.metadata.item_1617605131499[0].groups', '.metadata.item_1617605131499[0].licensefree', '.metadata.item_1617605131499[0].licensetype', '.metadata.item_1617605131499[0].url.label', '.metadata.item_1617605131499[0].url.objectType', '.metadata.item_1617605131499[0].url.url', '.metadata.item_1617605131499[0].version', '.metadata.item_1617620223087[0].subitem_1565671149650', '.metadata.item_1617620223087[0].subitem_1565671169640', '.metadata.item_1617620223087[0].subitem_1565671178623'], ['#ID', 'URI', '.IndexID[0]', '.POS_INDEX[0]', '.PUBLISH_STATUS', '.FEEDBACK_MAIL[0]', '.CNRI', '.DOI_RA', '.DOI', 'Keep/Upgrade Version', 'PubDate', 'Title[0].Title', 'Title[0].Language', 'Alternative Title[0].Alternative Title', 'Alternative Title[0].Language', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Creator[0].作成者所属[0].所属機関識別子[0].所属機関識別子URI', 'Creator[0].作成者所属[0].所属機関名[0].所属機関名', 'Creator[0].作成者所属[0].所属機関名[0].言語', 'Creator[0].作成者別名[0].別名', 'Creator[0].作成者別名[0].言語', 'Creator[0].作成者メールアドレス[0].メールアドレス', 'Creator[0].作成者姓名[0].姓名', 'Creator[0].作成者姓名[0].言語', 'Creator[0].作成者姓[0].姓', 'Creator[0].作成者姓[0].言語', 'Creator[0].作成者名[0].名', 'Creator[0].作成者名[0].言語', 'Creator[0].作成者識別子[0].作成者識別子', 'Creator[0].作成者識別子[0].作成者識別子Scheme', 'Creator[0].作成者識別子[0].作成者識別子URI', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子スキーマ', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関識別子URI', 'Contributor[0].寄与者所属[0].所属機関識別子[0].所属機関名', 'Contributor[0].寄与者所属[0].所属機関識別子[0].言語', 'Contributor[0].寄与者別名[0].別名', 'Contributor[0].寄与者別名[0].言語', 'Contributor[0].寄与者メールアドレス[0].メールアドレス', 'Contributor[0].寄与者姓名[0].姓名', 'Contributor[0].寄与者姓名[0].言語', 'Contributor[0].寄与者タイプ', 'Contributor[0].寄与者姓[0].姓', 'Contributor[0].寄与者姓[0].言語', 'Contributor[0].寄与者名[0].名', 'Contributor[0].寄与者名[0].言語', 'Contributor[0].寄与者識別子[0].寄与者識別子', 'Contributor[0].寄与者識別子[0].寄与者識別子Scheme', 'Contributor[0].寄与者識別子[0].寄与者識別子URI', 'Access Rights.アクセス権', 'Access Rights.アクセス権URI', 'APC.APC', 'Rights[0].言語', 'Rights[0].権利情報Resource', 'Rights[0].権利情報', 'Rights Holder[0].権利者識別子[0].権利者識別子', 'Rights Holder[0].権利者識別子[0].権利者識別子Scheme', 'Rights Holder[0].権利者識別子[0].権利者識別子URI', 'Rights Holder[0].権利者名[0].言語', 'Rights Holder[0].権利者名[0].権利者名', 'Subject[0].言語', 'Subject[0].主題Scheme', 'Subject[0].主題URI', 'Subject[0].主題', 'Description[0].内容記述', 'Description[0].言語', 'Description[0].内容記述タイプ', 'Publisher[0].言語', 'Publisher[0].出版者', 'Date[0].日付タイプ', 'Date[0].日付', 'Language[0].Language', 'Resource Type.資源タイプ', 'Resource Type.資源タイプ識別子', 'Version.バージョン情報', 'Version Type.出版タイプ', 'Version Type.出版タイプResource', 'Identifier[0].識別子タイプ', 'Identifier[0].識別子', 'Identifier Registration.ID登録', 'Identifier Registration.ID登録タイプ', 'Relation[0].関連タイプ', 'Relation[0].関連識別子.識別子タイプ', 'Relation[0].関連識別子.関連識別子', 'Relation[0].関連名称[0].言語', 'Relation[0].関連名称[0].関連名称', 'Temporal[0].言語', 'Temporal[0].時間的範囲', 'Geo Location[0].位置情報（空間）.東部経度', 'Geo Location[0].位置情報（空間）.北部緯度', 'Geo Location[0].位置情報（空間）.南部緯度', 'Geo Location[0].位置情報（空間）.西部経度', 'Geo Location[0].位置情報（自由記述）[0].位置情報（自由記述）', 'Geo Location[0].位置情報（点）.緯度', 'Geo Location[0].位置情報（点）.経度', 'Funding Reference[0].助成機関識別子.助成機関識別子タイプ', 'Funding Reference[0].助成機関識別子.助成機関識別子', 'Funding Reference[0].助成機関名[0].言語', 'Funding Reference[0].助成機関名[0].助成機関名', 'Funding Reference[0].研究課題番号.研究課題URI', 'Funding Reference[0].研究課題番号.研究課題番号', 'Funding Reference[0].研究課題名[0].言語', 'Funding Reference[0].研究課題名[0].研究課題名', 'Source Identifier[0].収録物識別子タイプ', 'Source Identifier[0].収録物識別子', 'Source Title[0].言語', 'Source Title[0].収録物名', 'Volume Number.Volume Number', 'Issue Number.Issue Number', 'Number of Pages.Number of Pages', 'Page Start.Page Start', 'Page End.Page End', 'Bibliographic Information.発行日.日付', 'Bibliographic Information.発行日.日付タイプ', 'Bibliographic Information.号', 'Bibliographic Information.ページ数', 'Bibliographic Information.終了ページ', 'Bibliographic Information.開始ページ', 'Bibliographic Information.巻', 'Bibliographic Information.雑誌名[0].タイトル', 'Bibliographic Information.雑誌名[0].言語', 'Dissertation Number.Dissertation Number', 'Degree Name[0].Degree Name', 'Degree Name[0].Language', 'Date Granted.Date Granted', 'Degree Grantor[0].Degree Grantor Name Identifier[0].Degree Grantor Name Identifier', 'Degree Grantor[0].Degree Grantor Name Identifier[0].Degree Grantor Name Identifier Scheme', 'Degree Grantor[0].Degree Grantor Name[0].Degree Grantor Name', 'Degree Grantor[0].Degree Grantor Name[0].Language', 'Conference[0].Conference Name[0].Conference Name', 'Conference[0].Conference Name[0].Language', 'Conference[0].Conference Sequence', 'Conference[0].Conference Sponsor[0].Conference Sponsor', 'Conference[0].Conference Sponsor[0].Language', 'Conference[0].Conference Date.Conference Date', 'Conference[0].Conference Date.Start Day', 'Conference[0].Conference Date.Start Month', 'Conference[0].Conference Date.Start Year', 'Conference[0].Conference Date.End Day', 'Conference[0].Conference Date.End Month', 'Conference[0].Conference Date.End Year', 'Conference[0].Conference Date.Language', 'Conference[0].Conference Venue[0].Conference Venue', 'Conference[0].Conference Venue[0].Language', 'Conference[0].Conference Place[0].Conference Place', 'Conference[0].Conference Place[0].Language', 'Conference[0].Conference Country', '.ファイルパス[0]', 'File[0].アクセス', 'File[0].オープンアクセスの日付[0].日付タイプ', 'File[0].オープンアクセスの日付[0].日付', 'File[0].表示形式', 'File[0].日付[0].日付タイプ', 'File[0].日付[0].日付', 'File[0].表示名', 'File[0].サイズ[0].サイズ', 'File[0].フォーマット', 'File[0].グループ', 'File[0].自由ライセンス', 'File[0].ライセンス', 'File[0].本文URL.ラベル', 'File[0].本文URL.オブジェクトタイプ', 'File[0].本文URL.本文URL', 'File[0].バージョン情報', 'Heading[0].Language', 'Heading[0].Banner Headline', 'Heading[0].Subheading'], ['#', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'System', '', '', 'System', '', '', 'System', 'System', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''], ['#', '', 'Allow Multiple', 'Allow Multiple', 'Required', 'Allow Multiple', '', '', '', 'Required', 'Required', 'Required, Allow Multiple', 'Required, Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Required', 'Required', '', '', '', 'Allow Multiple', 'Allow Multiple', '', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Allow Multiple', 'Allow Multiple', '', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple', 'Allow Multiple']], {1: ['1', '', 'public', '', '', '', '', 'Keep', '2022-08-20', 'title', 'ja', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'conference paper', 'http://purl.org/coar/resource_type/c_5794', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']})


# def get_list_file_by_record_id(recid):
# def write_bibtex_files(item_types_data, export_path):
# def write_csv_files(item_types_data, export_path, list_item_role):
# def check_item_type_name(name):
# def export_items(post_data):
# def _get_max_export_items():
# def _export_item(record_id,
#     def del_hide_sub_metadata(keys, metadata):
# def _custom_export_metadata(record_metadata: dict, hide_item: bool = True,
# def get_new_items_by_date(start_date: str, end_date: str, ranking=False) -> dict:
# def update_schema_remove_hidden_item(schema, render, items_name):
# def get_files_from_metadata(record):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_get_files_from_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_files_from_metadata(app,db_records):
    
    depid,rec,item = db_records[0]
    print(rec.files)
    with app.test_request_context():
        app.config.update(WEKO_BUCKET_QUOTA_SIZE = 50 * 1024 * 1024 * 1024  )
        assert get_files_from_metadata(rec)==""


# def to_files_js(record):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_to_files_js -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp

def test_to_files_js(app,db_records):    
    depid, record, item = db_records[0]
    record = WekoDeposit(record.model.json,record.model)
    with app.test_request_context():
        assert to_files_js(record)==""

# def update_sub_items_by_user_role(item_type_id, schema_form):
# def remove_excluded_items_in_json_schema(item_id, json_schema):
# def get_excluded_sub_items(item_type_name):
# def get_current_user_role():
# def is_need_to_show_agreement_page(item_type_name):
# def update_index_tree_for_record(pid_value, index_tree_id):
# def validate_user_mail(users, activity_id, request_data, keys, result):
# def check_approval_email(activity_id, user):
# def check_approval_email_in_flow(activity_id, users):
# def update_action_handler(activity_id, action_order, user_id):
# def validate_user_mail_and_index(request_data):
# def recursive_form(schema_form):
# def set_multi_language_name(item, cur_lang):
# def get_data_authors_prefix_settings():
# def get_data_authors_affiliation_settings():
# def hide_meta_data_for_role(record):
# def get_ignore_item_from_mapping(_item_type_id):
# def get_mapping_name_item_type_by_key(key, item_type_mapping):
# def get_mapping_name_item_type_by_sub_key(key, item_type_mapping):
# def get_hide_list_by_schema_form(item_type_id=None, schemaform=None):
# def get_hide_parent_keys(item_type_id=None, meta_list=None):
# def get_hide_parent_and_sub_keys(item_type):
# def get_item_from_option(_item_type_id):
# def get_options_list(item_type_id, json_item=None):
# def get_options_and_order_list(item_type_id, item_type_mapping=None,
# def hide_table_row_for_csv(table_row, hide_key):
# def is_schema_include_key(schema):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_is_schema_include_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_is_schema_include_key():
    with open("tests/data/itemtype_schema.json", "r") as f:
        schema = json.dumps(json.load(f))

    assert is_schema_include_key(schema) == ""


# def isExistKeyInDict(_key, _dict):
# def set_validation_message(item, cur_lang):
# def translate_validation_message(item_property, cur_lang):
# def get_workflow_by_item_type_id(item_type_name_id, item_type_id):
# def validate_bibtex(record_ids):
# def make_bibtex_data(record_ids):
# def translate_schema_form(form_element, cur_lang):
# def get_ranking(settings):
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
#.tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test_save_title -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_save_title(app,db_register,db_register2):
    request_data ={'metainfo': {'$schema': '1', 'item_1617186331708': [{'subitem_1551255647225': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000001(public_open_access_simple)', 'subitem_1551255648112': 'en'}], 'item_1617186385884': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}], 'item_1617186419668': [{'creatorAffiliations': [{'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048'}], 'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}]}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '4', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}], 'creatorAlternatives': [{}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}], 'creatorAlternatives': [{}], 'creatorAffiliations': [{'affiliationNameIdentifiers': [{}], 'affiliationNames': [{}]}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}], 'creatorAlternatives': [{}], 'creatorAffiliations': [{'affiliationNameIdentifiers': [{}], 'affiliationNames': [{}]}]}], 'item_1617186476635': {'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}, 'item_1617186499011': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}], 'item_1617186609386': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}], 'item_1617186626617': [{'subitem_description': 'Description\nDescription<br/>Description', 'subitem_description_language': 'en', 'subitem_description_type': 'Abstract'}, {'subitem_description': '概要\n概要\n概要\n概要', 'subitem_description_language': 'ja', 'subitem_description_type': 'Abstract'}], 'item_1617186643794': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}], 'item_1617186660861': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}], 'item_1617186702042': [{'subitem_1551255818386': 'jpn'}], 'item_1617186783814': [{'subitem_identifier_type': 'URI', 'subitem_identifier_uri': 'http://localhost'}], 'item_1617186859717': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}], 'item_1617186882738': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}], 'item_1617186901218': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}], 'item_1617186920753': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}], 'item_1617186941041': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}], 'item_1617186959569': {'subitem_1551256328147': '1'}, 'item_1617186981471': {'subitem_1551256294723': '111'}, 'item_1617186994930': {'subitem_1551256248092': '12'}, 'item_1617187024783': {'subitem_1551256198917': '1'}, 'item_1617187045071': {'subitem_1551256185532': '3'}, 'item_1617187112279': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}], 'item_1617187136212': {'subitem_1551256096004': '2021-06-30'}, 'item_1617187187528': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_1617265215918': {'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}, 'item_1617349709064': [{'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'contributorName': '情報, 太郎', 'lang': 'ja'}, {'contributorName': 'ジョウホウ, タロウ', 'lang': 'ja-Kana'}, {'contributorName': 'Joho, Taro', 'lang': 'en'}], 'contributorType': 'ContactPerson', 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}], 'contributorAlternatives': [{}], 'contributorAffiliations': [{'contributorAffiliationNameIdentifiers': [{}], 'contributorAffiliationNames': [{}]}]}], 'item_1617349808926': {'subitem_1523263171732': 'Version'}, 'item_1617351524846': {'subitem_1523260933860': 'Unknown'}, 'item_1617353299429': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}], 'item_1617605131499': [{'accessrole': 'open_access', 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'displaytype': 'simple', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'format': 'text/plain', 'mimetype': 'application/pdf', 'url': {'url': 'https://weko3.example.org/record/1/files/1KB.pdf'}, 'version_id': '427e7fc6-3586-4987-ab63-76a3416ee3db', 'fileDate': [{}], 'provide': [{}]}], 'item_1617610673286': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}], 'rightHolderNames': [{'rightHolderLanguage': 'ja', 'rightHolderName': 'Right Holder Name'}]}], 'item_1617620223087': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}], 'item_1617944105607': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}], 'owner': '1', 'pubdate': '2021-08-06', 'title': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'weko_shared_id': -1, 'item_1617187056579': {'bibliographic_titles': [{}]}, 'shared_user_id': -1}, 'files': [{'checksum': 'sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef', 'completed': True, 'displaytype': 'simple', 'filename': '1KB.pdf', 'is_show': False, 'is_thumbnail': False, 'key': '1KB.pdf', 'licensetype': None, 'links': {'self': '/api/files/bbd13a3e-d6c0-41c1-8f92-abb50ba3e85b/1KB.pdf?versionId=427e7fc6-3586-4987-ab63-76a3416ee3db'}, 'mimetype': 'application/pdf', 'progress': 100, 'size': 1024, 'version_id': '427e7fc6-3586-4987-ab63-76a3416ee3db'}], 'endpoints': {'initialization': '/api/deposits/redirect/1.0'}}
    save_title("A-00000000-00000",request_data)
    activity = WorkActivity()
    db_activity = activity.get_activity_detail("A-00000000-00000")
    assert db_activity.title == "ja_conference paperITEM00000001(public_open_access_open_access_simple)"


# def get_key_title_in_item_type_mapping(item_type_mapping):
# def get_title_in_request(request_data, key, key_child):
# def hide_form_items(item_type, schema_form):
# def hide_thumbnail(schema_form):
#     def is_thumbnail(items):
# def get_ignore_item(_item_type_id, item_type_mapping=None,
# def make_stats_csv_with_permission(item_type_id, recids,
#     def _get_root_item_option(item_id, item, sub_form={'title_i18n': {}}):
#         def __init__(self, record_ids, records_metadata):
#             def hide_metadata_email(record):
#         def get_max_ins(self, attr):
#         def get_max_ins_feedback_mail(self):
#         def get_max_items(self, item_attrs):
#         def get_subs_item(self,
# def check_item_is_being_edit(
# def check_item_is_deleted(recid):
# def permission_ranking(result, pid_value_permissions, display_rank, list_name,
# def has_permission_edit_item(record, recid):
