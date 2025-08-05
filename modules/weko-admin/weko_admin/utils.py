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

"""Utilities for convert response json."""
import csv
import json
import math
import os
import traceback
import zipfile
from datetime import datetime, timedelta
from io import BytesIO, StringIO
from typing import Dict, Optional, Tuple, Union

import redis
from redis import sentinel
import requests
from flask import current_app, request
from flask_babelex import gettext as __
from flask_babelex import lazy_gettext as _
from invenio_accounts.models import Role, userrole
from invenio_cache import cached_unless_authenticated
from invenio_db import db
from invenio_i18n.ext import current_i18n
from invenio_indexer.api import RecordIndexer
from invenio_mail.admin import MailSettingView
from invenio_mail.models import MailConfig
from invenio_records.models import RecordMetadata
from invenio_records_rest.facets import terms_filter, terms_condition_filter, range_filter
from invenio_stats.views import QueryFileStatsCount, QueryRecordViewCount
from jinja2 import Template
from simplekv.memory.redisstore import RedisStore
from sqlalchemy import func
from weko_authors.models import Authors
from weko_schema_ui.models import PublishStatus

from weko_records.api import ItemsMetadata
from weko_redis.redis import RedisConnection


from . import config
from .models import AdminLangSettings, AdminSettings, ApiCertificate, \
    FacetSearchSetting, FeedbackMailFailed, FeedbackMailHistory, \
    FeedbackMailSetting, SearchManagement, SiteInfo, StatisticTarget, \
    StatisticUnit


def get_response_json(result_list, n_lst):
    """Get a response json.

    :param result_list:
    :param n_lst:
    :return: result
    """
    result = {}
    if isinstance(result_list, list):
        newlst = []
        for rlst in result_list:
            adr_lst = rlst.get('addresses')
            for alst in adr_lst:
                alst['start_ip_address'] = alst['start_ip_address'].split(
                    '.')
                alst['finish_ip_address'] = alst[
                    'finish_ip_address'].split('.')
            newlst.append(rlst.dumps())
        result.update(dict(site_license=newlst))
        del result_list

    if n_lst:
        item_type = {}
        allow = []
        deny = []
        for lst in n_lst:
            tmp = []
            tmp.append({'id': str(lst.id), 'name': lst.name})
            if lst.has_site_license:
                allow.extend(tmp)
            else:
                deny.extend(tmp)

        item_type['deny'] = deny or []
        item_type['allow'] = allow or []
        result['item_type'] = item_type

    return result


