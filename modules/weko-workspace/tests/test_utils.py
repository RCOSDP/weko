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

import pytest
from mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from flask_babelex import gettext as _
from flask_login.utils import login_user
from invenio_cache import current_cache
from weko_user_profiles import UserProfile

import json
from unittest.mock import Mock, patch, call
import pytest
from sqlalchemy.exc import SQLAlchemyError
from flask_login import login_user
from weko_workspace.models import WorkspaceDefaultConditions
import requests

from weko_workspace.utils import *
from weko_workspace.config import WEKO_WORKSPACE_DEFAULT_FILTERS

# ===========================def get_workspace_filterCon():=====================================
# .tox/c1/bin/pytest tests/test_utils.py::test_get_workspace_filterCon -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
# ワークスペースのフィルター条件を取得する関数のテスト
@pytest.mark.parametrize('users_index, mock_setup, expected_response', [
    (0, 
     {'return_value': {'default_con': {"favorite": {"label": "お気に入り", "options": ["あり", "なし"], "default": "あり"}}}},  
     ({"favorite": {"label": "お気に入り", "options": ["あり", "なし"], "default": "あり"}}, True)),

    (0, 
     {'return_value': None},  
     (WEKO_WORKSPACE_DEFAULT_FILTERS, False)),

    (0, 
     {'side_effect': SQLAlchemyError("Database error")},  
     (WEKO_WORKSPACE_DEFAULT_FILTERS, False)),

    (0, 
     {'side_effect': Exception("Unexpected error")},  
     (WEKO_WORKSPACE_DEFAULT_FILTERS, False)),
])
def test_get_workspace_filterCon(users, users_index, mock_setup, expected_response, workspaceData, app):
    test_user = users[users_index]['obj']  
    with app.test_request_context():
        login_user(test_user)
        with patch('weko_workspace.views.WorkspaceDefaultConditions.query') as mock_query:
            mock_filter = mock_query.filter_by.return_value
            mock_filter.with_entities.return_value.scalar = Mock(**mock_setup)
            if 'return_value' in mock_setup and mock_setup['return_value'] is not None:
                mock_filter.with_entities.return_value.scalar.return_value = workspaceData[0].default_con
                expected_response = (workspaceData[0].default_con, True)
            result = get_workspace_filterCon()
            assert result == expected_response
            mock_query.filter_by.assert_called_once_with(user_id=users[users_index]['id'])
            mock_filter.with_entities.assert_called_once_with(WorkspaceDefaultConditions.default_con)


# ===========================def get_es_itemlist():=====================================
# .tox/c1/bin/pytest tests/test_utils.py::test_get_es_itemlist -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('mock_responses, mock_exception, expected_response', [
    (
        [
            {'hits': {'hits': [{'id': str(i), 'metadata': {'title': [f'Title {i}']}} for i in range(1, 4)]}},
        ],
        None,
        [{'id': str(i), 'metadata': {'title': [f'Title {i}']}} for i in range(1, 4)]
    ),
    (
        [
            {'hits': {'hits': []}},
        ],
        None,
        []
    ),
    (
        [
            {}
        ],
        None,
        []
    ),
    (
        [
            {'hits': {'hits': [{'id': str(i), 'metadata': {'title': [f'Title {i}']}} for i in range(1, 10001)]}},
            {'hits': {'hits': [{'id': str(i), 'metadata': {'title': [f'Title {i}']}} for i in range(10001, 10101)]}}
        ],
        None,
        [{'id': str(i), 'metadata': {'title': [f'Title {i}']}} for i in range(1, 10101)]
    ),
    (
        [],
        TransportError(500, 'Server Error'),
        None
    ),
    (
        [],
        Exception("Unexpected error"),
        None
    )
])
def test_get_es_itemlist(app, mock_responses, mock_exception, expected_response):
    with patch('weko_workspace.utils.RecordsSearch') as mock_search_cls:
        mock_search = MagicMock()
        
        # setup mock responses or exception
        if mock_exception:
            mock_search.execute.side_effect = mock_exception    
        else:
            side_effects = []
            for i in range(len(mock_responses)):
                if i == 0:
                    mock_execute = MagicMock()
                    mock_execute.to_dict.return_value = mock_responses[i]
                    mock_search.execute.return_value = mock_execute
                else:
                    mock_execute = MagicMock()
                    mock_execute.to_dict.return_value = mock_responses[i]
                    side_effects.append(mock_execute)
            if side_effects:
                mock_extra = MagicMock()
                mock_extra.execute.side_effect = side_effects
                mock_search.extra.return_value = mock_extra
        
        # Mock the RecordsSearch class
        mock_search_cls.return_value = mock_search
        mock_search.with_preference_param.return_value = mock_search
        mock_search.params.return_value = mock_search
        mock_search.filter.return_value = mock_search
        mock_search.query.return_value = mock_search
        mock_search.sort.return_value = mock_search

        result = get_es_itemlist()
        assert result == expected_response


# ===========================def get_workspace_status_management():=====================================
# ワークスペースのステータス管理情報を取得する関数のテスト
# .tox/c1/bin/pytest tests/test_utils.py::test_get_workspace_status_management -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('recid, mock_setup, expected_response', [
    (
        "recid_0",
        {'return_value': (True, False)},
        (True, False)
    ),
    (
        "nonexistent_recid",
        {'return_value': None},
        None
    ),
    (
        "recid_0",
        {'side_effect': SQLAlchemyError("Database error")},
        None
    ),
])
def test_get_workspace_status_management(recid, mock_setup, expected_response, app, users, workspaceData):
    test_user = users[0]['obj']
    with app.test_request_context():
        login_user(test_user)
        with patch('weko_workspace.utils.WorkspaceStatusManagement.query') as mock_query:
            mock_filter = mock_query.filter_by.return_value
            mock_filter.with_entities.return_value.first = Mock(**mock_setup)
            if mock_setup.get('return_value') == (True, False):
                mock_filter.with_entities.return_value.first.return_value = (
                    workspaceData[1].is_favorited,
                    workspaceData[1].is_read
                )
                expected_response = (workspaceData[1].is_favorited, workspaceData[1].is_read)
            result = get_workspace_status_management(recid)
            assert result == expected_response
            mock_query.filter_by.assert_called_once_with(user_id=test_user.id, recid=recid)
            mock_filter.with_entities.assert_called_once_with(
                WorkspaceStatusManagement.is_favorited,
                WorkspaceStatusManagement.is_read
            )

# ===========================def get_accessCnt_downloadCnt():=====================================
# アイテムのアクセス数とダウンロード数を取得する関数のテスト
# .tox/c1/bin/pytest tests/test_utils.py::test_get_accessCnt_downloadCnt -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('recid, mock_setup, expected_response', [
    (
        "valid_recid",
        {
            'pid_get': Mock(object_uuid="uuid_123"),
            'stat_result': {"detail_view": "5.0", "file_download": {"file1": "3.0", "file2": "2.0"}}
        },
        (5, 5)
    ),
    (
        "invalid_recid",
        {
            'pid_get': Exception("PID does not exist")
        },
        (0, 0)
    ),
    (
        "valid_recid",
        {
            'pid_get': Mock(object_uuid="uuid_123"),
            'stat_result': Exception("Database error")
        },
        (0, 0)
    ),
    (
        "valid_recid",
        {
            'pid_get': Mock(object_uuid="uuid_123"),
            'stat_result': {"wrong_key": "invalid"}
        },
        (0, 0)
    ),
    (
        "valid_recid",
        {
            'pid_get': Mock(object_uuid="uuid_123"),
            'stat_result': {"detail_view": "invalid", "file_download": {"file1": "not_a_number"}}
        },
        (0, 0)
    ),
])
def test_get_accessCnt_downloadCnt(recid, mock_setup, expected_response, app):
    with app.test_request_context():
        with patch('weko_workspace.utils.PersistentIdentifier.get') as mock_pid:
            with patch('weko_workspace.utils.StatisticMail.get_item_information') as mock_stat:
                if isinstance(mock_setup['pid_get'], Exception):
                    mock_pid.side_effect = mock_setup['pid_get']
                else:
                    mock_pid.return_value = mock_setup['pid_get']
                if 'stat_result' in mock_setup:
                    if isinstance(mock_setup['stat_result'], Exception):
                        mock_stat.side_effect = mock_setup['stat_result']
                    else:
                        mock_stat.return_value = mock_setup['stat_result']
                result = get_accessCnt_downloadCnt(recid)
                assert result == expected_response
                if not isinstance(mock_setup['pid_get'], Exception):
                    mock_pid.assert_called_once_with(
                        app.config["WEKO_WORKSPACE_PID_TYPE"], recid
                    )
                if 'stat_result' in mock_setup and not isinstance(mock_setup.get('stat_result'), Exception):
                    mock_stat.assert_called_once_with("uuid_123", None, "")

# ===========================def get_item_status():=====================================
# .tox/c1/bin/pytest tests/test_utils.py::test_get_item_status -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('recid, expected_response', [
    ('1', ['OA', 'Embargo OA']),
    ('2', 'Metadata Registered'),
    ('3', 'Unlinked'),
])
def test_get_item_status(app, oa_status, recid, expected_response):
    file_info = {}
    if recid == '1':
        dt = datetime.now(timezone.utc)
        file_info = {'date': [{'dateValue': dt.strftime('%Y-%m-%d')}]}
        result = get_item_status(recid, file_info)
        assert result == expected_response[0]

        dt = datetime.now(timezone.utc) + timedelta(days=1)
        file_info = {'date': [{'dateValue': dt.strftime('%Y-%m-%d')}]}
        result = get_item_status(recid, file_info)
        assert result == expected_response[1]

        file_info = {'date': [{}]}
        result = get_item_status(recid, file_info)
        assert result == expected_response[0]

        file_info = {}
        result = get_item_status(recid, file_info)
        assert result == expected_response[0]
    else:
        result = get_item_status(recid, file_info)
        assert result == expected_response

# ===========================def get_userNm_affiliation():=====================================
# .tox/c1/bin/pytest tests/test_utils.py::test_get_userNm_affiliation -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('mock_setup, expected_response', [
    (
        {
            'username': "test_user"
        },
        "test_user"
    ),
    (
        {
            'username': None
        },
        "contributor@test.org"
    ),
    (
        {
            'side_effect': SQLAlchemyError("Database error")
        },
        None
    ),
])
def test_get_userNm_affiliation(mock_setup, expected_response, app, users):
    test_user = users[0]['obj']
    with app.test_request_context():
        login_user(test_user)
        with patch('weko_workspace.utils.UserProfile.query') as mock_query:
            mock_filter = mock_query.filter_by.return_value
            if 'side_effect' in mock_setup:
                mock_filter.with_entities.return_value.scalar.side_effect = mock_setup['side_effect']
            else:
                mock_filter.with_entities.return_value.scalar.return_value = mock_setup['username']
            if 'side_effect' in mock_setup:
                with pytest.raises(SQLAlchemyError):
                    result = get_userNm_affiliation()
            else:
                result = get_userNm_affiliation()
                assert result == expected_response
            mock_query.filter_by.assert_called_once_with(user_id=test_user.id)
            mock_filter.with_entities.assert_called_once_with(UserProfile.username)

