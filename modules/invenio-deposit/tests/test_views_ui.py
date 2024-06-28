# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test deposit UI views."""

from __future__ import absolute_import, print_function

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from invenio_db import db


def test_index_new(base_app, test_client, users):
    """Test index view."""
    with base_app.test_request_context():
        index_url = url_for('invenio_deposit_ui.index')
        new_url = url_for('invenio_deposit_ui.new')

    for u in [index_url, new_url]:
        res = test_client.get(u)
        assert res.status_code == 302
        assert '/login/' in res.location

    login_user_via_session(test_client, email=users[0]['email'])
    for u in [index_url, new_url]:
        assert test_client.get(u).status_code == 200


def test_edit(base_app, test_client, users, deposit):
    """Test edit view."""
    with base_app.test_request_context():
        edit_url = url_for(
            'invenio_deposit_ui.depid', pid_value=deposit.pid.pid_value)

    res = test_client.get(edit_url)
    assert res.status_code == 200

    # Test tombstone
    deposit.pid.delete()
    db.session.commit()

    res = test_client.get(edit_url)
    assert res.status_code == 410
