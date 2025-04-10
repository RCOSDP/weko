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

"""WEKO3 module docstring."""

import os
import sys
from datetime import datetime
from enum import Enum

import celery
from flask import current_app, flash, jsonify, redirect, request, session, \
    url_for
from flask_admin import expose
from flask_admin.contrib.sqla import ModelView
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_admin.forms import LazyChoices
from invenio_communities.models import Community
from invenio_db import db
from markupsafe import Markup
from sqlalchemy import func
from weko_accounts.utils import get_remote_addr
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index
from weko_user_profiles.api import current_userprofile, localize_time

from .api import send_run_status_mail
from .models import HarvestLogs, HarvestSettings
from .tasks import link_error_handler, link_success_handler, run_harvesting


def _(x):
    return x


def run_stats():
    """Get run status."""
    def object_formatter(v, c, m, p):
        harvesting = HarvestSettings.query.filter_by(id=m.id).first()
        if harvesting.task_id is None and harvesting.resumption_token is None:
            return Markup('Harvesting is not running')
        elif harvesting.task_id is None:
            return Markup('Harvesting is paused with resumption token: '
                          + harvesting.resumption_token)
        else:
            return Markup('Harvesting is running at task id:' + harvesting.task_id
                          + '</br>' + str(harvesting.item_processed) + ' items processed')
    return object_formatter


def control_btns():
    """Generate a object formatter for buttons."""
    def object_formatter(v, c, m, p):
        """Format object view."""
        run_url = url_for('harvestsettings.run')
        run_text = _('Run')
        run_btn = '<a id="hvt-btn" class="btn btn-primary" href="{0}?id={1}">{2}</a>'.format(
            run_url, m.id, run_text)
        resume_text = _('Resume')
        resume_btn = '<a id="resume-btn" class="btn btn-primary" href="{0}?id={1}">{2}</a>'.format(
            run_url, m.id, resume_text)
        pause_url = url_for('harvestsettings.pause')
        pause_text = _('Pause')
        pause_btn = '<a id="pause-btn" class="btn btn-warning" href="{0}?id={1}">{2}</a>'.format(
            pause_url, m.id, pause_text)
        clear_url = url_for('harvestsettings.clear')
        clear_text = _('Clear')
        clear_btn = '<a id="clear-btn" class="btn btn-danger" href="{0}?id={1}">{2}</a>'.format(
            clear_url, m.id, clear_text)
        harvesting = HarvestSettings.query.filter_by(id=m.id).first()
        if harvesting.task_id is None and harvesting.resumption_token is None:
            return Markup(run_btn)
        elif harvesting.task_id is None:
            return Markup(resume_btn + clear_btn)
        else:
            return Markup(pause_btn)
    return object_formatter


def index_query():
    """Get index list."""
    if any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in current_user.roles):
        return Index.query.all()
    else:
        index_list = []
        repositories = Community.get_repositories_by_user(current_user)
        for repository in repositories:
            index = Indexes.get_child_list_recursive(repository.root_node_id)
            index_list.extend(index)
        return Index.query.filter(Index.id.in_([int(index) for index in index_list])).all()


