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
from flask_breadcrumbs import register_breadcrumb
from flask_login import current_user, login_required
from flask_menu import current_menu


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
# @register_menu(
#     workspace_blueprint, 'settings.Workspace',
#     _('%(icon)sWorkspace', icon='<i class="fa fa-list-alt" aria-hidden="true" style="margin-right: 8px;"></i>'),
#     order=20)
# @register_breadcrumb(workspace_blueprint, 'breadcrumbs.settings.Workspace', _('Workspace'))
def get_workspace_itemlist():
        print("==========guan.shuang workspace =========")
        # return None
        return render_template(
        'weko_workspace/workspace_base.html'
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


