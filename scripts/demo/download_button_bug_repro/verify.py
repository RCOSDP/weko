# -*- coding: utf-8 -*-
"""Verify that the download-button bug reproduces for the demo fixture.

Usage (inside the web container, after load.sh)::

    docker compose exec -T web invenio shell \
        /code/scripts/demo/download_button_bug_repro/verify.py

Expected output (= bug present)::

    activity_status                : activity_completed   <- approved & finished
    file_permission rows           : 0                    <- row was destroyed
    file_permission status=1 rows  : 0                    <- never written at all
    file_onetime_download          : ... contributor@example.org ...
    check_file_download_permission : False                <- no Download button
    get_permission                 : None                 <- -> "Apply" button
    rendered button                : ... term-condtion-modal / btn-start-workflow
"""
from __future__ import print_function

import re

from flask import current_app, render_template_string, session
from flask_login import login_user
from flask_security import url_for_security
from invenio_accounts.models import User
from weko_deposit.api import WekoRecord
from weko_records_ui.models import FileOnetimeDownload, FilePermission
from weko_records_ui.permissions import (
    check_content_clickable,
    check_file_download_permission,
    get_permission,
)
from weko_workflow.models import Activity

TARGET_RECID = '2003976'
ACTIVITY_ID = 'A-20260917-00001'
FILE_KEY = 'item_1617605131499'

activity = Activity.query.filter_by(activity_id=ACTIVITY_ID).one()
print('activity_status                :', activity.activity_status)
print('file_permission rows           :', FilePermission.query.filter_by(
    usage_application_activity_id=ACTIVITY_ID).count())
print('file_permission status=1 rows  :', FilePermission.query.filter_by(
    record_id=TARGET_RECID, status=1).count())
for fod in FileOnetimeDownload.query.filter_by(record_id=TARGET_RECID).all():
    print('file_onetime_download          :', fod.file_name, fod.user_mail,
          fod.extra_info)

user = User.query.filter_by(email='contributor@example.org').one()
record = WekoRecord.get_record_by_pid(TARGET_RECID)
fjson = record[FILE_KEY]['attribute_value_mlt'][0]

tpl = ("{% from 'weko_records_ui/_macros.html' import check_download_file %}"
       "{{ check_download_file(record, file, permission, None,"
       " url_for_security, False, file.filename) }}")

with current_app.test_request_context(
        'https://localhost/records/' + TARGET_RECID):
    login_user(user)
    access_permission = check_file_download_permission(record, fjson)
    clickable = check_content_clickable(record, fjson)
    permission = get_permission(record, fjson)
    session['user_id'] = user.id
    html = render_template_string(tpl, record=record, file=fjson,
                                  permission=permission,
                                  url_for_security=url_for_security)

print('check_file_download_permission :', access_permission)
print('get_permission                 :', permission)
print('check_content_file_clickable   :', clickable)
print('rendered button classes        :',
      re.findall(r'<button[^>]*class="([^"]*)"', html))
print('rendered download href present :',
      '/files/sample_restricted_data.txt' in html)
print('')
if not access_permission and permission is None:
    print('=> BUG REPRODUCED: the approved applicant gets the "Apply" button.')
else:
    print('=> Bug NOT reproduced (fix applied?).')
