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
from datetime import datetime, timedelta,timezone
import json
import os
import shutil
import tempfile
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
from weko_admin.api import TempDirInfo
from weko_records.api import FeedbackMailList
from invenio_db import db
from invenio_i18n.ext import current_i18n
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from sqlalchemy.exc import SQLAlchemyError
from flask import session
from weko_records.utils import selected_value_by_language

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
from weko_index_tree.models import Index
from flask_login import current_user
from weko_search_ui.utils import (
    get_data_by_property, handle_check_exist_record, handle_check_file_metadata, handle_item_title,
    handle_check_date, handle_check_id, handle_check_and_prepare_index_tree,
    handle_check_and_prepare_publish_status, import_items_to_activity,
    import_items_to_system
)
from weko_records.api import ItemTypeNames


from .utils import get_datacite_record_data, get_jalc_record_data, \
    get_cinii_record_data, get_jamas_record_data
from weko_records.serializers.utils import get_item_type_name, get_mapping
from weko_records.api import ItemTypes
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

    # Get item_type
    item_type_ids = set()
    for record in recordsData:
        item_type_ids.add(
            record['_source'].get('item_type_id')
            or record['_source']['_item_metadata'].get('item_type_id')
        )
    item_types = ItemTypes.get_records(list(item_type_ids))
    item_type_dict = {
        str(item_type.model.id): {
            "obj": item_type,
            "mapping": get_mapping(
                item_type.model.id, 'jpcoar_mapping', item_type=item_type.model
            )
        } for item_type in item_types
    }

    # ループ処理
    for record in recordsData:
        source = record.get("_source", {})
        if not source or (
            str(source.get("weko_creator_id", None)) != str(current_user.get_id()) and
            str(source.get("weko_shared_id", None)) != str(current_user.get_id())
        ):
            # If user ID does not match, skip this record
            current_app.logger.debug(f"[workspace] skip item \"_id\": {record.get('_id')}")
            continue

        workspaceItem = copy.deepcopy(current_app.config["WEKO_WORKSPACE_ITEM"])

        item_type_id = str(source.get("item_type_id") or source.get("_item_metadata", {}).get("item_type_id"))
        item_type = item_type_dict[item_type_id]["obj"]
        item_map = item_type_dict[item_type_id]["mapping"]

        # get title info
        title_value_key = 'title.@value'
        title_lang_key = 'title.@attributes.xml:lang'
        if title_value_key in item_map:
            title_languages = []
            _title_key_str = ''
            if title_lang_key in item_map:
                # get language
                title_languages, _title_key_str = get_data_by_property(
                    source.get("_item_metadata", {}), item_map, title_lang_key)
            # get value
            title_values, _title_key1_str = get_data_by_property(
                source.get("_item_metadata", {}), item_map, title_value_key)
            title_name = selected_value_by_language(
                title_languages,
                title_values,
                _title_key_str,
                _title_key1_str,
                current_i18n.language,
                source.get("_item_metadata", {}))
        workspaceItem["title"] = title_name if title_name else source.get("title", [""])[0]

        # ファイルリストと査読状況を取得
        fileList, peerReviewed = extract_metadata_info(source.get("_item_metadata", {}))

        # "recid": None,  # レコードID
        try:
            pid = PersistentIdentifier.get_by_object("recid", "rec", record.get("_id"))
        except PIDDoesNotExistError as e:
            current_app.logger.error(e)
            continue
        recid = pid.pid_value
        workspaceItem["recid"] = recid

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
        identifiers = source.get("identifier", [])
        workspaceItem["doi"] = ""
        if identifiers:
            for value in identifiers:
                if value.get("value"):
                    workspaceItem["doi"] = current_app.config.get("OAIHARVESTER_DOI_PREFIX", "") + "/" + identifiers[0].get("value", "")
                    break

        # "resourceType": None,  # リソースタイプ
        resourceType = source.get("type", [])
        workspaceItem["resourceType"] = resourceType[0] if resourceType else ""

        #  "authorlist": None,   著者リスト[著者名]
        workspaceItem["authorlist"] = (
            source["creator"]["creatorName"]
            if "creator" in source
            and source["creator"]["creatorName"]
            else None
        )

        # "accessCnt": None,  # アクセス数
        workspaceItem["accessCnt"] = get_accessCnt_downloadCnt(recid)[0]

        # "downloadCnt": None,  # ダウンロード数
        workspaceItem["downloadCnt"] = get_accessCnt_downloadCnt(recid)[1]

        # "itemStatus": None,  # アイテムステータス
        workspaceItem["itemStatus"] = get_item_status(str(recid))

        # "publicationDate": None,  # 出版年月日
        workspaceItem["publicationDate"] = source.get("publish_date", "")

        # "magazineName": None,  # 雑誌名
        workspaceItem["magazineName"] = (
            source["sourceTitle"][0]
            if "sourceTitle" in source
            else None
        )

        # "conferenceName": None,  # 会議名
        conference = source.get("conference", [])
        if conference and conference["conferenceName"]:
            workspaceItem["conferenceName"] = conference["conferenceName"][0]
        else:
            workspaceItem["conferenceName"] = None

        # "volume": None,  # 巻
        workspaceItem["volume"] = (
            source.get("volume", [])[0]
            if source.get("volume", [])
            else None
        )

        # "issue": None,  # 号
        workspaceItem["issue"] = (
            source.get("issue", [])[0]
            if source.get("issue", [])
            else None
        )

        # "funderName": None,  # 資金別情報機関名
        fundingReference = source.get("fundingReference", [])
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
            len(source["relation"]["relatedTitle"])
            if "relation" in source
            else 0
        )

        if "relation" in source:
            for i in range(relationLen):
                # "relationType": None,  # 関連情報タイプ
                workspaceItem["relationType"] = source.get("relation", [])[
                    "@attributes"
                ]["relationType"][i][0]

                # # "relationTitle": None,  # 関連情報タイトル
                workspaceItem["relationTitle"] = source.get("relation", [])[
                    "relatedTitle"
                ][i]

                # # "relationUrl": None,  # 関連情報URLやDOI
                workspaceItem["relationUrl"] = source.get("relation", [])["relatedIdentifier"][i]["value"]

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
                    "dateValue": item["date"][0]["dateValue"] if (
                        "date" in item and
                        item["date"] and
                        "dateValue" in item["date"][0]
                     ) else None,
                }
                for item in fileList if "accessrole" in item
            ]

            for accessrole_date in accessrole_date_list:
                access_role = accessrole_date["accessrole"]
                date_val = accessrole_date["dateValue"]

                if access_role == "open_access" or (
                    access_role == "open_date" and
                    date_val and
                    date_val <= datetime.now(timezone.utc).strftime("%Y-%m-%d")
                ):
                    # public
                    publicCnt += 1
                elif access_role in ["open_restricted", "open_login", 'open_no']:
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
            endpoints=endpoints,
            cur_step='item_login',
            enable_contributor=current_app.config[
                'WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'],
            enable_feedback_maillist=current_app.config[
                'WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL'],
            is_auto_set_index_action=True,
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
            endpoints=endpoints,
            cur_step='item_login',
            enable_contributor=current_app.config[
                'WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'],
            enable_feedback_maillist=current_app.config[
                'WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL'],
            is_auto_set_index_action=True,
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
        "result": "",
        "items": "",
        "error": ""
    }
    data_tmp_path = ""
    try:
        request_data = request.form.get("requestData")
        if request_data:
            request_data = json.loads(request_data)

        # upload file to tmp directory
        request_files = request.files.getlist("files[]")
        file_path_list = []
        data_tmp_path = os.path.join(
            tempfile.gettempdir(),
            current_app.config.get("WEKO_SEARCH_UI_IMPORT_TMP_PREFIX")
                + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:-3]
        )
        expire = datetime.now() + timedelta(days=1)
        TempDirInfo().set(
            data_tmp_path,
            {"expire": expire.strftime("%Y-%m-%d %H:%M:%S")}
        )
        data_path = os.path.join(data_tmp_path, "data")
        os.makedirs(data_path)
        for file in request_files:
            file_path = os.path.join(data_path, file.filename)
            file.save(file_path)
            file_path_list.append(file.filename)

        # set metadata for item registration
        settings = AdminSettings.get("workspace_workflow_settings")
        item_type_id = int(settings.item_type_id) if settings.item_type_id else None
        if settings.workFlow_select_flg == "0":
            if not settings.work_flow_id:
                result['error'] = _("Workflow ID is not set.")
                return jsonify(result)
            workflow = WorkFlow().get_workflow_by_id(settings.work_flow_id)
            item_type_id = workflow.itemtype_id
        if not item_type_id:
            result['error'] = _("Item type ID is not set.")
            return jsonify(result)
        metadata = request_data.get("recordModel", {})

        index_id_list = []
        index_list = request_data.get("indexlist", [])
        if index_list:
            indexs = Index.query.filter_by(is_deleted=False).all()
            index_id_list = [
                str(index.id)
                for index_name in index_list
                for index in indexs
                if index.index_name == index_name or index.index_name_english == index_name
            ]
        metadata["path"] = index_id_list

        item_type_name = ItemTypeNames.get_record(item_type_id)
        item_dict = {
            "root_path": data_path,
            "file_path": file_path_list,
            "metadata": metadata,
            "pos_index": index_id_list,
            "publish_status": "public",
            "item_type_id": item_type_id,
            "item_type_name": item_type_name.name,
            "$schema": "/items/jsonschema/{}".format(str(item_type_id)),
            "errors": None,
        }
        request_info = {"user_id": current_user.get_id()}

        list_record = [item_dict]
        list_record = handle_check_exist_record(list_record)
        handle_item_title(list_record)
        list_record = handle_check_date(list_record)
        handle_check_id(list_record)
        if index_id_list:
            handle_check_and_prepare_index_tree(list_record, True, [])
        handle_check_and_prepare_publish_status(list_record)
        if file_path_list:
            handle_check_file_metadata(list_record, data_path)

        if list_record[0].get("errors"):
            result['error'] = ', '.join(list_record[0].get("errors", ["error!!"]))
            return result

        if settings.workFlow_select_flg == "0":
            # registration by workflow
            request_info["workflow_id"] = settings.work_flow_id
            result["result"], _, _, result['error'] = import_items_to_activity(list_record[0], request_info)
        else:
            # directly registration
            register_result = import_items_to_system(list_record[0], request_info=request_info)
            if not register_result.get("success"):
                current_app.logger.error(
                    f"Error in import_items_to_system: {list_record[0].get('error_id')}"
                )
                result["error"] = "Error in import_items_to_system"
            result["result"] = register_result.get("recid")

    except Exception as e:
        current_app.logger.error(e)
        current_app.logger.error(traceback.format_exc())
        result["error"] = str(e)

    finally:
        # Clean up temporary directory
        if data_tmp_path and os.path.exists(data_tmp_path):
            shutil.rmtree(data_tmp_path)
            TempDirInfo().delete(data_tmp_path)

    return jsonify(result)

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
