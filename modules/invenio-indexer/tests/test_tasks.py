# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test celery task."""

from __future__ import absolute_import, print_function

import uuid

from mock import patch

from invenio_indexer.tasks import delete_record, index_record, \
    process_bulk_queue


def test_process_bulk_queue(app):
    """Test index records."""
    with patch('invenio_indexer.api.RecordIndexer.process_bulk_queue') as fun:
        process_bulk_queue.delay()
        assert fun.called


def test_index_record(app):
    """Test index records."""
    with patch('invenio_indexer.api.RecordIndexer.index_by_id') as fun:
        recid = str(uuid.uuid4())
        index_record.delay(recid)
        fun.assert_called_with(recid)


def test_delete_record(app):
    """Test index records."""
    with patch('invenio_indexer.api.RecordIndexer.delete_by_id') as fun:
        recid = str(uuid.uuid4())
        delete_record.delay(recid)
        fun.assert_called_with(recid)
