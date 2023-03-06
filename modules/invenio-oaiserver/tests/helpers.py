# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Utilities for loading test records."""

from __future__ import absolute_import, print_function

import uuid
import copy
import mock
import pkg_resources

from dojson.contrib.marc21 import marc21
from dojson.contrib.marc21.utils import load
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore import current_pidstore
from invenio_pidstore.minters import recid_minter
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, Redirect, RecordIdentifier
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records import Record
from invenio_records.models import RecordMetadata
from invenio_search import current_search, current_search_client
from weko_records.api import ItemsMetadata
from weko_deposit.api import WekoDeposit, WekoIndexer,WekoRecord


from invenio_oaiserver.provider import OAIIDProvider
from invenio_oaiserver.minters import oaiid_minter
from invenio_oaiserver.models import OAISet
from invenio_oaiserver.receivers import after_insert_oai_set


def load_records(app, filename, schema, tries=5):
    """Try to index records."""
    indexer = RecordIndexer()
    records = []
    with app.app_context():
        with mock.patch('invenio_records.api.Record.validate',
                        return_value=None):
            data_filename = pkg_resources.resource_filename(
                'invenio_records', filename)
            records_data = load(data_filename)
            with db.session.begin_nested():
                for item in records_data:
                    record_id = uuid.uuid4()
                    item_dict = dict(marc21.do(item))
                    item_dict['$schema'] = schema
                    recid = recid_minter(record_id, item_dict)
                    oaiid_minter(record_id, item_dict)
                    record = Record.create(item_dict, id_=record_id)
                    indexer.index(record)
                    records.append(record.id)
            db.session.commit()

        # Wait for indexer to finish
        for i in range(tries):
            response = current_search_client.search()
            if response['hits']['total'] >= len(records):
                break
            current_search.flush_and_refresh('_all')

    return records


def remove_records(app, record_ids):
    """Remove all records."""
    with app.app_context():
        indexer = RecordIndexer()
        for r_id in record_ids:
            record = RecordMetadata.query.get(r_id)
            indexer.delete_by_id(r_id)
            pids = PersistentIdentifier.query.filter_by(
                object_uuid=r_id).all()
            for pid in pids:
                db.session.delete(pid)
            db.session.delete(record)
        db.session.commit()


def run_after_insert_oai_set():
    """Run task run_after_insert_oai_set."""
    for oaiset_id in [oaiset_.spec for oaiset_ in OAISet.query.all()]:
        oaiset = OAISet.query.filter_by(spec=oaiset_id).one()
        after_insert_oai_set(None, None, oaiset)

from mock import patch
def create_record(app, item_dict, mint_oaiid=True):
    """Create test record."""
    indexer = RecordIndexer()
    with app.test_request_context():
        record_id = uuid.uuid4()
        recid = recid_minter(record_id, item_dict)
        if mint_oaiid:
            oaiid_minter(record_id, item_dict)
        record = Record.create(item_dict, id_=record_id)
        with patch("invenio_indexer.api.RecordIndexer.record_to_index",return_value=("test-weko-item-v1.0.0","item-v1.0.0")):
            indexer.index(record)
        return record


def create_record_oai(record_data, item_data):
    """Create a test record."""
    with db.session.begin_nested():
        record_data = copy.deepcopy(record_data)
        item_data = copy.deepcopy(item_data)
        rec_uuid = uuid.uuid4()
        pid = current_pidstore.minters['recid'](rec_uuid, record_data)
        oai_pro = OAIIDProvider.create(
            object_type='rec',
            object_uuid=rec_uuid,
            pid_value=str(pid)
        )
        oai_pro = OAIIDProvider.create(
            object_type='oai',
            object_uuid=rec_uuid,
            pid_value="oai:{}".format(str(pid))
        )
        record = Record.create(record_data, id_=rec_uuid)
        item = ItemsMetadata.create(item_data, id_=rec_uuid)
    return (pid, oai_pro, record, item)

def create_record2(record_data, item_data):
    """Create a test record."""
    with db.session.begin_nested():
        record_data = copy.deepcopy(record_data)
        item_data = copy.deepcopy(item_data)
        rec_uuid = uuid.uuid4()
        recid = PersistentIdentifier.create('recid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        depid = PersistentIdentifier.create('depid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        rel = PIDRelation.create(recid,depid,3)
        db.session.add(rel)
        parent=None
        oai = None
        if "_oai" in record_data:
            oai_url = "oai:https://test.org/"+record_data["_oai"]["id"]
            try:
                PersistentIdentifier.get("oai",oai_url)
            except PIDDoesNotExistError:
                oai = PersistentIdentifier.create('oai',oai_url,object_type='rec', pid_provider="oai",object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        if '.' in record_data["recid"]:
            parent = PersistentIdentifier.get("recid",int(float(record_data["recid"])))
            recid_p = PIDRelation.get_child_relations(parent).one_or_none()
            PIDRelation.create(recid_p.parent, recid,2)
        else:
            parent = PersistentIdentifier.create('parent', "parent:{}".format(record_data["recid"]),object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
            rel = PIDRelation.create(parent, recid,2,0)
            db.session.add(rel)
            RecordIdentifier.next()
        record = WekoRecord.create(record_data, id_=rec_uuid)
        item = ItemsMetadata.create(item_data, id_=rec_uuid)
        #deposit = WekoDeposit(record, record.model)

        #deposit.commit()

    return recid, depid, record, item, parent, oai
