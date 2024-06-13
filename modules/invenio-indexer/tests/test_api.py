# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test API."""

import json
import uuid
from unittest.mock import MagicMock, patch

import pytz
from celery.messaging import establish_connection
from invenio_db import db
from invenio_records.api import Record
from invenio_search.engine import dsl
from jsonresolver import JSONResolver
from jsonresolver.contrib.jsonref import json_loader_factory
from kombu.compat import Consumer

from invenio_indexer.api import BulkRecordIndexer, RecordIndexer
from invenio_indexer.signals import before_record_index


def test_indexer_bulk_index(app, queue):
    """Test delay indexing."""
    with app.app_context():
        with establish_connection() as c:
            indexer = RecordIndexer()
            id1 = uuid.uuid4()
            id2 = uuid.uuid4()
            indexer.bulk_index([id1, id2])
            indexer.bulk_delete([id1, id2])

            consumer = Consumer(
                connection=c,
                queue=indexer.mq_queue.name,
                exchange=indexer.mq_exchange.name,
                routing_key=indexer.mq_routing_key,
            )

            messages = list(consumer.iterqueue())
            [m.ack() for m in messages]

            assert len(messages) == 4
            data0 = messages[0].decode()
            assert data0["id"] == str(id1)
            assert data0["op"] == "index"
            data2 = messages[2].decode()
            assert data2["id"] == str(id1)
            assert data2["op"] == "delete"


def test_delete_action(app):
    """Test delete action."""
    with app.app_context():
        testid = str(uuid.uuid4())
        action = RecordIndexer()._delete_action(
            dict(id=testid, op="delete", index="idx")
        )
        assert action["_op_type"] == "delete"
        assert action["_index"] == "idx"
        assert action["_id"] == testid

        # Skip JSONSchema validation
        with patch("invenio_records.api._records_state.validate"):
            record = Record.create(
                {
                    "$schema": {"$ref": "/records/authorities/authority-v1.0.0.json"},
                    "title": "Test",
                }
            )
            db.session.commit()
        action = RecordIndexer()._delete_action(
            dict(id=str(record.id), op="delete", index=None)
        )
        assert action["_op_type"] == "delete"
        assert action["_index"] == "records-authorities-authority-v1.0.0"
        assert action["_id"] == str(record.id)

        record.delete()
        db.session.commit()
        action = RecordIndexer()._delete_action(
            dict(id=str(record.id), op="delete", index=None)
        )
        assert action["_op_type"] == "delete"
        # Deleted record doesn't have '$schema', so index cannot
        # be determined, resulting to the default from config
        assert action["_index"] == app.config["INDEXER_DEFAULT_INDEX"]
        assert action["_id"] == str(record.id)


def test_index_action(app):
    """Test index action."""
    with app.app_context():
        record = Record.create({"title": "Test"})
        db.session.commit()

        def receiver(sender, json=None, record=None, arguments=None, **kwargs):
            json["extra"] = "extra"
            arguments["pipeline"] = "foobar"

        with before_record_index.connected_to(receiver):
            action = RecordIndexer()._index_action(
                dict(
                    id=str(record.id),
                    op="index",
                )
            )
            assert action["_op_type"] == "index"
            assert action["_index"] == app.config["INDEXER_DEFAULT_INDEX"]
            assert action["_id"] == str(record.id)
            assert action["_version"] == record.revision_id
            assert action["_version_type"] == "external_gte"
            assert action["pipeline"] == "foobar"
            assert "title" in action["_source"]
            assert "extra" in action["_source"]


def test_process_bulk_queue(app, queue):
    """Test process indexing."""
    with app.app_context():
        # Create a test record
        r = Record.create({"title": "test"})
        db.session.commit()
        invalid_id2 = uuid.uuid4()

        RecordIndexer().bulk_index([r.id, invalid_id2])
        RecordIndexer().bulk_delete([r.id, invalid_id2])

        ret = {}

        def _mock_bulk(client, actions_iterator, **kwargs):
            ret["actions"] = list(actions_iterator)
            return len(ret["actions"])

        with patch("invenio_indexer.api.bulk", _mock_bulk):
            # Invalid actions are rejected
            assert RecordIndexer().process_bulk_queue() == 2
            assert [x["_op_type"] for x in ret["actions"]] == ["index", "delete"]


