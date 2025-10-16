# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

"""Click command-line interface for record management."""

from __future__ import absolute_import, print_function

import sys

import click
from flask import current_app
from flask.cli import with_appcontext
from invenio_pidstore import current_pidstore
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier

def process_minter(value):
    """Load minter from PIDStore registry based on given value.

    :param value: Name of the minter.
    :returns: The minter.
    """
    try:
        return current_pidstore.minters[value]
    except KeyError:
        raise click.BadParameter(
            'Unknown minter {0}. Please use one of {1}.'.format(
                value, ', '.join(current_pidstore.minters.keys())
            )
        )


def process_schema(value):
    """Load schema from JSONSchema registry based on given value.

    :param value: Schema path, relative to the directory when it was
        registered.
    :returns: The schema absolute path.
    """
    schemas = current_app.extensions['invenio-jsonschemas'].schemas
    try:
        return schemas[value]
    except KeyError:
        raise click.BadParameter(
            'Unknown schema {0}. Please use one of:\n {1}'.format(
                value, '\n'.join(schemas.keys())
            )
        )


#
# Deposit management commands
#
@click.group()
def deposit():
    """Deposit management commands."""


@deposit.command()
@click.argument('source')
@with_appcontext
def schema(source):
    """Create deposit schema from an existing schema."""
    click.echo(process_schema(source))
    # TODO


@deposit.command()
@click.argument('source', type=click.File('r'), default=sys.stdin)
@click.option('-i', '--id', 'ids', multiple=True)
@click.option('--force', is_flag=True, default=False)
@with_appcontext
def create(source, ids, force, pid_minter=None):
    """Create new deposit."""


@deposit.command()
@click.option('-i', '--id', 'ids', multiple=True)
def publish(ids):
    """Publish selected deposits."""


@deposit.command()
@click.option('-i', '--id', 'ids', multiple=True)
def edit(ids):
    """Make selected deposits editable."""


@deposit.command()
@click.option('-i', '--id', 'ids', multiple=True)
def discard(ids):
    """Discard selected deposits."""


@deposit.command('reindex')
@click.option('-r', '--recid', required=True)
@with_appcontext
def reindex(recid):
    """Initialize indexing queue."""
    click.secho('Indexing record {} ...'.format(recid), fg='green')
    try:
        pid = PersistentIdentifier.get_by_object(pid_type='recid',
                                                 object_type='rec',
                                                 object_uuid=recid)
        if pid:
            query = PersistentIdentifier.query.filter_by(pid_type='recid',object_type='rec',object_uuid=recid).values(PersistentIdentifier.object_uuid)
            query = (x[0] for x in query)
            RecordIndexer().bulk_index(query)
    except PIDDoesNotExistError as e:
        click.secho('Specified record does not exist', fg='red')
    except Exception as e:
        click.secho(e, fg='red')
    click.secho('Execute "run" command to process the queue.', fg='green')


@deposit.command('run')
@click.option(
    '--raise-on-error', type=bool,default=True,
    help='raise BulkIndexError containing errors (as .errors) from the execution of the last chunk when some occur. By default we raise.')
@click.option(
    '--raise-on-exception', type=bool,default=True,
    help='if False then don’t propagate exceptions from call to bulk and just report the items that failed as failed.')
@click.option('--chunk-size',type=int,default=500,help='number of docs in one chunk sent to es (default: 500)')
@click.option(
    '--max-chunk-bytes',type=int,default=104857600,
    help='the maximum size of the request in bytes (default: 100MB)')
@click.option(
    '--max-retries',type=int,default=0,
    help='maximum number of times a document will be retired when 429 is received, set to 0 (default) for no retries on 429')
@click.option('--initial_backoff',type=int,default=2,help='number of secconds we should wait before the first retry.')
@click.option('--max-backoff',type=int,default=600,help='maximim number of seconds a retry will wait')
@click.option('--stats-only', type=bool, default=True,
              help='Only show indexing statistics without performing indexing.')
@with_appcontext
def run(version_type=None, raise_on_error=True,raise_on_exception=True,
        chunk_size=500,max_chunk_bytes=104857600,max_retries=0,
        initial_backoff=2,max_backoff=600, stats_only=True):
    """Initialize indexing queue."""
    try:
       RecordIndexer(version_type=version_type).process_bulk_queue_reindex(
                es_bulk_kwargs={'raise_on_error': raise_on_error,
                            'raise_on_exception': raise_on_exception,
                            'chunk_size':chunk_size,
                            'max_chunk_bytes':max_chunk_bytes,
                            'max_retries': max_retries,
                            'initial_backoff': initial_backoff,
                            'max_backoff': max_backoff,
                            'stats_only': stats_only},)
    except Exception as e:
        click.secho(e, fg='red')
    click.secho('Reindex process finished!', fg='green')
