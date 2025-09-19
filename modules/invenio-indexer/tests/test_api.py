# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test API."""

from __future__ import absolute_import, print_function
import types
import json
import uuid

import pytz
import pytest
from celery.messaging import establish_connection
from invenio_db import db
from invenio_records.api import Record
from jsonresolver import JSONResolver
from jsonresolver.contrib.jsonref import json_loader_factory
from kombu.compat import Consumer
from kombu import Exchange, Queue

from mock import MagicMock, patch

from invenio_indexer.api import BulkRecordIndexer, RecordIndexer
from invenio_indexer.signals import before_record_index

class DummyRecord:
    def __init__(self, id, version_id, revision_id, created=None, updated=None):
        self.id = id
        self.model = types.SimpleNamespace(version_id=version_id)
        self.revision_id = revision_id
        self.created = created
        self.updated = updated
    def dumps(self):
        return {'dummy': True}
class DummyMessage:
    def __init__(self, payload):
        self._payload = payload
        self.acked = False
        self.rejected = False
    def decode(self):
        return self._payload
    def ack(self):
        self.acked = True
    def reject(self):
        self.rejected = True

# .tox/c1/bin/pytest --cov=invenio_indexer tests/test_api.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-indexer/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=invenio_indexer tests/test_api.py::test_indexer_bulk_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-indexer/.tox/c1/tmp
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
                routing_key=indexer.mq_routing_key)

            messages = list(consumer.iterqueue())
            [m.ack() for m in messages]

            assert len(messages) == 4
            data0 = messages[0].decode()
            assert data0['id'] == str(id1)
            assert data0['op'] == 'index'
            data2 = messages[2].decode()
            assert data2['id'] == str(id1)
            assert data2['op'] == 'delete'


def test_delete_action(app):
    """Test delete action."""
    with app.app_context():
        testid = str(uuid.uuid4())
        action = RecordIndexer()._delete_action(
            dict(id=testid, op='delete', index='idx', doc_type='doc'))
        assert action['_op_type'] == 'delete'
        assert action['_index'] == 'idx'
        assert action['_type'] == 'doc'
        assert action['_id'] == testid

        with patch('invenio_indexer.api.Record.get_record') as r:
            r.return_value = {'$schema': {
                '$ref': '/records/authorities/authority-v1.0.0.json'
            }}
            action = RecordIndexer()._delete_action(
                dict(id='myid', op='delete', index=None, doc_type=None))
            assert action['_op_type'] == 'delete'
            assert action['_index'] == 'records-authorities-authority-v1.0.0'
            assert action['_type'] == 'authority-v1.0.0'
            assert action['_id'] == 'myid'


def test_index_action(app):
    """Test index action."""
    with app.app_context():
        record = Record.create({'title': 'Test'})
        db.session.commit()

        def receiver(sender, json=None, record=None, arguments=None, **kwargs):
            json['extra'] = 'extra'
            arguments['pipeline'] = 'foobar'

        with before_record_index.connected_to(receiver):
            action = RecordIndexer()._index_action(dict(
                id=str(record.id),
                op='index',
            ))
            assert action['_op_type'] == 'index'
            assert action['_index'] == app.config['INDEXER_DEFAULT_INDEX']
            assert action['_type'] == app.config['INDEXER_DEFAULT_DOC_TYPE']
            assert action['_id'] == str(record.id)
            assert action['_version'] == record.revision_id
            assert action['_version_type'] == 'external_gte'
            assert action['pipeline'] == 'foobar'
            assert 'title' in action['_source']
            assert 'extra' in action['_source']


def test_process_bulk_queue(app, queue):
    """Test process indexing."""
    with app.app_context():
        # Create a test record
        r = Record.create({'title': 'test'})
        db.session.commit()
        invalid_id2 = uuid.uuid4()

        RecordIndexer().bulk_index([r.id, invalid_id2])
        RecordIndexer().bulk_delete([r.id, invalid_id2])

        ret = {}

        def _mock_bulk(client, actions_iterator, **kwargs):
            ret['actions'] = list(actions_iterator)
            return len(ret['actions'])

        with patch('invenio_indexer.api.bulk', _mock_bulk):
            # Invalid actions are rejected
            assert RecordIndexer().process_bulk_queue() == 2
            assert [x['_op_type'] for x in ret['actions']] == \
                ['index', 'delete']


def test_process_bulk_queue_errors(app, queue):
    """Test error handling during indexing."""
    with app.app_context():
        # Create a test record
        r1 = Record.create({
            'title': 'invalid', 'reffail': {'$ref': '#/invalid'}})
        r2 = Record.create({
            'title': 'valid', })
        db.session.commit()

        RecordIndexer().bulk_index([r1.id, r2.id])

        ret = {}

        def _mock_bulk(client, actions_iterator, **kwargs):
            ret['actions'] = list(actions_iterator)
            return len(ret['actions'])

        with patch('invenio_indexer.api.bulk', _mock_bulk):
            # Exceptions are caught
            assert RecordIndexer().process_bulk_queue() == 1
            assert len(ret['actions']) == 1
            assert ret['actions'][0]['_id'] == str(r2.id)