def allowed_file(filename):
    """Allowed file."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.LOGO_ALLOWED_EXTENSIONS


def get_search_setting():
    """Get search setting from DB.

    :return: Setting data by Json
    """
    res = SearchManagement.get()

    if res:
        db_obj = res.search_setting_all
        if not db_obj.get('init_disp_setting') and res.init_disp_setting:
            db_obj['init_disp_setting'] = res.init_disp_setting
        # current_app.logger.debug(db_str)
        # if 'False' in db_str:
        #     db_str.replace('False','false')
        # if 'True' in db_str:
        #     db_str.replace('True', 'true')
        # db_str = json.dumps(db_str)
        # db_obj= json.loads(db_str)

        return db_obj
    else:
        return config.WEKO_ADMIN_MANAGEMENT_OPTIONS


def get_admin_lang_setting():
    """Convert language list to json.

    :return:
    """
    try:
        active_lang_list = AdminLangSettings.get_active_language()
    except Exception as e:
        return str(e)
    return active_lang_list


def update_admin_lang_setting(admin_lang_settings):
    """Update language to admin_lang_settings table.

    :param admin_lang_settings: input data to update language into database
    """
    for admin_lang in admin_lang_settings:
        AdminLangSettings.update_lang(admin_lang.get('lang_code'),
                                      admin_lang.get('lang_name'),
                                      admin_lang.get('is_registered'),
                                      admin_lang.get('sequence'))

def get_selected_language():
    """Get selected language."""
    result = {
        'lang': '',
        'selected': ''
    }
    registered_languages = AdminLangSettings.get_registered_language()
    if not registered_languages:
        return result
    result['lang'] = registered_languages
    result['selected'] = current_i18n.language

    return result


def get_api_certification_type():
    """Get API certification type.

    :return: list of supported certification type
    """
    try:
        all_api = ApiCertificate.select_all()
        result = []
        for api in all_api:
            data = dict()
            data['api_code'] = api.get('api_code')
            data['api_name'] = api.get('api_name')
            result.append(data)
        return result
    except Exception as e:
        return str(e)


def get_current_api_certification(api_code):
    """Get current API certification.

    :param api_code: API code
    :return: API certification data if exist
    """
    results = {
        'api_code': api_code,
        'api_name': '',
        'cert_data': {}
    }
    try:
        cert_data = ApiCertificate.select_by_api_code(api_code)
        results['api_name'] = cert_data.get('api_name')
        results['cert_data'] = cert_data.get('cert_data')

    except Exception as e:
        traceback.print_exc()
        return str(e)

    return results


def save_api_certification(api_code, cert_data):
    """Save API certification to DB base on api code.

    :param api_code: API code
    :param cert_data: certification data
    :return: dict
    {
        'results': true // true if save successfully
        'error':''
    }
    """
    result = {
        'results': '',
        'error': ''
    }
    try:
        if cert_data:
            if ApiCertificate.select_by_api_code(api_code) is not None:
                """ Update database in case api_code exited """
                result['results'] = ApiCertificate.update_cert_data(api_code,
                                                                    cert_data)
            else:
                result['error'] = _(
                    "Input type is invalid. Please check again.")
        else:
            result['error'] = _(
                "Account information is invalid. Please check again.")
    except Exception as e:
        result['error'] = str(e)

    return result


def create_crossref_url(pid):
    """Create Crossref api url.

    :param pid:
    :return Crossref api url:
    """
    if not pid:
        raise ValueError('PID is required')
    url = config.WEKO_ADMIN_CROSSREF_API_URL + config.WEKO_ADMIN_ENDPOINT + \
        '?pid=' + pid + config.WEKO_ADMIN_TEST_DOI + config.WEKO_ADMIN_FORMAT
    return url


def validate_certification(cert_data):
    """Validate certification.

    :param cert_data: Certification data
    :return: true if certification is valid, false otherwise
    """
    response = requests.get(create_crossref_url(cert_data))
    return config.WEKO_ADMIN_VALIDATION_MESSAGE not in \
        str(vars(response).get('_content', None))


def get_initial_stats_report():
    """Get initial statistic report.

    :return: list unit and list target
    """
    result = {
        'target': '',
    }

    targets = StatisticTarget.get_all_stats_report_target()
    match_target = list()
    for target in targets:
        temp_target = dict()
        temp_target['id'] = target['id']
        temp_target['data'] = target['data']
        match_target.append(temp_target)
    result['target'] = match_target

    return result


def get_unit_stats_report(target_id):
    """Get unit statistic report."""
    result = {
        'unit': '',
    }

    target = StatisticTarget.get_target_by_id(target_id)
    target_units = target.target_unit
    units = StatisticUnit.get_all_stats_report_unit()

    list_unit = list()
    for unit in units:
        if target_units.find(unit['id']) != -1:
            list_unit.append(unit)

    result['unit'] = list_unit
    return result


def get_user_report_data(repo_id=None):
    """Get user report data from db and modify."""
    from invenio_communities.models import Community
    role_counts = []
    try:
        if repo_id != 'Root Index':
            repository = Community.get(repo_id)
            user_ids_with_role = db.session.query(userrole.c.user_id) \
                .filter(userrole.c.role_id == repository.group_id).subquery()
            role_counts = db.session.query(Role.name,
                                        func.count(userrole.c.role_id)) \
                    .outerjoin(userrole) \
                    .filter(userrole.c.user_id.in_(user_ids_with_role)) \
                    .group_by(Role.id).all()
        else:
            role_counts = db.session.query(Role.name,
                                        func.count(userrole.c.role_id)) \
                    .outerjoin(userrole) \
                    .group_by(Role.id).all()
    except Exception as e:
        current_app.logger.error('Could not retrieve user report data: ')
        traceback.print_exc()
        return {}

    role_counts = [dict(role_name=name, count=count)
                   for name, count in role_counts]
    results = {'all': role_counts}
    total_users = sum([x['count'] for x in role_counts])

    # Total registered users
    results['all'].append({'role_name': _('Registered Users'),
                           'count': total_users})
    return results


def package_reports(all_stats, year, month):
    """Package the .csv files into one zip file."""
    output_files = []
    zip_stream = BytesIO()
    year = str(year)
    month = str(month)
    file_format = current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()
    try:  # TODO: Make this into one loop, no need for two
        for stats_type, stats in all_stats.items():
            file_name = current_app.config['WEKO_ADMIN_REPORT_FILE_NAMES'].get(
                stats_type, '_')
            file_name = 'logReport_' + file_name + year + '-' + month + '.' + file_format
            output_files.append({
                'file_name': file_name,
                'stream': make_stats_file(stats, stats_type, year, month)})

        # Dynamically create zip from StringIO data into BytesIO
        report_zip = zipfile.ZipFile(zip_stream, 'w')
        for f in output_files:
            report_zip.writestr(f['file_name'],
                                f['stream'].getvalue().encode('utf-8-sig'))
        report_zip.close()
    except Exception as e:
        current_app.logger.error('Unexpected error: {}'.format(e))
        raise
    return zip_stream


def make_stats_file(raw_stats, file_type, year, month):
    """Make TSV/CSV report file for stats."""
    header_row = current_app.config['WEKO_ADMIN_REPORT_HEADERS'].get(file_type)
    sub_header_row = current_app.config['WEKO_ADMIN_REPORT_SUB_HEADERS'].get(
        file_type)
    file_output = StringIO()
    file_format = current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()
    file_delimiter = '\t' if file_format == 'tsv' else ','
    writer = csv.writer(file_output, delimiter=file_delimiter,
                        lineterminator="\n")
    writer.writerows([[header_row],
                      [_('Aggregation Month'), year + '-' + month],
                      [''], [header_row]])

    if file_type in ['billing_file_download', 'billing_file_preview']:
        col_dict_key = file_type.split('_', 1)[1]
        cols = current_app.config['WEKO_ADMIN_REPORT_COLS'].get(col_dict_key,
                                                                [])
        cols[3:1] = raw_stats.get('all_groups')  # Insert group columns
    else:
        cols = current_app.config['WEKO_ADMIN_REPORT_COLS'].get(file_type, [])
    writer.writerow(cols)

    # Special cases:
    # Write total for per index views
    if file_type == 'index_access':
        write_report_file_rows(writer, raw_stats.get(
            'all'), file_type, raw_stats.get('index_name'))
        writer.writerow([_('Total Detail Views'), raw_stats.get('total')])

    elif file_type in ['billing_file_download', 'billing_file_preview']:
        write_report_file_rows(writer, raw_stats.get('all'), file_type,
                              raw_stats.get('all_groups'))  # Pass all groups
    elif file_type == 'site_access':
        write_report_file_rows(writer,
                              raw_stats.get('site_license'),
                              file_type,
                              _('Site license member'))
        write_report_file_rows(writer,
                              raw_stats.get('other'),
                              file_type,
                              _('Other than site license'))
    else:
        write_report_file_rows(writer, raw_stats.get('all'), file_type)

    # Write open access stats
    if sub_header_row is not None:
        writer.writerows([[''], [sub_header_row]])
        if 'open_access' in raw_stats:
            writer.writerow(cols)
            write_report_file_rows(writer, raw_stats.get('open_access'))
        elif 'institution_name' in raw_stats:
            writer.writerows([[_('Institution Name')] + cols])
            write_report_file_rows(writer,
                                  raw_stats.get('institution_name'),
                                  file_type)
    return file_output


def write_report_file_rows(writer, records, file_type=None, other_info=None):
    """Write tsv/csv rows for stats."""
    from weko_items_ui.utils import get_user_information
    if not records:
        return
    if isinstance(records, dict):
        records = list(records.values())
    for record in records:
        if file_type is None or \
            file_type == 'file_download' or \
                file_type == 'file_preview':
            writer.writerow([record.get('file_key'), record.get('index_list'),
                             record.get('total'), record.get('no_login'),
                             record.get('login'), record.get('site_license'),
                             record.get('admin'), record.get('reg')])

        elif file_type in ['billing_file_download', 'billing_file_preview']:
            row = [record.get('file_key'), record.get('index_list'),
                   record.get('total'), record.get('no_login'),
                   record.get('login'), record.get('site_license'),
                   record.get('admin'), record.get('reg')]
            group_counts = []
            for group_name in other_info:  # Add group counts in
                if record.get('group_counts'):
                    group_counts.append(
                        record.get('group_counts').get(group_name, 0))
            row[3:1] = group_counts
            writer.writerow(row)

        elif file_type == 'index_access':
            writer.writerow(
                [record.get('index_name'), record.get('view_count')])
        elif file_type == 'search_count':
            writer.writerow([record.get('search_key'), record.get('count')])
        elif file_type == 'user_roles':
            writer.writerow([record.get('role_name'), record.get('count')])
        elif file_type == 'detail_view':
            item_metadata_json = ItemsMetadata. \
                get_record(record.get('record_id'))
            writer.writerow([
                item_metadata_json['title'], record.get('index_names'),
                record.get('total_all'), record.get('total_not_login')])
        elif file_type == 'file_using_per_user':
            user_email = ''
            user_name = 'Guest'
            user_id = int(record.get('cur_user_id'))
            if user_id > 0:
                user_infos = get_user_information([user_id])
                user_email = user_infos[0]['email']
                user_name = user_infos[0]['username']
            writer.writerow([
                user_email, user_name,
                record.get('total_download'), record.get('total_preview')])
        elif file_type == 'top_page_access':
            writer.writerow([record.get('host'), record.get('ip'),
                             record.get('count')])
        elif file_type == 'site_access' and record:
            if other_info:
                writer.writerow([other_info, record.get('top_view'),
                                 record.get('search'),
                                 record.get('record_view'),
                                 record.get('file_download'),
                                 record.get('file_preview')])
            else:
                writer.writerow([record.get('name'), record.get('top_view'),
                                 record.get('search'),
                                 record.get('record_view'),
                                 record.get('file_download'),
                                 record.get('file_preview')])


def reset_redis_cache(cache_key, value, ttl=None):
    """Delete and then reset a cache value to Redis."""
    try:
        redis_connection = RedisConnection()
        datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
        if datastore.redis.exists(cache_key):
            datastore.delete(cache_key)
        if ttl is None:
            datastore.put(cache_key, value.encode('utf-8'))
        else:
            datastore.put(cache_key, value.encode('utf-8'),ttl)
    except Exception as e:
        current_app.logger.error('Could not reset redis value: {}'.format(e))
        raise


def is_exists_key_in_redis(key):
    """Check key exist in redis."""
    try:
        redis_connection = RedisConnection()
        datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
        return datastore.redis.exists(key)
    except Exception as e:
        current_app.logger.error('Could get value for ' + key + ": {}".format(e))
    return False


def is_exists_key_or_empty_in_redis(key):
    """Check key exist in redis."""
    try:
        redis_connection = RedisConnection()
        datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
        return datastore.redis.exists(key) and datastore.redis.get(key) != b''
    except Exception as e:
        current_app.logger.error('Could get value for ' + key + ": {}".format(e))
    return False


def get_redis_cache(cache_key):
    """Check and then retrieve the value of a Redis cache key."""
    try:
        redis_connection = RedisConnection()
        datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
        if datastore.redis.exists(cache_key):
            return datastore.get(cache_key).decode('utf-8')
    except Exception as e:
        current_app.logger.error('Could get value for ' + cache_key + ": {}".format(e))
    return None


def get_system_default_language():
    """Get system default language.

    Returns:
        string -- language code

    """
    registered_languages = AdminLangSettings.get_registered_language()
    if not registered_languages:
        return 'en'
    default_language = registered_languages[0].get('lang_code')
    return default_language


class StatisticMail:
    """Pack of function to send statistic mail."""

    @classmethod
    def get_send_time(cls):
        """Get statistic time.

        Returns:
            string -- time with format yyyy-MM

        """
        previous_month = datetime.now().replace(day=1) - timedelta(days=1)
        return previous_month.strftime("%Y-%m")

    @classmethod
    def send_mail_to_all(cls):
        """Send mail to all setting email."""
        repo_ids = [setting.repository_id for setting in FeedbackMailSetting.query.all()]
        for repo in repo_ids:
            cls.send_mail_to_one(repo=repo)

    @classmethod
    def send_mail_to_one(cls, list_mail_data=None, stats_date=None, repo=None):
        """Send mail to setting email."""
        from weko_records.api import FeedbackMailList
        from weko_workflow.utils import get_site_info_name

        # Load setting:
        system_default_language = get_system_default_language()
        setting = FeedbackMail.get_feed_back_email_setting(repo_id=repo)
        if not setting.get('is_sending_feedback') and not stats_date:
            return
        banned_mail = cls.get_banned_mail(setting.get('data'))
        if repo != "Root Index":
            root_setting = FeedbackMail.get_feed_back_email_setting(repo_id='Root Index')
            root_banned_mail= cls.get_banned_mail(root_setting.get('data'))
            banned_mail = list(set(banned_mail + root_banned_mail))

        session = db.session
        id = FeedbackMailHistory.get_sequence(session)
        start_time = datetime.now()
        if not stats_date:
            stats_date = cls.get_send_time()
        failed_mail = 0
        total_mail = 0
        try:
            if not list_mail_data:
                list_mail_data = FeedbackMailList.get_feedback_mail_list(repo)
                if not list_mail_data:
                    return

            # Get site name.
            site_en, site_ja = get_site_info_name()
            # Set default site name.
            site_name = current_app.config.get(
                'WEKO_ADMIN_FEEDBACK_MAIL_DEFAULT_SUBJECT',
                config.WEKO_ADMIN_FEEDBACK_MAIL_DEFAULT_SUBJECT)
            if system_default_language == 'ja' and site_ja:
                site_name = site_ja
            elif system_default_language == 'en' and site_en:
                site_name = site_en
            # Build subject mail.
            subject = cls.build_statistic_mail_subject(
                site_name, stats_date, system_default_language)
            # Get host URL
            host_url = current_app.config['THEME_SITEURL']
            if host_url[-1] == '/':
                host_url = host_url[:-1]

            for k, v in list_mail_data.items():
                # Do not send mail to user if email in
                # "Send exclusion target persons" list.
                user_mail = str(k)
                if user_mail in banned_mail:
                    continue

                mail_data = {
                    'user_name': cls.get_author_name(
                        user_mail,
                        v.get('author_id')),
                    'organization': site_name,
                    'time': stats_date
                }
                body = str(cls.fill_email_data(
                    cls.get_list_statistic_data(
                        v.get('items'),
                        stats_date,
                        host_url),
                    mail_data, system_default_language)
                )

                send_result = cls.send_mail(user_mail, body, subject)
                total_mail += 1
                if not send_result:
                    FeedbackMailFailed.create(
                        session,
                        id,
                        v.get('author_id'),
                        user_mail
                    )
                    failed_mail += 1
        except Exception as ex:
            current_app.logger.error('Error has occurred: {}'.format(ex))
            traceback.print_exc()
        end_time = datetime.now()
        FeedbackMailHistory.create(
            session,
            id,
            start_time,
            end_time,
            stats_date,
            total_mail,
            failed_mail,
            repository_id=repo
        )

    @classmethod
    def get_banned_mail(cls, list_banned_mail):
        """Get banned mail from list of setting.

        Arguments:
            list_banned_mail {list} -- list banned mail setting

        Returns:
            list -- banned mail

        """
        result = list()
        if len(list_banned_mail) == 0:
            return result
        for data in list_banned_mail:
            result.append(data.get('email'))
        return result

    @classmethod
    def convert_download_count_to_int(cls, download_count):
        """Convert statistic float string to int string.

        Arguments:
            download_count {string} -- float string

        Returns:
            string -- int string

        """
        try:
            if '.' in download_count:
                index = download_count.index('.')
                download_count = download_count[0:index]
            return int(download_count)
        except Exception as ex:
            current_app.logger.error(
                'Cannot convert download count to int: {}'.format(ex))
            return 0

    @classmethod
    def get_list_statistic_data(cls, list_item_id, time, root_url):
        """Get list statistic data for user.

        Arguments:
            list_item_id {list} -- item id
            time {string} -- statistic time

        Returns:
            dictionary -- The statistic data

        """
        list_result = {
            'data': [],
            'summary': {}
        }
        statistic_data = list()
        total_item = 0
        total_files = 0
        total_view = 0
        total_download = 0
        for item_id in list_item_id:
            data = cls.get_item_information(item_id, time, root_url)
            file_download = data.get('file_download')
            list_file_download = list()
            for k, v in file_download.items():
                total_download += cls.convert_download_count_to_int(v)
                list_file_download.append(str(
                    k + '(' + str(cls.convert_download_count_to_int(v)) + ')'))
            total_item += 1
            total_files += len(list_file_download)
            total_view += cls.convert_download_count_to_int(
                data.get('detail_view'))
            data['file_download'] = list_file_download
            statistic_data.append(data)
        summary_data = {
            'total_item': total_item,
            'total_files': total_files,
            'total_view': total_view,
            'total_download': total_download
        }
        list_result['data'] = statistic_data
        list_result['summary'] = summary_data
        return list_result

    @classmethod
    def get_item_information(cls, item_id, time, root_url):
        """Get information of item.

        Arguments:
            item_id {string} -- id of item
            time {string} -- time to statistic data

        Returns:
            [dictionary] -- data template insert to email

        """
        result = db.session.query(RecordMetadata).filter(
            RecordMetadata.id == item_id).one_or_none()
        data = result.json
        count_item_view = cls.get_item_view(item_id, time)
        count_item_download = cls.get_item_download(data, time)
        title = data.get("item_title")
        url = root_url + '/records/' + data.get('recid', '').split('.')[0]
        result = {
            'title': title,
            'url': url,
            'detail_view': count_item_view,
            'file_download': count_item_download
        }
        return result

    @classmethod
    def get_item_view(cls, item_id, time):
        """Get view of item.

        Arguments:
            item_id {string} -- id of item
            time {string} -- time to statistic data

        Returns:
            [string] -- viewed of item

        """
        query_file_view = QueryRecordViewCount()
        return str(query_file_view.get_data(item_id, time).get("total"))

    @classmethod
    def get_item_download(cls, data, time):
        """Get download of item.

        Arguments:
            data {dictionary} -- data of item in records_metadata
            time {string} -- time to statistic data

        Returns:
            [dictionary] -- dictionary of file and it's downloaded

        """
        list_file = cls.get_file_in_item(data)
        result = {}
        if list_file:
            for file_key in list_file.get("list_file_key"):
                query_file_download = QueryFileStatsCount()
                count_file_download = query_file_download.get_data(
                    list_file.get("bucket_id"), file_key, time).get(
                    "download_total")
                result[file_key] = str(count_file_download)
        return result

    @classmethod
    def find_value_in_dict(cls, key, data):
        """Find value of key in dictionary.

        Arguments:
            key {string} -- key of dictionary to find
            data {dictionary} -- data to find key

        """
        for k, v in data.items():
            if k == key:
                yield v
            if isinstance(v, dict):
                for result in cls.find_value_in_dict(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    if isinstance(d, dict):
                        for result in cls.find_value_in_dict(key, d):
                            yield result

    @classmethod
    def get_file_in_item(cls, data):
        """Get all file in item.

        Arguments:
            data {dictionary} -- data of item in records_metadata

        Returns:
            [dictionary] -- bucket id and file key of all file in item

        """
        bucket_id = data.get("_buckets").get("deposit")
        list_file_key = list(cls.find_value_in_dict("filename", data))
        return {
            "bucket_id": bucket_id,
            "list_file_key": list_file_key,
        }

    @classmethod
    def fill_email_data(cls, statistic_data, mail_data,
                        system_default_language):
        """Fill data to template.

        Arguments:
            mail_data {string} -- data for mail content.
            system_default_language {string} -- default language.

        Returns:
            string -- mail content

        """
        current_path = os.path.dirname(os.path.abspath(__file__))
        file_name = 'statistic_mail_template_en.tpl'  # default template file
        if system_default_language == 'ja':
            file_name = 'statistic_mail_template_ja.tpl'
        elif system_default_language == 'en':
            file_name = 'statistic_mail_template_en.tpl'

        file_path = os.path.join(
            current_path,
            'templates',
            'weko_admin',
            'email_templates',
            file_name)
        with open(file_path, 'r') as file:
            data = file.read()

        data_content = cls.build_mail_data_to_string(
            statistic_data.get('data'), system_default_language)
        summary_data = statistic_data.get('summary')
        mail_data = {
            'user_name': mail_data.get('user_name'),
            'organization': mail_data.get('organization'),
            'time': mail_data.get('time'),
            'data': data_content,
            'total_item': summary_data.get('total_item'),
            'total_file': summary_data.get('total_files'),
            'total_detail_view': summary_data.get('total_view'),
            'total_download': summary_data.get('total_download')
        }
        return Template(data).render(mail_data)

    @classmethod
    def send_mail(cls, recipient, body, subject):
        """Send mail to receiver.

        Arguments:
            receiver {string} -- receiver mail address
            body {string} -- mail content
            subject {string} -- mail subject

        Returns:
            boolean -- True if send success

        """
        current_app.logger.debug("START Prepare Feedback Mail Data")
        current_app.logger.debug('Recipient: {0}'.format(recipient))
        current_app.logger.debug('Mail data: \n{0}'.format(body))
        rf = {
            'subject': subject,
            'body': body,
            'recipient': recipient
        }
        current_app.logger.debug("END Prepare Feedback Mail Data")
        return MailSettingView.send_statistic_mail(rf)

    @classmethod
    def build_statistic_mail_subject(cls, title, send_date,
                                     system_default_language):
        """Build mail subject.

        Arguments:
            title {string} -- The site name
            send_date {string} -- statistic time
            system_default_language {string} -- default language.

        Returns:
            string -- The mail subject

        """
        result = '[' + title + ']' + send_date
        if system_default_language == 'ja':
            result += ' 利用統計レポート'
        elif system_default_language == 'en':
            result += ' Usage Statistics Report'
        else:
            # default mail subject.
            result += ' Usage Statistics Report'
        return result

    @classmethod
    def build_mail_data_to_string(cls, data, system_default_language):
        """Build statistic data as string.

        Arguments:
            data {dictionary} -- mail data
            system_default_language {str} -- default language.

        Returns:
            string -- statistic data as string

        """
        result = ''
        if not data:
            return result  # Return null string, avoid exception

        for item in data:
            file_down_str = ''
            for str_count in item['file_download']:
                file_down_str += '    ' + str_count + '\n'
            result += '----------------------------------------\n'
            if system_default_language == 'ja':
                result += '[タイトル] : ' + item['title'] + '\n'
                result += '[URL] : ' + item['url'] + '\n'
                result += '[閲覧回数] : ' + str(
                    cls.convert_download_count_to_int(
                        item['detail_view'])) + '\n'
                result += '[ファイルダウンロード回数] : \n' + file_down_str

            else:
                result += '[Title] : ' + item['title'] + '\n'
                result += '[URL] : ' + item['url'] + '\n'
                result += '[DetailView] : ' + str(
                    cls.convert_download_count_to_int(
                        item['detail_view'])) + '\n'
                result += '[FileDownload] : \n' + file_down_str
        return result

    @classmethod
    def get_author_name(cls, mail, author_id):
        """Get author name by id.

        Arguments:
            mail {string} -- default email if author not exist
            author_id {string} -- author id

        Returns:
            string -- author name

        """
        if not author_id:
            return mail
        author_data = Authors.get_author_by_id(author_id)
        if not author_data:
            return mail
        author_info = author_data.get('authorNameInfo')
        if not author_info:
            return mail
        return author_info[0].get('fullName')


def str_to_bool(str):
    """Convert string to bool."""
    return str.lower() in ['true', 't']


class FeedbackMail:
    """The feedback mail service."""

    @classmethod
    def search_author_mail(cls, request_data: dict) -> dict:
        """Search author mail.

        :param request_data: request data
        :return: author mail
        """
        search_key = request_data.get('searchKey') or ''
        should = [
            {"bool": {"must": [{"term": {"is_deleted": {"value": "false"}}}]}},
            {"bool": {"must_not": {"exists": {"field": "is_deleted"}}}}
        ]
        match = [{"term": {"gather_flg": 0}}, {"bool": {"should": should}}]

        if search_key:
            match.append(
                {"multi_match": {"query": search_key, "type": "phrase"}})
        query = {"bool": {"must": match}}
        size = int(request_data.get('numOfPage')
                   or config.WEKO_ADMIN_FEEDBACK_MAIL_NUM_OF_PAGE)
        num = request_data.get('pageNumber') or 1
        offset = (int(num) - 1) * size if int(num) > 1 else 0

        body = {
            "query": query,
            "from": offset,
            "size": size,
        }
        indexer = RecordIndexer()
        result = indexer.client.search(
            index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
            doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
            body=body
        )

        author_id_list = []
        for es_hit in result['hits']['hits']:
            author_id_info = es_hit['_source']['authorIdInfo']
            if author_id_info:
                author_id_list.append(author_id_info[0]['authorId'])

        name_id = '_item_metadata.item_creator.attribute_value_mlt'
        name_id += '.nameIdentifiers.nameIdentifier.keyword'
        query_item = {
            'size': 0,
            'query': {
                'terms': {
                    name_id: author_id_list
                }
            }, 'aggs': {
                'item_count': {
                    'terms': {
                        'field': name_id,
                        'include': author_id_list
                    }
                }
            }
        }
        result_itemCnt = indexer.client.search(
            index=current_app.config['SEARCH_UI_SEARCH_INDEX'],
            body=query_item
        )

        result['item_cnt'] = result_itemCnt

        return result

    @classmethod
    def get_feed_back_email_setting(cls, repo_id=None):
        """Get list feedback email setting.

        Returns:
            dictionary -- feedback email setting

        """
        result = {
            'data': '',
            'is_sending_feedback': '',
            'root_url': '',
            'error': ''
        }
        setting = FeedbackMailSetting.get_feedback_email_setting_by_repo(repo_id)
        if len(setting) == 0:
            return result
        list_author_id = setting[0].account_author.split(',')

        list_manual_mail = setting[0].manual_mail.get('email')
        result['is_sending_feedback'] = setting[0].is_sending_feedback
        result['root_url'] = setting[0].root_url
        list_data = list()
        for author_id in list_author_id:
            if not author_id:
                continue
            emails = Authors.get_emails_by_id(author_id)
            for e in emails:
                new_data = dict()
                new_data['author_id'] = author_id
                new_data['email'] = e
                list_data.append(new_data)
        if list_manual_mail:
            for mail in list_manual_mail:
                new_data = dict()
                new_data['author_id'] = ''
                new_data['email'] = mail
                list_data.append(new_data)
        result['data'] = list_data
        return result

    @classmethod
    def update_feedback_email_setting(cls, data, is_sending_feedback,
                                      root_url, repo_id=None):
        """Update feedback email setting.

        Arguments:
            data {list} -- data list
            is_sending_feedback {bool} -- is sending feedback
            root_url (string) -- Root URL

        Returns:
            dict -- error message

        """
        result = {
            'error': ''
        }
        update_result = False

        if not repo_id:
            result['error'] = "Repository ID is required."
            return result

        if not data and not is_sending_feedback:
            update_result = FeedbackMailSetting.delete_by_repo(repo_id)
            return cls.handle_update_message(
                result,
                update_result
            )
        error_message = cls.validate_feedback_mail_setting(data)
        if error_message:
            result['error'] = error_message
            return result
        current_setting = FeedbackMailSetting.get_feedback_email_setting_by_repo(repo_id)
        if len(current_setting) == 0:
            update_result = FeedbackMailSetting.create(
                cls.convert_feedback_email_data_to_string(data),
                cls.get_list_manual_email(data),
                is_sending_feedback,
                root_url,
                repo_id
            )
        else:
            update_result = FeedbackMailSetting.update(
                cls.convert_feedback_email_data_to_string(data),
                cls.get_list_manual_email(data),
                is_sending_feedback,
                root_url,
                repo_id
            )
        return cls.handle_update_message(
            result,
            update_result
        )

    @classmethod
    def convert_feedback_email_data_to_string(cls, data, keyword='author_id'):
        """Convert feedback email data to string.

        Arguments:
            data {list} -- Data list

        Keyword Arguments:
            keyword {str} -- search keyword (default: {'author_id'})

        Returns:
            string -- list as string

        """
        if not isinstance(data, list):
            return None
        result = set()
        for item in data:
            if item.get(keyword):
                result.add(str(item.get(keyword)))
        return ','.join(list(result))

    @classmethod
    def get_list_manual_email(cls, data):
        """Get list manual email from request data.

        Arguments:
            data {dictionary} -- request data

        Returns:
            dictionary -- list manual email

        """
        if not isinstance(data, list):
            return None
        list_mail = list()
        for item in data:
            if not item.get('author_id'):
                list_mail.append(item.get('email'))
        result = {
            'email': list_mail
        }
        return result

    @classmethod
    def handle_update_message(cls, result, success):
        """Check query result and return message.

        Arguments:
            result {dict} -- message
            success {bool} -- query result

        Returns:
            dict -- message

        """
        if not success:
            result['error'] = _('Cannot update Feedback email settings.')
        return result

    @classmethod
    def validate_feedback_mail_setting(cls, data):
        """Validate duplicate email and author id.

        Arguments:
            data {list} -- data list

        Returns:
            string -- error message

        """
        error_message = None
        list_author = cls.convert_feedback_email_data_to_string(
            data
        ).split(',')
        list_email = cls.convert_feedback_email_data_to_string(
            data,
            'email'
        ).split(',')
        new_list = list()
        for item in list_author:
            if len(new_list) == 0 or item not in new_list:
                new_list.append(item)
            else:
                error_message = _('Author is duplicated.')
                return error_message
        new_list = list()
        for item in list_email:
            if len(new_list) == 0 or item not in new_list:
                new_list.append(item)
            else:
                error_message = _('Duplicate Email Addresses.')
                return error_message
        return error_message

    @classmethod
    def load_feedback_mail_history(cls, page_num, repo_id=None):
        """Load all history of send mail.

        Arguments:
            page_num {integer} -- The page number
            repo_id {string} -- The repository id

        Raises:
            ValueError: Parameter error

        Returns:
            dictionary -- List of send mail history

        """
        result = {
            'data': [],
            'total_page': 0,
            'selected_page': 0,
            'records_per_page': 0,
            'error': ''
        }
        try:
            data = FeedbackMailHistory.get_all_history(repo_id=repo_id)
            list_history = list()
            page_num_end = \
                page_num * config.WEKO_ADMIN_NUMBER_OF_SEND_MAIL_HISTORY
            page_num_start = \
                page_num_end - config.WEKO_ADMIN_NUMBER_OF_SEND_MAIL_HISTORY
            if page_num_start > len(data):
                raise ValueError('Page out of range')

            for index in range(page_num_start, page_num_end):
                if index >= len(data):
                    break
                new_data = dict()
                new_data['id'] = data[index].id
                new_data['start_time'] = data[index].start_time.strftime(
                    '%Y-%m-%d %H:%M:%S.%f')[:-3]
                new_data['end_time'] = data[index].end_time.strftime(
                    '%Y-%m-%d %H:%M:%S.%f')[:-3]
                new_data['count'] = int(data[index].count)
                new_data['error'] = int(data[index].error)
                new_data['success'] = int(
                    data[index].count) - int(data[index].error)
                new_data['is_latest'] = data[index].is_latest
                new_data['repo'] = data[index].repository_id
                list_history.append(new_data)
            result['data'] = list_history
            result['total_page'] = cls.get_total_page(
                len(data),
                config.WEKO_ADMIN_NUMBER_OF_SEND_MAIL_HISTORY)
            result['selected_page'] = page_num
            result['records_per_page'] = \
                config.WEKO_ADMIN_NUMBER_OF_SEND_MAIL_HISTORY
            return result
        except Exception as ex:
            traceback.print_exc()
            result['error'] = 'Cannot get data. Detail: ' + str(ex)
            return result

    @classmethod
    def load_feedback_failed_mail(cls, id, page_num):
        """Load all failed mail by history id.

        Arguments:
            id {integer} -- History id
            page_num {integer} -- Page number

        Raises:
            ValueError: Parameter error

        Returns:
            dictionary -- List email

        """
        result = {
            'data': [],
            'total_page': 0,
            'selected_page': 0,
            'records_per_page': 0,
            'error': ''
        }
        try:
            data = FeedbackMailFailed.get_by_history_id(id)
            list_mail = list()
            page_num_end = page_num * config.WEKO_ADMIN_NUMBER_OF_FAILED_MAIL
            page_num_start = \
                page_num_end - config.WEKO_ADMIN_NUMBER_OF_FAILED_MAIL
            if page_num_start > len(data):
                raise ValueError('Page out of range')

            for index in range(page_num_start, page_num_end):
                if index >= len(data):
                    break
                new_data = dict()
                new_data['name'] = cls.get_email_name(
                    data[index].author_id,
                    data[index].mail
                )
                new_data['mail'] = cls.get_newest_email(
                    data[index].author_id,
                    data[index].mail
                )
                list_mail.append(new_data)
            result['data'] = list_mail
            result['total_page'] = cls.get_total_page(
                len(data),
                config.WEKO_ADMIN_NUMBER_OF_FAILED_MAIL)
            result['selected_page'] = page_num
            result['records_per_page'] = \
                config.WEKO_ADMIN_NUMBER_OF_FAILED_MAIL
            return result
        except Exception as ex:
            result['error'] = 'Cannot get data. Detail: ' + str(ex)
            return result

    @classmethod
    def get_email_name(cls, author_id, mail):
        """Get name when author have id.

        Arguments:
            author_id {string} -- author id
            mail {string} -- email

        Returns:
            string -- name of author

        """
        if not author_id:
            return mail
        author_data = Authors.get_author_by_id(author_id)
        if not author_data:
            return mail
        author_info = author_data.get('authorNameInfo')
        if not author_info:
            return mail
        return author_info[0].get('fullName')

    @classmethod
    def get_newest_email(cls, author_id, mail):
        """Get newest email of author.

        Arguments:
            author_id {string} -- author id
            mail {string} -- email

        Returns:
            string -- newest email

        """
        if not author_id:
            return mail
        author_data = Authors.get_author_by_id(author_id)
        if not author_data:
            return mail
        email_info = author_data.get('emailInfo')
        if not email_info:
            return mail
        return email_info[0].get('email')

    @classmethod
    def get_total_page(cls, data_length, page_max_record):
        """Get total page.

        Arguments:
            data_length {integer} -- length of data

        Returns:
            integer -- total page number

        """
        if data_length % page_max_record != 0:
            return int(data_length / page_max_record) + 1
        else:
            return int(data_length / page_max_record)

    @classmethod
    def get_mail_data_by_history_id(cls, history_id):
        """Get list failed mail data.

        Arguments:
            history_id {string} -- The history id

        Returns:
            dictionary -- resend mail data

        """
        from weko_records.api import FeedbackMailList

        result = {
            'data': dict(),
            'stats_date': ''
        }
        history_data = FeedbackMailHistory.get_by_id(history_id)
        if not history_data:
            return None
        stats_time = history_data.stats_time
        list_failed_mail = FeedbackMailFailed.get_mail_by_history_id(
            history_id)
        if len(list_failed_mail) == 0:
            return None

        list_mail_data = FeedbackMailList.get_feedback_mail_list(repo_id=history_data.repository_id)
        if not list_mail_data:
            return None

        resend_mail_data = dict()
        for k, v in list_mail_data.items():
            if k in list_failed_mail:
                resend_mail_data[k] = v
        result['data'] = resend_mail_data
        result['stats_date'] = stats_time
        result['repository_id'] = history_data.repository_id
        return result

    @classmethod
    def update_history_after_resend(cls, history_id):
        """Update latest status after resend.

        Arguments:
            history_id {string} -- The history id

        """
        FeedbackMailHistory.update_lastest_status(history_id, False)


def validation_site_info(site_info):
    """Validate site_info.

    :param site_info:
    :return: result
    """
    list_lang_admin = get_admin_lang_setting()
    list_lang_register = [lang for lang in list_lang_admin if
                          lang.get('is_registered')]
    list_lang_code = [lang.get('lang_code') for lang in list_lang_register]
    site_name = site_info.get("site_name")
    notify = site_info.get("notify")
    errors_mess = []
    errors = []

    weko_admin_site_info_message = {
        'must_set_at_least_1_site_name_label': __(
            'Must set at least 1 site name.'),
        'please_input_site_infomation_for_empty_field_label': __(
            'Please input site information for empty field.'),
        'the_same_language_is_set_for_many_site_names_label': __(
            'The same language is set for many site names.'),
        'site_name_is_required_label': __('Site name is required.'),
        'language_not_match_label': __(
            'Language is deleted from Registered Language of system.'),
        'the_limit_is_1000_characters': __('The limit is 1000 characters'),
    }

    """check site_name len"""
    if not site_name:
        return {
            'error': weko_admin_site_info_message.get(
                'must_set_at_least_1_site_name_label'),
            'data': [],
            'status': False
        }
    elif len(list(filter(lambda a: not a.get('name'), site_name))) == len(
            site_name):
        return {
            'error': weko_admin_site_info_message.get(
                'must_set_at_least_1_site_name_label'),
            'data': ['site_name_0'],
            'status': False
        }
    for item in site_name:
        if not item.get("name").strip():
            return {
                'error': weko_admin_site_info_message.get(
                    'please_input_site_infomation_for_empty_field_label'),
                'data': ["site_name_" + str(
                    item.get("index"))],
                'status': False
            }
        check_dub = list(
            filter(lambda a: a.get("language") == item.get("language"),
                   site_name))
        if len(check_dub) >= 2:
            errors_mess.append(weko_admin_site_info_message.get(
                'the_same_language_is_set_for_many_site_names_label'))
            for cd in check_dub:
                errors.append("site_name_" + str(cd.get(
                    "index")))
            return {
                'error': weko_admin_site_info_message.get(
                    'the_same_language_is_set_for_many_site_names_label'),
                'data': errors,
                'status': False
            }
        if int(item.get("index")) > len(list_lang_register):
            return {
                'error': weko_admin_site_info_message.get(
                    'language_not_match_label'),
                'data': ["site_name_" + str(item.get(
                    "index"))],
                'status': False
            }
        if not item.get("language") in list_lang_code:
            return {
                'error': weko_admin_site_info_message.get(
                    'language_not_match_label'),
                'data': ["site_name_" + str(item.get(
                    "index"))],
                'status': False
            }

    '''Check length input notify'''
    for item in notify:
        if len(item.get('notify_name')) > 1000:
            return {
                'error': weko_admin_site_info_message.get(
                    'the_limit_is_1000_characters'),
                'data': ["notify_" + str(item.get(
                    "index"))],
                'status': False
            }

    return {
        'error': '',
        'data': [],
        'status': True
    }


def format_site_info_data(site_info):
    """
    Format site info data.

    :param site_info:
    :return: result
    """
    result = dict()
    site_name = []
    list_site_name = site_info.get('site_name') or []
    for sn in list_site_name:
        site_name.append({
            "index": sn.get('index'),
            "name": sn.get('name').strip(),
            "language": sn.get('language'),
        })
    notify = []
    list_notify = site_info.get('notify') or []
    for nt in list_notify:
        notify.append({
            "notify_name": nt.get('notify_name').strip(),
            "language": nt.get('language'),
        })
    result['site_name'] = site_name
    result['copy_right'] = site_info.get('copy_right').strip()
    result['description'] = site_info.get('description').strip()
    result['keyword'] = site_info.get('keyword').strip()
    result['favicon'] = site_info.get('favicon')
    result['favicon_name'] = site_info.get('favicon_name')
    result['notify'] = notify
    result['google_tracking_id_user'] = site_info.get(
        'google_tracking_id_user')
    result['ogp_image'] = site_info.get('ogp_image')
    result['ogp_image_name'] = site_info.get('ogp_image_name')
    return result


def get_site_name_for_current_language(site_name):
    """
    Get site name for current language system.

    :param site_name:
    :return: title
    """
    lang_code_english = 'en'
    if site_name:
        for sn in site_name:
            if sn.get('language') == current_i18n.language:
                return sn.get("name")
        for sn in site_name:
            if sn.get('language') == lang_code_english:
                return sn.get("name")
        return site_name[0].get("name")
    else:
        return ''


def get_notify_for_current_language(notify):
    """
    Get notify for current language system.

    :param notify:
    :return: notify_sign_up
    """
    lang_code_english = 'en'
    if notify:
        for nt in notify:
            if nt.get('language') == current_i18n.language:
                return nt.get("notify_name")
        for nt in notify:
            if nt.get('language') == lang_code_english:
                return nt.get("notify_name")
        return ''
    else:
        return ''


def __build_init_display_index(indexes: list,
                               init_display_indexes: list,
                               init_disp_index: str):
    """Build initial display index.

    :param indexes:index list from Database.
    :param init_display_indexes:index list.
    :param init_disp_index:selected index value
    """
    for child in indexes:
        if child.get('id') and child.get('public_state') is True:
            selected = child.get('id') == init_disp_index
            parent = child.get('parent', "0").split('/')[-1]
            index = {
                "id": child.get('id'),
                "parent": parent,
                "text": child.get('name'),
            }
            if selected:
                index['state'] = {"selected": selected}
                index['a_attr'] = {"class": "jstree-clicked"}
            init_display_indexes.append(index)
            if child.get('children'):
                __build_init_display_index(
                    child.get('children'),
                    init_display_indexes,
                    init_disp_index)


def get_init_display_index(init_disp_index: str) -> list:
    """Get initial display index.

    :param init_disp_index: Selected index.
    :return: index list.
    """
    from weko_index_tree.api import Indexes
    index_list = Indexes.get_index_tree()
    root_index = {
        "id": "0",
        "parent": "#",
        "text": "Root Index",
        "state": {"opened": True},
    }
    if not init_disp_index or init_disp_index == "0":
        root_index["state"].update({"selected": True})
        root_index['a_attr'] = {"class": "jstree-clicked"}
    init_display_indexes = [root_index]
    __build_init_display_index(index_list, init_display_indexes,
                               init_disp_index)

    return init_display_indexes


def get_restricted_access(key: Optional[str] = None) -> Optional[dict]:
    """Get registered access settings.

    :param key:setting key.
    :return:
    """
    restricted_access:dict = AdminSettings.get('restricted_access', False)
    if not restricted_access:
        restricted_access = current_app.config[
            'WEKO_ADMIN_RESTRICTED_ACCESS_SETTINGS']
    if not 'error_msg' in restricted_access:
            restricted_access['error_msg'] = config.WEKO_ADMIN_RESTRICTED_ACCESS_ERROR_MESSAGE
    if not key:
        return restricted_access
    elif key in restricted_access:
        return restricted_access[key]
    return {}


def update_restricted_access(restricted_access: dict):
    """Update the restricted access.

    :param restricted_access:
    """
    def parse_secret_URL_file_download():
        if secret_URL_file_download.get('secret_expiration_date_unlimited_chk'):
            secret_URL_file_download['secret_expiration_date'] = config.WEKO_ADMIN_RESTRICTED_ACCESS_MAX_INTEGER
        if secret_URL_file_download.get('secret_download_limit_unlimited_chk'):
            secret_URL_file_download['secret_download_limit'] = config.WEKO_ADMIN_RESTRICTED_ACCESS_MAX_INTEGER

        secret_URL_file_download['secret_expiration_date'] = int(
            secret_URL_file_download['secret_expiration_date'])
        secret_URL_file_download['secret_download_limit'] = int(
            secret_URL_file_download['secret_download_limit'])

    def validate_secret_URL_file_download():
        if not secret_URL_file_download.get(
            'secret_expiration_date_unlimited_chk') and not secret_URL_file_download[
            'secret_expiration_date'] or not secret_URL_file_download.get(
            'secret_download_limit_unlimited_chk') and not \
                secret_URL_file_download['secret_download_limit']:
            return False
        if secret_URL_file_download['secret_expiration_date'] and int(
            secret_URL_file_download['secret_expiration_date']) < 1 or \
            secret_URL_file_download['secret_download_limit'] and int(
                secret_URL_file_download['secret_download_limit']) < 1:
            return False
        return True

    def parse_content_file_download():
        if content_file_download.get('expiration_date_unlimited_chk'):
            content_file_download['expiration_date'] = config.WEKO_ADMIN_RESTRICTED_ACCESS_MAX_INTEGER
        if content_file_download.get('download_limit_unlimited_chk'):
            content_file_download['download_limit'] = config.WEKO_ADMIN_RESTRICTED_ACCESS_MAX_INTEGER

        content_file_download['expiration_date'] = int(
            content_file_download['expiration_date'])
        content_file_download['download_limit'] = int(
            content_file_download['download_limit'])

    def validate_content_file_download():
        if not content_file_download.get(
            'expiration_date_unlimited_chk') and not content_file_download[
            'expiration_date'] or not content_file_download.get(
            'download_limit_unlimited_chk') and not \
                content_file_download['download_limit']:
            return False
        if content_file_download['expiration_date'] and int(
            content_file_download['expiration_date']) < 1 or \
            content_file_download['download_limit'] and int(
                content_file_download['download_limit']) < 1:
            return False
        return True

    def validate_usage_report_wf_access():
        if not usage_report_wf_access.get(
            'expiration_date_access_unlimited_chk') and not \
                usage_report_wf_access.get('expiration_date_access'):
            return False
        if usage_report_wf_access['expiration_date_access'] and int(
                usage_report_wf_access['expiration_date_access']) < 1:
            return False
        return True

    def parse_usage_report_wf_access():
        if usage_report_wf_access.get('expiration_date_access_unlimited_chk'):
            usage_report_wf_access['expiration_date_access'] = config.WEKO_ADMIN_RESTRICTED_ACCESS_MAX_INTEGER

        usage_report_wf_access['expiration_date_access'] = int(
            usage_report_wf_access['expiration_date_access'])

    # Secret URL file download.
    if 'secret_URL_file_download' in restricted_access:
        secret_URL_file_download = restricted_access['secret_URL_file_download']
        if not validate_secret_URL_file_download():
            return False
        parse_secret_URL_file_download()

    # Content file download.
    if 'content_file_download' in restricted_access:
        content_file_download = restricted_access['content_file_download']
        if not validate_content_file_download():
            return False
        parse_content_file_download()

    # Usage Report Workflow Access
    if "usage_report_workflow_access" in restricted_access:
        usage_report_wf_access = restricted_access[
            'usage_report_workflow_access']
        if not validate_usage_report_wf_access():
            return False
        parse_usage_report_wf_access()

    AdminSettings.update('restricted_access', restricted_access)

    return True


class UsageReport:
    """Usage report."""

    def __init__(self):
        """Initialize the usage report."""
        from weko_workflow.api import WorkActivity
        from weko_workflow.models import ActionStatusPolicy
        from weko_workflow.utils import generate_guest_activity_token_value, \
            process_send_mail
        self.__activities_id = []
        self.__activities_number = 0
        self.__work_activity = WorkActivity()
        self.__action_status_policy = ActionStatusPolicy()
        self.__activity_token_value = generate_guest_activity_token_value
        self.__process_send_mail = process_send_mail
        self.__page_number = 1
        self.__usage_report_activities_data = []
        self.__mail_key = {
            "subitem_fullname": "restricted_fullname",
            "subitem_mail_address": "restricted_mail_address",
            "subitem_university/institution":
                "restricted_university_institution",
            "subitem_restricted_access_dataset_usage": "restricted_data_name",
            "subitem_restricted_access_application_date":
                "restricted_application_date",
            "subitem_restricted_access_research_title":
                "restricted_research_title",
            "subitem_research_title": "restricted_research_title"
        }
        self.__mail_info_lst = []

    def get_activities_per_page(
        self, activities_id: list = None, size: int = 25, page: int = 1
    ) -> Dict[str, Union[int, list, int]]:
        """Get activities per page.

        Args:
            activities_id (list, optional): Activities identifier list.
                                                            Defaults to None.
            size (int, optional): The number of activity per page.
                                                                Defaults to 20.
            page (int, optional): Page number. Defaults to 1.

        Returns:
            Dict[str, Union[int, list, int]]: activities per page.

        """
        # Get usage report activities identifier.
        if activities_id:
            self.__activities_id = activities_id
        # Get the number of usage report is not completed.
        self.__count_activities()
        # Maximum page number
        self.__page_number = math.ceil(self.__activities_number / int(size))
        # Validate page number
        if page > self.__page_number:
            page = 1
        # Perform get usage report activities.
        self.__usage_report_activities_data = self.__work_activity \
            .get_usage_report_activities(self.__activities_id, size, page)

        activities = self.__format_usage_report_data()
        return {
            "page": page,
            "size": size,
            "activities": activities,
            "number_of_pages": int(self.__page_number),
        }

    def __count_activities(self):
        """Get the number of usage report activities."""
        self.__activities_number = self.__work_activity \
            .count_all_usage_report_activities(self.__activities_id)

    def __format_usage_report_data(self) -> list:
        """Format usage report data.

        Returns:
            [list]: Activities is formatted.

        """
        activities = []
        action_status = self.__action_status_policy.describe(
            self.__action_status_policy.ACTION_DOING)
        for activity in self.__usage_report_activities_data:
            user_mail = activity.extra_info.get(
                'user_mail') if activity.extra_info.get(
                'user_mail') else activity.extra_info.get('guest_mail')
            activities.append(
                dict(
                    activity_id=activity.activity_id,
                    item_name=activity.title or activity.temp_data.get("title",
                                                                       ""),
                    workflow_name=activity.workflow.flows_name,
                    action_status=action_status,
                    user_mail=user_mail
                )
            )
        return activities

    def send_reminder_mail(self, activities_id: list,
                           mail_id: str = None, activities: list = None, forced_send = False):
        """Send reminder email to user.

        Args:
            activities_id (list): Activity identifier list.
            mail_id (str, optional): Mail template id.
            activities (list, optional): Activities list.
        """
        if not activities:
            activities = self.__work_activity.get_usage_report_activities(
                activities_id)
        records_id = []
        site_url = current_app.config['THEME_SITEURL']
        site_name_en, site_name_ja = self.__get_site_info()
        site_mail = self.__get_default_mail_sender()
        institution_name_ja = current_app.config['THEME_INSTITUTION_NAME']['ja']
        institution_name_en = current_app.config['THEME_INSTITUTION_NAME']['en']
        if not mail_id:
            mail_id = current_app.config\
                .get("WEKO_WORKFLOW_REQUEST_FOR_REGISTER_USAGE_REPORT")

        for activity in activities:
            if activity.item_id:
                records_id.append(activity.item_id)

            url, user_mail = self.__get_usage_report_email_and_url(activity)
            # Create mail info
            self.__mail_info_lst.append(
                {
                    "restricted_activity_id": activity.activity_id,
                    "restricted_mail_address": user_mail,
                    "data_download_date": activity.created.strftime("%Y-%m-%d"),
                    "usage_report_url": url,
                    "restricted_site_url": site_url,
                    "restricted_site_name_ja": site_name_ja,
                    "restricted_site_name_en": site_name_en,
                    "restricted_institution_name_ja": institution_name_ja,
                    "restricted_institution_name_en": institution_name_en,
                    "restricted_site_mail": site_mail,
                    "restricted_usage_activity_id": activity.extra_info.get(
                        'usage_activity_id'),
                }
            )
            if activity.extra_info:
                self.__build_user_info(
                    activity.extra_info.get('usage_application_record_data'),
                    self.__mail_info_lst[-1]
                )
            self.__mail_info_lst[-1]['mail_recipient'] = \
                self.__mail_info_lst[-1]['restricted_mail_address']
        is_sendmail_success = True
        if activity.extra_info.get('is_guest') or forced_send:
            for mail_info in self.__mail_info_lst:
                if not self.__process_send_mail(mail_info, mail_id):
                    is_sendmail_success = False
                    break
        return is_sendmail_success

    @staticmethod
    def __get_site_info():
        """Get site name.

        @return:
        """
        site_name_en = site_name_ja = ''
        site_info = SiteInfo.get()
        if site_info:
            if len(site_info.site_name) == 1:
                site_name_en = site_name_ja = site_info.site_name[0]['name']
            elif len(site_info.site_name) == 2:
                for site in site_info.site_name:
                    site_name_ja = site['name'] \
                        if site['language'] == 'ja' else site_name_ja
                    site_name_en = site['name'] \
                        if site['language'] == 'en' else site_name_en
        return site_name_en, site_name_ja

    def __get_usage_report_email_and_url(self, activity) -> Tuple[str, str]:
        """Get usage report email and url from activity.

        Args:
            activity (Activity): The activity

        Returns:
            Tuple[str, str]: Email and Url

        """
        extra_info = activity.extra_info
        file_name = extra_info.get('file_name')
        root_url = request.host_url
        activity_id = activity.activity_id
        if extra_info.get('is_guest'):
            url_pattern = "{}workflow/activity/guest-user/{}?token={}"
            email = activity.extra_info.get('guest_mail')
            token_value = self.__activity_token_value(
                activity_id, file_name, activity.created, email
            )
            url = url_pattern.format(root_url, file_name, token_value)
        else:
            email = activity.extra_info.get('user_mail')
            url = "{}workflow/activity/detail/{}".format(root_url, activity_id)
        return url, email

    def __build_user_info(self, record_data: Union[RecordMetadata, list],
                          mail_info: dict):
        """Build user info.

        Args:
            record_data (Union[RecordMetadata, list]):
            mail_info (dict):
        """
        if isinstance(record_data, dict):
            for k, v in record_data.items():
                if k in self.__mail_key and isinstance(v, str):
                    mail_info[self.__mail_key[k]] = v
                else:
                    self.__build_user_info(v, mail_info)
        elif isinstance(record_data, list):
            for data in record_data:
                self.__build_user_info(data, mail_info)

    @staticmethod
    def __get_default_mail_sender():
        """Get default mail sender.

        :return:
        """
        mail_config = MailConfig.get_config()
        return mail_config.get('mail_default_sender', '')


def get_facet_search(id: int = None):
    """Get facet search data.

    :param:id key.
    :return: facet search data

    Args:
        id:
    """
    if id is None:
        facet_search = current_app.config['WEKO_ADMIN_FACET_SEARCH_SETTING']
    else:
        facet_search_setting = FacetSearchSetting.get_by_id(id)
        facet_search = facet_search_setting.to_dict()
    return facet_search


def get_item_mapping_list():
    """Get Item Mapping list in Facet search setting.

    Returns:
        object:

    """
    def handle_prefix_key(pre_key, key):
        if key == 'properties':
            return pre_key
        pre_key = pre_key.replace('.fields', '')
        return "{}.{}".format(pre_key, key) if pre_key else key

    def get_mapping(pre_key, key, value, mapping_list):
        if isinstance(value, dict) and value.get('type') == 'keyword':
            mapping_list.append(handle_prefix_key(pre_key, key))
        if isinstance(value, dict):
            for k1, v1 in value.items():
                get_mapping(handle_prefix_key(
                    pre_key, key), k1, v1, mapping_list)

    import json

    import weko_schema_ui
    current_path = os.path.dirname(os.path.abspath(weko_schema_ui.__file__))
    file_path = os.path.join(current_path, 'mappings', 'v6', 'weko',
                             'item-v1.0.0.json')
    with open(file_path) as json_file:
        mappings = json.load(json_file).get('mappings')
        properties = mappings.get('item-v1.0.0').get('properties')
    result = [""]
    for k, v in properties.items():
        mapping_list = []
        get_mapping('', k, v, mapping_list)
        result = result + mapping_list
    return result

def get_detail_search_list():
    """
    Gets the name and type of the search condition used in the detail search.
    The purpose of this function is to return the information of a detail search in order to prevent
    duplication of parameter names used in a facet search with those used in a detail search.

    It extracts the part related to the detail_condition from the search settings and returns [id],
    which is the source of the parameter name, and [inputType], which determines the type.

    If there is a special search parameter, the parameter name is defined in [mappingName] and is included in the response.
    """
    detail_conditions = get_search_setting()["detail_condition"]
    result = []
    for k_v in detail_conditions:
        result.append([k_v.get("id"), k_v.get("inputType")])
        if k_v.get("mappingName"): result.append([k_v.get("mappingName"), k_v.get("id") + ".mappingName"])
    return result


def create_facet_search_query():
    """Create facet search query."""
    def create_agg_by_aggregations(aggregations, key, val):
        """Create aggregations query."""
        from .config import \
            WEKO_ADMIN_FACET_SEARCH_SETTING_BUCKET_SIZE as bucket_size
        if not aggregations or len(aggregations) == 0:
            result = {key: {'terms': {'field': val, "size": bucket_size}}}
        else:
            must = [dict(term={agg['agg_mapping']: agg['agg_value']})
                    for agg in aggregations]
            result = {key: {
                'filter': {'bool': {'must': must}},
                'aggs': {key: {'terms': {'field': val, "size": bucket_size}}}
            }}
        return result

    def create_aggregations(facets):
        """Create aggregations query."""
        agg_has_permission_query, agg_no_permission_query = dict(), dict()
        for facet in facets:
            key = facet.name_en
            val = facet.mapping
            # Update agg query for has permission.
            agg_has_permission_query.update(
                create_agg_by_aggregations(facet.aggregations, key, val))
            # Update agg query for no permission.
            facet.aggregations.append(
                {'agg_mapping': 'publish_status', 'agg_value': PublishStatus.PUBLIC.value})
            agg_no_permission_query.update(
                create_agg_by_aggregations(facet.aggregations, key, val))
        return agg_has_permission_query, agg_no_permission_query

    def create_post_filters(facets):
        """Create post filters query."""
        post_filters_query = dict()
        for facet in facets:
            if "fields.raw" in facet.mapping:
                """ remove "fields" when using multi-field """
                facet.mapping = facet.mapping.replace(".fields.raw", ".raw")
            post_filters_query.update({facet.name_en: facet.mapping})
        return post_filters_query

    search_index = current_app.config['SEARCH_UI_SEARCH_INDEX']
    has_permission_query, no_permission_query = dict(), dict()
    # Get all activated facets.
    activated_facets = FacetSearchSetting.get_activated_facets()
    # Get aggregations and post filters query.
    agg_has_permission, agg_no_permission = create_aggregations(
        activated_facets)
    post_filters = create_post_filters(activated_facets)
    # Create facet search query for has permission.
    has_permission_query[search_index] = dict(
        aggs=agg_has_permission,
        post_filters=post_filters
    )
    # Create facet search query for no permission.
    no_permission_query[search_index] = dict(
        aggs=agg_no_permission,
        post_filters=post_filters
    )
    return has_permission_query, no_permission_query


def store_facet_search_query_in_redis():
    """Store query facet search in redis."""
    has_permission_query, no_permission_query = create_facet_search_query()
    # Store query for has permission.
    key = get_query_key_by_permission(True)
    value = json.dumps(has_permission_query)
    reset_redis_cache(key, value)
    # Store query for no permission.
    key = get_query_key_by_permission(False)
    value = json.dumps(no_permission_query)
    reset_redis_cache(key, value)


def get_query_key_by_permission(has_permission):
    """Get query key by permission."""
    if has_permission:
        return 'facet_search_query_has_permission'
    return 'facet_search_query_no_permission'


def get_facet_search_query(has_permission=True):
    """Get facet search query in redis."""
    search_index = current_app.config['SEARCH_UI_SEARCH_INDEX']
    key = get_query_key_by_permission(has_permission)
    # Check query exists in redis.
    query = json.loads(get_redis_cache(key) or '{}')
    if not is_exists_key_or_empty_in_redis(key) \
            or query.get(search_index, {}).get('post_filters', {}) == {} \
            or query.get(search_index, {}).get('aggs', {}) == {}:
        store_facet_search_query_in_redis()
    # Get query on redis.
    result = json.loads(get_redis_cache(key)) or {}
    # Update terms filter function for post filters.

    post_filters = result.get(search_index).get('post_filters')
    from weko_admin.utils import get_title_facets
    titles, order, uiTypes, isOpens, displayNumbers, searchConditions = get_title_facets()
    for k, v in post_filters.items():
        if v == 'temporal':
            # If the mapping name is [template], it is assumed to be a Filter to date_range1.
            post_filters.update({k: range_filter('date_range1', False, False)})
        else:
            # Set whether the Filter is an AND or OR condition from the facet definition.
            post_filters.update({k: terms_condition_filter(v, searchConditions[k] == 'AND')})
    return result


def get_title_facets():
    """Get title for facet search.

    return: dict
        key: name_en
        value:
            if lang = 'ja' : name_jp
            if lang = 'en' : name_en
    """
    lang = current_i18n.language
    titles = {}
    order = {}
    uiTypes = {}
    isOpens = {}
    displayNumbers = {}
    searchConditions = {}
    activated_facets = FacetSearchSetting.get_activated_facets()
    for item in activated_facets:
        titles[item.name_en] = item.name_jp if lang == 'ja' else item.name_en
        order[item.id] = item.name_en
        uiTypes[item.name_en] = item.ui_type
        isOpens[item.name_en] = item.is_open
        displayNumbers[item.name_en] = item.display_number
        searchConditions[item.name_en] = item.search_condition
    return titles, order, uiTypes, isOpens, displayNumbers, searchConditions


def is_exits_facet(data, id):
    """Check facet search is exits."""
    facet_by_name = FacetSearchSetting.get_by_name(data.get('name_en'),
                                                   data.get('name_jp'))
    facet_by_mapping = FacetSearchSetting.get_by_mapping(data.get('mapping'))
    if id and len(id) > 0:
        id = int(id)
        id_name = facet_by_name.id if facet_by_name else id
        id_mapping = facet_by_mapping.id if facet_by_mapping else id
        if (id == id_name) and (id == id_mapping):
            return False
    else:
        if (facet_by_name is None) and (facet_by_mapping is None):
            return False
    return True


def overwrite_the_memory_config_with_db(app, site_info):
    """Overwrite the memory Config values with the DB values."""
    if site_info:
        if site_info.google_tracking_id_user:
            if 'GOOGLE_TRACKING_ID_USER' in app.config:
                del app.config['GOOGLE_TRACKING_ID_USER']
            app.config.setdefault(
                'GOOGLE_TRACKING_ID_USER',
                site_info.google_tracking_id_user,
            )

def elasticsearch_reindex( is_db_to_es ):
    """
    reindex *-weko-item-* of elasticsearch index

    Args:
    is_db_to_es : boolean
        if True,  index Documents from DB data
        if False, index Documents from ES data itself

    Returns:
        str : 'completed'

    Raises:
    AssersionError
        In case of the response code from ElasticSearch is not 200,
        Subsequent processing is interrupted.

    Todo:
        warning: Simultaneous execution is prohibited.
        warning: Execution during operation is prohibited
                because documents submitted during execution may not be reflected.
                Please allow execution only during maintenance periods.
    """
    from invenio_oaiserver.percolator import _create_percolator_mapping
    # consts
    elasticsearch_host = os.environ.get('INVENIO_ELASTICSEARCH_HOST')
    base_url = 'http://' + elasticsearch_host + ':9200/'
    reindex_url = base_url + '_reindex?pretty&refresh=true&wait_for_completion=true'

    # "{}-weko-item-v1.0.0".format(prefix)
    index = current_app.config['INDEXER_DEFAULT_INDEX']
    tmpindex = "{}-tmp".format(index)

    # "{}-weko".format(prefix)
    alias_name = current_app.config['SEARCH_UI_SEARCH_INDEX']

    # get base_index_definition (mappings and settings)
    current_path = os.path.dirname(os.path.abspath(weko_schema_ui.__file__))
    file_path = os.path.join(current_path, 'mappings', 'v6', 'weko', 'item-v1.0.0.json')
    with open(file_path,mode='r') as json_file:
        json_data = json_file.read()
        base_index_definition = json.loads(json_data)

    number_of_replicas = base_index_definition.get("settings").get("number_of_replicas")
    refresh_interval = base_index_definition.get("settings").get("refresh_interval")

    headers = {
        'Content-Type': 'application/json',
    }
    json_data_to_tmp = {
        'source': {
            'index': index,
        },
        'dest': {
            'index': tmpindex,
        },
    }
    json_data_to_dest = {
        'source': {
            'index': tmpindex,
        },
        'dest': {
            'index': index,
        },
    }
    json_data_set_alias = {
        "actions" : [
            { "add" : { "index" : index, "alias" : alias_name } }
        ]
    }

    current_app.logger.info(' START elasticsearch reindex: {}.'.format(index))

    # トランザクションログをLucenceに保存。
    response = requests.post(base_url + index + "/_flush?wait_if_ongoing=true")
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text

    response = requests.get(base_url + '_cat/indices/?h=index&index=' + tmpindex )

    # 一時保管用のインデックスを作成
    # create tmp index
    current_app.logger.info("START create tmpindex")
    current_app.logger.info("PUT tmpindex")
    response = requests.put(base_url + tmpindex + "?pretty", headers=headers ,json=base_index_definition)
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("add setting percolator")

    _create_percolator_mapping(tmpindex, "item-v1.0.0")
    current_app.logger.info("END create tmpindex")

    # 高速化を期待してインデックスの設定を変更。
    current_app.logger.info("START change setting for faster")
    response = requests.put(base_url + tmpindex + "/_settings?pretty", headers=headers ,json={ "index" : {"number_of_replicas" : 0, "refresh_interval": -1 }})
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text #
    current_app.logger.info("END change setting for faster")


    # document count
    current_app.logger.info("index document count:{}".format(requests.get(base_url + "_cat/count/"+ index ).text))
    current_app.logger.info("tmpindex document count:{}".format(requests.get(base_url + "_cat/count/"+ tmpindex ).text))

    # 一時保管用のインデックスに元のインデックスの再インデックスを行う
    # reindex from index to tmpindex
    current_app.logger.info("START reindex")
    response = requests.post(url=reindex_url, headers=headers, json=json_data_to_tmp)
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("END reindex")

    # document count
    index_cnt = requests.get(base_url + "_cat/count/"+ index + "?h=count").text
    tmpindex_cnt = requests.get(base_url + "_cat/count/"+ tmpindex + "?h=count").text
    current_app.logger.info("index document count:{}".format(index_cnt))
    current_app.logger.info("tmpindex document count:{}".format(tmpindex_cnt))
    assert index_cnt == tmpindex_cnt,'Document counts do not match.'

    # 再インデックス前のインデックスを削除する
    current_app.logger.info("START delete index")
    response = requests.delete(base_url + index)
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("END delete index")

    # 新しくインデックスを作成する
    #create index
    current_app.logger.info("START create index")
    current_app.logger.info("PUT index")
    response = requests.put(url = base_url + index + "?pretty", headers=headers ,json=base_index_definition)
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("add setting percolator")
    _create_percolator_mapping(index, "item-v1.0.0")
    current_app.logger.info("END create index")

    # 高速化を期待してインデックスの設定を変更。
    current_app.logger.info("START change setting for faster")
    response = requests.put(base_url + index + "/_settings?pretty", headers=headers ,json={ "index" : {"number_of_replicas" : 0, "refresh_interval": -1 }})
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("END change setting for faster")

    # aliasを再設定する。
    current_app.logger.info("START re-regist alias")
    response = requests.post(base_url + "_aliases", headers=headers, json=json_data_set_alias )
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("END re-regist alias")

    # アイテムを再投入する。
    current_app.logger.info("START reindex")
    if is_db_to_es :
        current_app.logger.info("reindex es from db")
        response = _elasticsearch_remake_item_index(index_name=index)
        current_app.logger.info(response) # array

        response = requests.post(url=base_url + "_refresh")
        current_app.logger.info(response.text)
        assert response.status_code == 200 ,response.text
    else :
        current_app.logger.info("reindex es from es")
        # 一時保管用のインデックスから、新しく作成したインデックスに再インデックスを行う
        # reindex from tmpindex to index
        response = requests.post(url=reindex_url , headers=headers, json=json_data_to_dest)
        current_app.logger.info(response.text)
        assert response.status_code == 200 ,response.text
    current_app.logger.info("END reindex")

    # 高速化を期待して変更したインデックスの設定を元に戻す。
    current_app.logger.info("START revert setting for faster")
    response = requests.put(base_url + index + "/_settings?pretty", headers=headers ,json={ "index" : {"number_of_replicas" : number_of_replicas, "refresh_interval": refresh_interval }})
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("END revert setting for faster")

    # document count
    index_cnt = requests.get(base_url + "_cat/count/"+ index + "?h=count").text
    tmpindex_cnt = requests.get(base_url + "_cat/count/"+ tmpindex + "?h=count").text
    current_app.logger.info("index document count:{}".format(index_cnt))
    current_app.logger.info("tmpindex document count:{}".format(tmpindex_cnt))
    assert index_cnt == tmpindex_cnt ,'Document counts do not match.'


    # 一時保管用のインデックスを削除する
    # delete tmp-index
    current_app.logger.info("START delete tmpindex")
    response = requests.delete(base_url + tmpindex)
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("END delete tmpindex")

    current_app.logger.info(' END elasticsearch reindex: {}.'.format(index))

    return 'completed'

def _elasticsearch_remake_item_index(index_name):
    """ index Documents from DB (Private method) """
    from invenio_oaiserver.models import OAISet
    from invenio_oaiserver.percolator import _new_percolator
    returnlist = []
    # インデックスを登録
    current_app.logger.info(' START elasticsearch import from oaiserver_set')
    oaiset_ = OAISet.query.all()
    for target in oaiset_ :
        spec = target.spec
        search_pattern = target.search_pattern
        _new_percolator(spec , search_pattern)
    current_app.logger.info(' END elasticsearch import from oaiserver_set')

    # アイテムを登録
    current_app.logger.info(' START elasticsearch import from records_metadata')
    # get all registered record_metadata's ids
    uuids = (x[0] for x in PersistentIdentifier.query.filter_by(
        object_type='rec', status=PIDStatus.REGISTERED
    ).filter(
        PersistentIdentifier.pid_type.in_(['oai'])
    ).values(
        PersistentIdentifier.object_uuid
    ))
    indexer = RecordIndexer()
    for x in uuids:
        res = indexer.index_by_id(x)
        assert res != None ,'Index class is None.'
        assert res.get("_shards").get("failed") == 0 ,'Index fail.'
        returnlist.append(res)
    current_app.logger.info(' END elasticsearch import from records_metadata')

    return returnlist
