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

"""Weko Search-UI admin."""

import codecs
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
import traceback
from urllib.parse import urlencode
import pickle
import sys

from blinker import Namespace
from celery import chord
from flask import Response, abort, current_app, jsonify, make_response, request
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from flask_login import current_user
from flask_wtf import FlaskForm
from weko_admin.api import validate_csrf_header
from invenio_db import db
from invenio_files_rest.models import FileInstance
from invenio_i18n.ext import current_i18n
from weko_admin.api import TempDirInfo
from weko_admin.utils import get_redis_cache, reset_redis_cache
from weko_index_tree.api import Indexes
from weko_index_tree.models import IndexStyle
from weko_index_tree.utils import (
    get_doi_items_in_index,
    get_editing_items_in_index,
    is_index_locked,
)
from weko_logging.activity_logger import UserActivityLogger
from weko_records.api import ItemTypes, JsonldMapping
from weko_workflow.api import WorkFlow
from weko_records_ui.external import call_external_system
from weko_deposit.api import WekoRecord

from weko_search_ui.api import get_search_detail_keyword

from .config import (
    WEKO_EXPORT_TEMPLATE_BASIC_ID,
    WEKO_EXPORT_TEMPLATE_BASIC_NAME,
    WEKO_EXPORT_TEMPLATE_BASIC_OPTION,
    WEKO_IMPORT_CHECK_LIST_NAME,
    WEKO_IMPORT_LIST_NAME,
    WEKO_ITEM_ADMIN_IMPORT_TEMPLATE,
    WEKO_ITEM_ADMIN_ROCRATE_IMPORT_TEMPLATE,
    WEKO_SEARCH_UI_ADMIN_EXPORT_TEMPLATE,
    WEKO_SEARCH_UI_BULK_EXPORT_FILE_CREATE_RUN_MSG,
)
from .tasks import (
    check_celery_is_run,
    check_session_lifetime,
    check_import_items_task,
    check_rocrate_import_items_task,
    export_all_task,
    import_item,
    is_import_running,
    remove_temp_dir_task,
)
from .utils import (
    cancel_export_all,
    check_sub_item_is_system,
    create_flow_define,
    delete_records,
    get_change_identifier_mode_content,
    get_content_workflow,
    get_export_status,
    get_lifetime,
    get_root_item_option,
    get_sub_item_option,
    get_tree_items,
    handle_metadata_by_doi,
    handle_get_all_sub_id_and_name,
    handle_workflow,
    make_stats_file,
    make_file_by_line,
)

_signals = Namespace()
searched = _signals.signal("searched")


class ItemManagementBulkDelete(BaseView):
    """Item Management - Bulk Delete view."""

    @expose("/", methods=["GET", "PUT"])
    def index(self):
        """Bulk delete items and index trees."""
        if request.method == "PUT":
            # Do delete items inside the current index tree (maybe root tree)
            q = request.values.get("q")
            UserActivityLogger.issue_log_group_id(db.session)
            if q is not None and q.isdigit():
                current_tree = Indexes.get_index(q)
                recursive_tree = Indexes.get_recursive_tree(q)
                recursively = request.values.get("recursively") == "true"

                msg = "Invalid tree"
                if current_tree:
                    try:
                        doi_items = get_doi_items_in_index(q, recursively)
                        edt_items = get_editing_items_in_index(q, recursively)
                        ignore_items = list(set(doi_items + edt_items))
                        # Delete items in current_tree
                        delete_record_list = delete_records(current_tree.id, ignore_items)

                        # If recursively, then delete items of child indices
                        if recursively:
                            # Delete recursively
                            direct_child_trees = []
                            for obj in recursive_tree:
                                if obj[1] != current_tree.id:
                                    child_tree = Indexes.get_index(obj[1])

                                    # Do delete items in child_tree
                                    child_delete_record_list = delete_records(child_tree.id, ignore_items)
                                    delete_record_list.extend(child_delete_record_list)
                                    # Add the level 1 child into the current_tree
                                    if obj[0] == current_tree.id:
                                        direct_child_trees.append(child_tree.id)

                        db.session.commit()
                        UserActivityLogger.info(operation="ITEM_BULK_DELETE")
                        for pid in delete_record_list:
                            UserActivityLogger.info(
                                operation="ITEM_DELETE",
                                target_key=pid
                            )

                        for recid in delete_record_list:
                            record = WekoRecord.get_record_by_pid(recid)
                            call_external_system(old_record=record)
                        if ignore_items:
                            msg = "{}<br/>".format(
                                _("The following item(s) cannot be deleted.")
                            )
                            if doi_items:
                                _item_d = ["recid: {}".format(i) for i in doi_items]
                                msg += "<br/>{}<br/>&nbsp;{}".format(
                                    _("DOI granting item(s):"), (", ").join(_item_d)
                                )
                            if edt_items:
                                _item_e = ["recid: {}".format(i) for i in edt_items]
                                msg += "<br/>{}<br/>&nbsp;{}".format(
                                    _("Editing item(s):"), (", ").join(_item_e)
                                )
                            return jsonify({"status": 1, "msg": msg})
                        return jsonify({"status": 1, "msg": _("Success")})
                    except Exception as e:
                        db.session.rollback()
                        current_app.logger.error(e)
                        exec_info = sys.exc_info()
                        tb_info = traceback.format_tb(exec_info[2])
                        UserActivityLogger.error(
                            operation="ITEM_BULK_DELETE",
                            remarks=tb_info[0]
                        )
                        msg = str(e)

            return jsonify({"status": 0, "msg": msg})

        """Render view."""
        detail_condition = get_search_detail_keyword("")
        return self.render(
            current_app.config["WEKO_THEME_ADMIN_ITEM_MANAGEMENT_TEMPLATE"],
            management_type="delete",
            detail_condition=detail_condition,
        )

    @expose("/check", methods=["GET"])
    def check(self):
        """Get list."""
        q = request.values.get("q")
        status = 0
        msg = None
        recursively = request.values.get("recursively") == "true"

        if q and q.isdigit() and Indexes.get_index(q):
            if is_index_locked(q):
                status = 0
                msg = _("Index Delete is in progress on another device.")
            elif get_doi_items_in_index(q, recursively):
                status = 1
                msg = _(
                    "DOI granting item(s) are including in the "
                    "deletion items.<br/>DOI granting item(s) cannot "
                    "be deleted without withdrawing the DOI.<br/>"
                    "Do you want to continue deleting items that are "
                    "not grant DOI?"
                )
            else:
                status = 1
                msg = _("Are you sure you want to delete it?")
        else:
            status = 0
            msg = _("No such index.")

        return jsonify({"status": status, "msg": msg})


