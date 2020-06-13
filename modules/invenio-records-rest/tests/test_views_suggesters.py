# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Basic tests."""

from __future__ import absolute_import, print_function

import json

import pytest
from elasticsearch import VERSION as ES_VERSION
from flask import url_for


@pytest.mark.parametrize('app', [dict(
    endpoint=dict(
        suggesters=dict(
            text=dict(completion=dict(
                field='suggest_title')),
            text_byyear=dict(completion=dict(
                field='suggest_byyear',
                context='year')),
            text_filtered_source=dict(
                _source=['control_number'],
                completion=dict(
                    field='suggest_title')),
        )
    )
)], indirect=['app'])
def test_valid_suggest(app, db, es, indexed_records):
    """Test VALID record creation request (POST .../records/)."""
    with app.test_client() as client:
        # Valid simple completion suggester
        res = client.get(
            url_for('invenio_records_rest.recid_suggest'),
            query_string={'text': 'Back'}
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert len(data['text'][0]['options']) == 2
        options = data['text'][0]['options']
        assert all('_source' in op for op in options)

        def is_option(d, options):
            """Check if the provided suggestion 'd' exists in the options."""
            return any(d == dict((k, op['_source'][k]) for k in d.keys())
                       for op in options)

        exp1 = {
            'control_number': '1',
            'stars': 4,
            'title': 'Back to the Future',
            'year': 2015
        }
        exp1_es5 = {
            'control_number': '1',
        }
        exp2 = {
            'control_number': '2',
            'stars': 3,
            'title': 'Back to the Past',
            'year': 2042
        }
        exp2_es5 = {
            'control_number': '2',
        }
        assert all(is_option(exp, options) for exp in [exp1, exp2])

        # Valid simple completion suggester with source filtering for ES5
        res = client.get(
            url_for('invenio_records_rest.recid_suggest'),
            query_string={'text_filtered_source': 'Back'}
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert len(data['text_filtered_source'][0]['options']) == 2
        options = data['text_filtered_source'][0]['options']
        assert all('_source' in op for op in options)

        exp_fi1 = exp1_es5 if ES_VERSION[0] >= 5 else exp1
        exp_fi2 = exp2_es5 if ES_VERSION[0] >= 5 else exp2
        assert all(is_option(exp, options) for exp in [exp_fi1, exp_fi2])

        # Valid simple completion suggester with size
        res = client.get(
            url_for('invenio_records_rest.recid_suggest'),
            query_string={'text': 'Back', 'size': 1}
        )
        data = json.loads(res.get_data(as_text=True))
        assert len(data['text'][0]['options']) == 1
        assert is_option(exp1, data['text'][0]['options'])

        # Valid context suggester
        res = client.get(
            url_for('invenio_records_rest.recid_suggest'),
            query_string={'text_byyear': 'Back', 'year': '2015'}
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert len(data['text_byyear'][0]['options']) == 1
        assert is_option(exp1, data['text_byyear'][0]['options'])

        # Missing context for context suggester
        res = client.get(
            url_for('invenio_records_rest.recid_suggest'),
            query_string={'text_byyear': 'Back'}
        )
        assert res.status_code == 400

        # Missing missing and invalid suggester
        res = client.get(
            url_for('invenio_records_rest.recid_suggest'),
            query_string={'invalid': 'Back'}
        )
        assert res.status_code == 400
