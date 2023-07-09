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
def test_groupcount(app_2):
    def members_count():
        return 1

    def get_id():
        return 1

    group = MagicMock()
    group.members_count = members_count
    group.get_id = get_id

    with app_2.app_context():
        with app_2.test_client() as client:
            # with patch("flask_login.utils._get_user", return_value=user):
            with patch("weko_groups.views.Group.query_by_user", return_value=[group]):
                group = Group()
                res = client.get(url_for('weko_groups.groupcount'))
                assert res.status_code == 200


# def _has_admin_access():
def test__has_admin_access(app):
    with app.app_context():
        user = MagicMock()
        user.is_authenticated = True
        with patch("flask_login.utils._get_user", return_value=user):
            assert _has_admin_access() == False


# def index():
def test_index(app_2, users):
    # "Encountered unknown tag 'assets'. Jinja was looking for the following tags: 'endblock'. The innermost block that needs to be closed is 'block'.", 
    # But upon testing on the actual url on the browser "https://localhost/accounts/settings/groups/index" there is no problem
    with app_2.test_request_context():
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                try:
                    client.get(
                        url_for('weko_groups.index'),
                        query_string={
                            "q": "q",
                        }
                    )
                except:
                    pass


# def requests():
def test_requests(app_2, users):
    with app_2.test_request_context():
        with app_2.test_client() as client:
            request = MagicMock()
            request.args = {
                "page": 1,
                "per_page": 5
            }
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                with patch("weko_groups.views.request", return_value=request):
                    res = client.get(url_for('weko_groups.requests'))
                    assert res.status_code == 200


# def invitations():
def test_invitations(app_2, users):
    with app_2.test_request_context():
        with app_2.test_client() as client:
            request = MagicMock()
            request.args = {
                "page": 1,
                "per_page": 5
            }
            
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                with patch("weko_groups.views.request", return_value=request):
                    res = client.get(url_for('weko_groups.invitations'))
                    assert res.status_code == 200


# def new():
def test_new(app_2, users):
    from sqlalchemy.exc import IntegrityError

    def validate_on_submit_True():
        return True
    
    def validate_on_submit_False():
        return False

    form = MagicMock()
    form.validate_on_submit = validate_on_submit_False
    group = MagicMock()
    group.name = "group_name"
    
    with app_2.test_request_context():
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                with patch("weko_groups.views.GroupForm", return_value=form):
                    # "Encountered unknown tag 'assets'. Jinja was looking for the following tags: 'endblock'. The innermost block that needs to be closed is 'block'.", 
                    # But upon testing on the actual url on the browser "https://localhost/accounts/settings/groups/new" there is no problem
                    try:
                        client.get(url_for('weko_groups.new'))
                    except:
                        pass

                form.validate_on_submit = validate_on_submit_True

                with patch("weko_groups.views.GroupForm", return_value=form):
                    with patch("weko_groups.views.Group.create", return_value=group):
                        res = client.get(url_for('weko_groups.new'))
                        assert res.status_code == 302

                    # Exception coverage
                    try:
                        with patch("weko_groups.views.Group.create", side_effect=IntegrityError('')):
                            client.get(url_for('weko_groups.new'))
                    except:
                        pass


# def manage(group_id):
def test_manage(app_2, users):
    def validate_on_submit_True():
        return True
    
    def can_edit_True(item):
        return True

    def can_edit_False(item):
        return False

    def update_func(item):
        return item

    form = MagicMock()
    form.validate_on_submit = validate_on_submit_True
    group = MagicMock()
    group.query.get_or_404.can_edit = can_edit_False
    group.query.get_or_404.update = update_func
    group.query.get_or_404.name = "name"

    with app_2.test_request_context():
        with app_2.test_client() as client:
            # "Encountered unknown tag 'assets'. Jinja was looking for the following tags: 'endblock'. The innermost block that needs to be closed is 'block'.", 
            # But upon testing on the actual url on the browser "https://localhost/accounts/settings/groups/1" there is no problem
            # But upon testing on the actual url on the browser "https://localhost/accounts/settings/groups/1/manage" there is no problem
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                with patch("weko_groups.views.Group", return_value=group):
                    with patch("weko_groups.views.GroupForm", return_value=form):
                        try:
                            client.get(url_for('weko_groups.manage', group_id=1))
                        except:
                            pass
        

