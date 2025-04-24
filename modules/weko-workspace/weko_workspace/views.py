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
import traceback

from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
)
from flask_babelex import gettext as _
from flask_login import current_user, login_required
from flask_menu import register_menu
from weko_records.api import FeedbackMailList
from invenio_db import db
from sqlalchemy.exc import SQLAlchemyError
from flask import session

from .utils import (
    extract_metadata_info,
    get_accessCnt_downloadCnt,
    get_es_itemlist,
    get_item_status,
    get_userNm_affiliation,
    get_workspace_status_management,
    insert_workspace_status,
    update_workspace_status,
    get_workspace_filterCon,
    changeLang,
    changeMsg
)
from .models import WorkspaceDefaultConditions

from weko_admin.models import AdminSettings
from weko_workflow.api import WorkFlow
from weko_items_ui.utils import is_schema_include_key
from flask_wtf import FlaskForm
from weko_workflow.utils import is_show_autofill_metadata

from weko_user_profiles.views import get_user_profile_info
from weko_accounts.utils import login_required_customize
from weko_workflow.headless.activity import HeadlessActivity
from weko_index_tree.models import Index
from flask_login import current_user
from weko_search_ui.utils import handle_check_exist_record, handle_item_title, \
    handle_check_date, handle_check_id, handle_check_and_prepare_index_tree, \
    handle_check_and_prepare_publish_status, import_items_to_system
from weko_records.api import ItemTypeNames


from .utils import get_datacite_record_data, get_jalc_record_data, \
    get_cinii_record_data, get_jamas_record_data
from weko_records.serializers.utils import get_item_type_name
from weko_records.api import ItemTypes
from weko_user_profiles.config import (
    WEKO_USERPROFILES_INSTITUTE_POSITION_LIST,
    WEKO_USERPROFILES_POSITION_LIST,
)
from .defaultfilters import merge_default_filters

workspace_blueprint = Blueprint(
    "weko_workspace",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/workspace",
)


blueprint_itemapi = Blueprint(
    "weko_workspace_api",
    __name__,
    url_prefix="/workspaceAPI",
)


# 2.1. アイテム一覧情報取得API
@workspace_blueprint.route("/", methods=["GET", "POST"])
@login_required
@register_menu(
    workspace_blueprint, 'settings.workspace',
    _('%(icon)s Workspace', icon='<i class="fa fa-list-alt fa-fw"></i>'),
    order=101) # after 'settings.admin'
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
    lang = session['language']

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
            defaultconditions=changeLang(lang, jsonCondition),
        )

    # Get items owned by this user.
    recordsDataList = []
    for item in recordsData["hits"]["hits"]:
        metadata = item.get("metadata", {})
        if (
            metadata.get("weko_creator_id") == str(current_user.id)
            or metadata.get("weko_shared_id") == current_user.id
        ):
            recordsDataList.append(item)

    # →ループ処理
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

        if workspaceItem["authorlist"] and userNm in workspaceItem["authorlist"]:
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
                access_role = accessrole_date["accessrole"]
                date_val = accessrole_date["dateValue"]

                if access_role == "open_access" or \
                    (access_role == "open_date" and date_val <= datetime.now(timezone.utc).strftime("%Y-%m-%d")):
                    # public
                    publicCnt += 1
                elif access_role == "open_restricted":
                    # restricted
                    restrictedPublicationCnt += 1
                else:
                    # embargo
                    embargoedCnt += 1
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
            'related_to_paper': 'connectionToPaperSts',
            'funder_name': 'funderName',
            'award_title': 'awardTitle',
        }

        # フィルタリング処理
        filteredItems = []
        for item in workspaceItemList:
            match = True
            for key, value in filter_mapping.items():
                if key in jsonCondition and jsonCondition[key] is not None and jsonCondition[key] != []:
                    if key in ['resource_type', 'award_title', 'funder_name']:
                        if item[value] not in jsonCondition[key]:
                            match = False
                            break
                    elif item[value] != jsonCondition[key]:
                        match = False
                        break
            if match:
                filteredItems.append(item)

        workspaceItemList = filteredItems

    else:
        defaultconditions = jsonCondition

    defaultconditions["funder_name"]["options"] = list(dict.fromkeys(funderNameList))
    defaultconditions["award_title"]["options"] = list(dict.fromkeys(awardTitleList))

    return render_template(
        current_app.config["WEKO_WORKSPACE_BASE_TEMPLATE"],
        username=userNm,
        workspaceItemList=workspaceItemList,
        defaultconditions=changeLang(lang, defaultconditions),
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
    lang = session['language']

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

        message = "Successfully saved default conditions."
        message = changeMsg(lang, 1, None, message)
        return (
            jsonify(
                {
                    "status": "success",
                    "message": message,
                }
            ),
            200,
        )

    except SQLAlchemyError as e:
        db.session.rollback()
        error_message = (
            f"Failed to save default conditions. Due to database error: {str(e)}"
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
    lang = session['language']

    try:
        record = WorkspaceDefaultConditions.query.filter_by(user_id=user_id).first()

        if record:
            db.session.delete(record)
            db.session.commit()
            
            message = "Successfully reset default conditions."
            message = changeMsg(lang, 2, True, message)
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": message,
                    }
                ),
                200,
            )
        else:
            message = "No default conditions found to reset."
            message = changeMsg(lang, 2, False, message)
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": message,
                    }
                ),
                200,
            )

    except SQLAlchemyError as e:
        db.session.rollback()
        error_message = (
            f"Failed to reset default conditions. Due to database error: {str(e)}"
        )
        return jsonify({"status": "error", "message": error_message}), 500
    except Exception as e:
        error_message = f"Unexpected error occurred: {str(e)}"
        return jsonify({"status": "error", "message": error_message}), 500


