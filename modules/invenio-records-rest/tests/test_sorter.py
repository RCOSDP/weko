# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test sorter."""

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_sorter.py -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp

from __future__ import absolute_import, print_function

import pytest
from elasticsearch_dsl import Search
from invenio_i18n.ext import InvenioI18N, current_i18n
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


def test_eval_field_string(app):
    """Test getting locales."""
    app.config["I18N_LANGUAGES"] = [("ja", "Japanese"), ("en", "English")]
    
    """Test string evaluation."""
    assert eval_field("myfield", True) == dict(myfield=dict(order='asc',unmapped_type='long'))
    assert eval_field("myfield", False) == dict(myfield=dict(order='desc',unmapped_type='long'))
    assert eval_field("-myfield", True) == dict(myfield=dict(order='desc',unmapped_type='long'))
    assert eval_field("-myfield", False) == dict(myfield=dict(order='asc',unmapped_type='long'))
    assert eval_field("myfield", True, True) == dict(myfield=dict(order='asc',unmapped_type='long',nested=True))
    with app.test_request_context(
        headers=[('Accept-Language','ja')]):
            assert eval_field("title", True) == dict(title=dict(order='asc',unmapped_type='long',mode='max'))
            assert eval_field("title", False) == dict(title=dict(order='desc',unmapped_type='long',mode='max'))
    with app.test_request_context(
        headers=[('Accept-Language','en')]):
            assert eval_field("title", True) == dict(title=dict(order='asc',unmapped_type='long',mode='min'))
            assert eval_field("title", False) == dict(title=dict(order='desc',unmapped_type='long',mode='min'))
    assert eval_field("date_range", True) == {"_script":{"type":"number", "script":{"lang":"painless","source":"def x = params._source.date_range1;SimpleDateFormat format = new SimpleDateFormat(); if (x != null && !x.isEmpty() ) { def value = x.get(0).get(\"gte\"); if(value != null && !value.equals(\"\")) { if(value.length() > 7) { format.applyPattern(\"yyyy-MM-dd\"); } else if(value.length() > 4) { format.applyPattern(\"yyyy-MM\");  } else { format.applyPattern(\"yyyy\"); } try { return format.parse(value).getTime(); } catch(Exception e) {} } } format.applyPattern(\"yyyy\"); return format.parse(\"9999\").getTime();"},"order": 'asc'}}
    assert eval_field("date_range", False) == {"_script":{"type":"number", "script":{"lang":"painless","source":"def x = params._source.date_range1;SimpleDateFormat format = new SimpleDateFormat(); if (x != null && !x.isEmpty() ) { def value = x.get(0).get(\"lte\"); if(value != null && !value.equals(\"\")) { if(value.length() > 7) { format.applyPattern(\"yyyy-MM-dd\"); } else if(value.length() > 4) { format.applyPattern(\"yyyy-MM\");  } else { format.applyPattern(\"yyyy\"); } try { return format.parse(value).getTime(); } catch(Exception e) {} } } format.applyPattern(\"yyyy\"); return format.parse(\"0\").getTime();"},"order": 'desc'}}

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

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_sorter.py::test_default_sorter_factory -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
def test_default_sorter_factory(app):
    """Test default sorter factory."""
    app.config["RECORDS_REST_SORT_OPTIONS"] = dict(
        myindex=dict(
            myfield=dict(
                fields=['field1', '-field2'],
            ),
            controlnumber=dict(
                title='ID',
                fields=['control_number'],
                default_order='asc',
                order=2
            ),
            temporal=dict(
                title="Temporal",
                fields=["date_range1.gte"],
                default_order="asc",
                order=3
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
            [{'field1': {'order': 'asc', 'unmapped_type': 'long'}},
             {'field2': {'order': 'desc', 'unmapped_type': 'long'}},
             {"_script":{"type":"number", "script": "Float.parseFloat(doc['control_number'].value)", "order": "asc"}}]
        assert urlargs['sort'] == 'myfield'

    # Reverse sort
    with app.test_request_context("?sort=-myfield"):
        query, urlargs = default_sorter_factory(Search(), 'myindex')
        assert query.to_dict()['sort'] == \
            [{'field1': {'order': 'desc', 'unmapped_type': 'long'}},
             {'field2': {'order': 'asc', 'unmapped_type': 'long'}},
             {"_script":{"type":"number", "script": "Float.parseFloat(doc['control_number'].value)", "order": "asc"}}]
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
            [{'field1': {'order': 'asc', 'unmapped_type': 'long'}},
             {'field2': {'order': 'desc', 'unmapped_type': 'long'}},
             {"_script":{"type":"number", "script": "Float.parseFloat(doc['control_number'].value)", "order": "asc"}}]
        assert urlargs == dict(sort='myfield')

    # Default sort with query
    with app.test_request_context("/?q=test"):
        query, urlargs = default_sorter_factory(Search(), 'myindex')
        assert query.to_dict()['sort'] == \
            [{'field1': {'order': 'desc', 'unmapped_type': 'long'}},
             {'field2': {'order': 'asc', 'unmapped_type': 'long'}},
             {"_script":{"type":"number", "script": "Float.parseFloat(doc['control_number'].value)", "order": "asc"}}]
        assert urlargs == dict(sort='-myfield')

    # Default sort with query that includes unicodes
    with app.test_request_context("/?q=tést"):
        query, urlargs = default_sorter_factory(Search(), 'myindex')
        assert query.to_dict()['sort'] == \
            [{'field1': {'order': 'desc', 'unmapped_type': 'long'}},
             {'field2': {'order': 'asc', 'unmapped_type': 'long'}},
             {"_script":{"type":"number", "script": "Float.parseFloat(doc['control_number'].value)", "order": "asc"}}]
        assert urlargs == dict(sort='-myfield')

    # Default sort another index
    with app.test_request_context("/?q=test"):
        query, urlargs = default_sorter_factory(Search(), 'aidx')
        assert 'sort' not in query.to_dict()
        
    # Sort with control_number
    with app.test_request_context("/?sort=controlnumber"):
        query, urlargs = default_sorter_factory(Search(), 'myindex')
        assert query.to_dict()['sort'] == \
            [{"_script":{"type":"number", "script": "Float.parseFloat(doc['control_number'].value)", "order": "asc"}}]
        assert urlargs == dict(sort='controlnumber')
    
    # Reverse sort with control_number
    with app.test_request_context("/?sort=-controlnumber"):
        query, urlargs = default_sorter_factory(Search(), 'myindex')
        assert query.to_dict()['sort'] == \
            [{"_script":{"type":"number", "script": "Float.parseFloat(doc['control_number'].value)", "order": "desc"}}]
        assert urlargs == dict(sort='-controlnumber')

    # Sort with temporal
    with app.test_request_context("/?sort=temporal"):
        query, urlargs = default_sorter_factory(Search(), 'myindex')
        assert query.to_dict()['sort'] == \
            [{"_script":{"type":"number","script":{"lang":"painless","source":"def x = params._source.date_range1;SimpleDateFormat format = new SimpleDateFormat(); if (x != null && !x.isEmpty() ) { def value = x.get(0).get(\"gte\"); if(value != null && !value.equals(\"\")) { if(value.length() > 7) { format.applyPattern(\"yyyy-MM-dd\"); } else if(value.length() > 4) { format.applyPattern(\"yyyy-MM\");  } else { format.applyPattern(\"yyyy\"); } try { return format.parse(value).getTime(); } catch(Exception e) {} } } format.applyPattern(\"yyyy\"); return format.parse(\"9999\").getTime();"},"order": 'asc'}},
            {"_script":{"type":"number", "script": "Float.parseFloat(doc['control_number'].value)", "order": "asc"}}]
        assert urlargs == dict(sort='temporal')
    
    # Reverse sort with control_number
    with app.test_request_context("/?sort=-temporal"):
        query, urlargs = default_sorter_factory(Search(), 'myindex')
        assert query.to_dict()['sort'] == \
            [{"_script":{"type":"number","script":{"lang":"painless","source":"def x = params._source.date_range1;SimpleDateFormat format = new SimpleDateFormat(); if (x != null && !x.isEmpty() ) { def value = x.get(0).get(\"lte\"); if(value != null && !value.equals(\"\")) { if(value.length() > 7) { format.applyPattern(\"yyyy-MM-dd\"); } else if(value.length() > 4) { format.applyPattern(\"yyyy-MM\");  } else { format.applyPattern(\"yyyy\"); } try { return format.parse(value).getTime(); } catch(Exception e) {} } } format.applyPattern(\"yyyy\"); return format.parse(\"0\").getTime();"},"order": 'desc'}},
            {"_script":{"type":"number", "script": "Float.parseFloat(doc['control_number'].value)", "order": "asc"}}]
        assert urlargs == dict(sort='-temporal')
