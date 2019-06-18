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

import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime

import redis
from flask import abort, current_app, flash, jsonify, make_response, \
    redirect, render_template, request, url_for
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from flask_login import current_user
from flask_mail import Attachment
from invenio_accounts.models import Role, userrole
from invenio_admin.views import blueprint as invenio_admin_blueprint
from invenio_admin.views import protected_adminview_factory
from invenio_db import db
from invenio_mail.api import send_mail
from simplekv.memory.redisstore import RedisStore

from .models import LogAnalysisRestrictedCrawlerList, \
    LogAnalysisRestrictedIpAddress, StatisticsEmail
from .permissions import admin_permission_factory
from .utils import allowed_file, get_redis_cache
from .utils import get_user_report_data as get_user_report
from .utils import package_reports, reset_redis_cache


class StyleSettingView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Block style setting page."""
        wysiwyg_editor_default = [
            '<div class="ql-editor ql-blank" data-gramm="false" '
            'contenteditable="true"><p><br></p></div>']

        body_bg = '#fff'
        panel_bg = '#fff'
        footer_default_bg = 'rgba(13,95,137,0.8)'
        navbar_default_bg = '#f8f8f8'
        panel_default_border = '#ddd'
        scss_file = os.path.join(current_app.static_folder,
                                 'css/weko_theme/_variables.scss')
        try:
            with open(scss_file, 'r', encoding='utf-8') as fp:
                for line in fp.readlines():
                    line = line.strip()
                    if '$body-bg:' in line:
                        body_bg = line[line.find('#'):-1]
                    if '$panel-bg:' in line:
                        panel_bg = line[line.find('#'):-1]
                    if '$footer-default-bg:' in line:
                        footer_default_bg = line[line.find('#'):-1]
                    if '$navbar-default-bg:' in line:
                        navbar_default_bg = line[line.find('#'):-1]
                    if '$panel-default-border:' in line:
                        panel_default_border = line[line.find('#'):-1]

            from weko_theme.views import blueprint as theme_bp

            # Header
            f_path_header_wysiwyg = os.path.join(
                theme_bp.root_path,
                theme_bp.template_folder,
                current_app.config['THEME_HEADER_WYSIWYG_TEMPLATE'])
            header_array_wysiwyg = self.get_contents(f_path_header_wysiwyg)

            f_path_header_editor = os.path.join(
                theme_bp.root_path,
                theme_bp.template_folder,
                current_app.config['THEME_HEADER_EDITOR_TEMPLATE'])

            if self.cmp_files(f_path_header_wysiwyg, f_path_header_editor):
                header_array_wysiwyg = wysiwyg_editor_default

            # Footer
            f_path_footer_wysiwyg = os.path.join(
                theme_bp.root_path,
                theme_bp.template_folder,
                current_app.config['THEME_FOOTER_WYSIWYG_TEMPLATE'])
            footer_array_wysiwyg = self.get_contents(f_path_footer_wysiwyg)

            f_path_footer_editor = os.path.join(
                theme_bp.root_path,
                theme_bp.template_folder,
                current_app.config['THEME_FOOTER_EDITOR_TEMPLATE'])

            if self.cmp_files(f_path_footer_wysiwyg, f_path_footer_editor):
                footer_array_wysiwyg = wysiwyg_editor_default

            # Color
            if request.method == 'POST':
                if not admin_permission_factory('update-style-action').can():
                    current_app.logger.debug('deny access')
                    flash(_('deny access'))
                else:
                    form_lines = []
                    body_bg = request.form.get('body-bg', '#fff')
                    panel_bg = request.form.get('panel-bg', '#fff')
                    footer_default_bg = request.form.get(
                        'footer-default-bg', 'rgba(13,95,137,0.8)')
                    navbar_default_bg = request.form.get(
                        'navbar-default-bg', '#f8f8f8')
                    panel_default_border = request.form.get(
                        'panel-default-border', '#ddd')
                    form_lines.append(
                        '$body-bg: ' + body_bg + ';')
                    form_lines.append(
                        '$panel-bg: ' + panel_bg + ';')
                    form_lines.append(
                        '$footer-default-bg: ' + footer_default_bg + ';')
                    form_lines.append(
                        '$navbar-default-bg: ' + navbar_default_bg + ';')
                    form_lines.append(
                        '$panel-default-border: ' + panel_default_border + ';')
                    form_lines.append(
                        '$input-bg-transparent: rgba(255, 255, 255, 0);')

                    with open(scss_file, 'w', encoding='utf-8') as fp:
                        fp.writelines('\n'.join(form_lines))
        except BaseException:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
        return self.render(
            current_app.config["WEKO_ADMIN_BlOCK_STYLE_TEMPLATE"],
            body_bg=body_bg,
            panel_bg=panel_bg,
            footer_default_bg=footer_default_bg,
            navbar_default_bg=navbar_default_bg,
            panel_default_border=panel_default_border,
            header_innerHtml=''.join(header_array_wysiwyg),
            footer_innerHtml=''.join(footer_array_wysiwyg)
        )

    @expose('/upload_editor', methods=['POST'])
    def upload_editor(self):
        """Upload header/footer settings from wysiwyg editor."""
        try:
            from html import unescape
            from weko_theme.views import blueprint as theme_bp
            write_path = folder_path = os.path.join(
                theme_bp.root_path, theme_bp.template_folder)
            data = request.get_json()
            temp = data.get('temp')
            wysiwyg_html = unescape(data.get('content'))

            if 'footer' == temp:
                if 'True' == str(data.get('isEmpty')):
                    read_path = os.path.join(
                        folder_path, current_app.config['THEME_FOOTER_EDITOR_TEMPLATE'])
                    wysiwyg_html = self.get_contents(read_path)

                write_path = os.path.join(folder_path,
                                          current_app.config[
                                              'THEME_FOOTER_WYSIWYG_TEMPLATE'])
            elif 'header' == temp:
                if 'True' == str(data.get('isEmpty')):
                    read_path = os.path.join(
                        folder_path, current_app.config['THEME_HEADER_EDITOR_TEMPLATE'])
                    wysiwyg_html = self.get_contents(read_path)

                write_path = os.path.join(folder_path,
                                          current_app.config[
                                              'THEME_HEADER_WYSIWYG_TEMPLATE'])
            else:
                abort(400)

            with open(write_path, 'w+', encoding='utf-8') as fp:
                fp.writelines(wysiwyg_html)
        except Exception:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
            abort(500)
        return jsonify({'code': 0, 'msg': 'success'})

    def get_contents(self, f_path):
        """Get the contents of the file."""
        array = []
        try:
            with open(f_path, 'r', encoding='utf-8') as fp:
                for line in fp.readlines():
                    array.append(line)
        except Exception:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
            abort(500)
        return array

    def cmp_files(self, f_path1, f_path2):
        """Compare the contents of the file."""
        checksum1 = ''
        checksum2 = ''
        try:
            with open(f_path1, 'rb') as fp1:
                checksum1 = hashlib.md5(fp1.read()).hexdigest()
            with open(f_path2, 'rb') as fp2:
                checksum2 = hashlib.md5(fp2.read()).hexdigest()
        except Exception:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
            abort(500)
        return checksum1 == checksum2


class ReportView(BaseView):
    """Report view."""

    @expose('/', methods=['GET'])
    def index(self):
        try:
            aggs_query = {
                "size": 0,
                "aggs": {
                    "aggs_term": {
                        "terms": {
                            "field": "publish_status",
                            "order": {"_count": "desc"}
                        }
                    }
                }
            }

            from invenio_stats.utils import get_aggregations
            aggs_results = get_aggregations('weko', aggs_query)

            total = 0
            result = {}
            if aggs_results and 'aggs_term' in aggs_results:
                for bucket in aggs_results['aggs_term']['buckets']:
                    bkt = {
                        'open': bucket['doc_count']} if bucket['key'] == '0' else {
                        'private': bucket['doc_count']}
                    result.update(bkt)
                    total = total + bucket['doc_count']

            result.update({'total': total})

            cache_key = current_app.config['WEKO_ADMIN_CACHE_PREFIX'].\
                format(name='email_schedule')
            current_schedule = get_redis_cache(cache_key)
            current_schedule = json.loads(current_schedule) if \
                current_schedule else \
                current_app.config['WEKO_ADMIN_REPORT_DELIVERY_SCHED']

            # current_schedule = self.get_current_email_schedule() or \
            #     current_app.config['WEKO_ADMIN_REPORT_DELIVERY_SCHED']

            # Emails to send reports to
            all_emailAddress = StatisticsEmail().get_all()
            current_app.logger.info(all_emailAddress)
            return self.render(
                current_app.config['WEKO_ADMIN_REPORT_TEMPLATE'],
                result=result,
                now=datetime.utcnow(),
                emails=all_emailAddress,
                days_of_week=[_('Monday'), _('Tuesday'), _('Wednesday'),
                              _('Thursday'), _('Friday'), _('Saturday'),
                              _('Sunday')],
                current_schedule=current_schedule,
                frequency_options=current_app.config['WEKO_ADMIN_REPORT_FREQUENCIES'])
        except Exception as e:
            current_app.logger.error('Unexpected error: ', e)
        return abort(400)

    @expose('/stats_file_tsv', methods=['POST'])
    def get_file_stats_tsv(self):
        """Get file download/preview stats report."""
        stats_json = json.loads(request.form.get('report'))
        file_type = request.form.get('type')
        year = request.form.get('year')
        month = request.form.get('month').zfill(2)

        # current_app.logger.info(request.form.to_dict())

        # File Format: logReport__YYYY-MM.zip
        zip_date = str(year) + '-' + str(month).zfill(2)
        zip_name = 'logReport_' + zip_date + '.zip'
        try:
            # Dynamically create zip from StringIO data into BytesIO
            zip_stream = package_reports(stats_json, year, month)

            # Make the send email function a task so it
            if request.form.get('send_email') == 'True':
                recepients = StatisticsEmail.get_all_emails()
                html_body = render_template(
                    current_app.config['WEKO_ADMIN_REPORT_EMAIL_TEMPLATE'],
                    report_date=zip_date,
                    attached_file=zip_name)
                subject = zip_date + _(' Log report.')
                attachments = [Attachment(zip_name,
                                          'application/x-zip-compressed',
                                          zip_stream.getvalue())]
                send_mail(subject, recepients, html=html_body,
                          attachments=attachments)
                flash(_('Successfully sent the reports to the recepients.'))
            else:
                resp = make_response()
                resp.data = zip_stream.getvalue()
                resp.headers['Content-Type'] = 'application/x-zip-compressed'
                resp.headers['Content-Disposition'] = 'attachment; filename=' + \
                    zip_name
                return resp
        except Exception as e:
            current_app.logger.error('Unexpected error: ', e)
            flash(_('Unexpected Error'))
        return redirect(url_for('report.index'))

    @expose('/user_report_data', methods=['GET'])
    def get_user_report_data(self):
        """Get user report data from db and modify."""
        return jsonify(get_user_report())

    @expose('/set_email_schedule', methods=['POST'])
    def set_email_schedule(self):
        """Set new email schedule."""
        cache_key = current_app.config['WEKO_ADMIN_CACHE_PREFIX'].\
            format(name='email_schedule')

        # Get Schedule
        # current_app.logger.info(request.form.to_dict())
        frequency = request.form.get('frequency')
        enabled = True if request.form.get('dis_enable_schedule') == 'True' \
            else False

        # Details come in two different types
        details = ''
        if frequency == 'weekly':
            details = request.form.get('weekly_details')
        elif frequency == 'monthly':
            details = request.form.get('monthly_details')

        schedule = {
            'frequency': frequency,
            'details': details,
            'enabled': enabled
        }

        try:
            reset_redis_cache(cache_key, json.dumps(schedule))
            flash(_('Successfully Changed Schedule.'))
        except Exception:
            flash(_('Could Not Save Changes.'))
        return redirect(url_for('report.index'))

    @expose('/get_email_address', methods=['POST'])
    def get_email_address(self):
        """Save Email Address."""
        inputEmail = request.form.getlist('inputEmail')
        StatisticsEmail.delete_all_row()
        alert_msg = 'Successfully saved email addresses.'
        for input in inputEmail:
            if input:
                match = re.match(
                    r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', input)
                if match:
                    StatisticsEmail.insert_email_address(input)
                else:
                    alert_msg = 'Please check email input fields.'
        flash(_(alert_msg))
        return redirect(url_for("report.index"))


class LanguageSettingView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        return self.render(
            current_app.config["WEKO_ADMIN_LANG_SETTINGS"]
        )


class WebApiAccount(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        return self.render(
            current_app.config["WEKO_ADMIN_WEB_API_ACCOUNT"]
        )


class StatsSettingsView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        cache_key = current_app.config['WEKO_ADMIN_CACHE_PREFIX'].\
            format(name='display_stats')

        current_display_setting = True  # Default
        datastore = RedisStore(redis.StrictRedis.from_url(
            current_app.config['CACHE_REDIS_URL']))
        if datastore.redis.exists(cache_key):
            curr_display_setting = datastore.get(cache_key).decode('utf-8')
            current_display_setting = True if curr_display_setting == 'True' \
                else False

        if request.method == 'POST':
            display_setting = request.form.get('record_stats_radio', 'True')
            datastore.delete(cache_key)
            datastore.put(cache_key, display_setting.encode('utf-8'))
            flash(_('Successfully Changed Settings.'))
            return redirect(url_for('statssettings.index'))

        return self.render(
            current_app.config["WEKO_ADMIN_STATS_SETTINGS_TEMPLATE"],
            display_stats=current_display_setting)


class LogAnalysisSettings(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        if request.method == 'POST':
            crawler_lists, new_ip_addresses = self.parse_form_data(
                request.form)
            try:
                LogAnalysisRestrictedIpAddress.update_table(new_ip_addresses)
                LogAnalysisRestrictedCrawlerList.update_or_insert_list(
                    crawler_lists)
            except Exception as e:
                current_app.logger.error(
                    'Could not save restricted data: ', e)
                flash(_('Could not save data.'))

        # Get most current restricted addresses/user agents
        try:
            restricted_ip_addresses = LogAnalysisRestrictedIpAddress.get_all()
            shared_crawlers = LogAnalysisRestrictedCrawlerList.get_all()
            # current_app.logger.info(LogAnalysisRestrictedCrawlerList.get_all_active())
            if not shared_crawlers:
                LogAnalysisRestrictedCrawlerList \
                    .add_list(current_app.config["WEKO_ADMIN_DEFAULT_CRAWLER_LISTS"])
                shared_crawlers = LogAnalysisRestrictedCrawlerList.get_all()
        except Exception:
            current_app.logger.error(_('Could not get restricted data: '),
                                     sys.exc_info()[0])
            restricted_ip_addresses = []
            shared_crawlers = []

        return self.render(
            current_app.config["WEKO_ADMIN_LOG_ANALYSIS_SETTINGS_TEMPLATE"],
            restricted_ip_addresses=restricted_ip_addresses,
            shared_crawlers=shared_crawlers
        )

    def parse_form_data(self, raw_data):
        """Parse the one dimensional form data into mult-dimensional objects."""
        new_ip_addresses = []
        seen_ip_addresses = []
        new_crawler_lists = []
        for name, value in raw_data.to_dict().items():
            if(re.match('^shared_crawler_[0-9]+$', name)):
                is_active = True if raw_data.get(name + '_check') else False
                new_crawler_lists.append({
                    'id': raw_data.get(name + '_id', 0),
                    'list_url': value,
                    'is_active': is_active,
                })
            elif(re.match('^address_list_[0-9]+$', name)):
                if name not in seen_ip_addresses and ''.join(
                        raw_data.getlist(name)):
                    seen_ip_addresses.append(name)
                    new_ip_addresses.append('.'.join(raw_data.getlist(name)))
        return new_crawler_lists, new_ip_addresses


def _role_endpoint_viewable(endpoint):
    """Check whether the current user role can view the endpoint - util."""
    conf = current_app.config
    access_table = conf['WEKO_ADMIN_ACCESS_TABLE']
    system_admin = conf['WEKO_ADMIN_PERMISSION_ROLE_SYSTEM']
    try:
        roles = db.session.query(Role).join(userrole).filter_by(
            user_id=current_user.get_id()).all()
    except Exception as e:
        current_app.logger.error(
            'Could not determine roles - returning False: ', e)
        # flash(_('Unexpected error occured.'))
        roles = []
    for role in roles:  # Check if role can view endpoint
        access_list = access_table[role.name] if role.name in access_table \
            else []
        if endpoint in access_list or role.name == system_admin:
            return True
    return False


@staticmethod
def role_has_access():
    """Check if user's role has access to view endpoint."""
    endpoint = request.url_rule.endpoint.split('.')[0]
    return _role_endpoint_viewable(endpoint)