# ===========================def insert_workspace_status():=====================================
# ワークスペースのステータスを挿入する関数のテスト
# .tox/c1/bin/pytest tests/test_utils.py::test_insert_workspace_status -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('user_id, recid, is_favorited, is_read, mock_setup, expected_exception', [
    (
        "1",
        "recid_1",
        True,
        False,
        {'commit': None},
        None
    ),
    (
        "2",
        "recid_2",
        False,
        True,
        {'commit': SQLAlchemyError("Commit failed")},
        SQLAlchemyError
    ),
    (
        "3",
        "recid_3",
        False,
        False,
        {'commit': None},
        None
    ),
])
def test_insert_workspace_status(user_id, recid, is_favorited, is_read, mock_setup, expected_exception, app):
    with app.app_context():
        with patch('weko_workspace.utils.db.session') as mock_session:
            if mock_setup['commit']:
                mock_session.commit.side_effect = mock_setup['commit']
            else:
                mock_session.commit = Mock()
            mock_session.rollback = Mock()
            mock_session.add = Mock()
            if expected_exception:
                with pytest.raises(expected_exception):
                    result = insert_workspace_status(user_id, recid, is_favorited, is_read)
                    mock_session.rollback.assert_called_once()
            else:
                result = insert_workspace_status(user_id, recid, is_favorited, is_read)
                mock_session.add.assert_called_once()
                mock_session.commit.assert_called_once()
                assert isinstance(result, WorkspaceStatusManagement)
                assert result.user_id == user_id
                assert result.recid == recid
                assert result.is_favorited == is_favorited
                assert result.is_read == is_read
                assert isinstance(result.created, datetime)
                assert isinstance(result.updated, datetime)

# ===========================def update_workspace_status():=====================================
# ワークスペースのステータスを更新する関数のテスト
# .tox/c1/bin/pytest tests/test_utils.py::test_update_workspace_status -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('user_id, recid, is_favorited, is_read, mock_setup, expected_favorited, expected_read', [
    (
        1,
        2000038,
        True,
        None,
        {'return_value': Mock(user_id=1, recid=2000038, is_favorited=False, is_read=True, updated=datetime(2023, 1, 1)), 'commit': None},
        True,
        True
    ),
    (
        1,
        2000038,
        None,
        True,
        {'return_value': Mock(user_id=1, recid=2000038, is_favorited=False, is_read=True, updated=datetime(2023, 1, 1)), 'commit': None},
        False,
        True
    ),
    (
        2,
        "nonexistent_recid",
        True,
        True,
        {'return_value': None, 'commit': None},
        None,
        None
    ),
    (
        1,
        2000038,
        False,
        True,
        {'return_value': Mock(user_id=1, recid=2000038, is_favorited=True, is_read=False, updated=datetime(2023, 1, 1)), 'commit': SQLAlchemyError("Commit failed")},
        None,
        None
    ),
])
def test_update_workspace_status(user_id, recid, is_favorited, is_read, mock_setup, expected_favorited, expected_read, app, workspaceData):
    with app.app_context():
        with patch('weko_workspace.utils.WorkspaceStatusManagement.query') as mock_query:
            mock_filter = mock_query.filter_by.return_value
            mock_filter.first = Mock(**mock_setup)
            with patch('weko_workspace.utils.db.session') as mock_session:
                if mock_setup['commit']:
                    mock_session.commit.side_effect = mock_setup['commit']
                else:
                    mock_session.commit = Mock()
                mock_session.rollback = Mock()
                if mock_setup['return_value'] and mock_setup['commit'] is None:
                    mock_filter.first.return_value = workspaceData[1]
                    if is_favorited is not None:
                        workspaceData[1].is_favorited = is_favorited
                    if is_read is not None:
                        workspaceData[1].is_read = is_read
                if mock_setup.get('commit') is not None:
                    with pytest.raises(SQLAlchemyError):
                        result = update_workspace_status(user_id, recid, is_favorited, is_read)
                        mock_session.rollback.assert_called_once()
                else:
                    result = update_workspace_status(user_id, recid, is_favorited, is_read)
                    if result:
                        assert result.user_id == user_id
                        assert result.recid == recid
                        assert result.is_favorited == expected_favorited
                        assert result.is_read == expected_read
                        assert isinstance(result.updated, datetime)
                        mock_session.commit.assert_called_once()
                    else:
                        assert result is None
                mock_query.filter_by.assert_called_once_with(user_id=user_id, recid=recid)

# ===========================def extract_metadata_info():=====================================
# メタデータからファイルリストとピアレビュー情報を抽出する関数のテスト
# .tox/c1/bin/pytest tests/test_utils.py::test_extract_metadata_info -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('item_metadata, expected_filelist, expected_peer_reviewed', [
    (
        {
            "file_key": {
                "attribute_type": "file",
                "attribute_value_mlt": ["file1.pdf", "file2.pdf"]
            },
            "review_key": {
                "attribute_value_mlt": [
                    {"subitem_peer_reviewed": "Peer reviewed"}
                ]
            }
        },
        ["file1.pdf", "file2.pdf"],
        True
    ),
    (
        {
            "file_key": {
                "attribute_type": "file",
                "attribute_value_mlt": ["file3.pdf"]
            },
            "other_key": {
                "attribute_value_mlt": [
                    {"subitem_peer_reviewed": "Not reviewed"}
                ]
            }
        },
        ["file3.pdf"],
        False
    ),
    (
        {
            "text_key": {
                "attribute_type": "text",
                "attribute_value_mlt": ["some text"]
            },
            "review_key": {
                "attribute_value_mlt": [
                    {"subitem_peer_reviewed": "Peer reviewed"}
                ]
            }
        },
        [],
        True
    ),
    (
        {
            "text_key": {
                "attribute_type": "text",
                "attribute_value_mlt": ["some text"]
            }
        },
        [],
        False
    ),
    (
        {},
        [],
        False
    ),
    (
        {
            "file_key1": {
                "attribute_type": "file",
                "attribute_value_mlt": ["file1.pdf"]
            },
            "file_key2": {
                "attribute_type": "file",
                "attribute_value_mlt": ["file2.pdf"]
            },
            "review_key": {
                "attribute_value_mlt": [
                    {"subitem_peer_reviewed": "Peer reviewed"}
                ]
            }
        },
        ["file1.pdf"],
        True
    ),
    (
        {
            "file_key": {
                "attribute_type": "file",
                "attribute_value_mlt": ["file4.pdf"]
            },
            "review_key": {
                "some_other_key": "value"
            }
        },
        ["file4.pdf"],
        False
    ),
])
def test_extract_metadata_info(item_metadata, expected_filelist, expected_peer_reviewed):
    result_filelist, result_peer_reviewed = extract_metadata_info(item_metadata)
    assert result_filelist == expected_filelist
    assert result_peer_reviewed == expected_peer_reviewed

# .tox/c1/bin/pytest tests/test_utils.py::test_changeLang -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('lang, expected_conditions', [
    ('en', {
        'resource_type': {
            'label': 'Resource Type',
            'options': ['conference paper', 'data paper']
        },
        'peer_review': {
            'label': 'Peer Review',
            'options': ['Yes', 'No'],
        },
        'related_to_paper': {
            'label': 'Related To Paper',
            'options': ['Yes', 'No'],
        },
        'related_to_data': {
            'label': 'Related To Data',
            'options': ['Yes', 'No'],
        },
        'funder_name': {
            'label': 'Funding Reference - Funder Name',
            'options': [],
        },
        'award_title': {
            'label': 'Funding Reference - Award Title',
            'options': [],
        },
        'file_present': {
            'label': 'File',
            'options': ['Yes', 'No'],
        },
        'favorite': {
            'label': 'Favorite',
            'options': ['Yes', 'No'],
        },
        'no_label': {
            'title': 'Resource Type',
            'options': ['conference paper', 'data paper'],
        },
        'no_mapping': {
            'label': 'No Mapping',
            'options': ['Option 1', 'Option 2'],
        }
    }),
    ('ja', {
        'resource_type': {
            'label': 'リソースタイプ',
            'options': ['conference paper', 'data paper'],
        },
        'peer_review': {
            'label': '査読',
            'options': ['Yes', 'No'],
        },
        'related_to_paper': {
            'label': '論文への関連',
            'options': ['Yes', 'No'],
        },
        'related_to_data': {
            'label': '根拠データへの関連',
            'options': ['Yes', 'No'],
        },
        'funder_name': {
            'label': '資金別情報 - 助成機関名',
            'options': [],
        },
        'award_title': {
            'label': '資金別情報 - 研究課題名',
            'options': [],
        },
        'file_present': {
            'label': '本文ファイル',
            'options': ['Yes', 'No'],
        },
        'favorite': {
            'label': 'お気に入り',
            'options': ['Yes', 'No'],
        },
        'no_label': {
            'title': 'Resource Type',
            'options': ['conference paper', 'data paper'],
        },
        'no_mapping': {
            'label': 'No Mapping',
            'options': ['Option 1', 'Option 2'],
        }
    }),
])
def test_changeLang(lang, expected_conditions):
    default_conditions = {
        'resource_type': {
            'label': 'Resource Type',
            'options': ['conference paper', 'data paper']
        },
        'peer_review': {
            'label': 'Peer Review',
            'options': ['Yes', 'No'],
        },
        'related_to_paper': {
            'label': 'Related To Paper',
            'options': ['Yes', 'No'],
        },
        'related_to_data': {
            'label': 'Related To Data',
            'options': ['Yes', 'No'],
        },
        'funder_name': {
            'label': 'Funding Reference - Funder Name',
            'options': [],
        },
        'award_title': {
            'label': 'Funding Reference - Award Title',
            'options': [],
        },
        'file_present': {
            'label': 'File',
            'options': ['Yes', 'No'],
        },
        'favorite': {
            'label': 'Favorite',
            'options': ['Yes', 'No'],
        },
        'no_label': {
            'title': 'Resource Type',
            'options': ['conference paper', 'data paper'],
        },
        'no_mapping': {
            'label': 'No Mapping',
            'options': ['Option 1', 'Option 2'],
        }
    }
    result = changeLang(lang, default_conditions)
    assert result == expected_conditions

    result = changeLang(lang, {})
    assert result == {}