def test_index(app):
    """Test record indexing."""
    with app.app_context():
        recid = uuid.uuid4()
        record = Record.create({'title': 'Test'}, id_=recid)
        db.session.commit()

        client_mock = MagicMock()
        RecordIndexer(search_client=client_mock, version_type='force').index(
            record, arguments={'pipeline': 'foobar'})

        client_mock.index.assert_called_with(
            id=str(recid),
            version=0,
            version_type='force',
            index=app.config['INDEXER_DEFAULT_INDEX'],
            doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],
            body={
                'title': 'Test',
                '_created': pytz.utc.localize(record.created).isoformat(),
                '_updated': pytz.utc.localize(record.updated).isoformat(),
            },
            pipeline='foobar',
        )

        with patch('invenio_indexer.api.RecordIndexer.index') as fun:
            RecordIndexer(search_client=client_mock).index_by_id(recid)
            assert fun.called


def test_delete(app):
    """Test record indexing."""
    with app.app_context():
        recid = uuid.uuid4()
        record = Record.create({'title': 'Test'}, id_=recid)
        db.session.commit()

        client_mock = MagicMock()
        RecordIndexer(search_client=client_mock).delete(record)

        client_mock.delete.assert_called_with(
            id=str(recid),
            index=app.config['INDEXER_DEFAULT_INDEX'],
            doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],
        )

        with patch('invenio_indexer.api.RecordIndexer.delete') as fun:
            RecordIndexer(search_client=client_mock).delete_by_id(recid)
            assert fun.called


def test_replace_refs(app):
    """Test replace refs."""
    app.config['INDEXER_REPLACE_REFS'] = False
    app.extensions['invenio-records'].loader_cls = json_loader_factory(
            JSONResolver(plugins=['tests.demo.json_resolver']))

    with app.app_context():
        record = Record({'$ref': 'http://dx.doi.org/10.1234/foo'})
        data = RecordIndexer._prepare_record(record, 'records', 'record')
        assert '$ref' in data

    app.config['INDEXER_REPLACE_REFS'] = True
    with app.app_context():
        record = Record({'$ref': 'http://dx.doi.org/10.1234/foo'})
        data = RecordIndexer._prepare_record(record, 'records', 'record')
        assert '$ref' not in data
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
                routing_key=indexer.mq_routing_key)

            messages = list(consumer.iterqueue())
            [m.ack() for m in messages]

            assert len(messages) == 2
            data0 = messages[0].decode()
            assert data0['id'] == str(id1)
            assert data0['op'] == 'index'
            data1 = messages[1].decode()
            assert data1['id'] == str(id1)
            assert data1['op'] == 'delete'


def test_bulkrecordindexer_index_delete_by_record(app, queue):
    """Test utility class BulkRecordIndexer index/delete by record object."""
    with app.app_context():
        with establish_connection() as c:
            recid = uuid.uuid4()
            record = Record.create({'title': 'Test'}, id_=recid)
            db.session.commit()
            indexer = BulkRecordIndexer()
            indexer.index(record)
            indexer.delete(record)

            consumer = Consumer(
                connection=c,
                queue=indexer.mq_queue.name,
                exchange=indexer.mq_exchange.name,
                routing_key=indexer.mq_routing_key)

            messages = list(consumer.iterqueue())
            [m.ack() for m in messages]

            assert len(messages) == 2
            data0 = messages[0].decode()
            assert data0['id'] == str(recid)
            assert data0['op'] == 'index'
            data1 = messages[1].decode()
            assert data1['id'] == str(recid)
            assert data1['op'] == 'delete'

