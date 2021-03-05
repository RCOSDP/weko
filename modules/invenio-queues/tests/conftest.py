# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile
from functools import wraps

import pytest
from flask import Flask
from kombu import Exchange
from mock import patch
from pkg_resources import EntryPoint

MOCK_MQ_EXCHANGE = Exchange(
    'test_events',
    type='direct',
    delivery_mode='transient',  # in-memory queue
    durable=True,
)


def remove_queues(app):
    """Delete all queues declared on the current app."""
    with app.app_context():
        ext = app.extensions['invenio-queues']
        for name, queue in ext.queues.items():
            if queue.exists:
                queue.queue.delete()


def mock_iter_entry_points_factory(data):
    """Create a mock iter_entry_points function."""
    from pkg_resources import iter_entry_points

    def entrypoints(group, name=None):
        if group == 'invenio_queues.queues':
            for entrypoint in data:
                yield entrypoint
        else:
            for x in iter_entry_points(group=group, name=name):
                yield x
    return entrypoints


@pytest.yield_fixture()
def test_queues_entrypoints(app):
    """Declare some queues by mocking the invenio_queues.queues entrypoint.

    It yields a list like [{name: queue_name, exchange: conf}, ...].
    """
    data = []
    result = []
    for idx in range(5):
        queue_name = 'queue{}'.format(idx)
        from pkg_resources import EntryPoint
        entrypoint = EntryPoint(queue_name, queue_name)
        conf = dict(name=queue_name, exchange=MOCK_MQ_EXCHANGE)
        entrypoint.load = lambda conf=conf: (lambda: [conf])
        data.append(entrypoint)
        result.append(conf)

    entrypoints = mock_iter_entry_points_factory(data)

    with patch('pkg_resources.iter_entry_points',
               entrypoints):
        try:
            yield result
        finally:
            remove_queues(app)


@pytest.yield_fixture()
def test_queues(app, test_queues_entrypoints):
    """Declare test queues."""
    with app.app_context():
        ext = app.extensions['invenio-queues']
        for conf in test_queues_entrypoints:
            queue = ext.queues[conf['name']]
            queue.queue.declare()
            assert queue.exists
    yield test_queues_entrypoints


@pytest.fixture()
def app():
    """Flask application fixture."""
    from invenio_queues import InvenioQueues
    app_ = Flask('testapp')
    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        TESTING=True,
    )
    InvenioQueues(app_)
    return app_
