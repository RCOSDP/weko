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
# from weko_workflow.schema.marshmallow import ActionSchema, \
#     ActivitySchema, ResponseMessageSchema, CancelSchema, PasswdSchema, LockSchema,\
#     ResponseLockSchema, LockedValueSchema, GetFeedbackMailListSchema, SaveActivityResponseSchema,\
#     SaveActivitySchema, CheckApprovalSchema,ResponseUnlockSchema
# from weko_workflow.schema.utils import get_schema_action, type_null_check
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
# from weko_items_ui.api import item_login
from weko_records.api import FeedbackMailList, ItemLink
from weko_records.models import ItemMetadata
from weko_records.serializers.utils import get_item_type_name
# from weko_records_ui.models import FilePermission
# from weko_search_ui.utils import check_import_items, import_items_to_system
from weko_user_profiles.config import \
    WEKO_USERPROFILES_INSTITUTE_POSITION_LIST, \
    WEKO_USERPROFILES_POSITION_LIST

# from .api import Action, Flow, GetCommunity, WorkActivity, \
#     WorkActivityHistory, WorkFlow
from .config import IDENTIFIER_GRANT_LIST, IDENTIFIER_GRANT_SELECT_DICT, \
    IDENTIFIER_GRANT_SUFFIX_METHOD, WEKO_WORKFLOW_TODO_TAB
from .errors import ActivityBaseRESTError, ActivityNotFoundRESTError, \
    DeleteActivityFailedRESTError, InvalidInputRESTError, \
    RegisteredActivityNotFoundRESTError
# from .models import ActionStatusPolicy, Activity, ActivityAction, \
#     ActivityStatusPolicy, FlowAction, GuestActivity
from .romeo import search_romeo_issn, search_romeo_jtitles
from .scopes import activity_scope
# from .utils import IdentifierHandle, auto_fill_title, \
#     check_authority_by_admin, check_continue, check_doi_validation_not_pass, \
#     check_existed_doi, is_terms_of_use_only, \
#     delete_cache_data, delete_guest_activity, filter_all_condition, \
#     get_account_info, get_actionid, get_activity_display_info, \
#     get_activity_id_of_record_without_version, \
#     get_application_and_approved_date, get_approval_keys, get_cache_data, \
#     get_files_and_thumbnail, get_identifier_setting, get_main_record_detail, \
#     get_pid_and_record, get_pid_value_by_activity_detail, \
#     get_record_by_root_ver, get_thumbnails, get_usage_data, \
#     get_workflow_item_type_names, grant_access_rights_to_all_open_restricted_files, handle_finish_workflow, \
#     init_activity_for_guest_user, is_enable_item_name_link, \
#     is_hidden_pubdate, is_show_autofill_metadata, \
#     is_usage_application_item_type, prepare_data_for_guest_activity, \
#     prepare_doi_link_workflow, process_send_approval_mails, \
#     process_send_notification_mail, process_send_reminder_mail, register_hdl, \
#     save_activity_data, saving_doi_pidstore, \
#     send_usage_application_mail_for_guest_user, set_files_display_type, \
#     update_approval_date, update_cache_data, validate_guest_activity_expired, \
#     validate_guest_activity_token, make_activitylog_tsv, \
#     delete_lock_activity_cache, delete_user_lock_activity_cache

workspace_blueprint = Blueprint(
    'weko_workspace',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/workspace'
)

@workspace_blueprint.route('/workspace')
@login_required
def workspace():
        print("==========guan.shuang workspace =========")
        # return None
        return render_template(
        # 'weko_workflow/workspaceItemList.html'
        'weko_workspace/workspace_base.html'
    )