@invenio_admin_blueprint.before_app_first_request
def is_accessible_to_role():
    """Check if current user's role has access to view."""
    for i, view in enumerate(current_app.extensions['admin'][0]._views):
        setattr(view, 'is_accessible', role_has_access.__func__)

        # Stop lambda from pointing to last instance of variable
        if _role_endpoint_viewable(view.endpoint):
            setattr(view, 'is_visible', lambda: True)
        else:
            setattr(view, 'is_visible', lambda: False)
        current_app.extensions['admin'][0]._views[i] = view  # Overwrite view


style_adminview = {
    'view_class': StyleSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Style'),
        'endpoint': 'stylesetting'
    }
}

report_adminview = {
    'view_class': ReportView,
    'kwargs': {
        'category': _('Statistics'),
        'name': _('Report'),
        'endpoint': 'report'
    }
}

stats_settings_adminview = {
    'view_class': StatsSettingsView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Stats'),
        'endpoint': 'statssettings'
    }
}

log_analysis_settings_adminview = {
    'view_class': LogAnalysisSettings,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Log Analysis'),
        'endpoint': 'loganalysissetting'
    }
}

language_adminview = {
    'view_class': LanguageSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Language'),
        'endpoint': 'language'
    }
}

web_api_account_adminview = {
    'view_class': WebApiAccount,
    'kwargs': {
        'category': _('Setting'),
        'name': _('WebAPI Account'),
        'endpoint': 'webapiaccount'
    }
}

__all__ = (
    'style_adminview',
    'report_adminview',
    'language_adminview',
    'web_api_account_adminview',
    'stats_settings_adminview',
    'log_analysis_settings_adminview',
)
