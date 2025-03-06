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

from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
)
from flask_babelex import gettext as _
from flask_login import current_user, login_required

from .utils import *
from .models import *
from .defaultfilters import merge_default_filters

workspace_blueprint = Blueprint(
    "weko_workspace",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/workspace",
)


# 2.1. アイテム一覧情報取得API
@workspace_blueprint.route("/get_workspace_itemlist", methods=["GET", "POST"])
@login_required
def get_workspace_itemlist():

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
    records_data = get_es_itemlist()
    # →ループ処理
    for hit in records_data["hits"]["hits"]:
        workspaceItem = copy.deepcopy(current_app.config["WEKO_WORKSPACE_ITEM"])

        # "recid": None,  # レコードID
        recid = hit["id"]
        workspaceItem["recid"] = str(recid)
        # print(f"recid : {recid}")

        # "title": None,  # タイトル
        workspaceItem["title"] = hit["metadata"].get("title", [])[0]
        # print("title : " + workspaceItem["title"])

        # "favoriteSts": None,  # お気に入りステータス状況
        workspaceItem["favoriteSts"] = (
            get_workspace_status_management(recid)[0]
            if get_workspace_status_management(recid)
            else False
        )
        # print("favoriteSts : " + str(workspaceItem["favoriteSts"]))

        # "readSts": None,  # 既読未読ステータス状況
        workspaceItem["readSts"] = (
            get_workspace_status_management(recid)[1]
            if get_workspace_status_management(recid)
            else False
        )
        # print("readSts : " + str(workspaceItem["readSts"]))

        # TODO "peerReviewSts": None,  # 査読チェック状況
        workspaceItem["peerReviewSts"] = True

        # "doi": None,  # DOIリンク
        identifiers = hit["metadata"].get("identifier", [])
        if identifiers:
            workspaceItem["doi"] = identifiers[0].get("value", "")
        else:
            workspaceItem["doi"] = ""
        # print(f"workspaceItem[doi] : {workspaceItem['doi']}")

        # "resourceType": None,  # リソースタイプ
        workspaceItem["resourceType"] = hit["metadata"].get("type", [])[0]
        # print(f"resourceType : {hit['metadata'].get('type', [])[0]}")

        #  "authorlist": None,   著者リスト[著者名]
        workspaceItem["authorlist"] = (
            hit["metadata"]["creator"]["creatorName"]
            if "creator" in hit["metadata"]
            and hit["metadata"]["creator"]["creatorName"]
            else None
        )
        if workspaceItem["authorlist"] is not None:
            workspaceItem["authorlist"].append("作成者02")
            workspaceItem["authorlist"].append("作成者03")
        # print("authorlist : " + str(workspaceItem["authorlist"]))

        # "accessCnt": None,  # アクセス数
        workspaceItem["accessCnt"] = get_accessCnt_downloadCnt(recid)[0]
        # print("accessCnt : " + str(workspaceItem["accessCnt"]))

        # "downloadCnt": None,  # ダウンロード数
        workspaceItem["downloadCnt"] = get_accessCnt_downloadCnt(recid)[1]
        # print("downloadCnt : " + str(workspaceItem["downloadCnt"]))

        # "itemStatus": None,  # アイテムステータス
        workspaceItem["itemStatus"] = get_item_status(recid)
        # print("itemStatus : " + str(workspaceItem["itemStatus"]))

        # "publicationDate": None,  # 出版年月日
        workspaceItem["publicationDate"] = hit["metadata"]["publish_date"]
        # print(f"publicationDate : " + workspaceItem["publicationDate"])

        # "magazineName": None,  # 雑誌名
        workspaceItem["magazineName"] = (
            hit["metadata"]["sourceTitle"][0]
            if "sourceTitle" in hit["metadata"]
            else None
        )
        # print("magazineName : "  + str(workspaceItem["magazineName"]))

        # "conferenceName": None,  # 会議名
        conference = hit["metadata"].get("conference", [])
        if conference and conference["conferenceName"]:
            workspaceItem["conferenceName"] = conference["conferenceName"][0]
        else:
            workspaceItem["conferenceName"] = None

        # print("conferenceName : " + str(workspaceItem["conferenceName"]))

        # "volume": None,  # 巻
        workspaceItem["volume"] = (
            hit["metadata"].get("volume", [])[0]
            if hit["metadata"].get("volume", [])
            else None
        )
        # print("volume : " + str(workspaceItem["volume"]))

        # "issue": None,  # 号
        workspaceItem["issue"] = (
            hit["metadata"].get("issue", [])[0]
            if hit["metadata"].get("issue", [])
            else None
        )
        # print("issue : " + str(workspaceItem["issue"]))

        # "funderName": None,  # 資金別情報機関名
        fundingReference = hit["metadata"].get("fundingReference", [])
        if fundingReference and fundingReference["funderName"]:
            workspaceItem["funderName"] = fundingReference["funderName"][0]

            # デフォルト条件の設定
            funderNameList.extend(fundingReference["funderName"])
        else:
            workspaceItem["funderName"] = None

        # print("funderName : " + str(workspaceItem["funderName"]))

        # "awardTitle": None,  # 資金別情報課題名
        if fundingReference and fundingReference["awardTitle"]:
            workspaceItem["awardTitle"] = fundingReference["awardTitle"][0]

            # デフォルト条件の設定
            awardTitleList.extend(fundingReference["awardTitle"])
        else:
            workspaceItem["awardTitle"] = None

        # print("awardTitle : " + str(workspaceItem["awardTitle"]))

        # TODO "fbEmailSts": None,  # フィードバックメールステータス
        # ①ログインユーザーのメールアドレスは2.1.2.2の
        # 取得結果の著者リストに存在すればtrueを設定する。逆にfalse。
        # ②2.1.2.2の取得結果のアイテムID(_id)でfeedback_mail_listテーブルのmail_list項目を取得して、
        # ログインユーザーのメールアドレスは該当リストに存在すればtrueを設定する。逆にfalse。
        workspaceItem["fbEmailSts"] = False if current_user.email else False
        # print("fbEmailSts : " + str(workspaceItem["fbEmailSts"]))

        # "connectionToPaperSts": None,  # 論文への関連チェック状況
        workspaceItem["connectionToPaperSts"] = True if workspaceItem["resourceType"] in current_app.config["WEKO_WORKSPACE_ARTICLE_TYPES"] else None

        # "connectionToDatasetSts": None,  # 根拠データへの関連チェック状況
        workspaceItem["connectionToDatasetSts"] = True if workspaceItem["resourceType"] in current_app.config["WEKO_WORKSPACE_DATASET_TYPES"] else None

        # "relation": None,  # 関連情報リスト
        relations = []
        relationLen = (
            len(hit["metadata"]["relation"]["relatedTitle"])
            if "relation" in hit["metadata"]
            else None
        )
        # print("relationLen : " + str(relationLen))

        if "relation" in hit["metadata"]:
            for i in range(relationLen):
                # "relationType": None,  # 関連情報タイプ
                workspaceItem["relationType"] = hit["metadata"].get("relation", [])[
                    "@attributes"
                ]["relationType"][i][0]
                # print("relationType : " + hit["metadata"].get("relation", [])["@attributes"]["relationType"][i][0])

                # # "relationTitle": None,  # 関連情報タイトル
                workspaceItem["relationTitle"] = hit["metadata"].get("relation", [])[
                    "relatedTitle"
                ][i]
                # print("relationTitle : " + hit["metadata"].get("relation", [])["relatedTitle"][i])

                # # "relationUrl": None,  # 関連情報URLやDOI
                workspaceItem["relationUrl"] = hit["metadata"].get("relation", [])[
                    "relatedIdentifier"
                ][i]["value"]
                # print("relationUrl : "+ hit["metadata"].get("relation", [])["relatedIdentifier"][i]["value"])

                relation = {
                    "relationType": workspaceItem["relationType"],
                    "relationTitle": workspaceItem["relationTitle"],
                    "relationUrl": workspaceItem["relationUrl"],
                }
                relations.append(relation)

        workspaceItem["relation"] = relations
        # print("relation : " + str(workspaceItem["relation"]))

        # file情報
        # print("file : ")
        fileObjNm = (
            "item_" + hit["metadata"]["_item_metadata"]["item_type_id"] + "_file"
        )
        fileObjNm = [
            key
            for key in hit["metadata"]["_item_metadata"].keys()
            if key.startswith(fileObjNm)
        ]

        if fileObjNm is not None and len(fileObjNm) > 0:
            file = fileObjNm[0]

            fileList = []
            fileList = hit["metadata"].get("_item_metadata", [])[file][
                "attribute_value_mlt"
            ]

            publicCnt = 0
            embargoedCnt = 0
            restrictedPublicationCnt = 0

            fileCnt = len(fileList)
            if fileCnt > 0:
                # "fileSts": None,  # 本文ファイル有無ステータス
                workspaceItem["fileSts"] = True
                # print("fileSts : " + str(workspaceItem["fileSts"]))

                # "fileCnt": None,  # 本文ファイル数
                workspaceItem["fileCnt"] = fileCnt
                # print("fileCnt : " + str(workspaceItem["fileCnt"]))

                accessrole_date_list = [
                    {
                        "accessrole": item["accessrole"],
                        "dateValue": item["date"][0]["dateValue"],
                    }
                    for item in fileList
                    if "accessrole" in item and "date" in item
                ]
                # print("accessrole_date_list : ")
                # print(accessrole_date_list)

                for accessrole_date in accessrole_date_list:
                    # print("accessrole : " + accessrole_date["accessrole"])
                    # print("dateValue : " + accessrole_date["dateValue"])

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
        # print("publicCnt : " + str(workspaceItem["publicCnt"]))
        # print("embargoedCnt : " + str(workspaceItem["embargoedCnt"]))
        # print("restrictedPublicationCnt : " + str(workspaceItem["restrictedPublicationCnt"]))
        
        if str(workspaceItem):
            workspaceItemList.append(workspaceItem)
        # print("------------------------------------")

    # 7,ユーザー名と所属情報取得処理
    userInfo = get_userNm_affiliation()
    # print(userInfo[0])
    # print(userInfo[1])
    
    # デフォルト絞込み条件より、workspaceItemListを洗い出す
    if isnotNone:
        defaultconditions = merge_default_filters(jsonCondition)
        print("jsonCondition : " + str(jsonCondition))
        # print("======================db table/post defaultconditions : " + str(defaultconditions))

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
        filtered_items = [
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
        workspaceItemList = filtered_items
        # print("after filter workspaceItemList : " + str(workspaceItemList))

    else:
        defaultconditions = jsonCondition
        # print("====================== default defaultconditions : " + str(defaultconditions))

    defaultconditions["funder_name"]["options"] = list(dict.fromkeys(funderNameList))
    defaultconditions["award_title"]["options"] = list(dict.fromkeys(awardTitleList))

    print("==========guan.shuang workspace end=========")
    return render_template(
        current_app.config["WEKO_WORKSPACE_BASE_TEMPLATE"],
        username=userInfo[0],
        affiliation=userInfo[1],
        workspaceItemList=workspaceItemList,
        defaultconditions=defaultconditions,
    )


@workspace_blueprint.route("/updateStatus", methods=["POST"])
@login_required
def update_workspace_status_management():
    """アイテムのステータスを更新する。

    Returns:
        _type_: _description_
    """
    # print("==========guan.shuang update_workspace_status_management start=========")
    data = request.get_json()

    user_id = current_user.id

    item_recid = data.get("itemRecid")  # 使用 itemRecid
    # print("item_recid : " + str(item_recid))

    type = data.get("type")
    # print("type : " + str(type))

    result = get_workspace_status_management(item_recid)
    # print("result : " + str(result))

    if not result:
        insert_workspace_status(
            user_id=user_id,
            recid=item_recid,
            is_favorited=data.get("favoriteSts", False) if type == "1" else False,
            is_read=data.get("readSts", False) if type == "2" else False,
        )
    else:
        if type == "1":
            update_workspace_status(
                user_id=user_id, recid=item_recid, is_favorited=data.get("favoriteSts")
            )
        elif type == "2":
            update_workspace_status(
                user_id=user_id, recid=item_recid, is_read=data.get("readSts")
            )
        else:
            return jsonify({"success": False, "message": "Invalid type"}), 400

    return jsonify({"success": True})


@workspace_blueprint.route("/save_filters", methods=["POST"])
@login_required
def save_filters():
    """
    デフォルト絞込み条件を保存する。

    Returns:
        JSON: 保存結果に基づいてステータスとメッセージを返します。
    """
    data = request.get_json()
    user_id = current_user.id

    try:
        record = WorkspaceDefaultConditions.query.filter_by(user_id=user_id).first()
        if record:
            record.default_con = data
            record.updated = datetime.utcnow()
        else:
            record = WorkspaceDefaultConditions(
                user_id=user_id,
                default_con=data,
                created=datetime.utcnow(),
                updated=datetime.utcnow(),
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
    現在のユーザーのworkspace_default_conditionsデータを削除します。

    Returns:
        JSON: 削除結果に基づいてステータスとメッセージを返します。
    """

    # print("Resetting filters================リセット============================:")

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