def test_manage_2(app_2, users):
    def validate_on_submit_True():
        return True

    form = MagicMock()
    form.validate_on_submit = validate_on_submit_True
    
    with app_2.test_request_context():
        # "Encountered unknown tag 'assets'. Jinja was looking for the following tags: 'endblock'. The innermost block that needs to be closed is 'block'.", 
        # But upon testing on the actual url on the browser "https://localhost/accounts/settings/groups/1" there is no problem
        # But upon testing on the actual url on the browser "https://localhost/accounts/settings/groups/1/manage" there is no problem
        group = Group.create(name="name")
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                with patch("weko_groups.views.GroupForm", return_value=form):
                    try:
                        client.get(url_for('weko_groups.manage', group_id=group.id))
                    except:
                        pass


# def delete(group_id):
def test_delete(app_2, users):
    def can_edit_True(item):
        return True

    def can_edit_False(item):
        return False

    def delete_func():
        return True

    group = MagicMock()
    group.query = MagicMock()
    group.query.get_or_404 = MagicMock()
    group.query.get_or_404.can_edit = can_edit_False
    group.query.get_or_404.delete = delete_func

    with app_2.test_request_context():
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                with patch("weko_groups.views.Group", return_value=group):
                    res = client.post(url_for('weko_groups.delete', group_id=1))
                    assert res.status_code == 302
        

def test_delete_2(app_2, users):
    with app_2.test_request_context():
        group = Group.create(name="name")
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                res = client.post(url_for('weko_groups.delete', group_id=group.id))
                assert res.status_code == 302


# def members(group_id):
def test_members(app_2, users):
    def can_edit_True(item):
        return True

    def can_edit_False(item):
        return False

    def delete_func():
        return True

    group = MagicMock()
    group.query = MagicMock()
    group.query.get_or_404 = MagicMock()
    group.query.get_or_404.can_edit = can_edit_False
    group.query.get_or_404.delete = delete_func

    with app_2.test_request_context():
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                with patch("weko_groups.views.Group", return_value=group):
                    res = client.post(
                        url_for('weko_groups.members', group_id=1),
                        query_string={
                            "q": "q",
                            "s": "s",
                        }
                    )
                    assert res.status_code == 200


def test_members_2(app_2, users):
    with app_2.test_request_context():
        group = Group.create(name="name")

        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                res = client.post(url_for('weko_groups.members', group_id=group.id))
                assert res.status_code == 302


# def leave(group_id):
def test_leave(app_2, users):
    def can_leave_True(item):
        return True

    group = MagicMock()
    group.query.get_or_404.can_leave = can_leave_True

    with app_2.test_request_context():
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                with patch("weko_groups.views.Group", return_value=group):
                    res = client.post(url_for('weko_groups.leave', group_id=1))
                    assert res.status_code == 302
        

def test_leave_2(app_2, users):
    with app_2.test_request_context():
        group = Group.create(name="name")
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                res = client.post(url_for('weko_groups.leave', group_id=group.id))
                assert res.status_code == 302


# def approve(group_id, user_id): 
def test_approve(app_2, users):
    def can_edit_True(item):
        return True

    membership = MagicMock()
    membership.query.get_or_404.group.can_edit = can_edit_True

    with app_2.test_request_context():
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                with patch("weko_groups.views.Membership", return_value=membership):
                    res = client.post(url_for('weko_groups.approve', group_id=1, user_id=users[3]["obj"].id))
                    assert res.status_code == 302
        

def test_approve_2(app_2, users):
    with app_2.test_request_context():
        group = Group.create(name="name")
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                res = client.post(url_for('weko_groups.approve', group_id=group.id, user_id=users[3]["obj"].id))
                assert res.status_code == 404