@workspace_blueprint.route('/item_registration', methods=['GET', 'POST'], endpoint='itemregister')
@login_required
def item_register():
    """Registration screen.

    :return: item_register.html
    """
    need_billing_file = False
    need_file = False
    settings = AdminSettings.get('workspace_workflow_settings')
    if settings.workFlow_select_flg == '0':
        workflow = WorkFlow()
        workflow_detail = workflow.get_workflow_by_id(settings.work_flow_id)
        if  workflow_detail.index_tree_id is not None:
            workflow_selected = True
        else:
            workflow_selected = False

        item_type = ItemTypes.get_by_id(workflow_detail.itemtype_id)
        user_id = current_user.id if hasattr(current_user , 'id') else None
        user_profile = None
        if user_id:

            user_profile={}
            user_profile['results'] = get_user_profile_info(int(user_id))

        if item_type is None:
            return render_template('weko_items_ui/iframe/error.html',
                                    error_type='no_itemtype'),404
        need_file, need_billing_file = is_schema_include_key(item_type.schema)


        json_schema = '/items/jsonschema/{}'.format(workflow_detail.itemtype_id)
        schema_form = '/items/schemaform/{}'.format(workflow_detail.itemtype_id)
        record = {}
        files = []
        endpoints = {}

        form = FlaskForm(request.form)
        institute_position_list = WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
        position_list = WEKO_USERPROFILES_POSITION_LIST

        item_type_name = get_item_type_name(workflow_detail.itemtype_id)
        show_autofill_metadata = is_show_autofill_metadata(item_type_name)

        return render_template(
            'weko_workspace/item_register.html',
            need_file=need_file,
            need_billing_file=need_billing_file,
            records=record,
            jsonschema=json_schema,
            schemaform=schema_form,
            id=workflow_detail.itemtype_id,
            itemtype_id=workflow_detail.itemtype_id,
            files=files,
            licences=current_app.config.get('WEKO_RECORDS_UI_LICENSE_DICT'),
            workflow_selected=workflow_selected,
            institute_position_list=institute_position_list,
            position_list=position_list,
            endpoints=endpoints,
            cur_step='item_login',
            enable_contributor=current_app.config[
                'WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'],
            enable_feedback_maillist=current_app.config[
                'WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL'],

            is_auto_set_index_action=True,
            item_save_uri='/items/iframe/model/save',
            page=None,

            is_show_autofill_metadata=show_autofill_metadata,
            form=form
        )
    else:
        item_type_id_as_int = int(settings.item_type_id)
        item_type = ItemTypes.get_by_id(item_type_id_as_int)
        user_id = current_user.id if hasattr(current_user , 'id') else None
        user_profile = None
        if user_id:
            user_profile={}
            user_profile['results'] = get_user_profile_info(int(user_id))

        if item_type is None:
            return render_template('weko_items_ui/iframe/error.html',
                                    error_type='no_itemtype'),404
        need_file, need_billing_file = is_schema_include_key(item_type.schema)

        json_schema = '/items/jsonschema/{}'.format(settings.item_type_id)
        schema_form = '/items/schemaform/{}'.format(settings.item_type_id)
        record = {}
        files = []
        endpoints = {}
        form = FlaskForm(request.form)
        institute_position_list = WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
        position_list = WEKO_USERPROFILES_POSITION_LIST

        item_type_name = get_item_type_name(settings.item_type_id)
        show_autofill_metadata = is_show_autofill_metadata(item_type_name)

        return render_template(
            'weko_workspace/item_register.html',
            need_file=need_file,
            need_billing_file=need_billing_file,
            records=record,
            jsonschema=json_schema,
            schemaform=schema_form,
            id=settings.item_type_id,
            itemtype_id=settings.item_type_id,
            files=files,
            licences=current_app.config.get('WEKO_RECORDS_UI_LICENSE_DICT'),

            institute_position_list=institute_position_list,
            position_list=position_list,
            endpoints=endpoints,
            cur_step='item_login',
            enable_contributor=current_app.config[
                'WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'],
            enable_feedback_maillist=current_app.config[
                'WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL'],

            is_auto_set_index_action=True,
            item_save_uri='/items/iframe/model/save',
            page=None,

            is_show_autofill_metadata=show_autofill_metadata,
            form=form
        )