# .tox/c1/bin/pytest tests/test_utils.py::test_changeMsg -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('lang, expected_messages', [
    (
        'en',
        [
            'Successfully saved default conditions.',
            'Successfully reset default conditions.',
            'No default conditions found to reset.'
        ]
    ),
    (
        'ja',
        [
            'デフォルト条件の保存に成功しました。',
            'デフォルト条件のリセットに成功しました。',
            'リセットするデフォルト条件が見つかりません。'
        ]
    )
])
def test_changeMsg(lang, expected_messages):
    message = 'Successfully saved default conditions.'
    result = changeMsg(lang, 1, None, message)
    assert result == expected_messages[0]

    message = 'Successfully reset default conditions.'
    result = changeMsg(lang, 2, True, message)
    assert result == expected_messages[1]

    message = 'No default conditions found to reset.'
    result = changeMsg(lang, 2, False, message)
    assert result == expected_messages[2]

    message = 'No change message.'
    result = changeMsg(lang, 3, None, message)
    assert result == message

# .tox/c1/bin/pytest tests/test_utils.py::test_convert_jamas_xml_data_to_dictionary -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_convert_jamas_xml_data_to_dictionary(app):
    with open('tests/data/test_convert_xml_to_dict.xml', 'r') as file:
        api_data = file.read()
    expected_result = {
        'response': {
            "identifier": 'test-identifier',
            "title": 'Test Title',
            "creator": ['Test Creator 1', 'Test Creator 2'],
            "type": ['Test Type 1', 'Test Type 2'],
            "language": 'en',
            "publisher": 'Test Publisher',
            "description": ['Test Description 1', 'Test Description 2'],
            "organization": ['Test Organization 1', 'Test Organization 2'],
            "publicationName": 'Test Publication Name',
            "issn": '1234-5678',
            "eIssn": '8765-4321',
            "isbn": ['978-3-16-148410-0', '978-1-23-456789-0'],
            "volume": '1',
            "number": '2',
            "startingPage": '10',
            "pageRange": '10-20',
            "publicationDate": ['2023-01-01', '2023-02-01'],
            "keyword": ['Test Keyword 1', 'Test Keyword 2'],
            "doi": '10.1234/test-doi',
            "postDate": ['2023-01-15', '2023-02-15'],
        },
        'error': ''
    }
    result = convert_jamas_xml_data_to_dictionary(api_data)
    assert result == expected_result

    with patch('lxml.etree.QName') as mock_qname:
        mock_qname.side_effect = Exception("XML parsing error")
        result = convert_jamas_xml_data_to_dictionary(api_data)
        assert result['error'] == 'XML parsing error'
        assert result['response'] == {}

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jamas_record_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_jamas_record_data(app, mocker_itemtype):
    mock_get_data = {
        'response': '<metadata></metadata>',
        'error': ''
    }
    mock_dictionary = {
        'response': {
            'identifier': 'test-identifier'
        },
        'error': ''
    }
    with patch('weko_workspace.utils.JamasURL.get_data', return_value=mock_get_data):
        with patch('weko_workspace.utils.convert_jamas_xml_data_to_dictionary', return_value=mock_dictionary):
            with patch('weko_workspace.utils.get_jamas_data_by_key', return_value={}):
                with patch('weko_workspace.utils.get_jamas_autofill_item'):
                    with patch('weko_workspace.utils.get_autofill_key_tree'):
                        with patch('weko_items_autofill.utils.sort_by_item_type_order'):
                            with patch('weko_workspace.utils.build_record_model', return_value=[1]):
                                current_cache.delete('jamas_data10.1234/test-doi1')
                                result = get_jamas_record_data('10.1234/test-doi', 1)
                                assert result == [1]
                
                item_type = Mock(item_type='test_item_type', form=None)
                with patch('weko_workspace.utils.ItemTypes.get_by_id', return_value=item_type):
                    current_cache.delete('jamas_data10.1234/test-doi1')
                    result = get_jamas_record_data('10.1234/test-doi', 1)
                    assert result == []

                with patch('weko_workspace.utils.ItemTypes.get_by_id', return_value=None):
                    current_cache.delete('jamas_data10.1234/test-doi1')
                    result = get_jamas_record_data('10.1234/test-doi', 1)
                    assert result == []

    # Test with error in convert_jamas_xml_data_to_dictionary
    mock_dictionary = {
        'response': {},
        'error': 'test error message'
    }
    with patch('weko_workspace.utils.JamasURL.get_data', return_value=mock_get_data):
        with patch('weko_workspace.utils.convert_jamas_xml_data_to_dictionary', return_value=mock_dictionary):
            current_cache.delete('jamas_data10.1234/test-doi1')
            result = get_jamas_record_data('10.1234/test-doi', 1)
            assert result == []

    # Test with error in get_data
    mock_get_data = {
        'response': '',
        'error': 'test error message'
    }
    with patch('weko_workspace.utils.JamasURL.get_data', return_value=mock_get_data):
        current_cache.delete('jamas_data10.1234/test-doi1')
        result = get_jamas_record_data('10.1234/test-doi', 1)
        assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jamas_autofill_item -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_jamas_autofill_item(app):
    mock_item = {
        'title': {
            '@value': 'subitem_1551255647225',
            '@attributes': { 'xml:lang': 'subitem_1551255648112' },
            'model_id': 'item_1617186331708'
        },
        'sourceTitle': {
            '@value': 'subitem_1522650091861',
            '@attributes': { 'xml:lang': 'subitem_1522650068558' },
            'model_id': 'item_1617186941041'
        },
        'sourceIdentifier': {
            '@value': 'subitem_1522646572813',
            '@attributes': { 'identifierType': 'subitem_1522646500366' },
            'model_id': 'item_1617186920753'
        },
        'no_required': {
            '@value': 'subitem_1234567890123',
            '@attributes': { 'identifierType': 'subitem_9876543210987' },
            'model_id': 'item_1122334455667'
        }
    }
    with patch('weko_workspace.utils.get_item_id', return_value=mock_item):
        result = get_jamas_autofill_item(15)
        del mock_item['no_required']
        assert result == mock_item

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jamas_data_by_key -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('keyword, expected_result', [
    ('title', {'title': [{'@value': 'title', '@language': 'en'}]}),
    ('creator', {'creator': [{'@value': 'test creator', '@language': 'en'}]}),
    ('sourceTitle', {'sourceTitle': [{'@value': 'sourceTitle', '@language': 'en'}]}),
    ('volume', {'volume': [{'@value': 'volume'}]}),
    ('issue', {'issue': [{'@value': 'issue'}]}),
    ('pageStart', {'pageStart': [{'@value': 'pageStart'}]}),
    ('numPages', {'numPages': [{'@value': 'numPages'}]}),
    ('date', {'date': [{'@value': '2025-01-01', '@type': 'Issued'}]}),
    ('relation', {'relation': [
        {'@value': 'test doi', '@type': 'DOI'},
        {'@value': 'test issn', '@type': 'ISSN'},
        {'@value': 'test eissn', '@type': 'EISSN'}
    ]}),
    ('sourceIdentifier', {'sourceIdentifier': [{'@value': 'test issn', '@type': 'ISSN'}]}),
    ('publisher', {'publisher': [{'@value': 'publisher', '@language': 'en'}]}),
    ('description', {'description': [{'@value': 'description', '@language': 'en'}]}),
    ('all', {
        'title': [{'@value': 'all', '@language': 'en'}],
        'creator': [{'@value': 'test creator', '@language': 'en'}],
        'sourceTitle': [{'@value': 'all', '@language': 'en'}],
        'volume': [{'@value': 'all'}],
        'issue': [{'@value': 'all'}],
        'pageStart': [{'@value': 'all'}],
        'numPages': [{'@value': 'all'}],
        'date': [{'@value': '2025-01-01', '@type': 'Issued'}],
        'relation': [
            {'@value': 'test doi', '@type': 'DOI'},
            {'@value': 'test issn', '@type': 'ISSN'},
            {'@value': 'test eissn', '@type': 'EISSN'}
        ],
        'sourceIdentifier': [{'@value': 'test issn', '@type': 'ISSN'}],
        'publisher': [{'@value': 'all', '@language': 'en'}],
        'description': [{'@value': 'all', '@language': 'en'}]
    }),
    ('error', None),
    ('empty', {}),
    ('none', None),
    ('invalid_key', {})
])
def test_get_jamas_data_by_key(app, mocker, keyword, expected_result):
    mocker.patch('weko_workspace.utils.get_jamas_language_data', return_value='en')
    mocker.patch(
        'weko_workspace.utils.pack_with_language_value_for_jamas',
        return_value=[{'@value': keyword, '@language': 'en'}]
    )
    mocker.patch(
        'weko_workspace.utils.get_jamas_creator_data',
        return_value=[{'@value': 'test creator', '@language': 'en'}]
    )
    mocker.patch(
        'weko_workspace.utils.pack_single_value_for_jamas',
        return_value=[{'@value': keyword}]
    )
    mocker.patch(
        'weko_workspace.utils.get_jamas_issue_date',
        return_value=[{'@value': '2025-01-01', '@type': 'Issued'}]
    )
    mocker.patch(
        'weko_workspace.utils.get_jamas_relation_data',
        return_value=[
            {'@value': 'test doi', '@type': 'DOI'},
            {'@value': 'test issn', '@type': 'ISSN'},
            {'@value': 'test eissn', '@type': 'EISSN'}
        ]
    )
    mocker.patch(
        'weko_workspace.utils.get_jamas_source_data',
        return_value=[{'@value': 'test issn', '@type': 'ISSN'}]
    )
    if keyword == 'error':
        api = {
            'response': {},
            'error': 'test error message'
        }
    elif keyword == 'empty':
        api = {
            'response': {},
            'error': ''
        }
    elif keyword == 'none':
        api = {
            'response': None,
            'error': ''
        }
    else: 
        api = {
            'response': {
                'language': 'en',
                'title': keyword,
                'creator': 'test creator',
                'publicationName': keyword,
                'volume': keyword,
                'number': keyword,
                'startingPage': keyword,
                'pageRange': keyword,
                'publicationDate': '2025年01月01日',
                'issn': 'test issn',
                'eIssn': 'test eissn',
                'doi': 'test doi',
                'publisher': keyword,
                'description': keyword
            },
            'error': ''
        }
    
    result = get_jamas_data_by_key(api, keyword)
    assert result == expected_result

