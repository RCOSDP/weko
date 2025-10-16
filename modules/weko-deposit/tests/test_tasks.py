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
import types
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
from sqlalchemy.exc import SQLAlchemyError
import pytest
from mock import patch
from weko_deposit.tasks import _get_author_prefix, _get_affiliation_id, _process, _change_to_meta, _update_author_data, update_items_by_authorInfo
from weko_authors.models import AuthorsPrefixSettings

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateItemsByAuthorInfo -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestUpdateItemsByAuthorInfo:
    def test_update_items_by_authorInfo_success(self,  db, app):
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
            force_change = False

            update_items_by_authorInfo(user_id, target, origin_pkid_list, origin_id_list, update_gather_flg, force_change)

            mock_process.assert_called()
            mock_get_origin_data.assert_called()
            mock_update_db_es_data.assert_called()
            mock_delete_cache_data.assert_called()
            mock_update_cache_data.assert_called()

    # Test for update_gather_flg = False and 「if not next」
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
            force_change = False

            update_items_by_authorInfo(user_id, target, origin_pkid_list, origin_id_list, update_gather_flg, force_change)

            mock_process.assert_called()
            mock_get_origin_data.assert_not_called()
            mock_update_db_es_data.assert_not_called()
            mock_delete_cache_data.assert_not_called()
            mock_update_cache_data.assert_not_called()

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
            force_change = False

            update_items_by_authorInfo(user_id, target, origin_pkid_list, origin_id_list, update_gather_flg, force_change)

            mock_process.assert_called()
            mock_db_rollback.assert_called()
            mock_retry.assert_called()

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestGetAuthorPrefix -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestGetAuthorPrefix:
    def test_get_author_prefix_with_data(self, db):
        # 条件: AuthorsPrefixSettings テーブルにデータが存在する
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

        # 期待結果: 関数はデータを含む辞書を返す
        expected_result = {'1': {'scheme': 'WEKO', 'url': None},
                        '2': {'scheme': 'ORCID', 'url': 'https://orcid.org/##'},
                        '3': {'scheme': 'CiNii', 'url': 'https://ci.nii.ac.jp/author/'}}
        assert _get_author_prefix() == expected_result

    def test_get_author_prefix_no_data(self, db):
        # 条件: AuthorsPrefixSettings テーブルにデータが存在しない
        # 期待結果: 関数は空の辞書を返す
        assert _get_author_prefix() == {}

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestGetAffiliaitonId -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestGetAffiliaitonId:
# テストケース1: 正常系 - データが存在する場合
    def test_get_affiliation_id_with_data(self, db):
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

        expected_result = {'1': {'scheme': 'ISNI', 'url': 'http://www.isni.org/isni/##'},
                        '2': {'scheme': 'GRID', 'url': 'https://www.grid.ac/institutes/'},
                        '3': {'scheme': 'Ringgold', 'url': None}}
        assert _get_affiliation_id() == expected_result

    # テストケース2: 正常系 - データが存在しない場合
    def test_get_affiliation_id_no_data(self, db):
        assert _get_affiliation_id() == {}

import uuid
from weko_deposit.api import WekoDeposit
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestProcess -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestProcess:

    class MockWekoDeposit:
        def __init__(self):
            self.control_number = '1'

        def get_record(self):
            return self

        def update_author_link_and_weko_link(self):
            pass

    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestProcess::test_process_with_data -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.RecordsSearch')
    @patch('weko_deposit.tasks._update_author_data')
    @patch('weko_deposit.tasks.db.session.commit')
    def test_process_with_data(self, mock_commit, mock_update_author_data, mock_records_search, app, db, mocker):
        mocker.patch('invenio_indexer.api.RecordIndexer.bulk_index')
        mocker.patch('invenio_indexer.api.RecordIndexer.process_bulk_queue')
        with patch('weko_deposit.api.WekoDeposit.get_record', return_value = WekoDeposit({})):
            mocker.patch('weko_deposit.api.WekoDeposit.update_author_link_and_weko_link')
            # 条件
            data_size = 10
            data_from = 0
            process_counter = {}
            target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1", "authorIdShowFlg": "true"}]}
            origin_pkid_list = ["1"]
            key_map = {...}
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
            mock_update_author_data.return_value = (uuid1, [uuid1], set(), {})

            # 実行
            result = _process(data_size, data_from, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id, force_change)

            # 期待結果
            assert result == (1, False)

            # if data_total > data_size + data_from
            mock_records_search.return_value.update_from_dict.return_value.execute.return_value.to_dict.return_value = {
                'hits': {
                    'hits': [{'_source': {'control_number': '1'}}],
                    'total': 11
                }
            }
            result = _process(data_size, data_from, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id, force_change)
            assert result == (1, True)



# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestProcess::test_process_no_data -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.RecordsSearch')
    @patch('weko_deposit.tasks._update_author_data')
    @patch('weko_deposit.tasks.db.session.commit')
    def test_process_no_data(self, mock_commit, mock_update_author_data, mock_records_search, app, db, mocker):
        mocker.patch('invenio_indexer.api.RecordIndexer.bulk_index')
        mocker.patch('invenio_indexer.api.RecordIndexer.process_bulk_queue')
        # 条件
        data_size = 10
        data_from = 0
        process_counter = {}
        target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1", "authorIdShowFlg": "true"}]}
        origin_pkid_list = ["1"]
        key_map = {...}
        author_prefix = {...}
        affiliation_id = {...}
        force_change = False

        # モックの設定
        mock_records_search.return_value.update_from_dict.return_value.execute.return_value.to_dict.return_value = {
            'hits': {
                'hits': [],
                'total': 0
            }
        }

        # 実行
        result = _process(data_size, data_from, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id, force_change)

        # 期待結果
        assert result == (0, False)

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestProcess::test_process_first_retry_error -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.RecordsSearch')
    @patch('weko_deposit.tasks._update_author_data')
    @patch('weko_deposit.tasks.db.session.commit')
    def test_process_first_retry_error(self, mock_commit, mock_update_author_data, mock_records_search, app):
        # 条件
        data_size = 10
        data_from = 0
        process_counter = {}
        target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1", "authorIdShowFlg": "true"}]}
        origin_pkid_list = ["1"]
        key_map = {...}
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
        mock_update_author_data.return_value = ('uuid', ['uuid'], set(), {})

        # 実行と期待結果
        with pytest.raises(Exception):
            _process(data_size, data_from, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id, force_change)

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestProcess::test_process_second_retry_error -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.RecordsSearch')
    @patch('weko_deposit.tasks._update_author_data')
    @patch('weko_deposit.tasks.db.session.commit')
    def test_process_second_retry_error(self, mock_commit, mock_update_author_data, mock_records_search, app, db, mocker):
        mocker.patch('invenio_indexer.api.RecordIndexer.bulk_index')
        mocker.patch('invenio_indexer.api.RecordIndexer.process_bulk_queue')
        # 条件
        data_size = 10
        data_from = 0
        process_counter = {}
        target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1", "authorIdShowFlg": "true"}]}
        origin_pkid_list = ["1"]
        key_map = {...}
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
        mock_update_author_data.return_value = (uuid1, [uuid1], set(), {})

        # 実行と期待結果
        with pytest.raises(Exception):
            _process(data_size, data_from, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id, force_change)


# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestChangeToMeta -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestChangeToMeta:
    # テストケース1: 正常系 - 強制変更フラグがオフの場合
    def test_change_to_meta_force_change_false(self, app, db):
        # 条件
        target = {
            "authorIdInfo": [
                {"idType": "1", "authorId": "weko_id_1", "authorIdShowFlg": "true"}
            ]
        }
        author_prefix = {
            "1": {"scheme": "WEKO", "url": "https://weko.example.com/##"}
        }
        affiliation_id = {}
        key_map = {
            "id_scheme_key": "nameIdentifierScheme",
            "id_key": "nameIdentifier",
            "id_uri_key": "nameIdentifierURI",
            "ids_key": "nameIdentifiers"
        }
        force_change = False

        # 期待結果
        expected_target_id = "weko_id_1"
        expected_meta = {
            "nameIdentifiers": [
                {
                    "nameIdentifierScheme": "WEKO",
                    "nameIdentifier": "weko_id_1",
                    "nameIdentifierURI": "https://weko.example.com/weko_id_1"
                }
            ]
        }

        # 実行と検証
        target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, key_map, force_change)
        assert target_id == expected_target_id
        assert meta == expected_meta

    # テストケース2: 正常系 - 強制変更フラグがオンの場合
    def test_change_to_meta_force_change_true1(self, app, db):
        # 条件
        target = {
            "authorIdInfo": [
                {"idType": "1", "authorId": "weko_id_1", "authorIdShowFlg": "true"}
            ],
            "authorNameInfo": [
                {"nameShowFlg": "true", "familyName": "Test", "firstName": "User", "language": "en"}
            ],
            "emailInfo": [
                {"email": "test@example.com"}
            ],
            "affiliationInfo": [
                {
                    "identifierInfo": [
                        {"identifierShowFlg": "true", "affiliationIdType": "1", "affiliationId": "aff_id_1"}
                    ],
                    "affiliationNameInfo": [
                        {"affiliationNameShowFlg": "true", "affiliationName": "Test Affiliation", "affiliationNameLang": "en"}
                    ]
                }
            ]
        }
        author_prefix = {
            "1": {"scheme": "WEKO", "url": "https://weko.example.com/##"}
        }
        affiliation_id = {
            "1": {"scheme": "Affiliation", "url": "https://affiliation.example.com/##"}
        }
        key_map = {
            "id_scheme_key": "nameIdentifierScheme",
            "id_key": "nameIdentifier",
            "id_uri_key": "nameIdentifierURI",
            "ids_key": "nameIdentifiers",
            "fnames_key": "familyNames",
            "fname_key": "familyName",
            "fname_lang_key": "familyNameLang",
            "gnames_key": "givenNames",
            "gname_key": "givenName",
            "gname_lang_key": "givenNameLang",
            "names_key": "names",
            "name_key": "name",
            "name_lang_key": "nameLang",
            "mails_key": "mails",
            "mail_key": "mail",
            "affiliations_key": "affiliations",
            "affiliation_ids_key": "nameIdentifiers",
            "affiliation_id_key": "nameIdentifier",
            "affiliation_id_uri_key": "nameIdentifierURI",
            "affiliation_id_scheme_key": "nameIdentifierScheme",
            "affiliation_names_key": "affiliationNames",
            "affiliation_name_key": "affiliationName",
            "affiliation_name_lang_key": "affiliationNameLang"
        }
        force_change = True

        # 期待結果
        expected_target_id = "weko_id_1"
        expected_meta = {
            "nameIdentifiers": [
                {
                    "nameIdentifierScheme": "WEKO",
                    "nameIdentifier": "weko_id_1",
                    "nameIdentifierURI": "https://weko.example.com/weko_id_1"
                }
            ],
            "familyNames": [
                {"familyName": "Test", "familyNameLang": "en"}
            ],
            "givenNames": [
                {"givenName": "User", "givenNameLang": "en"}
            ],
            "names": [
                {"name": "Test, User", "nameLang": "en"}
            ],
            "mails": [
                {"mail": "test@example.com"}
            ],
            "affiliations": [
                {
                    "nameIdentifiers": [
                        {
                            "nameIdentifierScheme": "Affiliation",
                            "nameIdentifier": "aff_id_1",
                            "nameIdentifierURI": "https://affiliation.example.com/aff_id_1"
                        }
                    ],
                    "affiliationNames": [
                        {"affiliationName": "Test Affiliation", "affiliationNameLang": "en"}
                    ]
                }
            ]
        }

        # 実行と検証
        target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, key_map, force_change)
        assert target_id == expected_target_id
        assert meta == expected_meta

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestChangeToMeta::test_change_to_meta_force_change_true2 -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    # テストケース3: 正常系 - 強制変更フラグがオンの場合,URLに♯♯なし
    def test_change_to_meta_force_change_true2(self, app, db):
        # 条件
        target = {
            "authorIdInfo": [
                {"idType": "1", "authorId": "weko_id_1", "authorIdShowFlg": "true"}
            ],
            "authorNameInfo": [
                {"nameShowFlg": "true", "familyName": "Test", "firstName": "User", "language": "en"}
            ],
            "emailInfo": [
                {"email": "test@example.com"}
            ],
            "affiliationInfo": [
                {
                    "identifierInfo": [
                        {"identifierShowFlg": "true", "affiliationIdType": "1", "affiliationId": "aff_id_1"}
                    ],
                    "affiliationNameInfo": [
                        {"affiliationNameShowFlg": "true", "affiliationName": "Test Affiliation", "affiliationNameLang": "en"}
                    ]
                }
            ]
        }
        author_prefix = {
            "1": {"scheme": "WEKO", "url": "https://weko.example.com/"}
        }
        affiliation_id = {
            "1": {"scheme": "Affiliation", "url": "https://affiliation.example.com/"}
        }
        key_map = {
            "id_scheme_key": "nameIdentifierScheme",
            "id_key": "nameIdentifier",
            "id_uri_key": "nameIdentifierURI",
            "ids_key": "nameIdentifiers",
            "fnames_key": "familyNames",
            "fname_key": "familyName",
            "fname_lang_key": "familyNameLang",
            "gnames_key": "givenNames",
            "gname_key": "givenName",
            "gname_lang_key": "givenNameLang",
            "names_key": "names",
            "name_key": "name",
            "name_lang_key": "nameLang",
            "mails_key": "mails",
            "mail_key": "mail",
            "affiliations_key": "affiliations",
            "affiliation_ids_key": "nameIdentifiers",
            "affiliation_id_key": "nameIdentifier",
            "affiliation_id_uri_key": "nameIdentifierURI",
            "affiliation_id_scheme_key": "nameIdentifierScheme",
            "affiliation_names_key": "affiliationNames",
            "affiliation_name_key": "affiliationName",
            "affiliation_name_lang_key": "affiliationNameLang"
        }
        force_change = True

        # 期待結果
        expected_target_id = "weko_id_1"
        expected_meta = {'familyNames': [{'familyName': 'Test', 'familyNameLang': 'en'}],
                    'givenNames': [{'givenName': 'User', 'givenNameLang': 'en'}],
                    'names': [{'name': 'Test, User', 'nameLang': 'en'}], 'nameIdentifiers':
                        [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': 'weko_id_1',
                        'nameIdentifierURI': 'https://weko.example.com/'}],
                        'mails': [{'mail': 'test@example.com'}],
                        'affiliations': [{'nameIdentifiers':
                            [{'nameIdentifierScheme': 'Affiliation', 'nameIdentifier': 'aff_id_1',
                            'nameIdentifierURI': 'https://affiliation.example.com/'}], 'affiliationNames':
                    [{'affiliationName': 'Test Affiliation', 'affiliationNameLang': 'en'}]}]}

        # 実行と検証
        target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, key_map, force_change)
        assert target_id == expected_target_id
        assert meta == expected_meta


    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestChangeToMeta::test_change_to_meta_other_pattern -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    # テストケース4: 正常系 - 表示フラグがオフの場合
    def test_change_to_meta_other_pattern(self, app, db):
        # 条件
        target = {
            "authorIdInfo": [
                {"idType": "1", "authorId": "weko_id_1", "authorIdShowFlg": "false"}
            ],
            "authorNameInfo": [
                {"nameShowFlg": "false", "familyName": "Test", "firstName": "User", "language": "en"}
            ],
            "emailInfo": [
                {"email": "test@example.com"}
            ],
            "affiliationInfo": [
                {
                    "identifierInfo": [
                        {"identifierShowFlg": "false", "affiliationIdType": "1", "affiliationId": "aff_id_1"}
                    ],
                    "affiliationNameInfo": [
                        {"affiliationNameShowFlg": "false", "affiliationName": "Test Affiliation", "affiliationNameLang": "en"}
                    ]
                }
            ]
        }
        author_prefix = {
            "1": {"scheme": "WEKO", "url": "https://weko.example.com/"}
        }
        affiliation_id = {
            "1": {"scheme": "Affiliation", "url": "https://affiliation.example.com/"}
        }
        key_map = {
            "id_scheme_key": "nameIdentifierScheme",
            "id_key": "nameIdentifier",
            "id_uri_key": "nameIdentifierURI",
            "ids_key": "nameIdentifiers",
            "fnames_key": "familyNames",
            "fname_key": "familyName",
            "fname_lang_key": "familyNameLang",
            "gnames_key": "givenNames",
            "gname_key": "givenName",
            "gname_lang_key": "givenNameLang",
            "names_key": "names",
            "name_key": "name",
            "name_lang_key": "nameLang",
            "mails_key": "mails",
            "mail_key": "mail",
            "affiliations_key": "affiliations",
            "affiliation_ids_key": "nameIdentifiers",
            "affiliation_id_key": "nameIdentifier",
            "affiliation_id_uri_key": "nameIdentifierURI",
            "affiliation_id_scheme_key": "nameIdentifierScheme",
            "affiliation_names_key": "affiliationNames",
            "affiliation_name_key": "affiliationName",
            "affiliation_name_lang_key": "affiliationNameLang"
        }
        force_change = True

        # 期待結果
        expected_target_id = "weko_id_1"
        expected_meta = {'mails': [{'mail': 'test@example.com'}], 'affiliations': [{'nameIdentifiers': [], 'affiliationNames': []}]}
        # 実行と検証
        target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, key_map, force_change)
        assert target_id == expected_target_id
        assert meta == expected_meta


    # テストケース5: 異常系 - targetが空の場合
    def test_change_to_meta_empty_target(self, app, db):
        # 条件
        target = {}
        author_prefix = {}
        affiliation_id = {}
        key_map = {}
        force_change = False

        # 期待結果
        expected_target_id = None
        expected_meta = {}

        # 実行と検証
        target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, key_map, force_change)
        assert target_id == expected_target_id
        assert meta == expected_meta

    # テストケース6: 異常系 - authorIdInfoが空の場合
    def test_change_to_meta_empty_authorIdInfo(self, app, db):
        # 条件
        target = {
            "authorIdInfo": []
        }
        author_prefix = {}
        affiliation_id = {}
        key_map = {}
        force_change = False

        # 期待結果
        expected_target_id = None
        expected_meta = {}

        # 実行と検証
        target_id, meta = _change_to_meta(target, author_prefix, affiliation_id, key_map, force_change)
        assert target_id == expected_target_id
        assert meta == expected_meta


