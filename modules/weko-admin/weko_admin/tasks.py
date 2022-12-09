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

"""Task for sending scheduled report emails."""

import os
import shutil
from datetime import datetime, timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from flask import current_app, render_template
from flask_babelex import gettext as _
from flask_mail import Attachment
from invenio_mail.api import send_mail
from invenio_stats.utils import QueryCommonReportsHelper, \
    QueryFileReportsHelper, QueryRecordViewPerIndexReportHelper, \
    QueryRecordViewReportHelper, QuerySearchReportHelper

from weko_admin.api import TempDirInfo

from .models import AdminSettings, StatisticsEmail
from .utils import StatisticMail, get_user_report_data, package_reports ,elasticsearch_reindex
from .views import manual_send_site_license_mail 
from celery.task.control import inspect
from .config import WEKO_ADMIN_SETTINGS_ELASTIC_REINDEX_SETTINGS,\
    WEKO_ADMIN_SETTINGS_ELASTIC_REINDEX_SETTINGS_HAS_ERRORED


logger = get_task_logger(__name__)


@shared_task(
    name = "weko_admin.tasks.reindex" 
    ,bind=True
    ,acks_late=False
    ,ignore_results=False)
def reindex(self, es_to_es , db_to_es ):
    """  
    
    note:elasticsearch_reindexの制限事項を理解した上で変更、修正を行ってください。
    
    Parameters
    ----------
    is_db_to_es : boolean
        Trueの場合、DBから取得したデータからDocumentsを作成します。
        Falseの場合、もともとの*-weko-item-*のDocumentsを再登録します。
    
    Returns
    -------
        'completed' : str
        
    Raises
    ------
    AssersionError 
        ElasticSearchからのレスポンスコードが200でなかった場合
        （後続処理は中断）
    """

    try:
        res = {}
        if es_to_es:
            result = elasticsearch_reindex(False)
            res.update({"es_to_es" : result})
        if db_to_es :
            # from .utils import _elasticsearch_remake_item_index
            # result = _elasticsearch_remake_item_index()
            result = elasticsearch_reindex(True)
            res.update({"db_to_es" : result})
        current_app.logger.info(res)
        return res
    except BaseException as ex:
        current_app.logger.error('Unexpected error',ex)
        # set error in admin_settings
        AdminSettings.update(WEKO_ADMIN_SETTINGS_ELASTIC_REINDEX_SETTINGS 
        , dict({WEKO_ADMIN_SETTINGS_ELASTIC_REINDEX_SETTINGS_HAS_ERRORED:True}))
        raise

def is_reindex_running():
    """Check import is running."""
    
    if not _check_celery_is_run():
        return False

    active = inspect().active()
    for worker in active:
        for task in active[worker]:
            current_app.logger.info("active")
            current_app.logger.info(task)
            if task["name"] == "weko_admin.tasks.reindex":
                current_app.logger.info("weko_admin.tasks.reindex is active")
                return True

    reserved = inspect().reserved()
    for worker in reserved:
        for task in reserved[worker]:
            current_app.logger.info("reserved")
            current_app.logger.info(task)
            if task["name"] == "weko_admin.tasks.reindex":
                current_app.logger.info("weko_admin.tasks.reindex is reserved")
                return True
    
    current_app.logger.info("weko_admin.tasks.reindex is not running")
    return False

def _check_celery_is_run():
    """Check celery is running, or not."""
    if not inspect().ping():
        return False
    else:
        return True