class ItemManagementCustomSort(BaseView):
    """Item Management - Custom Sort view."""

    @expose("/", methods=["GET"])
    def index(self):
        """Custom sort index."""
        return self.render(
            current_app.config["WEKO_THEME_ADMIN_ITEM_MANAGEMENT_TEMPLATE"],
            management_type="sort",
        )

    @expose("/save", methods=["POST"])
    def save_sort(self):
        """Save custom sort."""
        try:
            with db.session.begin_nested():
                data = request.get_json()
                index_id = data.get("q_id")
                sort_data = data.get("sort")

                # save data to DB
                item_sort = {}
                for sort in sort_data:
                    sd = sort.get("custom_sort", {}).get(index_id)
                    if sd:
                        item_sort[sort.get("id")] = sd

                result = Indexes.set_item_sort_custom(index_id, item_sort)

            # update es
            # fp = Indexes.get_self_path(index_id)
            # Indexes.update_item_sort_custom_es(fp.path, sort_data)

            if result:
                jfy = {"status": 200, "message": "Data is successfully updated."}
                db.session.commit()
            else:
                jfy = {"status": 405, "message": "Data update failed."}
        except Exception as ex:
            jfy = {"status": 405, "message": "Error."}
            current_app.logger.error(ex)
            db.session.rollback()
        return make_response(jsonify(jfy), jfy["status"])


class ItemManagementBulkSearch(BaseView):
    """Item Management - Search."""

    @expose("/", methods=["GET"])
    def index(self):
        """Index Search page ui."""
        search_type = request.args.get("search_type", "0")
        get_args = request.args
        community_id = ""
        ctx = {"community": None}
        cur_index_id = (
            search_type
            if search_type
            not in (
                "0",
                "1",
            )
            else None
        )
        if "community" in get_args:
            from weko_workflow.api import GetCommunity

            comm = GetCommunity.get_community_by_id(request.args.get("community"))
            ctx = {"community": comm}
            if comm is not None:
                community_id = comm.id

        # Get index style
        style = IndexStyle.get(
            current_app.config["WEKO_INDEX_TREE_STYLE_OPTIONS"]["id"]
        )
        width = style.width if style else "3"

        detail_condition = get_search_detail_keyword("")

        height = style.height if style else None
        header = ""
        if "item_management" in get_args:
            management_type = request.args.get("item_management", "sort")
            has_items = False
            has_child_trees = False
            header = _("Custom Sort")
            if management_type == "delete":
                header = _("Bulk Delete")
                # Does this tree has items or children?
                q = request.args.get("q")
                if q is not None and q.isdigit():
                    current_tree = Indexes.get_index(q)
                    recursive_tree = Indexes.get_recursive_tree(q)

                    if current_tree is not None:
                        tree_items = get_tree_items(current_tree.id, 1)
                        has_items = len(tree_items) > 0
                        if recursive_tree is not None:
                            has_child_trees = len(recursive_tree) > 1
            elif management_type == "update":
                header = _("Bulk Update")

            return self.render(
                current_app.config["WEKO_THEME_ADMIN_ITEM_MANAGEMENT_TEMPLATE"],
                index_id=cur_index_id,
                community_id=community_id,
                width=width,
                height=height,
                header=header,
                management_type=management_type,
                fields=current_app.config["WEKO_RECORDS_UI_BULK_UPDATE_FIELDS"][
                    "fields"
                ],
                licences=current_app.config["WEKO_RECORDS_UI_LICENSE_DICT"],
                has_items=has_items,
                has_child_trees=has_child_trees,
                detail_condition=detail_condition,
                **ctx
            )
        else:
            return abort(500)

    @staticmethod
    def is_visible():
        """Should never be visible."""
        return False


