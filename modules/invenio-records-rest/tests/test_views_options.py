# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_views_option.py -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
"""Test sorter."""

from __future__ import absolute_import, print_function

import json

import pytest
from flask import url_for


def test_options_view(app, search_class):
    """Test default sorter factory."""
    app.config["RECORDS_REST_SORT_OPTIONS"] = {
        search_class.Meta.index: dict(
            myfield=dict(
                fields=['field1:asc'],
                title='My Field',
                order=2,
            ),
            anotherfield=dict(
                fields=['field2:asc'],
                title='My Field',
                default_order='desc',
                order=1,
            )
        )
    }

    with app.test_client() as client:
        res = client.get(
            url_for('invenio_records_rest.recid_list_options'))
        data = json.loads(res.get_data(as_text=True))
        assert data['max_result_window'] == 10000
        assert data['default_media_type'] == 'application/json'
        assert data['item_media_types'] == ['application/json']
        assert data['search_media_types'] == ['application/json']
        assert data['sort_fields'] == []


@pytest.mark.parametrize('app', [dict(
    endpoint=dict(use_options_view=False)
)], indirect=['app'])
def test_use_options(app, db):
    """Test extension initialization."""
    # db fixture needed because _options will now be caught by the default
    # records detail item endpoint which requires db access.
    with app.app_context():
        with app.test_client() as client:
            res = client.get('/records/_options')
            assert res.status_code == 404