# .tox/c1/bin/pytest tests/test_utils.py::test_pack_single_value_for_jamas -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_pack_single_value_for_jamas():
    # Test with string value
    value = "test_value"
    result = pack_single_value_for_jamas(value)
    assert result == [{'@value': value}]

    # Test with list of strings
    value = ["value1", "value2"]
    result = pack_single_value_for_jamas(value)
    assert result == [{'@value': v} for v in value]

    # Test with empty list
    value = []
    result = pack_single_value_for_jamas(value)
    assert result == []

    # Test with none value
    value = None
    result = pack_single_value_for_jamas(value)
    assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_pack_with_language_value_for_jamas -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_pack_with_language_value_for_jamas():
    # Test with string value
    value = "test_value"
    result = pack_with_language_value_for_jamas(value)
    assert result == [{'@value': value, '@language': 'en'}]

    # Test with string value and specific language
    lang = "ja"
    value = "テスト値"
    result = pack_with_language_value_for_jamas(value, lang)
    assert result == [{'@value': value, '@language': lang}]

    # Test with list of strings
    value = ["value1", "value2"]
    result = pack_with_language_value_for_jamas(value)
    assert result == [{'@value': v, '@language': 'en'} for v in value]

    # Test with list of strings and specific language
    lang = "ja"
    value = ["値1", "値2"]
    result = pack_with_language_value_for_jamas(value, lang)
    assert result == [{'@value': v, '@language': lang} for v in value]

    # Test with empty list
    value = []
    result = pack_with_language_value_for_jamas(value)
    assert result == []

    # Test with none value
    value = None
    result = pack_with_language_value_for_jamas(value)
    assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jamas_source_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_jamas_source_data():
    # Test with string value
    value = "test_value"
    result = get_jamas_source_data(value)
    assert result == [{'@value': value, '@type': 'ISSN'}]

    # Test with list of strings
    value = ["value1", "value2"]
    result = get_jamas_source_data(value)
    assert result == [{'@value': v, '@type': 'ISSN'} for v in value]

    # Test with empty list
    value = []
    result = get_jamas_source_data(value)
    assert result == []

    # Test with none value
    value = None
    result = get_jamas_source_data(value)
    assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jamas_relation_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_jamas_relation_data():
    # Test with string value
    issn_value = "test_issn"
    eissn_value = "test_eissn"
    doi_value = "test_doi"
    result = get_jamas_relation_data(issn_value, eissn_value, doi_value)
    assert result == [
        {'@value': doi_value, '@type': 'DOI'},
        {'@value': issn_value, '@type': 'ISSN'},
        {'@value': eissn_value, '@type': 'EISSN'}
    ]

    # Test with list of strings
    issn_value = ["issn1", "issn2"]
    eissn_value = ["eissn1", "eissn2"]
    doi_value = ["doi1", "doi2"]
    result = get_jamas_relation_data(issn_value, eissn_value, doi_value)
    assert result == [
        {'@value': doi, '@type': 'DOI'} for doi in doi_value
    ] + [
        {'@value': issn, '@type': 'ISSN'} for issn in issn_value
    ] + [
        {'@value': eissn, '@type': 'EISSN'} for eissn in eissn_value
    ]

    # Test with empty lists
    issn_value = []
    eissn_value = []
    doi_value = []
    result = get_jamas_relation_data(issn_value, eissn_value, doi_value)
    assert result == []

    # Test with none value
    issn_value = None
    eissn_value = None
    doi_value = None
    result = get_jamas_relation_data(issn_value, eissn_value, doi_value)
    assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jamas_issue_date -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_jamas_issue_date():
    # Test with string value that formats as 'YYYY-MM-DD'
    date_value = "2025-01-01"
    result = get_jamas_issue_date(date_value)
    assert result == [{'@value': date_value, '@type': 'Issued'}]

    # Test with string value that formats as 'YYYY年MM月DD日'
    date_value = "2025年01月01日"
    result = get_jamas_issue_date(date_value)
    assert result == [{'@value': '2025-01-01', '@type': 'Issued'}]

    # Test with string value that formats as 'YYYY.MM.DD'
    date_value = "2025.01.01"
    result = get_jamas_issue_date(date_value)
    assert result == [{'@value': '2025-01-01', '@type': 'Issued'}]

    # Test with string value that formats as 'YYYY/MM/DD'
    date_value = "2025/01/01"
    result = get_jamas_issue_date(date_value)
    assert result == [{'@value': date_value, '@type': 'Issued'}]

    # Test with list of strings
    date_value = ["2025-01-01", "2025年02月01日", "2025.03.01"]
    result = get_jamas_issue_date(date_value)
    assert result == [
        {'@value': '2025-01-01', '@type': 'Issued'},
        {'@value': '2025-02-01', '@type': 'Issued'},
        {'@value': '2025-03-01', '@type': 'Issued'}
    ]

    # Test with empty list
    date_value = []
    result = get_jamas_issue_date(date_value)
    assert result == []
    
    # Test with none value
    date_value = None
    result = get_jamas_issue_date(date_value)
    assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jamas_creator_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_jamas_creator_data():
    # Test with string value
    creator_value = "test_creator"
    result = get_jamas_creator_data(creator_value)
    assert result == [{'@value': creator_value, '@language': 'en'}]

    # Test with string value and specific language
    creator_value = "テストクリエイター"
    lang = "ja"
    result = get_jamas_creator_data(creator_value, lang)
    assert result == [{'@value': creator_value, '@language': lang}]

    # Test with list of strings
    creator_value = ["creator1", "creator2"]
    result = get_jamas_creator_data(creator_value)
    assert result == [[{'@value': c, '@language': 'en'}] for c in creator_value]

    # Test with list of strings and specific language
    creator_value = ["クリエイター1", "クリエイター2"]
    lang = "ja"
    result = get_jamas_creator_data(creator_value, lang)
    assert result == [[{'@value': c, '@language': lang}] for c in creator_value]

    # Test with empty list
    creator_value = []
    result = get_jamas_creator_data(creator_value)
    assert result == []

    # Test with none value
    creator_value = None
    result = get_jamas_creator_data(creator_value)
    assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jamas_language_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('lang, expected_response', [
    ('en', 'en'),
    ('eng', 'en'),
    ('English', 'en'),
    ('英語', 'en'),
    ('ja', 'ja'),
    ('jpn', 'ja'),
    ('japanese', 'ja'),
    ('日本語', 'ja'),
    ('', 'en'),
    (['en', 'ja'], 'en'),
    ([], 'en'),
    (None, 'en')
])
def test_get_jamas_language_data(app, lang, expected_response):
    result = get_jamas_language_data(lang)
    assert result == expected_response

