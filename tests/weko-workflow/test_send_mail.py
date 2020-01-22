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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""WEKO3 pytest docstring."""


import os
from functools import wraps

import pytest
from invenio_accounts.models import User
from mock import mock, patch
from pytest_invenio.fixtures import app, database, es_clear
from send_mail_helpers import insert_action_data_to_db, \
    insert_activity_data_to_db, insert_history_doing_data_to_db, \
    insert_history_done_data_to_db, insert_metadata_to_db, insert_user_to_db, \
    login_user_via_session
from weko_user_profiles.config import WEKO_USERPROFILES_ADMINISTRATOR_ROLE, \
    WEKO_USERPROFILES_GENERAL_ROLE, WEKO_USERPROFILES_GRADUATED_STUDENT_ROLE
from weko_workflow.api import WorkActivity
from weko_workflow.models import Activity
from weko_workflow.views import process_send_notification_mail


def test_send_reminder_mail(app, database, client, mailbox, es_clear):
    """Test_send_reminder_mail."""
    # # enable when run function alone
    insert_user_to_db(database)
    login_user_via_session(client, 1)
    insert_metadata_to_db(database)
    insert_activity_data_to_db(database)

    current_user = mock.MagicMock()
    current_user.email = 'test01@hitachi.com'
    assert len(mailbox) == 0
    user_info = dict(
        email='info@inveniosoftware.org',
        username='admin'
    )
    wrong_user_info = dict(
        email='',
        username=''
    )
    with mock.patch("weko_workflow.utils.current_user", current_user), \
        mock.patch(
            "weko_items_ui.utils.get_user_information",
            return_value=user_info):

        # Test fail 1: wrong template: 1, 3
        client.post(
            '/workflow/send_mail/A-20191218-00007/email_pattern_20.tpl')
        assert len(mailbox) == 0

        # Test fail 2: sender not found: 2
        client.post(
            '/workflow/send_mail/A-20191218-00007/email_pattern_11.tpl')
        assert len(mailbox) == 0

    with mock.patch("weko_workflow.utils.current_user", current_user), \
        mock.patch("weko_items_ui.utils.get_user_information",
                   return_value=wrong_user_info):
        # Test fail 3: user doesn't have email: 4
        client.post(
            '/workflow/send_mail/A-20191218-00007/email_pattern_11.tpl')
        assert len(mailbox) == 0

    from invenio_mail.admin import _load_mail_cfg_from_db, _save_mail_cfg_to_db
    mail_cfg = _load_mail_cfg_from_db()
    mail_cfg['mail_default_sender'] = 'info@inveniosoftware.org'
    _save_mail_cfg_to_db(mail_cfg)

    with mock.patch("weko_workflow.utils.current_user", current_user), \
        mock.patch("weko_items_ui.utils.get_user_information",
                   return_value=user_info):
        client.post(
            '/workflow/send_mail/A-20191218-00007/email_pattern_11.tpl')
        assert len(mailbox) == 1


def test_index(app, database, client, es_clear):
    """Test_index."""
    insert_action_data_to_db(database)
    insert_history_doing_data_to_db(database)
    # insert_user_to_db(database)
    # login_user_via_session(client,1)
    # insert_activity_data_to_db(database)
    # insert_full_action_data_to_db(database)

    user = mock.MagicMock()
    user.roles = [WEKO_USERPROFILES_ADMINISTRATOR_ROLE]

    activities = Activity.query.filter_by().all()
    for item_activity in activities:
        setattr(item_activity, "User", User.query.filter_by(
            id=item_activity.activity_update_user).first())
        setattr(item_activity, "type", 'ToDo')

    req_test_index(activities, user, client)
    insert_history_done_data_to_db(database)
    req_test_index(activities, user, client)


def test_send_mail(app, database, client, mailbox, es_clear):
    """Test_send_mail."""
    assert len(mailbox) == 0
    user = mock.MagicMock()
    user.roles = WEKO_USERPROFILES_GRADUATED_STUDENT_ROLE
    user.email = 'info@inveniosoftware.org'

    general_user = mock.MagicMock()
    general_user.roles = WEKO_USERPROFILES_GENERAL_ROLE
    general_user.email = 'info@inveniosoftware.org'

    unknown_user = mock.MagicMock()
    unknown_user.roles = None
    unknown_user.email = ''

    # enable when run function alone
    # insert_user_to_db(database)
    # login_user_via_session(client,1)
    # insert_metadata_to_db(database)
    # insert_activity_data_to_db(database)
    # insert_action_data_to_db(database)
    # insert_history_done_data_to_db(database)

    # send 1 mail success: pattern 13
    send_mail(user, 'A-20191218-00007', 13,
              'e8492239-8e49-47b3-93c3-5081a96aaf05', 'item_login',
              'approval_advisor', '利用報告')
    assert len(mailbox) == 1

    # insert_full_action_data_to_db(database)
    # send 1 mail success: pattern 14
    send_mail(user, 'A-20191218-00007', 13,
              'e8492239-8e49-47b3-93c3-5081a96aaf05', 'item_login',
              'approval_advisor', '成果物登録')
    assert len(mailbox) == 2

    # send 1 mail success: pattern 15
    send_mail(user, 'A-20191218-00007', 13,
              'e8492239-8e49-47b3-93c3-5081a96aaf05', 'approval_administrator',
              'end_action', '利用報告')
    assert len(mailbox) == 3

    # send 1 mail success: pattern 16
    send_mail(user, 'A-20191218-00007', 13,
              'e8492239-8e49-47b3-93c3-5081a96aaf05', 'approval_administrator',
              'end_action', '成果物登録')
    assert len(mailbox) == 4

    # send 2 mail success: pattern 4,8_1
    send_mail(general_user, 'A-20191218-00007', 13,
              'e8492239-8e49-47b3-93c3-5081a96aaf05', 'item_login',
              'approval_advisor', 'ライフ利用申請')
    assert len(mailbox) == 6

    # send 2 mail success: pattern 5,8_1
    send_mail(user, 'A-20191218-00007', 13,
              'e8492239-8e49-47b3-93c3-5081a96aaf05', 'item_login',
              'approval_advisor', 'ライフ利用申請')
    assert len(mailbox) == 8

    # send 2 mail success: pattern 6,8_1
    send_mail(general_user, 'A-20191218-00007', 13,
              'e8492239-8e49-47b3-93c3-5081a96aaf05', 'item_login',
              'approval_advisor', '都道府県利用申請')
    assert len(mailbox) == 10

    # send 2 mail success: pattern 7,8_2
    send_mail(user, 'A-20191218-00007', 13,
              'e8492239-8e49-47b3-93c3-5081a96aaf05', 'item_login',
              'approval_guarantor', '地点情報利用申請')
    assert len(mailbox) == 12

    # send 1 mail success: pattern 9
    send_mail(general_user, 'A-20191218-00007', 13,
              'e8492239-8e49-47b3-93c3-5081a96aaf05', 'approval_administrator',
              'end_action', 'ライフ利用申請')
    assert len(mailbox) == 13

    #  send 1 mail success: pattern 10
    send_mail(general_user, 'A-20191218-00007', 13,
              'e8492239-8e49-47b3-93c3-5081a96aaf05', 'approval_administrator',
              'end_action', '地点情報利用申請')
    assert len(mailbox) == 14

    #  send 1 mail fail: wrong item type name 7
    send_mail(general_user, 'A-20191218-00007', 13,
              'e8492239-8e49-47b3-93c3-5081a96aaf05', 'approval_administrator',
              'end_action', 'ABC')
    assert len(mailbox) == 14

    #  send 1 mail fail: wrong item type name 5
    send_mail(general_user, 'A-20191218-00007', 13,
              'e8492239-8e49-47b3-93c3-5081a96aaf05', 'item_login',
              'approval_guarantor', 'ABC')
    assert len(mailbox) == 14

    #  send 1 mail fail: role not found
    send_mail(unknown_user, 'A-20191218-00007', 13,
              'e8492239-8e49-47b3-93c3-5081a96aaf05', 'item_login',
              'approval_administrator', '地点情報利用申請')
    assert len(mailbox) == 14

    #  send 1 mail fail: cannot get item data (wrong item_id)
    send_mail(general_user, 'A-20191218-00007', 13,
              'f8492239-8e49-47b3-93c3-5081a96aaf05', 'approval_administrator',
              'end_action', 'ABC')
    assert len(mailbox) == 14

    wrong_config = dict(
        WEKO_WORKFLOW_ENGLISH_MAIL_TEMPLATE_FOLDER_PATH='/code/modules/en',
        WEKO_WORKFLOW_JAPANESE_MAIL_TEMPLATE_FOLDER_PATH='/code/modules/ja',
        WEKO_ITEMS_UI_APPLICATION_FOR_LIFE="ライフ利用申請",
        WEKO_ITEMS_UI_APPLICATION_FOR_ACCUMULATION="累積利用申請",
        WEKO_ITEMS_UI_APPLICATION_FOR_COMBINATIONAL_ANALYSIS="組合せ分析利用申請",
        WEKO_ITEMS_UI_APPLICATION_FOR_PERFECTURES="都道府県利用申請",
        WEKO_ITEMS_UI_APPLICATION_FOR_LOCATION_INFORMATION="地点情報利用申請",
        WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPES_LIST=[
            "ライフ利用申請", "累積利用申請", "組合せ分析利用申請",
            "都道府県利用申請", "地点情報利用申請"
        ],
        WEKO_WORKFLOW_APPROVE_USAGE_APP_BESIDE_LOCATION_DATA='email_pattern_9'
                                                             '.tpl',
        WEKO_WORKFLOW_APPROVE_LOCATION_DATA='email_pattern_10.tpl'
    )
    with mock.patch("weko_workflow.utils.current_app.config", wrong_config):
        #  send 1 mail fail: wrong path config
        send_mail(general_user, 'A-20191218-00007', 13,
                  'e8492239-8e49-47b3-93c3-5081a96aaf05',
                  'approval_administrator', 'end_action', '地点情報利用申請')
        assert len(mailbox) == 14

    class JPLanguage:
        language = 'ja'

    japanese = JPLanguage()
    with mock.patch("weko_workflow.utils.current_i18n", japanese):
        #  send 1 mail success: language = japanese
        send_mail(general_user, 'A-20191218-00007', 13,
                  'e8492239-8e49-47b3-93c3-5081a96aaf05',
                  'approval_administrator', 'end_action', '地点情報利用申請')
        assert len(mailbox) == 15


def send_mail(user, activity_id, workflow_id, item_id, current_step,
              next_step, item_type_name):
    """Send_mail."""
    from weko_workflow.views import process_send_notification_mail

    with mock.patch("weko_workflow.utils.current_user", user), \
        mock.patch("weko_workflow.utils.get_current_user_role",
                   return_value=user.roles), \
        mock.patch("weko_workflow.utils.get_item_type_name",
                   return_value=item_type_name):
        activity_detail = Activity()
        activity_detail.workflow_id = workflow_id
        activity_detail.item_id = item_id
        activity_detail.activity_id = activity_id
        process_send_notification_mail(activity_detail,
                                       current_step,
                                       next_step)


def req_test_index(activities, user, client):
    """Req_test_index."""
    with mock.patch("weko_workflow.api.WorkActivity.get_activity_list",
                    return_value=activities),\
            mock.patch("weko_workflow.views.current_user", user):
        res = client.get('/workflow/')
        expect_activity_id = b'A-20191218-00007'
        assert expect_activity_id in res.data