def test_process_bulk_queue_errors(app, queue):
    """Test error handling during indexing."""
    with app.app_context():
        # Create a test record
        r1 = Record.create({"title": "invalid", "reffail": {"$ref": "#/invalid"}})
        r2 = Record.create(
            {
                "title": "valid",
            }
        )
        db.session.commit()

        RecordIndexer().bulk_index([r1.id, r2.id])

        ret = {}

        def _mock_bulk(client, actions_iterator, **kwargs):
            ret["actions"] = list(actions_iterator)
            return len(ret["actions"])

        with patch("invenio_indexer.api.bulk", _mock_bulk):
            # Exceptions are caught
            assert RecordIndexer().process_bulk_queue() == 1
            assert len(ret["actions"]) == 1
            assert ret["actions"][0]["_id"] == str(r2.id)


def test_index(app):
    """Test record indexing."""
    with app.app_context():
        recid = uuid.uuid4()
        record = Record.create({"title": "Test"}, id_=recid)
        db.session.commit()

        client_mock = MagicMock()
        RecordIndexer(search_client=client_mock, version_type="force").index(
            record, arguments={"pipeline": "foobar"}
        )

        client_mock.index.assert_called_with(
            id=str(recid),
            version=0,
            version_type="force",
            index=app.config["INDEXER_DEFAULT_INDEX"],
            body={
                "title": "Test",
                "_created": pytz.utc.localize(record.created).isoformat(),
                "_updated": pytz.utc.localize(record.updated).isoformat(),
            },
            pipeline="foobar",
        )

        with patch("invenio_indexer.api.RecordIndexer.index") as fun:
            RecordIndexer(search_client=client_mock).index_by_id(recid)
            assert fun.called


def test_refresh_with_indexer(app, record_cls_with_index):
    """Test index refresh."""
    with app.app_context():
        client_mock = MagicMock()
        ri = RecordIndexer(
            search_client=client_mock,
            record_cls=record_cls_with_index,
            version_type="force",
        )
        ri.refresh()

        client_mock.indices.refresh.assert_called_with(
            index=app.config["INDEXER_DEFAULT_INDEX"]
        )


def test_refresh_with_indexer_and_prefix(search_prefix, app, record_cls_with_index):
    """Test index refresh."""
    with app.app_context():
        client_mock = MagicMock()
        ri = RecordIndexer(
            search_client=client_mock,
            record_cls=record_cls_with_index,
            version_type="force",
        )
        ri.refresh()

        prefix = app.config["SEARCH_INDEX_PREFIX"]
        index_name = app.config["INDEXER_DEFAULT_INDEX"]
        prefixed_index = f"{prefix}{index_name}"

        client_mock.indices.refresh.assert_called_with(index=prefixed_index)


def test_refresh_with_index_name(app):
    """Test index refresh."""
    with app.app_context():
        client_mock = MagicMock()
        index_name = app.config["INDEXER_DEFAULT_INDEX"]

        ri = RecordIndexer(search_client=client_mock, version_type="force")
        ri.refresh(index=index_name)

        client_mock.indices.refresh.assert_called_with(index=index_name)


def test_refresh_with_index_obj(app):
    """Test index refresh."""
    with app.app_context():
        client_mock = MagicMock()
        index_name = app.config["INDEXER_DEFAULT_INDEX"]

        ri = RecordIndexer(search_client=client_mock, version_type="force")
        ri.refresh(index=dsl.Index(index_name))

        client_mock.indices.refresh.assert_called_with(index=index_name)


def test_delete(app):
    """Test record indexing."""
    with app.app_context():
        recid = uuid.uuid4()
        record = Record.create({"title": "Test"}, id_=recid)
        db.session.commit()

        client_mock = MagicMock()
        RecordIndexer(search_client=client_mock).delete(record)

        client_mock.delete.assert_called_with(
            id=str(recid),
            index=app.config["INDEXER_DEFAULT_INDEX"],
            version=record.revision_id,
            version_type="external_gte",
        )

        with patch("invenio_indexer.api.RecordIndexer.delete") as fun:
            RecordIndexer(search_client=client_mock).delete_by_id(recid)
            assert fun.called


