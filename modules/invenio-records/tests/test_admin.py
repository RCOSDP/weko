# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test admin interface."""

from __future__ import absolute_import, print_function

import uuid

from flask import url_for
from flask_admin import Admin, menu
from mock import patch
from sqlalchemy.exc import SQLAlchemyError

from invenio_records.admin import record_adminview
from invenio_records.api import Record

# .tox/c1/bin/pytest --cov=invenio_records tests/test_admin.py::test_admin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records/.tox/c1/tmp
def test_admin(app, db):
    """Test flask-admin interace."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type', 'application/json')
    ]
    admin = Admin(app, name="Test")

    assert 'model' in record_adminview
    assert 'modelview' in record_adminview

    # Register both models in admin
    model = record_adminview.pop('model')
    view = record_adminview.pop('modelview')
    admin.add_view(view(model, db.session, **record_adminview))

    # Check if generated admin menu contains the correct items
    menu_items = {str(item.name): item for item in admin.menu()}
    assert 'Records' in menu_items
    assert menu_items['Records'].is_category()

    submenu_items = {
        str(item.name): item for item in menu_items['Records'].get_children()}
    assert 'Record Metadata' in submenu_items
    assert isinstance(submenu_items['Record Metadata'], menu.MenuView)

    # Create a test record.
    rec_uuid = str(uuid.uuid4())
    Record.create({'title': 'test<script>alert(1);</script>'}, id_=rec_uuid)
    db.session.commit()

    with app.test_request_context():
        index_view_url = url_for('recordmetadata.index_view')
        delete_view_url = url_for('recordmetadata.delete_view')
        detail_view_url = url_for(
            'recordmetadata.details_view', id=rec_uuid)
        soft_delete_url = url_for('recordmetadata.soft_delete', id=1)

    with app.test_client() as client:
        # List index view and check record is there.
        res = client.get(index_view_url)
        assert res.status_code == 200

        # # Check for XSS in JSON output
        # res = client.get(detail_view_url)
        # assert res.status_code == 200
        # data = res.get_data(as_text=True)
        # assert '<pre>{' in data
        # assert '}</pre>' in data
        # assert '<script>alert(1);</script>' not in data

        # # Fake a problem with SQLAlchemy.
        # with patch('invenio_records.models.RecordMetadata') as db_mock:
        #     db_mock.side_effect = SQLAlchemyError()
        #     res = client.post(
        #         delete_view_url, data={'id': rec_uuid}, follow_redirects=True)
        #     assert res.status_code == 200

        # soft delete
        res = client.get(soft_delete_url, headers=HEADERS)
        assert res.status_code == 500

        # Delete it.
        res = client.post(
            delete_view_url, data={'id': rec_uuid}, follow_redirects=True)
        assert res.status_code == 200

        # # View the delete record
        # res = client.get(detail_view_url)
        # assert res.status_code == 200
        # assert '<pre>null</pre>' in res.get_data(as_text=True)

        # # Delete it again
        # res = client.post(
        #     delete_view_url, data={'id': rec_uuid}, follow_redirects=True)
        # assert res.status_code == 200
