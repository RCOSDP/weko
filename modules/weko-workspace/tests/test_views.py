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

from unittest.mock import MagicMock
from mock import patch

from flask import json
from flask_babelex import gettext as _

from invenio_accounts.testutils import login_user_via_session as login

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


def response_data(response):
    return json.loads(response.data)

# .tox/c1/bin/pytest --cov=weko_workspace tests/test_views.py::test_itemregister -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-weko_workspace/.tox/c1/tmp
def test_itemregister(db,users, workflow, app, client,mocker,without_remove_session):
    # ワークフローを経由で
    admin_settings = {"workFlow_select_flg": '0', "work_flow_id": '1'}
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        url = url_for("weko_workspace.itemregister")
        res = client.get(url, json=admin_settings)
        assert res is not None

    # item_type is None
    admin_settings = {"workFlow_select_flg": '0', "work_flow_id": '1'}

    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        with patch("weko_records.api.ItemTypes.get_by_id", return_value=None):
            url = url_for("weko_workspace.itemregister")
            res = client.get(url, json=admin_settings)
            assert res.status_code == 404


    # 直接登録
    admin_settings = {"workFlow_select_flg": '1', "item_type_id": '1'}
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        url = url_for("weko_workspace.itemregister")
        res = client.get(url, json=admin_settings)
        assert res is not None
    
        # item_type is None
    admin_settings = {"workFlow_select_flg": '1', "item_type_id": '1'}

    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        with patch("weko_records.api.ItemTypes.get_by_id", return_value=None):
            url = url_for("weko_workspace.itemregister")
            res = client.get(url, json=admin_settings)
            assert res.status_code == 404


# .tox/c1/bin/pytest --cov=weko_workspace tests/test_views.py::test_get_auto_fill_record_data_ciniiapi -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-weko_workspace/.tox/c1/tmp
def test_get_auto_fill_record_data_ciniiapi(db,users, workflow,client_api, client,mocker,without_remove_session):
    # data あり
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from mock import MagicMock, patch, PropertyMock
    from unittest.mock import patch, Mock, MagicMock
    import os
    item_type = Mock()
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data/item_type/15_render.json"
    )
    with open(filepath, encoding="utf-8") as f:
        render = json.load(f)
    item_type.render = render

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data/item_type/15_schema.json"
    )
    with open(filepath, encoding="utf-8") as f:
        schema = json.load(f)
    item_type.schema = schema

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data/item_type/15_form.json"
    )
    with open(filepath, encoding="utf-8") as f:
        form = json.load(f)
    item_type.form = form

    item_type.item_type_name.name="デフォルトアイテムタイプ（フル）"
    item_type.item_type_name.item_type.first().id=15
    data = {
        "search_data":"10.5109/16119",
        "item_type_id":"1"
    }

    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=item_type):
        with patch("weko_workspace.utils.get_cinii_record_data", return_value={"result":"","items":"test","error":""}):
            url = url_for("weko_workspace_api.get_auto_fill_record_data_ciniiapi")
            res = client.post(url, 
                        data=json.dumps(data),
                        content_type='application/json')
            assert res.status_code == 200
            assert res is not None

    # header error
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }

    data = {
        "search_data":"10.5109/16119",
        "item_type_id":"15"
    }

    mocker.patch("weko_workspace.views.session",session)
    url = url_for("weko_workspace_api.get_auto_fill_record_data_ciniiapi")
    res = client.post(url, 
                data=json.dumps(data),
                content_type='test/json')
    assert res.status_code == 200


    # not exist
    data = {
        "search_data":"test",
        "item_type_id":"15"
    }

    mocker.patch("weko_workspace.views.session",session)
    url = url_for("weko_workspace_api.get_auto_fill_record_data_ciniiapi")
    res = client.post(url, 
                data=json.dumps(data),
                content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data) == {"result":[],"items":"","error":""}


