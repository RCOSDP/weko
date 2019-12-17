# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test utility functions."""

from mock import patch

from invenio_stats.utils import get_geoip, get_user, obj_or_import_string


def myfunc():
    """Example function."""
    pass


def test_get_user(app, mock_users, request_headers):
    """Test the get_user function."""
    header = request_headers['user']
    with patch(
                'invenio_stats.utils.current_user',
                mock_users['authenticated']
            ), app.test_request_context(
                headers=header, environ_base={'REMOTE_ADDR': '142.0.0.1'}
            ):
        user = get_user()
    assert user['user_id'] == mock_users['authenticated'].get_id()
    assert user['user_agent'] == header['USER_AGENT']
    assert user['ip_address'] == '142.0.0.1'


def test_get_geoip():
    """Test looking up IP address."""
    assert get_geoip("74.125.67.100") == 'US'


def test_obj_or_import_string(app):
    """Test obj_or_import_string."""
    assert not obj_or_import_string(value=None)
    assert myfunc == obj_or_import_string(value=myfunc)
