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
from helpers import create_record
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, \
    RecordIdentifier


def test_record_resolution(app, db):
    """Test resolution of PIDs to records."""
    # OK PID
    pid_ok, record = create_record({'title': 'test'})

    # Deleted PID
    pid_del, record = create_record({'title': 'deleted'})
    pid_del.delete()

    # Missing object PID
    pid_noobj = PersistentIdentifier.create(
        'recid', str(RecordIdentifier.next()), status=PIDStatus.REGISTERED)
    db.session.commit()

    # Redirected PID
    pid_red = PersistentIdentifier.create(
        'recid', '101', status=PIDStatus.REGISTERED)
    pid_red.redirect(pid_ok)

    # Redirect PID - different endpoint
    pid_doi = PersistentIdentifier.create(
        'doi', '10.1234/foo', status=PIDStatus.REGISTERED)
    pid_red_doi = PersistentIdentifier.create(
        'recid', '102', status=PIDStatus.REGISTERED)
    pid_red_doi.redirect(pid_doi)
    db.session.commit()

    headers = [('Accept', 'application/json')]
    with app.test_client() as client:
        # PID deleted
        res = client.get(
            url_for('invenio_records_rest.recid_item',
                    pid_value=pid_del.pid_value),
            headers=headers)
        assert res.status_code == 410

        # PID missing object
        res = client.get(
            url_for('invenio_records_rest.recid_item',
                    pid_value=pid_noobj.pid_value),
            headers=headers)
        assert res.status_code == 500

        # Redirected invalid endpoint
        res = client.get(
            url_for('invenio_records_rest.recid_item',
                    pid_value=pid_red_doi.pid_value),
            headers=headers)
        assert res.status_code == 500

        # Redirected
        res = client.get(
            url_for('invenio_records_rest.recid_item',
                    pid_value=pid_red.pid_value),
            headers=headers)
        assert res.status_code == 301
