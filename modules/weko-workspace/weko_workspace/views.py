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

import redis
from redis import sentinel
from marshmallow.exceptions import ValidationError

from flask import Response, Blueprint, abort, current_app, has_request_context, \
    jsonify, make_response, render_template, request, session, url_for, send_file
from flask_babelex import gettext as _
from flask_login import current_user, login_required
from weko_admin.api import validate_csrf_header
from flask_wtf import FlaskForm
from invenio_accounts.models import Role, User, userrole
from invenio_db import db
from invenio_files_rest.utils import remove_file_cancel_action
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore.errors import PIDDoesNotExistError,PIDDeletedError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_rest import ContentNegotiatedMethodView
from simplekv.memory.redisstore import RedisStore
from sqlalchemy import types,or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.expression import cast
from weko_redis import RedisConnection
from weko_accounts.api import ShibUser
from weko_accounts.utils import login_required_customize
from weko_authors.models import Authors
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_deposit.links import base_factory
from weko_deposit.pidstore import get_record_identifier, \
    get_record_without_version
from weko_deposit.signals import item_created
from weko_records.api import FeedbackMailList, ItemLink
from weko_records.models import ItemMetadata
from weko_records.serializers.utils import get_item_type_name
from weko_user_profiles.config import \
    WEKO_USERPROFILES_INSTITUTE_POSITION_LIST, \
    WEKO_USERPROFILES_POSITION_LIST
from .config import IDENTIFIER_GRANT_LIST, IDENTIFIER_GRANT_SELECT_DICT, \
    IDENTIFIER_GRANT_SUFFIX_METHOD, WEKO_WORKFLOW_TODO_TAB
from .errors import ActivityBaseRESTError, ActivityNotFoundRESTError, \
    DeleteActivityFailedRESTError, InvalidInputRESTError, \
    RegisteredActivityNotFoundRESTError

from .romeo import search_romeo_issn, search_romeo_jtitles
from .scopes import activity_scope

# =============本物=================
from flask_menu import register_menu
from flask_breadcrumbs import register_breadcrumb


workspace_blueprint = Blueprint(
    'weko_workspace',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/workspace'
)

@workspace_blueprint.route('/getworkspaceitemlist')
@login_required
# @register_menu(
#     workspace_blueprint, 'settings.Workspace',
#     _('%(icon)s Workspace', icon='<i class="fa fa-list-alt" aria-hidden="true" style="margin-right: 8px;"></i>'),
#     order=20)
# @register_breadcrumb(workspace_blueprint, 'breadcrumbs.settings.Workspace', _('Workspace'))
def get_workspace_itemlist():
        print("==========guan.shuang workspace =========")
        # return None
        return render_template(
        'weko_workspace/workspace_base.html'
    )


@workspace_blueprint.route('/updateworkspacestatusmanagement')
@login_required
def update_workspace_status_management(statusTyp):

        return None
