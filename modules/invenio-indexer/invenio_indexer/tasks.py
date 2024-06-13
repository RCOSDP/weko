# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Celery tasks to index records."""

from celery import shared_task

from .api import RecordIndexer
from .proxies import current_indexer_registry


@shared_task(ignore_result=True)
def process_bulk_queue(version_type=None, search_bulk_kwargs=None, indexer_name=None):
    """Process bulk indexing queue.

    :param str version_type: the search engine version type.
    :param dict search_bulk_kwargs: Passed to `search.helpers.bulk`.
    :param indexer_name: Name of the indexer to get from the registry.
        Incompatible with version_type.

    Note: You can start multiple versions of this task.
    """
    if indexer_name:
        indexer = current_indexer_registry.get(indexer_name)
    else:
        indexer = RecordIndexer(version_type=version_type)

    indexer.process_bulk_queue(search_bulk_kwargs=search_bulk_kwargs)


@shared_task(ignore_result=True)
def index_record(record_uuid, indexer_name=None):
    """Index a single record.

    :param record_uuid: The record UUID.
    :param indexer_name: Name of the indexer to get from the registry.
    """
    if indexer_name:
        indexer = current_indexer_registry.get(indexer_name)
    else:
        indexer = RecordIndexer()

    indexer.index_by_id(record_uuid)


@shared_task(ignore_result=True)
def delete_record(record_uuid, indexer_name=None):
    """Delete a single record.

    :param record_uuid: The record UUID.
    :param indexer_name: Name of the indexer to get from the registry.
    """
    if indexer_name:
        indexer = current_indexer_registry.get(indexer_name)
    else:
        indexer = RecordIndexer()

    indexer.delete_by_id(record_uuid)
