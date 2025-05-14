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
from invenio_search import RecordsSearch


# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_views_suggesters.py -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
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
def test_valid_suggest(app, db, es, item_type, indexed_records, mock_es_execute, mocker):
    """Test VALID record creation request (POST .../records/)."""
    with app.test_client() as client:
        suggest_mocker = mocker.patch("elasticsearch_dsl.Search.suggest", return_value=RecordsSearch())
        # Valid simple completion suggester
        mocker.patch("elasticsearch_dsl.Search.execute", return_value=mock_es_execute({"suggest":{"text":"test_value", "text_filtered_source": {"_source": "1"}, "suggest_title": "test_title", "text_byyear": "test_byyear", "year": 1990}}))
        res = client.get(
            url_for('invenio_records_rest.recid_suggest'),
            query_string={'text': 'Back'}
        )
        assert res.status_code == 200
        suggest_mocker.assert_has_calls(
            [mocker.call("text","Back",completion=dict(field='suggest_title'))]
        )
        data = json.loads(res.get_data(as_text=True))
        assert data == {'text': 'test_value'}

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

        # Valid simple completion suggester with source filtering for ES5
        res = client.get(
            url_for('invenio_records_rest.recid_suggest'),
            query_string={'text_filtered_source': 'Back'}
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert data == { "text_filtered_source": {"_source": "1"}}

        # Valid simple completion suggester with size
        res = client.get(
            url_for('invenio_records_rest.recid_suggest'),
            query_string={'text': 'Back', 'size': 1}
        )
        data = json.loads(res.get_data(as_text=True))
        assert data == {'text': 'test_value'}

        # Valid context suggester
        res = client.get(
            url_for('invenio_records_rest.recid_suggest'),
            query_string={'text_byyear': 'Back', 'year': '2015'}
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert data == {"text_byyear": "test_byyear"}

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
