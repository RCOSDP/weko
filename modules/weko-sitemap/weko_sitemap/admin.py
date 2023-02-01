# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-sitemap is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-sitemap."""

from __future__ import absolute_import, print_function

from datetime import datetime
from urllib.parse import urlparse

from celery.result import AsyncResult
from celery.task.control import inspect
from flask import abort, current_app, jsonify, render_template, request, \
    session, url_for
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from flask_login import current_user
from flask_wtf import FlaskForm,Form
from weko_admin.api import validate_csrf_header
from wtforms import ValidationError

from weko_accounts.utils import get_remote_addr




class SitemapSettingView(BaseView):
    """Sitemap setting view."""
    @expose('/', methods=['GET'])
    def index(self):
        """Update sitemap page."""
        form = Form()
        return self.render(current_app.config["WEKO_SITEMAP_ADMIN_TEMPLATE"],form=form)

    @expose('/update_sitemap', methods=['POST'])
    def update_sitemap(self):
        """Start the task to update the sitemap."""
        from .tasks import update_sitemap, link_success_handler, link_error_handler
        
        validate_csrf_header(request)
                
        # Celery cannot access config
        task = update_sitemap.apply_async(args=(
            datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z'),
            {'ip_address': get_remote_addr(),
            'user_agent': request.user_agent.string,
            'user_id': (
                current_user.get_id() if current_user.is_authenticated else None),
            'session_id': session.get('sid_s')}),
            link=link_success_handler.s(),
            link_error=link_error_handler.s())
        # Get all tasks:
        return jsonify({'task_id': task.id, 'loc': url_for(
            '.get_task_status', task_id=task.id)})

    @expose('/task_status/<string:task_id>', methods=['GET'])
    def get_task_status(self, task_id):
        """Get the status of the sitemap update task."""
        if not task_id:
            return abort(500)

        # TODO: Change the responses and the logic
        task_result = AsyncResult(task_id)
        if task_result.state == 'SUCCESS':
            response = {
                'start_time': task_result.info[0]['start_time'],
                'end_time': task_result.info[0]['end_time'],
                'total': task_result.info[0]['total'],
                'state': task_result.state
            }
        else:  # PENDING ERROR or other state
            response = {
                'start_time': '',
                'end_time': '',
                'total': '',
                'state': task_result.state
            }
        return jsonify(response)



sitemap_adminview = {
    'view_class': SitemapSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Sitemap'),
        'endpoint': 'sitemap'
    }
}
