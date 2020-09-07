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

import copy
import hashlib
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta

import redis
from flask import abort, current_app, flash, jsonify, make_response, \
    redirect, render_template, request, url_for
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.form import rules
from flask_babelex import gettext as _
from flask_login import current_user
from flask_mail import Attachment
from invenio_communities.models import Community
from invenio_db import db
from invenio_files_rest.storage.pyfs import remove_dir_with_file
from invenio_mail.api import send_mail
from simplekv.memory.redisstore import RedisStore
from weko_records.api import ItemTypes, SiteLicense
from weko_records.models import SiteLicenseInfo
from wtforms.fields import StringField
from wtforms.validators import ValidationError

from .config import WEKO_PIDSTORE_IDENTIFIER_TEMPLATE_CREATOR, \
    WEKO_PIDSTORE_IDENTIFIER_TEMPLATE_EDITOR
from .models import AdminSettings, Identifier, \
    LogAnalysisRestrictedCrawlerList, LogAnalysisRestrictedIpAddress, \
    RankingSettings, SearchManagement, StatisticsEmail
from .permissions import admin_permission_factory
from .utils import get_init_display_index, get_redis_cache, \
    get_response_json, get_search_setting
from .utils import get_user_report_data as get_user_report
from .utils import package_reports, reset_redis_cache, str_to_bool


