# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask
from werkzeug.http import parse_options_header

from invenio_app import InvenioApp


def test_rate_secure_headers(app):
    """Test Rate Limiter extension."""
    app.config['APP_ENABLE_SECURE_HEADERS'] = False
    # Initialize the app
    InvenioApp(app)
    assert 'talisman' not in app.extensions


def test_headers(app_with_no_limiter):
    """Test headers."""
    app_with_no_limiter.config['RATELIMIT_APPLICATION'] = '1/day'
    ext = InvenioApp(app_with_no_limiter)

    for handler in app_with_no_limiter.logger.handlers:
        ext.limiter.logger.addHandler(handler)

    @app_with_no_limiter.route('/jessica_jones')
    def jessica_jones():
        return 'jessica jones'

    @app_with_no_limiter.route('/avengers')
    def avengers():
        return 'infinity war'

    with app_with_no_limiter.test_client() as client:
        res = client.get('/jessica_jones')
        assert res.status_code == 200
        assert res.headers['X-RateLimit-Limit'] == '1'
        assert res.headers['X-RateLimit-Remaining'] == '0'
        assert res.headers['X-RateLimit-Reset']

        res = client.get('/jessica_jones')
        assert res.status_code == 429
        assert res.headers['X-RateLimit-Limit']
        assert res.headers['X-RateLimit-Remaining']
        assert res.headers['X-RateLimit-Reset']

        res = client.get('/avengers')
        assert res.status_code == 429
        assert res.headers['X-Content-Security-Policy']
        assert res.headers['X-Content-Type-Options']
        assert res.headers['X-Frame-Options']
        assert res.headers['X-XSS-Protection']
        assert res.headers['X-RateLimit-Limit']
        assert res.headers['X-RateLimit-Remaining']
        assert res.headers['X-RateLimit-Reset']


def _normalize_csp_header(header):
    """Normalize a CSP header for consistent comparisons."""
    return {p.strip() for p in (header or '').split(';')}


def _test_csp_default_src(app, expect):
    """Assert that the Content-Security-Policy header is the expect param."""
    ext = InvenioApp(app)

    @app.route('/captain_america')
    def captain_america():
        return 'captain america'

    with app.test_client() as client:
        res = client.get('/captain_america')
        assert res.status_code == 200
        assert _normalize_csp_header(
            res.headers.get('Content-Security-Policy')
        ) == _normalize_csp_header(expect)
        assert _normalize_csp_header(
            res.headers.get('X-Content-Security-Policy')
        ) == _normalize_csp_header(expect)


def test_csp_default_src_when_debug_false(app):
    """Test the Content-Security-Policy header when app debug is False."""
    expect = "default-src 'self'; object-src 'none'"
    _test_csp_default_src(app, expect)


def test_csp_default_src_when_debug_true(app):
    """Test the Content-Security-Policy header when app debug is True."""
    app.config['DEBUG'] = True
    expect = "default-src 'self' 'unsafe-inline'; object-src 'none'"
    _test_csp_default_src(app, expect)


def test_empty_csp_when_set_empty(app):
    """Test empty Content-Security-Policy header when set emtpy."""
    app.config['DEBUG'] = True
    app.config['APP_DEFAULT_SECURE_HEADERS']['content_security_policy'] = {}
    expect = None
    _test_csp_default_src(app, expect)


def test_default_health_blueprint(app):
    app.config['APP_HEALTH_BLUEPRINT_ENABLED'] = True
    # Initialize the app
    InvenioApp(app)
    with app.test_client() as client:
        res = client.get('/ping')
        assert res.status_code == 200


def test_ping_exempt_from_rate_limiting(app_with_no_limiter):
    app_with_no_limiter.config['APP_HEALTH_BLUEPRINT_ENABLED'] = True
    app_with_no_limiter.config['RATELIMIT_APPLICATION'] = '1/day'
    # Initialize the app
    InvenioApp(app_with_no_limiter)
    with app_with_no_limiter.test_client() as client:
        res = client.get('/ping')
        assert res.status_code == 200
        res = client.get('/ping')
        assert res.status_code == 200


def test_requestid(base_app):
    """Test extraction of header id."""
    InvenioApp(base_app)
    with base_app.test_client() as client:
        assert '1234' == client.get(
            '/requestid',  headers={'X-Request-ID': '1234'}
        ).get_data(as_text=True)


def test_requestid_different_header(base_app):
    """Test changing header name."""
    base_app.config['APP_REQUESTID_HEADER'] = 'Request-ID'
    InvenioApp(base_app)
    with base_app.test_client() as client:
        # Extracted
        assert '1234' == client.get(
            '/requestid',  headers={'Request-ID': '1234'}
        ).get_data(as_text=True)
        # Not extracted
        assert '' == client.get(
            '/requestid',  headers={'X-Request-ID': '1234'}
        ).get_data(as_text=True)


def test_requestid_cap_200(base_app):
    """Test cap at 200 chars of request id."""
    InvenioApp(base_app)
    with base_app.test_client() as client:
        assert '1'*200 == client.get(
            '/requestid',  headers={'X-Request-ID': '1'*500}
        ).get_data(as_text=True)


def test_requestid_no_extraction(base_app):
    """Test no extraction of header id."""
    base_app.config['APP_REQUESTID_HEADER'] = None
    InvenioApp(base_app)
    with base_app.test_client() as client:
        assert '' == client.get(
            '/requestid',  headers={'X-Request-ID': '1234'}
        ).get_data(as_text=True)
