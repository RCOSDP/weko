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

from flask import url_for
from invenio_accounts.testutils import login_user_via_session


def get_json(response):
    """Get JSON from response."""
    return json.loads(response.get_data(as_text=True))


def test_create_prefix_guest(client):
    """
    Test of create author prefix.
    :param client: The flask client.
    """
    input = {'name': 'test', 'scheme': 'test', 'url': 'https://test/##'}
    res = client.put('/api/authors/add_prefix',
                     data=json.dumps(input),
                     content_type='application/json', follow_redirects=False)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


def test_create_prefix_user(client, users):
    """
    Test of create author prefix.
    :param client: The flask client.
    """
    # login
    login_user_via_session(client=client, email=users[0]['email'])

    input = {'name': 'test0', 'scheme': 'test0', 'url': 'https://test0/##'}
    res = client.put('/api/authors/add_prefix',
                     data=json.dumps(input),
                     content_type='application/json')
    assert res.status_code == 403


def test_create_prefix_contributor(client, users):
    """
    Test of create author prefix.
    :param client: The flask client.
    """
    # login
    login_user_via_session(client=client, email=users[1]['email'])

    input = {'name': 'test1', 'scheme': 'test1', 'url': 'https://test1/##'}
    res = client.put('/api/authors/add_prefix',
                     data=json.dumps(input),
                     content_type='application/json')
    assert res.status_code == 403


def test_create_prefix_comadmin(client, users):
    """
    Test of create author prefix.
    :param client: The flask client.
    """
    # login
    login_user_via_session(client=client, email=users[2]['email'])

    input = {'name': 'test2', 'scheme': 'test2', 'url': 'https://test2/##'}
    res = client.put('/api/authors/add_prefix',
                     data=json.dumps(input),
                     content_type='application/json')
    assert res.status_code == 403


def test_create_prefix_repoadmin(client, users):
    """
    Test of create author prefix.
    :param client: The flask client.
    """
    # login
    login_user_via_session(client=client, email=users[3]['email'])

    input = {'name': 'test3', 'scheme': 'test3', 'url': 'https://test3/##'}
    res = client.put('/api/authors/add_prefix',
                     data=json.dumps(input),
                     content_type='application/json')
    res_dict = get_json(res)
    assert res_dict['code'] == 200
    assert res_dict['msg'] == 'Success'


def test_create_prefix_sysadmin(client, users):
    """
    Test of create author prefix.
    :param client: The flask client.
    """
    # login
    login_user_via_session(client=client, email=users[4]['email'])

    input = {'name': 'test4', 'scheme': 'test4', 'url': 'https://test4/##'}
    res = client.put('/api/authors/add_prefix',
                     data=json.dumps(input),
                     content_type='application/json')
    res_dict = get_json(res)
    assert res_dict['code'] == 200
    assert res_dict['msg'] == 'Success'


def test_update_prefix_user(client, users):
    """
    Test of update author prefix.
    :param client: The flask client.
    """
    # login for create prefix
    login_user_via_session(client=client, email=users[4]['email'])

    input = {'name': 'test4', 'scheme': 'test4', 'url': 'https://test4/##'}
    res = client.put('/api/authors/add_prefix',
                     data=json.dumps(input),
                     content_type='application/json')
    client.get(url_for('security.logout'))

    # login
    login_user_via_session(client=client, email=users[0]['email'])
    input2 = {'id': 1, 'name': 'test0changed', 'scheme': 'test0changed',
              'url': 'https://test0changed/##'}
    client.put('/api/authors/add_prefix',
               data=json.dumps(input),
               content_type='application/json')
    res = client.post('/api/authors/edit_prefix',
                      data=json.dumps(input2),
                      content_type='application/json')
    assert res.status_code == 403


def test_update_prefix_contributor(client, users):
    """
    Test of update author prefix.
    :param client: The flask client.
    """
    # login
    login_user_via_session(client=client, email=users[1]['email'])

    input = {'name': 'test1', 'scheme': 'test1', 'url': 'https://test1/##'}
    input2 = {'id': 1, 'name': 'test1changed', 'scheme': 'test1changed',
              'url': 'https://test1changed/##'}
    client.put('/api/authors/add_prefix',
               data=json.dumps(input),
               content_type='application/json')
    res = client.post('/api/authors/edit_prefix',
                      data=json.dumps(input2),
                      content_type='application/json')
    assert res.status_code == 403