@blueprint_itemapi.route('/get_auto_fill_record_data_jamasapi', methods=['POST'])
@login_required_customize
def get_auto_fill_record_data_jamasapi():
    """Get auto fill record data from Jamas API.

    :return: record model as json
    """
    result = {
        'result': '',
        'items': '',
        'error': ''
    }

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()

    search_data = data.get('search_data', '')
    item_type_id = data.get('item_type_id', '')

    try:
        api_response = get_jamas_record_data(
            search_data, item_type_id)
        result['result'] = api_response
    except Exception as e:
        current_app.logger.error(e)
        current_app.logger.error(traceback.format_exc())
        result['error'] = str(e)
    return jsonify(result)


@blueprint_itemapi.route('/get_auto_fill_record_data_ciniiapi', methods=['POST'])
@login_required_customize
def get_auto_fill_record_data_ciniiapi():
    """Get auto fill record data.

    :return: record model as json
    """
    result = {
        'result': '',
        'items': '',
        'error': ''
    }

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    search_data = data.get('search_data', '')
    item_type_id = data.get('item_type_id', '')

    try:
        api_response = get_cinii_record_data(
            search_data, item_type_id)
        result['result'] = api_response
    except Exception as e:
        current_app.logger.error(e)
        current_app.logger.error(traceback.format_exc())
        result['error'] = str(e)
    return jsonify(result)


@blueprint_itemapi.route('/get_auto_fill_record_data_jalcapi', methods=['POST'])
@login_required_customize
def get_auto_fill_record_data_jalcapi():
    """Get auto fill record data.

    :return: record model as json
    """
    result = {
        'result': '',
        'items': '',
        'error': ''
    }

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    search_data = data.get('search_data', '')
    item_type_id = data.get('item_type_id', '')
    try:
        api_response = get_jalc_record_data(
            search_data, item_type_id)
        result['result'] = api_response
    except Exception as e:
        current_app.logger.error(e)
        current_app.logger.error(traceback.format_exc())
        result['error'] = str(e)
    return jsonify(result)


