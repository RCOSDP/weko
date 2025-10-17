# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Facets tests."""

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_facets.py -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp

from __future__ import absolute_import, print_function

import pytest
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Q, Range
from flask import Flask
from invenio_rest.errors import RESTValidationError
from werkzeug.datastructures import MultiDict

from weko_admin.models import FacetSearchSetting

from invenio_records_rest.facets import _aggregations, _create_filter_dsl, \
    _post_filter, _query_filter, default_facets_factory, range_filter, \
    terms_filter, terms_condition_filter


def test_terms_filter():
    """Test terms filter."""
    f = terms_filter('test')
    assert f(['a', 'b']).to_dict() == dict(terms={'test': ['a', 'b']})

def test_terms_codition_filter():
    """Test terms filter."""
    f1 = terms_condition_filter('test', False)
    assert f1(['a']).to_dict() == dict(terms={'test': ['a']})
    assert f1(['a', 'b']).to_dict() == dict(terms={'test': ['a', 'b']})

    f2 = terms_condition_filter('test', True)
    assert f2(['a']).to_dict() == dict(terms={'test': ['a']})
    assert f2(['a', 'b']).to_dict() == dict(bool={'must':[dict(term={'test': 'a'}), dict(term={'test': 'b'})]})



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

def test_default_facets_factory(app, db, search_user, redis_connect):
    """Test aggregations."""
    test_redis_key = "test_facet_search_query_has_permission"
    redis_connect.delete(test_redis_key)
    defs = dict(
        aggs=dict(
            type=dict(
                filter=dict(
                    bool=dict(
                        must=[
                            dict(
                                term=dict(publish_status="0")
                            )
                        ]
                    )
                ),
                aggs=dict(
                    type=dict(
                        terms=dict(
                            field="upload_type",size=1000
                        )
                    )
                )
            ),
            subtype=dict(
                filter=dict(
                    bool=dict(
                        must=[
                            dict(
                                term=dict(publish_status="0")
                            )
                        ]
                    )
                ),
                aggs=dict(
                    subtype=dict(
                        terms=dict(
                            field="subtype",size=1000
                        )
                    )
                )
            )
        ),
        post_filters=dict(
            bool=dict(
                must=[
                    dict(terms=dict(upload_type=["a"])),
                    dict(terms=dict(subtype=["b"]))
                ]
            )
        ),
    )
    type_setting = FacetSearchSetting(
        name_en="type",
        name_jp="type",
        mapping="upload_type",
        aggregations=[],
        active=True,
        ui_type="SelectBox",
        display_number=1,
        is_open=True,
        search_condition="AND"
    )
    subtype_setting = FacetSearchSetting(
        name_en="subtype",
        name_jp="subtype",
        mapping="subtype",
        aggregations=[],
        active=True,
        ui_type="SelectBox",
        display_number=2,
        is_open=True,
        search_condition="AND"
    )
    db.session.add(type_setting)
    db.session.add(subtype_setting)
    db.session.commit()
    app.config['SEARCH_UI_SEARCH_INDEX'] = 'testidx'
    from mock import patch
    with patch("weko_search_ui.permissions.search_permission.can",return_value=True):
        with patch("weko_admin.utils.get_query_key_by_permission", return_value=test_redis_key):
            with app.test_request_context('?type=a&subtype=b'):
                search = Search().query(Q(query='value'))
                search, urlkwargs = default_facets_factory(search, 'testidx')
                assert search.to_dict()['aggs'] == defs['aggs']
                assert 'post_filter' in search.to_dict()
                assert search.to_dict()['post_filter'] == defs['post_filters']

                search = Search().query(Q(query='value'))
                search, urlkwargs = default_facets_factory(search, 'anotheridx')
                assert 'aggs' not in search.to_dict()
                assert 'post_filter' not in search.to_dict()
                assert 'bool' not in search.to_dict()['query']
    redis_connect.delete(test_redis_key)