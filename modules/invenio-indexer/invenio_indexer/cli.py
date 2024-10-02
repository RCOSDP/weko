# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CLI for indexer."""

import click
import copy
import uuid
import itertools
from celery.messaging import establish_connection
from flask import current_app
from flask.cli import with_appcontext
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from invenio_search import current_search_client
from invenio_search.cli import index
from sqlalchemy.dialects import postgresql

from .api import RecordIndexer
from .proxies import current_indexer_registry
from .tasks import process_bulk_queue


def abort_if_false(ctx, param, value):
    """Abort command is value is False."""
    if not value:
        ctx.abort()


def resultcallback(group):
    """Compatibility layer for Click 7 and 8."""
    if hasattr(group, "result_callback") and group.result_callback is not None:
        decorator = group.result_callback()
    else:
        # Click < 8.0
        decorator = group.resultcallback()
    return decorator


@index.command()
@click.option("--delayed", "-d", is_flag=True, help="Run indexing in background.")
@click.option(
    "--concurrency",
    "-c",
    default=1,
    type=int,
    help="Number of concurrent indexing tasks to start.",
)
@click.option(
    "--queue",
    "-q",
    type=str,
    help="Name of the celery queue used to put the tasks into.",
)
@click.option("--version-type", help="The search engine version type to use.")
@click.option(
    '--raise-on-error', type=bool,default=True,
    help='raise BulkIndexError containing errors (as .errors) from the execution of the last chunk when some occur. By default we raise.')
@click.option(
    '--raise-on-exception', type=bool,default=True,
    help='if False then don’t propagate exceptions from call to bulk and just report the items that failed as failed.')
@click.option('--chunk-size',type=int,default=500,help='number of docs in one chunk sent to es (default: 500)')
@click.option('--max-chunk-bytes',type=int,default=104857600,help='the maximum size of the request in bytes (default: 100MB)')
@click.option('--max-retries',type=int,default=0,help='maximum number of times a document will be retired when 429 is received, set to 0 (default) for no retries on 429')
@click.option('--initial_backoff',type=int,default=2,help='number of secconds we should wait before the first retry.')
@click.option('--max-backoff',type=int,default=600,help='maximim number of seconds a retry will wait')
@with_appcontext
def run(delayed, concurrency, version_type=None, queue=None,
        raise_on_error=True,raise_on_exception=True,chunk_size=500,max_chunk_bytes=104857600,max_retries=0,initial_backoff=2,max_backoff=600):
    """Run bulk record indexing."""
    if delayed:
        celery_kwargs = {
            "kwargs": {
                "version_type": version_type,
                "search_bulk_kwargs": {"raise_on_error": raise_on_error,'chunk_size':chunk_size,'max_chunk_bytes':max_chunk_bytes,'max_retries': max_retries,'initial_backoff': initial_backoff,'max_backoff': max_backoff},
                'with_deleted': True
            }
        }
        click.secho(
            "Starting {0} tasks for indexing records...".format(concurrency), fg="green"
        )
        if queue is not None:
            celery_kwargs.update({"queue": queue})
        for c in range(0, concurrency):
            process_bulk_queue.apply_async(**celery_kwargs)
    else:
        click.secho("Indexing records...", fg="green")
        RecordIndexer(version_type=version_type).process_bulk_queue(
            search_bulk_kwargs={"raise_on_error": raise_on_error,
                            'raise_on_exception': raise_on_exception,
                            'chunk_size':chunk_size,
                            'max_chunk_bytes':max_chunk_bytes,
                            'max_retries': max_retries,
                            'initial_backoff': initial_backoff,
                            'max_backoff': max_backoff},
            with_deleted=True
        )


@index.command()
@click.option(
    "--yes-i-know",
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt="Do you really want to reindex all records?",
)
@click.option("-t", "--pid-type", multiple=True, required=True)
@click.option('--skip-exists', is_flag=True, default=False)
@click.option('--size',type=int,default=6000)
@with_appcontext
def reindex(pid_type,skip_exists,size):
    """Reindex all records.

    :param pid_type: Pid type.
    """
    click.secho("Sending records to indexing queue ...", fg="green")

    query = (
        x[0]
        for x in PersistentIdentifier.query.filter_by(
            object_type="rec", status=PIDStatus.REGISTERED
        )
    )
    query = query.filter(RecordMetadata.id==PersistentIdentifier.object_uuid)
    query = query.filter(PersistentIdentifier.pid_type.in_(pid_type))
    values = query.values(PersistentIdentifier.object_uuid)
    _values = (str(x[0]) for x in values)

    if skip_exists:
        index=current_app.config["SEARCH_INDEX_PREFIX"]+"weko-item-v1.0.0"
        query = {"query": {"bool": {"must":{"exists":{"field":"itemtype"}}}},"_source":["itemtype"],"sort" : [{"_id":"asc"}],"size":size}
        res = current_search_client.search(index=index,
                                           body=query)
        hits = res['hits']['hits']
        ids = [x["_id"] for x in hits]
        while len(hits) == size:
            last_sort_key = hits[-1]['sort']
            query['search_after'] = last_sort_key
            _res = current_search_client.search(
                index=index,
                body=query
            )
            hits = _res['hits']['hits']
            _ids = [x["_id"] for x in hits]
            ids.extend(_ids)

        _tmp = set(_values)
        _ids = set(ids)
        diff = list(_tmp - _ids)
        _values = (x for x in diff)

    _values, _values2 = itertools.tee(_values)
    cnt = sum(1 for _ in _values2)
    click.secho('Queueing {} records..'.format(cnt),fg='green')
    RecordIndexer().bulk_index(_values)
    click.secho('Execute "run" command to process the queue!', fg="yellow")


@index.group(chain=True)
@click.option("-q", "--queue", "indexer_ids", multiple=True)
@click.option("-a", "--all-queues", is_flag=True)
def queue(indexer_ids=[], all_queues=False):
    """Manage indexing queue."""


@resultcallback(queue)
@with_appcontext
def process_actions(actions, indexer_ids=[], all_queues=False):
    """Process queue actions."""
    # Resolve indexer IDs
    if all_queues:
        indexers = current_indexer_registry.all().values()
    else:
        indexers = [current_indexer_registry.get(i) for i in indexer_ids]
    # Get queues
    queues = [i.mq_queue for i in indexers]
    # Always add the default indexer queue (for backwards compatibility)
    queues.append(current_app.config["INDEXER_MQ_QUEUE"])
    with establish_connection() as c:
        for queue in queues:
            bound_queue = queue(c)
            for action in actions:
                action(bound_queue)


@queue.command("init")
def init_queue():
    """Initialize indexing queue."""

    def action(queue):
        queue.declare()
        click.secho("Indexing queue has been initialized.", fg="green")
        return queue

    return action


@queue.command("purge")
def purge_queue():
    """Purge indexing queue."""

    def action(queue):
        queue.purge()
        click.secho("Indexing queue has been purged.", fg="green")
        return queue

    return action


@queue.command("delete")
def delete_queue():
    """Delete indexing queue."""

    def action(queue):
        queue.delete()
        click.secho("Indexing queue has been deleted.", fg="green")
        return queue

    return action