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

"""Module tests."""
import json
import pytest

from flask import url_for
from weko_deposit.api import WekoDeposit
from invenio_accounts.testutils import login_user_via_session


# def test_publish(app, location):
#    deposit = WekoDeposit.create({})
#    kwargs = {
#        'pid_value': deposit.pid.pid_value
#    }


def test_publish_guest(client, deposit):
    """
    Test of publish.
    """
    kwargs = {
        'pid_value': deposit
    }
    url = url_for('weko_deposit_rest.publish', pid_value=kwargs['pid_value'])
    input = {}
    res = client.put(url, data=json.dumps(input),
                     content_type='application/json')
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
])
def test_publish_users(client, users, deposit, index, status_code):
    """
    Test of publish.
    """
    login_user_via_session(client=client, email=users[index]['email'])
    kwargs = {
        'pid_value': deposit
    }
    url = url_for('weko_deposit_rest.publish', pid_value=kwargs['pid_value'])
    input = {}
    res = client.put(url, data=json.dumps(input),
                     content_type='application/json')
    assert res.status_code == status_code


def test_depid_item_put_guest(client, deposit):
    """
    Test of depid_item post.
    :param client: The flask client.
    """
    kwargs = {
        'pid_value': deposit
    }
    url = url_for('weko_deposit_rest.depid_item',
                  pid_value=kwargs['pid_value'])
    input = {"item_1617186331708": [{"subitem_1551255647225": "tetest",
             "subitem_1551255648112": "en"}], "pubdate": "2021-01-01",
             "item_1617258105262": {"resourcetype": "conference paper",
                                    "resourceuri": "http://purl.org/coar/resource_type/c_5794"},
             "shared_user_id": -1, "title": "tetest", "lang": "en",
             "deleted_items": ["item_1617186385884", "item_1617186419668",
                               "approval1", "approval2"],
             "$schema": "/items/jsonschema/15"}
    res = client.put(url, data=json.dumps(input),
                     content_type='application/json')
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
])
def test_depid_item_put_users(client, users, deposit, index, status_code):
    """
    Test of depid_item post.
    :param client: The flask client.
    """
    login_user_via_session(client=client, email=users[index]['email'])
    kwargs = {
        'pid_value': deposit
    }
    url = url_for('weko_deposit_rest.depid_item',
                  pid_value=kwargs['pid_value'])
    input = {}
    res = client.put(url, data=json.dumps(input),
                     content_type='application/json')
    assert res.status_code == status_code


def test_depid_item_post_guest(client, deposit):
    """
    Test of depid_item post.
    :param client: The flask client.
    """
    kwargs = {
            'pid_value': deposit
    }
    url = url_for('weko_deposit_rest.depid_item',
                  pid_value=kwargs['pid_value'])
    input = {}
    res = client.post(url,
                      data=json.dumps(input),
                      content_type='application/json')
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('index, status_code', [
    (0, 403),
    (1, 201),
    (2, 201),
    (3, 201),
    (4, 201),
])
def test_depid_item_post_users(client, users, deposit, index, status_code):
    """
    Test of depid_item post.
    :param client: The flask client.
    """
    login_user_via_session(client=client, email=users[index]['email'])
    kwargs = {
        'pid_value': deposit
    }
    url = url_for('weko_deposit_rest.depid_item',
                  pid_value=kwargs['pid_value'])
    input = {}
    res = client.post(url,
                      data=json.dumps(input),
                      content_type='application/json')
    assert res.status_code == status_code
