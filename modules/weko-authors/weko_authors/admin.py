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

"""Weko Authors admin."""

from __future__ import absolute_import, print_function

import os
import json, tempfile, datetime, base64
from celery import group, states
from celery.task.control import revoke
from flask import abort, current_app, request, session, send_file
from flask.helpers import url_for
from flask.json import jsonify
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from invenio_files_rest.models import FileInstance
from invenio_cache import current_cache
from weko_workflow.utils import update_cache_data

from .config import WEKO_AUTHORS_EXPORT_FILE_NAME, \
    WEKO_AUTHORS_IMPORT_CACHE_KEY
from .permissions import author_permission
from .tasks import check_is_import_available, export_all, import_author, import_author_over_max
from .utils import check_import_data, delete_export_status, \
    get_export_status, get_export_url, set_export_status, delete_export_url,\
     band_check_file_for_user, prepare_import_data, create_result_file_for_user


class AuthorManagementView(BaseView):
    """Weko authors admin view."""

    @author_permission.require(http_exception=403)
    @expose('/', methods=['GET'])
    def index(self):
        """Render author list view."""
        tab_value = request.args.get('tab', 'author')
        template = current_app.config['WEKO_AUTHORS_ADMIN_LIST_TEMPLATE']
        if tab_value == 'prefix':
            template = \
                current_app.config['WEKO_AUTHORS_ADMIN_PREFIX_TEMPLATE']
        if tab_value == 'affiliation':
            template = \
                current_app.config['WEKO_AUTHORS_ADMIN_AFFILIATION_TEMPLATE']
        return self.render(
            template,
            render_widgets=False,  # Moved to admin, no need for widgets
            lang_code=session.get(
                'selected_language',
                'en')  # Set default lang
        )

    @author_permission.require(http_exception=403)
    @expose('/add', methods=['GET'])
    def add(self):
        """Render author edit view."""
        return self.render(
            current_app.config['WEKO_AUTHORS_ADMIN_EDIT_TEMPLATE'],
            identifier_reg=json.dumps(current_app.config['WEKO_AUTHORS_IDENTIFIER_REG']),
            render_widgets=False,  # Moved to admin, no need for widgets
            lang_code=session.get(
                'selected_language',
                'en'),  # Set default lang
        )

    @author_permission.require(http_exception=403)
    @expose('/edit', methods=['GET'])
    def edit(self):
        """Render an adding author view."""
        return self.render(
            current_app.config['WEKO_AUTHORS_ADMIN_EDIT_TEMPLATE'],
            identifier_reg=json.dumps(current_app.config['WEKO_AUTHORS_IDENTIFIER_REG']),
            render_widgets=False,  # Moved to admin, no need for widgets
            lang_code=session.get('selected_language', 'en')  # Set default
        )


