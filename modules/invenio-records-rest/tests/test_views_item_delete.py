# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Delete record tests."""

from __future__ import absolute_import, print_function

from flask import url_for
from helpers import get_json, record_url
from invenio_pidstore.models import PersistentIdentifier
from mock import patch
from sqlalchemy.exc import SQLAlchemyError


def test_valid_delete(app, indexed_records):
    """Test VALID record delete request (DELETE .../records/<record_id>)."""
    # Test with and without headers
    for i, headers in enumerate([[], [('Accept', 'video/mp4')]]):
        pid, record = indexed_records[i]
        with app.test_client() as client:
            res = client.delete(record_url(pid), headers=headers)
            assert res.status_code == 204

            res = client.get(record_url(pid))
            assert res.status_code == 410


def test_delete_deleted(app, indexed_records):
    """Test deleting a perviously deleted record."""
    pid, record = indexed_records[0]

    with app.test_client() as client:
        res = client.delete(record_url(pid))
        assert res.status_code == 204

        res = client.delete(record_url(pid))
        assert res.status_code == 410
        data = get_json(res)
        assert 'message' in data
        assert data['status'] == 410


def test_delete_notfound(app, indexed_records):
    """Test INVALID record delete request (DELETE .../records/<record_id>)."""
    with app.test_client() as client:
        # Check that GET with non existing id will return 404
        res = client.delete(url_for(
            'invenio_records_rest.recid_item', pid_value=0))
        assert res.status_code == 404


def test_delete_with_sqldatabase_error(app, indexed_records):
    """Test VALID record delete request (GET .../records/<record_id>)."""
    pid, record = indexed_records[0]

    with app.test_client() as client:
        def raise_error():
            raise SQLAlchemyError()
        # Force an SQLAlchemy error that will rollback the transaction.
        with patch.object(PersistentIdentifier, 'delete',
                          side_effect=raise_error):
            res = client.delete(record_url(pid))
            assert res.status_code == 500

    with app.test_client() as client:
            res = client.get(record_url(pid))
            assert res.status_code == 200
