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

import json
from celery import group, states
from celery.task.control import revoke
from flask import abort, current_app, request, session
from flask.helpers import url_for
from flask.json import jsonify
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from invenio_files_rest.models import FileInstance
from weko_workflow.utils import update_cache_data

from .config import WEKO_AUTHORS_EXPORT_FILE_NAME, \
    WEKO_AUTHORS_IMPORT_CACHE_KEY
from .permissions import author_permission
from .tasks import check_is_import_available, export_all, import_author
from .utils import check_import_data, delete_export_status, \
    get_export_status, get_export_url, set_export_status


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
        status = get_export_status()
        if not status:
            status = get_export_url()
        elif status.get('task_id'):
            task = export_all.AsyncResult(status.get('task_id'))
            if task.successful() or task.failed() \
                    or task.state == states.REVOKED:
                delete_export_status()
                status = get_export_url()
                if not task.result:
                    status['error'] = 'export_fail'
            else:
                status['file_uri'] = get_export_url().get('file_uri', '')

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

        json_data = request.get_json()
        if json_data:
            result = check_import_data(
                json_data.get('file_name'),
                json_data.get('file').split(",")[-1]
            )
            error = result.get('error')
            list_import_data = result.get('list_import_data')

        return jsonify(
            code=1,
            error=error,
            list_import_data=list_import_data)

    @author_permission.require(http_exception=403)
    @expose('/import', methods=['POST'])
    def import_authors(self) -> jsonify:
        """Import author into System."""
        data = request.get_json() or {}
        
        # check import feature is available before import
        result_check = check_is_import_available(data.get('group_task_id'))
        if not result_check['is_available']:
            return jsonify(result_check)

        tasks = []
        records = [item for item in data.get(
            'records', []) if not item.get('errors')]
        
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
            "data": {**response_data}
        }

        return jsonify(response_object)

    @expose('/check_import_status', methods=['POST'])
    def check_import_status(self):
        """Is import available."""
        result = []
        data = request.get_json() or {}
        if data and data.get('tasks'):
            for task_id in data.get('tasks'):
                task = import_author.AsyncResult(task_id)
                start_date = task.result['start_date'] if task.result else ''
                end_date = task.result['end_date'] if task.result else ''
                status = states.PENDING
                error_id = None
                if task.result and task.result.get('status'):
                    status = task.result.get('status')
                    error_id = task.result.get('error_id')
                result.append({
                    "task_id": task_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "status": status,
                    "error_id": error_id
                })

        return jsonify(result)


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