@pytest.mark.parametrize(
    "body, expected_file, has_content, version_id, es_version, expect_commit, max_body_size, expect_error",
    [
        # If body_size > max_body_size and content exists, commit because version_id < es_version
        ({'content': [{'file': 'a'*100}]}, '', True, 1, 3, True, 10, False),
        # If body_size > max_body_size and no content, commit because version_id < es_version
        ({'foo': 'bar', 'file': 'a'*100}, 'a'*100, False, 1, 3, True, 10, False),
        # Normal commit
        ({'foo': 'bar', 'content': [{'file': 'abc'}]}, 'abc', True, 1, 3, True, 1000, False),
        # No commit
        ({'foo': 'bar', 'content': [{'file': 'abc'}]}, 'abc', True, 5, 3, False, 1000, False),
        # SQLAlchemyError occurs
        ({'foo': 'bar', 'content': [{'file': 'abc'}]}, 'abc', True, 1, 3, False, 1000, True),
    ]
)
def test__index_action_sync_version_cases(monkeypatch, body, expected_file, has_content, version_id, es_version, expect_commit, max_body_size, expect_error):
    import sys
    import sqlalchemy

    def setup_indexer_and_env():
        # Setup dummy record and monkeypatch Record.get_record
        dummy_record = DummyRecord('rid', version_id, 2)
        monkeypatch.setattr('invenio_indexer.api.Record', types.SimpleNamespace(get_record=lambda rid: dummy_record))
        # Setup dummy WekoIndexer
        class DummyWekoIndexer:
            def get_es_index(self): return None
            def get_metadata_by_item_id(self, rid): return {'_version': es_version}
        sys.modules['weko_deposit.api'] = types.SimpleNamespace(WekoIndexer=DummyWekoIndexer)
        # Setup dummy DB session
        committed = {'called': False}
        class DummySession:
            def commit(self):
                if expect_error:
                    raise sqlalchemy.exc.SQLAlchemyError('sqlalchemy')
                committed['called'] = True
            def rollback(self):
                pass
        monkeypatch.setattr('invenio_indexer.api.db', types.SimpleNamespace(session=DummySession()))
        # Setup dummy logger and traceback
        called = {'error': False, 'trace': False}
        class DummyLogger:
            def error(self, *a, **k): called['error'] = True
        monkeypatch.setattr('invenio_indexer.api.current_app', types.SimpleNamespace(
            logger=DummyLogger(),
            config={'INDEXER_MAX_BODY_SIZE': max_body_size}
        ))
        monkeypatch.setattr('invenio_indexer.api.click', types.SimpleNamespace(secho=lambda *a, **k: None))
        monkeypatch.setattr('invenio_indexer.api.traceback', types.SimpleNamespace(print_exc=lambda: called.update({'trace': True})))
        # Setup indexer
        indexer = RecordIndexer(search_client=None)
        indexer.count = 0
        indexer.record_to_index = lambda record: ('idx', 'doc')
        indexer._prepare_record = lambda record, index, doc_type, arguments: body.copy()
        return indexer, committed, called

    payload = {'id': 'rid'}
    indexer, committed, called = setup_indexer_and_env()

    if expect_error:
        with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
            indexer._index_action_sync_version(payload)
        assert called['error']
        assert called['trace']
        assert not committed['called']
    else:
        action = indexer._index_action_sync_version(payload)
        if has_content:
            assert action['_source']['content'][0]['file'] == expected_file
        else:
            assert action['_source']['file'] == expected_file
            assert 'content' not in action['_source']
        if expect_commit:
            assert committed['called']
        else:
            assert not committed['called']

def test__actionsiter_sync_version_exception(monkeypatch):
    """Test that reject and logger.error are called when an exception occurs in _actionsiter_sync_version."""
    indexer = RecordIndexer(search_client=None)
    # Raise exception in index side (could be _delete_action or _index_action_sync_version)
    def raise_exc(payload):
        raise Exception('test error')
    monkeypatch.setattr(indexer, '_index_action_sync_version', raise_exc)
    # Detect logger.error call
    called = {'error': False}
    monkeypatch.setattr('invenio_indexer.api.current_app', types.SimpleNamespace(
        logger=types.SimpleNamespace(error=lambda *a, **k: called.update({'error': True}))
    ))
    msg = DummyMessage({'op': 'index', 'id': 'rid'})
    # Execute
    result = list(indexer._actionsiter_sync_version([msg]))
    assert msg.rejected
    assert not msg.acked
    assert called['error']

def test__actionsiter_sync_version_noresultfound(monkeypatch):
    """Test that reject is called when NoResultFound occurs in _actionsiter_sync_version."""
    indexer = RecordIndexer(search_client=None)
    from sqlalchemy.orm.exc import NoResultFound
    # Make Record.get_record raise NoResultFound
    monkeypatch.setattr('invenio_indexer.api.Record', types.SimpleNamespace(get_record=lambda rid: (_ for _ in ()).throw(NoResultFound('not found'))))
    msg = DummyMessage({'op': 'index', 'id': 'rid'})
    list(indexer._actionsiter_sync_version([msg]))
    assert msg.rejected
    assert not msg.acked

def test__actionsiter_sync_version_delete(monkeypatch):
    """Test that _delete_action is called and acked when delete pattern in _actionsiter_sync_version."""
    indexer = RecordIndexer(search_client=None)
    called = {'delete': False}
    # Detect _delete_action call
    def dummy_delete_action(payload):
        called['delete'] = True
        return {'_op_type': 'delete'}
    monkeypatch.setattr(indexer, '_delete_action', dummy_delete_action)
    msg = DummyMessage({'op': 'delete', 'id': 'rid'})
    list(indexer._actionsiter_sync_version([msg]))
    assert called['delete']
    assert msg.acked
    assert not msg.rejected
