# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Utilities for loading test records."""

import uuid

import mock
import pkg_resources
from dojson.contrib.marc21 import marc21
from dojson.contrib.marc21.utils import load
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.minters import recid_minter
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata
from invenio_search import current_search, current_search_client

from invenio_oaiserver import current_oaiserver
from invenio_oaiserver.minters import oaiid_minter
from invenio_oaiserver.models import OAISet
from invenio_oaiserver.receivers import after_insert_oai_set


def load_records(app, filename, schema, tries=5):
    """Try to index records."""
    indexer = RecordIndexer()
    records = []
    with app.app_context():
        with mock.patch("invenio_records.api.Record.validate", return_value=None):
            data_filename = pkg_resources.resource_filename("invenio_records", filename)
            records_data = load(data_filename)
            with db.session.begin_nested():
                for item in records_data:
                    record_id = uuid.uuid4()
                    item_dict = dict(marc21.do(item))
                    item_dict["$schema"] = schema
                    recid_minter(record_id, item_dict)
                    oaiid_minter(record_id, item_dict)
                    record = current_oaiserver.record_cls.create(
                        item_dict, id_=record_id
                    )
                    indexer.index(record)
                    records.append(record.id)
            db.session.commit()

        # Wait for indexer to finish
        for i in range(tries):
            response = current_search_client.search()
            if response["hits"]["total"] >= len(records):
                break
            current_search.flush_and_refresh("_all")

    return records


def remove_records(app, record_ids):
    """Remove all records."""
    with app.app_context():
        indexer = RecordIndexer()
        for r_id in record_ids:
            record = RecordMetadata.query.get(r_id)
            indexer.delete_by_id(r_id)
            pids = PersistentIdentifier.query.filter_by(object_uuid=r_id).all()
            for pid in pids:
                db.session.delete(pid)
            db.session.delete(record)
        db.session.commit()


def run_after_insert_oai_set():
    """Run task run_after_insert_oai_set."""
    for oaiset_id in [oaiset_.spec for oaiset_ in OAISet.query.all()]:
        oaiset = OAISet.query.filter_by(spec=oaiset_id).one()
        after_insert_oai_set(None, None, oaiset)


def create_record(app, item_dict, mint_oaiid=True):
    """Create test record."""
    indexer = RecordIndexer()
    with app.test_request_context():
        record_id = uuid.uuid4()
        recid_minter(record_id, item_dict)
        if mint_oaiid:
            oaiid_minter(record_id, item_dict)
        record = current_oaiserver.record_cls.create(item_dict, id_=record_id)
        indexer.index(record)
        return record
