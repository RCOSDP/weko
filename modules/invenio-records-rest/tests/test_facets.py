# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Facets tests."""

from __future__ import absolute_import, print_function

import pytest
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Q, Range
from flask import Flask
from invenio_rest.errors import RESTValidationError
from werkzeug.datastructures import MultiDict

from invenio_records_rest.facets import _aggregations, _create_filter_dsl, \
    _post_filter, _query_filter, default_facets_factory, range_filter, \
    terms_filter


def test_terms_filter():
    """Test terms filter."""
    f = terms_filter('test')
    assert f(['a', 'b']).to_dict() == dict(terms={'test': ['a', 'b']})


def test_range_filter():
    """Test range filter."""
    f = range_filter('test', start_date_math='startmath',
                     end_date_math='endmath')
    assert f(['1821--1940']) == Range(test={
        'gte': '1821||startmath', 'lte': '1940||endmath',
    })
    assert f(['>1821--']) == Range(test={'gt': '1821||startmath'})
    assert f(['1821--<1940']) == Range(test={'gte': '1821||startmath',
                                             'lt': '1940||endmath'})

    assert pytest.raises(RESTValidationError, f, ['2016'])
    assert pytest.raises(RESTValidationError, f, ['--'])


def test_create_filter_dsl():
    """Test request value extraction."""
    app = Flask('testapp')
    kwargs = MultiDict([('a', '1')])
    defs = dict(
        type=terms_filter('type.type'),
        subtype=terms_filter('type.subtype'),
    )

    with app.test_request_context(u'?type=a&type=b&subtype=c&type=zażółcić'):
        filters, args = _create_filter_dsl(kwargs, defs)
        assert len(filters) == 2
        assert args == MultiDict([
            ('a', u'1'),
            ('type', u'a'),
            ('type', u'b'),
            ('subtype', u'c'),
            ('type', u'zażółcić')
        ])

    kwargs = MultiDict([('a', '1')])
    with app.test_request_context('?atype=a&atype=b'):
        filters, args = _create_filter_dsl(kwargs, defs)
        assert not filters
        assert args == kwargs


def test_post_filter(app):
    """Test post filter."""
    urlargs = MultiDict()
    defs = dict(
        type=terms_filter('type'),
        subtype=terms_filter('subtype'),
    )

    with app.test_request_context('?type=test'):
        search = Search().query(Q(query='value'))
        search, args = _post_filter(search, urlargs, defs)
        assert 'post_filter' in search.to_dict()
        assert search.to_dict()['post_filter'] == dict(
            terms=dict(type=['test'])
        )
        assert args['type'] == 'test'

    with app.test_request_context('?anotertype=test'):
        search = Search().query(Q(query='value'))
        search, args = _post_filter(search, urlargs, defs)
        assert 'post_filter' not in search.to_dict()


def test_query_filter(app):
    """Test post filter."""
    urlargs = MultiDict()
    defs = dict(
        type=terms_filter('type'),
        subtype=terms_filter('subtype'),
    )

    with app.test_request_context('?type=test'):
        search = Search().query(Q('multi_match', query='value'))
        body = search.to_dict()
        search, args = _query_filter(search, urlargs, defs)
        assert 'post_filter' not in search.to_dict()
        assert search.to_dict()['query']['bool']['must'][0] == body['query']
        assert search.to_dict()['query']['bool']['filter'] == [
            dict(terms=dict(type=['test']))
        ]
        assert args['type'] == 'test'

    with app.test_request_context('?anotertype=test'):
        search = Search().query(Q(query='value'))
        body = search.to_dict()
        query, args = _query_filter(search, urlargs, defs)
        assert query.to_dict() == body


def test_aggregations(app):
    """Test aggregations."""
    with app.test_request_context(''):
        search = Search().query(Q(query='value'))
        defs = dict(
            type=dict(
                terms=dict(field='upload_type'),
            ),
            subtype=dict(
                terms=dict(field='subtype'),
            )
        )
        assert _aggregations(search, defs).to_dict()['aggs'] == defs


def test_default_facets_factory(app):
    """Test aggregations."""
    defs = dict(
        aggs=dict(
            type=dict(
                terms=dict(field='upload_type'),
            ),
            subtype=dict(
                terms=dict(field='subtype'),
            )
        ),
        filters=dict(
            subtype=terms_filter('subtype'),
        ),
        post_filters=dict(
            type=terms_filter('type'),
        ),
    )
    app.config['RECORDS_REST_FACETS']['testidx'] = defs

    with app.test_request_context('?type=a&subtype=b'):
        search = Search().query(Q(query='value'))
        search, urlkwargs = default_facets_factory(search, 'testidx')
        assert search.to_dict()['aggs'] == defs['aggs']
        assert 'post_filter' in search.to_dict()
        assert search.to_dict(
            )['query']['bool']['filter'][0]['terms']['subtype']

        search = Search().query(Q(query='value'))
        search, urlkwargs = default_facets_factory(search, 'anotheridx')
        assert 'aggs' not in search.to_dict()
        assert 'post_filter' not in search.to_dict()
        assert 'bool' not in search.to_dict()['query']