def test_update_prefix_comadmin(client, users):
    """
    Test of update author prefix.
    :param client: The flask client.
    """
    # login
    login_user_via_session(client=client, email=users[2]['email'])

    input = {'name': 'test2', 'scheme': 'test2', 'url': 'https://test2/##'}
    input2 = {'id': 1, 'name': 'test2changed', 'scheme': 'test2changed',
              'url': 'https://test2changed/##'}
    client.put('/api/authors/add_prefix',
               data=json.dumps(input),
               content_type='application/json')
    res = client.post('/api/authors/edit_prefix',
                      data=json.dumps(input2),
                      content_type='application/json')
    assert res.status_code == 403


def test_update_prefix_repoadmin(client, users):
    """
    Test of update author prefix.
    :param client: The flask client.
    """
    # login
    login_user_via_session(client=client, email=users[3]['email'])

    input = {'name': 'test3', 'scheme': 'test3', 'url': 'https://test3/##'}
    input2 = {'id': 1, 'name': 'test3changed', 'scheme': 'test3changed',
              'url': 'https://test3changed/##'}
    client.put('/api/authors/add_prefix',
               data=json.dumps(input),
               content_type='application/json')
    res = client.post('/api/authors/edit_prefix',
                      data=json.dumps(input2),
                      content_type='application/json')
    res_dict = get_json(res)
    assert res_dict['code'] == 200
    assert res_dict['msg'] == 'Success'


def test_update_prefix_sysadmin(client, users):
    """
    Test of update author prefix.
    :param client: The flask client.
    """
    # login
    login_user_via_session(client=client, email=users[4]['email'])

    input = {'name': 'test4', 'scheme': 'test4', 'url': 'https://test4/##'}
    input2 = {'id': 1, 'name': 'test4changed', 'scheme': 'test4changed',
              'url': 'https://test4changed/##'}
    client.put('/api/authors/add_prefix',
               data=json.dumps(input),
               content_type='application/json')
    res = client.post('/api/authors/edit_prefix',
                      data=json.dumps(input2),
                      content_type='application/json')
    res_dict = get_json(res)
    assert res_dict['code'] == 200
    assert res_dict['msg'] == 'Success'


def test_delete_prefix_contributor(client, users):
    """
    Test of delete author prefix.
    :param client: The flask client.
    """
    # login
    login_user_via_session(client=client, email=users[1]['email'])

    input = {'name': 'test1', 'scheme': 'test1', 'url': 'https://test1/##'}
    client.put('/api/authors/add_prefix',
               data=json.dumps(input),
               content_type='application/json')
    res = client.delete('/api/authors/delete_prefix/1')
    assert res.status_code == 403


def test_delete_prefix_comadmin(client, users):
    """
    Test of delete author prefix.
    :param client: The flask client.
    """
    # login
    login_user_via_session(client=client, email=users[2]['email'])

    input = {'name': 'test2', 'scheme': 'test2', 'url': 'https://test2/##'}
    client.put('/api/authors/add_prefix',
               data=json.dumps(input),
               content_type='application/json')
    res = client.delete('/api/authors/delete_prefix/1')
    assert res.status_code == 403


def test_delete_prefix_repoadmin(client, users):
    """
    Test of delete author prefix.
    :param client: The flask client.
    """
    # login
    login_user_via_session(client=client, email=users[3]['email'])

    input = {'name': 'test3', 'scheme': 'test3', 'url': 'https://test3/##'}
    client.put('/api/authors/add_prefix',
               data=json.dumps(input),
               content_type='application/json')
    res = client.delete('/api/authors/delete_prefix/1')
    res_dict = get_json(res)
    assert res_dict['msg'] == 'Success'


def test_delete_prefix_sysadmin(client, users):
    """
    Test of delete author prefix.
    :param client: The flask client.
    """
    # login
    login_user_via_session(client=client, email=users[4]['email'])

    input = {'name': 'test4', 'scheme': 'test4', 'url': 'https://test4/##'}
    client.put('/api/authors/add_prefix',
               data=json.dumps(input),
               content_type='application/json')
    res = client.delete('/api/authors/delete_prefix/1')
    res_dict = get_json(res)
    assert res_dict['msg'] == 'Success'