# .tox/c1/bin/pytest tests/test_utils.py::test_get_cinii_record_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_cinii_record_data(app, mocker_itemtype):
    mock_get_data = {
        'response': {
            'items': [
                {
                    'title': 'Test Title',
                    'creator': 'Test Creator',
                    'publicationDate': '2023-01-01',
                    'identifier': '10.1234/test-doi',
                    'language': 'en'
                }
            ]
        },
        'error': ''
    }
    with patch('weko_workspace.utils.CiNiiURL.get_data', return_value=mock_get_data):
        with patch('weko_workspace.utils.get_cinii_data_by_key', return_value={}):
            with patch('weko_workspace.utils.get_cinii_autofill_item'):
                with patch('weko_workspace.utils.get_autofill_key_tree'):
                    with patch('weko_workspace.utils.build_record_model', return_value=[1]):
                        current_cache.delete('cinii_data10.1234/test-doi1')
                        result = get_cinii_record_data('10.1234/test-doi', 1)
                        assert result == [1]
            
            item_type = Mock(item_type='test_item_type', form=None)
            with patch('weko_workspace.utils.ItemTypes.get_by_id', return_value=item_type):
                current_cache.delete('cinii_data10.1234/test-doi1')
                result = get_cinii_record_data('10.1234/test-doi', 1)
                assert result == []
            
            with patch('weko_workspace.utils.ItemTypes.get_by_id', return_value=None):
                current_cache.delete('cinii_data10.1234/test-doi1')
                result = get_cinii_record_data('10.1234/test-doi', 1)
                assert result == []
    
    # Test with error in get_data
    mock_get_data = {
        'response': {},
        'error': 'test error message'
    }
    with patch('weko_workspace.utils.CiNiiURL.get_data', return_value=mock_get_data):
        current_cache.delete('cinii_data10.1234/test-doi1')
        result = get_cinii_record_data('10.1234/test-doi', 1)
        assert result == []
    
    # Test with response type is not dict
    mock_get_data = {
        'response': 'not a dict',
        'error': ''
    }
    with patch('weko_workspace.utils.CiNiiURL.get_data', return_value=mock_get_data):
        current_cache.delete('cinii_data10.1234/test-doi1')
        result = get_cinii_record_data('10.1234/test-doi', 1)
        assert result == []

    # Test with item is not found in response
    mock_get_data = {
        'response': {
            'items': []
        },
        'error': ''
    }
    with patch('weko_workspace.utils.CiNiiURL.get_data', return_value=mock_get_data):
        current_cache.delete('cinii_data10.1234/test-doi1')
        result = get_cinii_record_data('10.1234/test-doi', 1)
        assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_get_cinii_data_by_key -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('keyword, expected_result', [
    ('title', {'title': [{'@value': 'title', '@language': 'ja'}]}),
    ('creator', {'creator': [[{'@value': 'test creator', '@language': 'ja'}]]}),
    ('description', {'description': [{'@value': 'test description', '@type': 'Abstract', '@language': 'ja'}]}),
    ('subject', {'subject': [{'@scheme': 'Other', '@value': 'test subject', '@language': 'ja'}]}),
    ('sourceTitle', {'sourceTitle': [{'@value': 'sourceTitle', '@language': 'ja'}]}),
    ('volume', {'volume': {'@value': 'volume'}}),
    ('issue', {'issue': {'@value': 'issue'}}),
    ('pageStart', {'pageStart': {'@value': '10'}}),
    ('pageEnd', {'pageEnd': {'@value': '10'}}),
    ('numPages', {'numPages': {'@value': '1'}}),
    ('date', {'date': {'@value': '2025-01-01', '@type': 'Issued'}}),
    ('publisher', {'publisher': [{'@value': 'publisher', '@language': 'ja'}]}),
    ('sourceIdentifier', {'sourceIdentifier': [{'@value': 'test issn', '@type': 'ISSN'}]}),
    ('relation', {'relation': [{'@value': 'test doi', '@type': 'DOI'}, {'@value': 'test naid', '@type': 'NAID'}]}),
    ('all', {
        'title': [{'@value': 'all', '@language': 'ja'}],
        'creator': [[{'@value': 'test creator', '@language': 'ja'}]],
        'description': [{'@value': 'test description', '@type': 'Abstract', '@language': 'ja'}],
        'subject': [{'@scheme': 'Other', '@value': 'test subject', '@language': 'ja'}],
        'sourceTitle': [{'@value': 'all', '@language': 'ja'}],
        'volume': {'@value': 'all'},
        'issue': {'@value': 'all'},
        'pageStart': {'@value': '10'},
        'pageEnd': {'@value': '10'},
        'numPages': {'@value': '1'},
        'date': {'@value': '2025-01-01', '@type': 'Issued'},
        'publisher': [{'@value': 'all', '@language': 'ja'}],
        'sourceIdentifier': [{'@value': 'test issn', '@type': 'ISSN'}],
        'relation': [{'@value': 'test doi', '@type': 'DOI'}, {'@value': 'test naid', '@type': 'NAID'}]
    }),
    ('empty', {
        'title': None,
        'creator': None,
        'description': None,
        'subject': None,
        'sourceTitle': None,
        'volume': None,
        'issue': None,
        'pageStart': None,
        'pageEnd': None,
        'numPages': {'@value': '1'},
        'date': None,
        'publisher': None,
        'sourceIdentifier': None,
        'relation': None
    }),
    ('none', {})
])
def test_get_cinii_data_by_key(app, mocker, keyword, expected_result):
    mocker.patch(
        'weko_workspace.utils.get_cinii_title_data',
        return_value=[{'@value': keyword, '@language': 'ja'}]
    )
    mocker.patch(
        'weko_workspace.utils.get_cinii_creator_data',
        return_value=[[{'@value': 'test creator', '@language': 'ja'}]]
    )
    mocker.patch(
        'weko_workspace.utils.get_cinii_description_data',
        return_value=[{'@value': 'test description', '@type': 'Abstract', '@language': 'ja'}]
    )
    mocker.patch(
        'weko_workspace.utils.get_cinii_subject_data',
        return_value=[{'@scheme': 'Other', '@value': 'test subject', '@language': 'ja'}]
    )
    mocker.patch(
        'weko_workspace.utils.pack_single_value_as_dict',
        return_value={'@value': keyword}
    )
    mocker.patch(
        'weko_workspace.utils.get_cinii_page_data',
        return_value={'@value': '10'}
    )
    mocker.patch(
        'weko_workspace.utils.get_cinii_numpage',
        return_value={'@value': '1'}
    )
    mocker.patch(
        'weko_workspace.utils.get_cinii_date_data',
        return_value={'@value': '2025-01-01', '@type': 'Issued'}
    )
    mocker.patch(
        'weko_workspace.utils.pack_data_with_multiple_type_cinii',
        return_value=[{'@value': 'test issn', '@type': 'ISSN'}]
    )
    mocker.patch(
        'weko_workspace.utils.get_cinii_product_identifier',
        return_value=[{'@value': 'test doi', '@type': 'DOI'}, {'@value': 'test naid', '@type': 'NAID'}]
    )

    if keyword == 'empty':
        api = {
            'response': {
                'items': [
                    {
                        'title': '',
                        'dc:creator': [],
                        'description': '',
                        'dc:subject': '',
                        'prism:publicationName': '',
                        'prism:volume': '',
                        'prism:number': '',
                        'prism:startingPage': '',
                        'prism:endingPage': '',
                        'prism:publicationDate': '',
                        'prism:issn': '',
                        'dc:identifier': [],
                        'dc:publisher': '',
                    }
                ]
            }
        }
    elif keyword == 'none':
        api = {
            'response': None
        }
    else:
        api = {
            'response': {
                'items': [
                    {
                        'title': keyword,
                        'dc:creator': ['test creator'],
                        'description': 'test description',
                        'dc:subject': 'test subject',
                        'prism:publicationName': keyword,
                        'prism:volume': keyword,
                        'prism:number': keyword,
                        'prism:startingPage': '10',
                        'prism:endingPage': '10',
                        'prism:publicationDate': '2025-01-01',
                        'prism:issn': 'test issn',
                        'dc:identifier': [{'@value': 'test doi', '@type': 'cir:DOI'}, {'@value': 'test naid', '@type': 'cir:NAID'}],
                        'dc:publisher': keyword,
                    }
                ]
            }
        }
    
    result = get_cinii_data_by_key(api, keyword if keyword != 'empty' else 'all')
    assert result == expected_result

    if keyword == 'all':
        api['response']['items'].insert(0, {})
        mocker.patch(
            'weko_workspace.utils.get_cinii_numpage',
            return_value={'@value': None}
        )
        result = get_cinii_data_by_key(api, keyword)
        assert result == {
            'title': None,
            'creator': None,
            'description': None,
            'subject': None,
            'sourceTitle': None,
            'volume': None,
            'issue': None,
            'pageStart': None,
            'pageEnd': None,
            'numPages': {'@value': None},
            'date': None,
            'publisher': None,
            'sourceIdentifier': None,
            'relation': None
        }

# .tox/c1/bin/pytest tests/test_utils.py::test_get_cinii_product_identifier -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_cinii_product_identifier():
    data = [
        {'@type': 'cir:DOI', '@value': '10.1234/test-doi'},
        {'@type': 'cir:NAID', '@value': '123456789'}
    ]
    # type1 and type2 are in the list
    result = get_cinii_product_identifier(data, 'cir:DOI', 'cir:NAID')
    assert result == [
        {'@value': '10.1234/test-doi', '@type': 'DOI'},
        {'@value': '123456789', '@type': 'NAID'}
    ]

    # type1 is in the list, type2 is not in the list
    result = get_cinii_product_identifier(data, 'cir:DOI', 'cir:ISBN')
    assert result == [{'@value': '10.1234/test-doi', '@type': 'DOI'}]

    # type1 is not in the list, type2 is in the list
    result = get_cinii_product_identifier(data, 'cir:ISBN', 'cir:NAID')
    assert result == [{'@value': '123456789', '@type': 'NAID'}]

    # type1 and type2 are not in the list
    result = get_cinii_product_identifier(data, 'cir:ISBN', 'cir:ISSN')
    assert result == []

    # Test with empty data
    data = []
    result = get_cinii_product_identifier(data, 'cir:DOI', 'cir:NAID')
    assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_pack_data_with_multiple_type_cinii -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_pack_data_with_multiple_type_cinii():
    # Test with single value
    value = 'test_value'
    result = pack_data_with_multiple_type_cinii(value)
    assert result == [{'@value': value, '@type': 'ISSN'}]

    # Test with list of values
    value = ['value1', 'value2']
    result = pack_data_with_multiple_type_cinii(value)
    assert result == [{'@value': value, '@type': 'ISSN'}]

# .tox/c1/bin/pytest tests/test_utils.py::test_get_cinii_date_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_cinii_date_data():
    # Test with string value that formats as 'YYYY-MM-DD'
    date_value = "2025-01-01"
    result = get_cinii_date_data(date_value)
    assert result == {'@value': date_value, '@type': 'Issued'}

    # Test with string value that formats as 'YYYY年MM月DD日'
    date_value = "2025年01月01日"
    result = get_cinii_date_data(date_value)
    assert result == {'@value': None, '@type': None}

    # Test with string value that formats as 'YYYY-MM'
    date_value = "2025-01"
    result = get_cinii_date_data(date_value)
    assert result == {'@value': None, '@type': None}

    # Test with empty string
    date_value = ""
    result = get_cinii_date_data(date_value)
    assert result == {'@value': None, '@type': None}

# .tox/c1/bin/pytest tests/test_utils.py::test_get_cinii_numpage -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_cinii_numpage(app):
    # startingPage and endingPage are both present and valid
    starting_page = "10"
    ending_page = "20"
    result = get_cinii_numpage(starting_page, ending_page)
    assert result == {'@value': '11'}

    # startingPage and endingPage are both present but invalid
    starting_page = "invalid"
    ending_page = "invalid"
    result = get_cinii_numpage(starting_page, ending_page)
    assert result == {'@value': None}

    # startingPage is present and valid, endingPage is not present
    starting_page = "10"
    ending_page = None
    result = get_cinii_numpage(starting_page, ending_page)
    assert result == {'@value': None}

    # startingPage is not present, endingPage is present and valid
    starting_page = None
    ending_page = "20"
    result = get_cinii_numpage(starting_page, ending_page)
    assert result == {'@value': None}

    # both startingPage and endingPage are not present
    starting_page = None
    ending_page = None
    result = get_cinii_numpage(starting_page, ending_page)
    assert result == {'@value': None}

# .tox/c1/bin/pytest tests/test_utils.py::test_get_cinii_page_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_cinii_page_data(app):
    # value is number
    value = "10"
    result = get_cinii_page_data(value)
    assert result == {'@value': value}

    # value is string
    value = "test_page"
    result = get_cinii_page_data(value)
    assert result == {'@value': None}

# .tox/c1/bin/pytest tests/test_utils.py::test_pack_single_value_as_dict -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_pack_single_value_as_dict():
    value = "test_value"
    result = pack_single_value_as_dict(value)
    assert result == {'@value': value}

# .tox/c1/bin/pytest tests/test_utils.py::test_get_cinii_subject_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_cinii_subject_data(app):
    # Test with list of strings
    value = ["subject1", "subject2"]
    result = get_cinii_subject_data(value, None)
    assert result == [{'@scheme': 'Other', '@value': v, '@language': 'en'} for v in value]

    # Test with empty list
    value = []
    result = get_cinii_subject_data(value, None)
    assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_get_cinii_creator_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_cinii_creator_data(app):
    # Test with list of strings
    value = ["creator1", "creator2"]
    result = get_cinii_creator_data(value)
    assert result == [[{'@value': c, '@language': 'en'}] for c in value]

    # Test with list of strings what value is empty
    value = ["", "creator2"]
    result = get_cinii_creator_data(value)
    assert result == [[{'@value': 'creator2', '@language': 'en'}]]

    # Test with list of strings what value is None
    value = [None, "creator2"]
    result = get_cinii_creator_data(value)
    assert result == [[{'@value': 'creator2', '@language': 'en'}]]

    # Test with empty list
    value = []
    result = get_cinii_creator_data(value)
    assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_get_cinii_title_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_cinii_title_data(app):
    value = "test_title"
    result = get_cinii_title_data(value)
    assert result == [{'@value': value, '@language': 'en'}]

# .tox/c1/bin/pytest tests/test_utils.py::test_get_cinii_description_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_cinii_description_data(app):
    value = "test_description"
    result = get_cinii_description_data(value)
    assert result == [{'@value': value, '@type': 'Abstract', '@language': 'en'}]

