# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Test location related views."""

from __future__ import absolute_import, print_function

import pytest
from flask import json, url_for
from testutils import login_user

from invenio_files_rest.models import Bucket


def get_json(resp):
    """Get JSON from response."""
    return json.loads(resp.get_data(as_text=True))


@pytest.mark.parametrize('user, expected', [
    (None, 401),
    ('auth', 403),
    ('location', 200),
])
def test_post_bucket(app, client, headers, dummy_location, permissions,
                     user, expected):
    """Test post a bucket."""
    expected_keys = [
        'id', 'links', 'size', 'quota_size', 'max_file_size', 'locked',
        'created', 'updated']
    params = [{}, {'location_name': dummy_location.name}]

    login_user(client, permissions[user])

    for data in params:
        resp = client.post(
            url_for('invenio_files_rest.location_api'),
            data=data,
            headers=headers
        )
        assert resp.status_code == expected
        if resp.status_code == 200:
            resp_json = get_json(resp)
            for key in expected_keys:
                assert key in resp_json
            assert Bucket.get(resp_json['id'])


@pytest.mark.parametrize('user, expected', [
    (None, 405),
    ('auth', 405),
    ('location', 405),
])
def test_get_location(app, client, headers, dummy_location, permissions,
                      user, expected):
    """Test GET a location."""
    login_user(client, permissions[user])
    r = client.get(url_for('invenio_files_rest.location_api'), headers=headers)
    assert r.status_code == expected
