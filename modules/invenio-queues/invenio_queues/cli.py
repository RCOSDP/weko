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

"""CLI for Invenio-Stats."""

from __future__ import absolute_import, print_function

import click
from click.exceptions import ClickException
from flask.cli import with_appcontext

from .proxies import current_queues


@click.group(chain=True)
def queues():
    """Manage events queue."""


@queues.command('list')
@click.option('--declared', is_flag=True, help='show declared queues.')
@click.option('--undeclared', is_flag=True,
              help='show undeclared queues.')
@with_appcontext
def list(declared, undeclared):
    """List configured queues."""
    queues = current_queues.queues.values()
    if declared:
        queues = filter(lambda queue: queue.exists, queues)
    elif undeclared:
        queues = filter(lambda queue: not queue.exists, queues)
    queue_names = [queue.routing_key for queue in queues]
    queue_names.sort()
    for queue in queue_names:
        click.secho(queue)


@queues.command('declare')
@click.argument('queues', nargs=-1)
@with_appcontext
def declare(queues):
    """Initialize the given queues."""
    current_queues.declare(queues=queues)
    click.secho(
        'Queues {} have been declared.'.format(
            queues or current_queues.queues.keys()),
        fg='green'
    )


@queues.command('purge')
@click.argument('queues', nargs=-1)
@with_appcontext
def purge_queues(queues=None):
    """Purge the given queues."""
    current_queues.purge(queues=queues)
    click.secho(
        'Queues {} have been purged.'.format(
            queues or current_queues.queues.keys()),
        fg='green'
    )


@queues.command('delete')
@click.argument('queues', nargs=-1)
@with_appcontext
def delete_queue(queues):
    """Delete the given queues."""
    current_queues.delete(queues=queues)
    click.secho(
        'Queues {} have been deleted.'.format(
            queues or current_queues.queues.keys()),
        fg='green'
    )
