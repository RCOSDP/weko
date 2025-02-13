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

import json
import os
import re
import shutil
import sys
import traceback
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
from functools import wraps
from typing import List

from flask import Response, Blueprint, abort, current_app, has_request_context, \
    jsonify, make_response, render_template, request, session, url_for, send_file
from flask_babelex import gettext as _
from flask_login import current_user, login_required

from .utils import *

workspace_blueprint = Blueprint(
    'weko_workspace',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/workspace'
)


# 2.1. アイテム一覧情報取得API
@workspace_blueprint.route('/')
@login_required
def get_workspace_itemlist():
        print("==========guan.shuang workspace start=========")
        
        # 変数初期化
        #　JSON条件
        jsonCondition  = {
                "name": "Alice",
                "age": 25,
                "is_student": False     
        }
    
        # reqeustからのパラメータを確認する。
        # パラメータなし、1,デフォルト絞込み条件取得処理へ。
        # パラメータあり、1,デフォルト絞込み条件取得処理をスキップ。
        if request.args:
            jsonCondition = request.args.to_dict()
        else:
            # 1,デフォルト絞込み条件取得処理
            jsonCondition = get_workspace_filterCon()


        # 2,ESからアイテム一覧取得処理
        esResult = get_es_itemlist(jsonCondition)
        data = json.loads(esResult)
        # →ループ処理
        for hit in data['hits']['hits']:
            # レコードID
            recid = hit['_id']
            # uuid
            uuid = hit['_id']
            # print(recid)

            # 3,お気に入り既読未読ステータス取得処理
            stsRes = get_workspace_status_management(recid)

            # 4,アクセス数取得処理
            accessCnt = get_access_cnt(uuid)

            # 5,アイテムステータス取得処理
            itemSts = get_item_status(recid)

            # 6,ダウンロード数取得処理
            fielList = ""
            fileDownloadCnt = get_download_cnt(fielList)

        # 7,ユーザー名と所属情報取得処理
        userInfo = get_userNm_affiliation()
        # print(userInfo[0])
        # print(userInfo[1])
        print("==========guan.shuang workspace end=========")

        return render_template(
        current_app.config['WEKO_WORKSPACE_BASE_TEMPLATE'],
        username=userInfo[0],
        affiliation=userInfo[1]
    )


# 2.2. お気に入り既読未読ステータス更新API
@workspace_blueprint.route('/updateStatus')
@login_required
def update_workspace_status_management(statusTyp):
        return None



# 2.1. デフォルト絞込み条件更新API
@workspace_blueprint.route('/updateDefaultConditon')
@login_required
def update_workspace_default_conditon(buttonTyp,default_con):
        return None


