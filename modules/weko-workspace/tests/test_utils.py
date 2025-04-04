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
from mock import patch
import datetime
from flask_babelex import gettext as _
from flask_login.utils import login_user
from weko_user_profiles import UserProfile

import json
from unittest.mock import Mock, patch
import pytest
from sqlalchemy.exc import SQLAlchemyError
from flask_login import login_user
from weko_workspace.models import WorkspaceDefaultConditions
import requests

from weko_workspace.utils import *
from weko_workspace.defaultfilters import DEFAULT_FILTERS

# ===========================def get_workspace_filterCon():=====================================
# ワークスペースのフィルター条件を取得する関数のテスト
@pytest.mark.parametrize('users_index, mock_setup, expected_response', [
    (0, 
     {'return_value': {'default_con': {"favorite": {"label": "お気に入り", "options": ["あり", "なし"], "default": "あり"}}}},  
     ({"favorite": {"label": "お気に入り", "options": ["あり", "なし"], "default": "あり"}}, True)),

    (0, 
     {'return_value': None},  
     (DEFAULT_FILTERS, False)),

    (0, 
     {'side_effect': SQLAlchemyError("Database error")},  
     (DEFAULT_FILTERS, False)),

    (0, 
     {'side_effect': Exception("Unexpected error")},  
     (DEFAULT_FILTERS, False)),
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
# Elasticsearchからアイテムリストを取得する関数のテスト
@pytest.mark.parametrize('mock_setup, expected_response, expected_exception', [
    (
        {
            'first_response': Mock(status_code=200, json=lambda: {"hits": {"total": 2}}),
            'second_response': Mock(status_code=200, json=lambda: {
                "hits": {
                    "hits": [
                        {"id": "1", "metadata": {"title": ["Title 1"]}},
                        {"id": "2", "metadata": {"title": ["Title 2"]}}
                    ]
                }
            })
        },
        {
            "hits": {
                "hits": [
                    {"id": "1", "metadata": {"title": ["Title 1"]}},
                    {"id": "2", "metadata": {"title": ["Title 2"]}}
                ]
            }
        },
        None
    ),
    (
        {
            'first_response': Mock(status_code=404, json=lambda: {"error": "Not Found"}, raise_for_status=lambda: (_ for _ in ()).throw(requests.exceptions.HTTPError("404 Not Found"))),
            'second_response': None
        },
        None,
        requests.exceptions.RequestException
    ),
    (
        {
            'first_response': Mock(status_code=200, json=lambda: {"hits": {"total": 2}}),
            'second_response': Mock(status_code=500, json=lambda: {"error": "Server Error"}, raise_for_status=lambda: (_ for _ in ()).throw(requests.exceptions.HTTPError("500 Server Error")))
        },
        None,
        requests.exceptions.RequestException
    ),
    (
        {
            'first_response': Mock(status_code=200, json=lambda: {"hits": {"total": 2}}),
            'second_response': Mock(status_code=200, text="invalid json", json=lambda: (_ for _ in ()).throw(json.JSONDecodeError("Invalid JSON", "invalid json", 0)))
        },
        None,
        json.JSONDecodeError
    ),
    (
        {
            'first_response': Mock(status_code=200, json=lambda: {"not_hits": "invalid data"}),
            'second_response': None
        },
        None,
        KeyError
    ),
])
def test_get_es_itemlist(mock_setup, expected_response, expected_exception, app):
    with patch('requests.get') as mock_get:
        mock_get.side_effect = (
            [mock_setup['first_response'], mock_setup['second_response']]
            if mock_setup['second_response'] is not None
            else [mock_setup['first_response']]
        )
        with app.test_request_context(base_url='http://test.example.com'):
            result = get_es_itemlist()
            assert result == expected_response
            if expected_response is not None:
                mock_get.assert_called_with(
                    'http://test.example.com/api/workspace/search?size=2',
                    headers={"Accept": "application/json"}
                )
        if mock_setup['second_response'] is not None:
            assert mock_get.call_count == 2
        else:
            assert mock_get.call_count == 1

# ===========================def get_workspace_status_management():=====================================
# ワークスペースのステータス管理情報を取得する関数のテスト
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
# TODO アイテムのステータスを取得する関数のテスト（未完成）
@pytest.mark.parametrize('recid, expected_response', [
    (123, "Unlinked-testdata"),
])
def test_get_item_status(recid, expected_response):
    result = get_item_status(recid)
    assert result == expected_response

# ===========================def get_userNm_affiliation():=====================================
# TODO ユーザー名と所属情報を取得する関数のテスト（未完成）
@pytest.mark.parametrize('mock_setup, expected_response', [
    (
        {
            'username': "test_user"
        },
        ("test_user", "ivis-testdata")
    ),
    (
        {
            'username': None
        },
        ("contributor@test.org", "ivis-testdata")
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