# .tox/c1/bin/pytest tests/test_utils.py::test_get_autofill_key_tree -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('item_keys, mock_result, expected_result', [
    (
        ['creator'],
        [
            {
                '@value': 'item_1617186419668.creatorNames.creatorName',
                '@language': 'item_1617186419668.creatorNames.creatorNameLang'
            }
        ],
        {
            'creator': {
                '@value': 'item_1617186419668.creatorNames.creatorName',
                '@language': 'item_1617186419668.creatorNames.creatorNameLang'
            }
        }
    ),
    (
        ['contributor'],
        [
            {
                '@value': 'item_1617349709064.contributorNames.contributorName',
                '@language': 'item_1617349709064.contributorNames.lang'
            }
        ],
        {
            'contributor': {
                '@value': 'item_1617349709064.contributorNames.contributorName',
                '@language': 'item_1617349709064.contributorNames.lang'
            }
        }
    ),
    (
        ['relation'],
        [
            {
                '@value': 'item_1617353299429.subitem_1522306287251.subitem_1522306436033',
                '@type': 'item_1617353299429.subitem_1522306287251.subitem_1522306382014'
            }
        ],
        {
            'relation': {
                '@value': 'item_1617353299429.subitem_1522306287251.subitem_1522306436033',
                '@type': 'item_1617353299429.subitem_1522306287251.subitem_1522306382014'
            }
        }
    ),
    (
        ['issue'],
        [
            {'@value': 'item_1617186981471.subitem_1551256294723'},
            {'@value': 'item_1617187056579.bibliographicIssueNumber'}
        ],
        {
            'issue': [
                {'issue': {'@value': 'item_1617186981471.subitem_1551256294723'}},
                {'issue': {'@value': 'item_1617187056579.bibliographicIssueNumber'}}
            ]
        }
    ),
    (
        ['relation', 'issue'],
        [
            {
                '@value': 'item_1617353299429.subitem_1522306287251.subitem_1522306436033',
                '@type': 'item_1617353299429.subitem_1522306287251.subitem_1522306382014'
            },
            {'@value': 'item_1617186981471.subitem_1551256294723'},
            {'@value': 'item_1617187056579.bibliographicIssueNumber'}
        ],
        {
            'relation': {
                '@value': 'item_1617353299429.subitem_1522306287251.subitem_1522306436033',
                '@type': 'item_1617353299429.subitem_1522306287251.subitem_1522306382014'
            },
            'issue': [
                {'issue': {'@value': 'item_1617186981471.subitem_1551256294723'}},
                {'issue': {'@value': 'item_1617187056579.bibliographicIssueNumber'}}
            ]
        }
    ),
    (
        ['others'],
        [],
        {}
    )
])
def test_get_autofill_key_tree(item_keys, mock_result, expected_result):
    with open('tests/data/item_type/15_form.json', 'r') as f:
        form = json.load(f)

    if item_keys != ['others']:
        with open('tests/data/test_get_autofill_key_tree.json', 'r') as f:
            autofill_item = json.load(f)
        
        item = {}
        for key in item_keys:
            if key in autofill_item:
                item[key] = autofill_item[key]
        
        with patch('weko_workspace.utils.get_key_value', side_effect=mock_result) as mock_get_key_value:
            result = get_autofill_key_tree(form, item)
            assert result == expected_result
            expected_calls = []
            for key in item_keys:
                if key == 'creator':
                    expected_calls.append(
                        call(form, item[key]['creatorName'], item[key]['model_id'])
                    )
                elif key == 'contributor':
                    expected_calls.append(
                        call(form, item[key]['contributorName'], item[key]['model_id'])
                    )
                elif key == 'relation':
                    expected_calls.append(
                        call(form, item[key]['relatedIdentifier'], item[key]['model_id'])
                    )
            mock_get_key_value.assert_has_calls(expected_calls)
        
        input_result = {'key': 'value'}
        with patch('weko_workspace.utils.get_key_value', side_effect=mock_result):
            result = get_autofill_key_tree(form, item, input_result)
            assert result == {**input_result, **expected_result}
        
        if len(item_keys) == 1 and item_keys[0] in ['creator', 'contributor', 'relation']:
            if item_keys[0] == 'creator':
                del item['creator']['creatorName']
            elif item_keys[0] == 'contributor':
                del item['contributor']['contributorName']
            elif item_keys[0] == 'relation':
                del item['relation']['relatedIdentifier']
            with patch('weko_workspace.utils.get_key_value', side_effect=mock_result) as mock_get_key_value:
                result = get_autofill_key_tree(form, item)
                assert result == {}
                mock_get_key_value.assert_not_called()
    else:
        # item's type is not dict
        item = 'not a dict'
        result = get_autofill_key_tree(form, item)
        assert result is None

        # item's type is not dict with input_result
        input_result = {'key': 'value'}
        result = get_autofill_key_tree(form, item, input_result)
        assert result is None

        item = {
            'pubdate': {
                '@value': 'pubdate',
                'model_id': 'pubdate'
            },
            'three': [
                {
                    'three': {
                        '@value': 'three_value1',
                        'model_id': 'three_model_id_1'
                    }
                },
                {
                    'three': {
                        '@value': 'three_value2',
                        'model_id': 'three_model_id_2'
                    }
                },
                {
                    'three': {
                        '@value': 'three_value3',
                        'model_id': 'three_model_id_3'
                    }
                }
            ],
            'no_model_id': {
                '@value': 'no_model_id_value'
            },
            'not_dict': 'not a dict value'
        }
        side_effects = [
            {'@value': 'three_value1'},
            {'@value': 'three_value2'},
            {'@value': 'three_value3'}
        ]
        with patch('weko_workspace.utils.get_key_value', side_effect=side_effects) as mock_get_key_value:
            result = get_autofill_key_tree(form, item)
            assert result == {
                'three': [
                    {'three': {'@value': 'three_value1'}},
                    {'three': {'@value': 'three_value2'}},
                    {'three': {'@value': 'three_value3'}}
                ]
            }
            assert mock_get_key_value.call_count == 3 

# .tox/c1/bin/pytest tests/test_utils.py::test_get_key_value -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('value, parent_key, mock_result, expected_result, expected_value_key_list', [
    (
        {
            "@value": "subitem_1551256294723",
            "model_id": "item_1617186981471"
        },
        'item_1617186981471',
        [{'key': 'item_1617186981471.subitem_1551256294723'}],
        {'@value': 'item_1617186981471.subitem_1551256294723'},
        ['subitem_1551256294723']
    ),
    (
        {
            "@value": "subitem_description",
            "@attributes": {
                "xml:lang": "subitem_description_language",
                "descriptionType": "subitem_description_type"
            },
            "model_id": "item_1617186626617"
        },
        'item_1617186626617',
        [
            {'key': 'item_1617186626617.subitem_description'},
            {'key': 'item_1617186626617.subitem_description_language'},
            {'key': 'item_1617186626617.subitem_description_type'}
        ],
        {
            '@value': 'item_1617186626617.subitem_description',
            '@language': 'item_1617186626617.subitem_description_language',
            '@type': 'item_1617186626617.subitem_description_type'
        },
        ['subitem_description', 'subitem_description_language', 'subitem_description_type']
    ),
    (
        {
            "@value": "subitem_1522646572813",
            "@attributes": {
                "identifierType": "subitem_1522646500366"
            },
            "model_id": "item_1617186920753"
        },
        'item_1617186920753',
        [
            {'key': 'item_1617186920753.subitem_1522646572813'},
            {'key': 'item_1617186920753.subitem_1522646500366'}
        ],
        {
            '@value': 'item_1617186920753.subitem_1522646572813',
            '@type': 'item_1617186920753.subitem_1522646500366'
        },
        ['subitem_1522646572813', 'subitem_1522646500366']
    ),
    (
        {
            "@value": "subitem_1523261968819",
            "@attributes": {
                "xml:lang": "subitem_1522299896455",
                "subjectURI": "subitem_1522300048512",
                "subjectScheme": "subitem_1522300014469"
            },
            "model_id": "item_1617186609386"
        },
        'item_1617186609386',
        [
            {'key': 'item_1617186609386.subitem_1523261968819'},
            {'key': 'item_1617186609386.subitem_1522299896455'},
            {'key': 'item_1617186609386.subitem_1522300014469'},
            {'key': 'item_1617186609386.subitem_1522300048512'}
        ],
        {
            '@value': 'item_1617186609386.subitem_1523261968819',
            '@language': 'item_1617186609386.subitem_1522299896455',
            '@scheme': 'item_1617186609386.subitem_1522300014469',
            '@URI': 'item_1617186609386.subitem_1522300048512'
        },
        ['subitem_1523261968819', 'subitem_1522299896455', 'subitem_1522300014469', 'subitem_1522300048512']
    ),
    (
        {
            "@value": "subitem_1522300722591",
            "@attributes": {
                "dateType": "subitem_1522300695726"
            },
            "model_id": "item_1617186660861"
        },
        'item_1617186660861',
        [
            {'key': 'item_1617186660861.subitem_1522300722591'},
            {'key': 'item_1617186660861.subitem_1522300695726'}
        ],
        {
            '@value': 'item_1617186660861.subitem_1522300722591',
            '@type': 'item_1617186660861.subitem_1522300695726'
        },
        ['subitem_1522300722591', 'subitem_1522300695726']
    ),
    (
        {
            '@attribute': {
                'no_value': 'subitem_1522300722591'
            }
        },
        'item_123456789012',
        [],
        {},
        []
    )
])
def test_get_key_value(value, parent_key, mock_result, expected_result, expected_value_key_list):
    with open('tests/data/item_type/15_form.json', 'r') as f:
        form = json.load(f)
    
    with patch('weko_workspace.utils.get_autofill_key_path', side_effect=mock_result) as mock_get_autofill_key_path:
        result = get_key_value(form, value, parent_key)
        assert result == expected_result
        expect_call_args = []
        for key in expected_value_key_list:
            expect_call_args.append(call(form, parent_key, key))
        if expected_value_key_list:
            mock_get_autofill_key_path.assert_has_calls(expect_call_args)
        else:
            mock_get_autofill_key_path.assert_not_called()

# .tox/c1/bin/pytest tests/test_utils.py::test_get_item_id -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_item_id(app, mocker_itemtype):
    class MockMapping:
        def items(self):
            raise Exception("Mocked items method")
    result = get_item_id(15)
    with open('tests/data/test_get_item_id.json', 'r') as f:
        expected_result = json.load(f)
    assert result == expected_result

    # Test with mapping having no items
    with patch('weko_workspace.utils.Mapping.get_record', return_value={}):
        result = get_item_id(15)
        assert result == {}

    # Test with error
    with patch('weko_workspace.utils.Mapping.get_record', return_value=MockMapping()):
        result = get_item_id(15)
        assert result == {'error': 'Mocked items method'}

