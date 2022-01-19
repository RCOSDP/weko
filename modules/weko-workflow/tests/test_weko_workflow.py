# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Module tests."""

import threading

from flask import Flask, json, url_for
from invenio_db import db
from sqlalchemy import func

import weko_workflow.utils
from weko_workflow import WekoWorkflow
from weko_workflow.models import Activity


def test_version():
    """Test version import."""
    from weko_workflow import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoWorkflow(app)
    assert 'weko-workflow' in app.extensions

    app = Flask('testapp')
    ext = WekoWorkflow()
    assert 'weko-workflow' not in app.extensions
    ext.init_app(app)
    assert 'weko-workflow' in app.extensions


def test_view(app):
    """Test view."""
    WekoWorkflow(app)
    with app.test_request_context():
        url = url_for('weko_workflow.index')

    with app.test_client() as client:
        res = client.get(url)
        code = res.status_code
        assert code == 200 or code == 301 or code == 302
        if res.status_code == 200:
            assert 'Welcome to weko-workflow' in str(res.data)


def test_init_activity_success(app):
    """Test init_activity."""
    app.login_manager._login_disabled = True
    WekoWorkflow(app)
    with app.test_request_context():
        url = url_for('weko_workflow.init_activity')

    with app.test_client() as client:
        # Count Activity records before post
        before = db.session.query(func.count(Activity.id)).scalar()

        res = _post(client, url, {'workflow_id': 1, 'flow_id': 1})
        json_response = json.loads(res.get_data())
        assert json_response.get('code') == 0
        assert json_response.get('msg') == 'success'

        # Count Activity records after post
        after = db.session.query(func.count(Activity.id)).scalar()

        assert (before + 1) == after


def test_init_activity_failed(app):
    """Test init_activity failed."""
    app.login_manager._login_disabled = True
    WekoWorkflow(app)
    with app.test_request_context():
        url = url_for('weko_workflow.init_activity')

    with app.test_client() as client:
        # Count Activity records before post
        before = db.session.query(func.count(Activity.id)).scalar()

        res = _post(client, url, {})
        json_response = json.loads(res.get_data())
        assert json_response.get('code') == -1
        assert json_response.get('msg') == 'Failed to init activity!'

        # Count Activity records after post
        after = db.session.query(func.count(Activity.id)).scalar()

        assert before == after


def test_init_activity_thread(app):
    """Test init_activity."""
    app.login_manager._login_disabled = True
    WekoWorkflow(app)
    with app.test_request_context():
        url = url_for('weko_workflow.init_activity')

    with app.test_client() as client:
        t1 = threading.Thread(
            target=_post, args=(client, url, {
                'workflow_id': 1, 'flow_id': 1, 'extra_info': 'Thread_1'
            }))
        t2 = threading.Thread(
            target=_post, args=(client, url, {
                'workflow_id': 1, 'flow_id': 1, 'extra_info': 'Thread_2'
            }))
        t3 = threading.Thread(
            target=_post, args=(client, url, {
                'workflow_id': 1, 'flow_id': 1, 'extra_info': 'Thread_3'
            }))

        # Count Activity records before start
        before = db.session.query(func.count(Activity.id)).scalar()
        print(before)

        # Start threads
        t1.start()
        t2.start()
        t3.start()

        # Wait for threads complete
        t1.join()
        t2.join()
        t3.join()

        # Count Activity records after complete
        after = db.session.query(func.count(Activity.id)).scalar()
        print(after)

        assert (before + 3) == after


def _post(client, url, json_data):
    return client.post(url, json=json_data)