# FIXME: Change all setting views' path to be under settings/
class StyleSettingView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Block style setting page."""
        # wysiwyg_editor_default = [
        #     '<div class="ql-editor ql-blank" data-gramm="false" '
        #     'contenteditable="true"><p><br></p></div>']

        body_bg = '#fff'
        panel_bg = '#fff'
        footer_default_bg = 'rgba(13,95,137,0.8)'
        navbar_default_bg = '#f8f8f8'
        panel_default_border = '#ddd'
        scss_file = os.path.join(
            current_app.instance_path,
            current_app.config['WEKO_THEME_INSTANCE_DATA_DIR'],
            '_variables.scss')

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

            # Color
            if request.method == 'POST':
                if not admin_permission_factory('update-style-action').can():
                    current_app.logger.debug('deny access')
                    flash(_('deny access'))
                else:
                    form_lines = []
                    body_bg = request.form.get('body-bg', body_bg)
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
                    flash(_('Successfully update color.'), category="success")
        except BaseException:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
        return self.render(
            current_app.config["WEKO_ADMIN_BlOCK_STYLE_TEMPLATE"],
            body_bg=body_bg,
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
                        folder_path, current_app.config[
                            'THEME_FOOTER_EDITOR_TEMPLATE'])
                    wysiwyg_html = self.get_contents(read_path)

                write_path = os.path.join(folder_path,
                                          current_app.config[
                                              'THEME_FOOTER_WYSIWYG_TEMPLATE'])
            elif 'header' == temp:
                if 'True' == str(data.get('isEmpty')):
                    read_path = os.path.join(
                        folder_path, current_app.config[
                            'THEME_HEADER_EDITOR_TEMPLATE'])
                    wysiwyg_html = self.get_contents(read_path)

                write_path = os.path.join(folder_path, current_app.config[
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
                "post_filter": {
                    "term": {
                        "relation_version_is_last": True
                    }
                },
                "aggs": {
                    "aggs_filter": {
                        "filter": {
                            "term": {
                                "relation_version_is_last": True
                            }
                        },
                        "aggs": {
                            "aggs_term": {
                                "terms": {
                                    "field": "publish_status",
                                    "order": {"_count": "desc"}
                                }
                            }
                        }
                    }
                }
            }

            from invenio_stats.utils import get_aggregations
            aggs_results = get_aggregations(
                current_app.config['SEARCH_UI_SEARCH_INDEX'], aggs_query)

            total = 0
            result = {}
            if aggs_results \
                    and 'aggs_filter' in aggs_results \
                    and 'aggs_term' in aggs_results['aggs_filter']:
                for bucket \
                        in aggs_results['aggs_filter']['aggs_term']['buckets']:
                    bkt = {'open': bucket['doc_count']} \
                        if bucket['key'] == '0' \
                        else {'private': bucket['doc_count']}
                    result.update(bkt)
                    total = total + bucket['doc_count']

            result.update({'total': total})

            cache_key = current_app.config['WEKO_ADMIN_CACHE_PREFIX'].\
                format(name='email_schedule')
            current_schedule = get_redis_cache(cache_key)
            current_schedule = json.loads(current_schedule) if \
                current_schedule else \
                current_app.config['WEKO_ADMIN_REPORT_DELIVERY_SCHED']

            # Emails to send reports to
            all_email_address = StatisticsEmail().get_all()
            return self.render(
                current_app.config['WEKO_ADMIN_REPORT_TEMPLATE'],
                result=result,
                now=datetime.utcnow(),
                emails=all_email_address,
                days_of_week=[_('Monday'), _('Tuesday'), _('Wednesday'),
                              _('Thursday'), _('Friday'), _('Saturday'),
                              _('Sunday')],
                current_schedule=current_schedule,
                frequency_options=current_app.config[
                    'WEKO_ADMIN_REPORT_FREQUENCIES'])
        except Exception as e:
            current_app.logger.error('Unexpected error: ', e)
        return abort(400)

    @expose('/stats_file_tsv', methods=['POST'])
    def get_file_stats_tsv(self):
        """Get file download/preview stats report."""
        stats_json = json.loads(request.form.get('report'))
        # file_type = request.form.get('type')
        year = request.form.get('year')
        month = request.form.get('month').zfill(2)

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
                resp.headers['Content-Disposition'] = 'attachment; filename='\
                                                      + zip_name
                return resp
        except Exception as e:
            current_app.logger.error('Unexpected error: ', e)
            flash(_('Unexpected error occurred.'), 'error')
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
            flash(_('Successfully Changed Schedule.'), 'error')
        except Exception:
            flash(_('Could Not Save Changes.'), 'error')
        return redirect(url_for('report.index'))

    @expose('/get_email_address', methods=['POST'])
    def get_email_address(self):
        """Save Email Address."""
        input_email = request.form.getlist('input_email')
        StatisticsEmail.delete_all_row()
        alert_msg = 'Successfully saved email addresses.'
        category = 'info'
        for input in input_email:
            if input:
                match = re.match(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+('
                                 r'\.[a-z0-9-]+)*(\.[a-z]{2,4})$', input)
                if match:
                    StatisticsEmail.insert_email_address(input)
                else:
                    alert_msg = 'Please check email input fields.'
                    category = 'error'
        flash(_(alert_msg), category=category)
        return redirect(url_for("report.index"))


class FeedbackMailView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        return self.render(
            current_app.config["WEKO_ADMIN_FEEDBACK_MAIL"]
        )


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
                flash(_('Could not save data.'), 'error')

        # Get most current restricted addresses/user agents
        try:
            restricted_ip_addresses = LogAnalysisRestrictedIpAddress.get_all()
            shared_crawlers = LogAnalysisRestrictedCrawlerList.get_all()
            if not shared_crawlers:
                LogAnalysisRestrictedCrawlerList.add_list(current_app.config[
                    "WEKO_ADMIN_DEFAULT_CRAWLER_LISTS"])
                shared_crawlers = LogAnalysisRestrictedCrawlerList.get_all()
        except Exception as e:
            current_app.logger.error(_('Could not get restricted data: '), e)
            flash(_('Could not get restricted data.'), 'error')
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


class RankingSettingsView(BaseView):
    """Ranking settings view."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        if request.method == 'POST':
            try:
                form = request.form.get('submit', None)
                if form == 'save_ranking_settings':
                    settings = RankingSettings()
                    settings.is_show = request.form.get('is_show',
                                                        False) == 'True'
                    new_item_period = int(request.form.get('new_item_period',
                                                           14))
                    if new_item_period < 1 or new_item_period > 30:
                        current_app.logger.debug(new_item_period)
                        raise
                    settings.new_item_period = new_item_period
                    settings.statistical_period = \
                        request.form.get('statistical_period', 365)
                    settings.display_rank = \
                        request.form.get('display_rank', 10)
                    most_reviewed_items_flag = True \
                        if request.form.get('most_reviewed_items') else False
                    most_downloaded_items_flag = True \
                        if request.form.get('most_downloaded_items') \
                        else False
                    created_most_items_user_flag = True \
                        if request.form.get('created_most_items_user') \
                        else False
                    most_searched_keywords_flag = True \
                        if request.form.get('most_searched_keywords') \
                        else False
                    new_items_flag = True \
                        if request.form.get('new_items') else False
                    settings.rankings = {
                        'most_reviewed_items': most_reviewed_items_flag,
                        'most_downloaded_items': most_downloaded_items_flag,
                        'created_most_items_user':
                        created_most_items_user_flag,
                        'most_searched_keywords': most_searched_keywords_flag,
                        'new_items': new_items_flag
                    }
                    RankingSettings.update(data=settings)
                    flash(_('Successfully Changed Settings.'))
                    return redirect(url_for('rankingsettings.index'))
            except Exception as ex:
                current_app.logger.debug(ex)
                flash(_('Failurely Changed Settings.'), 'error')
                return redirect(url_for('rankingsettings.index'))

        settings = RankingSettings.get()
        if settings:
            is_show = settings.is_show
            new_item_period = settings.new_item_period
            statistical_period = settings.statistical_period
            display_rank = settings.display_rank
            rankings = settings.rankings
        else:
            is_show = False
            new_item_period = 14
            statistical_period = 365
            display_rank = 10
            rankings = {'most_reviewed_items': False,
                        'most_downloaded_items': False,
                        'created_most_items_user': False,
                        'most_searched_keywords': False,
                        'new_items': False}

        return self.render(
            current_app.config["WEKO_ADMIN_RANKING_SETTINGS_TEMPLATE"],
            is_show=is_show,
            new_item_period=new_item_period,
            statistical_period=statistical_period,
            display_rank=display_rank,
            rankings=rankings
        )


