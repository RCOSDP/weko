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

"""Module tests."""

import csv
from io import StringIO
from unittest import mock
import pytest
import json
from tests.helpers import json_data
from unittest.mock import patch, MagicMock
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_search.engine import search
from sqlalchemy.exc import SQLAlchemyError
from weko_authors.models import Authors, AuthorsAffiliationSettings,AuthorsPrefixSettings

from weko_deposit.tasks import (
    get_origin_data,
    make_stats_file,
    update_db_es_data,
    update_items_by_authorInfo
)
[
    {
        "recid": "1",
        "year": 1985,
        "stars": 4,
        "title": ["test_item1"],
        "item_title": "test_item1",
        "_deposit": {
            "id": "3",
            "pid": { "type": "depid", "value": "3", "revision_id": 0 },
            "owner": "1",
            "owners": [1],
            "status": "published",
            "created_by": 1,
            "owners_ext": {
                "email": "wekosoftware@nii.ac.jp",
                "username": "",
                "displayname": ""
            }
        }
    },
]

# mock Elasticsearch search
class MockRecordsSearch:
    class MockQuery:
        class MockExecute:
            def __init__(self):
                pass
            def to_dict(self):
                record_hit={'hits': {'hits': json_data('data/record_hit1.json'), 'total': {"value": 2, "relation": "eq"}}}
                return record_hit
        def __init__(self):
            pass
        def execute(self):
            return self.MockExecute()
    def __init__(self, index=None):
        pass

    def update_from_dict(self,query=None):
        return self.MockQuery()

# mock the index creation
class MockRecordIndexer:
    def bulk_index(self, query):
        pass

    def process_bulk_queue(self, es_bulk_kwargs):
        pass

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::test_update_authorInfo -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_update_authorInfo(app, db, location, records):
# def test_update_authorInfo(app, db, records, authors):
    app.config.update(WEKO_SEARCH_MAX_RESULT=1)
    patch("weko_deposit.tasks.WekoDeposit.update_author_link")
    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch("weko_deposit.tasks.RecordsSearch", mock_recordssearch):
        with patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer):
            update_items_by_authorInfo(["1","xxx"], {})
    _target = {
        'authorNameInfo': [
            {'nameShowFlg': False}
        ],
        'authorIdInfo': [
            {'authorIdShowFlg': False}
        ],
        'affiliationInfo': [
        ],
        'emailInfo': []
    }

    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch("weko_deposit.tasks.RecordsSearch", mock_recordssearch):
        with patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer):
            update_items_by_authorInfo(["1","xxx"], _target)

    weko = AuthorsPrefixSettings(
        id=1,
        name="WEKO",
        scheme="WEKO"
    )
    orcid = AuthorsPrefixSettings(
        id=2,
        name="ORCID",
        scheme="ORCID",
        url="https://orcid.org/##"
    )
    cinii = AuthorsPrefixSettings(
        id=3,
        name="CiNii",
        scheme="CiNii",
        url="https://ci.nii.ac.jp/author/"
    )
    db.session.add(weko)
    db.session.add(orcid)
    db.session.add(cinii)
    isni = AuthorsAffiliationSettings(
        id=1,
        name="ISNI",
        scheme="ISNI",
        url="http://www.isni.org/isni/##"
    )
    grid = AuthorsAffiliationSettings(
        id=2,
        name="GRID",
        scheme="GRID",
        url="https://www.grid.ac/institutes/"
    )
    ringgold = AuthorsAffiliationSettings(
        id=3,
        name="Ringgold",
        scheme="Ringgold",
    )
    db.session.add(isni)
    db.session.add(grid)
    db.session.add(ringgold)
    db.session.commit()

    _target = {
        'authorNameInfo': [
            {"nameShowFlg":False},
            {
                'nameShowFlg': True,
                'familyName': 'Test Fname',
                'language': 'en',
                'firstName': 'Test Gname'
            }
        ],
        'authorIdInfo': [
            {"authorIdShowFlg":False},
            {
                'authorIdShowFlg': True,
                'idType': '', # not prefix_info
                'authorId':'1'
            },
            {
                "authorIdShowFlg":True,
                "idType":"1", # prefix_info[url] is none
                'authorId':'2'
            },
            {
                "authorIdShowFlg":True,
                "idType":"2", # prefix_info[url] contain ##
                'authorId':'3'
            },
            {
                "authorIdShowFlg":True,
                "idType":"3", # prefix_info[url] not contain ##
                'authorId':'4'
            }
        ],
        'affiliationInfo': [
            {
                'identifierInfo': [
                    {'identifierShowFlg': False},
                    {
                        "identifierShowFlg":True,
                        "affiliationIdType":"",
                        "affiliationId":"aaa"
                    },
                    {
                        "identifierShowFlg":True,
                        "affiliationIdType":"1", # url contain ##
                        "affiliationId":"bbb"
                    },
                    {
                        "identifierShowFlg":True,
                        "affiliationIdType":"2", # url not contain ##
                        "affiliationId":"ccc"
                    },
                    {
                        "identifierShowFlg":True,
                        "affiliationIdType":"3", # not url
                        "affiliationId":"ddd"
                    }
                ],
                'affiliationNameInfo': [
                    {"affiliationNameShowFlg":False},
                    {
                        'affiliationNameShowFlg': True,
                        'affiliationName': 'A01',
                        'affiliationNameLang': 'en'
                    }
                ]
            }
        ],
        'emailInfo': [
            {
                'email': 'test@nii.ac.jp'
            }
        ]
    }
    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch("weko_deposit.tasks.RecordsSearch", mock_recordssearch):
        with patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer):
            update_items_by_authorInfo(["1","xxx"], _target)

    # SQLAlchemyError
    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch("weko_deposit.tasks.RecordsSearch", mock_recordssearch):
        with patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer):
            ex = SQLAlchemyError("test_error")
            with patch("weko_deposit.tasks.db.session.commit", side_effect=ex):
                with patch("weko_deposit.tasks.update_items_by_authorInfo.retry") as mock_retry:
                    with patch("weko_deposit.tasks.weko_logger") as mock_logger:
                        update_items_by_authorInfo(["1","xxx"], _target)
                        mock_logger.assert_any_call(key='WEKO_COMMON_DB_SOME_ERROR', ex=ex)

    # Exception
    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch("weko_deposit.tasks.RecordsSearch", mock_recordssearch):
        with patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer):
            ex = Exception("test_exception")
            with patch("weko_deposit.tasks.db.session.commit", side_effect=ex):
                with patch("weko_deposit.tasks.update_items_by_authorInfo.retry") as mock_retry:
                    with patch("weko_deposit.tasks.weko_logger") as mock_logger:
                        update_items_by_authorInfo(["1","xxx"], _target)
                        mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)

