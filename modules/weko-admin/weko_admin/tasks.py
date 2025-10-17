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

from .models import AdminSettings, StatisticsEmail, FeedbackMailSetting
from .utils import StatisticMail, get_user_report_data, package_reports ,elasticsearch_reindex
from .views import manual_send_site_license_mail
from celery.task.control import inspect
from weko_search_ui.tasks import check_celery_is_run
from .config import WEKO_ADMIN_SETTINGS_ELASTIC_REINDEX_SETTINGS,\
    WEKO_ADMIN_SETTINGS_ELASTIC_REINDEX_SETTINGS_HAS_ERRORED


logger = get_task_logger(__name__)


@shared_task(
    name = "weko_admin.tasks.reindex"
    ,bind=True
    ,acks_late=False
    ,ignore_results=False)
def reindex(self, is_db_to_es ):
    """
    Celery task to do elasticsearch_reindex
    if error has occord in elasticsearch_reindex , update admin_settings

    Args:
    self : any
        object assigned by "bind=True"
    is_db_to_es : boolean
        if True,  index Documents from DB data
        if False, index Documents from ES data itself

    Returns:
        str : elasticsearch_reindex responce text

    Raises:
        raises error in elasticsearch_reindex

    Todo:
        if you change this codes, please keep in mind Todo of the method "elasticsearch_reindex"
        in .utils.py .
    """

    try:
        return elasticsearch_reindex(is_db_to_es)
    except BaseException as ex:
        # set error in admin_settings
        AdminSettings.update(WEKO_ADMIN_SETTINGS_ELASTIC_REINDEX_SETTINGS
        , dict({WEKO_ADMIN_SETTINGS_ELASTIC_REINDEX_SETTINGS_HAS_ERRORED:True}))
        raise ex

def is_reindex_running():
    """Check reindex is running."""

    if not check_celery_is_run():
        return False

    _timeout = current_app.config.get("CELERY_GET_STATUS_TIMEOUT", 3.0)
    reserved = inspect(timeout=_timeout).reserved()
    active = inspect(timeout=_timeout).active()
    for worker in active:
        for task in active[worker]:
            current_app.logger.debug("active")
            current_app.logger.debug(task)
            if task["name"] == "weko_admin.tasks.reindex":
                current_app.logger.info("weko_admin.tasks.reindex is active")
                return True

    for worker in reserved:
        for task in reserved[worker]:
            current_app.logger.debug("reserved")
            current_app.logger.debug(task)
            if task["name"] == "weko_admin.tasks.reindex":
                current_app.logger.info("weko_admin.tasks.reindex is reserved")
                return True

    current_app.logger.debug("weko_admin.tasks.reindex is not running")
    return False

@shared_task(ignore_results=True)
def send_all_reports(report_type=None, year=None, month=None, repository_id=None):
    """Query elasticsearch for each type of stats report."""
    # By default get the current month and year
    now = datetime.now()
    month = month or now.month
    year = year or now.year
    repository_id = repository_id or 'Root Index'
    all_results = {
        'file_download': QueryFileReportsHelper.get(
            year=year, month=month, event='file_download', repository_id=repository_id),
        'file_preview': QueryFileReportsHelper.get(
            year=year, month=month, event='file_preview', repository_id=repository_id),
        'index_access': QueryRecordViewPerIndexReportHelper.get(
            year=year, month=month, repository_id=repository_id),
        'detail_view': QueryRecordViewReportHelper.get(
            year=year, month=month, repository_id=repository_id),
        'file_using_per_user': QueryFileReportsHelper.get(
            year=year, month=month, event='file_using_per_user', repository_id=repository_id),
        'top_page_access': QueryCommonReportsHelper.get(
            year=year, month=month, event='top_page_access'),
        'search_count': QuerySearchReportHelper.get(
            year=year, month=month, repository_id=repository_id),
        'user_roles': get_user_report_data(repo_id=repository_id),
        'site_access': QueryCommonReportsHelper.get(
            year=year, month=month, event='site_access', repository_id=repository_id),
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

        recepients = StatisticsEmail.get_emails_by_repo(repository_id=repository_id)
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
        schedules = AdminSettings.get(name='report_email_schedule_settings',
                                     dict_to_object=False)
        schedules = schedules if schedules else {}
        for repository_id, schedule in schedules.items():
            if schedule and _due_to_run(schedule):
                send_all_reports.delay(repository_id=repository_id)


@shared_task(ignore_results=True)
def send_feedback_mail():
    """Check Redis periodically for when to run a task."""
    with current_app.app_context():
        setting = FeedbackMailSetting.get_feedback_email_setting_by_repo(repo_id='Root Index')
        if setting:
            if setting[0].is_sending_feedback:
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
    settings = AdminSettings.get('site_license_mail_settings',dict_to_object=False)
    for repository_id, setting in settings.items():
        if setting and setting.get("auto_send_flag"):
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
                                        end_month=end_month, repo_id=repository_id)


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
                if extra_info.get("is_export"):
                    from weko_search_ui.utils import delete_exported
                    can_delete = delete_exported(temp_path,extra_info)
                else:
                    shutil.rmtree(temp_path)
                    can_delete = True
        if can_delete:
            temp_dir_api.delete(temp_path)
