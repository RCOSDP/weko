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

"""Blueprint for weko-workspace."""

import copy
from datetime import datetime,timezone

from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
)
from flask_babelex import gettext as _
from flask_login import current_user, login_required
from weko_records.api import FeedbackMailList
from invenio_db import db
from sqlalchemy.exc import SQLAlchemyError

from .utils import (
    extract_metadata_info,
    get_accessCnt_downloadCnt,
    get_es_itemlist,
    get_item_status,
    get_userNm_affiliation,
    get_workspace_status_management,
    insert_workspace_status,
    update_workspace_status,
    get_workspace_filterCon
)
from .models import WorkspaceDefaultConditions
from .defaultfilters import merge_default_filters

workspace_blueprint = Blueprint(
    "weko_workspace",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/workspace",
)

# 2.1. アイテム一覧情報取得API
@workspace_blueprint.route("/", methods=["GET", "POST"])
@login_required
def get_workspace_itemlist():
    """
    Retrieves the list of items in the workspace and applies filters based on default conditions and user input.

    Returns:
        HTML: Renders the workspace item list page with the relevant metadata and user information.

    Raises:
        Exception: Any unexpected errors during the database or data fetching operations will be handled and returned as a generic response.
    """

    # 変数初期化
    workspaceItemList = []
    funderNameList = []
    awardTitleList = []

    # 1,デフォルト絞込み条件取得処理
    jsonCondition, isnotNone = (request.get_json() if request.method == "POST" else None), True

    if jsonCondition is None:
        # 1,デフォルト絞込み条件取得処理
        jsonCondition, isnotNone = get_workspace_filterCon()

    # 2,ESからアイテム一覧取得処理
    recordsData = get_es_itemlist()

    # 7,ユーザー名と所属情報取得処理
    userNm = get_userNm_affiliation()

    if ( not recordsData or "hits" not in recordsData or "hits" not in recordsData["hits"]):
        return render_template(
            current_app.config["WEKO_WORKSPACE_BASE_TEMPLATE"],
            username=userNm,
            workspaceItemList=[],
            defaultconditions=jsonCondition,
        )
    
    # ログインユーザーのIDとロールを取得
    recordsDataList = recordsData["hits"]["hits"]
    rolelist = []
    for role in current_user.roles:
        rolelist.append(role.id)
    # リポジトリ管理者の場合、全てのアイテムを表示
    if 2 in rolelist:
        pass
    # 登録者の場合、自分のアイテムのみ表示
    elif 3 in rolelist:
        recordsDataList = [hit for hit in recordsDataList if hit["metadata"]["weko_creator_id"] == str(current_user.id)]
    else:
        return render_template(
            current_app.config["WEKO_WORKSPACE_BASE_TEMPLATE"],
            username=userNm,
            workspaceItemList=[],
            defaultconditions=jsonCondition,
        )

    # →ループ処理
    # for hit in recordsData["hits"]["hits"]:
    for hit in recordsDataList:
        workspaceItem = copy.deepcopy(current_app.config["WEKO_WORKSPACE_ITEM"])

        # ファイルリストと査読状況を取得
        itemMetadata = hit["metadata"]["_item_metadata"]
        fileList, peerReviewed = extract_metadata_info(itemMetadata)

        # "recid": None,  # レコードID
        recid = hit["id"]
        workspaceItem["recid"] = str(recid)

        # "title": None,  # タイトル
        workspaceItem["title"] = hit["metadata"].get("title", [])[0]

        # "favoriteSts": None,  # お気に入りステータス状況
        workspaceItem["favoriteSts"] = (
            get_workspace_status_management(recid)[0]
            if get_workspace_status_management(recid)
            else False
        )

        # "readSts": None,  # 既読未読ステータス状況
        workspaceItem["readSts"] = (
            get_workspace_status_management(recid)[1]
            if get_workspace_status_management(recid)
            else False
        )

        # "peerReviewSts": None,  # 査読チェック状況
        workspaceItem["peerReviewSts"] = peerReviewed

        # "doi": None,  # DOIリンク
        identifiers = hit["metadata"].get("identifier", [])
        if identifiers:
            workspaceItem["doi"] = identifiers[0].get("value", "")
        else:
            workspaceItem["doi"] = ""

        # "resourceType": None,  # リソースタイプ
        workspaceItem["resourceType"] = hit["metadata"].get("type", [])[0]

        #  "authorlist": None,   著者リスト[著者名]
        workspaceItem["authorlist"] = (
            hit["metadata"]["creator"]["creatorName"]
            if "creator" in hit["metadata"]
            and hit["metadata"]["creator"]["creatorName"]
            else None
        )

        # "accessCnt": None,  # アクセス数
        workspaceItem["accessCnt"] = get_accessCnt_downloadCnt(recid)[0]

        # "downloadCnt": None,  # ダウンロード数
        workspaceItem["downloadCnt"] = get_accessCnt_downloadCnt(recid)[1]

        # "itemStatus": None,  # アイテムステータス
        workspaceItem["itemStatus"] = get_item_status(str(recid))

        # "publicationDate": None,  # 出版年月日
        workspaceItem["publicationDate"] = hit["metadata"]["publish_date"]

        # "magazineName": None,  # 雑誌名
        workspaceItem["magazineName"] = (
            hit["metadata"]["sourceTitle"][0]
            if "sourceTitle" in hit["metadata"]
            else None
        )

        # "conferenceName": None,  # 会議名
        conference = hit["metadata"].get("conference", [])
        if conference and conference["conferenceName"]:
            workspaceItem["conferenceName"] = conference["conferenceName"][0]
        else:
            workspaceItem["conferenceName"] = None

        # "volume": None,  # 巻
        workspaceItem["volume"] = (
            hit["metadata"].get("volume", [])[0]
            if hit["metadata"].get("volume", [])
            else None
        )

        # "issue": None,  # 号
        workspaceItem["issue"] = (
            hit["metadata"].get("issue", [])[0]
            if hit["metadata"].get("issue", [])
            else None
        )

        # "funderName": None,  # 資金別情報機関名
        fundingReference = hit["metadata"].get("fundingReference", [])
        if fundingReference and fundingReference["funderName"]:
            workspaceItem["funderName"] = fundingReference["funderName"][0]

            # デフォルト条件の設定
            funderNameList.extend(fundingReference["funderName"])
        else:
            workspaceItem["funderName"] = None

        # "awardTitle": None,  # 資金別情報課題名
        if fundingReference and fundingReference["awardTitle"]:
            workspaceItem["awardTitle"] = fundingReference["awardTitle"][0]

            # デフォルト条件の設定
            awardTitleList.extend(fundingReference["awardTitle"])
        else:
            workspaceItem["awardTitle"] = None

        # "fbEmailSts": None,  # フィードバックメールステータス
        workspaceItem["fbEmailSts"] = (
            True
            if current_user.email
            in list(FeedbackMailList.get_feedback_mail_list().keys())
            else False
        )

        if userNm in workspaceItem["authorlist"]:
            workspaceItem["fbEmailSts"] = True

        # "connectionToPaperSts": None,  # 論文への関連チェック状況
        workspaceItem["connectionToPaperSts"] = (
            True
            if workspaceItem["resourceType"]
            in current_app.config["WEKO_WORKSPACE_ARTICLE_TYPES"]
            else None
        )

        # "connectionToDatasetSts": None,  # 根拠データへの関連チェック状況
        workspaceItem["connectionToDatasetSts"] = (
            True
            if workspaceItem["resourceType"]
            in current_app.config["WEKO_WORKSPACE_DATASET_TYPES"]
            else None
        )

        # "relation": None,  # 関連情報リスト
        relations = []
        relationLen = (
            len(hit["metadata"]["relation"]["relatedTitle"])
            if "relation" in hit["metadata"]
            else 0
        )

        if "relation" in hit["metadata"]:
            for i in range(relationLen):
                # "relationType": None,  # 関連情報タイプ
                workspaceItem["relationType"] = hit["metadata"].get("relation", [])[
                    "@attributes"
                ]["relationType"][i][0]

                # # "relationTitle": None,  # 関連情報タイトル
                workspaceItem["relationTitle"] = hit["metadata"].get("relation", [])[
                    "relatedTitle"
                ][i]

                # # "relationUrl": None,  # 関連情報URLやDOI
                workspaceItem["relationUrl"] = hit["metadata"].get("relation", [])["relatedIdentifier"][i]["value"]

                relation = {
                    "relationType": workspaceItem["relationType"],
                    "relationTitle": workspaceItem["relationTitle"],
                    "relationUrl": workspaceItem["relationUrl"],
                }
                relations.append(relation)

        workspaceItem["relation"] = relations

        # file情報
        publicCnt = 0
        embargoedCnt = 0
        restrictedPublicationCnt = 0

        if fileList is not None and len(fileList) > 0:
            # "fileSts": None,  # 本文ファイル有無ステータス
            workspaceItem["fileSts"] = True

            # "fileCnt": None,  # 本文ファイル数
            workspaceItem["fileCnt"] = len(fileList)

            accessrole_date_list = [
                {
                    "accessrole": item["accessrole"],
                    "dateValue": item["date"][0]["dateValue"],
                }
                for item in fileList
                if "accessrole" in item and "date" in item
            ]

            for accessrole_date in accessrole_date_list:

                # "publicSts": None,  # 公開ファイル有無ステータス
                # "publicCnt": None,  # 公開ファイル数
                if accessrole_date["dateValue"] <= hit["metadata"]["publish_date"]:
                    publicCnt += 1

                # "embargoedSts": None,  # エンバーゴ有無ステータス
                # "embargoedCnt": None,  # エンバーゴ有数
                if accessrole_date["dateValue"] > datetime.now().strftime("%Y%m%d"):
                    embargoedCnt += 1

                # "restrictedPublicationSts": None,  # 制限公開有無ステータス
                # "restrictedPublicationCnt": None,  # 制限公開ファイル数
                if accessrole_date["accessrole"] == "open_access":
                    restrictedPublicationCnt += 1
        else:
            workspaceItem["fileSts"] = False
            workspaceItem["fileCnt"] = 0

        workspaceItem["publicCnt"] = publicCnt if "publicCnt" in locals() else 0
        workspaceItem["embargoedCnt"] = (
            embargoedCnt if "embargoedCnt" in locals() else 0
        )
        workspaceItem["restrictedPublicationCnt"] = (
            restrictedPublicationCnt if "restrictedPublicationCnt" in locals() else 0
        )

        workspaceItemList.append(workspaceItem)

    # デフォルト絞込み条件より、workspaceItemListを洗い出す
    if isnotNone:
        defaultconditions = merge_default_filters(jsonCondition)

        # フィルタリングマッピング
        filter_mapping = {
            'favorite': 'favoriteSts',
            'peer_review': 'peerReviewSts',
            'file_present': 'fileSts',
            'resource_type': 'resourceType',
            'related_to_data': 'connectionToDatasetSts',
            'related_to_paper': 'connectionToPaperSts'
        }

        # フィルタリング処理
        filteredItems = [
            item for item in workspaceItemList
            if all(
                item.get(filter_mapping[key]) == jsonCondition[key]
                if key != 'resource_type'
                else item.get(filter_mapping[key]) in jsonCondition[key]
                for key in filter_mapping
                if key in jsonCondition and
                key not in ['award_title', 'funder_name'] and
                jsonCondition.get(key) is not None and
                jsonCondition.get(key) != []
            )
        ]
        workspaceItemList = filteredItems

    else:
        defaultconditions = jsonCondition

    defaultconditions["funder_name"]["options"] = list(dict.fromkeys(funderNameList))
    defaultconditions["award_title"]["options"] = list(dict.fromkeys(awardTitleList))

    return render_template(
        current_app.config["WEKO_WORKSPACE_BASE_TEMPLATE"],
        username=userNm,
        workspaceItemList=workspaceItemList,
        defaultconditions=defaultconditions,
    )