# def _update_author_data(item_id, record_ids):
# isinstance(data, dict) and 'nameIdentifiers' in data is False
def test_update_authorInfo_no_nameIdentifiers(app, db, location, records2):
    app.config.update(WEKO_SEARCH_MAX_RESULT=1)
    patch("weko_deposit.tasks.WekoDeposit.update_author_link")
    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch("weko_deposit.tasks.update_db_es_data") as mock_update_db_es_data:
        with patch("weko_deposit.tasks.RecordsSearch", mock_recordssearch):
            with patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer):
                update_items_by_authorInfo(1, {})

# Test for _update_author_data when for loop continues
def test_no_creatorNames_contributorNames_names(app, db, location, records3):
    app.config.update(WEKO_SEARCH_MAX_RESULT=1)
    patch("weko_deposit.tasks.WekoDeposit.update_author_link")
    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch("weko_deposit.tasks.RecordsSearch", mock_recordssearch):
        with patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer):
            update_items_by_authorInfo(1, {})

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::test_update_authorInfo -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_update_authorInfo_case1(app, db, location, records):
# def test_update_authorInfo(app, db, records, authors):
    app.config.update(WEKO_SEARCH_MAX_RESULT=1)
    patch("weko_deposit.tasks.WekoDeposit.update_author_link")
    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch("weko_deposit.tasks.RecordsSearch", mock_recordssearch):
        with patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer):
            update_items_by_authorInfo(["1","xxx"], {}, ['xxx', '1', '2'], [], False)
    _target = {
        'authorNameInfo': [
            {'nameShowFlg': False}
        ],
        'authorIdInfo': [
            {'authorIdShowFlg': False}
        ],
        'affiliationInfo': [
        ],
        'emailInfo': []
    }

    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch("weko_deposit.tasks.RecordsSearch", mock_recordssearch):
        with patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer):
            update_items_by_authorInfo(["1","xxx"], _target, ['xxx', '1', '2'], [], False)

    weko = AuthorsPrefixSettings(
        id=1,
        name="WEKO",
        scheme="WEKO"
    )
    orcid = AuthorsPrefixSettings(
        id=2,
        name="ORCID",
        scheme="ORCID",
        url="https://orcid.org/##"
    )
    cinii = AuthorsPrefixSettings(
        id=3,
        name="CiNii",
        scheme="CiNii",
        url="https://ci.nii.ac.jp/author/"
    )
    db.session.add(weko)
    db.session.add(orcid)
    db.session.add(cinii)
    isni = AuthorsAffiliationSettings(
        id=1,
        name="ISNI",
        scheme="ISNI",
        url="http://www.isni.org/isni/##"
    )
    grid = AuthorsAffiliationSettings(
        id=2,
        name="GRID",
        scheme="GRID",
        url="https://www.grid.ac/institutes/"
    )
    ringgold = AuthorsAffiliationSettings(
        id=3,
        name="Ringgold",
        scheme="Ringgold",
    )
    db.session.add(isni)
    db.session.add(grid)
    db.session.add(ringgold)
    db.session.commit()

    _target = {
        'authorNameInfo': [
            {"nameShowFlg":False},
            {
                'nameShowFlg': True,
                'familyName': 'Test Fname',
                'language': 'en',
                'firstName': 'Test Gname'
            }
        ],
        'authorIdInfo': [
            {"authorIdShowFlg":False},
            {
                'authorIdShowFlg': True,
                'idType': '', # not prefix_info
                'authorId':'1'
            },
            {
                "authorIdShowFlg":True,
                "idType":"1", # prefix_info[url] is none
                'authorId':'2'
            },
            {
                "authorIdShowFlg":True,
                "idType":"2", # prefix_info[url] contain ##
                'authorId':'3'
            },
            {
                "authorIdShowFlg":True,
                "idType":"3", # prefix_info[url] not contain ##
                'authorId':'4'
            }
        ],
        'affiliationInfo': [
            {
                'identifierInfo': [
                    {'identifierShowFlg': False},
                    {
                        "identifierShowFlg":True,
                        "affiliationIdType":"",
                        "affiliationId":"aaa"
                    },
                    {
                        "identifierShowFlg":True,
                        "affiliationIdType":"1", # url contain ##
                        "affiliationId":"bbb"
                    },
                    {
                        "identifierShowFlg":True,
                        "affiliationIdType":"2", # url not contain ##
                        "affiliationId":"ccc"
                    },
                    {
                        "identifierShowFlg":True,
                        "affiliationIdType":"3", # not url
                        "affiliationId":"ddd"
                    }
                ],
                'affiliationNameInfo': [
                    {"affiliationNameShowFlg":False},
                    {
                        'affiliationNameShowFlg': True,
                        'affiliationName': 'A01',
                        'affiliationNameLang': 'en'
                    }
                ]
            }
        ],
        'emailInfo': [
            {
                'email': 'test@nii.ac.jp'
            }
        ]
    }
    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch("weko_deposit.tasks.RecordsSearch", mock_recordssearch):
        with patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer):
            update_items_by_authorInfo(["1","xxx"], _target, ['xxx', '1', '2'], [], False)