from weko_records.api import ItemsMetadata
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateAuthorData -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestUpdateAuthorData:
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateAuthorData::test_update_author_data_success -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.PersistentIdentifier.get')
    @patch('weko_deposit.tasks.WekoDeposit.get_record')
    @patch('weko_deposit.tasks.ItemsMetadata.get_record')
    @patch('weko_deposit.tasks._change_to_meta')
    @patch('weko_deposit.tasks.WekoDeposit.update_item_by_task')
    def test_update_author_data_success(self, mock_update_item, mock_change_to_meta, mock_get_record, mock_get_record_items, mock_get_pid, app, db, mocker):
        mocker.patch("weko_deposit.api.WekoDeposit.update")
        mocker.patch("weko_deposit.api.WekoDeposit.commit")
        # 条件
        item_id = "1"
        record_ids = []
        process_counter = {"success_items": [], "fail_items": []}
        target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1"}]}
        origin_pkid_list = ["1"]
        key_map = {"creator": {}, "contributor": {}, "full_name": {}}
        author_prefix = {}
        affiliation_id = {}
        force_change = False
        dep_items = {
            "title": "Sample Title",
            "test":{
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {"nameIdentifierScheme": "ORCID", "nameIdentifier": "0000-0002-1825-0097"}
                        ],
                        "test": [
                            {"contributorName": "Jane Smith", "lang": "en"}
                        ]
                    }
                ]
            },
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
            },
            "contributor": {
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {"nameIdentifierScheme": "ORCID", "nameIdentifier": "0000-0002-1825-0097"}
                        ],
                        "contributorNames": [
                            {"contributorName": "Jane Smith", "lang": "en"}
                        ]
                    }
                ]
            },
            "names":{
                "attribute_value_mlt": [
                    {
                        "nameIdentifiers": [
                            {"nameIdentifierScheme": "ORCID", "nameIdentifier": "0000-0002-1825-0097"}
                        ],
                        "names": [
                            {"contributorName": "Jane Smith", "lang": "en"}
                        ]
                    }
                ]
            },
            "weko_link": {
                "1": "12345"
            }
        }

        # モックの設定
        mock_get_pid.return_value = MagicMock(object_uuid="uuid1")
        mock_get_record.return_value = WekoDeposit({})
        mock_get_record_items.return_value = WekoDeposit(dep_items)
        mock_change_to_meta.return_value = ("weko_id_1", {})

        # 実行
        result = _update_author_data(item_id, record_ids, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id, force_change)
        # 期待結果
        assert result ==  ('uuid1', ['uuid1'], {'1'}, {'1': 'weko_id_1'})
        assert process_counter["success_items"] == [{"record_id": "1", "author_ids": [], "message": ""}]

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::TestUpdateAuthorData::test_update_author_data_pid_not_exist -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    @patch('weko_deposit.tasks.PersistentIdentifier.get')
    @patch('weko_deposit.tasks.WekoDeposit.get_record')
    @patch('weko_deposit.tasks.ItemsMetadata.get_record')
    def test_update_author_data_pid_not_exist(self, mock_get_record_items, mock_get_record, mock_get_pid, app, db):
        # 条件
        item_id = "1"
        record_ids = []
        process_counter = {"success_items": [], "fail_items": []}
        target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1"}]}
        origin_pkid_list = ["1"]
        key_map = {"creator": {}, "contributor": {}, "full_name": {}}
        author_prefix = {}
        affiliation_id = {}
        force_change = False

        # モックの設定
        mock_get_pid.side_effect = PIDDoesNotExistError("pid_type", "pid_value")

        # 実行
        result = _update_author_data(item_id, record_ids, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id, force_change)

        # 期待結果
        assert result == (None, set(), {})
        assert process_counter["fail_items"] == [{"record_id": "1", "author_ids": [], "message": "PID 1 does not exist."}]

    @patch('weko_deposit.tasks.PersistentIdentifier.get')
    @patch('weko_deposit.tasks.WekoDeposit.get_record')
    @patch('weko_deposit.tasks.ItemsMetadata.get_record')
    def test_update_author_data_exception(self, mock_get_record_items, mock_get_record, mock_get_pid, app, db):
        # 条件
        item_id = "1"
        record_ids = []
        process_counter = {"success_items": [], "fail_items": []}
        target = {"pk_id": "1", "authorIdInfo": [{"idType": "1", "authorId": "weko_id_1"}]}
        origin_pkid_list = ["1"]
        key_map = {"creator": {}, "contributor": {}, "full_name": {}}
        author_prefix = {}
        affiliation_id = {}
        force_change = False

        # モックの設定
        mock_get_pid.side_effect = Exception("Test Exception")

        # 実行
        result = _update_author_data(item_id, record_ids, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id, force_change)

        # 期待結果
        assert result == (None, set(), {})
        assert process_counter["fail_items"] == [{"record_id": "1", "author_ids": [], "message": "Test Exception"}]


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
    indexer = WekoIndexer()
    indexer.get_es_index()

    app.config["WEKO_DEPOSIT_FILESIZE_LIMIT"] = 100 * 1024 # 1KB
    rec_uuid = uuid.uuid4()
    pdf_files, deposit = create_record_with_pdf(rec_uuid,1)
    mock_pdf_msg = "This is test pdf"
    mock_tika_msg = "this is test word"
    test_data = {}
    num_pdf = 0
    num_not_pdf = 0
    test_file_data = {}
    
    # Create the number of pdf files to analyze, the number of tika files, 
    # and the value to be passed to the method to update es
    for filename, info in pdf_files.items():
        file = info.get("file")
        if file.obj.mimetype == 'application/pdf':
            
            is_pdf = True
            if filename == "not_exist.pdf":
                test_file_data[filename] = ""
            else:
                test_file_data[filename] = mock_pdf_msg
                num_pdf += 1
        else:
            num_not_pdf += 1
            is_pdf = False
            test_file_data[filename] = mock_tika_msg
        test_data[filename] = {
            "uri":file.obj.file.uri,
            "size":file.obj.file.size,
            "is_pdf": is_pdf
        }
        
    with patch("weko_deposit.utils.extract_text_from_pdf", return_value=mock_pdf_msg) as mock_pdf, \
        patch("weko_deposit.utils.extract_text_with_tika", return_value=mock_tika_msg) as mock_tika:
        with patch("weko_deposit.tasks.update_file_content") as mock_update:
            extract_pdf_and_update_file_contents(test_data, deposit.id)
            assert mock_pdf.call_count == num_pdf
            assert mock_tika.call_count == num_not_pdf
            mock_update.assert_called_with(rec_uuid,test_file_data)
            
            # Check if temporary files have been deleted
            for call in mock_pdf.call_args_list:
                args, _ = call
                filepath = args[0]
                assert os.path.exists(filepath) == False

            for call in mock_tika.call_args_list:
                args, _ = call
                filepath = args[0]
                assert os.path.exists(filepath) == False
                
            assert "Resource not found: b'not_exist_dir1'" in caplog.text
            caplog.clear()
            
            from fs.errors import ResourceNotFoundError
            # error in extract_text_from_pdf
            # Check if temporary files have been deleted
            with patch("weko_deposit.utils.extract_text_from_pdf", side_effect=FileNotFoundError("test exception")) as mock_pdf,\
                    patch("weko_deposit.utils.extract_text_with_tika", side_effect=ResourceNotFoundError("test_exception")) as mock_tika:
                extract_pdf_and_update_file_contents(test_data, deposit.id)
                assert mock_pdf.call_count == num_pdf
                assert "test exception" in caplog.text
                caplog.clear()
                
                for call in mock_pdf.call_args_list:
                    args, _ = call
                    filepath = args[0]
                    assert os.path.exists(filepath) == False

                for call in mock_tika.call_args_list:
                    args, _ = call
                    filepath = args[0]
                    assert os.path.exists(filepath) == False

        from elasticsearch.exceptions import NotFoundError, ConflictError
        # raise ConflictError in update_file_content
        with patch("weko_deposit.tasks.update_file_content", side_effect=ConflictError()) as mock_update:
            extract_pdf_and_update_file_contents(test_data, deposit.id)
            assert mock_update.call_count == 3 # retry 3 times
            assert f"Failed to update file content after 3 attempts. record_uuid: {rec_uuid}" in caplog.text
            caplog.clear()
        # raise ConflictError in update_file_content
        with patch("weko_deposit.tasks.update_file_content", side_effect=NotFoundError()) as mock_update:
            extract_pdf_and_update_file_contents(test_data, deposit.id)
            assert mock_update.call_count == 3 # retry 3 times
            assert f"Failed to update file content after 3 attempts. record_uuid: {rec_uuid}" in caplog.text
            caplog.clear()


# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::test_extract_pdf_and_update_file_contents_api_cases -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
@pytest.mark.parametrize("tika_path, isfile, storage_exception, subprocess_returncode, update_side_effect, expect_error_attr, expect_content", [
    ("/tmp/tika.jar", True, None, 0, None, None, "abc"),  # normal
    (None, True, None, 0, None, Exception, None),  # tika jar not found
    ("/tmp/tika.jar", True, FileNotFoundError("not found"), 0, None, "file_error", None),  # storage_factory error
    ("/tmp/tika.jar", True, None, 1, None, "subprocess_error", None),  # subprocess error
    ("/tmp/tika.jar", True, None, 0, "conflict", "update_error", None),  # ConflictError
    ("/tmp/tika.jar", True, None, 0, "notfound", "update_error", None),  # NotFoundError
    ("/tmp/tika.jar", True, "ResourceNotFoundError", 0, None, None, None),  # ResourceNotFoundError
    ("/tmp/tika.jar", True, None, 0, "other", "update_error", None),  # other exception
])
def test_extract_pdf_and_update_file_contents_cases(monkeypatch, tika_path, isfile, storage_exception, subprocess_returncode, update_side_effect, expect_error_attr, expect_content):
    if tika_path is not None:
        monkeypatch.setenv("TIKA_JAR_FILE_PATH", tika_path)
    else:
        monkeypatch.delenv("TIKA_JAR_FILE_PATH", raising=False)
    monkeypatch.setattr(os.path, "isfile", lambda path: isfile)
    class DummyStorage:
        def open(self, mode):
            class DummyFP:
                def read(self, size): return b'data'
                def __enter__(self): return self
                def __exit__(self, exc_type, exc_val, exc_tb): pass
            return DummyFP()
    if storage_exception == 'ResourceNotFoundError':
        import weko_deposit.tasks as tasks_mod
        monkeypatch.setattr("weko_deposit.tasks.current_files_rest", types.SimpleNamespace(storage_factory=lambda fileurl, size: (_ for _ in ()).throw(tasks_mod.ResourceNotFoundError("not found"))))
    elif storage_exception:
        monkeypatch.setattr("weko_deposit.tasks.current_files_rest", types.SimpleNamespace(storage_factory=lambda fileurl, size: (_ for _ in ()).throw(storage_exception)))
    else:
        monkeypatch.setattr("weko_deposit.tasks.current_files_rest", types.SimpleNamespace(storage_factory=lambda fileurl, size: DummyStorage()))
    dummy_logger = types.SimpleNamespace(error=lambda x: setattr(monkeypatch, expect_error_attr, x) if expect_error_attr and expect_error_attr is not Exception else None)
    dummy_app = types.SimpleNamespace(config={'WEKO_DEPOSIT_FILESIZE_LIMIT': 100}, logger=dummy_logger)
    monkeypatch.setattr("weko_deposit.tasks.current_app", dummy_app)
    monkeypatch.setattr("weko_deposit.tasks.subprocess", types.SimpleNamespace(
        run=lambda *a, **k: types.SimpleNamespace(returncode=subprocess_returncode, stdout=b'abc\n', stderr=b''),
        PIPE=object()
    ))
    import weko_deposit.tasks as tasks_mod
    if update_side_effect == 'conflict':
        monkeypatch.setattr("weko_deposit.tasks.update_file_content", lambda *a, **k: (_ for _ in ()).throw(tasks_mod.ConflictError()))
    elif update_side_effect == 'notfound':
        monkeypatch.setattr("weko_deposit.tasks.update_file_content", lambda *a, **k: (_ for _ in ()).throw(tasks_mod.NotFoundError()))
    elif update_side_effect == 'other':
        monkeypatch.setattr("weko_deposit.tasks.update_file_content", lambda *a, **k: (_ for _ in ()).throw(Exception("other")))
    else:
        called = {}
        def dummy_update(record_uuid, file_datas):
            called['called'] = (record_uuid, file_datas)
        monkeypatch.setattr("weko_deposit.tasks.update_file_content", dummy_update)
    file_dict = {'f.pdf': {'uri': 'u', 'size': 1}}
    if expect_error_attr == Exception:
        with pytest.raises(Exception, match="not exist tika jar file."):
            extract_pdf_and_update_file_contents(file_dict, 'rid')
    else:
        extract_pdf_and_update_file_contents(file_dict, 'rid')
        if expect_content:
            assert called['called'][0] == 'rid'
            assert called['called'][1]['f.pdf'] == expect_content
        if expect_error_attr and expect_error_attr is not Exception:
            assert hasattr(monkeypatch, expect_error_attr)


# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::test_update_file_content_cases -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
@pytest.mark.parametrize("content, file_datas, expected", [
    ([{'filename': 'f1', 'attachment': {'content': ''}}, {'filename': 'f2', 'attachment': {'content': ''}}, {'filename': 'f3'}], {'f1': 'abc', 'f2': 'def'}, ['abc', 'def', None]),
    ([{'filename': 'f1', 'attachment': {'content': ''}}], {'f2': 'zzz'}, [None]),
    ([], {'f1': 'abc'}, []),
    ([{'filename': 'f1'}, {'filename': 'f2', 'attachment': {'content': ''}}], {'f1': 'abc', 'f2': 'def'}, [None, 'def']),
])
def test_update_file_content_cases(monkeypatch, content, file_datas, expected):
    called = {}
    class DummyClient:
        def index(self, **kwargs):
            called['body'] = kwargs['body']
            return {'result': 'ok'}
    class DummyIndexer:
        def __init__(self):
            self.client = DummyClient()
            self.es_index = 'idx'
            self.es_doc_type = 'doc'
        def get_es_index(self): pass
        def get_metadata_by_item_id(self, rid):
            return {
                '_source': {'content': content} if content is not None else {},
                '_version': 1,
                '_type': 'doc'
            }
    monkeypatch.setattr("weko_deposit.tasks.WekoIndexer", DummyIndexer)
    update_file_content('rid', file_datas)
    if content:
        result = called['body']['content']
        for i, exp in enumerate(expected):
            if exp is not None:
                assert result[i].get('attachment', {}).get('content') == exp
            else:
                assert 'attachment' not in result[i] or result[i]['attachment'].get('content') == ''
