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
# WEKO3 is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.


"""Test groups data models."""

import pytest
from mock import patch, MagicMock
from flask import Flask, json, jsonify, session, url_for

from weko_groups.models import Group
from weko_groups.views import (
    sanitize_html_group,
    groupcount,
    _has_admin_access,
    index,
    requests,
    invitations,
    new,
    manage,
    delete,
    members,
    leave,
    approve,
    remove,
    accept,
    reject,
    new_member,
    remove_csrf,
    dbsession_clean
)

# def sanitize_html_group(value):
def test_sanitize_html_group(app):
    value = "value"
    assert sanitize_html_group(value=value) != None


# def groupcount():
def test_groupcount(app):
    def members_count():
        return 1

    def get_id():
        return 1

    group = MagicMock()
    group.members_count = members_count
    group.get_id = get_id

    with app.app_context():
        # with patch("flask_login.utils._get_user", return_value=user):
        with patch("weko_groups.views.Group.query_by_user", return_value=[group]):
            group = Group()
            groupcount()


# def _has_admin_access(): ~ Not yet done
def test__has_admin_access(app):
    with app.app_context():
        user = MagicMock()
        user.is_authenticated = True
        with patch("flask_login.utils._get_user", return_value=user):
            assert _has_admin_access() == False


# def requests():
def test_requests(app_2, users):
    with app_2.test_request_context():
        request = MagicMock()
        request.args = {
            "page": 1,
            "per_page": 5
        }
        with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
            with patch("weko_groups.views.request", return_value=request):
                assert requests() != None


# def invitations():
def test_invitations(app_2, users):
    with app_2.test_request_context():
        request = MagicMock()
        request.args = {
            "page": 1,
            "per_page": 5
        }
        
        with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
            with patch("weko_groups.views.request", return_value=request):
                assert invitations() != None


# def new(): ~ Not yet done
def test_new(app):
    with app.test_request_context():
        assert new() != None


# def remove_csrf(form):
def test_remove_csrf(app):
    form = MagicMock()
    form.data = {
        "not_csrf_token_key": "not_csrf_token_value"
    }
    
    assert remove_csrf(form=form) != None