class ItemImportView(BaseView):
    """BaseView for Admin Import."""

    @expose("/", methods=["GET"])
    def index(self):
        """Renders an item import view.

        :param
        :return: The rendered template.
        """
        workflow = WorkFlow()
        workflows = workflow.get_workflow_list()
        workflows_js = [get_content_workflow(item) for item in workflows]

        form =FlaskForm(request.form)

        return self.render(
            WEKO_ITEM_ADMIN_IMPORT_TEMPLATE,
            workflows=json.dumps(workflows_js),
            file_format=current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower(),
            form=form
        )

    @expose("/check", methods=["POST"])
    def check(self) -> jsonify:
        """Validate item import."""

        validate_csrf_header(request)

        data = request.form
        file = request.files["file"] if request.files else None

        role_ids = []
        can_edit_indexes = []
        if current_user and current_user.is_authenticated:
            for role in current_user.roles:
                if role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']:
                    role_ids = []
                    can_edit_indexes = [0]
                    break
                else:
                    role_ids.append(role.id)
        if role_ids:
            from invenio_communities.models import Community
            comm_data = Community.query.filter(
                Community.id_role.in_(role_ids)
            ).all()
            for comm in comm_data:
                can_edit_indexes += [i.cid for i in Indexes.get_self_list(comm.root_node_id)]
            can_edit_indexes = list(set(can_edit_indexes))
        if data and file:
            temp_path = (
                tempfile.gettempdir()
                + "/"
                + current_app.config["WEKO_SEARCH_UI_IMPORT_TMP_PREFIX"]
                + datetime.utcnow().strftime(r"%Y%m%d%H%M%S%f")
            )
            os.mkdir(temp_path)
            file_path = temp_path + "/" + file.filename
            file.save(file_path)
            task = check_import_items_task.apply_async(
                (
                    file_path,
                    data.get("is_change_identifier") == "true",
                    request.host_url,
                    current_i18n.language,
                    False,
                    can_edit_indexes
                ),
            )
        return jsonify(code=1, check_import_task_id=task.task_id)

    @expose("/get_check_status", methods=["POST"])
    def get_check_status(self) -> jsonify:
        """Validate item import."""
        data = request.get_json()
        result = {}

        if data and data.get("task_id"):
            task = import_item.AsyncResult(data.get("task_id"))
            if task and isinstance(task.result, dict):
                start_date = task.result.get("start_date")
                end_date = task.result.get("end_date")
                result.update(
                    {"start_date": start_date, "end_date": end_date, **task.result}
                )
            elif task and task.status != "PENDING":
                result["error"] = _("Internal server error")
        return jsonify(**result)

    @expose("/download_check", methods=["POST"])
    def download_check(self):
        """Download report check result."""
        data = request.get_json()
        now = str(datetime.date(datetime.now()))
        file_format = current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()

        file_name = "check_{}.{}".format(now, file_format)
        if data:
            output_file = make_stats_file(
                data.get("list_result"), WEKO_IMPORT_CHECK_LIST_NAME
            )
            return Response(
                output_file.getvalue(),
                mimetype="text/{}".format(file_format),
                headers={"Content-disposition": "attachment; filename=" + file_name},
            )
        else:
            return Response(
                [],
                mimetype="text/{}".format(file_format),
                headers={"Content-disposition": "attachment; filename=" + file_name},
            )

    @expose("/import", methods=["POST"])
    def import_items(self) -> jsonify:
        """Import item into System."""
        data = request.get_json() or {}
        data_path = data.get("data_path")
        user_id = current_user.get_id() if current_user else -1
        request_info = {
            "remote_addr": request.remote_addr,
            "referrer": request.referrer,
            "hostname": request.host,
            "user_id": user_id,
            "action": "IMPORT"
        }
        request_info.update(
            UserActivityLogger.get_summary_from_request()
        )
        # update temp dir expire to 1 day from now
        expire = datetime.now() + timedelta(days=1)
        TempDirInfo().set(data_path, {"expire": expire.strftime("%Y-%m-%d %H:%M:%S")})

        tasks = []
        list_record = [
            item for item in data.get("list_record", []) if not item.get("errors")
        ]
        list_doi = data.get("list_doi")
        if UserActivityLogger.issue_log_group_id(db.session):
            log_group_id = UserActivityLogger.get_log_group_id(request_info)
            request_info["log_group_id"] = log_group_id
        UserActivityLogger.info(operation="ITEM_IMPORT")
        if list_record:
            group_tasks = []
            UserActivityLogger.info(operation="ITEM_BULK_CREATE")
            for idx, item in enumerate(list_record):
                try:
                    item["root_path"] = data_path + "/data"
                    create_flow_define()
                    handle_workflow(item)
                    if (list_doi[idx]):
                        metadata_doi = handle_metadata_by_doi(item, list_doi[idx])
                        item["metadata"] = metadata_doi
                    group_tasks.append(import_item.s(item, request_info))
                    db.session.commit()
                except Exception as ex:
                    db.session.rollback()
                    current_app.logger.error("Failed to Item import.")
                    exec_info = sys.exc_info()
                    tb_info = traceback.format_tb(exec_info[2])
                    UserActivityLogger.error(
                        operation="ITEM_BULK_CREATE",
                        remarks=tb_info[0]
                    )

            # handle import tasks
            import_task = chord(group_tasks)(remove_temp_dir_task.si(data_path))
            for idx, task in enumerate(import_task.parent.results):
                tasks.append(
                    {
                        "task_id": task.task_id,
                        "item_id": list_record[idx].get("id"),
                    }
                )

        response_object = {
            "status": "success",
            "data": {"tasks": tasks},
        }
        return jsonify(response_object)

    @expose("/check_status", methods=["POST"])
    def get_status(self):
        """Get status of import process."""
        data = request.get_json()
        result = []
        if data and data.get("tasks"):
            status = "done"
            for task_item in data.get("tasks"):
                task_id = task_item.get("task_id")
                task = import_item.AsyncResult(task_id)
                start_date = (
                    task.result.get("start_date")
                    if task and isinstance(task.result, dict)
                    else ""
                )
                end_date = (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if task.successful() or task.failed()
                    else ""
                )
                item_id = task_item.get("item_id", None)
                if not item_id and task.result:
                    item_id = task.result.get("recid", None)
                result.append({
                    "task_status": task.status,
                    "task_result": task.result,
                    "start_date": start_date,
                    "end_date": task_item.get("end_date") or end_date,
                    "task_id": task_id,
                    "item_id": item_id,
                })
                status = (
                    "doing"
                    if not (task.successful() or task.failed()) or status == "doing"
                    else "done"
                )
            response_object = {"status": status, "result": result}
        else:
            response_object = {"status": "error", "result": result}
        return jsonify(response_object)

    @expose("/export_import", methods=["POST"])
    def download_import(self):
        """Download import result."""
        data = request.get_json()
        now = str(datetime.date(datetime.now()))

        file_format = current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()
        file_name = "List_Download {}.{}".format(now, file_format)
        if data:
            output_file = make_stats_file(
                data.get("list_result"),
                list(map(lambda x: str(x) , WEKO_IMPORT_LIST_NAME))
            )
            return Response(
                output_file.getvalue(),
                mimetype="text/{}".format(file_format),
                headers={"Content-disposition": "attachment; filename=" + file_name},
            )
        else:
            return Response(
                [],
                mimetype="text/{}".format(file_format),
                headers={"Content-disposition": "attachment; filename=" + file_name},
            )

    @expose("/get_disclaimer_text", methods=["GET"])
    def get_disclaimer_text(self):
        """Get disclaimer text."""
        data = get_change_identifier_mode_content()
        return jsonify(code=1, data=data)

    @expose("/export_template", methods=["POST"])
    def export_template(self):
        """Download item type template."""
        file_format = current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()
        file_name = None
        output_file = None
        data = request.get_json()
        if data:
            item_type_id = int(data.get("item_type_id", 0))
            if item_type_id > 0:
                item_type = ItemTypes.get_by_id(id_=item_type_id, with_deleted=True)
                if item_type:
                    file_name = "{}({}).{}".format(
                        item_type.item_type_name.name, item_type.id, file_format
                    )
                    item_type_line = [
                        "#ItemType",
                        "{}({})".format(item_type.item_type_name.name, item_type.id),
                        "{}items/jsonschema/{}".format(request.url_root, item_type.id),
                    ]
                    ids_line = pickle.loads(pickle.dumps(WEKO_EXPORT_TEMPLATE_BASIC_ID, -1))
                    names_line = pickle.loads(pickle.dumps(WEKO_EXPORT_TEMPLATE_BASIC_NAME, -1))
                    systems_line = ["#"] + ["" for _ in range(len(ids_line) - 1)]
                    options_line = pickle.loads(pickle.dumps(WEKO_EXPORT_TEMPLATE_BASIC_OPTION, -1))

                    item_type = item_type.render
                    meta_list = {
                        **item_type.get("meta_fix", {}),
                        **item_type.get("meta_list", {}),
                    }
                    meta_system = [key for key in item_type.get("meta_system", {})]
                    schema = (
                        item_type.get("table_row_map", {})
                        .get("schema", {})
                        .get("properties", {})
                    )
                    form = item_type.get("table_row_map", {}).get("form", [])

                    count_file = 0
                    count_thumbnail = 0
                    for key in ["pubdate", *item_type.get("table_row", [])]:
                        if key in meta_system:
                            continue

                        item = schema.get(key)
                        item_option = meta_list.get(key) if meta_list.get(key) else item
                        sub_form = next(
                            (x for x in form if key == x.get("key")), {"title_i18n": {}}
                        )
                        root_id, root_name, root_option = get_root_item_option(
                            key, item_option, sub_form
                        )
                        # have not sub item
                        if not (item.get("properties") or item.get("items")):
                            ids_line.append(root_id)
                            names_line.append(root_name)
                            systems_line.append("")
                            options_line.append(", ".join(root_option))
                        else:
                            # have sub item
                            sub_items = (
                                item.get("properties")
                                if item.get("properties")
                                else item.get("items").get("properties")
                            )
                            _ids, _names = handle_get_all_sub_id_and_name(
                                sub_items, root_id, root_name, sub_form.get("items", [])
                            )
                            _options = []
                            for _id in _ids:
                                if "filename" in _id:
                                    ids_line.append(".file_path[{}]".format(count_file))
                                    file_path_name = (
                                        "File Path"
                                        if current_i18n.language == "en"
                                        else "ファイルパス"
                                    )
                                    names_line.append(
                                        ".{}[{}]".format(file_path_name, count_file)
                                    )
                                    systems_line.append("")
                                    options_line.append("Allow Multiple")
                                    count_file += 1
                                if "thumbnail_label" in _id:
                                    thumbnail_path_name = (
                                        "Thumbnail Path"
                                        if current_i18n.language == "en"
                                        else "サムネイルパス"
                                    )
                                    if item.get("items"):
                                        ids_line.append(
                                            ".thumbnail_path[{}]".format(
                                                count_thumbnail
                                            )
                                        )
                                        names_line.append(
                                            ".{}[{}]".format(
                                                thumbnail_path_name, count_thumbnail
                                            )
                                        )
                                        options_line.append("Allow Multiple")
                                        count_thumbnail += 1
                                    else:
                                        ids_line.append(".thumbnail_path")
                                        names_line.append(
                                            ".{}".format(thumbnail_path_name)
                                        )
                                        options_line.append("")
                                    systems_line.append("")

                                clean_key = _id.replace(".metadata.", "").replace(
                                    "[0]", "[]"
                                )
                                _options.append(
                                    get_sub_item_option(clean_key, form) or []
                                )
                                systems_line.append(
                                    "System"
                                    if check_sub_item_is_system(clean_key, form)
                                    else ""
                                )

                            ids_line += _ids
                            names_line += _names
                            for _option in _options:
                                options_line.append(
                                    ", ".join(list(set(root_option + _option)))
                                )
                    output_file = make_file_by_line(
                        [
                            item_type_line,
                            ids_line,
                            names_line,
                            systems_line,
                            options_line,
                        ]
                    )
        return Response(
            []
            if not output_file
            else codecs.BOM_UTF8.decode("utf8")
            + codecs.BOM_UTF8.decode()
            + output_file.getvalue(),
            mimetype="text/{}".format(file_format),
            headers={
                "Content-type": "text/{}; charset=utf-8".format(file_format),
                "Content-disposition": "attachment; "
                + (
                    "filename=" if not file_name else urlencode({"filename": file_name})
                ),
            },
        )

    @expose("/check_import_is_available", methods=["GET"])
    def check_import_available(self):
        check = is_import_running()
        if check:
            return jsonify(
                {
                    "is_available": False,
                    "error_id": check,
                }
            )

        else:
            return jsonify({"is_available": True})