# .tox/c1/bin/pytest --cov=weko_workspace tests/test_views.py::test_get_auto_fill_record_data_jalcapi -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-weko_workspace/.tox/c1/tmp
def test_get_auto_fill_record_data_jalcapi(db,users, workflow,client_api, client,mocker,without_remove_session):
    # data あり
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from unittest.mock import patch, Mock, MagicMock
    import os
    item_type = Mock()
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data/item_type/15_render.json"
    )
    with open(filepath, encoding="utf-8") as f:
        render = json.load(f)
    item_type.render = render

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data/item_type/15_schema.json"
    )
    with open(filepath, encoding="utf-8") as f:
        schema = json.load(f)
    item_type.schema = schema

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data/item_type/15_form.json"
    )
    with open(filepath, encoding="utf-8") as f:
        form = json.load(f)
    item_type.form = form

    item_type.item_type_name.name="デフォルトアイテムタイプ（フル）"
    item_type.item_type_name.item_type.first().id=15
    data = {
        "search_data":"10.5109/16119",
        "item_type_id":"1"
    }

    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=item_type):
        with patch("weko_workspace.utils.get_jalc_record_data", return_value={"result":"","items":"test","error":""}):
            url = url_for("weko_workspace_api.get_auto_fill_record_data_jalcapi")
            res = client.post(url, 
                        data=json.dumps(data),
                        content_type='application/json')
            assert res.status_code == 200
            assert res is not None

    # header error
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }

    data = {
        "search_data":"10.5109/16119",
        "item_type_id":"15"
    }

    mocker.patch("weko_workspace.views.session",session)
    url = url_for("weko_workspace_api.get_auto_fill_record_data_jalcapi")
    res = client.post(url, 
                data=json.dumps(data),
                content_type='test/json')
    assert res.status_code == 200


    # not exist
    data = {
        "search_data":"test",
        "item_type_id":"15"
    }

    mocker.patch("weko_workspace.views.session",session)
    url = url_for("weko_workspace_api.get_auto_fill_record_data_jalcapi")
    res = client.post(url, 
                data=json.dumps(data),
                content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data) == {"result":[],"items":"","error":""}


# .tox/c1/bin/pytest --cov=weko_workspace tests/test_views.py::test_get_auto_fill_record_data_dataciteapi -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-weko_workspace/.tox/c1/tmp
def test_get_auto_fill_record_data_dataciteapi(db,users, workflow,client_api, client,mocker,without_remove_session):
    # data あり
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from mock import MagicMock, patch, PropertyMock
    from unittest.mock import patch, Mock, MagicMock
    import os
    item_type = Mock()
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data/item_type/15_render.json"
    )
    with open(filepath, encoding="utf-8") as f:
        render = json.load(f)
    item_type.render = render

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data/item_type/15_schema.json"
    )
    with open(filepath, encoding="utf-8") as f:
        schema = json.load(f)
    item_type.schema = schema

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data/item_type/15_form.json"
    )
    with open(filepath, encoding="utf-8") as f:
        form = json.load(f)
    item_type.form = form

    item_type.item_type_name.name="デフォルトアイテムタイプ（フル）"
    item_type.item_type_name.item_type.first().id=15
    data = {
        "search_data":"10.14454/FXWS-0523",
        "item_type_id":"1"
    }

    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=item_type):
        with patch("weko_workspace.utils.get_datacite_record_data", return_value={"result":"","items":"test","error":""}):
            url = url_for("weko_workspace_api.get_auto_fill_record_data_dataciteapi")
            res = client.post(url, 
                        data=json.dumps(data),
                        content_type='application/json')
            assert res.status_code == 200
            assert res is not None

    # header error
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }

    data = {
        "search_data":"10.5109/16119",
        "item_type_id":"15"
    }

    mocker.patch("weko_workspace.views.session",session)
    url = url_for("weko_workspace_api.get_auto_fill_record_data_dataciteapi")
    res = client.post(url, 
                data=json.dumps(data),
                content_type='test/json')
    assert res.status_code == 200


    # not exist
    data = {
        "search_data":"test",
        "item_type_id":"15"
    }

    mocker.patch("weko_workspace.views.session",session)
    url = url_for("weko_workspace_api.get_auto_fill_record_data_dataciteapi")
    res = client.post(url, 
                data=json.dumps(data),
                content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data) == {"result":[],"items":"","error":""}


