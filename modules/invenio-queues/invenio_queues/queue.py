# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""API for logging stats events."""

from __future__ import absolute_import, print_function

from contextlib import contextmanager

from amqp.exceptions import ChannelError, NotFound
from kombu import Producer
from kombu import Queue as Q
from kombu.compat import Consumer
from werkzeug.utils import cached_property


class Queue(object):
    """Simple event queue."""

    def __init__(self, exchange, routing_key, connection_pool,
                 no_ack=True):
        """Initialize indexer."""
        self.exchange = exchange
        self.routing_key = routing_key
        self._connection_pool = connection_pool
        self.no_ack = no_ack

    @cached_property
    def connection_pool(self):
        """Retrieve the connection pool to the AMQP service."""
        return self._connection_pool()

    @property
    def queue(self):
        """Message queue queue."""
        with self.connection_pool.acquire(block=True) as conn:
            return Q(
                self.routing_key,
                exchange=self.exchange,
                routing_key=self.routing_key
            )(conn)

    @property
    def exists(self):
        """Test if this queue exists in the AMQP store.

        Note: This doesn't work with redis as declaring queues has not effect
        except creating the exchange.

        :returns: True if the queue exists, else False.
        :rtype: bool
        """
        try:
            queue = self.queue
            queue.queue_declare(passive=True)
        except NotFound:
            return False
        except ChannelError as e:
            if e.reply_code == '404':
                return False
            raise e
        return True

    def producer(self, conn):
        """Get a consumer for a connection."""
        return Producer(
            conn,
            exchange=self.exchange,
            routing_key=self.routing_key,
            auto_declare=True,
        )

    def consumer(self, conn):
        """Get a consumer for a connection."""
        return Consumer(
            connection=conn,
            queue=self.queue.name,
            exchange=self.exchange.name,
            exchange_type=self.exchange.type,
            durable=self.exchange.durable,
            auto_delete=self.exchange.auto_delete,
            routing_key=self.routing_key,
            no_ack=self.no_ack,
        )

    @contextmanager
    def create_producer(self):
        """Context manager that yields an instance of ``Producer``."""
        with self.connection_pool.acquire(block=True) as conn:
            yield self.producer(conn)

    @contextmanager
    def create_consumer(self):
        """Context manager that yields an instance of ``Consumer``."""
        with self.connection_pool.acquire(block=True) as conn:
            yield self.consumer(conn)

    def publish(self, events):
        """Publish events."""
        assert len(events) > 0
        with self.create_producer() as producer:
            for event in events:
                producer.publish(event)

    def consume(self, payload=True):
        """Consume events."""
        with self.create_consumer() as consumer:
            for msg in consumer.iterqueue():
                yield msg.payload if payload else msg