# update_gather_flg = True
def test_update_authorInfo_with_update_gather_flg(app, db, location, records):
    app.config.update(WEKO_SEARCH_MAX_RESULT=1)
    patch("weko_deposit.tasks.WekoDeposit.update_author_link")
    _target = {
        'authorNameInfo': [
            {'nameShowFlg': False},
            {'nameShowFlg': True, 'familyName': 'Test Fname', 'firstName': 'Test Gname', 'language': 'en'}
        ],
        'affiliationInfo': [
            {
                'affiliationNameInfo': [
                    {'affiliationNameShowFlg': False},
                    {'affiliationName': 'A01', 'affiliationNameLang': 'en'}
                ]
            }
        ],
        'emailInfo': [
            {'email': 'test@nii.ac.jp'}
        ]
    }
    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch("weko_deposit.tasks.RecordsSearch", mock_recordssearch):
        with patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer):
            with patch("weko_deposit.tasks.get_origin_data", return_value={}):
                with patch("weko_deposit.tasks.update_db_es_data") as mock_update_db_es_data:
                    with patch("weko_deposit.tasks.delete_cache_data") as mock_delete_cache_data:
                        with patch("weko_deposit.tasks.update_cache_data") as mock_update_cache_data:
                            with patch("weko_deposit.tasks.weko_logger") as mock_logger:
                                    update_items_by_authorInfo(["1","xxx"], _target, ['xxx', '1', '2'], [], True)
                                    mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='update_gather_flg is not empty')
                                    mock_update_db_es_data.assert_called_once()
                                    mock_delete_cache_data.assert_called_once_with("update_items_by_authorInfo_['1', 'xxx']")
                                    mock_update_cache_data.assert_called_once()

