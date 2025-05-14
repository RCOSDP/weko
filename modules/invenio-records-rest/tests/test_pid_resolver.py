# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""PID resolver tests."""

from __future__ import absolute_import, print_function

from flask import url_for
from tests.helpers import create_record
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, \
    RecordIdentifier

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_pid_resolver.py -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
def test_record_resolution(app, db, test_records, item_type):
    """Test resolution of PIDs to records."""
    headers = [('Accept', 'application/json')]
    with app.test_client() as client:

        # Deleted PID
        pid_del, record = create_record({'title': 'deleted'})
        pid_del.delete()
        db.session.commit()
        # PID deleted
        res = client.get(
            url_for('invenio_records_rest.recid_item',
                    pid_value=pid_del.pid_value),
            headers=headers)
        assert res.status_code == 410

        # Missing object PID
        pid_noobj = PersistentIdentifier.create(
            'recid', str(RecordIdentifier.next()), status=PIDStatus.REGISTERED)
        db.session.commit()
        # PID missing object
        res = client.get(
            url_for('invenio_records_rest.recid_item',
                    pid_value=pid_noobj.pid_value),
            headers=headers)
        assert res.status_code == 500

         # Redirect PID - different endpoint
        pid_doi = PersistentIdentifier.create(
            'doi', '10.1234/foo', status=PIDStatus.REGISTERED)
        pid_red_doi = PersistentIdentifier.create(
            'recid', '102', status=PIDStatus.REGISTERED)
        pid_red_doi.redirect(pid_doi)
        db.session.commit()
        # Redirected invalid endpoint
        res = client.get(
            url_for('invenio_records_rest.recid_item',
                    pid_value=pid_red_doi.pid_value),
            headers=headers)
        assert res.status_code == 500

        # OK PID
        pid_ok, record = create_record({'title': 'test', 'item_type_id': '15'})
        # Redirected PID
        pid_red = PersistentIdentifier.create(
            'recid', '101', status=PIDStatus.REGISTERED)
        pid_red.redirect(pid_ok)
        db.session.commit()
        # Redirected
        res = client.get(
            url_for('invenio_records_rest.recid_item',
                    pid_value=pid_red.pid_value),
            headers=headers)
        assert res.status_code == 301