class ItemRocrateImportView(BaseView):
    """BaseView for Admin RO-Crate Import."""

    @expose("/", methods=["GET"])
    def index(self):
        """Renders an item rocrate import view.

        :return: The rendered template.
        """
        workflow = WorkFlow()
        workflows = workflow.get_workflow_list()
        workflows_js = [get_content_workflow(item) for item in workflows]

        form = FlaskForm(request.form)

        return self.render(
            WEKO_ITEM_ADMIN_ROCRATE_IMPORT_TEMPLATE,
            workflows=json.dumps(workflows_js),
            file_format=current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'json').lower(),
            form=form
        )

    @expose("/check", methods=["POST"])
    def check(self):
        """Validate item import.

        :return: The result of the validation.
        """

        validate_csrf_header(request)

        data = request.form
        file = request.files["file"] if request.files else None
        packaging = request.headers.get("Packaging")
        mapping_id = data.get("mapping_id")

        role_ids = []
        can_edit_indexes = []
        if current_user and current_user.is_authenticated:
            for role in current_user.roles:
                if role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']:
                    role_ids = []
                    can_edit_indexes = [0]
                    break
                else:
                    role_ids.append(role.id)
        if role_ids:
            from invenio_communities.models import Community
            comm_data = Community.query.filter(
                Community.id_role.in_(role_ids)
            ).all()
            for comm in comm_data:
                can_edit_indexes += [i.cid for i in Indexes.get_self_list(comm.root_node_id)]
            can_edit_indexes = list(set(can_edit_indexes))
        if data and file:
            temp_path = os.path.join(
                tempfile.gettempdir(),
                current_app.config["WEKO_SEARCH_UI_ROCRATE_IMPORT_TMP_PREFIX"]
                    + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:-3]
            )
            os.mkdir(temp_path)
            file_path = os.path.join(temp_path, file.filename)
            file.save(file_path)
            task = check_rocrate_import_items_task.apply_async(
                (
                    file_path,
                    data.get("is_change_identifier") == "true",
                    request.host_url,
                    packaging,
                    mapping_id,
                    current_i18n.language,
                    can_edit_indexes
                ),
            )
            return jsonify(code=1, check_rocrate_import_task_id=task.task_id)
        else:
            return make_response(jsonify({"error": "No file or data provided."}), 400)

    @expose("/get_check_status", methods=["POST"])
    def get_check_status(self) -> jsonify:
        """Validate item import.

        :return: check status.
        """
        data = request.get_json()
        result = {}

        if data and data.get("task_id"):
            task = import_item.AsyncResult(data.get("task_id"))
            if task and isinstance(task.result, dict):
                start_date = task.result.get("start_date")
                end_date = task.result.get("end_date")
                result.update(
                    {"start_date": start_date, "end_date": end_date, **task.result}
                )
            elif task and task.status != "PENDING":
                current_app.logger.error(f"Task {task.id} failed")
                result["error"] = _("Internal server error")
        return jsonify(**result)

    @expose("/download_check", methods=["POST"])
    def download_check(self):
        """Download report check result.

        :return: The response of the download.
        """
        data = request.get_json()
        now = datetime.now().strftime("%Y-%m-%d")
        file_format = current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()

        file_name = "check_{}.{}".format(now, file_format)
        if data:
            output_file = make_stats_file(
                data.get("list_result"), WEKO_IMPORT_CHECK_LIST_NAME
            )
            return Response(
                output_file.getvalue(),
                mimetype="text/{}".format(file_format),
                headers={"Content-disposition": "attachment; filename=" + file_name},
            )
        else:
            return Response(
                [],
                mimetype="text/{}".format(file_format),
                headers={"Content-disposition": "attachment; filename=" + file_name},
            )

    @expose("/import", methods=["POST"])
    def import_items(self):
        """Import item into System.

        :return: The response of the import.
        """
        data = request.get_json() or {}
        data_path = data.get("data_path")
        user_id = current_user.get_id() if current_user else -1
        request_info = {
            "remote_addr": request.remote_addr,
            "referrer": request.referrer,
            "hostname": request.host,
            "user_id": user_id,
            "action": "IMPORT"
        }
        request_info.update(
            UserActivityLogger.get_summary_from_request()
        )
        # update temp dir expire to 1 day from now
        expire = datetime.now() + timedelta(days=1)
        TempDirInfo().set(data_path, {"expire": expire.strftime("%Y-%m-%d %H:%M:%S")})

        tasks = []
        list_record = [
            item for item in data.get("list_record", []) if not item.get("errors")
        ]
        if UserActivityLogger.issue_log_group_id(db.session):
            log_group_id = UserActivityLogger.get_log_group_id(request_info)
            request_info["log_group_id"] = log_group_id

        UserActivityLogger.info(
            operation="ITEM_IMPORT",
            remarks="RO-Crate Import"
        )
        if list_record:
            group_tasks = []
            UserActivityLogger.info(
                operation="ITEM_BULK_CREATE",
                remarks="RO-Crate Import"
            )
            for item in list_record:
                try:
                    item["root_path"] = os.path.join(data_path, "data")
                    create_flow_define()
                    handle_workflow(item)
                    group_tasks.append(import_item.s(item, request_info))
                    db.session.commit()
                except Exception as ex:
                    db.session.rollback()
                    current_app.logger.error("Failed to item import.")
                    traceback.print_exc()
                    exec_info = sys.exc_info()
                    tb_info = traceback.format_tb(exec_info[2])
                    UserActivityLogger.error(
                        operation="ITEM_BULK_CREATE",
                        remarks=tb_info[0]
                    )

            # handle import tasks
            import_task = chord(group_tasks)(remove_temp_dir_task.si(data_path))
            for idx, task in enumerate(import_task.parent.results):
                tasks.append(
                    {
                        "task_id": task.task_id,
                        "item_id": list_record[idx].get("id"),
                    }
                )

        response_object = {
            "status": "success",
            "data": {"tasks": tasks},
        }
        return jsonify(response_object)

    @expose("/check_status", methods=["POST"])
    def get_status(self):
        """Get status of import process.

        :return: check status.
        """
        data = request.get_json()
        result = []
        if data and data.get("tasks"):
            status = "done"
            for task_item in data.get("tasks"):
                task_id = task_item.get("task_id")
                task = import_item.AsyncResult(task_id)
                start_date = (
                    task.result.get("start_date")
                    if task and isinstance(task.result, dict)
                    else ""
                )
                end_date = (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if task.successful() or task.failed()
                    else ""
                )
                item_id = task_item.get("item_id", None)
                if not item_id and task.result:
                    item_id = task.result.get("recid", None)
                result.append({
                    "task_status": task.status,
                    "task_result": task.result,
                    "start_date": start_date,
                    "end_date": task_item.get("end_date") or end_date,
                    "task_id": task_id,
                    "item_id": item_id,
                })
                status = (
                    "doing"
                    if not (task.successful() or task.failed()) or status == "doing"
                    else "done"
                )
            response_object = {"status": status, "result": result}
        else:
            response_object = {"status": "error", "result": result}
        return jsonify(response_object)

    @expose("/export_import", methods=["POST"])
    def download_import(self):
        """Download import result.

        :return: The response of the download.
        """
        data = request.get_json()
        now = datetime.now().strftime("%Y-%m-%d")

        file_format = current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()
        file_name = "List_Download {}.{}".format(now, file_format)
        if data:
            output_file = make_stats_file(
                data.get("list_result"),
                list(map(lambda x: str(x) , WEKO_IMPORT_LIST_NAME))
            )
            return Response(
                output_file.getvalue(),
                mimetype="text/{}".format(file_format),
                headers={"Content-disposition": "attachment; filename=" + file_name},
            )
        else:
            return Response(
                [],
                mimetype="text/{}".format(file_format),
                headers={"Content-disposition": "attachment; filename=" + file_name},
            )

    @expose("/get_disclaimer_text", methods=["GET"])
    def get_disclaimer_text(self):
        """Get disclaimer text.

        :return: The disclaimer text.
        """
        data = get_change_identifier_mode_content()
        return jsonify(code=1, data=data)

    @expose("/check_import_is_available", methods=["GET"])
    def check_import_available(self):
        """Check import is available.

        :return: check result.
        """
        check = is_import_running()
        if check:
            return jsonify(
                {
                    "is_available": False,
                    "error_id": check,
                }
            )
        else:
            return jsonify({"is_available": True})

    @expose("/all_mappings", methods=["GET"])
    def all_mappings(self):
        """Get all ItemTypeJsonldMapping as JSON.

        Returns:
            flask.Response: JSON list of dicts with id, name, item_type_id,
            retrieved from ItemTypeJsonldMapping records that are not deleted.
        """
        mappings = [
            {
                "id": item.id,
                "name": item.name,
                "item_type_id": item.item_type_id
            }
            for item in JsonldMapping.get_all()
        ]
        return jsonify(mappings)


