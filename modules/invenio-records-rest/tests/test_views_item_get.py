# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_views_item_get.py -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp

"""Get record tests."""

from __future__ import absolute_import, print_function

from flask import url_for
from tests.helpers import get_json, record_url, to_relative_url


def test_item_get(app, test_records):
    """Test record retrieval."""
    with app.test_client() as client:
        pid, record = test_records[0]

        res = client.get(record_url(pid))
        assert res.status_code == 200
        assert res.headers['ETag'] == '"{}"'.format(record.revision_id)

        # Check metadata
        data = get_json(res)
        for k in ['id', 'created', 'updated', 'metadata', 'links']:
            assert k in data

        assert data['id'] == int(pid.pid_value)
        assert data['metadata'] == record.dumps()

        # Check self links
        client.get(to_relative_url(data['links']['self']))
        assert res.status_code == 200
        assert data == get_json(res)


def test_item_get_etag(app, db, test_records):
    """Test VALID record get request (GET .../records/<record_id>)."""
    with app.test_client() as client:
        pid, record = test_records[0]

        res = client.get(record_url(pid))
        assert res.status_code == 200

def test_item_get_etag2(app, db, test_records):
    """Test VALID record get request (GET .../records/<record_id>)."""
    with app.test_client() as client:
        pid, record = test_records[0]

        res = client.get(record_url(pid))
        assert res.status_code == 200

        # Test request via etag
        etag = res.headers['ETag']
        res = client.get(record_url(pid), headers={'If-None-Match': etag})
        assert res.status_code == 304

def test_item_get_etag3(app, db, test_records):
    """Test VALID record get request (GET .../records/<record_id>)."""
    with app.test_client() as client:
        pid, record = test_records[0]

        res = client.get(record_url(pid))
        assert res.status_code == 200

        last_modified = res.headers['Last-Modified']
        # Test request via last-modified.
        res = client.get(
            record_url(pid), headers={'If-Modified-Since': last_modified})
        assert res.status_code == 304


def test_item_get_norecord(app, test_records):
    """Test INVALID record get request (GET .../records/<record_id>)."""
    with app.test_client() as client:
        # check that GET with non existing id will return 404
        res = client.get(url_for(
            'invenio_records_rest.recid_item', pid_value='0'),
        )
        assert res.status_code == 404


def test_item_get_invalid_mimetype(app, test_records):
    """Test invalid mimetype returns 406."""
    with app.test_client() as client:
        pid, record = test_records[0]

        # Check that GET with non accepted format will return 406
        res = client.get(record_url(pid), headers=[('Accept', 'video/mp4')])
        assert res.status_code == 406