class SearchSettingsView(BaseView):
    """Search settings view."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Site license setting page."""
        search_setting = get_search_setting()
        result = json.dumps(copy.deepcopy(search_setting))
        options = json.dumps(current_app.config['WEKO_ADMIN_SEARCH_OPTIONS'])
        init_disp_index = json.dumps(get_init_display_index(search_setting))
        if 'POST' in request.method:
            jfy = {}
            try:
                # update search setting
                db_data = request.get_json()
                res = SearchManagement.get()

                if res:
                    id = res.id
                    SearchManagement.update(id, db_data)
                else:
                    SearchManagement.create(db_data)
                jfy['status'] = 201
                jfy['message'] = 'Search setting was successfully updated.'
            except BaseException as e:
                current_app.logger.error('Could not save search settings', e)
                jfy['status'] = 500
                jfy['message'] = 'Failed to update search setting.'
            return make_response(jsonify(jfy), jfy['status'])

        try:
            return self.render(
                current_app.config['WEKO_ADMIN_SEARCH_MANAGEMENT_TEMPLATE'],
                setting_data=result,
                search_management_options=options,
                init_disp_index=init_disp_index,
            )
        except BaseException as e:
            current_app.logger.error('Could not save search settings', e)
            abort(500)
            # flash(_('Unable to change search settings.'), 'error')


class SiteLicenseSettingsView(BaseView):
    """Site License settings view."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Site License settings view."""
        if 'POST' in request.method:
            jfy = {}
            try:
                # update item types and site license info
                data = request.get_json()
                if data and data.get('site_license'):
                    for license in data['site_license']:
                        err_addr = False
                        if not license.get('addresses'):
                            err_addr = True
                        else:
                            for addresses in license['addresses']:
                                for item in addresses.values():
                                    if not item or '' in item:
                                        err_addr = True
                                        # break for item addresses
                                        break
                                if err_addr:
                                    # break for addresses
                                    break
                        if err_addr:
                            raise ValueError('IP Address is incorrect')

                SiteLicense.update(data)
                jfy['status'] = 201
                jfy['message'] = 'Site license was successfully updated.'
            except BaseException:
                jfy['status'] = 500
                jfy['message'] = 'Failed to update site license.'
            return make_response(jsonify(jfy), jfy['status'])

        try:
            # site license list
            result_list = SiteLicense.get_records()
            # item types list
            n_lst = ItemTypes.get_latest()
            result = get_response_json(result_list, n_lst)
            return self.render(
                current_app.config['WEKO_ADMIN_SITE_LICENSE_TEMPLATE'],
                result=json.dumps(result))
        except BaseException as e:
            current_app.logger.error('Could not save site license settings', e)
            abort(500)