class ItemBulkExport(BaseView):
    """BaseView for Admin Export."""

    @expose("/", methods=["GET"])
    def index(self):
        """Renders admin bulk export page.

        :param
        :return: The rendered template.
        """
        _cache_prefix = current_app.config["WEKO_ADMIN_CACHE_PREFIX"]
        _msg_config = current_app.config["WEKO_SEARCH_UI_BULK_EXPORT_MSG"]
        _msg_key = _cache_prefix.format(
            name=_msg_config,
            user_id=current_user.get_id()
        )
        reset_redis_cache(_msg_key, "")
        return self.render(WEKO_SEARCH_UI_ADMIN_EXPORT_TEMPLATE)

    @expose("/export_all", methods=["POST"])
    def export_all(self):
        """Export all items."""
        data = request.get_json()
        user_id = current_user.get_id()
        _task_config = current_app.config["WEKO_SEARCH_UI_BULK_EXPORT_TASK"]
        _cache_key = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name=_task_config,
            user_id=user_id
        )
        export_status, download_uri, message, run_message, \
            _, _, _ = get_export_status()
        start_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

        if not export_status:
            export_task = export_all_task.apply_async(
                args=(request.url_root, user_id, data, start_time)
            )
            reset_redis_cache(_cache_key, str(export_task.task_id))

        # return Response(status=200)
        check_celery = check_celery_is_run()
        check_life_time = check_session_lifetime()
        export_status, download_uri, message, run_message, \
            status, start_time, finish_time = get_export_status()
        return jsonify(
            data={
                "export_status": export_status,
                "uri_status": True if download_uri else False,
                "celery_is_run": check_celery,
                "is_lifetime": check_life_time,
                "error_message": message,
                "export_run_msg": run_message,
                "status": status,
                "start_time": start_time,
                "finish_time": finish_time
            }
        )

    @expose("/check_export_status", methods=["GET"])
    def check_export_status(self):
        """Check export status."""
        check_celery = check_celery_is_run()
        check_life_time = check_session_lifetime()
        export_status, download_uri, message, run_message, \
            status, start_time, finish_time = get_export_status()
        return jsonify(
            data={
                "export_status": export_status,
                "uri_status": True if download_uri else False,
                "celery_is_run": check_celery,
                "is_lifetime": check_life_time,
                "error_message": message,
                "export_run_msg": run_message,
                "status": status,
                "start_time": start_time,
                "finish_time": finish_time
            }
        )

    @expose("/cancel_export", methods=["GET"])
    def cancel_export(self):
        """Check export status."""
        result = cancel_export_all()
        export_status, _, _, _, status, _, _ = get_export_status()
        return jsonify(data={"cancel_status": result, "export_status":export_status, "status":status})

    @expose("/download", methods=["GET"])
    def download(self):
        """Funtion send file to Client.

        Sends the exported file to the client for download.
        Checks the download URI and file expiration, and if the conditions are met,
        returns the file as an attachment. If the file is not available for download,
        returns status 200.
        """
        file_msg = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name=WEKO_SEARCH_UI_BULK_EXPORT_FILE_CREATE_RUN_MSG,
            user_id=current_user.get_id()
        )
        export_info = json.loads(get_redis_cache(file_msg))
        export_path = export_info["export_path"]
        export_status, download_uri, _, _, \
            _, _, _ = get_export_status()
        if not export_status and download_uri is not None:
            file_instance = FileInstance.get_by_uri(download_uri)

            # Check the TTL in the cache and extend it
            # if the remaining time is below a certain threshold.
            tmp_cache = TempDirInfo().get(export_path)
            expire = tmp_cache.get("expire") if tmp_cache else None
            now = datetime.now()
            if (
                expire and
                (datetime.strptime(expire,"%Y-%m-%d %H:%M:%S") - now).total_seconds()
                    <= current_app.config["WEKO_SEARCH_UI_FILE_DOWNLOAD_TTL_BUFFER"]
            ):
                expire = datetime.strptime(expire,"%Y-%m-%d %H:%M:%S")
                new_expire = (
                    expire + timedelta(
                        seconds=current_app.config["WEKO_SEARCH_UI_FILE_DOWNLOAD_TTL_BUFFER"]
                    )
                )
                tmp_cache["expire"] = new_expire.strftime("%Y-%m-%d %H:%M:%S")
                TempDirInfo().set(export_path, tmp_cache)
            return file_instance.send_file(
                "export-all.zip",
                mimetype="application/octet-stream",
                as_attachment=True,
            )
        else:
            return Response(status=200)


