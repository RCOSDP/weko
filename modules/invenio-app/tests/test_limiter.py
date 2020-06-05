# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import current_app
from mock import patch


def exhaust_and_test_rate_limit_per_second(client, rate_to_exhaust):
    """Helper function to test,per second,rate limits."""
    available_rate = int(rate_to_exhaust.split('per')[0])
    for x in range(0, available_rate):
        assert 200 == client.get(
                '/limited_rate'
            ).status_code
    assert 429 == client.get(
        '/limited_rate'
        ).status_code


def test_limiter(app):
    """Test the Flask limiter function."""
    with app.test_client() as client:
        exhaust_and_test_rate_limit_per_second(
            client,
            current_app.config['RATELIMIT_GUEST_USER']
        )
        for x in range(0, 2):
            assert 200 == client.get(
                '/unlimited_rate'
            ).status_code
        assert 200 == client.get(
            '/unlimited_rate'
            ).status_code


def test_limiter_for_authenticated_user(
        app, create_mocked_flask_security_with_user_init):
    """Test the Flask limiter function."""
    init_mocked_flask_security_with_user = \
        create_mocked_flask_security_with_user_init
    init_mocked_flask_security_with_user(
        {'is_authenticated': True, 'id': '1825'})
    with app.test_client() as client:
        with patch(
            'pkg_resources.get_distribution',
            return_value=True
                ):
            exhaust_and_test_rate_limit_per_second(
                client,
                current_app.config['RATELIMIT_AUTHENTICATED_USER']
            )
            assert 200 == client.get(
                    '/unlimited_rate'
                ).status_code


def test_limiter_for_privileged_user(
        app, create_mocked_flask_security_with_user_init,
        push_rate_limit_to_context):
    """Test the Flask limiter function."""
    init_mocked_flask_security_with_user = \
        create_mocked_flask_security_with_user_init
    user = {'is_authenticated': True, 'id': '1111'}
    init_mocked_flask_security_with_user(user)
    with app.test_client() as client:
        with patch(
            'pkg_resources.get_distribution',
            return_value=True
                ):
            exhaust_and_test_rate_limit_per_second(
                client,
                push_rate_limit_to_context
            )

            assert 200 == client.get(
                '/unlimited_rate'
                ).status_code