@workspace_blueprint.route("/updateStatus", methods=["POST"])
@login_required
def update_workspace_status_management():
    """
    Updates the status of a workspace item (e.g., favorite or read status) based on user input.

    Args:
        None (request data is retrieved directly from the request body)

    Returns:
        JSON: A JSON response with the result of the update operation:
            - success (bool): True if the update was successful, False otherwise.
            - message (str): Describes the result of the update operation.

    Raises:
        HTTPError (400): If an invalid type is provided in the request data.
    """
    data = request.get_json()

    user_id = current_user.id

    item_recid = data.get("itemRecid")

    type = data.get("type")

    result = get_workspace_status_management(item_recid)

    if not result:
        insert_workspace_status(
            user_id=user_id,
            recid=item_recid,
            is_favorited=data.get("favoriteSts", False) if type == "1" else False,
            is_read=data.get("readSts", False) if type == "2" else False,
        )
    else:
        #　お気に入りステータス更新の場合
        if type == "1":
            update_workspace_status(
                user_id=user_id, recid=item_recid, is_favorited=data.get("favoriteSts")
            )
        # 既読未読ステータス更新の場合
        elif type == "2":
            update_workspace_status(
                user_id=user_id, recid=item_recid, is_read=data.get("readSts")
            )
        else:
            return jsonify({"success": False, "message": "Invalid type"}), 400

    return jsonify({"success": True}), 200


