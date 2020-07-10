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

"""Invenio Queues utility functions."""

from flask import current_app
from kombu import Connection
from kombu.pools import connections


def get_connection_pool():
    """Retrieve the broker connection pool.

    Note: redis is not supported as "queue.exists" doesn't behave the same
    way.
    """
    return connections[Connection(
        # Allow invenio-queues to have a different broker than the Celery one
        current_app.config.get('QUEUES_BROKER_URL',
                               # otherwise use Celery's BROKER_URL
                               current_app.config.get('BROKER_URL', 'amqp://'))
    )]