class HarvestSettingView(ModelView):
    """Harvest setting page view."""

    @expose('/run/')
    def run(self):
        """Run harvesting."""
        user_id = current_user.get_id() if current_user and current_user.is_authenticated else -1
        user_data = {
            'ip_address': get_remote_addr(),
            'user_agent': request.user_agent.string,
            'user_id': user_id,
            'session_id': session.get('sid_s')
        }
        request_info = {
            "remote_addr": request.remote_addr,
            "referrer": request.referrer,
            "hostname": request.host,
            "user_id": user_id,
            "action": "HARVEST"
        }

        run_harvesting.apply_async(args=(
            request.args.get('id'),
            datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z'),
            user_data,
            request_info),
            link=link_success_handler.s(),
            link_error=link_error_handler.s())
        return redirect(url_for('harvestsettings.details_view',
                                id=request.args.get('id')))

    @expose('/pause/')
    def pause(self):
        """Pause harvesting."""
        harvesting = HarvestSettings.query.filter_by(
            id=request.args.get('id')).first()
        celery.current_app.control.revoke(harvesting.task_id, terminate=True)
        return redirect(url_for('harvestsettings.details_view',
                                id=request.args.get('id')))

    @expose('/clear/')
    def clear(self):
        """Clear harvesting."""
        try:
            harvesting = HarvestSettings.query.filter_by(
                id=request.args.get('id')).first()
            harvesting.task_id = None
            harvesting.resumption_token = None
            harvesting.item_processed = 0
            harvest_log = \
                HarvestLogs.query.filter_by(
                    harvest_setting_id=harvesting.id).order_by(
                    HarvestLogs.id.desc()).first()
            harvest_log.status = 'Cancel'
            harvest_log.end_time = datetime.now()
            send_run_status_mail(harvesting, harvest_log)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
        return redirect(url_for('harvestsettings.details_view',
                                id=request.args.get('id')))

    @expose('/get_logs/')
    def get_logs(self):
        """Get Logs."""
        number_of_histories = current_app.config['OAIHARVESTER_NUMBER_OF_HISTORIES']
        logs = HarvestLogs.query.filter_by(
            harvest_setting_id=request.args.get('id')).order_by(HarvestLogs.id.desc()).limit(number_of_histories).all()
        res = []
        for log in logs:
            log.__dict__.pop('_sa_instance_state')
            start_time = log.__dict__['start_time']
            end_time = log.__dict__['end_time']
            start_time = localize_time(start_time)
            log.__dict__['start_time'] = start_time.isoformat()
            if end_time:
                end_time = localize_time(end_time)
                log.__dict__['end_time'] = end_time.isoformat()
            res.append(log.__dict__)
        return jsonify(res)

    @expose('/get_log_detail/<id>/')
    def get_log_detail(self, id):
        """Get log detail."""
        log = HarvestLogs.query.filter_by(id=id).first()
        return jsonify(log.setting)

    @expose('/set_schedule/<id>/', methods=['POST'])
    def set_schedule(self, id):
        """Set schedule."""
        try:
            harvesting = HarvestSettings.query.filter_by(
                id=id).first()
            harvesting.schedule_enable = eval(request.form['dis_enable_schedule'])
            harvesting.schedule_frequency = request.form['frequency']
            if harvesting.schedule_frequency == 'weekly':
                harvesting.schedule_details = request.form['weekly_details']
            elif harvesting.schedule_frequency == 'monthly':
                harvesting.schedule_details = request.form['monthly_details']
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
        return redirect(url_for('harvestsettings.edit_view', id=id))

    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        """Edit view."""
        harvesting = HarvestSettings.query.filter_by(
            id=request.args.get('id')).first()
        self._template_args['current_schedule'] = {
            'frequency': harvesting.schedule_frequency,
            'details': harvesting.schedule_details,
            'enabled': harvesting.schedule_enable}
        self._template_args['days_of_week'] = [_('Monday'), _('Tuesday'), _('Wednesday'),
                                               _('Thursday'), _(
                                                   'Friday'), _('Saturday'),
                                               _('Sunday')]
        self._template_args['frequency_options'] = [
            'daily', 'weekly', 'monthly']
        return super(HarvestSettingView, self).edit_view()


    def get_query(self):
        """Return a query for the model type."""
        if any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in current_user.roles):
            return self.session.query(self.model)
        else:
            return self.session.query(self.model).filter(self._index_filter())

    def get_count_query(self):
        """Return a the count query for the model type."""
        if any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in current_user.roles):
            return self.session.query(func.count('*')).select_from(self.model)
        else:
            return self.session.query(func.count('*')).select_from(self.model).filter(self._index_filter())

    def _index_filter(self):
        """Get index list."""
        index_list = []
        repositories = Community.get_repositories_by_user(current_user)
        for repository in repositories:
            index = Indexes.get_child_list_recursive(repository.root_node_id)
            index_list.extend(index)
        return self.model.index_id.in_([int(index) for index in index_list])

    details_template = 'invenio_oaiharvester/details.html'
    edit_template = 'invenio_oaiharvester/edit.html'
    can_create = True
    can_delete = True
    can_edit = True
    can_view_details = True
    page_size = 25

    column_formatters = dict(
        running_status=run_stats(),
        Harvesting=control_btns()
    )
    column_details_list = (
        'repository_name', 'base_url', 'from_date', 'until_date',
        'set_spec', 'metadata_prefix', 'target_index.index_name',
        'update_style', 'auto_distribution', 'running_status', 'Harvesting',
    )

    form_columns = (
        'repository_name', 'base_url', 'from_date', 'until_date',
        'set_spec', 'metadata_prefix', 'target_index',
        'update_style', 'auto_distribution'
    )
    column_list = (
        'repository_name', 'base_url', 'from_date', 'until_date',
        'set_spec', 'metadata_prefix', 'target_index.index_name',
        'update_style', 'auto_distribution',
    )
    form_choices = dict(
        update_style=LazyChoices(lambda: current_app.config[
            'OAIHARVESTER_UPDATE_STYLE_OPTIONS'].items()),
        auto_distribution=LazyChoices(lambda: current_app.config[
            'OAIHARVESTER_AUTO_DISTRIBUTION_OPTIONS'].items()))

    form_args = {
        'target_index': {
            'query_factory': index_query
        }
    }


harvest_admin_view = dict(
    modelview=HarvestSettingView,
    model=HarvestSettings,
    category=_('OAI-PMH'),
    name=_('Harvesting'))
