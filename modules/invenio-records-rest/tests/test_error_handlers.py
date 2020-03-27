# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Error handler tests."""

from __future__ import absolute_import, print_function

import json

import pytest
from flask import jsonify, make_response, url_for

from invenio_records_rest.errors import PIDDoesNotExistRESTError
from invenio_records_rest.proxies import current_records_rest


def custom_error_handler(error):
    """Test error handler."""
    return make_response(jsonify({
        'status': error.code,
        'message': error.description,
        'info': {
            'pid_value': error.pid_error.pid_value,
            'pid_type': error.pid_error.pid_type,
        }
    }), error.code)


@pytest.mark.parametrize('app', [dict(
    endpoint=dict(error_handlers={
        PIDDoesNotExistRESTError: custom_error_handler,
    }),
)], indirect=['app'])
def test_custom_error_handlers(app, db, test_data):
    """Test custom error handlers for endpoints."""
    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', 'application/json'),
        ]

        # Test the custom handler
        res = client.get(
            url_for('invenio_records_rest.recid_item', pid_value='1'),
            headers=HEADERS)
        assert res.status_code == 404
        data = json.loads(res.get_data(as_text=True))
        assert data == {
            'status': 404,
            'message': 'PID does not exist.',
            'info': {'pid_value': '1', 'pid_type': 'recid'}
        }

        # Check that the default handlers still work
        res = client.post(
            url_for('invenio_records_rest.recid_list'),
            data='{invalid-json',
            headers=HEADERS)
        assert res.status_code == 400
        data = json.loads(res.get_data(as_text=True))
        assert data == {
            'message': (
                'The browser (or proxy) sent a request that this server could '
                'not understand.'),
            'status': 400
        }