# def update_items_by_authorInfo(user_id, target, origin_pkid_list=[], origin_id_list=[], update_gather_flg=False):
#   def _update_author_data(item_id, record_ids):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::test_update_author_data -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp --full-trace
def test_update_author_data(app, db, es_records):
    pid_value = es_records[1][0]["deposit"].pid.pid_value
    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch("weko_deposit.tasks.RecordsSearch", mock_recordssearch):
        with patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer):
            patch("weko_deposit.tasks.WekoDeposit.update_author_link")
            ex = PIDDoesNotExistError(pid_type='recid', pid_value=pid_value)
            with patch("weko_deposit.tasks.PersistentIdentifier.get", side_effect=ex) as mock_pid:
                with patch("weko_deposit.tasks.weko_logger")as mock_logger:
                    update_items_by_authorInfo(["1","xxx"], {})
                    mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                    mock_logger.assert_any_call(key='WEKO_COMMON_WHILE_START')
                    mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                    mock_logger.assert_any_call(count=mock.ANY, element=mock.ANY, key='WEKO_COMMON_WHILE_LOOP_ITERATION')
                    mock_logger.assert_any_call(ex=ex, key='WEKO_DEPOSIT_PID_STATUS_NOT_REGISTERED', pid=mock.ANY)
                    mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                    mock_logger.assert_called_with(key='WEKO_COMMON_WHILE_END')

            ex = SQLAlchemyError()
            with patch("weko_deposit.tasks.PersistentIdentifier.get", side_effect=ex) as mock_pid:
                with patch("weko_deposit.tasks.weko_logger")as mock_logger:
                    update_items_by_authorInfo(["1","xxx"], {})
                    mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                    mock_logger.assert_any_call(key='WEKO_COMMON_WHILE_START')
                    mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                    mock_logger.assert_any_call(count=mock.ANY, element=mock.ANY, key='WEKO_COMMON_WHILE_LOOP_ITERATION')
                    mock_logger.assert_any_call(ex=ex, key='WEKO_COMMON_DB_SOME_ERROR')
                    mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=(None, set()))
                    mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                    mock_logger.assert_called_with(key='WEKO_COMMON_WHILE_END')

            ex = Exception()
            with patch("weko_deposit.tasks.PersistentIdentifier.get", side_effect=ex) as mock_pid:
                with patch("weko_deposit.tasks.weko_logger")as mock_logger:
                    update_items_by_authorInfo(["1","xxx"], {})
                    mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                    mock_logger.assert_any_call(key='WEKO_COMMON_WHILE_START')
                    mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                    mock_logger.assert_any_call(count=mock.ANY, element=mock.ANY, key='WEKO_COMMON_WHILE_LOOP_ITERATION')
                    mock_logger.assert_any_call(ex=ex, key='WEKO_COMMON_ERROR_UNEXPECTED')
                    mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=(None, set()))
                    mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                    mock_logger.assert_called_with(key='WEKO_COMMON_WHILE_END')

# def get_origin_data(origin_pkid_list):
def test_get_origin_data(app, db):
    origin_pkid_list = [1, 2]
    db.session.add(Authors(
            id=1,
            json={"name": "Test Fname"},
            is_deleted=False
        ))
    db.session.add(Authors(
            id=2,
            json={"name": "Test Gname"},
            is_deleted=False
        ))
    db.session.commit()

    result = get_origin_data(origin_pkid_list)
    expected_result = [{"name": "Test Fname"}, {"name": "Test Gname"}]
    assert result == expected_result

    result = get_origin_data([5])
    assert result == []

