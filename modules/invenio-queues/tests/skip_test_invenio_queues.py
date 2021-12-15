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

"""Module tests."""

from __future__ import absolute_import, print_function

import pytest
from click.testing import CliRunner
from conftest import MOCK_MQ_EXCHANGE, mock_iter_entry_points_factory, \
    remove_queues
from flask import Flask
from mock import patch
from pkg_resources import EntryPoint

from invenio_queues import InvenioQueues
from invenio_queues.errors import DuplicateQueueError
from invenio_queues.proxies import current_queues


def test_version():
    """Test version import."""
    from invenio_queues import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = InvenioQueues(app)
    assert 'invenio-queues' in app.extensions

    app = Flask('testapp')
    ext = InvenioQueues()
    assert 'invenio-queues' not in app.extensions
    ext.init_app(app)
    assert 'invenio-queues' in app.extensions


def test_duplicate_queue(app):
    """Check that duplicate queues raise an exception."""
    with app.app_context():
        data = []
        for idx in range(2):
            queue_name = 'myqueue'
            entrypoint = EntryPoint(queue_name, queue_name)
            conf = dict(name=queue_name, exchange=MOCK_MQ_EXCHANGE)
            entrypoint.load = lambda conf=conf: (lambda: [conf])
            data.append(entrypoint)

        entrypoints = mock_iter_entry_points_factory(data)

        with patch('pkg_resources.iter_entry_points',
                   entrypoints):
            with pytest.raises(DuplicateQueueError):
                current_queues.queues()


with_different_brokers = pytest.mark.parametrize("config", [
    # test with default connection pool
    {},
    # test with in memory broker as the exception is not the same
    {'QUEUES_BROKER_URL': 'memory://'},
])
"""Test with standard and in memory broker."""


@with_different_brokers
def test_publish_and_consume(app, test_queues, config):
    """Test queue.publish and queue.consume."""
    app.config.update(config)
    with app.app_context():
        queue = current_queues.queues[test_queues[0]['name']]
        queue.publish([1, 2, 3])
        queue.publish([4, 5])
        assert list(queue.consume()) == [1, 2, 3, 4, 5]


@with_different_brokers
def test_queue_exists(app, test_queues_entrypoints, config):
    """Test the "declare" CLI."""
    app.config.update(config)
    with app.app_context():
        for queue in current_queues.queues.values():
            assert not queue.exists
        current_queues.declare()
        for queue in current_queues.queues.values():
            assert queue.exists


@with_different_brokers
def test_routing(app, test_queues, config):
    """Test basic routing of messages."""
    app.config.update(config)
    with app.app_context():
        q0 = current_queues.queues[test_queues[0]['name']]
        q1 = current_queues.queues[test_queues[1]['name']]
        q0.publish([{'event': '0'}])
        q1.publish([{'event': '1'}])

        assert list(q0.consume()) == [{'event': '0'}]
        assert list(q1.consume()) == [{'event': '1'}]
