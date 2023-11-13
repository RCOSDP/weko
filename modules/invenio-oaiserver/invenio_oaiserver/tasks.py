# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Task for OAI."""

from time import sleep

from celery import group, shared_task
from flask import current_app
from flask_celeryext import RequestContextTask
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record

from .query import get_affected_records

try:
    from itertools import zip_longest
except ImportError:  # pragma: no cover
    from itertools import izip_longest as zip_longest


def _records_commit(record_ids):
    """Commit all records."""
    for record_id in record_ids:
        record = Record.get_record(record_id)
        record.commit()


@shared_task(base=RequestContextTask)
def update_records_sets(record_ids):
    """Update records sets.

    :param record_ids: List of record UUID.
    """
    try:
        _records_commit(record_ids)
        db.session.commit()

        # update record to ES
        sleep(20)
        query = (x[0] for x in PersistentIdentifier.query.filter_by(
            object_type='rec', status=PIDStatus.REGISTERED
        ).filter(
            PersistentIdentifier.pid_type.in_(['oai'])
        ).filter(
            PersistentIdentifier.object_uuid.in_(record_ids)
        ).values(
            PersistentIdentifier.object_uuid
        ))
        RecordIndexer().bulk_index(query)
        RecordIndexer().process_bulk_queue(
            es_bulk_kwargs={'raise_on_error': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)


@shared_task(base=RequestContextTask)
def update_affected_records(spec=None, search_pattern=None):
    """Update all affected records by OAISet change.

    :param spec: The record spec.
    :param search_pattern: The search pattern.
    """
    chunk_size = current_app.config['OAISERVER_CELERY_TASK_CHUNK_SIZE']
    record_ids = get_affected_records(spec=spec, search_pattern=search_pattern)

    group(
        update_records_sets.s(list(filter(None, chunk)))
        for chunk in zip_longest(*[iter(record_ids)] * chunk_size)
    )()
