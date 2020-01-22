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

from invenio_accounts.models import Role
from mock import mock, patch
from pytest_invenio.fixtures import app, database


def insert_data_for_activity(database):
    """Insert data for activity."""
    from weko_workflow.models import ActivityAction, ActionStatus
    flow_id = "ed1fc1a1-db3d-450c-a093-b85e63d3d647"
    item_id = "f7ab31d0-f401-4e60-adc9-000000000111"
    record = {
        'item_1574156725144': {
            'subitem_usage_location': 'sage location',
            'pubdate': '2019-12-08',
            '$schema': '/items/jsonschema/19',
            'title': 'username'
        }
    }
    from helpers import insert_activity, insert_flow, insert_record_metadata,\
        insert_workflow, insert_action_to_db, insert_flow_action,\
        insert_item_type_name, insert_item_type, insert_activity_action

    insert_record_metadata(database, item_id, record)
    insert_flow(database, 1, flow_id, "Flow Name", 1, "A")
    insert_item_type_name(database, "地点情報利用申請", True, True)
    insert_item_type(database, 1, {}, {}, {}, 1, 1, True)
    insert_action_to_db(database)

    # Insert a flow contain 5 steps

    insert_flow_action(database, flow_id, 1, 1)
    insert_flow_action(database, flow_id, 2, 5)
    insert_flow_action(database, flow_id, 8, 2)
    insert_flow_action(database, flow_id, 9, 3)
    insert_flow_action(database, flow_id, 11, 4)
    insert_workflow(database, 1, flow_id, "Flow Name", 1, 1, 1)
    insert_activity(database, "A-20200108-00100", item_id, 1, 1, 8)
    action_status = ActionStatus(
        action_status_id="A",
        action_status_name="Name"
    )
    database.session.add(action_status)
    database.session.commit()
    insert_activity_action(database, "A-20200108-00100", 8, 2)


def test_update_action_handler(app, database, client):
    """Test update action handler."""
    from helpers import login_user_via_session, insert_user_to_db
    insert_user_to_db(database)
    insert_data_for_activity(database)
    login_user_via_session(client, 1)
    from weko_items_ui.utils import update_action_handler, \
        get_user_info_by_email
    update_action_handler("A-20200108-00100", 8, 1)


def get_user_info_by_email(app, database, client):
    """Get user info by email."""
    from weko_items_ui.utils import get_user_info_by_email
    # Normal
    assert get_user_info_by_email("info@inveniosoftware.org").get('email') == \
        'info@inveniosoftware.org'
    # Non-Profile
    assert get_user_info_by_email("info@inveniosoftware.org").get('email') == \
        'admin@inveniosoftware.org'
    # Execption
    with mock.patch('weko_items_ui.utils.db.session.query', return_value="1"):
        assert 'NoneType' in get_user_info_by_email(
            "admin@inveniosoftware.org"
        ).get('error')


def test_is_need_to_show_agreement_page():
    """Test is need to show agreent page."""
    from weko_items_ui.utils import is_need_to_show_agreement_page
    with mock.patch(
        'weko_items_ui.utils.get_current_user_role',
        return_value='General'
    ):
        assert not is_need_to_show_agreement_page("ライフ利用申請")
        assert is_need_to_show_agreement_page("Return False")


def test_get_current_user_role():
    """Test get current user role."""
    m1 = mock.MagicMock()
    m1.roles = ['General']
    from weko_items_ui.utils import get_current_user_role
    with mock.patch('weko_items_ui.utils.current_user', m1):
        assert get_current_user_role()


def test_recursive_form():
    """Test recursive form."""
    from weko_items_ui.utils import recursive_form
    target_form = [{
        "key": "pubdate",
        "type": "template"
    }, {
        "key": "item_1574156824929",
        "type": "fieldset",
        "items": [
            {
                "key": "item_1574156824929.subitem_advisor_position",
                "type": "select",
                "title": "Position"
            },
            {
                "key": "item_1574156824929.subitem_advisor_position(other)",
                "type": "text",
                "title": "Position(Others)"
            }
        ],
        "title": "Advisor"
    }]
    recursive_form(target_form)
    # Data of titleMap after should be not empty
    assert len(target_form[1].get('items', [])[0].get('titleMap')) > 0


def side_effect_deposit(*args, **kwargs):
    """Side effect deposit."""
    return None


def test_update_index_tree_for_record():
    """Test update index tree for record."""
    from weko_items_ui.utils import update_index_tree_for_record
    from weko_deposit.api import WekoRecord
    m = mock.MagicMock()
    m.return_value.update = side_effect_deposit
    m.return_value.commit = side_effect_deposit
    data = {
        'item_1574156962829': {
            'attribute_value_mlt': [
                {
                    'subitem_1574055330661': 'esearch Title'
                }
            ],
            'attribute_name': 'Research Title'
        },
        'path': ['1576561016241']
    }
    record = WekoRecord(data, model=123)
    with patch.object(
        WekoRecord,
        'get_record_by_pid',
        return_value=record
    ), mock.patch('weko_items_ui.utils.WekoDeposit', m):
        assert not update_index_tree_for_record(1, 1)