@shared_task(ignore_results=True)
def send_all_reports(report_type=None, year=None, month=None):
    """Query elasticsearch for each type of stats report."""
    # By default get the current month and year
    now = datetime.now()
    month = month or now.month
    year = year or now.year
    all_results = {
        'file_download': QueryFileReportsHelper.get(
            year=year, month=month, event='file_download'),
        'file_preview': QueryFileReportsHelper.get(
            year=year, month=month, event='file_preview'),
        'index_access': QueryRecordViewPerIndexReportHelper.get(
            year=year, month=month),
        'detail_view': QueryRecordViewReportHelper.get(
            year=year, month=month),
        'file_using_per_user': QueryFileReportsHelper.get(
            year=year, month=month, event='file_using_per_user'),
        'top_page_access': QueryCommonReportsHelper.get(
            year=year, month=month, event='top_page_access'),
        'search_count': QuerySearchReportHelper.get(
            year=year, month=month),
        'user_roles': get_user_report_data(),
        'site_access': QueryCommonReportsHelper.get(
            year=year, month=month, event='site_access')
    }
    with current_app.app_context():
        # Allow for this to be used to get specific emails as well
        reports = {}
        if report_type is not None and report_type in all_results:
            reports[report_type] = all_results[report_type]
        else:
            reports = all_results

        zip_date = str(year) + '-' + str(month).zfill(2)
        zip_name = 'logReport_' + zip_date + '.zip'
        zip_stream = package_reports(reports, year, month)

        recepients = StatisticsEmail.get_all_emails()
        attachments = [Attachment(zip_name,
                                  'application/x-zip-compressed',
                                  zip_stream.getvalue())]
        html_body = render_template(
            current_app.config['WEKO_ADMIN_REPORT_EMAIL_TEMPLATE'],
            report_date=zip_date,
            attached_file=zip_name)
        subject = zip_date + _(' Log report.')
        try:
            send_mail(subject, recepients, html=html_body,
                      attachments=attachments)
            current_app.logger.info('[{0}] [{1}] '.format(0, 'Sent email'))
        except Exception as e:
            current_app.logger.info('[{0}] [{1}] '.format(1, 'Could not send'))


@shared_task(ignore_results=True)  # Set for timedelta(days=1)
def check_send_all_reports():
    """Check Redis periodically for when to run a task."""
    with current_app.app_context():
        # Schedule set in the view
        schedule = AdminSettings.get(name='report_email_schedule_settings',
                                     dict_to_object=False)
        schedule = schedule if schedule else None
        if schedule and _due_to_run(schedule):
            send_all_reports.delay()


@shared_task(ignore_results=True)
def send_feedback_mail():
    """Check Redis periodically for when to run a task."""
    with current_app.app_context():
        StatisticMail.send_mail_to_all()


def _due_to_run(schedule):
    """Check if a task needs to be ran."""
    if not schedule['enabled']:
        return False
    now = datetime.now()
    return (schedule['frequency'] == 'daily') or \
        (schedule['frequency'] == 'weekly'
         and int(schedule['details']) == now.weekday()) or \
        (schedule['frequency'] == 'monthly'
         and int(schedule['details']) == now.day)


@shared_task(ignore_results=True)
def check_send_site_access_report():
    """Check send site access report."""
    settings = AdminSettings.get('site_license_mail_settings')
    if settings and settings.auto_send_flag:
        agg_month = \
            current_app.config.get('WEKO_ADMIN_DEFAULT_AGGREGATION_MONTH', 1)
        # Previous months
        end_date = datetime.utcnow().replace(day=1) - timedelta(days=1)
        count = 1
        start_date = end_date.replace(day=1)
        while count < agg_month:
            start_date = (start_date - timedelta(days=1)).replace(day=1)
            count = count + 1
        end_month = end_date.strftime('%Y-%m')
        start_month = start_date.strftime('%Y-%m')
        # send mail api
        manual_send_site_license_mail(start_month=start_month,
                                      end_month=end_month)


@shared_task(ignore_results=True)
def clean_temp_info():
    """A schedule task for clean temporary information."""
    temp_dir_api = TempDirInfo()
    datas = temp_dir_api.get_all()
    for temp_path, extra_info in datas.items():
        can_delete = False
        if not os.path.exists(temp_path):
            can_delete = True
        else:
            expire = extra_info.get('expire', '')
            if not expire:
                continue
            if expire < datetime.now().strftime('%Y-%m-%d %H:%M:%S'):
                can_delete = True
                shutil.rmtree(temp_path)
        if can_delete:
            temp_dir_api.delete(temp_path)