# .tox/c1/bin/pytest tests/test_utils.py::test_get_cinii_autofill_item -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_cinii_autofill_item(app):
    with open('tests/data/test_get_item_id.json', 'r') as f:
        mock_item = json.load(f)
    with patch('weko_workspace.utils.get_item_id', return_value=mock_item):
        result = get_cinii_autofill_item(15)
        with open('tests/data/test_get_cinii_autofill_item.json', 'r') as f:
            expected_result = json.load(f)
        assert result == expected_result
    
    # Test with empty item
    with patch('weko_workspace.utils.get_item_id', return_value={}):
        result = get_cinii_autofill_item(15)
        assert result == {}

# .tox/c1/bin/pytest tests/test_utils.py::test_get_autofill_key_path -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_autofill_key_path(app):
    with open('tests/data/item_type/15_form.json', 'r') as f:
        form = json.load(f)
    
    mock_side_effect = [
        (False, None),
        (True, 'item_1617187056579.bibliographicIssueDates.bibliographicIssueDateType'),
    ]
    with patch('weko_workspace.utils.get_specific_key_path', side_effect=mock_side_effect) as mock_get_specific_key_path:
        result = get_autofill_key_path(form, 'item_1617187056579', 'bibliographicIssueDates.bibliographicIssueDateType')
        assert result == {'key': 'item_1617187056579.bibliographicIssueDates.bibliographicIssueDateType'}
        assert mock_get_specific_key_path.call_count == 2

    # Test with non-existing key
    with patch('weko_workspace.utils.get_specific_key_path',  return_value=(False, None)):
        result = get_autofill_key_path(form, 'item_1617187056579', 'nonExistingKey')
        assert result == {'key': None}
    
    with patch('weko_workspace.utils.get_specific_key_path', side_effect=Exception("Mocked exception")):
        result = get_autofill_key_path(form, 'item_1617187056579', 'bibliographicIssueDates.bibliographicIssueDateType')
        assert result == {'key': None, 'error': 'Mocked exception'}

# .tox/c1/bin/pytest tests/test_utils.py::test_get_specific_key_path -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_specific_key_path():
    des_key = ['bibliographicIssueDates', 'bibliographicIssueDateType']
    form = {
        "key": "item_1617187056579.bibliographicIssueDates",
        "type": "fieldset",
        "items": [
            {
                "key": "item_1617187056579.bibliographicIssueDates.bibliographicIssueDateType",
                "type": "select",
                "title": "日付タイプ",
                "titleMap": [
                    {
                        "name": "Issued",
                        "value": "Issued"
                    }
                ],
                "title_i18n": {
                    "en": "Date Type",
                    "ja": "日付タイプ"
                },
                "title_i18n_temp": {
                    "en": "Date Type",
                    "ja": "日付タイプ"
                }
            },
            {
                "key": "item_1617187056579.bibliographicIssueDates.bibliographicIssueDate",
                "type": "template",
                "title": "日付",
                "format": "yyyy-MM-dd",
                "title_i18n": {
                    "en": "Date",
                    "ja": "日付"
                },
                "templateUrl": "/static/templates/weko_deposit/datepicker_multi_format.html",
                "title_i18n_temp": {
                    "en": "Date",
                    "ja": "日付"
                }
            }
        ],
        "title": "発行日",
        "title_i18n": {
            "en": "Issue Date",
            "ja": "発行日"
        },
        "title_i18n_temp": {
            "en": "Issue Date",
            "ja": "発行日"
        }
    }
    existed, result = get_specific_key_path(des_key, form)
    assert existed is True
    assert result == 'item_1617187056579.bibliographicIssueDates.bibliographicIssueDateType'
    
    # Test with non-existing key
    des_key = ['bibliographicIssueDates', 'nonExistingKey']
    existed, result = get_specific_key_path(des_key, form)
    assert existed is False
    assert result is None

    # Test with form not having 'key'
    form = {
        "type": "fieldset",
        "items": [
            {
                "key": "item_1617187056579.bibliographicIssueDates.bibliographicIssueDateType",
                "type": "select",
                "title": "日付タイプ"
            }
        ],
        "title": "発行日"
    }
    des_key = ['bibliographicIssueDates', 'bibliographicIssueDateType']
    existed, result = get_specific_key_path(des_key, form)
    assert existed is True
    assert result == 'item_1617187056579.bibliographicIssueDates.bibliographicIssueDateType'

    # Test with form type not dict or list
    form = "not a dict or list"
    existed, result = get_specific_key_path(des_key, form)
    assert existed is False
    assert result is None

# .tox/c1/bin/pytest tests/test_utils.py::test_build_form_model -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('form_model, form_key, expected_value',[
    (
        {},
        {
            '@value': 'item_1617186419668.creatorNames.creatorName',
            '@language': 'item_1617186419668.creatorNames.creatorNameLang'
        },
        {
            '@value': {
                'item_1617186419668': {
                    'creatorNames': {
                        'creatorName': '@value'
                    }
                }
            },
            '@language': {
                'item_1617186419668': {
                    'creatorNames': {
                        'creatorNameLang': '@language'
                    }
                }
            }
        }
    ),
    (
        {},
        {
            '@value': 'item_1617605131499[].filesize[].value'
        },
        {
            '@value': {
                'item_1617605131499': [
                    {
                        'filesize': [
                            {
                                'value': '@value'
                            }
                        ]
                    }
                ]
            }
        }
    ),
    ({}, {'@value': {'key': 'value'}}, {}),
    ({}, 'item_123456789012', {}),
    ([], [], []),
    ('', ['item_123456789012'], '')
])
def test_build_form_model(form_model, form_key, expected_value):
    build_form_model(form_model, form_key)
    assert form_model == expected_value

# .tox/c1/bin/pytest tests/test_utils.py::test_build_model -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_build_model():
    # form_model is a dict and form_key is including '[]'
    form_model = {}
    form_key = 'item_123456789012[]'
    build_model(form_model, form_key)
    assert form_model == {'item_123456789012': []}

    # form_model is a dict and form_key is not including '[]'
    form_model = {}
    form_key = 'item_123456789012'
    build_model(form_model, form_key)
    assert form_model == {'item_123456789012': {}}

    # form_model is a list and form_key is including '[]'
    form_model = []
    form_key = 'item_123456789012[]'
    build_model(form_model, form_key)
    assert form_model == [{'item_123456789012': []}]

    # form_model is a list and form_key is not including '[]'
    form_model = []
    form_key = 'item_123456789012'
    build_model(form_model, form_key)
    assert form_model == [{'item_123456789012': {}}]

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jalc_data_by_key -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
@pytest.mark.parametrize('keyword, expected_result', [
    ('title', {'title': [{'@value': 'test title', '@language': 'ja'}]}),
    ('creator', {'creator': [[{'@value': 'Doe John', '@language': 'en'}]]}),
    ('sourceTitle', {'sourceTitle': [{'@value': 'test subject', '@language': 'ja'}]}),
    ('volume', {'volume': {'@value': '1'}}),
    ('issue', {'issue': {'@value': '1'}}),
    ('pageStart', {'pageStart': {'@value': '10'}}),
    ('pageEnd', {'pageEnd': {'@value': '10'}}),
    ('numPages', {'numPages': {'@value': '1'}}),
    ('date', {'date': {'@value': '2025-01-01', '@type': 'Issued'}}),
    ('publisher', {'publisher': [{'@value': 'Publisher A', '@language': 'ja'}]}),
    ('sourceIdentifier', {'sourceIdentifier': [{'@value': '1234-5678', '@type': 'ISSN'}]}),
    ('relation', {'relation': [{'@value': '10.1234/56789'}]}),
    ('all', {
        'title': [{'@value': 'test title', '@language': 'ja'}],
        'creator': [[{'@value': 'Doe John', '@language': 'en'}]],
        'sourceTitle': [{'@value': 'test subject', '@language': 'ja'}],
        'volume': {'@value': '1'},
        'issue': {'@value': '1'},
        'pageStart': {'@value': '10'},
        'pageEnd': {'@value': '10'},
        'numPages': {'@value': '1'},
        'date': {'@value': '2025-01-01', '@type': 'Issued'},
        'publisher': [{'@value': 'Publisher A', '@language': 'ja'}],
        'sourceIdentifier': [{'@value': '1234-5678', '@type': 'ISSN'}],
        'relation': [{'@value': '10.1234/56789'}]
    }),
    ('empty', {
        'title': None,
        'creator': None,
        'sourceTitle': None,
        'volume': None,
        'issue': None,
        'pageStart': None,
        'pageEnd': None,
        'numPages': {'@value': '1'},
        'date': None,
        'publisher': None,
        'sourceIdentifier': None,
        'relation': None
    }),
    ('none', {})
])
def test_get_jalc_data_by_key(app, mocker, keyword, expected_result):
    mocker.patch(
        'weko_workspace.utils.get_jalc_title_data',
        return_value=[{'@value': 'test title', '@language': 'ja'}]
    )
    mocker.patch(
        'weko_workspace.utils.get_jalc_creator_data',
        return_value=[[{'@value': 'Doe John', '@language': 'en'}]]
    )
    mocker.patch(
        'weko_workspace.utils.get_jalc_source_title_data',
        return_value=[{'@value': 'test subject', '@language': 'ja'}]
    )
    mocker.patch(
        'weko_workspace.utils.pack_single_value_as_dict',
        return_value={'@value': '1'}
    )
    mocker.patch(
        'weko_workspace.utils.get_jalc_page_data',
        return_value={'@value': '10'}
    )
    mocker.patch(
        'weko_workspace.utils.get_jalc_numpage',
        return_value={'@value': '1'}
    )
    mocker.patch(
        'weko_workspace.utils.get_jalc_date_data',
        return_value={'@value': '2025-01-01', '@type': 'Issued'}
    )
    mocker.patch(
        'weko_workspace.utils.get_jalc_publisher_data',
        return_value=[{'@value': 'Publisher A', '@language': 'ja'}]
    )
    mocker.patch(
        'weko_workspace.utils.pack_data_with_multiple_type_jalc',
        return_value=[{'@value': '1234-5678', '@type': 'ISSN'}]
    )
    mocker.patch(
        'weko_workspace.utils.get_jalc_product_identifier',
        return_value=[{'@value': '10.1234/56789'}]
    )

    if keyword == 'empty':
        api = {
            'response': {
                'data': {
                    'title_list': [{}],
                    'creator_list': [],
                    'journal_title_name_list': [],
                    'volume': '',
                    'issue': '',
                    'first_page': '',
                    'last_page': '',
                    'date': '',
                    'publisher_list': [],
                    'journal_id_list': [],
                    'doi': ''
                }
            }
        }
    elif keyword == 'none':
        api = {
            'response': None
        }
    else:
        api = {
            'response': {
                'data': {
                    'title_list': [
                        {
                            'title': 'test title',
                            'lang': 'ja'
                        }
                    ],
                    'creator_list': [
                        {
                            'sequence': 1,
                            'type': 'person',
                            'names': [
                                {
                                    'lang': 'en',
                                    'last_name': 'Doe',
                                    'first_name': 'John'
                                }
                            ],
                            'affiliation_list': [
                                {
                                    'affiliation_name': 'University A',
                                    'sequence': 1,
                                    'lang': 'en'
                                }
                            ]
                        }
                    ],
                    'journal_title_name_list': [
                        {
                            'journal_title_name': 'test subject',
                            'type': 'full',
                            'lang': 'ja'
                        }
                    ],
                    'volume': '1',
                    'issue': '1',
                    'first_page': '10',
                    'last_page': '10',
                    'date': '2025-01-01',
                    'publisher_list': [
                        {
                            'publisher_name': 'Publisher A',
                            'lang': 'ja'
                        }
                    ],
                    'journal_id_list': [
                        {
                            'journal_id': '1234-5678',
                            'type': 'ISSN',
                            'issn_type': 'print'
                        }
                    ],
                    'doi': '10.1234/56789'
                }
            }
        }
    
    result = get_jalc_data_by_key(api, keyword if keyword != 'empty' else 'all')
    assert result == expected_result

    if keyword == 'title':
        api['response']['data']['title_list'].insert(0, {})
        result = get_jalc_data_by_key(api, keyword)
        assert result == {}


