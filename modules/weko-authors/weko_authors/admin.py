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

from celery import states
from celery.task.control import revoke
from flask import abort, current_app, request, session
from flask.helpers import url_for
from flask.json import jsonify
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from invenio_files_rest.models import FileInstance

from weko_authors.config import WEKO_AUTHORS_EXPORT_FILE_NAME
from weko_authors.utils import delete_export_status, get_export_status, \
    get_export_url, set_export_status

from .permissions import author_permission
from .tasks import export_all


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
            render_widgets=False,  # Moved to admin, no need for widgets
            lang_code=session.get(
                'selected_language',
                'en')  # Set default lang
        )

    @author_permission.require(http_exception=403)
    @expose('/edit', methods=['GET'])
    def edit(self):
        """Render an adding author view."""
        return self.render(
            current_app.config['WEKO_AUTHORS_ADMIN_EDIT_TEMPLATE'],
            render_widgets=False,  # Moved to admin, no need for widgets
            lang_code=session.get('selected_language', 'en')  # Set default
        )


class ExportView(BaseView):
    """Weko export authors admin view."""

    @author_permission.require(http_exception=403)
    @expose('/', methods=['GET'])
    def index(self):
        return self.render(
            current_app.config['WEKO_AUTHORS_ADMIN_EXPORT_TEMPLATE']
        )

    @author_permission.require(http_exception=403)
    @expose('/download/' + WEKO_AUTHORS_EXPORT_FILE_NAME, methods=['GET'])
    def download(self):
        data = get_export_url()
        if data.get('file_uri'):
            file_instance = FileInstance.get_by_uri(data.get('file_uri'))
            return file_instance.send_file(
                WEKO_AUTHORS_EXPORT_FILE_NAME,
                mimetype='application/octet-stream',
                as_attachment=True
            )
        else:
            abort(404)

    @author_permission.require(http_exception=403)
    @expose('/check_status', methods=['GET'])
    def check_status(self):
        status = get_export_status()
        if not status:
            status = get_export_url()
        elif status.get('task_id'):
            task = export_all.AsyncResult(status.get('task_id'))
            if task.successful() or task.failed() \
                    or task.state == states.REVOKED:
                delete_export_status()
                status = get_export_url()
            else:
                status['file_uri'] = get_export_url().get('file_uri', '')

        # set download_link
        status['download_link'] = url_for(
            'authors/export.download', _external=True)
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
        task = export_all.delay()
        set_export_status(task_id=task.id)
        return jsonify({
            'code': 200,
            'data': {'task_id': task.id}
        })

    @author_permission.require(http_exception=403)
    @expose('/cancel', methods=['POST'])
    def cancel(self):
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
    pass


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
