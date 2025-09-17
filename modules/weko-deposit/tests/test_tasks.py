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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Module tests."""

import pytest
import uuid
import os
from tests.helpers import json_data, create_record_with_pdf
from mock import patch, MagicMock
from weko_authors.models import AuthorsAffiliationSettings,AuthorsPrefixSettings
from weko_deposit.api import WekoIndexer, WekoDeposit
from weko_deposit.tasks import (
    update_items_by_authorInfo,
    extract_pdf_and_update_file_contents,
    update_file_content,
    _get_author_prefix,
    _get_affiliation_id,
    _change_to_meta,
    _update_author_data,
    _process
)
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.errors import PIDDoesNotExistError
from sqlalchemy.exc import SQLAlchemyError

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
class MockRecordsSearch:
    class MockQuery:
        class MockExecute:
            def __init__(self):
                pass
            def to_dict(self):
                record_hit={'hits': {'hits': json_data('data/record_hit1.json'), 'total': 2}}
                return record_hit
        def __init__(self):
            pass
        def execute(self):
            return self.MockExecute()
    def __init__(self, index=None):
        pass
    
    def update_from_dict(self,query=None):
        return self.MockQuery()

class MockRecordIndexer:
    def bulk_index(self, query):
        list(query)
        pass

    def process_bulk_queue(self, es_bulk_kwargs):
        pass

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::test_update_authorInfo -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_update_authorInfo(app, db, records,mocker):
    app.config.update(WEKO_SEARCH_MAX_RESULT=1)
    mocker.patch("weko_deposit.tasks.WekoDeposit.update_author_link")
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

class TestUpdateItemsByAuthorInfo:
    # 54702-3
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateItemsByAuthorInfo::test_update_authorInfo_not_exists_update_gather_flg -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_authorInfo_not_exists_update_gather_flg(self, app, db, records, mocker, caplog):
        with patch('weko_deposit.tasks._get_author_prefix') as mock_get_author_prefix, \
                patch('weko_deposit.tasks._get_affiliation_id') as mock_get_affiliation_id, \
                patch('weko_deposit.tasks._process') as mock_process, \
                patch('weko_deposit.tasks.get_origin_data') as mock_get_origin_data, \
                patch('weko_deposit.tasks.update_db_es_data') as mock_update_db_es_data, \
                patch('weko_deposit.tasks.delete_cache_data') as mock_delete_cache_data, \
                patch('weko_deposit.tasks.update_cache_data') as mock_update_cache_data:

            mock_get_author_prefix.return_value = {}
            mock_get_affiliation_id.return_value = {}
            mock_process.return_value = (1, False)
            mock_get_origin_data.return_value = []
            mock_update_db_es_data.return_value = None
            mock_delete_cache_data.return_value = None
            mock_update_cache_data.return_value = None

            user_id = 1
            target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1", "authorIdShowFlg": "true"}]}

            with caplog.at_level("DEBUG"):
                update_items_by_authorInfo(user_id, target)
                assert "Total 1 items have been updated." in caplog.text

    # 54702-25
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateItemsByAuthorInfo::test_update_items_by_authorInfo_success -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_items_by_authorInfo_success(self, db, app):
        with patch('weko_deposit.tasks._get_author_prefix') as mock_get_author_prefix, \
                patch('weko_deposit.tasks._get_affiliation_id') as mock_get_affiliation_id, \
                patch('weko_deposit.tasks._process') as mock_process, \
                patch('weko_deposit.tasks.get_origin_data') as mock_get_origin_data, \
                patch('weko_deposit.tasks.update_db_es_data') as mock_update_db_es_data, \
                patch('weko_deposit.tasks.delete_cache_data') as mock_delete_cache_data, \
                patch('weko_deposit.tasks.update_cache_data') as mock_update_cache_data:
            mock_get_author_prefix.return_value = {}
            mock_get_affiliation_id.return_value = {}
            mock_process.return_value = (1, False)
            mock_get_origin_data.return_value = []
            mock_update_db_es_data.return_value = None
            mock_delete_cache_data.return_value = None
            mock_update_cache_data.return_value = None
            user_id = 1
            target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1", "authorIdShowFlg": "true"}]}
            origin_pkid_list = ["1"]
            origin_id_list = ["weko_id_1"]
            update_gather_flg = True
            update_items_by_authorInfo(user_id, target, origin_pkid_list, origin_id_list, update_gather_flg)
            mock_process.assert_called()
            mock_get_origin_data.assert_called()
            mock_update_db_es_data.assert_called()
            mock_delete_cache_data.assert_called()
            mock_update_cache_data.assert_called()

    # 54702-26
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateItemsByAuthorInfo::test_update_items_by_authorInfo_success2 -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_items_by_authorInfo_success2(self, db, app):
        with patch('weko_deposit.tasks._get_author_prefix') as mock_get_author_prefix, \
                patch('weko_deposit.tasks._get_affiliation_id') as mock_get_affiliation_id, \
                patch('weko_deposit.tasks._process') as mock_process, \
                patch('weko_deposit.tasks.get_origin_data') as mock_get_origin_data, \
                patch('weko_deposit.tasks.update_db_es_data') as mock_update_db_es_data, \
                patch('weko_deposit.tasks.delete_cache_data') as mock_delete_cache_data, \
                patch('weko_deposit.tasks.update_cache_data') as mock_update_cache_data:
            mock_get_author_prefix.return_value = {}
            mock_get_affiliation_id.return_value = {}
            mock_process.side_effect = [(1, True), (2, False)]  # 1度目と2度目のreturn_valueを設定
            mock_get_origin_data.return_value = []
            mock_update_db_es_data.return_value = None
            mock_delete_cache_data.return_value = None
            mock_update_cache_data.return_value = None
            user_id = 1
            target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1", "authorIdShowFlg": "true"}]}
            origin_pkid_list = ["1"]
            origin_id_list = ["weko_id_1"]
            update_gather_flg = False
            update_items_by_authorInfo(user_id, target, origin_pkid_list, origin_id_list, update_gather_flg)
            mock_process.assert_called()
            mock_get_origin_data.assert_not_called()
            mock_update_db_es_data.assert_not_called()
            mock_delete_cache_data.assert_not_called()
            mock_update_cache_data.assert_not_called()

    # 54702-31
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateItemsByAuthorInfo::test_update_items_by_authorInfo_sqlalchemy_error -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_items_by_authorInfo_sqlalchemy_error(self, db, app):
        with patch('weko_deposit.tasks._get_author_prefix') as mock_get_author_prefix, \
                patch('weko_deposit.tasks._get_affiliation_id') as mock_get_affiliation_id, \
                patch('weko_deposit.tasks._process') as mock_process, \
                patch('weko_deposit.tasks.get_origin_data') as mock_get_origin_data, \
                patch('weko_deposit.tasks.update_db_es_data') as mock_update_db_es_data, \
                patch('weko_deposit.tasks.delete_cache_data') as mock_delete_cache_data, \
                patch('weko_deposit.tasks.update_cache_data') as mock_update_cache_data, \
                patch('weko_deposit.tasks.db.session.rollback') as mock_db_rollback, \
                patch('weko_deposit.tasks.update_items_by_authorInfo.retry') as mock_retry:

            mock_get_author_prefix.return_value = {}
            mock_get_affiliation_id.return_value = {}
            mock_process.side_effect = SQLAlchemyError("Test SQLAlchemyError")
            mock_get_origin_data.return_value = []
            mock_update_db_es_data.return_value = None
            mock_delete_cache_data.return_value = None
            mock_update_cache_data.return_value = None
            mock_db_rollback.return_value = None
            mock_retry.return_value = None

            user_id = 1
            target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1", "authorIdShowFlg": "true"}]}
            origin_pkid_list = ["1"]
            origin_id_list = ["weko_id_1"]
            update_gather_flg = True

            update_items_by_authorInfo(user_id, target, origin_pkid_list, origin_id_list, update_gather_flg)

            mock_process.assert_called()
            mock_db_rollback.assert_called()
            mock_retry.assert_called()

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestGetAuthorPrefix -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestGetAuthorPrefix:
    # 54702-4,5
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestGetAuthorPrefix::test_get_author_prefix -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_author_prefix(self, app, db, records, mocker):
        db.session.query(AuthorsPrefixSettings).delete()
        results = _get_author_prefix()

        assert results == {}

        weko = AuthorsPrefixSettings(id=1, name="GRID", scheme="GRID", url="https://grid.ac/##")
        orcid = AuthorsPrefixSettings(id=2, name="ROR", scheme="ROR", url="https://ror.org/##")
        db.session.add(weko)
        db.session.add(orcid)

        results = _get_author_prefix()
        assert results == {
            "1": {"scheme": "GRID", "url": "https://grid.ac/##"},
            "2": {"scheme": "ROR", "url": "https://ror.org/##"},
        }
        db.session.rollback()

    # 54702-27
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestGetAuthorPrefix::test_get_author_prefix_error -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_author_prefix_error(self, app, db, records, mocker):
        with patch("weko_authors.models.AuthorsPrefixSettings.query", side_effect=Exception("DB error")):
            with pytest.raises(Exception) as e:
                _get_author_prefix()
                assert str(e.value) == "DB error"

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestGetAffiliaitonId -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestGetAffiliaitonId:
    # 54702-6,7
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestGetAffiliaitonId::test_get_affiliation_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_affiliation_id(self, app, db, records, mocker):
        db.session.query(AuthorsAffiliationSettings).delete()
        results = _get_affiliation_id()

        assert results == {}

        weko = AuthorsAffiliationSettings(id=1, name="GRID", scheme="GRID", url="https://grid.ac/##")
        orcid = AuthorsAffiliationSettings(id=2, name="ROR", scheme="ROR", url="https://ror.org/##")
        db.session.add(weko)
        db.session.add(orcid)

        results = _get_affiliation_id()
        assert results == {
            "1": {"scheme": "GRID", "url": "https://grid.ac/##"},
            "2": {"scheme": "ROR", "url": "https://ror.org/##"},
        }
        db.session.rollback()

    # 54702-28
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestGetAffiliaitonId::test_get_affiliation_id_error -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_affiliation_id_error(self, app, db, records, mocker):
        with patch("weko_authors.models.AuthorsAffiliationSettings.query", side_effect=Exception("DB error")):
            with pytest.raises(Exception) as e:
                _get_affiliation_id()
                assert str(e.value) == "DB error"

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestProcess -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestProcess:
    # 54702-21
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestProcess::test_process_with_record_ids -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.RecordsSearch')
    @patch('weko_deposit.tasks._update_author_data')
    @patch('weko_deposit.tasks.db.session.commit')
    def test_process_with_record_ids(self, mock_commit, mock_update_author_data, mock_records_search, app, db, records, mocker, prepare_key_map):
        mock_bulk_index = mocker.patch('invenio_indexer.api.RecordIndexer.bulk_index')
        mock_process_bulk_queue = mocker.patch('invenio_indexer.api.RecordIndexer.process_bulk_queue')
        with patch('weko_deposit.api.WekoDeposit.get_record', return_value = WekoDeposit({})):
            # 条件
            data_size = 10
            data_from = 0
            process_counter = {}
            target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1", "authorIdShowFlg": "true"}]}
            origin_pkid_list = ["1"]
            author_prefix = {...}
            affiliation_id = {...}
            force_change = False

            # モックの設定
            mock_records_search.return_value.update_from_dict.return_value.execute.return_value.to_dict.return_value = {
                'hits': {
                    'hits': [{'_source': {'control_number': '1'}}],
                    'total': 1
                }
            }
            uuid1 = uuid.uuid4()
            mock_update_author_data.return_value = (uuid1, [uuid1], set())

            # 実行
            result = _process(data_size, data_from, process_counter, target, origin_pkid_list, prepare_key_map, author_prefix, affiliation_id)
            mock_bulk_index.assert_called()
            mock_process_bulk_queue.assert_called()

    # 54702-22,23
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestProcess::test_process_compare_data_size -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.RecordsSearch')
    @patch('weko_deposit.tasks._update_author_data')
    @patch('weko_deposit.tasks.db.session.commit')
    def test_process_compare_data_size(self, mock_commit, mock_update_author_data, mock_records_search, app, db, records, mocker, prepare_key_map):
        mocker.patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer)
        data_size = 1
        data_from = 0
        process_counter = {}
        target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1", "authorIdShowFlg": "true"}]}
        origin_pkid_list = ["1"]
        author_prefix = {...}
        affiliation_id = {...}

        with patch('weko_deposit.api.WekoDeposit.get_record', return_value = WekoDeposit({})):
            mock_records_search.return_value.update_from_dict.return_value.execute.return_value.to_dict.return_value = {
                'hits': {
                    'hits': [{'_source': {'control_number': '1'}}, {'_source': {'control_number': '2'}}],
                    'total': 2
                }
            }
            uuid1 = uuid.uuid4()
            mock_update_author_data.return_value = (uuid1, [uuid1], set())
            result = _process(data_size, data_from, process_counter, target, origin_pkid_list, prepare_key_map, author_prefix, affiliation_id)
            assert result == (2, True)

            data_size = 10
            mock_records_search.return_value.update_from_dict.return_value.execute.return_value.to_dict.return_value = {
                'hits': {
                    'hits': [{'_source': {'control_number': '1'}}],
                    'total': 1
                }
            }
            result = _process(data_size, data_from, process_counter, target, origin_pkid_list, prepare_key_map, author_prefix, affiliation_id)
            assert result == (1, False)

    # 54702-24
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestProcess::test_process_update_author_data_error -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.RecordsSearch')
    @patch('weko_deposit.tasks._update_author_data')
    @patch('weko_deposit.tasks.db.session.commit')
    def test_process_update_author_data_error(self, mock_commit, mock_update_author_data, mock_records_search, app, db, records, mocker, prepare_key_map):
        mock_bulk_index = mocker.patch('invenio_indexer.api.RecordIndexer.bulk_index')
        mock_process_bulk_queue = mocker.patch('invenio_indexer.api.RecordIndexer.process_bulk_queue')
        with patch('weko_deposit.api.WekoDeposit.get_record', return_value = WekoDeposit({})):
            # 条件
            data_size = 10
            data_from = 0
            process_counter = {}
            target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1", "authorIdShowFlg": "true"}]}
            origin_pkid_list = ["1"]
            author_prefix = {...}
            affiliation_id = {...}
            force_change = False

            # モックの設定
            mock_records_search.return_value.update_from_dict.return_value.execute.return_value.to_dict.return_value = {
                'hits': {
                    'hits': [{'_source': {'control_number': '1'}}],
                    'total': 1
                }
            }
            uuid1 = uuid.uuid4()
            mock_update_author_data.return_value = (None, set(), {})

            # 実行
            result = _process(data_size, data_from, process_counter, target, origin_pkid_list, prepare_key_map, author_prefix, affiliation_id)
            assert result[0] == 0

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestChangeToMeta -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestChangeToMeta:
    # 54702-8
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestChangeToMeta::test_change_to_meta_empty_target -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_change_to_meta_empty_target(self, app, db, records, mocker, prepare_key_map):
        target = {}
        author_prefix = {}
        affiliation_id = {}
        item_names_data = {}

        target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, prepare_key_map, item_names_data)

        assert target_id == None
        assert meta == {}

    # 54702-9,10
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestChangeToMeta::test_change_to_meta_exists_authorNameInfo -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_change_to_meta_exists_authorNameInfo(self, app, db, records, mocker, prepare_key_map):
        target = {"authorNameInfo": [{"nameShowFlg": True, "familyName": "山田", "firstName": "太郎", "language": "ja"}, {"nameShowFlg": False, "familyName": "Yamada", "firstName": "Taro", "language": "en"}]}
        author_prefix = {}
        affiliation_id = {}
        item_names_data = {}
        for key in prepare_key_map:
            if key == "creator":
                target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, prepare_key_map["creator"], item_names_data)
                assert meta == {"creatorNames": [{"creatorName": "山田, 太郎", "creatorNameLang": "ja"}], "familyNames": [{"familyName": "山田", "familyNameLang": "ja"}], "givenNames": [{"givenName": "太郎", "givenNameLang": "ja"}]}
            elif key == "contributor":
                target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, prepare_key_map["contributor"], item_names_data)
                assert meta == {"contributorNames": [{"contributorName": "山田, 太郎", "lang": "ja"}], "familyNames": [{"familyName": "山田", "familyNameLang": "ja"}], "givenNames": [{"givenName": "太郎", "givenNameLang": "ja"}]}
            elif key == "full_name":
                target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, prepare_key_map["full_name"], item_names_data)
                assert meta == {"names": [{"name": "山田, 太郎", "nameLang": "ja"}], "familyNames": [{"familyName": "山田", "familyNameLang": "ja"}], "givenNames": [{"givenName": "太郎", "givenNameLang": "ja"}]}

        target = {"authorNameInfo": [{"nameShowFlg": True, "familyName": "山田", "firstName": "太郎", "language": "ja"}, {"nameShowFlg": True, "familyName": "Yamada", "firstName" :"Taro", "language": "en"}]}

        for key in prepare_key_map:
            if key == "creator":
                item_names_data = [{"creatorName": "テスト, 太郎", "creatorNameLang": "ja", "creatorNameType": "Personal"}]
                target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, prepare_key_map["creator"], item_names_data)
                assert meta == {"creatorNames":[{"creatorName": "山田, 太郎", "creatorNameLang": "ja", "creatorNameType": "Personal"}, {"creatorName": "Yamada, Taro", "creatorNameLang": "en"}], "familyNames": [{"familyName": "山田", "familyNameLang": "ja"}, {"familyName": "Yamada", "familyNameLang": "en"}], "givenNames": [{"givenName": "太郎", "givenNameLang": "ja"}, {"givenName": "Taro", "givenNameLang": "en"}]}
            elif key == "contributor":
                item_names_data = [{"contributorName": "テスト, 太郎", "lang": "ja", "nameType": "Personal"}]
                target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, prepare_key_map["contributor"], item_names_data)
                assert meta == {"contributorNames":[{"contributorName": "山田, 太郎", "lang": "ja", "nameType": "Personal"}, {"contributorName": "Yamada, Taro", "lang": "en"}], "familyNames": [{"familyName": "山田", "familyNameLang": "ja"}, {"familyName": "Yamada", "familyNameLang": "en"}], "givenNames": [{"givenName": "太郎", "givenNameLang": "ja"}, {"givenName": "Taro", "givenNameLang": "en"}]}
            elif key == "full_name":
                item_names_data = [{"name": "テスト, 太郎", "nameLang": "ja"}]
                target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, prepare_key_map["full_name"], item_names_data)
                assert meta == {"names":[{"name": "山田, 太郎", "nameLang": "ja"}, {"name": "Yamada, Taro", "nameLang": "en"}], "familyNames": [{"familyName": "山田", "familyNameLang": "ja"}, {"familyName": "Yamada", "familyNameLang": "en"}], "givenNames": [{"givenName": "太郎", "givenNameLang": "ja"}, {"givenName": "Taro", "givenNameLang": "en"}]}

    # 54702-11
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestChangeToMeta::test_change_to_meta_target_has_empty_list -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_change_to_meta_target_has_empty_list(self, app, db, records, mocker, prepare_key_map):
        target = {"authorNameInfo": {}, "authorIdInfo": {}, "emailInfo": {}, "affiliationInfo": {}}
        author_prefix = {}
        affiliation_id = {}
        item_names_data = {}

        target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, prepare_key_map, item_names_data)

        assert target_id == None
        assert meta == {}

    # 54702-12
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestChangeToMeta::test_change_to_meta_exists_authorIdInfo -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_change_to_meta_exists_authorIdInfo(self, app, db, records, mocker, prepare_key_map):
        target = {"authorIdInfo": [{"authorIdShowFlg": True, "idType": "-1"}, {"authorIdShowFlg": True, "idType": "1", "authorId": "1"}, {"authorIdShowFlg": True, "idType": "2", "authorId": "0000-0001-0002-0003"}, {"authorIdShowFlg": True, "idType": "3", "authorId": "0000-0001-0002-0003"}, {"authorIdShowFlg": False, "idType": "-1"}]}
        author_prefix = {"1": {"scheme": "WEKO", "url": ""}, "2": {"scheme": "ORCID", "url": "https://orcid.org/##"}, "3": {"scheme": "ISNI", "url": "http://isni.org/isni/"}}
        affiliation_id = {}
        item_names_data = {}
        for key in prepare_key_map:
            target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, prepare_key_map[key], item_names_data)
            assert target_id == '1'
            assert meta == {"nameIdentifiers": [{"nameIdentifierScheme": "WEKO", "nameIdentifier": "1"}, {"nameIdentifierScheme": "ORCID", "nameIdentifier": "0000-0001-0002-0003", "nameIdentifierURI": "https://orcid.org/0000-0001-0002-0003"}, {"nameIdentifierScheme": "ISNI", "nameIdentifier": "0000-0001-0002-0003", "nameIdentifierURI": "http://isni.org/isni/"}]}

    # 54702-13
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestChangeToMeta::test_change_to_meta_exists_emailInfo -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_change_to_meta_exists_emailInfo(self, app, db, records, mocker, prepare_key_map):
        target = {"emailInfo": [{"email": "test@nii.co.jp"}]}
        author_prefix = {}
        affiliation_id = {}
        item_names_data = {}
        for key in prepare_key_map:
            if key == "creator":
                target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, prepare_key_map["creator"], item_names_data)
                assert meta == {"creatorMails": [{"creatorMail": "test@nii.co.jp"}]}
            elif key == "contributor":
                target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, prepare_key_map["contributor"], item_names_data)
                assert meta == {"contributorMails": [{"contributorMail": "test@nii.co.jp"}]}
            elif key == "full_name":
                target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, prepare_key_map["full_name"], item_names_data)
                assert meta == {"mails": [{"mail": "test@nii.co.jp"}]}

    # 54702-14
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestChangeToMeta::test_change_to_meta_exists_affiliationInfo -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_change_to_meta_exists_affiliationInfo(self, app, db, records, mocker, prepare_key_map):
        target = {"affiliationInfo": [{"identifierInfo": [{"identifierShowFlg": False}, {"identifierShowFlg": True, "affiliationIdType": "-1"}, {"identifierShowFlg": True, "affiliationIdType": "1", "affiliationId": "057zh3y96"}, {"identifierShowFlg": True, "affiliationIdType": "2", "affiliationId": "000000012192178X"}, {"identifierShowFlg": True, "affiliationIdType": "3", "affiliationId": "0000000121691048"}], "affiliationNameInfo": [{"affiliationNameShowFlg": False}, {"affiliationNameShowFlg": True, "affiliationName": "The University of Tokyo", "affiliationNameLang": "en"}]}]}
        author_prefix = {}
        affiliation_id = {"1": {"scheme": "ROR", "url": "https://ror.org/##"}, "2": {"scheme": "ISNI", "url": "http://isni.org/isni/"}, "3": {"scheme": "kakenhi", "url": ""}}
        item_names_data = {}
        for key in prepare_key_map:
            if key == "creator":
                target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, prepare_key_map["creator"], item_names_data)
                assert meta == {"creatorAffiliations": [{"affiliationNameIdentifiers": [{"affiliationNameIdentifierScheme": "ROR", "affiliationNameIdentifier": "057zh3y96", "affiliationNameIdentifierURI": "https://ror.org/057zh3y96"}, {"affiliationNameIdentifierScheme": "ISNI", "affiliationNameIdentifier": "000000012192178X", "affiliationNameIdentifierURI": "http://isni.org/isni/"}, {"affiliationNameIdentifierScheme": "kakenhi", "affiliationNameIdentifier": "0000000121691048"}], "affiliationNames": [{"affiliationName": "The University of Tokyo", "affiliationNameLang": "en"}]}]}
            elif key == "contributor":
                target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, prepare_key_map["contributor"], item_names_data)
                assert meta == {"contributorAffiliations": [{"contributorAffiliationNameIdentifiers": [{"contributorAffiliationScheme": "ROR", "contributorAffiliationNameIdentifier": "057zh3y96", "contributorAffiliationURI": "https://ror.org/057zh3y96"}, {"contributorAffiliationScheme": "ISNI", "contributorAffiliationNameIdentifier": "000000012192178X", "contributorAffiliationURI": "http://isni.org/isni/"}, {"contributorAffiliationScheme": "kakenhi", "contributorAffiliationNameIdentifier": "0000000121691048"}], "contributorAffiliationNames": [{"contributorAffiliationName": "The University of Tokyo", "contributorAffiliationNameLang": "en"}]}]}
            elif key == "full_name":
                target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, prepare_key_map["full_name"], item_names_data)
                assert meta == {"affiliations": [{"nameIdentifiers": [{"nameIdentifierScheme": "ROR", "nameIdentifier": "057zh3y96", "nameIdentifierURI": "https://ror.org/057zh3y96"}, {"nameIdentifierScheme": "ISNI", "nameIdentifier": "000000012192178X", "nameIdentifierURI": "http://isni.org/isni/"}, {"nameIdentifierScheme": "kakenhi", "nameIdentifier": "0000000121691048"}], "affiliationNames": [{"affiliationName": "The University of Tokyo", "lang": "en"}]}]}

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateAuthorData -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestUpdateAuthorData:
    # 54702-15
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateAuthorData::test_update_author_data_has_weko_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.PersistentIdentifier.get')
    @patch('weko_deposit.tasks.WekoDeposit.get_record')
    @patch('weko_deposit.tasks.ItemsMetadata.get_record')
    @patch('weko_deposit.tasks._change_to_meta')
    @patch('weko_deposit.tasks.WekoDeposit.update_item_by_task')
    def test_update_author_data_has_weko_id(self, mock_update_item, mock_change_to_meta, mock_get_record, mock_get_record_items, mock_get_pid, app, db, mocker, prepare_key_map):
        mocker.patch("weko_deposit.api.WekoDeposit.update")
        mocker.patch("weko_deposit.api.WekoDeposit.commit")
        # 条件
        item_id = "1"
        record_ids = []
        process_counter = {"success_items": [], "fail_items": []}
        target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1"}]}
        origin_pkid_list = ["12345"]
        key_map = prepare_key_map
        author_prefix = {}
        affiliation_id = {}
        dep_items = {
            "title": "Sample Title",
            "creator": {
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {"nameIdentifierScheme": "ORCID", "nameIdentifier": "12345"},
                            {"nameIdentifierScheme": "WEKO", "nameIdentifier": "12345"}
                        ],
                        "creatorNames": [
                            {"creatorName": "John Doe", "creatorNameLang": "en"}
                        ]
                    }
                ]
            }
        }
                # モックの設定
        mock_get_pid.return_value = MagicMock(object_uuid="uuid1")
        mock_get_record.return_value = WekoDeposit({})
        mock_get_record_items.return_value = WekoDeposit(dep_items)
        mock_change_to_meta.return_value = ("12345", {})
        # 実行
        result = _update_author_data(item_id, record_ids, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id)
        # 期待結果
        mock_change_to_meta.assert_called()
        assert result ==  ('uuid1', ['uuid1'], {'12345'})
        assert process_counter["success_items"] == [{"record_id": "1", "author_ids": [], "message": ""}]

    # 54702-16
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateAuthorData::test_update_author_data_no_weko_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.PersistentIdentifier.get')
    @patch('weko_deposit.tasks.WekoDeposit.get_record')
    @patch('weko_deposit.tasks.ItemsMetadata.get_record')
    @patch('weko_deposit.tasks._change_to_meta')
    @patch('weko_deposit.tasks.WekoDeposit.update_item_by_task')
    def test_update_author_data_no_weko_id(self, mock_update_item, mock_change_to_meta, mock_get_record, mock_get_record_items, mock_get_pid, app, db, mocker, prepare_key_map):
        mocker.patch("weko_deposit.api.WekoDeposit.update")
        mocker.patch("weko_deposit.api.WekoDeposit.commit")
        # 条件
        item_id = "1"
        record_ids = []
        process_counter = {"success_items": [], "fail_items": []}
        target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1"}]}
        origin_pkid_list = ["12345"]
        key_map = prepare_key_map
        author_prefix = {}
        affiliation_id = {}
        dep_items = {
            "title": "Sample Title",
            "creator": {
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {"nameIdentifierScheme": "WEKO", "nameIdentifier": ""}
                        ],
                        "creatorNames": [
                            {"creatorName": "John Doe", "creatorNameLang": "en"}
                        ]
                    }
                ]
            }
        }
                # モックの設定
        mock_get_pid.return_value = MagicMock(object_uuid="uuid1")
        mock_get_record.return_value = WekoDeposit({})
        mock_get_record_items.return_value = WekoDeposit(dep_items)
        mock_change_to_meta.return_value = ("12345", {})
        # 実行
        result = _update_author_data(item_id, record_ids, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id)
        # 期待結果
        assert result ==  ('uuid1', [], {""})
        assert process_counter["success_items"] == [{"record_id": "1", "author_ids": [], "message": ""}]

    # 54702-17
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateAuthorData::test_update_author_data_contributor_weko_id_not_match -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.PersistentIdentifier.get')
    @patch('weko_deposit.tasks.WekoDeposit.get_record')
    @patch('weko_deposit.tasks.ItemsMetadata.get_record')
    @patch('weko_deposit.tasks._change_to_meta')
    @patch('weko_deposit.tasks.WekoDeposit.update_item_by_task')
    def test_update_author_data_contributor_weko_id_not_match(self, mock_update_item, mock_change_to_meta, mock_get_record, mock_get_record_items, mock_get_pid, app, db, mocker, prepare_key_map):
        mocker.patch("weko_deposit.api.WekoDeposit.update")
        mocker.patch("weko_deposit.api.WekoDeposit.commit")
        # 条件
        item_id = "2"
        record_ids = []
        process_counter = {"success_items": [], "fail_items": []}
        target = {"pk_id": "2", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_2"}]}
        origin_pkid_list = ["2"]
        key_map = prepare_key_map
        author_prefix = {}
        affiliation_id = {}
        dep_items = {
            "contributor": {
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {"nameIdentifierScheme": "WEKO", "nameIdentifier": "2"}
                        ],
                        "contributorNames": [
                            {"contributorName": "Jane Smith", "lang": "en"}
                        ]
                    }
                ]
            }
        }

        mock_get_pid.return_value = MagicMock(object_uuid="uuid1")
        mock_get_record.return_value = WekoDeposit({})
        mock_get_record_items.return_value = WekoDeposit(dep_items)
        mock_change_to_meta.return_value = ("12345", {})
        # 実行
        result = _update_author_data(item_id, record_ids, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id)
        # 期待結果
        mock_change_to_meta.assert_called()
        assert result ==  ('uuid1', ['uuid1'], {'12345'})
        assert process_counter["success_items"] == [{"record_id": "2", "author_ids": ["2"], "message": ""}]

    # 54702-18
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateAuthorData::test_update_author_data_full_name_weko_id_not_match -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.PersistentIdentifier.get')
    @patch('weko_deposit.tasks.WekoDeposit.get_record')
    @patch('weko_deposit.tasks.ItemsMetadata.get_record')
    @patch('weko_deposit.tasks._change_to_meta')
    @patch('weko_deposit.tasks.WekoDeposit.update_item_by_task')
    def test_update_author_data_full_name_weko_id_not_match(self, mock_update_item, mock_change_to_meta, mock_get_record, mock_get_record_items, mock_get_pid, app, db, mocker, prepare_key_map):
        mocker.patch("weko_deposit.api.WekoDeposit.update")
        mocker.patch("weko_deposit.api.WekoDeposit.commit")
        # 条件
        item_id = "3"
        record_ids = []
        process_counter = {"success_items": [], "fail_items": []}
        target = {"pk_id": "3", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_3"}]}
        origin_pkid_list = ["1"]
        key_map = prepare_key_map
        author_prefix = {}
        affiliation_id = {}
        dep_items = {
            "title": "Sample Title",
            "full_name":{
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {"nameIdentifierScheme": "WEKO", "nameIdentifier": "3"}
                        ],
                        "names": [
                            {"name": "Jane Smith", "lang": "en"}
                        ]
                    }
                ]
            },
            "rights_holder": {
                "attribute_value_mlt": [
                    {"rightsHolder": "権利者名"}
                ]
            },
            "pubdate": "2025-09-11"
        }

        mock_get_pid.return_value = MagicMock(object_uuid="uuid1")
        mock_get_record.return_value = WekoDeposit({})
        mock_get_record_items.return_value = WekoDeposit(dep_items)

        result = _update_author_data(item_id, record_ids, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id)

        assert result ==  ('uuid1', [], {'3'})
        assert process_counter["success_items"] == [{"record_id": "3", "author_ids": [], "message": ""}]

    # 54702-19
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateAuthorData::test_update_author_data_not_match_key_map -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.PersistentIdentifier.get')
    @patch('weko_deposit.tasks.WekoDeposit.get_record')
    @patch('weko_deposit.tasks.ItemsMetadata.get_record')
    @patch('weko_deposit.tasks._change_to_meta')
    @patch('weko_deposit.tasks.WekoDeposit.update_item_by_task')
    def test_update_author_data_not_match_key_map(self, mock_update_item, mock_change_to_meta, mock_get_record, mock_get_record_items, mock_get_pid, app, db, mocker, prepare_key_map):
        mocker.patch("weko_deposit.api.WekoDeposit.update")
        mocker.patch("weko_deposit.api.WekoDeposit.commit")
        # 条件
        item_id = "1"
        record_ids = []
        process_counter = {"success_items": [], "fail_items": []}
        target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1"}]}
        origin_pkid_list = ["1"]
        key_map = prepare_key_map
        author_prefix = {}
        affiliation_id = {}
        dep_items = {
            "title": "Sample Title",
            "test": {
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {"nameIdentifierScheme": "WEKO", "nameIdentifier": ""}
                        ]
                    }
                ]
            }
        }

        mock_get_pid.return_value = MagicMock(object_uuid="uuid1")
        mock_get_record.return_value = WekoDeposit({})
        mock_get_record_items.return_value = WekoDeposit(dep_items)

        result = _update_author_data(item_id, record_ids, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id)

        assert result ==  ('uuid1', [], set())
        assert process_counter["success_items"] == [{"record_id": "1", "author_ids": [], "message": ""}]

    # 54702-20
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateAuthorData::test_update_author_data_scheme_is_not_WEKO -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.PersistentIdentifier.get')
    @patch('weko_deposit.tasks.WekoDeposit.get_record')
    @patch('weko_deposit.tasks.ItemsMetadata.get_record')
    @patch('weko_deposit.tasks._change_to_meta')
    @patch('weko_deposit.tasks.WekoDeposit.update_item_by_task')
    def test_update_author_data_scheme_is_not_WEKO(self, mock_update_item, mock_change_to_meta, mock_get_record, mock_get_record_items, mock_get_pid, app, db, mocker, prepare_key_map):
        mocker.patch("weko_deposit.api.WekoDeposit.update")
        mocker.patch("weko_deposit.api.WekoDeposit.commit")
        # 条件
        item_id = "1"
        record_ids = []
        process_counter = {"success_items": [], "fail_items": []}
        target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1"}]}
        origin_pkid_list = ["1"]
        key_map = prepare_key_map
        author_prefix = {}
        affiliation_id = {}
        dep_items = {
            "title": "Sample Title",
            "creator": {
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {"nameIdentifierScheme": "ORCID", "nameIdentifier": ""}
                        ],
                        "creatorNames": [
                            {"creatorName": "John Doe", "creatorNameLang": "en"}
                        ]
                    }
                ]
            }
        }

        mock_get_pid.return_value = MagicMock(object_uuid="uuid1")
        mock_get_record.return_value = WekoDeposit({})
        mock_get_record_items.return_value = WekoDeposit(dep_items)

        result = _update_author_data(item_id, record_ids, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id)

        assert result ==  ('uuid1', [], set())
        assert process_counter["success_items"] == [{"record_id": "1", "author_ids": [], "message": ""}]

    # 54702-29
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateAuthorData::test_update_author_data_pid_not_exist -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.PersistentIdentifier.get')
    @patch('weko_deposit.tasks.WekoDeposit.get_record')
    @patch('weko_deposit.tasks.ItemsMetadata.get_record')
    def test_update_author_data_pid_not_exist(mock_get_record_items, mock_get_record, mock_get_pid, app, db):
        # 条件
        item_id = "1"
        record_ids = []
        process_counter = {"success_items": [], "fail_items": []}
        target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1"}]}
        origin_pkid_list = ["1"]
        key_map = {"creator": {}, "contributor": {}, "full_name": {}}
        author_prefix = {}
        affiliation_id = {}
        # モックの設定
        mock_get_pid.side_effect = PIDDoesNotExistError("pid_type", "pid_value")
        # 実行
        result = _update_author_data(item_id, record_ids, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id)
        # 期待結果
        assert result == (None, set(), {})
        assert process_counter["fail_items"] == [{"record_id": "1", "author_ids": [], "message": "PID 1 does not exist."}]

    # 54702-30
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateAuthorData::test_update_author_data_exception -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.PersistentIdentifier.get')
    @patch('weko_deposit.tasks.WekoDeposit.get_record')
    @patch('weko_deposit.tasks.ItemsMetadata.get_record')
    def test_update_author_data_exception(mock_get_record_items, mock_get_record, mock_get_pid, app, db):
        # 条件
        item_id = "1"
        record_ids = []
        process_counter = {"success_items": [], "fail_items": []}
        target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1"}]}
        origin_pkid_list = ["1"]
        key_map = {"creator": {}, "contributor": {}, "full_name": {}}
        author_prefix = {}
        affiliation_id = {}
        # モックの設定
        mock_get_pid.side_effect = Exception("Test Exception")
        # 実行
        result = _update_author_data(item_id, record_ids, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id)
        # 期待結果
        assert result == (None, set(), {})
        assert process_counter["fail_items"] == [{"record_id": "1", "author_ids": [], "message": "Test Exception"}]

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::test_extract_pdf_and_update_file_contents -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_extract_pdf_and_update_file_contents(app, db, location, caplog):
    app.config["TIKA_JAE_FILE_PARH"] = "/code/tika/tika-app-2.6.0.jar"
    indexer = WekoIndexer()
    indexer.get_es_index()

    app.config["WEKO_DEPOSIT_FILESIZE_LIMIT"] = 100 * 1024 # 1KB
    rec_uuid = uuid.uuid4()
    pdf_files, deposit = create_record_with_pdf(rec_uuid,1)
    test_data = {}
    for filename, file in pdf_files.items():
        test_data[filename] = {
            "uri":file.obj.file.uri,
            "size":file.obj.file.size
        }
    extract_pdf_and_update_file_contents(test_data, deposit.id)
    result = indexer.client.get(
        index=app.config["INDEXER_DEFAULT_INDEX"],
        doc_type="item-v1.0.0",
        id=deposit.id
    )

    attachments = [r["attachment"] for r in result["_source"]["content"]]
    test = [
        {"content":"test file page1   test file page2   test file page3   test file page4   test file page5   test file page6   test file page7   test file page8    test file page9   test file page10   test file page11   test file page12   test file page13   test file page14   test file page15   test file page16   test file page17   test file page18   test file page19   test file page20   test file page21   test file page22   test file page23   test file page24   test file page25   test file page26   test file page27   test file page28   test file page29   test file page30   test file page31   test file page32   test file page33   test file page34   test file page35   test file page36   test file page37   test file page38   test file page39   test file page40 test file page1   test file page2   test file page3   test file page4   test file page5   test file page6   test file page7   test file page8    test file page9   test file page10   test file page11   test file page12   test file page13   test file page14   test file page15   test file page16   test file page17   test file page18   test file page19   test file page20   test file page21   test file page22   test file page23   test file page24   test file page25   test file page26   test file page27   test file page28   test file page29   test file page30   test file page31   test file page32   test file page33   test file page34   test file page35   test file page36   test file page37   test file page38   test file page39   test file page40 test file page1   test file page2   test file page3   test file page4   test file page5   test file page6   test file page7   test file page8    test file page9   test file page10   test file page11   test file page12   test file page13   test file page14   test file page15   test file page16   test file page17   test file page18   test file page19   test file page20   test file page21   test file page22   test file page23   test file page24   test file page25   test file page26   test file page27   test file page28   test file page29   test file page30   test file page31   test file page32   test file page33   test file page34   test file page35   test file page36   test file page37   test file page38   test file page39   test file page40 test file page1   test file page2   test file page3   test file page4   test file page5   test file page6   test file page7   test file page8    test file page9   test file page10   test file page11   test file page12   test file page13   test file page14   test file page15   test file page16   test file page17   test file page18   test file page19   test file page20   test file page21   test file page22   test file page23   test file page24   test file page25   test file page26   test file page27   test file page28   test file page29   test file page30   test file page31   test file page32   test file page33   test file page34   test file page35   test file page36   "}, # big pdf
        {"content":"これはテストファイルです  This is test file.  "}, # small pdf
        {}, # not pdf
        {"content":""}, # not exist pdf
    ]

    assert attachments == test
    assert "Resource not found: b'not_exist_dir1'" in caplog.text
    caplog.clear()

    # not exist es data
    rec_uuid = uuid.uuid4()
    pdf_files, deposit = create_record_with_pdf(rec_uuid,2)
    test_data = {}
    for filename, file in pdf_files.items():
        test_data[filename] = {
            "uri":file.obj.file.uri,
            "size":file.obj.file.size
        }
    indexer.client.delete(
        index=app.config["INDEXER_DEFAULT_INDEX"],
        doc_type="item-v1.0.0",
        id=deposit.id
    )

    extract_pdf_and_update_file_contents(test_data, deposit.id)
    assert f"The document targeted for content update({deposit.id}) does not exist." in caplog.text
    caplog.clear()

    # not jar file
    tika_path = os.environ.get("TIKA_JAR_FILE_PATH")
    os.environ["TIKA_JAR_FILE_PATH"] = "not_exist_path"
    rec_uuid = uuid.uuid4()
    pdf_files, deposit = create_record_with_pdf(rec_uuid,3)
    test_data = {}
    for filename, file in pdf_files.items():
        test_data[filename] = {
            "uri":file.obj.file.uri,
            "size":file.obj.file.size
        }
    with pytest.raises(Exception) as e:
        extract_pdf_and_update_file_contents(test_data, deposit.id)
    assert str(e.value) == f"not exist tika jar file."
    result = indexer.client.get(
        index=app.config["INDEXER_DEFAULT_INDEX"],
        doc_type="item-v1.0.0",
        id=deposit.id
    )

    attachments = [r["attachment"] for r in result["_source"]["content"]]
    test = [
        {"content":""}, # small pdf
        {"content":""}, # big pdf
        {}, # not pdf
        {"content":""}, # not exist pdf
    ]

    assert attachments == test
    caplog.clear()

    # raise tika error
    os.environ["TIKA_JAR_FILE_PATH"] = tika_path
    rec_uuid = uuid.uuid4()
    pdf_files, deposit = create_record_with_pdf(rec_uuid,4)
    test_data = {}
    for filename, file in pdf_files.items():
        test_data[filename] = {
            "uri":file.obj.file.uri,
            "size":file.obj.file.size
        }
    from mock import MagicMock
    mock_run = MagicMock()
    mock_run.returncode.return_value = 1
    mock_run.stderr.decode.return_value="test_error"
    with patch("weko_deposit.tasks.subprocess.run", return_value = mock_run):
        extract_pdf_and_update_file_contents(test_data, deposit.id)
    result = indexer.client.get(
        index=app.config["INDEXER_DEFAULT_INDEX"],
        doc_type="item-v1.0.0",
        id=deposit.id
    )

    attachments = [r["attachment"] for r in result["_source"]["content"]]
    test = [
        {"content":""}, # small pdf
        {"content":""}, # big pdf
        {}, # not pdf
        {"content":""}, # not exist pdf
    ]

    assert attachments == test
    assert "test_error" in caplog.text
    caplog.clear()

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::test_update_file_content -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_update_file_content(app, db, location):
    indexer = WekoIndexer()
    indexer.get_es_index()
    rec_uuid = uuid.uuid4()
    pdf_files, deposit = create_record_with_pdf(rec_uuid,1)

    file_datas = {}
    for filename, data in pdf_files.items():
        file_datas[filename] = f"this is {filename}"

    update_file_content(rec_uuid,file_datas)

    result = indexer.client.get(
        index=app.config["INDEXER_DEFAULT_INDEX"],
        doc_type="item-v1.0.0",
        id=deposit.id
    )
    attachments = [r["attachment"] for r in result["_source"]["content"]]
    test = [
        {"content":"this is test_file_1.2M.pdf"},
        {"content":"this is test_file_82K.pdf"},
        {},
        {"content":"this is not_exist.pdf"},
    ]
    assert attachments == test