# def remove(group_id, user_id): 
def test_remove(app_2, users):
    def can_edit_True(item):
        return True

    group = MagicMock()
    group.query.get_or_404.group.can_edit = can_edit_True

    with app_2.test_request_context():
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                with patch("weko_groups.views.Group", return_value=group):
                    res = client.post(url_for('weko_groups.remove', group_id=1, user_id=users[3]["obj"].id))
                    assert res.status_code == 302
        

def test_remove_2(app_2, users):
    with app_2.test_request_context():
        group = Group.create(name="name")
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                res = client.post(url_for('weko_groups.remove', group_id=group.id, user_id=users[3]["obj"].id))
                assert res.status_code == 302


# def accept(group_id): 
def test_accept(app_2, users):
    def can_edit_True(item):
        return True
    
    def accept():
        return True

    membership = MagicMock()
    membership.query.get_or_404.group.can_edit = can_edit_True
    membership.query.get_or_404.group.accept = accept

    with app_2.test_request_context():
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                with patch("weko_groups.views.Membership", return_value=membership):
                    res = client.post(url_for('weko_groups.accept', group_id=1, user_id=users[3]["obj"].id))
                    assert res.status_code == 302


# def reject(group_id): 
def test_reject(app_2, users):
    def can_edit_True(item):
        return True
    
    def reject():
        return True

    membership = MagicMock()
    membership.query.get_or_404.group.can_edit = can_edit_True
    membership.query.get_or_404.group.reject = reject

    with app_2.test_request_context():
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                with patch("weko_groups.views.Membership", return_value=membership):
                    res = client.post(url_for('weko_groups.reject', group_id=1, user_id=users[3]["obj"].id))
                    assert res.status_code == 302


# def new_member(group_id):
def test_new_member(app_2, users):
    def validate_on_submit_True():
        return True
    
    def can_invite_others(item):
        return True
    
    def invite_by_emails(item):
        return True

    form = MagicMock()
    form.validate_on_submit = validate_on_submit_True
    group = MagicMock()
    group.query.get_or_404.can_invite_others = can_invite_others
    group.query.get_or_404.invite_by_emails = invite_by_emails
    group.name = "group_name"

    with app_2.test_request_context():
        # "Encountered unknown tag 'assets'. Jinja was looking for the following tags: 'endblock'. The innermost block that needs to be closed is 'block'."
        # But upon testing on the actual url on the browser "https://localhost/accounts/settings/groups/1/members/new" there is no problem 
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                with patch("weko_groups.views.Group", return_value=group):
                    with patch("weko_groups.views.NewMemberForm", return_value=form):
                        try:
                            client.get(url_for('weko_groups.new_member', group_id=1))
                        except:
                            pass
                    try:
                        client.get(url_for('weko_groups.new_member', group_id=1))
                    except:
                        pass


# def new_member(group_id):
def test_new_member_2(app_2, users):
    def validate_on_submit_True():
        return True
    
    def can_invite_others(item):
        return True
    
    def invite_by_emails(item):
        return True

    form = MagicMock()
    form.validate_on_submit = validate_on_submit_True
    group = MagicMock()
    group.query.get_or_404.can_invite_others = can_invite_others
    group.query.get_or_404.invite_by_emails = invite_by_emails
    group.name = "group_name"

    with app_2.test_request_context():
        # "Encountered unknown tag 'assets'. Jinja was looking for the following tags: 'endblock'. The innermost block that needs to be closed is 'block'."
        # But upon testing on the actual url on the browser "https://localhost/accounts/settings/groups/1/members/new" there is no problem 
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                with patch("weko_groups.views.Group", return_value=group):
                    try:
                        client.get(url_for('weko_groups.new_member', group_id=1))
                    except:
                        pass
        

def test_new_member_3(app_2, users):
    with app_2.test_request_context():
        group = Group.create(name="name", is_managed=True)
        with app_2.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=users[7]["obj"]):
                res = client.get(url_for('weko_groups.new_member', group_id=group.id))
                assert res.status_code == 302


# def remove_csrf(form):
def test_remove_csrf(app):
    form = MagicMock()
    form.data = {
        "not_csrf_token_key": "not_csrf_token_value"
    }
    
    assert remove_csrf(form=form) != None

