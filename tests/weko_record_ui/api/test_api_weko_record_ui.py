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

from mock import mock, patch
from pytest_invenio.fixtures import app, es_clear
from weko_records_ui.permissions import check_created_id


class User:
    """Test check created id."""

    name = ''


def test_check_created_id(app, es_clear):
    """Test check created id."""
    record = {"_deposit": {
        "id": "55.1",
        "pid": {
            "type": "recid",
            "value": "55.1",
            "revision_id": 0
        },
        "owners": [
            1
        ],
        "status": "published",
        "created_by": 1
    }, "item_type_id": "6", }

    with app.app_context(), mock.patch(
            'weko_records.serializers.utils.get_item_type_name',
            return_value="ライフ利用申請"
         ):
        mock_user = mock.MagicMock()
        mock_user.get_id.return_value = '1'
        mock_user.is_authenticated = True
        admin = User
        admin.name = 'Administrator'
        mock_user.roles = [admin]
        # User is admin,,should have permission
        with mock.patch('weko_records_ui.permissions.current_user', mock_user):
            assert check_created_id(record)
        non_admin = User
        non_admin.name = 'General'
        mock_user.roles = [non_admin]
        # User is not admin but author,should have permission
        with mock.patch('weko_records_ui.permissions.current_user', mock_user):
            assert check_created_id(record)
        # User is not admin nor author,should not have permission
        mock_user.get_id.return_value = '2'
        with mock.patch('weko_records_ui.permissions.current_user', mock_user):
            assert not check_created_id(record)