item_management_bulk_search_adminview = {
    "view_class": ItemManagementBulkSearch,
    "kwargs": {
        "endpoint": "items/search",
        "category": _("Index Tree"),
        "name": "",
    },
}

item_management_bulk_delete_adminview = {
    "view_class": ItemManagementBulkDelete,
    "kwargs": {
        "category": _("Items"),
        "name": _("Bulk Delete"),
        "endpoint": "items/bulk/delete",
    },
}

item_management_custom_sort_adminview = {
    "view_class": ItemManagementCustomSort,
    "kwargs": {
        "category": _("Index Tree"),
        "name": _("Custom Sort"),
        "endpoint": "items/custom_sort",
    },
}

item_management_import_adminview = {
    "view_class": ItemImportView,
    "kwargs": {
        "category": _("Items"),
        "name": _("Import"),
        "endpoint": "items/import",
    },
}

item_management_rocrate_import_adminview = {
    "view_class": ItemRocrateImportView,
    "kwargs": {
        "category": _("Items"),
        "name": _("RO-Crate Import"),
        "endpoint": "items/rocrate_import",
    },

}

item_management_export_adminview = {
    "view_class": ItemBulkExport,
    "kwargs": {
        "category": _("Items"),
        "name": _("Bulk Export"),
        "endpoint": "items/bulk-export",
    },
}

__all__ = (
    "item_management_bulk_delete_adminview",
    "item_management_bulk_search_adminview",
    "item_management_custom_sort_adminview",
    "item_management_import_adminview",
    "item_management_rocrate_import_adminview",
    "item_management_export_adminview",
)
