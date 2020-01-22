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

import os

import pytest
from helpers import insert_user_to_db, login_user_via_session
from mock import mock
from pytest_invenio.fixtures import app, database, es_clear
from weko_admin.models import SiteInfo
from weko_admin.utils import format_site_info_data, \
    get_notify_for_current_language, validation_site_info
from weko_admin.views import get_site_info


def test_update_site_info(app, database, es_clear):
    """Test update site info."""
    site_info = {
        'copy_right': "",
        'description': "",
        'favicon':
            "https://community.repo.nii.ac.jp/images/common/favicon.ico",
        'favicon_name': "JAIRO Cloud icon",
        'notify': [
            {
                'language': "en",
                'notify_name': "test_pytest_notify"
            }
        ],
        'keyword': "abc"
    }

    expect_result = {
        'notify': [
            {
                'language': "en",
                'notify_name': "test_pytest_notify"
            }
        ],
    }

    except_for = format_site_info_data(site_info)
    # site_instance = SiteInfo()
    actual_result = SiteInfo().update(site_info)
    query_object = SiteInfo.query.filter_by().one_or_none()
    assert query_object.notify == expect_result['notify']