class ExportView(BaseView):
    """Weko export authors admin view."""

    @author_permission.require(http_exception=403)
    @expose('/', methods=['GET'])
    def index(self):
        """Render export authors view."""
        return self.render(
            current_app.config['WEKO_AUTHORS_ADMIN_EXPORT_TEMPLATE']
        )

    @author_permission.require(http_exception=403)
    @expose('/download/' + WEKO_AUTHORS_EXPORT_FILE_NAME, methods=['GET'])
    def download(self):
        """Download the export file."""
        data = get_export_url()
        if data.get('file_uri'):
            file_instance = FileInstance.get_by_uri(data.get('file_uri'))
            file_name = "{}_{}.{}".format(
                WEKO_AUTHORS_EXPORT_FILE_NAME,
                file_instance.updated.strftime("%Y%m%d%H%M"),
                current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()
            )
            return file_instance.send_file(
                file_name,
                mimetype='application/octet-stream',
                as_attachment=True
            )
        else:
            abort(404)

    @author_permission.require(http_exception=403)
    @expose('/check_status', methods=['GET'])
    def check_status(self):
        """Api check export status."""
        
        # stop_pointを確認
        stop_point= current_cache.get(current_app.config["WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY"])
        
        status = get_export_status()
        if not status:
            status = get_export_url()
        elif status.get('task_id'):
            task = export_all.AsyncResult(status.get('task_id'))
            if task.successful() or task.failed() \
                    or task.state == states.REVOKED:
                delete_export_status()
                status = get_export_url()
                if not task.result and not stop_point:
                    status['error'] = 'export_fail'
            else:
                status['file_uri'] = get_export_url().get('file_uri', '')

        if stop_point:
            status['stop_point'] = stop_point
        # set download_link
        status['download_link'] = url_for(
            'authors/export.download', _external=True)
        status['filename'] = ''
        file_instance = FileInstance.get_by_uri(status.get('file_uri', ''))
        if file_instance:
            status['filename'] = "{}_{}.{}".format(
                WEKO_AUTHORS_EXPORT_FILE_NAME,
                file_instance.updated.strftime("%Y%m%d%H%M"),
                current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()
            )
        if not status.get('file_uri'):
            status['download_link'] = ''
        if 'file_uri' in status:
            del status['file_uri']

        return jsonify({
            'code': 200,
            'data': status
        })

    @author_permission.require(http_exception=403)
    @expose('/export', methods=['POST'])
    def export(self):
        """Process export authors."""
        #実行時に以前のexport_urlを削除
        delete_export_url()
        temp_folder_path ='/var/tmp/authors_export'
        os.makedirs(temp_folder_path, exist_ok=True)
        prefix = current_app.config["WEKO_AUTHORS_EXPORT_TMP_PREFIX"] + datetime.datetime.now().strftime("%Y%m%d%H%M")
        
        with tempfile.NamedTemporaryFile(dir=temp_folder_path, prefix=prefix, suffix='.tsv', mode='w+', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        # redisに一時ファイルのパスを保存
        update_cache_data(
            current_app.config["WEKO_AUTHORS_EXPORT_CACHE_TEMP_FILE_PATH_KEY"],
            temp_file_path,
            current_app.config["WEKO_AUTHORS_IMPORT_TEMP_FILE_RETENTION_PERIOD"]
        )
        task = export_all.delay()
        set_export_status(task_id=task.id)
        return jsonify({
            'code': 200,
            'data': {'task_id': task.id}
        })

    @author_permission.require(http_exception=403)
    @expose('/cancel', methods=['POST'])
    def cancel(self):
        """Cancel export progress."""
        result = {'status': 'fail'}
        try:
            status = get_export_status()
            # stop_pointがあるならstop_pointとtemp_file_pathを削除
            if current_cache.get(current_app.config["WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY"]):
                current_cache.delete(current_app.config["WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY"])
                temp_file_path=current_cache.get(\
                    current_app.config["WEKO_AUTHORS_EXPORT_CACHE_TEMP_FILE_PATH_KEY"])
                if temp_file_path:
                    os.remove(temp_file_path)                    
                    current_cache.delete(current_app.config["WEKO_AUTHORS_EXPORT_CACHE_TEMP_FILE_PATH_KEY"])
            if status and status.get('task_id'):
                revoke(status.get('task_id'), terminate=True)
                delete_export_status()
                result['status'] = 'success'
        except Exception as ex:
            current_app.logger.error(ex)
        return jsonify({
            'code': 200,
            'data': result
        })


    # 再開用メソッド
    @author_permission.require(http_exception=403)
    @expose('/resume', methods=['POST'])
    def resume(self):
        """Resume export progress."""

        delete_export_url()
        temp_folder_path ='/var/tmp/authors_export'
        os.makedirs(temp_folder_path, exist_ok=True)
        prefix = current_app.config["WEKO_AUTHORS_EXPORT_TMP_PREFIX"] + datetime.datetime.now().strftime("%Y%m%d%H%M")
        
        with tempfile.NamedTemporaryFile(dir=temp_folder_path, prefix=prefix, suffix='.tsv', mode='w+', delete=False) as temp_file:
            temp_file_path = temp_file.name
        update_cache_data(current_app.config["WEKO_AUTHORS_EXPORT_CACHE_TEMP_FILE_PATH_KEY"],
            temp_file_path,
            current_app.config["WEKO_AUTHORS_IMPORT_TEMP_FILE_RETENTION_PERIOD"]
        )
        task = export_all.delay()
        set_export_status(task_id=task.id)
        return jsonify({
            'code': 200,
            'data': {'task_id': task.id}
        })

class ImportView(BaseView):
    """Weko import authors admin view."""

    @author_permission.require(http_exception=403)
    @expose('/', methods=['GET'])
    def index(self):
        """Render import authors view."""
        return self.render(
            current_app.config['WEKO_AUTHORS_ADMIN_IMPORT_TEMPLATE']
        )

    @expose('/is_import_available', methods=['GET'])
    def is_import_available(self):
        """Is import available."""
        group_task_id = request.args.get(
            'group_task_id', type=str, default=None)

        return jsonify(check_is_import_available(group_task_id))
    
    @author_permission.require(http_exception=403)
    @expose('/check_import_file', methods=['POST'])
    def check_import_file(self):
        """Validate author import."""
        error = None  
        list_import_data = []
        temp_folder_path = current_app.config.get("WEKO_AUTHORS_IMPORT_TEMP_FOLDER_PATH")
        os.makedirs(temp_folder_path, exist_ok=True)
        prefix = current_app.config["WEKO_AUTHORS_IMPORT_TMP_PREFIX"] + datetime.datetime.now().strftime("%Y%m%d%H%M")
        json_data = request.get_json()
        if json_data:
            file_suffix = json_data.get('file_name').split('.')[-1].lower()
            with tempfile.NamedTemporaryFile(dir=temp_folder_path, prefix=prefix, suffix='.'+file_suffix, mode='wb', delete=False) as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(base64.b64decode(str(json_data.get('file').split(",")[-1])))
                temp_file.flush()
            
            update_cache_data(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_USER_TSV_FILE_KEY"],
                temp_file_path,
                current_app.config["WEKO_AUTHORS_IMPORT_TEMP_FILE_RETENTION_PERIOD"]
            )
            result = check_import_data(os.path.basename(temp_file_path))
            error = result.get('error')
            list_import_data = result.get('list_import_data')
            counts = result.get("counts")
            max_page = result.get("max_page")
            current_cache.delete(\
            current_app.config["WEKO_AUTHORS_IMPORT_CACHE_BAND_CHECK_USER_FILE_PATH_KEY"])
                    
        return jsonify(
            code=1,
            error=error,
            list_import_data=list_import_data,
            counts=counts,
            max_page=max_page)

    @author_permission.require(http_exception=403)
    @expose('/check_pagination', methods=['GET'])
    def check_pagination(self) -> jsonify:
        """pagination checkfile"""
        page_number = request.args.get("page_number")
        temp_file_path = current_cache.get(\
                current_app.config["WEKO_AUTHORS_IMPORT_CACHE_USER_TSV_FILE_KEY"])
        temp_folder_path = current_app.config.get("WEKO_AUTHORS_IMPORT_TEMP_FOLDER_PATH")
        
        # checkファイルパスの作成
        base_file_name = os.path.splitext(os.path.basename(temp_file_path))[0]
        check_file_name = f"{base_file_name}-check"
        part_check_file_name = f"{check_file_name}-part{page_number}"
        check_file_part1_path = os.path.join(temp_folder_path, part_check_file_name)
        
        with open(check_file_part1_path, "r", encoding="utf-8-sig") as check_part_file:
            result = json.load(check_part_file)
        return jsonify(result)

    @author_permission.require(http_exception=403)
    @expose('/check_file_download', methods=['POST'])
    def check_file_download(self):
        """インポートチェック画面でダウンロード処理"""
        band_file_path = current_cache.get(\
            current_app.config["WEKO_AUTHORS_IMPORT_CACHE_BAND_CHECK_USER_FILE_PATH_KEY"])
        if not band_file_path:        
            max_page = request.get_json().get("max_page")
            band_file_path = band_check_file_for_user(max_page)                    
        try:
            return send_file(band_file_path, as_attachment=True)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(e)

    @author_permission.require(http_exception=403)
    @expose('/import', methods=['POST'])
    def import_authors(self) -> jsonify:
        """Import author into System."""
        data = request.get_json() or {}
        
        # check import feature is available before import
        result_check = check_is_import_available(data.get('group_task_id'))
        if not result_check['is_available']:
            return jsonify(result_check)
        
        # 既にある結果一時ファイルの削除
        result_over_max_file_path = current_cache.get(\
                current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_OVER_MAX_FILE_PATH_KEY"])
        result_file_path = current_cache.get(\
                current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_FILE_PATH_KEY"])

        if result_over_max_file_path:
            try:
                current_cache.delete(\
                    current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_OVER_MAX_FILE_PATH_KEY"])
                os.remove(result_over_max_file_path)
                current_app.logger.debug(f"Deleted: {result_over_max_file_path}")
            except Exception as e:
                current_app.logger.error(f"Error deleting {result_over_max_file_path}: {e}")
        if result_file_path:
            try:
                current_cache.delete(\
                    current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_FILE_PATH_KEY"])
                os.remove(result_file_path)
                current_app.logger.debug(f"Deleted: {result_file_path}")
            except Exception as e:
                current_app.logger.error(f"Error deleting {result_file_path}: {e}")

        # 前回のimport結果サマリーを削除
        result_summary = current_cache.get(\
            current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_SUMMARY_KEY"])
        if result_summary:
            current_cache.delete(\
                current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_SUMMARY_KEY"])

        max_page_for_import_tab = data.get("max_page")
        
        # フロントの最大表示数分だけrecordsを確保
        records, reached_point, count = prepare_import_data(max_page_for_import_tab)
        tasks = []
        task_ids =[]
        
        group_tasks = []
        for author in records:
            group_tasks.append(import_author.s(author))

        # handle import tasks
        import_task = group(group_tasks).apply_async()
        import_task.save()
        for idx, task in enumerate(import_task.children):
            tasks.append({
                'task_id': task.task_id,
                'record_id': records[idx].get('pk_id'),
                'status': 'PENDING'
            })
            task_ids.append(task.task_id)
            
        # WEKO_AUTHORS_IMPORT_MAX_NUM_OF_DISPLAYSを超えた分を別のタスクで処理
        if count > current_app.config.get("WEKO_AUTHORS_IMPORT_MAX_NUM_OF_DISPLAYS"):
            task = import_author_over_max.delay(reached_point, count ,task_ids, max_page_for_import_tab)
            update_cache_data(\
                current_app.config.get("WEKO_AUTHORS_IMPORT_CACHE_OVER_MAX_TASK_KEY")
                , task.id, 0)
        response_data = {
            'group_task_id': import_task.id,
            "tasks": tasks
        }
        update_cache_data(
            WEKO_AUTHORS_IMPORT_CACHE_KEY,
            {**response_data, **{'records': records}},
            0
        )
        
        response_object = {
            "status": "success",
            "count": count,
            "data": {**response_data},
            "records":records
        }

        return jsonify(response_object)

    @expose('/check_import_status', methods=['POST'])
    def check_import_status(self):
        """Is import available."""
        result_task={}
        result = []
        data = request.get_json() or {}
        success_count = 0
        failure_count = 0
        if data and data.get('tasks'):
            for task_id in data.get('tasks'):
                task = import_author.AsyncResult(task_id)
                start_date = ""
                end_date = ""
                if task.result:
                    start_date = task.result.get('start_date', '')
                    end_date = task.result.get('end_date', '')
                status = states.PENDING
                error_id = None
                if task.result and task.result.get('status'):
                    status = task.result.get('status')
                    error_id = task.result.get('error_id')
                    if status == states.SUCCESS:
                        success_count += 1
                    elif status == states.FAILURE:
                        failure_count += 1
                result.append({
                    "task_id": task_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "status": status,
                    "error_id": error_id
                })
        over_max_task = current_cache.get(\
            current_app.config.get("WEKO_AUTHORS_IMPORT_CACHE_OVER_MAX_TASK_KEY")
        )
        if over_max_task:
            task = import_author_over_max.AsyncResult(over_max_task)
            status = states.PENDING
            error_id = None
            if task.result and task.result.get('status'):
                status = task.result.get('status')
                error_id = task.result.get('error_id')
            result_task["over_max"]={
                "task_id": over_max_task,
                "status": status,
                "error_id": error_id
            }
        summary = current_cache.get(\
            current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_SUMMARY_KEY"])
        if summary:
            success_count += summary["success_count"]
            failure_count += summary["failure_count"]
        result_task["summary"] = {
            "success_count": success_count,
            "failure_count": failure_count
        }
        result_task["tasks"] = result
        return jsonify(result_task)

    @author_permission.require(http_exception=403)
    @expose('/result_download', methods=['POST'])
    def result_file_download(self):
        """インポートチェック画面でダウンロード処理"""
        json = request.get_json().get("json")
        result_file_path = current_cache.get(\
            current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_FILE_PATH_KEY"])
        if not result_file_path:
            result_file_path = create_result_file_for_user(json)
        if not result_file_path:
            return jsonify({"Result": "Dont need to create result file"})
        try:
            return send_file(result_file_path, as_attachment=True)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(e)
        
    
authors_list_adminview = {
    'view_class': AuthorManagementView,
    'kwargs': {
        'category': _('Author Management'),
        'name': _('Edit'),
        'endpoint': 'authors'
    }
}

authors_export_adminview = {
    'view_class': ExportView,
    'kwargs': {
        'category': _('Author Management'),
        'name': _('Export'),
        'endpoint': 'authors/export'
    }
}

authors_import_adminview = {
    'view_class': ImportView,
    'kwargs': {
        'category': _('Author Management'),
        'name': _('Import'),
        'endpoint': 'authors/import'
    }
}

__all__ = (
    'authors_list_adminview',
    'authors_export_adminview',
    'authors_import_adminview'
)
