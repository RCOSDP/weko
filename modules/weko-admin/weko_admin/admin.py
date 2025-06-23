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
import traceback
import unicodedata
import ipaddress
from datetime import datetime, timedelta

from flask import abort, current_app, flash, jsonify, make_response, \
    redirect, render_template, request, url_for
from markupsafe import Markup
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.form import rules
from flask_admin.helpers import get_redirect_target
from flask_babelex import gettext as _
from flask_login import current_user
from flask_mail import Attachment
from flask_wtf import FlaskForm,Form
from sqlalchemy.exc import SQLAlchemyError
from invenio_communities.models import Community
from invenio_accounts.models import User
from invenio_db import db
from invenio_files_rest.storage.pyfs import remove_dir_with_file
from invenio_mail.api import send_mail
from weko_index_tree.models import IndexStyle
from weko_records.api import ItemTypes, SiteLicense, ItemTypeNames, JsonldMapping
from weko_records.models import SiteLicenseInfo, ItemTypeJsonldMapping
from weko_records_ui.utils import check_items_settings
from weko_schema_ui.models import PublishStatus
from weko_search_ui.mapper import JsonLdMapper
from weko_swordserver.models import SwordClientModel
from weko_swordserver.api import SwordClient
from weko_workflow.api import WorkFlow, WorkActivity
from wtforms.fields import StringField
from wtforms.validators import ValidationError
from weko_items_autofill.config import WEKO_ITEMS_AUTOFILL_API_LIST
from invenio_oauth2server.models import Client
from invenio_accounts.models import User

from .config import WEKO_PIDSTORE_IDENTIFIER_TEMPLATE_CREATOR, \
    WEKO_PIDSTORE_IDENTIFIER_TEMPLATE_EDITOR, WEKO_ADMIN_SWORD_API_JSONLD_TEMPLATE, \
    WEKO_ADMIN_SWORD_API_JSONLD_MAPPING_TEMPLATE
from .models import AdminSettings, FacetSearchSetting, Identifier, \
    LogAnalysisRestrictedCrawlerList, LogAnalysisRestrictedIpAddress, \
    RankingSettings, SearchManagement, StatisticsEmail
from .permissions import admin_permission_factory ,superuser_access
from .utils import get_facet_search, get_item_mapping_list, \
    get_response_json, get_restricted_access, get_search_setting, get_detail_search_list
from .utils import get_user_report_data as get_user_report
from .utils import package_reports, str_to_bool
from .tasks import is_reindex_running ,reindex

class ReindexElasticSearchView(BaseView):

    @expose('/', methods=['GET'])
    @superuser_access.require(http_exception=403)
    def index(self):
        """
        show view Maintenance/ElasticSearch

        Returns:
            'weko_admin/admin/reindex_elasticsearch.html'
        """
        try:
            status =  self._check_reindex_is_running()
            is_error = status.get("isError")
            is_executing = status.get("isExecuting")
            disabled_btn = status.get("disabled_Btn")

            return self.render(
                template=current_app.config['WEKO_ADMIN_REINDEX_ELASTICSEARCH_TEMPLATE']
                ,isError=is_error
                ,isExecuting=is_executing
                ,disabled_Btn=disabled_btn
            )
        except BaseException:
            estr = traceback.format_exc()
            current_app.logger.error('Unexpected error: {}'.format( estr ))
            return abort(500)

    @expose('/reindex', methods=['POST'])
    @superuser_access.require(http_exception=403)
    def reindex(self):
        """
        Processing when "Executing Button" is pressed

        Args:
        is_db_to_es : boolean (GET paramater)
            if True,  index Documents from DB data
            if False, index Documents from ES data itself

        Returns:
            responce json text and responce code

        Todo:
        if you change this codes or operating, please keep in mind Todo of the method "elasticsearch_reindex"
        in .utils.py .
        """


        try:
            ## exclusion check
            status =  self._check_reindex_is_running()
            is_error = status.get("isError")
            is_executing = status.get("isExecuting")
            if is_error:
                return jsonify({"error" : _('haserror')}) , 400
            if is_executing:
                return jsonify({"error" : _('executing...')}) , 400

            is_db_to_es=request.args.get('is_db_to_es') == 'true'
            # execute in celery task
            res = reindex.apply_async(args=(is_db_to_es,))
            res_output = res.get() #wait until celery task finish
            current_app.logger.info(res_output)
            return jsonify({"responce" : _('completed')}), 200

        except BaseException:
            estr = traceback.format_exc()
            current_app.logger.error('Unexpected error: {}'.format( estr ))
            AdminSettings.update(current_app.config['WEKO_ADMIN_SETTINGS_ELASTIC_REINDEX_SETTINGS']
            , dict({current_app.config['WEKO_ADMIN_SETTINGS_ELASTIC_REINDEX_SETTINGS_HAS_ERRORED']:True}))
            return jsonify({"error" : estr }), 500

    @expose('/is_reindex_running', methods=['GET'])
    @superuser_access.require(http_exception=403)
    def check_reindex_is_running(self):
        """
        Monitor whether the reindex process is running/error is occurred
        by Celery task and admin_settings

        Returns:
            str : View state json text
                isError      : boolean
                isExecuting  : boolean
                disabled_Btn : boolean

        """
        try:
            return jsonify(self._check_reindex_is_running())
        except BaseException:
            estr = traceback.format_exc()
            current_app.logger.error('Unexpected error: {}'.format( estr ))
            return abort(500)

    def _check_reindex_is_running(self):
        """
        Monitor whether the reindex process is running/error is occurred
        by Celery task and admin_settings
        """
        ELASTIC_REINDEX_SETTINGS = current_app.config['WEKO_ADMIN_SETTINGS_ELASTIC_REINDEX_SETTINGS']
        HAS_ERRORED = current_app.config['WEKO_ADMIN_SETTINGS_ELASTIC_REINDEX_SETTINGS_HAS_ERRORED']

        admin_setting = AdminSettings.get(ELASTIC_REINDEX_SETTINGS,False)
        is_error = admin_setting.get(HAS_ERRORED)
        is_executing = is_reindex_running()
        result = dict({
            "isError": is_error
            ,"isExecuting": is_executing
            ,"disabled_Btn": is_error or is_executing
        })
        return result



