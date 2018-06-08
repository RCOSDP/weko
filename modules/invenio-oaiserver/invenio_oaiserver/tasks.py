# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Task for OAI."""

from celery import group, shared_task
from flask import current_app
from flask_celeryext import RequestContextTask
from invenio_db import db
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
    _records_commit(record_ids)
    db.session.commit()


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
