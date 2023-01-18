# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Stats testing helpers."""
import json
import copy
import uuid
from os.path import dirname, join

from invenio_db import db
from invenio_pidstore import current_pidstore
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from weko_records.api import ItemsMetadata, WekoRecord
from invenio_queues.proxies import current_queues


def get_queue_size(queue_name):
    """Get the current number of messages in a queue."""
    queue = current_queues.queues[queue_name]
    _, size, _ = queue.queue.queue_declare(passive=True)
    return size


def json_data(filename):
    with open(join(dirname(__file__),filename), "r") as f:
        return json.load(f)


def create_record(record_data, item_data):
    """Create a test record."""
    with db.session.begin_nested():
        record_data = copy.deepcopy(record_data)
        item_data = copy.deepcopy(item_data)
        rec_uuid = uuid.uuid4()
        recid = PersistentIdentifier.create(
            'recid',
            record_data['recid'],
            object_type='rec',
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED
        )
        depid = PersistentIdentifier.create(
            'depid',
            record_data['recid'],
            object_type='rec',
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED
        )
        record = WekoRecord.create(record_data, id_=rec_uuid)
        item = ItemsMetadata.create(item_data, id_=rec_uuid)
    return recid, record, item