# .tox/c1/bin/pytest --cov=weko_workspace tests/test_views.py::test_itemregister_save -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-weko_workspace/.tox/c1/tmp
def test_itemregister_save(db,users,location, workflow, app, client,mocker,without_remove_session):
    # ワークフローを経由で
    admin_settings = {"workFlow_select_flg": '0', "work_flow_id": '1'}
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }

    index_metadata = {
        "id": 2,
        "parent": 1,
        "position": 1,
        "index_name": "test-weko",
        "index_name_english": "Contents Type",
        "index_link_name": "",
        "index_link_name_english": "New Index",
        "index_link_enabled": False,
        "more_check": False,
        "display_no": 5,
        "harvest_public_state": True,
        "display_format": 1,
        "image_name": "",
        "public_state": True,
        "recursive_public_state": True,
        "rss_status": False,
        "coverpage_state": False,
        "recursive_coverpage_check": False,
        "browsing_role": "3,-98,-99",
        "recursive_browsing_role": False,
        "contribute_role": "1,2,3,4,-98,-99",
        "recursive_contribute_role": False,
        "browsing_group": "",
        "recursive_browsing_group": False,
        "recursive_contribute_group": False,
        "owner_user_id": 1,
        "item_custom_sort": {"2": 1}
    }
    from weko_index_tree.models import Index
    index = Index(**index_metadata)

    with db.session.begin_nested():
        db.session.add(index)

    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    data = {
        "recordModel":{'pubdate': '2025-03-11', 'item_30002_title0': [{'subitem_title': 'Identification of cDNA Sequences Encoding the Complement Components of Zebrafish (Danio rerio)', 'subitem_title_language': 'en'}], 'item_30002_creator2': [{'creatorNames': [{'creatorName': 'Vo Kha Tam', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Tsujikura Masakazu', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Somamoto Tomonori', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Nakano Miki', 'creatorNameLang': 'en'}]}], 'item_30002_identifier16': [{'subitem_identifier_uri': '10.5109/16119'}], 'item_30002_relation18': [{'subitem_relation_type_id': {'subitem_relation_type_id_text': '10.5109/16119', 'subitem_relation_type_select': 'DOI'}}], 'item_30002_funding_reference21': [{'subitem_funder_names': [{'subitem_funder_name': 'test1'}]}], 'item_30002_conference34': [{'subitem_conference_names': [{'subitem_conference_name': 'test3'}]}], 'item_30002_file35': [{'version_id': '9e7f93b3-7290-4a6f-aea0-87856279cf48', 'filename': '1_1.png', 'filesize': [{'value': '55 KB'}], 'format': 'image/png', 'date': [{'dateValue': '2025-03-11', 'dateType': 'Available'}], 'accessrole': 'open_access', 'url': {'url': 'https://192.168.56.106/record/2000235/files/1_1.png'}}], 'item_30002_bibliographic_information29': {'bibliographic_titles': [{'bibliographic_title': 'test2'}]}, 'item_30002_source_title23': [{'subitem_source_title': 'Journal of the Faculty of Agriculture, Kyushu University', 'subitem_source_title_language': 'en'}], 'item_30002_source_identifier22': [{'subitem_source_identifier': '0023-6152', 'subitem_source_identifier_type': 'ISSN'}], 'item_30002_volume_number24': {'subitem_volume': '54'}, 'item_30002_issue_number25': {'subitem_issue': '2'}, 'item_30002_page_start27': {'subitem_start_page': '373'}, 'item_30002_page_end28': {'subitem_end_page': '387'}, 'item_30002_date11': [{'subitem_date_issued_datetime': '2009', 'subitem_date_issued_type': 'Issued'}], 'item_30002_access_rights4': {'subitem_access_right': 'embargoed access'}, 'item_30002_resource_type13': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_30002_version_type15': {'subitem_version_type': 'AO'}, 'deleted_items': []},
        "indexlist":['test-weko']
    }
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        url = url_for("weko_workspace.workflow_registration")
        res = client.post(url, json=data)
        assert res is not None

    # header error
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }

    data = {
        "recordModel":{'pubdate': '2025-03-11', 'item_30002_title0': [{'subitem_title': 'Identification of cDNA Sequences Encoding the Complement Components of Zebrafish (Danio rerio)', 'subitem_title_language': 'en'}], 'item_30002_creator2': [{'creatorNames': [{'creatorName': 'Vo Kha Tam', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Tsujikura Masakazu', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Somamoto Tomonori', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Nakano Miki', 'creatorNameLang': 'en'}]}], 'item_30002_identifier16': [{'subitem_identifier_uri': '10.5109/16119'}], 'item_30002_relation18': [{'subitem_relation_type_id': {'subitem_relation_type_id_text': '10.5109/16119', 'subitem_relation_type_select': 'DOI'}}], 'item_30002_funding_reference21': [{'subitem_funder_names': [{'subitem_funder_name': 'test1'}]}], 'item_30002_conference34': [{'subitem_conference_names': [{'subitem_conference_name': 'test3'}]}], 'item_30002_file35': [{'version_id': '9e7f93b3-7290-4a6f-aea0-87856279cf48', 'filename': '1_1.png', 'filesize': [{'value': '55 KB'}], 'format': 'image/png', 'date': [{'dateValue': '2025-03-11', 'dateType': 'Available'}], 'accessrole': 'open_access', 'url': {'url': 'https://192.168.56.106/record/2000235/files/1_1.png'}}], 'item_30002_bibliographic_information29': {'bibliographic_titles': [{'bibliographic_title': 'test2'}]}, 'item_30002_source_title23': [{'subitem_source_title': 'Journal of the Faculty of Agriculture, Kyushu University', 'subitem_source_title_language': 'en'}], 'item_30002_source_identifier22': [{'subitem_source_identifier': '0023-6152', 'subitem_source_identifier_type': 'ISSN'}], 'item_30002_volume_number24': {'subitem_volume': '54'}, 'item_30002_issue_number25': {'subitem_issue': '2'}, 'item_30002_page_start27': {'subitem_start_page': '373'}, 'item_30002_page_end28': {'subitem_end_page': '387'}, 'item_30002_date11': [{'subitem_date_issued_datetime': '2009', 'subitem_date_issued_type': 'Issued'}], 'item_30002_access_rights4': {'subitem_access_right': 'embargoed access'}, 'item_30002_resource_type13': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_30002_version_type15': {'subitem_version_type': 'AO'}, 'deleted_items': []}
    }

    mocker.patch("weko_workspace.views.session",session)
    url = url_for("weko_workspace.workflow_registration")
    res = client.post(url, 
                data=json.dumps(data),
                content_type='test/json')
    assert res.status_code == 200

    # error
    admin_settings = {"workFlow_select_flg": '0', "work_flow_id": '1'}
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    data = {
        "recordModel":{}
    }
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        url = url_for("weko_workspace.workflow_registration")
        res = client.post(url, json=data)
        assert res is not None


    # data is None
    admin_settings = {"workFlow_select_flg": '0', "work_flow_id": '1'}

    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    data = {
        "recordModel":{'pubdate': '2025-03-11', 'item_30002_title0': [{'subitem_title': 'Identification of cDNA Sequences Encoding the Complement Components of Zebrafish (Danio rerio)', 'subitem_title_language': 'en'}], 'item_30002_creator2': [{'creatorNames': [{'creatorName': 'Vo Kha Tam', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Tsujikura Masakazu', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Somamoto Tomonori', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Nakano Miki', 'creatorNameLang': 'en'}]}], 'item_30002_identifier16': [{'subitem_identifier_uri': '10.5109/16119'}], 'item_30002_relation18': [{'subitem_relation_type_id': {'subitem_relation_type_id_text': '10.5109/16119', 'subitem_relation_type_select': 'DOI'}}], 'item_30002_funding_reference21': [{'subitem_funder_names': [{'subitem_funder_name': 'test1'}]}], 'item_30002_conference34': [{'subitem_conference_names': [{'subitem_conference_name': 'test3'}]}], 'item_30002_file35': [{'version_id': '9e7f93b3-7290-4a6f-aea0-87856279cf48', 'filename': '1_1.png', 'filesize': [{'value': '55 KB'}], 'format': 'image/png', 'date': [{'dateValue': '2025-03-11', 'dateType': 'Available'}], 'accessrole': 'open_access', 'url': {'url': 'https://192.168.56.106/record/2000235/files/1_1.png'}}], 'item_30002_bibliographic_information29': {'bibliographic_titles': [{'bibliographic_title': 'test2'}]}, 'item_30002_source_title23': [{'subitem_source_title': 'Journal of the Faculty of Agriculture, Kyushu University', 'subitem_source_title_language': 'en'}], 'item_30002_source_identifier22': [{'subitem_source_identifier': '0023-6152', 'subitem_source_identifier_type': 'ISSN'}], 'item_30002_volume_number24': {'subitem_volume': '54'}, 'item_30002_issue_number25': {'subitem_issue': '2'}, 'item_30002_page_start27': {'subitem_start_page': '373'}, 'item_30002_page_end28': {'subitem_end_page': '387'}, 'item_30002_date11': [{'subitem_date_issued_datetime': '2009', 'subitem_date_issued_type': 'Issued'}], 'item_30002_access_rights4': {'subitem_access_right': 'embargoed access'}, 'item_30002_resource_type13': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_30002_version_type15': {'subitem_version_type': 'AO'}, 'deleted_items': []}
    }
    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        with patch("weko_workflow.headless.activity.HeadlessActivity.auto", return_value=None):
            url = url_for("weko_workspace.workflow_registration")
            res = client.post(url, json=data)
            assert res.status_code == 200


    # 直接登録
    admin_settings = {"workFlow_select_flg": '1', "item_type_id": '1'}
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }

    index_metadata = {
        "id": 3,
        "parent": 1,
        "position": 2,
        "index_name": "test-weko",
        "index_name_english": "Contents Type",
        "index_link_name": "",
        "index_link_name_english": "New Index",
        "index_link_enabled": False,
        "more_check": False,
        "display_no": 5,
        "harvest_public_state": True,
        "display_format": 1,
        "image_name": "",
        "public_state": True,
        "recursive_public_state": True,
        "rss_status": False,
        "coverpage_state": False,
        "recursive_coverpage_check": False,
        "browsing_role": "3,-98,-99",
        "recursive_browsing_role": False,
        "contribute_role": "1,2,3,4,-98,-99",
        "recursive_contribute_role": False,
        "browsing_group": "",
        "recursive_browsing_group": False,
        "recursive_contribute_group": False,
        "owner_user_id": 1,
        "item_custom_sort": {"2": 1}
    }

    return_value = {
            "error_id":None,
        }
    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    data = {
        "recordModel":{'pubdate': '2025-03-11', 'item_30002_title0': [{'subitem_title': 'Identification of cDNA Sequences Encoding the Complement Components of Zebrafish (Danio rerio)', 'subitem_title_language': 'en'}], 'item_30002_creator2': [{'creatorNames': [{'creatorName': 'Vo Kha Tam', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Tsujikura Masakazu', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Somamoto Tomonori', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Nakano Miki', 'creatorNameLang': 'en'}]}], 'item_30002_relation18': [{'subitem_relation_type_id': {'subitem_relation_type_id_text': '10.5109/16119', 'subitem_relation_type_select': 'DOI'}}], 'item_30002_file35': [{'date': [{'dateValue': '2025-03-11'}], 'url': {'url': 'https://192.168.56.106/record/2000235/files/1_1.png'}}], 'item_30002_source_title23': [{'subitem_source_title': 'Journal of the Faculty of Agriculture, Kyushu University', 'subitem_source_title_language': 'en'}], 'item_30002_source_identifier22': [{'subitem_source_identifier': '0023-6152', 'subitem_source_identifier_type': 'ISSN'}], 'item_30002_volume_number24': {'subitem_volume': '54'}, 'item_30002_issue_number25': {'subitem_issue': '2'}, 'item_30002_page_start27': {'subitem_start_page': '373'}, 'item_30002_page_end28': {'subitem_end_page': '387'}, 'item_30002_date11': [{'subitem_date_issued_datetime': '2009', 'subitem_date_issued_type': 'Issued'}], 'item_30002_resource_type13': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'deleted_items': ['item_30002_identifier16', 'item_30002_funding_reference21', 'item_30002_conference34', 'item_30002_bibliographic_information29'], 'path': ['1623632832836']},
        "indexlist":['Sample Index']
    }
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        submeta2 = {'success': True}
        with patch("weko_search_ui.utils.import_items_to_system",side_effect=submeta2): 
            with patch("weko_search_ui.utils.register_item_metadata"):
                with patch("weko_search_ui.utils.register_item_doi"):
                    with patch("weko_search_ui.utils.register_item_update_publish_status"):
                
                        url = url_for("weko_workspace.workflow_registration")
                        res = client.post(url, json=data)
                        assert res is not None


    admin_settings = {"workFlow_select_flg": '1', "item_type_id": '1'}
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }

    index_metadata = {
        "id": 3,
        "parent": 1,
        "position": 2,
        "index_name": "test-weko",
        "index_name_english": "Contents Type",
        "index_link_name": "",
        "index_link_name_english": "New Index",
        "index_link_enabled": False,
        "more_check": False,
        "display_no": 5,
        "harvest_public_state": True,
        "display_format": 1,
        "image_name": "",
        "public_state": True,
        "recursive_public_state": True,
        "rss_status": False,
        "coverpage_state": False,
        "recursive_coverpage_check": False,
        "browsing_role": "3,-98,-99",
        "recursive_browsing_role": False,
        "contribute_role": "1,2,3,4,-98,-99",
        "recursive_contribute_role": False,
        "browsing_group": "",
        "recursive_browsing_group": False,
        "recursive_contribute_group": False,
        "owner_user_id": 1,
        "item_custom_sort": {"2": 1}
    }

    return_value = {
            "error_id":None,
        }
    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    data = {
        "recordModel":{'pubdate': '2025-03-11', 'item_30002_title0': [{'subitem_title': 'Identification of cDNA Sequences Encoding the Complement Components of Zebrafish (Danio rerio)', 'subitem_title_language': 'en'}], 'item_30002_creator2': [{'creatorNames': [{'creatorName': 'Vo Kha Tam', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Tsujikura Masakazu', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Somamoto Tomonori', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Nakano Miki', 'creatorNameLang': 'en'}]}], 'item_30002_relation18': [{'subitem_relation_type_id': {'subitem_relation_type_id_text': '10.5109/16119', 'subitem_relation_type_select': 'DOI'}}], 'item_30002_file35': [{'date': [{'dateValue': '2025-03-11'}], 'url': {'url': 'https://192.168.56.106/record/2000235/files/1_1.png'}}], 'item_30002_source_title23': [{'subitem_source_title': 'Journal of the Faculty of Agriculture, Kyushu University', 'subitem_source_title_language': 'en'}], 'item_30002_source_identifier22': [{'subitem_source_identifier': '0023-6152', 'subitem_source_identifier_type': 'ISSN'}], 'item_30002_volume_number24': {'subitem_volume': '54'}, 'item_30002_issue_number25': {'subitem_issue': '2'}, 'item_30002_page_start27': {'subitem_start_page': '373'}, 'item_30002_page_end28': {'subitem_end_page': '387'}, 'item_30002_date11': [{'subitem_date_issued_datetime': '2009', 'subitem_date_issued_type': 'Issued'}], 'item_30002_resource_type13': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'deleted_items': ['item_30002_identifier16', 'item_30002_funding_reference21', 'item_30002_conference34', 'item_30002_bibliographic_information29'], 'path': ['1623632832836']},

        "indexlist":['Sample Index']
    }

    submeta2 = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
   
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        from elasticsearch import ElasticsearchException

        with patch("weko_search_ui.utils.import_items_to_system", return_value={"success": False, "recid": 1}):
            with patch("weko_search_ui.utils.register_item_metadata"):
                with patch("weko_search_ui.utils.register_item_doi",MagicMock(side_effect=ElasticsearchException())):
                    with patch("weko_search_ui.utils.register_item_update_publish_status",side_effect=submeta2):
                        with patch("weko_search_ui.utils.register_item_doi"):
                            with patch("weko_search_ui.utils.register_item_doi"):
                                    url = url_for("weko_workspace.workflow_registration")
                                    res = client.post(url, json=data)
                                    assert res is not None

    # error
    admin_settings = {"workFlow_select_flg": '1', "item_type_id": '1'}
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    data = {
        "recordModel":{}
    }
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        url = url_for("weko_workspace.workflow_registration")
        res = client.post(url, json=data)
        assert res is not None


    # data is None
    admin_settings = {"workFlow_select_flg": '1', "item_type_id": '30002'}

    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    data = {
        "recordModel":{'pubdate': '2025-03-11', 'item_30002_title0': [{'subitem_title': 'Identification of cDNA Sequences Encoding the Complement Components of Zebrafish (Danio rerio)', 'subitem_title_language': 'en'}], 'item_30002_creator2': [{'creatorNames': [{'creatorName': 'Vo Kha Tam', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Tsujikura Masakazu', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Somamoto Tomonori', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Nakano Miki', 'creatorNameLang': 'en'}]}], 'item_30002_identifier16': [{'subitem_identifier_uri': '10.5109/16119'}], 'item_30002_relation18': [{'subitem_relation_type_id': {'subitem_relation_type_id_text': '10.5109/16119', 'subitem_relation_type_select': 'DOI'}}], 'item_30002_funding_reference21': [{'subitem_funder_names': [{'subitem_funder_name': 'test1'}]}], 'item_30002_conference34': [{'subitem_conference_names': [{'subitem_conference_name': 'test3'}]}], 'item_30002_file35': [{'version_id': '9e7f93b3-7290-4a6f-aea0-87856279cf48', 'filename': '1_1.png', 'filesize': [{'value': '55 KB'}], 'format': 'image/png', 'date': [{'dateValue': '2025-03-11', 'dateType': 'Available'}], 'accessrole': 'open_access', 'url': {'url': 'https://192.168.56.106/record/2000235/files/1_1.png'}}], 'item_30002_bibliographic_information29': {'bibliographic_titles': [{'bibliographic_title': 'test2'}]}, 'item_30002_source_title23': [{'subitem_source_title': 'Journal of the Faculty of Agriculture, Kyushu University', 'subitem_source_title_language': 'en'}], 'item_30002_source_identifier22': [{'subitem_source_identifier': '0023-6152', 'subitem_source_identifier_type': 'ISSN'}], 'item_30002_volume_number24': {'subitem_volume': '54'}, 'item_30002_issue_number25': {'subitem_issue': '2'}, 'item_30002_page_start27': {'subitem_start_page': '373'}, 'item_30002_page_end28': {'subitem_end_page': '387'}, 'item_30002_date11': [{'subitem_date_issued_datetime': '2009', 'subitem_date_issued_type': 'Issued'}], 'item_30002_access_rights4': {'subitem_access_right': 'embargoed access'}, 'item_30002_resource_type13': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_30002_version_type15': {'subitem_version_type': 'AO'}, 'deleted_items': []}
    }
    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        with patch("weko_search_ui.utils.import_items_to_system", side_effect=Exception):
            with patch("weko_search_ui.utils.register_item_metadata", side_effect=Exception):
                url = url_for("weko_workspace.workflow_registration")
                res = client.post(url, json=data)
                assert res.status_code == 200