@workspace_blueprint.route("/save_filters", methods=["POST"])
@login_required
def save_filters():
    """
    Save the default filter conditions for a user.

    Args:
        None (request data is retrieved directly from the request body)

    Returns:
        JSON: A JSON response indicating the result of the operation:
            - status (str): "success" if the conditions were saved successfully, "error" if an error occurred.
            - message (str): Describes the outcome of the save operation.

    Raises:
        HTTPError (500): If a database error or unexpected error occurs during the operation.
    """
    data = request.get_json()
    user_id = current_user.id

    try:
        record = WorkspaceDefaultConditions.query.filter_by(user_id=user_id).first()
        if record:
            record.default_con = data
            record.updated = datetime.now(timezone.utc)
        else:
            record = WorkspaceDefaultConditions(
                user_id=user_id,
                default_con=data,
                created=datetime.now(timezone.utc),
                updated=datetime.now(timezone.utc),
            )
            db.session.add(record)
        db.session.commit()
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Successfully saved default conditions.",
                }
            ),
            200,
        )

    except SQLAlchemyError as e:
        db.session.rollback()
        error_message = (
            f"Failed to save default conditions due to database error: {str(e)}"
        )
        return jsonify({"status": "error", "message": error_message}), 500
    except Exception as e:
        error_message = f"Unexpected error occurred: {str(e)}"
        return jsonify({"status": "error", "message": error_message}), 500


@workspace_blueprint.route("/reset_filters", methods=["DELETE"])
@login_required
def reset_filters():
    """
    Delete the default filter conditions for the current user.

    Args:
        None (request data is retrieved directly from the current user session)

    Returns:
        JSON: A JSON response indicating the result of the operation:
            - status (str): "success" if the conditions were deleted successfully or if no conditions were found.
            - message (str): Describes the outcome of the reset operation.

    Raises:
        HTTPError (500): If a database error or unexpected error occurs during the operation.

    """

    user_id = current_user.id
    try:
        record = WorkspaceDefaultConditions.query.filter_by(user_id=user_id).first()

        if record:
            db.session.delete(record)
            db.session.commit()
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Successfully reset default conditions.",
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "No default conditions found to reset.",
                    }
                ),
                200,
            )

    except SQLAlchemyError as e:
        db.session.rollback()
        error_message = (
            f"Failed to reset default conditions due to database error: {str(e)}"
        )
        return jsonify({"status": "error", "message": error_message}), 500
    except Exception as e:
        error_message = f"Unexpected error occurred: {str(e)}"
        return jsonify({"status": "error", "message": error_message}), 500
