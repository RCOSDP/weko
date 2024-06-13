# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record indexer for Invenio."""

from kombu import Exchange, Queue

INDEXER_DEFAULT_INDEX = "records-record-v1.0.0"
"""Default index to use if no schema is defined."""

INDEXER_MQ_EXCHANGE = Exchange("indexer", type="direct")
"""Default exchange for message queue."""

INDEXER_MQ_QUEUE = Queue("indexer", exchange=INDEXER_MQ_EXCHANGE, routing_key="indexer")
"""Default queue for message queue."""

INDEXER_MQ_ROUTING_KEY = "indexer"
"""Default routing key for message queue."""

INDEXER_MQ_PUBLISH_KWARGS = {}
"""Default message queue producer publishing kwargs.

Passed to ``kombu.Producer:publish``.

.. code-block:: python

    INDEXER_MQ_PUBLISH_KWARGS = {
        "retry": True,
        "retry_policy": {         # Setting for maximum waiting time of ~10min:
            "interval_start": 0,  # First retry immediately,
            "interval_step": 2,   # then increase by 2s for every retry.
            "interval_max": 30,   # but don't exceed 30s between retries.
            "max_retries": 30,    # give up after 30 tries.
        },
    }
"""

INDEXER_REPLACE_REFS = True
"""Whether to replace JSONRefs prior to indexing record."""

INDEXER_BULK_REQUEST_TIMEOUT = 10
"""Request timeout to use in Bulk indexing."""

INDEXER_MAX_BULK_CONSUMERS = 5
"""Maximum number of concurrent consumers for bulk indexing.

This threshold is applied per queue, so each indexing queue would
have a maximum of 5 consumers at the same time.
"""

INDEXER_RECORD_TO_INDEX = "invenio_indexer.utils.default_record_to_index"
"""Provide an implementation of record_to_index function"""

INDEXER_BEFORE_INDEX_HOOKS = []
"""List of automatically connected hooks (function or importable string)."""

INDEXER_MAX_BODY_SIZE = 62914560
