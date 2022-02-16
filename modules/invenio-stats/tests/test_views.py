# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test view functions."""
import json

from flask import url_for


def test_post_request(app, db, query_entrypoints,
                      users, custom_permission_factory,
                      sample_histogram_query_data):
    """Test post request to stats API."""
    with app.test_client() as client:
        headers = [('Content-Type', 'application/json'),
                   ('Accept', 'application/json')]
        sample_histogram_query_data['mystat']['stat'] = 'test-query'
        resp = client.post(
            url_for('invenio_stats.stat_query',
                    access_token=users['authorized'].allowed_token),
            headers=headers,
            data=json.dumps(sample_histogram_query_data))


def test_unauthorized_request(app, query_entrypoints,
                              custom_permission_factory,
                              sample_histogram_query_data, users):
    """Test rejecting unauthorized requests."""

    def client_req(user):
        with app.test_client() as client:
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'application/json')]
            resp = client.post(
                url_for('invenio_stats.stat_query',
                        access_token=user.allowed_token if user else None),
                headers=headers,
                data=json.dumps(sample_histogram_query_data))
            return resp.status_code

    sample_histogram_query_data['mystat']['stat'] = 'test-query'
    # assert client_req(users['unauthorized']) == 403
    # assert client_req(None) == 401
    # assert client_req(users['authorized']) == 200

    # assert custom_permission_factory.query_name == 'test-query'
    # assert custom_permission_factory.params == \
    #     sample_histogram_query_data['mystat']['params']
