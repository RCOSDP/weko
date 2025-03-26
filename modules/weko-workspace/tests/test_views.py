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
from datetime import datetime
from flask import url_for
from flask_babelex import gettext as _
from invenio_accounts.testutils import login_user_via_session as login
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import Mock, patch
from weko_workspace.models import WorkspaceDefaultConditions
from weko_workspace.ext import WekoWorkspace
import pytest

# ===========================def __init__(self, app=None):():=====================================
def test_ext_class_init(app):
    WekoWorkspace.__init__(app)
    assert 1 == 1

# ===========================def reset_filters():=====================================
@pytest.mark.parametrize(
    "users_index, status_code, mock_setup, expected_response",
    [
        (
            0,
            200,
            {"return_value": None},
            {"status": "success", "message": "Successfully reset default conditions."},
        ),
        (
            0,
            200,
            {"return_value": None},
            {"status": "success", "message": "No default conditions found to reset."},
        ),
        (
            0,
            500,
            {"side_effect": SQLAlchemyError("Database error")},
            {
                "status": "error",
                "message": "Failed to reset default conditions due to database error: Database error",
            },
        ),
        (
            0,
            500,
            {"side_effect": Exception("Unexpected error")},
            {
                "status": "error",
                "message": "Unexpected error occurred: Unexpected error",
            },
        ),
    ],
)
def test_reset_filters(
    client,
    users,
    users_index,
    status_code,
    mock_setup,
    expected_response,
    workspaceData,
):
    login(client=client, email=users[users_index]["email"])

    if (
        status_code == 200
        and expected_response.get("message") == "Successfully reset default conditions."
    ):
        if workspaceData:
            mock_setup["return_value"] = workspaceData[0]
        else:
            raise ValueError(
                "workspaceData is empty. Please ensure data is inserted correctly."
            )

    with patch("weko_workspace.views.WorkspaceDefaultConditions.query") as mock_query:
        mock_filter = mock_query.filter_by.return_value
        mock_filter.first = Mock(**mock_setup)

        url = url_for("weko_workspace.reset_filters")
        res = client.delete(url)
        assert res.status_code == status_code
        assert res.json == expected_response


# ===========================def save_filters():=====================================
@pytest.mark.parametrize(
    "users_index, status_code, mock_setup, post_data, expected_response",
    [
        (
            1,
            200,
            {"return_value": None},
            {"filters": {"key": "value"}},
            {"status": "success", "message": "Successfully saved default conditions."},
        ),
        (
            0,
            200,
            {"return_value": None},
            {"filters": {"key": "value"}},
            {"status": "success", "message": "Successfully saved default conditions."},
        ),
        (
            1,
            500,
            {"side_effect": SQLAlchemyError("Database error")},
            {"filters": {"key": "value"}},
            {
                "status": "error",
                "message": "Failed to save default conditions due to database error: Database error",
            },
        ),
        (
            1,
            500,
            {"side_effect": Exception("Unexpected error")},
            {"filters": {"key": "value"}},
            {
                "status": "error",
                "message": "Unexpected error occurred: Unexpected error",
            },
        ),
    ],
)
def test_save_filters(
    client,
    users,
    users_index,
    status_code,
    mock_setup,
    post_data,
    expected_response,
    workspaceData,
    db,
):
    login(client=client, email=users[users_index]["email"])

    if (
        status_code == 200
        and expected_response.get("message") == "Successfully saved default conditions."
    ):
        if workspaceData and users_index == 0:
            mock_setup["return_value"] = workspaceData[0]
        else:
            mock_setup["return_value"] = None

    with patch("weko_workspace.views.WorkspaceDefaultConditions.query") as mock_query:
        mock_filter = mock_query.filter_by.return_value
        mock_filter.first = Mock(**mock_setup)

        url = url_for("weko_workspace.save_filters")
        # print(f"Generated URL: {url}")

        if status_code == 500:
            with patch("weko_workspace.views.db.session.commit") as mock_commit:
                with patch("weko_workspace.views.db.session.rollback") as mock_rollback:
                    if "side_effect" in mock_setup:
                        mock_filter.first.side_effect = mock_setup["side_effect"]
                    try:
                        res = client.post(url, json=post_data)
                        # print(f"Response status: {res.status_code}")
                        # print(f"Response data: {res.data.decode('utf-8')}")
                        assert res.status_code == status_code
                        assert res.json == expected_response
                        # mock_rollback.assert_called_once()
                        # mock_commit.assert_not_called()
                    except Exception as e:
                        # print(f"Exception during client.post: {str(e)}")
                        raise
        else:
            with patch("weko_workspace.views.db.session.add") as mock_add:
                with patch("weko_workspace.views.db.session.commit") as mock_commit:
                    res = client.post(url, json=post_data)

                    # print(f"Response status: {res.status_code}")
                    # print(f"Response data: {res.data.decode('utf-8')}")

                    assert res.status_code == status_code
                    assert res.json == expected_response

                    if mock_setup.get("return_value") is not None:
                        record = mock_setup["return_value"]
                        assert record.default_con == post_data
                        assert isinstance(record.updated, datetime)
                    else:
                        assert mock_add.call_count >= 1
                        workspace_calls = [
                            call
                            for call in mock_add.call_args_list
                            if isinstance(call[0][0], WorkspaceDefaultConditions)
                        ]
                        assert len(workspace_calls) == 1
                        added_record = workspace_calls[0][0][0]
                        assert added_record.user_id == users[users_index]["id"]
                        assert added_record.default_con == post_data
                        assert isinstance(added_record.created, datetime)
                        assert isinstance(added_record.updated, datetime)


