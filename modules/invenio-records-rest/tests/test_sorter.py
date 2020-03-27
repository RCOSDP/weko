# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test sorter."""

from __future__ import absolute_import, print_function

import pytest
from elasticsearch_dsl import Search

from invenio_records_rest.sorter import default_sorter_factory, eval_field, \
    geolocation_sort, parse_sort_field, reverse_order


def test_parse_sort_field():
    """Test parse sort field."""
    assert parse_sort_field("field") == ("field", True)
    assert parse_sort_field("-field") == ("field", False)
    assert parse_sort_field("field:_dfdf") == ("field:_dfdf", True)
    assert parse_sort_field("-field:_dfdf") == ("field:_dfdf", False)
    pytest.raises(AttributeError, parse_sort_field, None)


def test_reverse_order():
    """Test reverse order."""
    assert reverse_order('asc') == 'desc'
    assert reverse_order('desc') == 'asc'
    assert reverse_order('invalid') is None


def test_eval_field_string():
    """Test string evaluation."""
    assert eval_field("myfield", True) == dict(myfield=dict(order='asc'))
    assert eval_field("myfield", False) == dict(myfield=dict(order='desc'))
    assert eval_field("-myfield", True) == dict(myfield=dict(order='desc'))
    assert eval_field("-myfield", False) == dict(myfield=dict(order='asc'))


def test_eval_field_callable():
    """Test string evaluation."""
    def mycallable(order):
        return {'afield': {'order': 'asc' if order else 'desc'}}

    assert eval_field(mycallable, True) == dict(afield=dict(order='asc'))
    assert eval_field(mycallable, False) == dict(afield=dict(order='desc'))


def test_eval_field_dict():
    """Test string evaluation."""
    field = {'myfield': {'order': 'asc', 'mode': 'avg'}}

    assert eval_field(field, True) == dict(
        myfield=dict(order='asc', mode='avg'))
    computed = eval_field(field, False)
    assert computed == dict(
        myfield=dict(order='desc', mode='avg'))
    # Test for immutability
    assert field != computed


def test_geolocation_sort(app):
    """Test geolocation sort."""
    with app.test_request_context("/?pin=10,20&pin=gcpuuz94kkp"):
        v = geolocation_sort(
            'pin.location', 'pin', 'km', mode='avg', distance_type='arc')(True)
        assert v == {
            '_geo_distance': {
                'pin.location': ['10,20', 'gcpuuz94kkp'],
                'order': 'asc',
                'unit': 'km',
                'mode': 'avg',
                'distance_type': 'arc',
            }
        }


def test_default_sorter_factory(app):
    """Test default sorter factory."""
    app.config["RECORDS_REST_SORT_OPTIONS"] = dict(
        myindex=dict(
            myfield=dict(
                fields=['field1', '-field2'],
            )
        ),
    )
    app.config["RECORDS_REST_DEFAULT_SORT"] = dict(
        myindex=dict(
            query='-myfield',
            noquery='myfield',
        ),
    )

    # Sort
    with app.test_request_context("?sort=myfield"):
        query, urlargs = default_sorter_factory(Search(), 'myindex')
        assert query.to_dict()['sort'] == \
            [{'field1': {'order': 'asc'}}, {'field2': {'order': 'desc'}}]
        assert urlargs['sort'] == 'myfield'

    # Reverse sort
    with app.test_request_context("?sort=-myfield"):
        query, urlargs = default_sorter_factory(Search(), 'myindex')
        assert query.to_dict()['sort'] == \
            [{'field1': {'order': 'desc'}}, {'field2': {'order': 'asc'}}]
        assert urlargs['sort'] == '-myfield'

    # Invalid sort key
    with app.test_request_context("?sort=invalid"):
        query, urlargs = default_sorter_factory(Search(), 'myindex')
        assert 'sort' not in query.to_dict()
        assert urlargs == {}

    # Default sort without query
    with app.test_request_context("/?q="):
        query, urlargs = default_sorter_factory(Search(), 'myindex')
        assert query.to_dict()['sort'] == \
            [{'field1': {'order': 'asc'}}, {'field2': {'order': 'desc'}}]
        assert urlargs == dict(sort='myfield')

    # Default sort with query
    with app.test_request_context("/?q=test"):
        query, urlargs = default_sorter_factory(Search(), 'myindex')
        assert query.to_dict()['sort'] == \
            [{'field1': {'order': 'desc'}}, {'field2': {'order': 'asc'}}]
        assert urlargs == dict(sort='-myfield')

    # Default sort with query that includes unicodes
    with app.test_request_context("/?q=tést"):
        query, urlargs = default_sorter_factory(Search(), 'myindex')
        assert query.to_dict()['sort'] == \
            [{'field1': {'order': 'desc'}}, {'field2': {'order': 'asc'}}]
        assert urlargs == dict(sort='-myfield')

    # Default sort another index
    with app.test_request_context("/?q=test"):
        query, urlargs = default_sorter_factory(Search(), 'aidx')
        assert 'sort' not in query.to_dict()