# FIXME: Change all setting views' path to be under settings/
class StyleSettingView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Block style setting page."""
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
            current_app.logger.error(
                "Unexpected error: {}".format(sys.exc_info()))
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
            current_app.logger.error(
                "Unexpected error: {}".format(sys.exc_info()))
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
            current_app.logger.error(
                "Unexpected error: {}".format(sys.exc_info()))
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
            current_app.logger.error(
                "Unexpected error: {}".format(sys.exc_info()))
            abort(500)
        return checksum1 == checksum2


class ReportView(BaseView):
    """Report view."""

    @expose('/', methods=['GET'])
    def index(self):
        from invenio_stats.utils import get_aggregations
        from weko_index_tree.api import Indexes

        is_super = any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in current_user.roles)
        if is_super:
            repositories = [{"id": "Root Index"}] + \
                [com.to_dict() for com in Community.query.all()]
        else:
            repositories = [com.to_dict() for com in Community.get_repositories_by_user(current_user)]

        repo_id = request.args.get('repo_id')
        if repo_id:
            if repo_id not in [r.get("id") for r in repositories]:
                abort(403)
        else:
            repo_id = repositories[0]["id"] if repositories else None

        try:
            indexes = Indexes.get_public_indexes_list()
            if repo_id and repo_id != "Root Index":
                repository = Community.query.get(repo_id)
                community_indexes = Indexes.get_child_list_recursive(repository.root_node_id)
                indexes = list(set(indexes) & set(community_indexes))

            indexes_query = []

            if indexes:
                indexes_num = len(indexes)
                div_indexes = []
                max_clause_count = current_app.config.get(
                    'OAISERVER_ES_MAX_CLAUSE_COUNT', 1024)
                for div in range(0, int(indexes_num / max_clause_count) + 1):
                    e_right = div * max_clause_count
                    e_left = (div + 1) * max_clause_count \
                        if indexes_num > (div + 1) * max_clause_count \
                        else indexes_num
                    div_indexes.append({
                        "terms": {
                            "path": indexes[e_right:e_left]
                        }
                    })
                indexes_query.append({
                    "bool": {
                        "should": div_indexes
                    }
                })

            aggs_query = {
                "size": 0,
                "aggs": {
                    "aggs_public": {
                        "filter": {
                            "bool": {
                                "must": [
                                    {
                                        "term": {
                                            "publish_status": PublishStatus.PUBLIC.value
                                        }
                                    },
                                    {
                                        "range": {
                                            "publish_date": {
                                                "lte": "now/d"
                                            }
                                        }
                                    }
                                ],
                                "should": indexes_query
                            }
                        }
                    }
                },
                "query": {
                    "bool": {
                        "must": [
                            {
                                "term":
                                {
                                    "relation_version_is_last": True
                                }
                            },
                            {
                                "exists":
                                {
                                    "field": "path"
                                }
                            },
                            {
                                "terms":
                                {
                                    "publish_status": [
                                        PublishStatus.PUBLIC.value,
                                        PublishStatus.PRIVATE.value
                                    ]
                                }
                            }
                        ]
                    }
                }
            }

            if repo_id and repo_id != "Root Index":
                aggs_query["query"]["bool"]["should"] = {"terms": {"path": community_indexes}}
                aggs_query["query"]["bool"]["minimum_should_match"] = 1

            aggs_results = get_aggregations(
                current_app.config['SEARCH_UI_SEARCH_INDEX'], aggs_query)

            result = {
                'total': 0,
                'open': 0,
                'private': 0
            }
            if aggs_results and aggs_results.get(
                    'aggregations', {}).get('aggs_public'):
                result = {
                    'total': aggs_results['hits']['total'],
                    'open': aggs_results['aggregations'][
                        'aggs_public']['doc_count']
                }
                result['private'] = result['total'] - result['open']


            settings = AdminSettings.get(
                name='report_email_schedule_settings',
                dict_to_object=False)
            current_schedule = None
            if settings:
                current_schedule = settings.get(repo_id)
            if not current_schedule:
                current_schedule = current_app.config['WEKO_ADMIN_REPORT_DELIVERY_SCHED']

            # Emails to send reports to
            all_email_address = StatisticsEmail.query.filter_by(repository_id=repo_id).all()

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
                    'WEKO_ADMIN_REPORT_FREQUENCIES'],
                repositories=repositories,
                selected_repo_id=repo_id
            )
        except Exception as e:
            traceback.print_exc()
            current_app.logger.error("Unexpected error: {}".format(e))
        return abort(400)

    @expose('/stats_file_output', methods=['POST'])
    def get_file_stats_output(self):
        """Get file download/preview stats report."""
        stats_json = json.loads(request.form.get('report'))
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
                ret = send_mail(subject, recepients,
                                html=html_body,
                                attachments=attachments)
                if ret:
                    flash(ret, 'error')
                else:
                    flash(
                        _('Successfully sent the reports to the recepients.'))
            else:
                resp = make_response()
                resp.data = zip_stream.getvalue()
                resp.headers['Content-Type'] = 'application/x-zip-compressed'
                resp.headers['Content-Disposition'] = 'attachment; filename='\
                                                      + zip_name
                return resp
        except Exception as e:
            current_app.logger.error("Unexpected error: {}".format(e))
            flash(_('Unexpected error occurred.'), 'error')
        return redirect(url_for('report.index'))

    @expose('/user_report_data', methods=['GET'])
    def get_user_report_data(self):
        """Get user report data from db and modify."""
        repository_id = request.args.get('repository_id')
        return jsonify(get_user_report(repo_id=repository_id))

    @expose('/set_email_schedule', methods=['POST'])
    def set_email_schedule(self):
        """Set new email schedule."""
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
            repository_id = request.form.get('repository_select')
            settings = AdminSettings.get('report_email_schedule_settings', False)
            if not settings:
                settings = {}
            settings[repository_id] = schedule
            AdminSettings.update('report_email_schedule_settings', settings)
            flash(_('Successfully Changed Schedule.'), 'error')
        except Exception as ex:
            traceback.print_exc()
            flash(_('Could Not Save Changes.'), 'error')
        return redirect(url_for('report.index'))

    @expose('/get_email_address', methods=['POST'])
    def get_email_address(self):
        """Save Email Address."""
        input_email = request.form.getlist('inputEmail')
        repo_select = request.form.get('repository_select')
        StatisticsEmail.delete_by_repo(repo_select)
        alert_msg = 'Successfully saved email addresses.'
        category = 'info'
        for input in input_email:
            if input:
                match = re.match(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+('
                                 r'\.[a-z0-9-]+)*(\.[a-z]{2,4})$', input)
                if match:
                    StatisticsEmail.insert_email_address(input, repo_select)
                else:
                    alert_msg = 'Please check email input fields.'
                    category = 'error'
                    current_app.logger.error(alert_msg)
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
        if request.method == 'POST':
            display_setting = True if request.form.get(
                'record_stats_radio') == 'True' else False
            AdminSettings.update('display_stats_settings',
                                 {'display_stats': display_setting})
            flash(_('Successfully Changed Settings.'))
            return redirect(url_for('statssettings.index'))

        current_display_setting = True  # Default
        display_setting = AdminSettings.get(
            name='display_stats_settings',
            dict_to_object=False)
        if display_setting:
            current_display_setting = display_setting.get('display_stats')

        return self.render(
            current_app.config["WEKO_ADMIN_STATS_SETTINGS_TEMPLATE"],
            display_stats=current_display_setting)


class LogAnalysisSettings(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        form = FlaskForm(request.form)
        if request.method == 'POST' and form.validate():
            crawler_lists, new_ip_addresses = self.parse_form_data(
                request.form)
            try:
                LogAnalysisRestrictedIpAddress.update_table(new_ip_addresses)
                LogAnalysisRestrictedCrawlerList.update_or_insert_list(
                    crawler_lists)
                flash(_('Successfully Changed Settings.'))
            except Exception as e:
                current_app.logger.error(
                    'Could not save restricted data: {}'.format(e))
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
            current_app.logger.error(_('Could not get restricted data: %s'), e)
            flash(_('Could not get restricted data.'), 'error')
            restricted_ip_addresses = []
            shared_crawlers = []

        return self.render(
            current_app.config["WEKO_ADMIN_LOG_ANALYSIS_SETTINGS_TEMPLATE"],
            restricted_ip_addresses=restricted_ip_addresses,
            shared_crawlers=shared_crawlers,
            form = form
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
        f = FlaskForm(request.form)
        if request.method == 'POST' and f.validate():
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
                    new_statistical_period = int(request.form.get('statistical_period',
                                                                  365))
                    if new_statistical_period < 1 or new_statistical_period > 3650:
                        current_app.logger.debug(new_statistical_period)
                        raise
                    settings.statistical_period = new_statistical_period
                    new_display_rank = int(request.form.get('display_rank',
                                                            10))
                    if new_display_rank < 1 or new_display_rank > 100:
                        current_app.logger.debug(new_display_rank)
                        raise
                    settings.display_rank = new_display_rank
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
            rankings=rankings,
            form=f
        )


class SearchSettingsView(BaseView):
    """Search settings view."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Site license setting page."""
        search_setting = get_search_setting()
        # get search author setting
        check_items_settings()
        search_author_flg = 'name'
        if 'ITEM_SEARCH_FLG' in current_app.config:
            search_author_flg = current_app.config['ITEM_SEARCH_FLG']
        search_setting['search_author_flg'] = search_author_flg
        # get index tree style setting
        style = IndexStyle.get(
            current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
        width = style.width if style else '3'
        height = style.height if style else None
        search_setting['index_tree_style'] = {
            'width_options': current_app.config[
                'WEKO_INDEX_TREE_STYLE_OPTIONS']['widths'],
            'width': width,
            'height': height
        }
        # dump json string
        result = json.dumps(copy.deepcopy(search_setting))
        if 'POST' in request.method:
            jfy = {}
            try:
                # get requset data
                db_data = request.get_json()

                # update search author setting to db
                if 'search_author_flg' in db_data:
                    search_author_flg = db_data.pop('search_author_flg')
                    settings = AdminSettings.get('items_display_settings')
                    settings.items_search_author = search_author_flg
                    AdminSettings.update('items_display_settings',
                                         settings.__dict__)
                # update index tree style setting
                if 'index_tree_style' in db_data:
                    index_tree_style = db_data.pop('index_tree_style')
                    width = index_tree_style.get('width', '3')
                    height = index_tree_style.get('height', None)
                    if style:
                        IndexStyle.update(
                            current_app.config[
                                'WEKO_INDEX_TREE_STYLE_OPTIONS']['id'],
                            width=width,
                            height=height)
                    else:
                        IndexStyle.create(
                            current_app.config[
                                'WEKO_INDEX_TREE_STYLE_OPTIONS']['id'],
                            width=width,
                            height=height)
                # update other search settings
                res = SearchManagement.get()
                if res:
                    id = res.id
                    SearchManagement.update(id, db_data)
                else:
                    SearchManagement.create(db_data)
                jfy['status'] = 201
                jfy['message'] = 'Search setting was successfully updated.'
            except BaseException as e:
                current_app.logger.error('Could not save search settings: {}'.format(e))
                jfy['status'] = 500
                jfy['message'] = 'Failed to update search setting.'
            return make_response(jsonify(jfy), jfy['status'])

        try:
            lists = ItemTypes.get_latest()  # ItemTypes.get_all()
            return self.render(
                current_app.config['WEKO_ADMIN_SEARCH_MANAGEMENT_TEMPLATE'],
                widths=current_app.config[
                    'WEKO_INDEX_TREE_STYLE_OPTIONS']['widths'],
                setting_data=result,
                lists=lists,
            )
        except BaseException as e:
            current_app.logger.error('Could not save search settings: {}'.format(e))
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
                                    addr_check = '.'.join(item)
                                    try:
                                        ip_check = ipaddress.ip_address(addr_check)
                                    except ValueError:
                                        err_addr = True
                                        break
                                if err_addr:
                                    # break for addresses
                                    break
                        if err_addr:
                            current_app.logger.error("IP Address is incorrect")
                            raise ValueError('IP Address is incorrect')

                SiteLicense.update(data)
                db.session.commit()
                jfy['status'] = 201
                jfy['message'] = 'Site license was successfully updated.'
            except Exception as ex:
                db.session.rollback()
                current_app.logger.error('Failed to update site license: {}'.format(ex))
                traceback.print_exc()
                jfy['status'] = 500
                jfy['message'] = 'Failed to update site license.'
            return make_response(jsonify(jfy), jfy['status'])

        try:
            # site license list
            result_list = SiteLicense.get_records(user=current_user)
            # item types list
            n_lst = ItemTypes.get_latest()
            result = get_response_json(result_list, n_lst)
            return self.render(
                current_app.config['WEKO_ADMIN_SITE_LICENSE_TEMPLATE'],
                result=json.dumps(result))
        except BaseException as e:
            current_app.logger.error('Could not save site license settings {}'.format(e))
            abort(500)


class SiteLicenseSendMailSettingsView(BaseView):
    """Site-License send mail settings."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        repository_id = None
        if request.method == 'POST':
            data = request.get_json()
            settings = AdminSettings.get('site_license_mail_settings', False)
            new_settings = settings.copy()
            repository_id = data['repository_id']
            new_settings[repository_id]={'auto_send_flag': data['auto_send_flag']}
            AdminSettings.update('site_license_mail_settings',
                                 new_settings)
            for name in data['checked_list']:
                sitelicense = SiteLicenseInfo.query.filter_by(
                    organization_name=name).first()
                if sitelicense:
                    sitelicense.receive_mail_flag = data['checked_list'][name]
                    try:
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        current_app.logger.error(e)

        if any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in current_user.roles):
            repositories = [{"id": "Root Index"}] + Community.query.all()
            if repository_id is None:
                repository_id = "Root Index"
        else:
            repositories = Community.get_repositories_by_user(current_user)
            if repository_id is None:
                repository_id = repositories[0].id if repositories else None

        sitelicenses = SiteLicenseInfo.query.filter_by(repository_id=repository_id).order_by(
                    SiteLicenseInfo.organization_id).all()
        settings = AdminSettings.get('site_license_mail_settings', False)
        setting = settings.get(repository_id) if settings else {}
        auto_send = setting.get("auto_send_flag", False) if setting else False

        now = datetime.utcnow()
        last_month = (now.replace(day=1) - timedelta(days=1)).replace(day=1)

        return self.render(
            current_app.config['WEKO_ADMIN_SITE_LICENSE_SEND_MAIL_TEMPLATE'],
            sitelicenses=sitelicenses,
            auto_send=auto_send,
            now=now,
            last_month=last_month,
            repositories=repositories
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
            contents_setting = request.form.get(
                'export_contents_radio',
                'True')
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
    # use flask-wtf CSRF protection
    form_base_class = Form

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
                flash(_('Specified repository is already registered.'),
                      'error')
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
        query_data = []
        try:
            query_data = Community.query.all()
            query_data.insert(0, Community(id='Root Index'))
        except Exception as ex:
            current_app.logger.debug(ex)
        return query_data


class RestrictedAccessSettingView(BaseView):
    """Restricted Access Setting admin view."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        _restricted_access = get_restricted_access()
        _restricted_access["restricted_access_display_flag"] = current_app.config[
            "WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG"]
        return self.render(
            current_app.config[
                "WEKO_ADMIN_RESTRICTED_ACCESS_SETTINGS_TEMPLATE"],
            data=json.dumps(_restricted_access),
            items_per_page=current_app.config[
                "WEKO_ADMIN_ITEMS_PER_PAGE_USAGE_REPORT_REMINDER"],
            maxint=current_app.config["WEKO_ADMIN_RESTRICTED_ACCESS_MAX_INTEGER"]
        )


class FacetSearchSettingView(ModelView):
    """Facet Search view."""

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    column_list = (
        'id',
        'name_en',
        'name_jp',
        'mapping',
        'ui_type',
        'active',
    )
    column_searchable_list = (
        'id',
        'name_en',
        'name_jp',
        'mapping',
        'ui_type',
        'active',
    )

    column_filters = (
        'id',
        'name_en',
        'name_jp',
        'mapping',
        'ui_type',
        'active',
    )
    column_labels = dict(
        id=_('ID'),
        name_en=_('Item Name(EN)'),
        name_jp=_('Item Name(JP)'),
        mapping=_('Mapping'),
        ui_type=_('UI'),
        active=_('Active')
    )

    def search_placeholder(self):
        """Return search placeholder."""
        return 'Search'

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        return_url = get_redirect_target() or self.get_url('.index_view')
        if not self.can_create:
            return redirect(return_url)
        facet_search = get_facet_search()
        facet_search.update({'mapping_list': get_item_mapping_list()})
        facet_search.update({'detail_condition': get_detail_search_list()})
        return self.render(
            current_app.config['WEKO_ADMIN_FACET_SEARCH_SETTING_TEMPLATE'],
            data=json.dumps(facet_search),
            type_str='new'
        )

    @expose('/edit/<int:id>', methods=['GET', 'POST'])
    def edit_view(self, id=None):
        return_url = get_redirect_target() or self.get_url('.index_view')
        if not self.can_edit:
            return redirect(return_url)
        facet_search = get_facet_search(id=id)
        facet_search.update({'mapping_list': get_item_mapping_list()})
        facet_search.update({'detail_condition': get_detail_search_list()})
        return self.render(
            current_app.config['WEKO_ADMIN_FACET_SEARCH_SETTING_TEMPLATE'],
            data=json.dumps(facet_search),
            type_str='edit',
            id=id
        )

    @expose('/details/<int:id>', methods=['GET', 'POST'])
    def details_view(self, id=None):
        return_url = get_redirect_target() or self.get_url('.index_view')
        if not self.can_edit:
            return redirect(return_url)
        facet_search = get_facet_search(id=id)
        facet_search.update({'mapping_list': get_item_mapping_list()})
        #facet_search.update({'detail_condition': get_detail_search_list()})
        return self.render(
            current_app.config['WEKO_ADMIN_FACET_SEARCH_SETTING_TEMPLATE'],
            data=json.dumps(facet_search),
            type_str='details',
            id=id
        )

    @expose('/delete/', methods=['GET', 'POST'])
    @expose('/delete/<int:id>', methods=['GET', 'POST'])
    def delete(self, id=None):
        """Soft-delete an Facet Search."""
        return_url = get_redirect_target() or self.get_url('.index_view')
        if not self.can_delete:
            return redirect(return_url)
        if not id:
            id = request.form.get('id')
        facet_search = get_facet_search(id=id)
        return self.render(
            current_app.config['WEKO_ADMIN_FACET_SEARCH_SETTING_TEMPLATE'],
            data=json.dumps(facet_search),
            type_str='delete',
            id=id
        )


class SwordAPISettingsView(BaseView):
    """SWORD API TSV/CSV and XML Settings admin view."""
    @expose("/", methods=["GET","POST"])
    def index(self):
        """Each metadata format settings."""
        TSVCSV = "TSV/CSV"
        XML = "XML"
        page_type = TSVCSV
        if request.args.get("tab") == "xml":
            page_type = XML

        if request.method == "GET":
            # GET
            default_settings = {
                TSVCSV: {
                    "active": True,
                    "registration_type": "Direct",
                    "duplicate_check": False,
                },
                XML: {
                    "active": False,
                    "registration_type": "Workflow",
                    "workflow": "-1",
                    "duplicate_check": False,
                }
            }  # Default
            current_settings = AdminSettings.get("sword_api_setting", False)
            if not current_settings:
                AdminSettings.update("sword_api_setting", default_settings)
                current_settings = default_settings
                current_app.logger.info(
                    "Create default settings for SWORD API settings."
                )

            current_settings_json = json.dumps(current_settings)
            if "default_format" in current_settings:
                # old format fix
                current_settings = AdminSettings.get("sword_api_setting", False)
                tsvcsv_registration_type = current_settings["data_format"]["TSV"]["register_format"]
                xml_registration_type = current_settings["data_format"]["XML"]["register_format"]
                xml_workflow = current_settings["data_format"]["XML"]["workflow"]

                new_settings = {
                    TSVCSV: {
                        "active": True,
                        "registration_type": tsvcsv_registration_type,
                        "duplicate_check": False,
                    },
                    XML: {
                        "active": False,
                        "registration_type": xml_registration_type,
                        "workflow": xml_workflow,
                        "duplicate_check": False,
                    }
                }
                AdminSettings.update("sword_api_setting", new_settings)
                current_app.logger.info(
                    "Update SWORD API settings to new format."
                )
                current_settings = new_settings
                current_settings_json = json.dumps(current_settings)

            form = FlaskForm(request.form)
            workflow = WorkFlow()
            workflow_list = workflow.get_workflow_list()
            reduce_workflows = workflow.reduce_workflows_for_registration(workflow_list)
            workflows = workflow.get_workflows_by_roles(reduce_workflows)
            deleted_workflows = workflow.get_deleted_workflow_list()
            deleted_workflow_name_dict = {
                deleted_workflow.id: deleted_workflow.flows_name
                for deleted_workflow in deleted_workflows
            }

            # Process exclude workflows
            from weko_workflow.utils import exclude_admin_workflow
            exclude_admin_workflow(workflows)

            active_value = ""
            workflow_value = ""
            duplicate_check_value = ""
            if page_type == XML:
                if current_settings[XML]["active"] == True:
                    active_value = "checked"
                registration_type_value = current_settings[XML]["registration_type"]
                workflow_value = current_settings[XML]["workflow"]
                if current_settings[XML]["duplicate_check"] == True:
                    duplicate_check_value = "checked"
            else:
                if current_settings[TSVCSV]["active"] == True:
                    active_value = "checked"
                registration_type_value = current_settings[TSVCSV]["registration_type"]
                if current_settings[TSVCSV]["duplicate_check"] == True:
                    duplicate_check_value = "checked"

            return self.render(
                current_app.config["WEKO_ADMIN_SWORD_API_TEMPLATE"],
                current_settings = current_settings,
                current_settings_json = current_settings_json,
                deleted_workflow_name_dict = json.dumps(deleted_workflow_name_dict),
                workflows = workflows,
                form = form,
                page_type = page_type,
                active_value = active_value,
                registration_type_value = registration_type_value,
                workflow_value = workflow_value,
                duplicate_check_value = duplicate_check_value
            )
        else:
            # POST
            current_settings = AdminSettings.get("sword_api_setting", False)

            active = request.json.get("active")
            registration_type = request.json.get("registration_type")
            workflow = request.json.get("workflow")
            duplicate_check = request.json.get("duplicate_check")

            current_settings.update({
                page_type: {
                    "active": active,
                    "registration_type": registration_type,
                    "workflow": workflow,
                    "duplicate_check": duplicate_check
                }
            })
            AdminSettings.update("sword_api_setting", current_settings)
            current_app.logger.info(
                "Update settings for Sword API: {}".format(page_type)
            )
            return jsonify(success=True),200


class SwordAPIJsonldSettingsView(ModelView):
    """SWORD API JSON-LD Settings admin view."""
    form_base_class = Form

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    column_display_all_relations = True
    create_template = WEKO_ADMIN_SWORD_API_JSONLD_TEMPLATE
    edit_template = WEKO_ADMIN_SWORD_API_JSONLD_TEMPLATE

    column_labels = {
        "oauth_client.name": _("Application"),
        "oauth_client.user.email": _("Creator"),
        "registration_type_id": _("Registration Type"),
        "mapping.name": _("Mapping"),
        "workflow.flows_name": _("Workflow"),

    }
    column_list = (
        "oauth_client.name",
        "active",
        "oauth_client.user.email",
        "registration_type_id",
        "metadata_collection",
        "duplicate_check"
    )
    column_filters = (
        "oauth_client.name",
        "active",
        "oauth_client.user.email",
        "registration_type_id",
        "duplicate_check",
    )
    column_details_list = (
        "id",
        "created",
        "updated",
        "oauth_client.name",
        "active",
        "registration_type_id",
        "workflow.flows_name",
        "mapping.name",
        "duplicate_check",
        "meta_data_api",
    )

    def _format_active(view, context, model, name):
        if model.active:
            return _("Active Message")
        else:
            return _("Inactive Message")

    def _format_registration_type(view, context, model, name):
        if not isinstance(model, SwordClientModel):
            return ""
        if model.registration_type == "Direct":
            return _("Direct_Registration")
        elif model.registration_type == "Workflow":
            return _("WorkFlow_Registration")
        else:
            return ""

    def _format_metadata_collection(view, context, model, name):
        if len(model.meta_data_api) > 0:
            return _("Active Message")
        else:
            return _("Inactive Message")

    def _format_duplicate_check(view, context, model, name):
        if model.duplicate_check:
            return _("Active Message")
        else:
            return _("Inactive Message")

    column_formatters = {
        "active": _format_active,
        "registration_type_id": _format_registration_type,
        "metadata_collection": _format_metadata_collection,
        "duplicate_check": _format_duplicate_check,
        "created": lambda v, c, m, n: m.created.strftime("%Y-%m-%d %H:%M:%S"),
        "updated": lambda v, c, m, n: m.updated.strftime("%Y-%m-%d %H:%M:%S"),
    }
    column_sortable_list = ()
    column_searchable_list = (
        "oauth_client.name",
        "oauth_client.user.email",
    )

    def get_query(self):
        """Get query for SWORD API JSON-LD settings."""
        query = super().get_query().order_by(SwordClientModel.id)
        list_role = [role.name for role in current_user.roles]
        if current_app.config["WEKO_ADMIN_PERMISSION_ROLE_SYSTEM"] not in list_role:
            query = (
                query.join(Client)
                .filter(Client.client_id == SwordClientModel.client_id)
                .filter(Client.user_id == current_user.get_id())
            )
        return query

    def get_count_query(self):
        """Get count query for SWORD API JSON-LD settings."""
        query = super().get_count_query()
        list_role = [role.name for role in current_user.roles]
        if current_app.config["WEKO_ADMIN_PERMISSION_ROLE_SYSTEM"] not in list_role:
            query = (
                query.join(Client)
                .filter(Client.client_id == SwordClientModel.client_id)
                .filter(Client.user_id == current_user.get_id())
            )
        return query

    @expose("/add/", methods=["GET", "POST"])
    def create_view(self):
        """Create new SWORD API JSON-LD settings."""
        if request.method == "GET":
            # GET
            form = FlaskForm(request.form)

            # GET current user oauth clients
            list_cur_user_client = [
                client
                for client in Client.get_by_user_id(current_user.get_id())
                # exclude personal clients
                if not client.is_internal
            ]
            list_sword_clients = SwordClient.get_client_id_all()
            # exclude already registered clients
            client_list = [
                client for client in list_cur_user_client
                if client.client_id not in list_sword_clients
            ]

            # GET metadata api
            metadata_api = []
            metadata_api.extend(
                current_app.config.get("WEKO_ITEMS_AUTOFILL_API_LIST", []).copy()
            )
            metadata_api.append("Original")

            # GET workflow
            workflow = WorkFlow()
            workflow_list = workflow.get_workflow_list()
            reduce_workflows = workflow.reduce_workflows_for_registration(workflow_list)
            workflows = workflow.get_workflows_by_roles(reduce_workflows)
            deleted_workflows = workflow.get_deleted_workflow_list()
            deleted_workflow_name_dict = {}
            for deleted_workflow in deleted_workflows:
                deleted_workflow_name_dict[deleted_workflow.id] = deleted_workflow.flows_name
            # Process exclude workflows
            from weko_workflow.utils import exclude_admin_workflow
            exclude_admin_workflow(workflows)

            # All mapping
            jsonld_mappings = [
                {
                    "id": mapping.id,
                    "name": mapping.name,
                    "item_type_id": mapping.item_type_id
                } for mapping in JsonldMapping.get_all()
            ]

            # All ItemTypeNames
            item_type_names = [
                {"id": item_type.id, "name": item_type.name}
                for item_type in ItemTypeNames.get_name_and_id_all()
            ]

            return self.render(
                self.create_template,
                form=form,
                client_list=client_list,
                active_value="checked",
                metadata_api=metadata_api,
                deleted_workflow_name_dict=json.dumps(deleted_workflow_name_dict),
                workflows=workflows,
                jsonld_mappings=jsonld_mappings,
                current_page_type="add",
                current_client_name=None,
                current_model_json=None,
                can_edit=True,
                item_type_names=item_type_names,
            )
        else:
            # POST
            try:
                client_id = request.json.get("application")
                if request.json.get("registration_type") == "Direct":
                    registration_type_id = SwordClientModel.RegistrationType.DIRECT
                    workflow_id = None
                else:
                    registration_type_id = SwordClientModel.RegistrationType.WORKFLOW
                    workflow_id = request.json.get("workflow_id")
                mapping_id = request.json.get("mapping_id")
                active = request.json.get("active") == "True"
                duplicate_check = request.json.get("duplicate_check") == "True"
                meta_data_api = request.json.get("metadata_api_selected")
                if meta_data_api and "Original" not in meta_data_api:
                    msg = "Cannot disable 'Original'."
                    current_app.logger.error(msg)
                    return jsonify({"error": msg}), 400
                obj = JsonldMapping.get_mapping_by_id(mapping_id)
                try:
                    if not JsonLdMapper(obj.item_type_id, obj.mapping).is_valid:
                        msg = f"Invalid jsonld mapping."
                        current_app.logger.error(msg)
                        return jsonify({"error": msg}), 400
                except Exception as ex:
                    msg = f"Failed to validate jsonld mapping."
                    current_app.logger.error(msg)
                    traceback.print_exc()
                    return jsonify({"error": msg}), 400

                obj = SwordClient.register(
                    client_id=client_id,
                    registration_type_id=registration_type_id,
                    mapping_id=mapping_id,
                    workflow_id=workflow_id,
                    active=active,
                    duplicate_check=duplicate_check,
                    meta_data_api=meta_data_api
                )
                current_app.logger.info(
                    f"Create settings for Sword API: {obj.oauth_client.name}"
                )
                return jsonify(results=True), 200

            except SQLAlchemyError as ex:
                db.session.rollback()
                msg = "Failed to create application settings."
                current_app.logger.error(msg)
                traceback.print_exc()
                return jsonify({"error": msg}), 400


    @expose("/edit/<string:id>/", methods=["GET", "POST"])
    def edit_view(self, id):
        """Edit SWORD API JSON-LD settings."""
        model = self.get_one(id)
        if model is None:
            current_app.logger.error(
                f"SWORD API JSON-LD settings not found: {id}"
            )
            abort(404)

        # GET activity Waiting approval workflow
        can_edit = self._is_editable(model.workflow_id)
        if not can_edit:
            current_app.logger.info(
                "Cannot edit SWORD API JSON-LD settings because there are "
                "activities awaiting approval that use workflow: {}."
                .format(model.workflow_id)
            )

        if request.method == "GET":
            # GET
            form = FlaskForm(request.form)

            # GET metadata api
            metadata_api = WEKO_ITEMS_AUTOFILL_API_LIST.copy()
            metadata_api.append("Original")

            # GET workflow
            workflow = WorkFlow()
            workflow_list = workflow.get_workflow_list()
            reduce_workflows = workflow.reduce_workflows_for_registration(workflow_list)
            workflows = workflow.get_workflows_by_roles(reduce_workflows)
            deleted_workflows = workflow.get_deleted_workflow_list()
            deleted_workflow_name_dict = {}
            for deleted_workflow in deleted_workflows:
                deleted_workflow_info = {
                    "name": deleted_workflow.flows_name,
                    "itemtype_id": deleted_workflow.itemtype_id,
                }
                deleted_workflow_name_dict[deleted_workflow.id] = deleted_workflow_info
            # Process exclude workflows

            from weko_workflow.utils import exclude_admin_workflow
            exclude_admin_workflow(workflows)


            # All mapping
            jsonld_mappings = [
                {
                    "id": mapping.id,
                    "name": mapping.name,
                    "item_type_id": mapping.item_type_id
                } for mapping in JsonldMapping.get_all()
            ]

            current_model_json = {
                "id": model.id,
                "client_id": model.client_id,
                "registration_type_id": model.registration_type_id,
                "mapping_id": model.mapping_id,
                "workflow_id": model.workflow_id,
                "active": model.active,
                "duplicate_check": model.duplicate_check,
                "meta_data_api": model.meta_data_api
            }

            # All ItemTypeNames
            item_type_names = [
                {"id": item_type.id, "name": item_type.name}
                for item_type in ItemTypeNames.get_name_and_id_all()
            ]

            return self.render(
                self.edit_template,
                form=form,
                metadata_api=metadata_api,
                deleted_workflow_name_dict=json.dumps(deleted_workflow_name_dict),
                workflows=workflows,
                jsonld_mappings=jsonld_mappings,
                current_page_type="edit",
                current_client_name=model.oauth_client.name,
                current_model_json=current_model_json,
                can_edit=can_edit,
                item_type_names=item_type_names,
                id=model.id,
            )
        else:
            # POST
            if not can_edit:
                return jsonify("Unapproved items exit."), 400

            try:
                if request.json.get("registration_type") == "Direct":
                    registration_type_id = SwordClientModel.RegistrationType.DIRECT
                    workflow_id = None
                else:
                    registration_type_id = SwordClientModel.RegistrationType.WORKFLOW
                    workflow_id = request.json.get("workflow_id")
                mapping_id = request.json.get("mapping_id")
                active = request.json.get("active") == "True"
                duplicate_check = request.json.get("duplicate_check") == "True"
                meta_data_api = request.json.get("metadata_api_selected")

                if meta_data_api == ["Original"]:
                    meta_data_api = []
                if meta_data_api and "Original" not in meta_data_api:
                    msg = "Cannot disable 'Original'."
                    current_app.logger.error(msg)
                    return jsonify({"error": msg}), 400
                obj = JsonldMapping.get_mapping_by_id(mapping_id)
                try:
                    if not JsonLdMapper(obj.item_type_id, obj.mapping).is_valid:
                        msg = "Invalid jsonld mapping."
                        current_app.logger.error(msg)
                        return jsonify({"error": msg}), 400
                except Exception as ex:
                    msg = "Failed to validate jsonld mapping."
                    current_app.logger.error(msg)
                    traceback.print_exc()
                    return jsonify({"error": msg}), 400

                SwordClient.update(
                    client_id=model.client_id,
                    registration_type_id=registration_type_id,
                    mapping_id=mapping_id,
                    workflow_id=workflow_id,
                    active=active,
                    duplicate_check=duplicate_check,
                    meta_data_api=meta_data_api
                )
                current_app.logger.info(
                    f"Update settings for Sword API: {model.oauth_client.name}"
                )
                return jsonify(results=True), 200

            except SQLAlchemyError as ex:
                msg = f"Failed to update application settings: {model.oauth_client.name}"
                current_app.logger.error(msg)
                traceback.print_exc()
                return jsonify({"error": msg}), 400


    @expose("/validate/<string:id>/", methods=["GET"])
    def validate_mapping(self, id):
        obj = JsonldMapping.get_mapping_by_id(id)
        itemtype_id = obj.item_type_id
        try:
            return jsonify(results=JsonLdMapper(itemtype_id, obj.mapping).is_valid), 200
        except Exception as ex:
            msg = "Failed to validate jsonld mapping."
            current_app.logger.error(msg)
            traceback.print_exc()
            return jsonify({"error": msg}), 400


    @expose("/delete/", methods=["POST"])
    def delete_data(self):
        model = self.get_one(request.form.get("id"))
        if model is None:
            current_app.logger.error(
                f"SWORD API JSON-LD settings not found: {id}"
            )
            abort(404)

        name = model.oauth_client.name

        if self._is_editable(model.workflow_id):
            try:
                SwordClient.remove(model.client_id)
                current_app.logger.info(
                    f"SWORD API JSON-LD settings deleted: {name}"
                )
                flash(_("SWORD API JSON-LD settings deleted."), "success")
            except SQLAlchemyError as e:
                db.session.rollback()
                msg = f"Failed to delete SWORD API JSON-LD settings: {name}"
                current_app.logger.error(msg)
                traceback.print_exc()
                flash(_("Failed to delete SWORD API JSON-LD settings."), "error")
        else:
            current_app.logger.info(
                "Cannot delete SWORD API JSON-LD settings because there are "
                "activities awaiting approval that use workflow: {}."
                .format(model.workflow_id)
            )
            flash(_("Unapproved Items Exit."), "error")

        return_url = get_redirect_target() or self.get_url(".index_view")
        return redirect(return_url)


    def _is_editable(self, workflow_id):
        """Check if the mapping is editable."""
        can_edit = True
        if workflow_id is not None:
            count = (
                WorkActivity()
                .count_waiting_approval_by_workflow_id(workflow_id)
            )
            can_edit = not bool(count)
        return can_edit


class JsonldMappingView(ModelView):
    """Pidstore Identifier admin view."""
    form_base_class = Form

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True
    column_display_all_relations = True
    create_template = WEKO_ADMIN_SWORD_API_JSONLD_MAPPING_TEMPLATE
    edit_template = WEKO_ADMIN_SWORD_API_JSONLD_MAPPING_TEMPLATE

    column_filters = (
        "name",
        "item_type.item_type_name.name"
    )

    column_list = (
        "name",
        "item_type",
        "updated",
    )
    column_labels = {
        "name": _("Name"),
        "item_type.item_type_name.name": _("Item Type"),
        "updated": _("Updated"),
    }
    column_details_list = (
        "created",
        "updated",
        "name",
        "item_type",
        "mapping",
        "version_id",
    )

    def _item_type_name(view, context, model, name):
        item_type_name = ""
        if model.item_type and model.item_type.item_type_name:
            item_type_name = model.item_type.item_type_name.name
        else:
            item_type_name = _("Not Found ItemType")
        return item_type_name

    def _formated_jsonld_mapping(view, context, model, name):
        format_json =json.dumps(model.mapping, indent=4, ensure_ascii=False)
        return Markup(
            '<pre style="white-space: pre; border: none; '
            f'background-color: transparent;">{format_json}</pre>'
        )

    column_formatters = {
        "item_type": _item_type_name,
        "mapping": _formated_jsonld_mapping,
        "created": lambda v, c, m, n: m.created.strftime("%Y-%m-%d %H:%M:%S"),
        "updated": lambda v, c, m, n: m.updated.strftime("%Y-%m-%d %H:%M:%S"),
    }
    column_sortable_list = (
        "name",
        ('item_type', 'item_type.item_type_name.name'),
        "updated",
    )
    column_searchable_list = (
        "name",
        "item_type.item_type_name.name"
    )

    def get_query(self):
        """Get query for JSON-LD mapping."""
        return (
            super().get_query()
            .filter(ItemTypeJsonldMapping.is_deleted == False)
            .order_by(ItemTypeJsonldMapping.id)
        )

    @expose("/new/", methods=["GET", "POST"])
    def create_view(self):

        if request.method == "GET":
            # GET
            form = FlaskForm(request.form)

            # GET ItemType
            itemtypes = ItemTypes.get_latest_with_item_type()
            item_types = [
                {"id": itemtype.id, "item_type_name": itemtype.name}
                for itemtype in itemtypes
            ]

            return self.render(
                self.create_template,
                form=form,
                current_page_type="new",
                item_types=item_types,
                current_name=None,
                current_mapping=None,
                current_item_type_id=None,
                current_model_json=None,
                can_edit=False,
                id=None,
            )
        else:
            # POST
            name = request.json.get("name")
            item_type_id = request.json.get("item_type_id")
            mapping = request.json.get("mapping")

            try:
                JsonldMapping.create(name, mapping, item_type_id)
                current_app.logger.info(f"new jsonld mapping created: {name}")
                return jsonify(results=True), 200

            except SQLAlchemyError as ex:
                msg = f"Failed to create jsonld mapping: {name}"
                current_app.logger.error(msg)
                traceback.print_exc()
                return jsonify({"error": msg}), 500

    @expose("/edit/<string:id>/", methods=["GET", "POST"])
    def edit_view(self, id):
        model = self.get_one(id)
        if model is None:
            current_app.logger.error(
                f"JSON-LD mapping not found. ID: {id}"
            )
            abort(404)

        # Get activity waiting approval workflow
        can_edit = self._is_editable(id)
        if not can_edit:
            current_app.logger.info(
                "Cannot edit JSON-LD mapping because there are "
                "some activities awaiting approval that use mapping {}."
                .format(model.name)
            )

        # check if this mapping is using sword_clients
        can_change_itemtype = not SwordClient.get_clients_by_mapping_id(model.id)
        if not can_change_itemtype:
            current_app.logger.info(
                "Cannot edit JSON-LD mapping because this mapping is using "
                "SWORD API JSON-LD settings."
            )

        if request.method == "GET":
            # GET
            form = FlaskForm(request.form)

            # GET ItemType
            itemtypes = ItemTypes.get_latest_with_item_type()
            item_types = [
                {"id": itemtype.id, "item_type_name": itemtype.name}
                for itemtype in itemtypes
            ]

            current_model_json = {
                "id": model.id,
                "name": model.name,
                "mapping": model.mapping,
                "item_type_id": model.item_type_id,
            }

            return self.render(
                self.edit_template,
                form=form,
                current_page_type="edit",
                item_types=item_types,
                current_name=model.name,
                current_mapping=model.mapping,
                current_item_type_id=model.item_type_id,
                current_model_json=current_model_json,
                can_edit=can_edit,
                can_change_itemtype=can_change_itemtype,
                id=id,
            )
        else:
            # POST
            if not can_edit:
                return jsonify("Unapproved items exit."), 400


            name = request.json.get("name")
            mapping = request.json.get("mapping")
            item_type_id = request.json.get("item_type_id")

            if (
                not can_change_itemtype
                and int(item_type_id) != model.item_type_id
            ):
                return jsonify("Cannot change item type"), 400
            try:
                JsonldMapping.update(id, name, mapping, item_type_id)
                current_app.logger.info(f"jsonld mapping updated: {name}")
                return jsonify(results=True),200

            except SQLAlchemyError as ex:
                msg = f"Failed to update jsonld mapping: {model.name}"
                current_app.logger.error(msg)
                traceback.print_exc()
                return jsonify({"error": msg}), 400

    @expose("/delete/<string:id>/", methods=["DELETE"])
    def delete(self, id):
        """Delete JSON-LD mapping."""
        model = self.get_one(id)
        if model is None:
            current_app.logger.error(
                f"JSON-LD mapping not found. ID: {id}"
            )
            abort(404)
        if not self._is_editable(id):
            current_app.logger.info(
                "Cannot delete JSON-LD mapping because there are "
                "some activities awaiting approval that use mapping {}."
                .format(model.name)
            )
            return jsonify("Unapproved items exit."), 400

        try:
            obj = JsonldMapping.delete(id)
            current_app.logger.info(f"jsonld mapping deleted: {obj.name}")
            return jsonify(results=True), 200

        except SQLAlchemyError as ex:
            db.session.rollback()
            msg = f"Failed to delete jsonld mapping: {model.name}"
            current_app.logger.error(msg)
            traceback.print_exc()
            return jsonify({"error": msg}), 400


    @expose("/validate", methods=["POST"])
    def validate_mapping(self):
        data = request.get_json()
        itemtype_id = data.get("itemtype_id")
        mapping_id = data.get("mapping_id")
        mapping = data.get("mapping")

        if mapping is None:
            mapping = JsonldMapping.get_mapping_by_id(mapping_id).mapping

        return jsonify(JsonLdMapper(itemtype_id, mapping).validate())

    def _is_editable(self, mapping_id):
        """Check if the mapping is editable.

        This method checks if there are any activities awaiting approval
        that use the given mapping ID.

        Args:
            mapping_id (str): Mapping ID.

        Returns:
            bool: True if the mapping is editable, False otherwise.
        """
        list_sword_client = SwordClient.get_clients_by_mapping_id(mapping_id)
        list_workflow_id = [
            client.workflow_id for client in list_sword_client
            if client.workflow_id is not None
        ]
        for workflow_id in list_workflow_id:
            count = WorkActivity().count_waiting_approval_by_workflow_id(workflow_id)
            if count > 0:
                return False
        return True



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

restricted_access_adminview = {
    'view_class': RestrictedAccessSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Restricted Access'),
        'endpoint': 'restricted_access'
    }
}
identifier_adminview = dict(
    modelview=IdentifierSettingView,
    model=Identifier,
    category=_('Setting'),
    name=_('Identifier'),
    endpoint='identifier'
)