@blueprint_itemapi.route('/get_auto_fill_record_data_dataciteapi', methods=['POST'])
@login_required_customize
def get_auto_fill_record_data_dataciteapi():
    """Get auto fill record data.

    :return: record model as json
    """
    result = {
        'result': '',
        'items': '',
        'error': ''
    }

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    search_data = data.get('search_data', '')
    item_type_id = data.get('item_type_id', '')
    try:
        api_response = get_datacite_record_data(
            search_data, item_type_id)

        result['result'] = api_response
    except Exception as e:
        current_app.logger.error(e)
        current_app.logger.error(traceback.format_exc())
        result['error'] = str(e)
    return jsonify(result)


@workspace_blueprint.route('/workflow_registration', methods=['POST'], endpoint='workflow_registration')
@login_required
def item_register_save():
    """Item Registration.

    :return: response
    """
    result = {
        'result': '',
        'items': '',
        'error': ''
    }

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    item = data.get('recordModel', '')
    settings = AdminSettings.get('workspace_workflow_settings')

    indexIdList = []
    indexList = data.get('indexlist', '')
    for indexName in indexList:
        indexs = Index.query.filter_by(is_deleted=False).all()
        for index in indexs:
            if index.index_name == indexName or index.index_name_english == indexName:
                indexIdList.append(str(index.id))
    if settings.workFlow_select_flg == '0':
        # registration by workflow
        grant_data = {}
        link_data = []
        comment = ""
        index =  []
        item['path'] = []
        files = []
        for key in item:
            if isinstance(item[key], list):
                for file in item[key]:
                    if "filename" in file:
                        files.append(file)
        settings = AdminSettings.get('workspace_workflow_settings')
        workflow = WorkFlow()
        workflow_detail = workflow.get_workflow_by_id(settings.work_flow_id)
        if  workflow_detail.index_tree_id is not None:
            item['path'].append(workflow_detail.index_tree_id)
            index.append(workflow_detail.index_tree_id)
        else:
            item['path'] = indexIdList
            index = indexIdList
        item['publish_status'] = '2'
        workspace_register = True
        try:
            headless = HeadlessActivity()
            user_id=current_user.get_id()
            api_response = headless.auto(
                user_id= user_id, workflow_id=settings.work_flow_id,
                index=index, metadata=item, files=files, comment=comment,
                link_data=link_data, grant_data=grant_data, 
                workspace_register=workspace_register
            )

            result['result'] = api_response
        except Exception as e:
            current_app.logger.error(e)
            current_app.logger.error(traceback.format_exc())
            result['error'] = str(e)
        return jsonify(result)
    else:
        # directly registration
        try:
            list_record = []
            item_dict = {}
            item['path'] = indexIdList
            item_dict['metadata'] = item

            item_type_name = ItemTypeNames.get_record(int(settings.item_type_id))

            item_dict['pos_index'] = indexList

            item_dict['publish_status'] = "public"
            item_dict['item_type_id'] = int(settings.item_type_id)

            item_dict['item_type_name'] = item_type_name.name
            item_dict['errors'] = None
            item_dict['$schema'] = '/items/jsonschema/{}'.format(settings.item_type_id)
            all_index_permission=True
            can_edit_indexes=[]

            list_record.append(item_dict)

            # current_app.logger.debug("list_record1: {}".format(list_record))
            # [{'pos_index': ['Index A'], 'publish_status': 'public', 'feedback_mail': ['wekosoftware@nii.ac.jp'], 'edit_mode': 'Keep', 'metadata': {'pubdate': '2021-03-19', 'item_1617186331708': [{'subitem_1551255647225': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000001(public_open_access_simple)', 'subitem_1551255648112': 'en'}], 'item_1617186385884': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}], 'item_1617186419668': [{'creatorAffiliations': [{'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048'}], 'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}]}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '4', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}], 'item_1617349709064': [{'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'contributorName': '情報, 太郎', 'lang': 'ja'}, {'contributorName': 'ジョウホウ, タロウ', 'lang': 'ja-Kana'}, {'contributorName': 'Joho, Taro', 'lang': 'en'}], 'contributorType': 'ContactPerson', 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}], 'item_1617186476635': {'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}, 'item_1617351524846': {'subitem_1523260933860': 'Unknown'}, 'item_1617186499011': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}], 'item_1617610673286': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}], 'rightHolderNames': [{'rightHolderLanguage': 'ja', 'rightHolderName': 'Right Holder Name'}]}], 'item_1617186609386': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}], 'item_1617186626617': [{'subitem_description': 'Description\nDescription<br/>Description', 'subitem_description_language': 'en', 'subitem_description_type': 'Abstract'}, {'subitem_description': '概要\n概要\n概要\n概要', 'subitem_description_language': 'ja', 'subitem_description_type': 'Abstract'}], 'item_1617186643794': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}], 'item_1617186660861': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}], 'item_1617186702042': [{'subitem_1551255818386': 'jpn'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_1617349808926': {'subitem_1523263171732': 'Version'}, 'item_1617265215918': {'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}, 'item_1617186783814': [{'subitem_identifier_type': 'URI', 'subitem_identifier_uri': 'http://localhost'}], 'item_1617353299429': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}], 'item_1617186859717': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}], 'item_1617186882738': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}], 'item_1617186901218': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}], 'item_1617186920753': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}], 'item_1617186941041': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}], 'item_1617186959569': {'subitem_1551256328147': '1'}, 'item_1617186981471': {'subitem_1551256294723': '111'}, 'item_1617186994930': {'subitem_1551256248092': '12'}, 'item_1617187024783': {'subitem_1551256198917': '1'}, 'item_1617187045071': {'subitem_1551256185532': '3'}, 'item_1617187112279': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}], 'item_1617187136212': {'subitem_1551256096004': '2021-06-30'}, 'item_1617944105607': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}], 'item_1617187187528': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}], 'item_1617605131499': [{'accessrole': 'open_access', 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'displaytype': 'simple', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'format': 'text/plain'}, {'filename': ''}], 'item_1617620223087': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}]}, 'file_path': ['file00000001/1KB.pdf', ''], 'item_type_name': 'デフォルトアイテムタイプ（フル）', 'item_type_id': 15, '$schema': 'https://localhost:8443/items/jsonschema/15', 'identifier_key': 'item_1617186819068', 'errors': None}]
            list_record = handle_check_exist_record(list_record)
            # current_app.logger.debug("list_record2: {}".format(list_record))
            # [{'pos_index': ['Index A'], 'publish_status': 'public', 'feedback_mail': ['wekosoftware@nii.ac.jp'], 'edit_mode': 'Keep', 'metadata': {'pubdate': '2021-03-19', 'item_1617186331708': [{'subitem_1551255647225': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000001(public_open_access_simple)', 'subitem_1551255648112': 'en'}], 'item_1617186385884': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}], 'item_1617186419668': [{'creatorAffiliations': [{'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048'}], 'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}]}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '4', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}], 'item_1617349709064': [{'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'contributorName': '情報, 太郎', 'lang': 'ja'}, {'contributorName': 'ジョウホウ, タロウ', 'lang': 'ja-Kana'}, {'contributorName': 'Joho, Taro', 'lang': 'en'}], 'contributorType': 'ContactPerson', 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}], 'item_1617186476635': {'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}, 'item_1617351524846': {'subitem_1523260933860': 'Unknown'}, 'item_1617186499011': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}], 'item_1617610673286': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}], 'rightHolderNames': [{'rightHolderLanguage': 'ja', 'rightHolderName': 'Right Holder Name'}]}], 'item_1617186609386': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}], 'item_1617186626617': [{'subitem_description': 'Description\nDescription<br/>Description', 'subitem_description_language': 'en', 'subitem_description_type': 'Abstract'}, {'subitem_description': '概要\n概要\n概要\n概要', 'subitem_description_language': 'ja', 'subitem_description_type': 'Abstract'}], 'item_1617186643794': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}], 'item_1617186660861': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}], 'item_1617186702042': [{'subitem_1551255818386': 'jpn'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_1617349808926': {'subitem_1523263171732': 'Version'}, 'item_1617265215918': {'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}, 'item_1617186783814': [{'subitem_identifier_type': 'URI', 'subitem_identifier_uri': 'http://localhost'}], 'item_1617353299429': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}], 'item_1617186859717': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}], 'item_1617186882738': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}], 'item_1617186901218': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}], 'item_1617186920753': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}], 'item_1617186941041': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}], 'item_1617186959569': {'subitem_1551256328147': '1'}, 'item_1617186981471': {'subitem_1551256294723': '111'}, 'item_1617186994930': {'subitem_1551256248092': '12'}, 'item_1617187024783': {'subitem_1551256198917': '1'}, 'item_1617187045071': {'subitem_1551256185532': '3'}, 'item_1617187112279': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}], 'item_1617187136212': {'subitem_1551256096004': '2021-06-30'}, 'item_1617944105607': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}], 'item_1617187187528': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}], 'item_1617605131499': [{'accessrole': 'open_access', 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'displaytype': 'simple', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'format': 'text/plain'}, {'filename': ''}], 'item_1617620223087': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}]}, 'file_path': ['file00000001/1KB.pdf', ''], 'item_type_name': 'デフォルトアイテムタイプ（フル）', 'item_type_id': 15, '$schema': 'https://localhost:8443/items/jsonschema/15', 'identifier_key': 'item_1617186819068', 'errors': None, 'status': 'new', 'id': None}]
            handle_item_title(list_record)
            # current_app.logger.debug("list_record3: {}".format(list_record))
            # [{'pos_index': ['Index A'], 'publish_status': 'public', 'feedback_mail': ['wekosoftware@nii.ac.jp'], 'edit_mode': 'Keep', 'metadata': {'pubdate': '2021-03-19', 'item_1617186331708': [{'subitem_1551255647225': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000001(public_open_access_simple)', 'subitem_1551255648112': 'en'}], 'item_1617186385884': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}], 'item_1617186419668': [{'creatorAffiliations': [{'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048'}], 'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}]}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '4', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}], 'item_1617349709064': [{'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'contributorName': '情報, 太郎', 'lang': 'ja'}, {'contributorName': 'ジョウホウ, タロウ', 'lang': 'ja-Kana'}, {'contributorName': 'Joho, Taro', 'lang': 'en'}], 'contributorType': 'ContactPerson', 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}], 'item_1617186476635': {'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}, 'item_1617351524846': {'subitem_1523260933860': 'Unknown'}, 'item_1617186499011': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}], 'item_1617610673286': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}], 'rightHolderNames': [{'rightHolderLanguage': 'ja', 'rightHolderName': 'Right Holder Name'}]}], 'item_1617186609386': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}], 'item_1617186626617': [{'subitem_description': 'Description\nDescription<br/>Description', 'subitem_description_language': 'en', 'subitem_description_type': 'Abstract'}, {'subitem_description': '概要\n概要\n概要\n概要', 'subitem_description_language': 'ja', 'subitem_description_type': 'Abstract'}], 'item_1617186643794': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}], 'item_1617186660861': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}], 'item_1617186702042': [{'subitem_1551255818386': 'jpn'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_1617349808926': {'subitem_1523263171732': 'Version'}, 'item_1617265215918': {'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}, 'item_1617186783814': [{'subitem_identifier_type': 'URI', 'subitem_identifier_uri': 'http://localhost'}], 'item_1617353299429': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}], 'item_1617186859717': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}], 'item_1617186882738': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}], 'item_1617186901218': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}], 'item_1617186920753': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}], 'item_1617186941041': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}], 'item_1617186959569': {'subitem_1551256328147': '1'}, 'item_1617186981471': {'subitem_1551256294723': '111'}, 'item_1617186994930': {'subitem_1551256248092': '12'}, 'item_1617187024783': {'subitem_1551256198917': '1'}, 'item_1617187045071': {'subitem_1551256185532': '3'}, 'item_1617187112279': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}], 'item_1617187136212': {'subitem_1551256096004': '2021-06-30'}, 'item_1617944105607': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}], 'item_1617187187528': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}], 'item_1617605131499': [{'accessrole': 'open_access', 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'displaytype': 'simple', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'format': 'text/plain'}, {'filename': ''}], 'item_1617620223087': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}]}, 'file_path': ['file00000001/1KB.pdf', ''], 'item_type_name': 'デフォルトアイテムタイプ（フル）', 'item_type_id': 15, '$schema': 'https://localhost:8443/items/jsonschema/15', 'identifier_key': 'item_1617186819068', 'errors': None, 'status': 'new', 'id': None, 'item_title': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)'}]

            list_record = handle_check_date(list_record)
            # current_app.logger.debug("list_record4: {}".format(list_record))
            # [{'pos_index': ['Index A'], 'publish_status': 'public', 'feedback_mail': ['wekosoftware@nii.ac.jp'], 'edit_mode': 'Keep', 'metadata': {'pubdate': '2021-03-19', 'item_1617186331708': [{'subitem_1551255647225': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000001(public_open_access_simple)', 'subitem_1551255648112': 'en'}], 'item_1617186385884': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}], 'item_1617186419668': [{'creatorAffiliations': [{'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048'}], 'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}]}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '4', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}], 'item_1617349709064': [{'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'contributorName': '情報, 太郎', 'lang': 'ja'}, {'contributorName': 'ジョウホウ, タロウ', 'lang': 'ja-Kana'}, {'contributorName': 'Joho, Taro', 'lang': 'en'}], 'contributorType': 'ContactPerson', 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}], 'item_1617186476635': {'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}, 'item_1617351524846': {'subitem_1523260933860': 'Unknown'}, 'item_1617186499011': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}], 'item_1617610673286': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}], 'rightHolderNames': [{'rightHolderLanguage': 'ja', 'rightHolderName': 'Right Holder Name'}]}], 'item_1617186609386': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}], 'item_1617186626617': [{'subitem_description': 'Description\nDescription<br/>Description', 'subitem_description_language': 'en', 'subitem_description_type': 'Abstract'}, {'subitem_description': '概要\n概要\n概要\n概要', 'subitem_description_language': 'ja', 'subitem_description_type': 'Abstract'}], 'item_1617186643794': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}], 'item_1617186660861': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}], 'item_1617186702042': [{'subitem_1551255818386': 'jpn'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_1617349808926': {'subitem_1523263171732': 'Version'}, 'item_1617265215918': {'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}, 'item_1617186783814': [{'subitem_identifier_type': 'URI', 'subitem_identifier_uri': 'http://localhost'}], 'item_1617353299429': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}], 'item_1617186859717': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}], 'item_1617186882738': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}], 'item_1617186901218': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}], 'item_1617186920753': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}], 'item_1617186941041': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}], 'item_1617186959569': {'subitem_1551256328147': '1'}, 'item_1617186981471': {'subitem_1551256294723': '111'}, 'item_1617186994930': {'subitem_1551256248092': '12'}, 'item_1617187024783': {'subitem_1551256198917': '1'}, 'item_1617187045071': {'subitem_1551256185532': '3'}, 'item_1617187112279': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}], 'item_1617187136212': {'subitem_1551256096004': '2021-06-30'}, 'item_1617944105607': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}], 'item_1617187187528': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}], 'item_1617605131499': [{'accessrole': 'open_access', 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'displaytype': 'simple', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'format': 'text/plain'}, {'filename': ''}], 'item_1617620223087': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}]}, 'file_path': ['file00000001/1KB.pdf', ''], 'item_type_name': 'デフォルトアイテムタイプ（フル）', 'item_type_id': 15, '$schema': 'https://localhost:8443/items/jsonschema/15', 'identifier_key': 'item_1617186819068', 'errors': None, 'status': 'new', 'id': None, 'item_title': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)'}]
            handle_check_id(list_record)

            handle_check_and_prepare_index_tree(list_record, all_index_permission, can_edit_indexes)
            # current_app.logger.debug("list_record5: {}".format(list_record))
            # [{'pos_index': ['Index A'], 'publish_status': 'public', 'feedback_mail': ['wekosoftware@nii.ac.jp'], 'edit_mode': 'Keep', 'metadata': {'pubdate': '2021-03-19', 'item_1617186331708': [{'subitem_1551255647225': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000001(public_open_access_simple)', 'subitem_1551255648112': 'en'}], 'item_1617186385884': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}], 'item_1617186419668': [{'creatorAffiliations': [{'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048'}], 'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}]}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '4', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}], 'item_1617349709064': [{'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'contributorName': '情報, 太郎', 'lang': 'ja'}, {'contributorName': 'ジョウホウ, タロウ', 'lang': 'ja-Kana'}, {'contributorName': 'Joho, Taro', 'lang': 'en'}], 'contributorType': 'ContactPerson', 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}], 'item_1617186476635': {'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}, 'item_1617351524846': {'subitem_1523260933860': 'Unknown'}, 'item_1617186499011': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}], 'item_1617610673286': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}], 'rightHolderNames': [{'rightHolderLanguage': 'ja', 'rightHolderName': 'Right Holder Name'}]}], 'item_1617186609386': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}], 'item_1617186626617': [{'subitem_description': 'Description\nDescription<br/>Description', 'subitem_description_language': 'en', 'subitem_description_type': 'Abstract'}, {'subitem_description': '概要\n概要\n概要\n概要', 'subitem_description_language': 'ja', 'subitem_description_type': 'Abstract'}], 'item_1617186643794': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}], 'item_1617186660861': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}], 'item_1617186702042': [{'subitem_1551255818386': 'jpn'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_1617349808926': {'subitem_1523263171732': 'Version'}, 'item_1617265215918': {'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}, 'item_1617186783814': [{'subitem_identifier_type': 'URI', 'subitem_identifier_uri': 'http://localhost'}], 'item_1617353299429': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}], 'item_1617186859717': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}], 'item_1617186882738': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}], 'item_1617186901218': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}], 'item_1617186920753': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}], 'item_1617186941041': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}], 'item_1617186959569': {'subitem_1551256328147': '1'}, 'item_1617186981471': {'subitem_1551256294723': '111'}, 'item_1617186994930': {'subitem_1551256248092': '12'}, 'item_1617187024783': {'subitem_1551256198917': '1'}, 'item_1617187045071': {'subitem_1551256185532': '3'}, 'item_1617187112279': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}], 'item_1617187136212': {'subitem_1551256096004': '2021-06-30'}, 'item_1617944105607': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}], 'item_1617187187528': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}], 'item_1617605131499': [{'accessrole': 'open_access', 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'displaytype': 'simple', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'format': 'text/plain'}, {'filename': ''}], 'item_1617620223087': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}], 'path': [1031]}, 'file_path': ['file00000001/1KB.pdf', ''], 'item_type_name': 'デフォルトアイテムタイプ（フル）', 'item_type_id': 15, '$schema': 'https://localhost:8443/items/jsonschema/15', 'identifier_key': 'item_1617186819068', 'errors': None, 'status': 'new', 'id': None, 'item_title': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)'}]

            handle_check_and_prepare_publish_status(list_record)


            request_info = {}

            register_result = import_items_to_system(list_record[0], request_info=request_info)
            if not register_result.get("success"):
                current_app.logger.error(
                    f"Error in import_items_to_system: {item.get('error_id')}"
                )

                result['error'] = "Error in import_items_to_system"
            result['result'] = register_result.get("recid")
        except Exception as e:
            current_app.logger.error(e)
            current_app.logger.error(traceback.format_exc())
            result['error'] = str(e)
        return result

@workspace_blueprint.teardown_request
@blueprint_itemapi.teardown_request
def dbsession_clean(exception):
    """
    Cleans up the database session after each request.

    Args:
        exception (Exception): The exception that occurred during the request.

    Returns:
        None

    Raises:
        None
    """
    current_app.logger.debug("weko_workspace dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()