class SiteLicenseSendMailSettingsView(BaseView):
    """Site-License send mail settings."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        if request.method == 'POST':
            data = request.get_json()
            settings = AdminSettings.get('site_license_mail_settings')
            settings.auto_send_flag = data['auto_send_flag']
            AdminSettings.update('site_license_mail_settings',
                                 settings.__dict__)
            for name in data['checked_list']:
                sitelicense = SiteLicenseInfo.query.filter_by(
                    organization_name=name).first()
                if sitelicense:
                    sitelicense.receive_mail_flag = data['checked_list'][name]
                    db.session.commit()

        sitelicenses = SiteLicenseInfo.query.order_by(
            SiteLicenseInfo.organization_id).all()
        settings = AdminSettings.get('site_license_mail_settings')
        now = datetime.utcnow()
        last_month = (now.replace(day=1) - timedelta(days=1)).replace(day=1)

        return self.render(
            current_app.config['WEKO_ADMIN_SITE_LICENSE_SEND_MAIL_TEMPLATE'],
            sitelicenses=sitelicenses,
            auto_send=settings.auto_send_flag,
            now=now,
            last_month=last_month
        )


class FilePreviewSettingsView(BaseView):
    """File preview settings."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """File preview settings."""
        if request.method == 'POST':
            try:
                form = request.form.get('submit', None)
                if form == 'save_settings':
                    old_settings = AdminSettings.get('convert_pdf_settings')
                    old_path = old_settings.path if old_settings else None

                    new_settings = {}
                    new_path = request.form.get('path')
                    if not new_path or new_path == '/':
                        current_app.logger.debug(new_path)
                        raise
                    else:
                        new_path = new_path \
                            if not new_path[-1:] == '/' else new_path[:-1]

                    # Delete files in old folder if folder is changed
                    if old_path and not new_path == old_path:
                        old_path = old_path + '/pdf_dir'
                        remove_dir_with_file(old_path)

                    # Save settings in db
                    new_settings['path'] = new_path
                    new_settings['pdf_ttl'] = \
                        int(request.form.get('pdf_ttl'))
                    AdminSettings.update('convert_pdf_settings',
                                         new_settings)
                    flash(_('Successfully Changed Settings.'))
                else:
                    current_app.logger.debug(form)
                    flash(_('Failurely Changed Settings.'), 'error')
            except Exception as ex:
                current_app.logger.error(ex)
                flash(_('Failurely Changed Settings.'), 'error')
            return redirect(url_for('filepreview.index'))

        # Load settings from settings if there is not settings in db
        settings = AdminSettings.get('convert_pdf_settings')
        if not settings:
            temp = {}
            temp['path'] = current_app.config.get(
                'FILES_REST_DEFAULT_PDF_SAVE_PATH')
            temp['pdf_ttl'] = current_app.config.get(
                'FILES_REST_DEFAULT_PDF_TTL')
            settings = AdminSettings.Dict2Obj(temp)

        return self.render(
            current_app.config["WEKO_ADMIN_FILE_PREVIEW_SETTINGS_TEMPLATE"],
            settings=settings
        )


class ItemExportSettingsView(BaseView):
    """Item export settings."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """File preview settings."""
        if request.method == 'POST':
            item_setting = request.form.get('item_export_radio', 'True')
            contents_setting = request.form.get('export_contents_radio', 'True')
            new_settings = {
                'allow_item_exporting': str_to_bool(item_setting),
                'enable_contents_exporting': str_to_bool(contents_setting)
            }

            try:
                AdminSettings.update('item_export_settings', new_settings)
                flash(_('Successfully Changed Settings'))
            except Exception as e:
                current_app.logger.error(
                    'ERROR Item Export Settings: {}'.format(e))
                flash(_('Failed To Change Settings'), 'error')

            return redirect(url_for('itemexportsettings.index'))

        return self.render(
            current_app.config['WEKO_ADMIN_ITEM_EXPORT_SETTINGS_TEMPLATE'],
            settings=self._get_current_settings()
        )

    def _get_current_settings(self):
        """Get current item export settings."""
        return AdminSettings.get('item_export_settings') or \
            AdminSettings.Dict2Obj(
                current_app.config['WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS'])


class SiteInfoView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        return self.render(
            current_app.config["WEKO_ADMIN_SITE_INFO"],
            enable_notify=current_app.config[
                "WEKO_ADMIN_ENABLE_LOGIN_INSTRUCTIONS"]
        )


class IdentifierSettingView(ModelView):
    """Pidstore Identifier admin view."""

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True
    create_template = WEKO_PIDSTORE_IDENTIFIER_TEMPLATE_CREATOR
    edit_template = WEKO_PIDSTORE_IDENTIFIER_TEMPLATE_EDITOR

    column_list = (
        'repository', 'jalc_doi', 'jalc_crossref_doi', 'jalc_datacite_doi',
        'ndl_jalc_doi',
        'suffix',
        'jalc_flag',
        'jalc_crossref_flag',
        'jalc_datacite_flag',
        'ndl_jalc_flag')

    column_searchable_list = (
        'repository', 'jalc_doi', 'jalc_crossref_doi', 'jalc_datacite_doi',
        'ndl_jalc_doi',
        'suffix')

    column_details_list = (
        'repository', 'jalc_doi', 'jalc_crossref_doi', 'jalc_datacite_doi',
        'ndl_jalc_doi',
        'suffix', 'created_userId', 'created_date', 'updated_userId',
        'updated_date')

    form_extra_fields = {
        'repo_selected': StringField('Repository Selector'),
    }

    form_create_rules = [rules.Header(_('Prefix')),
                         'repository',
                         'jalc_doi',
                         'jalc_crossref_doi',
                         'jalc_datacite_doi',
                         'ndl_jalc_doi',
                         rules.Header(_('Suffix')),
                         'suffix',
                         rules.Header(_('Enable/Disable')),
                         'jalc_flag',
                         'jalc_crossref_flag',
                         'jalc_datacite_flag',
                         'ndl_jalc_flag',
                         'repo_selected',
                         ]

    form_edit_rules = form_create_rules

    column_labels = dict(repository=_('Repository'), jalc_doi=_('JaLC DOI'),
                         jalc_crossref_doi=_('JaLC CrossRef DOI'),
                         jalc_datacite_doi=_('JaLC DataCite DOI'),
                         ndl_jalc_doi=_('NDL JaLC DOI'),
                         suffix=_('Semi-automatic Suffix')
                         )

    def _validator_halfwidth_input(form, field):
        """
        Valid input character set.

        :param form: Form used to create/update model
        :param field: Template fields contain data need validator
        """
        if field.data is None:
            return
        else:
            try:
                for inchar in field.data:
                    if unicodedata.east_asian_width(inchar) in 'FWA':
                        raise ValidationError(
                            _('Only allow half with 1-bytes character in '
                              'input'))
            except Exception as ex:
                raise ValidationError('{}'.format(ex))

    form_args = {
        'jalc_doi': {
            'validators': [_validator_halfwidth_input]
        },
        'jalc_crossref_doi': {
            'validators': [_validator_halfwidth_input]
        },
        'jalc_datacite_doi': {
            'validators': [_validator_halfwidth_input]
        },
        'ndl_jalc_doi': {
            'validators': [_validator_halfwidth_input]
        },
        'suffix': {
            'validators': [_validator_halfwidth_input]
        }
    }

    form_widget_args = {
        'jalc_doi': {
            'maxlength': 100,
            'readonly': True,
        },
        'jalc_crossref_doi': {
            'maxlength': 100,
            'readonly': True,
        },
        'jalc_datacite_doi': {
            'maxlength': 100,
            'readonly': True,
        },
        'ndl_jalc_doi': {
            'maxlength': 100,
            'readonly': True,
        },
        'suffix': {
            'maxlength': 100,
        }
    }

    form_overrides = {
        'repository': QuerySelectField,
    }

    def validate_form(self, form):
        """
        Custom validate the form on submit.

        :param form:
            Form to validate
        """
        if isinstance(form.repository.data, Community):
            id_list = []
            id_data = Identifier.query.all()
            for i in id_data:
                id_list.append(i.repository)

            if (form.repository.data.id in id_list) and \
                (form.action == 'create'
                 or form.repo_selected.data != form.repository.data.id):
                flash(_('Specified repository is already registered.'), 'error')
                return False
        return super(IdentifierSettingView, self).validate_form(form)

    def on_model_change(self, form, model, is_created):
        """
        Perform some actions before a model is created or updated.

        Called from create_model and update_model in the same transaction
        (if it has any meaning for a store backend).
        By default does nothing.

        :param form: Form used to create/update model
        :param model: Model that will be created/updated
        :param is_created: Will be set to True if model was created
            and to False if edited
        """
        # Update hidden data automation
        if is_created:
            model.created_userId = current_user.get_id()
            model.created_date = datetime.utcnow().replace(microsecond=0)
        model.updated_userId = current_user.get_id()
        model.updated_date = datetime.utcnow().replace(microsecond=0)
        model.repository = str(model.repository.id)

    def on_form_prefill(self, form, id):
        form.repo_selected.data = form.repository.data

    def create_form(self, obj=None):
        """
        Instantiate model delete form and return it.

        Override to implement custom behavior.
        The delete form originally used a GET request, so delete_form
        accepts both GET and POST request for backwards compatibility.

        :param obj: input object
        """
        return self._use_append_repository(
            super(IdentifierSettingView, self).create_form()
        )

    def edit_form(self, obj):
        """
        Instantiate model editing form and return it.

        Override to implement custom behavior.

        :param obj: input object
        """
        return self._use_append_repository_edit(
            super(IdentifierSettingView, self).edit_form(obj)
        )

    def _use_append_repository(self, form):
        form.repository.query_factory = self._get_community_list
        form.repo_selected.data = 'Root Index'
        setattr(form, 'action', 'create')
        return form

    def _use_append_repository_edit(self, form):
        form.repository.query_factory = self._get_community_list
        setattr(form, 'action', 'edit')
        return form

    def _get_community_list(self):
        try:
            query_data = Community.query.all()
            query_data.insert(0, Community(id='Root Index'))
        except Exception as ex:
            current_app.logger.debug(ex)
        return query_data


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

feedback_mail_adminview = {
    'view_class': FeedbackMailView,
    'kwargs': {
        'category': _('Statistics'),
        'name': _('Feedback Mail'),
        'endpoint': 'feedbackmail'
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

ranking_settings_adminview = {
    'view_class': RankingSettingsView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Ranking'),
        'endpoint': 'rankingsettings'
    }
}

search_settings_adminview = {
    'view_class': SearchSettingsView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Search'),
        'endpoint': 'searchsettings'
    }
}

site_license_settings_adminview = {
    'view_class': SiteLicenseSettingsView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Site License'),
        'endpoint': 'sitelicensesettings'
    }
}

site_license_send_mail_settings_adminview = {
    'view_class': SiteLicenseSendMailSettingsView,
    'kwargs': {
        'category': _('Statistics'),
        'name': _('Site License'),
        'endpoint': 'sitelicensesendmail'
    }
}

file_preview_settings_adminview = {
    'view_class': FilePreviewSettingsView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('File Preview'),
        'endpoint': 'filepreview'
    }
}

item_export_settings_adminview = {
    'view_class': ItemExportSettingsView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Item Export'),
        'endpoint': 'itemexportsettings'
    }
}

site_info_settings_adminview = {
    'view_class': SiteInfoView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Site Info'),
        'endpoint': 'site_info'
    }
}

identifier_adminview = dict(
    modelview=IdentifierSettingView,
    model=Identifier,
    category=_('Setting'),
    name=_('Identifier'),
    endpoint='identifier'
)

__all__ = (
    'style_adminview',
    'report_adminview',
    'feedback_mail_adminview',
    'language_adminview',
    'web_api_account_adminview',
    'stats_settings_adminview',
    'log_analysis_settings_adminview',
    'ranking_settings_adminview',
    'search_settings_adminview',
    'site_license_settings_adminview',
    'site_license_send_mail_settings_adminview',
    'file_preview_settings_adminview',
    'item_export_settings_adminview',
    'site_info_settings_adminview',
    'identifier_adminview'
)
