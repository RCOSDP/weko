# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Tests for patching records."""

import pytest
from flask import Flask, url_for
from flask_login import AnonymousUserMixin
import flask_security
from invenio_records_rest.views import RecordsListResource
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

class DummyUser(AnonymousUserMixin):
    is_authenticated = False
    id = None

class DummySearch:
    def with_preference_param(self):
        return self
    def params(self, **kwargs):
        return self
    def to_dict(self):
        return {"sort": [{"control_number": {"order": "desc"}}]}
    def __getitem__(self, key):
        return self
    def execute(self):
        class Result:
            hits = type('hits', (), {'total': 0})()
            def to_dict(self):
                return {}
        return Result()

def make_request(app, query_string=None):
    builder = EnvironBuilder(method='GET', query_string=query_string)
    env = builder.get_environ()
    req = Request(env)
    return req

@pytest.fixture
def resource_with_dummy_search(app):
    def dummy_search_factory(self, search):
        return search, {}

    return RecordsListResource(
        minter_name="recid",
        pid_type="recid",
        pid_fetcher="recid",
        read_permission_factory=None,
        create_permission_factory=None,
        list_permission_factory=None,
        search_class=DummySearch,
        record_serializers={},
        record_loaders=None,
        search_serializers={'application/json': lambda *a, **k: {}},
        default_media_type='application/json',
        max_result_window=10000,
        search_factory=dummy_search_factory,
        item_links_factory=None,
        record_class=None,
        indexer_class=None
    )

def test_format_html_redirect(monkeypatch, app, resource_with_dummy_search):
    # Should redirect when format=html is specified
    with app.test_request_context('/?format=html'):
        monkeypatch.setattr(flask_security, "current_user", DummyUser())
        monkeypatch.setattr('flask.url_for', lambda endpoint, **kwargs: '/dummy_url')
        monkeypatch.setattr('invenio_records_rest.views.url_for', lambda endpoint, **kwargs: '/dummy_url')
        monkeypatch.setattr('invenio_accounts.models.User', type('User', (), {'query': type('query', (), {'get': staticmethod(lambda x: type('U', (), {'email': 'dummy@example.com'})())})()}) )
        resp = resource_with_dummy_search.get()
        assert resp.status_code == 302
        assert 'search' in resp.location

def test_format_rss(monkeypatch, app, resource_with_dummy_search):
    # Should NOT redirect when format=rss is specified
    with app.test_request_context('/?format=rss&q=test'):
        monkeypatch.setattr(flask_security, "current_user", DummyUser())
        monkeypatch.setattr('flask.url_for', lambda endpoint, **kwargs: '/dummy_url')
        monkeypatch.setattr('invenio_records_rest.views.url_for', lambda endpoint, **kwargs: '/dummy_url')
        monkeypatch.setattr('invenio_accounts.models.User', type('User', (), {'query': type('query', (), {'get': staticmethod(lambda x: type('U', (), {'email': 'dummy@example.com'})())})()}) )
        resp = resource_with_dummy_search.get()
        # Should return a dict as search result, not a redirect
        assert isinstance(resp, dict)

def test_format_multiple(monkeypatch, app, resource_with_dummy_search):
    # Should prioritize html when both format=html&format=rss are specified
    with app.test_request_context('/?format=html&format=rss'):
        monkeypatch.setattr('flask_security.current_user', DummyUser())
        monkeypatch.setattr('flask.url_for', lambda endpoint, **kwargs: '/dummy_url')
        monkeypatch.setattr('invenio_records_rest.views.url_for', lambda endpoint, **kwargs: '/dummy_url')
        monkeypatch.setattr('invenio_accounts.models.User', type('User', (), {'query': type('query', (), {'get': staticmethod(lambda x: type('U', (), {'email': 'dummy@example.com'})())})()}) )
        resp = resource_with_dummy_search.get()
        assert resp.status_code == 302
        assert 'search' in resp.location

def test_no_format_no_query(monkeypatch, app, resource_with_dummy_search):
    # Should redirect when neither format nor q is specified
    with app.test_request_context('/'):
        monkeypatch.setattr('flask_security.current_user', DummyUser())
        monkeypatch.setattr('flask.url_for', lambda endpoint, **kwargs: '/dummy_url')
        monkeypatch.setattr('invenio_records_rest.views.url_for', lambda endpoint, **kwargs: '/dummy_url')
        monkeypatch.setattr('invenio_accounts.models.User', type('User', (), {'query': type('query', (), {'get': staticmethod(lambda x: type('U', (), {'email': 'dummy@example.com'})())})()}) )
        resp = resource_with_dummy_search.get()
        assert resp.status_code == 302
        assert 'search' in resp.location

# def test_redirect_to_search_sets_format_html(app):
    # Should always set format=html in redirect URL, even if other formats are specified
    from invenio_records_rest.views import redirect_to_search
    with app.test_request_context('/?format=rss&q=test&foo=bar'):
        resp = redirect_to_search(page=2, size=50)
        assert resp.status_code == 302
        location = resp.location
        assert 'format=html' in location
        assert 'page=2' in location
        assert 'size=50' in location
        assert 'foo=bar' in location
        assert 'q=test' in location
        assert location.startswith('http')


def test_redirect_to_search_no_format(app):
    # Should add format=html if no format is specified, and preserve other parameters
    from invenio_records_rest.views import redirect_to_search
    with app.test_request_context('/?q=xyz'):
        resp = redirect_to_search(page=3, size=75)
        assert resp.status_code == 302
        location = resp.location
        assert 'format=html' in location
        assert 'q=xyz' in location
        assert 'page=3' in location
        assert 'size=75' in location

def test_redirect_to_search_page_size_falsy(app):
    # Should not include page or size in URL if they are None, but should include format=html and other params
    from invenio_records_rest.views import redirect_to_search
    with app.test_request_context('/?format=xml&q=abc'):
        resp = redirect_to_search(page=None, size=None)
        location = resp.location
        assert 'page=None' not in location
        assert 'size=None' not in location
        assert 'format=html' in location
        assert 'q=abc' in location

def test_redirect_to_search_exclude_keys(app):
    # Should exclude specific keys (page_no, list_view_num, log_term, lang) from the redirect URL, but include others
    from invenio_records_rest.views import redirect_to_search
    with app.test_request_context('/?page_no=5&list_view_num=99&log_term=foo&lang=ja&q=zzz'):
        resp = redirect_to_search(page=1, size=20)
        location = resp.location
        # Excluded keys should not be in the URL
        assert 'page_no=' not in location
        assert 'list_view_num=' not in location
        assert 'log_term=' not in location
        assert 'lang=' not in location
        # Other parameters should be present
        assert 'q=zzz' in location
        assert 'page=1' in location
        assert 'size=20' in location
        assert 'format=html' in location