# ===========================def update_workspace_status_management(): =====================================
@pytest.mark.parametrize(
    "users_index, status_code, mock_setup, post_data, expected_response",
    [
        (
            0,
            200,
            {"return_value": None},
            {"itemRecid": "new_recid", "type": "1", "favoriteSts": True},
            {"success": True},
        ),
        (
            0,
            200,
            {"return_value": None},
            {"itemRecid": "new_recid", "type": "2", "readSts": True},
            {"success": True},
        ),
        (
            0,
            200,
            {"return_value": {"user_id": 1, "recid": "123"}},
            {"itemRecid": "123", "type": "1", "favoriteSts": True},
            {"success": True},
        ),
        (
            0,
            200,
            {"return_value": {"user_id": 1, "recid": "123"}},
            {"itemRecid": "123", "type": "2", "readSts": True},
            {"success": True},
        ),
        (
            0,
            400,
            {"return_value": {"user_id": 1, "recid": "123"}},
            {"itemRecid": "123", "type": "3"},
            {"success": False, "message": "Invalid type"},
        ),
    ],
)
def test_update_workspace_status_management(
    client,
    users,
    users_index,
    status_code,
    mock_setup,
    post_data,
    expected_response,
    workspaceData,
):
    login(client=client, email=users[users_index]["email"])

    if status_code == 200 and mock_setup.get("return_value") is not None:
        mock_setup["return_value"] = {
            "user_id": workspaceData[1].user_id,
            "recid": workspaceData[1].recid,
            "is_favorited": workspaceData[1].is_favorited,
            "is_read": workspaceData[1].is_read,
        }

    with patch(
        "weko_workspace.views.get_workspace_status_management"
    ) as mock_get_status:
        mock_get_status.return_value = mock_setup["return_value"]

        with patch("weko_workspace.views.insert_workspace_status") as mock_insert:
            with patch("weko_workspace.views.update_workspace_status") as mock_update:
                url = url_for("weko_workspace.update_workspace_status_management")
                res = client.post(url, json=post_data)
                # print(f"Response status: {res.status_code}")
                # print(f"Response data: {res.data.decode('utf-8')}")
                assert res.status_code == status_code
                assert res.json == expected_response

                if status_code == 200:
                    if mock_setup["return_value"] is None:
                        mock_insert.assert_called_once()
                        mock_update.assert_not_called()
                        call_args = mock_insert.call_args[1]
                        assert call_args["user_id"] == users[users_index]["id"]
                        assert call_args["recid"] == post_data["itemRecid"]
                        if post_data["type"] == "1":
                            assert call_args["is_favorited"] == post_data.get(
                                "favoriteSts", False
                            )
                            assert call_args["is_read"] == False
                        elif post_data["type"] == "2":
                            assert call_args["is_favorited"] == False
                            assert call_args["is_read"] == post_data.get(
                                "readSts", False
                            )
                    else:
                        mock_insert.assert_not_called()
                        mock_update.assert_called_once()
                        call_args = mock_update.call_args[1]
                        assert call_args["user_id"] == users[users_index]["id"]
                        assert call_args["recid"] == post_data["itemRecid"]
                        if post_data["type"] == "1":
                            assert call_args["is_favorited"] == post_data.get(
                                "favoriteSts"
                            )
                            assert "is_read" not in call_args
                        elif post_data["type"] == "2":
                            assert call_args["is_read"] == post_data.get("readSts")
                            assert "is_favorited" not in call_args
                elif status_code == 400:
                    mock_insert.assert_not_called()
                    mock_update.assert_not_called()