def test_replace_refs(app):
    """Test replace refs."""
    app.config["INDEXER_REPLACE_REFS"] = False
    app.extensions["invenio-records"].loader_cls = json_loader_factory(
        JSONResolver(plugins=["demo.json_resolver"])
    )

    with app.app_context():
        record = Record({"$ref": "http://dx.doi.org/10.1234/foo"})
        data = RecordIndexer()._prepare_record(record, "records", "record")
        assert "$ref" in data

    app.config["INDEXER_REPLACE_REFS"] = True
    with app.app_context():
        record = Record({"$ref": "http://dx.doi.org/10.1234/foo"})
        data = RecordIndexer()._prepare_record(record, "records", "record")
        assert "$ref" not in data
        assert json.dumps(data)


def test_bulkrecordindexer_index_delete_by_record_id(app, queue):
    """Test utility class BulkRecordIndexer index/delete by record id."""
    with app.app_context():
        with establish_connection() as c:
            indexer = BulkRecordIndexer()
            id1 = uuid.uuid4()
            indexer.index_by_id(id1)
            indexer.delete_by_id(id1)

            consumer = Consumer(
                connection=c,
                queue=indexer.mq_queue.name,
                exchange=indexer.mq_exchange.name,
                routing_key=indexer.mq_routing_key,
            )

            messages = list(consumer.iterqueue())
            [m.ack() for m in messages]

            assert len(messages) == 2
            data0 = messages[0].decode()
            assert data0["id"] == str(id1)
            assert data0["op"] == "index"
            data1 = messages[1].decode()
            assert data1["id"] == str(id1)
            assert data1["op"] == "delete"


def test_bulkrecordindexer_index_delete_by_record(app, queue):
    """Test utility class BulkRecordIndexer index/delete by record object."""
    with app.app_context():
        with establish_connection() as c:
            recid = uuid.uuid4()
            record = Record.create({"title": "Test"}, id_=recid)
            db.session.commit()
            indexer = BulkRecordIndexer()
            indexer.index(record)
            indexer.delete(record)

            consumer = Consumer(
                connection=c,
                queue=indexer.mq_queue.name,
                exchange=indexer.mq_exchange.name,
                routing_key=indexer.mq_routing_key,
            )

            messages = list(consumer.iterqueue())
            [m.ack() for m in messages]

            assert len(messages) == 2
            data0 = messages[0].decode()
            assert data0["id"] == str(recid)
            assert data0["op"] == "index"
            data1 = messages[1].decode()
            assert data1["id"] == str(recid)
            assert data1["op"] == "delete"


def test_before_record_index_dynamic_connect(app):
    """Test before_record_index.dynamic_connect."""
    with app.app_context():
        with patch("invenio_records.api._records_state.validate"):
            auth_record = Record.create(
                {
                    "$schema": "/records/authorities/authority-v1.0.0.json",
                    "title": "Test",
                }
            )
            bib_record = Record.create(
                {
                    "$schema": "/records/bibliographic/bibliographic-v1.0.0.json",
                    "title": "Test",
                }
            )
            db.session.commit()

        def _simple(sender, json=None, **kwargs):
            json["simple"] = "simple"

        def _custom(sender, json=None, **kwargs):
            json["custom"] = "custom"

        def _cond(sender, connect_kwargs, index=None, **kwargs):
            return "bibliographic" in index

        _receiver1 = before_record_index.dynamic_connect(
            _simple, index="records-authorities-authority-v1.0.0"
        )
        _receiver2 = before_record_index.dynamic_connect(_custom, condition_func=_cond)

        action = RecordIndexer()._index_action(dict(id=str(auth_record.id), op="index"))
        assert "title" in action["_source"]
        assert action["_source"]["simple"] == "simple"

        action = RecordIndexer()._index_action(
            dict(id=str(bib_record.id), index="foo", op="index")
        )
        assert "title" in action["_source"]
        assert action["_source"]["custom"] == "custom"

        before_record_index.disconnect(_receiver1)
        before_record_index.disconnect(_receiver2)


def test_indexer_record_class():
    """Tests the usage of a custom record class."""

    class DummyRecord:
        """Dummy record class."""

        pass

    indexer = RecordIndexer()
    assert indexer.record_cls == Record

    indexer = RecordIndexer(record_cls=DummyRecord)
    assert indexer.record_cls == DummyRecord