facet_search_adminview = dict(
    modelview=FacetSearchSettingView,
    model=FacetSearchSetting,
    category=_('Setting'),
    name=_('Faceted Search'),
    endpoint='facet-search'
)

reindex_elasticsearch_adminview = {
    'view_class': ReindexElasticSearchView,
    'kwargs': {
        'category': _('Maintenance'),
        'name': _('ElasticSearch Index'),
        'endpoint': 'reindex_es'
    }
}

sword_api_settings_adminview = {
    'view_class': SwordAPISettingsView,
    'kwargs': {
        'category': _('SWORD API'),
        'name': _('TSV/XML'),
        'endpoint': 'swordapi'
    }
}
sword_api_settings_jsonld_adminview = dict(
    modelview=SwordAPIJsonldSettingsView,
    model=SwordClientModel,
    category=_('SWORD API'),
    name=_('JSON-LD'),
    endpoint='swordapi/jsonld'
)

sword_api_jsonld_mapping_adminview = dict(
    modelview=JsonldMappingView,
    model=ItemTypeJsonldMapping,
    category=_('Item Types'),
    name=_('JSON-LD Mapping'),
    endpoint='jsonld-mapping'
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
    'restricted_access_adminview',
    'identifier_adminview',
    'facet_search_adminview',
    'reindex_elasticsearch_adminview',
    'sword_api_settings_adminview',
    'sword_api_settings_jsonld_adminview',
    'sword_api_jsonld_mapping_adminview'
)