# # =============================================================================================================================================================
# ===========================def get_workspace_itemlist():=====================================
@pytest.mark.parametrize(
    "users_index, method, mock_setup, post_data, expected_items_count",
    [
        (
            0,
            "GET",
            {
                "es_data": {
                    "hits": {
                        "hits": [
                            {
                                "id": "123",
                                "metadata": {
                                    "title": ["Test Title"],
                                    "identifier": [{"value": "10.1000/test.doi"}],
                                    "type": ["Article"],
                                    "creator": {"creatorName": ["Author Name"]},
                                    "publish_date": "2023-01-01",
                                    "_item_metadata": {"file": [], "peer_review": True},
                                },
                            }
                        ]
                    }
                },
                "filter_con": None,
                "status_data": (True, False),  # favoriteSts, readSts
                "access_data": (10, 5),  # accessCnt, downloadCnt
                "item_status": "active",
            },
            None,
            1,
        ),  
        (
            0,
            "GET",
            {
                "es_data": {
                    "hits": {
                        "hits": [
                            {
                                "id": "123",
                                "metadata": {
                                    "title": ["Test Title"],
                                    #  "identifier": [{"value": "10.1000/test.doi"}],
                                    "conference": {
                                        "conferenceDate": [],
                                        "conferenceName": ["test4会議名"],
                                        "conferenceVenue": [],
                                        "conferenceCountry": [],
                                        "conferenceSponsor": [],
                                        "conferenceSequence": [],
                                    },
                                    "fundingReference": {
                                        "awardNumber": [],
                                        "awardTitle": [
                                            "test4研究課題名01",
                                            "test4研究課題名02",
                                            "test4研究課題名03",
                                        ],
                                        "funderIdentifier": [],
                                        "funderName": [
                                            "test4助成期間名01",
                                            "test4助成期間名02",
                                            "test4助成期間名03",
                                        ],
                                    },
                                    "relation": {
                                        "@attributes": {
                                            "relationType": [
                                                ["isVersionOf"],
                                                ["isPartOf"],
                                                ["isFormatOf"],
                                            ]
                                        },
                                        "relatedIdentifier": [
                                            {"identifierType": "ARK", "value": "AEK"},
                                            {"identifierType": "DOI", "value": "なし"},
                                            {
                                                "identifierType": "URI",
                                                "value": "https://testtest.com",
                                            },
                                        ],
                                        "relatedTitle": [
                                            "test4関連名称１",
                                            "test4関連名称２",
                                            "test4関連名称３",
                                        ],
                                    },
                                    "type": ["Article"],
                                    "creator": {
                                        "creatorName": [
                                            "Author Name",
                                            "contributor@test.org",
                                        ]
                                    },
                                    "publish_date": "2025-02-14",
                                    "_item_metadata": {
                                        "item_30002_file35": {
                                            "attribute_name": "File",
                                            "attribute_type": "file",
                                            "attribute_value_mlt": [
                                                {
                                                    "accessrole": "open_access",
                                                    "date": [
                                                        {
                                                            "dateType": "Available",
                                                            "dateValue": "2025-02-13",
                                                        }
                                                    ],
                                                    "displaytype": "detail",
                                                    "filename": "test4 ファイル名",
                                                    "licensetype": "license_2",
                                                    "version": "test4ファイルのバージョン情報",
                                                },
                                                {
                                                    "accessrole": "open_access",
                                                    "date": [
                                                        {
                                                            "dateType": "Available",
                                                            "dateValue": "2026-02-14",
                                                        }
                                                    ],
                                                    "filename": "NO1.error.txt",
                                                    "filesize": [{"value": "11 KB"}],
                                                    "format": "text/plain",
                                                    "url": {
                                                        "url": "https://weko3.example.org/record/2000004/files/NO1.error.txt"
                                                    },
                                                },
                                                {
                                                    "accessrole": "open_access_no_download",
                                                    "date": [
                                                        {
                                                            "dateType": "Available",
                                                            "dateValue": "2025-02-14",
                                                        }
                                                    ],
                                                    "filename": "test4-file1.txt",
                                                    "filesize": [{"value": "0 B"}],
                                                    "url": {
                                                        "url": "https://weko3.example.org/record/2000004/files/test4-file1.txt"
                                                    },
                                                },
                                                {
                                                    "accessrole": "open_access",
                                                    "date": [
                                                        {
                                                            "dateType": "Available",
                                                            "dateValue": "2025-02-14",
                                                        }
                                                    ],
                                                    "filename": "test4-file1.txt",
                                                    "filesize": [{"value": "15 B"}],
                                                    "format": "text/plain",
                                                    "url": {
                                                        "url": "https://weko3.example.org/record/2000004/files/test4-file1.txt"
                                                    },
                                                },
                                            ],
                                        },
                                        "peer_review": True,
                                    },
                                },
                            }
                        ]
                    }
                },
                "filter_con": None,
                "status_data": (True, False),  # favoriteSts, readSts
                "access_data": (10, 5),  # accessCnt, downloadCnt
                "item_status": "active",
            },
            None,
            1,
        ),  
        (
            0,
            "POST",
            {
                "es_data": {
                    "hits": {
                        "hits": [
                            {
                                "id": "123",
                                "metadata": {
                                    "title": ["Test Title"],
                                    "identifier": [{"value": "10.1000/test.doi"}],
                                    "type": ["Article"],
                                    "creator": {"creatorName": ["Author Name"]},
                                    "publish_date": "2023-01-01",
                                    "_item_metadata": {"file": [], "peer_review": True},
                                },
                            },
                            {
                                "id": "124",
                                "metadata": {
                                    "title": ["Another Title"],
                                    "identifier": [{"value": "10.1000/another.doi"}],
                                    "type": ["Dataset"],
                                    "creator": {"creatorName": ["Another Author"]},
                                    "publish_date": "2023-02-01",
                                    "_item_metadata": {
                                        "file": [],
                                        "peer_review": False,
                                    },
                                },
                            },
                        ]
                    }
                },
                "filter_con": None,
                "status_data": (True, False),
                "access_data": (10, 5),
                "item_status": "active",
            },
            {"favorite": True, "resource_type": ["Article"]},
            1,
        ),  
        (
            0,
            "GET",
            {
                "es_data": {"hits": {"hits": []}},
                "filter_con": None,
                "status_data": (False, False),
                "access_data": (0, 0),
                "item_status": None,
            },
            None,
            0,
        ),  
        (
            0,
            "GET",
            {
                "es_data": None,
                "filter_con": None,
                "status_data": (False, False),
                "access_data": (0, 0),
                "item_status": None,
            },
            None,
            0,
        ), 
    ],
)
def test_get_workspace_itemlist(
    client, users, users_index, method, mock_setup, post_data, expected_items_count
):
    # ログイン処理
    login(client=client, email=users[users_index]["email"])

    # 依存関数のモック設定
    # 注意：get_es_itemlist は weko_workspace.views でインポートされているため、views の名前空間を対象にする
    with patch("weko_workspace.views.get_es_itemlist") as mock_es:
        mock_es.return_value = mock_setup["es_data"]
        # モックが正しく設定されているか確認
        assert mock_es.return_value == mock_setup["es_data"]

        # URLを生成
        url = url_for("weko_workspace.get_workspace_itemlist")
        if method == "GET":
            # print("GET mock_es.return_value : ", mock_es.return_value)
            res = client.get(url)
        else:  # POST
            # print("POST mock_es.return_value : ", mock_es.return_value)
            res = client.post(url, json=post_data)

        # モックが呼び出されたことを確認
        assert mock_es.called, "mock_es was not called, check patch path!"

    with patch("weko_workspace.utils.get_workspace_filterCon") as mock_filter:
        mock_filter.return_value = (
            (mock_setup["filter_con"], True)
            if mock_setup["filter_con"] is not None
            else (None, False)
        )

    with patch("weko_workspace.utils.get_workspace_status_management") as mock_status:
        mock_status.return_value = mock_setup["status_data"]

    with patch("weko_workspace.utils.get_accessCnt_downloadCnt") as mock_access:
        mock_access.return_value = mock_setup["access_data"]

    with patch("weko_workspace.utils.get_item_status") as mock_item_status:
        mock_item_status.return_value = mock_setup["item_status"]

    with patch("weko_workspace.utils.extract_metadata_info") as mock_extract:
        mock_extract.return_value = ([], True)  # ファイルリスト、査読状況

    with patch("weko_workspace.utils.get_userNm_affiliation") as mock_user_info:
        mock_user_info.return_value = ("Test User", "Test Affiliation")

    with patch(
        "weko_records.api.FeedbackMailList.get_feedback_mail_list"
    ) as mock_feedback:
        mock_feedback.return_value = {users[users_index]["email"]: True}

    with patch("weko_workspace.defaultfilters.merge_default_filters") as mock_merge:
        mock_merge.return_value = post_data if post_data else {}

    # render_template は Flask フレームワークのメソッドであり、weko_workspace.views ではない
    with patch("flask.templating.render_template") as mock_render:
        mock_render.return_value = "mocked_html"

        # レスポンスのステータスコードを確認
        assert res.status_code == 200
        # render_template が呼び出されたことを確認
        assert mock_render.called

        # render_template の呼び出し引数を取得
        call_args = mock_render.call_args[1]
        workspaceItemList = call_args["workspaceItemList"]
        defaultconditions = call_args["defaultconditions"]

        # workspaceItemList の数を検証
        assert len(workspaceItemList) == expected_items_count

        # プロジェクトが存在する場合、一部のフィールドを検証
        if expected_items_count > 0:
            item = workspaceItemList[0]
            assert item["recid"] == mock_setup["es_data"]["hits"]["hits"][0]["id"]
            assert (
                item["title"]
                == mock_setup["es_data"]["hits"]["hits"][0]["metadata"]["title"][0]
            )
            assert item["favoriteSts"] == mock_setup["status_data"][0]
            assert item["readSts"] == mock_setup["status_data"][1]
            assert item["accessCnt"] == mock_setup["access_data"][0]
            assert item["downloadCnt"] == mock_setup["access_data"][1]
            assert item["itemStatus"] == mock_setup["item_status"]
            assert (
                item["fbEmailSts"] == True
            )  # ユーザーがフィードバックメールリストに含まれている

        # defaultconditions の検証
        if post_data:
            assert defaultconditions == post_data
