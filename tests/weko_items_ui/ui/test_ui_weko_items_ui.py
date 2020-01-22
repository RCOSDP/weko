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

"""WEKO3 pytest docstring."""

from helpers import insert_access, insert_user_to_db, login_user_via_session
from mock import mock, patch
from weko_workflow.models import Activity


def test_ui(app, database, client):
    """Test UI."""
    from weko_deposit.api import WekoRecord
    insert_user_to_db(database)
    login_user_via_session(client, 1)
    activity_result = Activity()
    activity_result.workflow_id = '132'
    steps = [
        {
            'ActionEndpoint': 'begin_action',
            'ActionName': 'Start',
            'ActivityId': 'A-20191217-00004',
            'Author': 'info@inveniosoftware.org',
            'Status': 'action_done',
            'ActionId': 1,
            'ActionVersion': '1.0.0'
        },
        {
            'ActionEndpoint': 'item_login_application',
            'ActionName': 'Item Registration for Usage Application',
            'ActivityId': 'A-20191217-00004',
            'Author': 'info@inveniosoftware.org',
            'Status': 'action_done',
            'ActionId': 8,
            'ActionVersion': '1.0.1'
        },
        {
            'ActionEndpoint': 'approval_advisor',
            'ActionName': 'Adivisor Approval',
            'ActivityId': 'A-20191217-00004',
            'Author': '',
            'Status': ' ',
            'ActionId': 9,
            'ActionVersion': '1.0.0'
        },
        {
            'ActionEndpoint': 'approval_guarantor',
            'ActionName': 'Guarantor Approval',
            'ActivityId': 'A-20191217-00004clear',
            'Author': '',
            'Status': ' ',
            'ActionId': 10,
            'ActionVersion': '1.0.0'
        }
    ]
    with client.session_transaction() as sess:
        sess['itemlogin_activity'] = activity_result
        sess['itemlogin_steps'] = steps
    with patch.object(
        WekoRecord,
        'get_record_by_pid',
        return_value={
            '1': '2'
        }
    ), mock.patch(
        'weko_items_ui.views.get_index_id',
        return_value='123'
    ), mock.patch(
        'weko_items_ui.views.update_index_tree_for_record',
        return_value='123'
    ):
        insert_access()
        res = client.get('/items/iframe/index/123')
        # If success, It will redirect to iframe_success
        assert res.status_code == 302