# .tox/c1/bin/pytest tests/test_utils.py::test_get_jalc_publisher_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_jalc_publisher_data(app):
    # Test with valid data
    data = [
        {
            'publisher_name': '出版者A',
            'lang': 'ja'
        },
        {
            'publisher_name': 'Publisher B'
        }
    ]
    result = get_jalc_publisher_data(data)
    assert result == [
        {
            '@value': '出版者A',
            '@language': 'ja'
        },
        {
            '@value': 'Publisher B',
            '@language': 'en'
        }
    ]

    # Test with empty data
    data = []
    result = get_jalc_publisher_data(data)
    assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jalc_title_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_jalc_title_data(app):
    # data has 'lang' key
    data = {
        'title': 'test title',
        'lang': 'ja'
    }
    result = get_jalc_title_data(data)
    assert result == [{'@value': 'test title', '@language': 'ja'}]

    # data does not have 'lang' key
    data = {
        'title': 'test title'
    }
    result = get_jalc_title_data(data)
    assert result == [{'@value': 'test title', '@language': 'en'}]

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jalc_creator_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_jalc_creator_data(app):
    # Test with valid data
    data = [
        {
            'sequence': 1,
            'type': 'person',
            'names': [
                {
                    'lang': 'en',
                    'last_name': 'Doe',
                    'first_name': 'John',
                }
            ],
            'affiliation_list': [
                {
                    'affiliation_name': 'University A',
                    'sequence': 1,
                    'lang': 'en'
                }
            ]
        },
        {
            'sequence': 2,
            'type': 'person',
            'names': [
                {
                    'last_name': '山田',
                    'first_name': '太郎',
                },
                {
                    'lang': 'en',
                    'last_name': 'Yamada',
                    'first_name': 'Taro',
                }
            ],
            'affiliation_list': [
                {
                    'affiliation_name': 'B大学',
                    'sequence': 2,
                    'lang': 'ja'
                },
                {
                    'affiliation_name': 'University B',
                    'sequence': 2,
                    'lang': 'en'
                }
            ]
        },
        {
            'sequence': 3,
            'type': 'other'
        }
    ]
    result = get_jalc_creator_data(data)
    assert result == [
        [
            {
                '@value': 'Doe John',
                '@language': 'en'
            }
        ],
        [
            {
                '@value': '山田 太郎',
                '@language': 'en'
            },
            {
                '@value': 'Yamada Taro',
                '@language': 'en'
            }
        ]
    ]

    # Test with empty data
    data = []
    result = get_jalc_creator_data(data)
    assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jalc_source_title_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_jalc_source_title_data(app):
    # Test with valid data
    data = [
        {
            'journal_title_name': 'Journal of Example Studies',
            'type': 'full',
            'lang': 'en'
        },
        {
            'journal_title_name': '例の研究ジャーナル',
            'type': 'full',
        }
    ]
    result = get_jalc_source_title_data(data)
    assert result == [
        {
            '@value': 'Journal of Example Studies',
            '@language': 'en'
        },
        {
            '@value': '例の研究ジャーナル',
            '@language': 'en'
        }
    ]

    # Test with empty data
    data = []
    result = get_jalc_source_title_data(data)
    assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jalc_page_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_jalc_page_data(app):
    # Test with valid page number
    value = "10"
    result = get_jalc_page_data(value)
    assert result == {'@value': value}

    # Test with invalid page number
    value = "invalid"
    result = get_jalc_page_data(value)
    assert result == {'@value': None}

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jalc_numpage -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_jalc_numpage(app):
    # Test with valid startingPage and endingPage
    starting_page = "10"
    ending_page = "20"
    result = get_jalc_numpage(starting_page, ending_page)
    assert result == {'@value': '11'}

    # Test with invalid startingPage and endingPage
    starting_page = "invalid"
    ending_page = "invalid"
    result = get_jalc_numpage(starting_page, ending_page)
    assert result == {'@value': None}

    # Test with only startingPage present
    starting_page = "10"
    ending_page = None
    result = get_jalc_numpage(starting_page, ending_page)
    assert result == {'@value': None}

    # Test with only endingPage present
    starting_page = None
    ending_page = "20"
    result = get_jalc_numpage(starting_page, ending_page)
    assert result == {'@value': None}

    # Test with neither startingPage nor endingPage present
    starting_page = None
    ending_page = None
    result = get_jalc_numpage(starting_page, ending_page)
    assert result == {'@value': None}

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jalc_date_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_jalc_date_data():
    # Test with string value that formats as 'YYYY-MM-DD'
    date_value = "2025-01-01"
    result = get_jalc_date_data(date_value)
    assert result == {'@value': date_value, '@type': 'Issued'}

    # Test with string value that formats as 'YYYY年MM月DD日'
    date_value = "2025年01月01日"
    result = get_jalc_date_data(date_value)
    assert result == {'@value': None, '@type': None}

    # Test with string value that formats as 'YYYY-MM'
    date_value = "2025-01"
    result = get_jalc_date_data(date_value)
    assert result == {'@value': None, '@type': None}

    # Test with empty string
    date_value = ""
    result = get_jalc_date_data(date_value)
    assert result == {'@value': None, '@type': None}

# .tox/c1/bin/pytest tests/test_utils.py::test_pack_data_with_multiple_type_jalc -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_pack_data_with_multiple_type_jalc():
    # Test with valid data
    data = [
        {
            'journal_id': '1234-5678',
            'type': 'ISSN',
            'issn_type': 'print'
        },
        {
            'journal_id': 'AA12345678',
            'type': 'NCID'
        }
    ]
    result = pack_data_with_multiple_type_jalc(data)
    assert result == [
        {
            '@value': '1234-5678',
            '@type': 'ISSN'
        },
        {
            '@value': 'AA12345678',
            '@type': 'NCID'
        }
    ]

    # Test with empty data
    data = []
    result = pack_data_with_multiple_type_jalc(data)
    assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_get_jalc_product_identifier -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_jalc_product_identifier():
    data = '10.1234/56789'
    result = get_jalc_product_identifier(data)
    assert result == [{'@value': '10.1234/56789'}]

# .tox/c1/bin/pytest tests/test_utils.py::test_get_datacite_title_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_datacite_title_data(app):
    # Test with valid data
    data = [
        {
            'title': 'Test Title',
            'lang': 'en'
        },
        {
            'title': 'テストタイトル'
        }
    ]
    result = get_datacite_title_data(data)
    assert result == [
        {'@value': 'Test Title', '@language': 'en'},
        {'@value': 'テストタイトル', '@language': 'en'}
    ]

    # Test with empty data
    data = []
    result = get_datacite_title_data(data)
    assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_get_datacite_creator_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_datacite_creator_data(app):
    # Test with valid data
    data = [
        {
            'name': 'Doe, John',
            'affiliation': [],
            'nameIdentifiers': []
        },
        {
            'affiliation': [
                'University A',
            ],
            'nameIdentifiers': [
                {
                    'nameIdentifier': 'http://orcid.org/0000-0001-2345-6789',
                    'nameIdentifierScheme': 'ORCID',
                    'schemeURI': 'http://orcid.org'
                }
            ]
        }
    ]
    result = get_datacite_creator_data(data)
    assert result == [[{'@value': 'Doe, John', '@language': 'en'}]]

    # Test with empty data
    data = []
    result = get_datacite_creator_data(data)
    assert result == []

# .tox/c1/bin/pytest tests/test_utils.py::test_get_datacite_contributor_data -vv -s --cov-branch --cov=weko_workspace --cov-report=term --basetemp=/code/modules/weko-workspace/tests/.tox/c1/tmp
def test_get_datacite_contributor_data(app):
    # Test with valid data
    data = [
        {
            'name': 'Smith, Jane',
            'givenName': 'Jane',
            'familyName': 'Smith',
            'affiliation': [
                'Institute A',
            ],
            'contributorType': 'ProjectLeader',
            'nameIdentifiers': [
                {
                    'nameIdentifier': 'http://orcid.org/0000-0001-2345-6789',
                    'nameIdentifierScheme': 'ORCID',
                    'schemeURI': 'http://orcid.org'
                }
            ]
        },
        {
            'givenName': 'Taro',
            'familyName': 'Yamada',
            'affiliation': [
                'Institute B',
            ],
            'contributorType': 'Editor',
            'nameIdentifiers': [
                {
                    'nameIdentifier': 'http://orcid.org/0000-0002-3456-7890',
                    'nameIdentifierScheme': 'ORCID',
                    'schemeURI': 'http://orcid.org'
                }
            ]
        }
    ]
    result = get_datacite_contributor_data(data)
    assert result == [[{'@value': 'Smith, Jane', '@language': 'en'}]]

    # Test with empty data
    data = []
    result = get_datacite_contributor_data(data)
    assert result == []
