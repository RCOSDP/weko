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

import json
from datetime import datetime

from celery import shared_task
from celery.utils.log import get_task_logger
from flask import current_app, render_template
from flask_babelex import gettext as _
from flask_mail import Attachment
from invenio_mail.api import send_mail
from invenio_stats.utils import QueryCommonReportsHelper, \
    QueryFileReportsHelper, QueryRecordViewPerIndexReportHelper, \
    QueryRecordViewReportHelper, QuerySearchReportHelper

from .models import StatisticsEmail
from .utils import StatisticMail, get_redis_cache, get_user_report_data, \
    package_reports

logger = get_task_logger(__name__)


@shared_task(ignore_results=True)
def send_all_reports(report_type=None, year=None, month=None):
    """Query elasticsearch for each type of stats report."""
    # By default get the current month and year
    now = datetime.now()
    month = month or now.month
    year = year or now.year
    tsv_files = []
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
        current_app.logger.info(
            '[{0}] [{1}] '.format(0, 'Got all stats reports'))

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
        current_app.logger.info(
            '[{0}] [{1}] '.format(0, 'Checking if report emails are due'))

        cache_key = current_app.config['WEKO_ADMIN_CACHE_PREFIX']. \
            format(name='email_schedule')
        schedule = get_redis_cache(cache_key)  # Schedule set in the view
        schedule = json.loads(schedule) if schedule else None
        if schedule and _due_to_run(schedule):
            current_app.logger.info(
                '[{0}] [{1}] '.format(0, 'Started report email task'))
            send_all_reports.delay()


@shared_task(ignore_results=True)  # Set for timedelta(days=1)
def send_feedback_mail():
    """Check Redis periodically for when to run a task."""
    with current_app.app_context():
        # TODO: Implement code auto send email here
        # StatisticMail.send_mail_to_all()
        StatisticMail.send_mail('weko-ope@nii.ac.jp', 'This is a test mail.',
                                'Test statistic mail')


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