# def update_db_es_data(origin_pkid_list, origin_id_list):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::test_get_origin_data -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp --full-trace
def test_update_db_es_data(app, db,esindex, es_records,authors):
    authors_db = Authors.query.all()
    origin_id_list=[]
    for author in authors_db:
        origin_id_list.append(author.json["id"])
    origin_pkid_list = [1, 2]

    update_db_es_data(origin_pkid_list, origin_id_list)
    author1 = db.session.query(Authors).filter(Authors.id == 1).first()
    author2 = db.session.query(Authors).filter(Authors.id == 2).first()
    assert author1.gather_flg == 1
    assert author2.gather_flg == 1
    from flask import current_app
    current_app.config["WEKO_AUTHORS_ES_DOC_TYPE"]="wrong_doctype"

    # SQLAlchemyError by db.session.commit()
    ex = SQLAlchemyError("test_error")
    with patch("weko_deposit.tasks.db.session.commit", side_effect=ex):
        with patch("weko_deposit.tasks.weko_logger") as mock_logger:
            update_db_es_data(origin_pkid_list, origin_id_list)
            mock_logger.assert_any_call(key='WEKO_COMMON_DB_SOME_ERROR', ex=ex)

    # ElasticsearchException by indexer.client.update()
    ex = search.OpenSearchException("test_elasticsearch_error")
    with patch("invenio_search.ext.Elasticsearch.update", side_effect=ex):
        with patch("weko_deposit.tasks.weko_logger") as mock_logger:
            update_db_es_data(origin_pkid_list, origin_id_list)
            mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_ELASTICSEARCH', ex=ex)

    # Exception by indexer.client.update()
    ex = Exception("test_exception")
    with patch("invenio_search.ext.Elasticsearch.update", side_effect=ex):
        with patch("weko_deposit.tasks.weko_logger") as mock_logger:
            update_db_es_data(origin_pkid_list, origin_id_list)
            mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)

# def make_stats_file(raw_stats):
def test_make_stats_file(app, db):
    TARGET_LABEL = 'target'
    # file_format is tsv
    # success_items and fail_items is empty
    raw_stats = {
        "target": {},
        "origin": [],
        "success_items": [],
        "fail_items": []
    }
    file = StringIO()
    writer = csv.writer(file, delimiter="\t", lineterminator="\n")
    writer.writerow(["[TARGET]"])
    writer.writerow([])
    writer.writerow([])
    writer.writerow("")
    writer.writerow(["[ORIGIN]"])
    writer.writerow("")
    writer.writerow(["[SUCCESS]"])
    writer.writerow("")
    writer.writerow(["[FAIL]"])

    result = make_stats_file(raw_stats)
    assert result.getvalue() == file.getvalue()

    # file_format is csv
    app.config.update(WEKO_ADMIN_OUTPUT_FORMAT='csv')
    # success_items and fail_items is not empty
    raw_stats = {
        "target": {
            "target_key1": "target_value1",
            "target_key2": "target_value2"
        },
        "origin": [{}, {}],
        "success_items": [
            {
                "record_id":"test_id1",
                "author_ids":"test_id2",
                "message":"test_message"
            },
            {
                "record_id":"test_id3",
                "author_ids":"test_id4",
                "message":"test_message"
            }],
        "fail_items": [
            {
                "record_id":"test_id5",
                "author_ids":"test_id6",
                "message":"test_message"
            },
            {
                "record_id":"test_id7",
                "author_ids":"test_id8",
                "message":"test_message"
            }]
    }
    file = StringIO()
    writer = csv.writer(file, delimiter=",", lineterminator="\n")
    writer.writerow(["[TARGET]"])
    writer.writerow(["target_key1", "target_key2"])
    writer.writerow(["target_value1", "target_value2"])
    writer.writerow("")
    writer.writerow(["[ORIGIN]"])
    writer.writerow([])
    writer.writerow([])
    writer.writerow([])
    writer.writerow([])
    writer.writerow("")
    writer.writerow(["[SUCCESS]"])
    writer.writerow(["record_id", "author_ids", "message"])
    writer.writerow(["test_id1", "test_id2", "test_message"])
    writer.writerow(["test_id3", "test_id4", "test_message"])
    writer.writerow("")
    writer.writerow(["[FAIL]"])
    writer.writerow(["record_id", "author_ids", "message"])
    writer.writerow(["test_id5", "test_id6", "test_message"])
    writer.writerow(["test_id7", "test_id8", "test_message"])

    result = make_stats_file(raw_stats)
    assert result.getvalue() == file.getvalue()
