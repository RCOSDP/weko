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
from unittest.mock import call
from invenio_indexer.api import BulkRecordIndexer, RecordIndexer, BulkBaseException, BulkConnectionTimeout, BulkConnectionError, BulkException
from invenio_indexer.signals import before_record_index
from elasticsearch import ConnectionError, ConnectionTimeout
from elasticsearch.helpers import BulkIndexError
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


# .tox/c1/bin/pytest --cov=invenio_indexer tests/test_api.py::test_process_bulk_queue_errors -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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

# .tox/c1/bin/pytest --cov=invenio_indexer tests/test_api.py::test_process_bulk_queue -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_process_bulk_queue(app, queue):
    """Test process indexing."""
    with app.app_context():
        records = [Record.create({'title': f'test{i}'}, id_=str(uuid.uuid4())) for i in range(10)]
        db.session.commit()
        _values = [str(r.id) for r in records]
        es_bulk_kwargs = {"chunk_size": 500}
        # bulk処理でエラーが起きなかった
        RecordIndexer().bulk_index(_values)
        with patch('weko_deposit.utils.update_pdf_contents_es', lambda ids: None):
            with patch('invenio_indexer.api.RecordIndexer.reindex_bulk', return_value=(10, 0)):
                assert RecordIndexer().process_bulk_queue(es_bulk_kwargs=es_bulk_kwargs) == (10, 0)

            # BulkIndexError
            errors = [
                {"index": {"_id": str(records[4].id), "error": {"type": "version_conflict"}}},
                {"index": {"_id": str(records[5].id), "error": {"type": "version_conflict"}}}
            ]
            app.config['SEARCH_UI_SEARCH_INDEX'] = 'test-index'
            def mock_reindex_bulk_be(self, client, actions, **kwargs):
                self.count = 10
                raise DummyBulkIndexError(errors)

            with patch('invenio_indexer.api.RecordIndexer.reindex_bulk', new=mock_reindex_bulk_be):
                with patch('invenio_indexer.api.RecordIndexer._actionsiter', return_value=[{}]*10):
                    indexer = RecordIndexer()
                    result = indexer.process_bulk_queue(es_bulk_kwargs=es_bulk_kwargs)
                    assert result[0] == 8  # success数
                    assert result[1] == 2  # fail数
                    assert errors[0]['index']['error']['type'] == "version_conflict"

            # ConnectionError
            errors = [
                {"index": {"_id": str(records[9].id), "error": {"type": "ConnectionError"}}}
            ]
            es_conn_error = ConnectionError("ConnectionError!", {}, {})
            with patch('invenio_indexer.api.RecordIndexer.reindex_bulk', side_effect=DummyBulkConnectionError(success=8, failed=1, errors=errors, original_exception=es_conn_error)):
                with patch('invenio_indexer.api.RecordIndexer._actionsiter', return_value=[{}]*10):
                    indexer = RecordIndexer()
                    result = indexer.process_bulk_queue(es_bulk_kwargs=es_bulk_kwargs)
                    assert result[1] == 1  # fail数
                    assert errors[0]['index']['error']['type'] == 'ConnectionError'

            # ConnectionTimeout
            errors = [
                {"index": {"_id": str(records[9].id), "error": {"type": "ConnectionTimeout"}}}
            ]
            es_conn_error = ConnectionTimeout("ConnectionTimeout!", {}, {})
            def mock_reindex_bulk_ct(client, actions, **kwargs):
                indexer.latest_item_id = 9
                raise DummyBulkConnectionTimeout(success=8, failed=1, errors=errors, original_exception=es_conn_error)
            with patch('invenio_indexer.api.RecordIndexer.reindex_bulk', side_effect=mock_reindex_bulk_ct):
                with patch('invenio_indexer.api.RecordIndexer._actionsiter', return_value=[{}]*10):
                    indexer = RecordIndexer()
                    result = indexer.process_bulk_queue(es_bulk_kwargs=es_bulk_kwargs)
                    assert result[1] == 1
                    assert errors[0]['index']['error']['type'] == 'ConnectionTimeout'

            # Exception
            errors = [
                {"index": {"_id": str(records[9].id), "error": {"type": "Exception"}}}
            ]
            es_conn_error = Exception("Exception!", {}, {})
            def mock_reindex_bulk_ct(client, actions, **kwargs):
                indexer.latest_item_id = 9
                raise DummyBulkException(success=8, failed=1, errors=errors, original_exception=es_conn_error)
            with patch('invenio_indexer.api.RecordIndexer.reindex_bulk', side_effect=mock_reindex_bulk_ct):
                with patch('invenio_indexer.api.RecordIndexer._actionsiter', return_value=[{}]*10):
                    indexer = RecordIndexer()
                    result = indexer.process_bulk_queue(es_bulk_kwargs=es_bulk_kwargs)
                    assert result[1] == 1  # fail数
                    assert errors[0]['index']['error']['type'] == 'Exception'

            # BulkIndexError (when errors is an empty list)
            errors = []
            app.config['SEARCH_UI_SEARCH_INDEX'] = 'test-index'
            def mock_reindex_bulk_be_empty(self, client, actions, **kwargs):
                self.count = 10
                raise DummyBulkIndexError(errors)

            with patch('invenio_indexer.api.RecordIndexer.reindex_bulk', new=mock_reindex_bulk_be_empty):
                with patch('invenio_indexer.api.RecordIndexer._actionsiter', return_value=[{}]*10):
                    indexer = RecordIndexer()
                    result = indexer.process_bulk_queue(es_bulk_kwargs=es_bulk_kwargs)
                assert result[0] == 10  # Number of successes (all considered successful)
                assert result[1] == 0   # Number of failures
                assert errors == []

            #BulkIndexError (err_info is string)
            errors = [{"index": {"_id": "dummy", "error": "Some string error"}}]
            def mock_reindex_bulk_be_str(self, client, actions, **kwargs):
                self.count = 10
                raise DummyBulkIndexError(errors)
            with patch('invenio_indexer.api.RecordIndexer.reindex_bulk', new=mock_reindex_bulk_be_str):
                with patch('invenio_indexer.api.RecordIndexer._actionsiter', return_value=[{}]*10):
                    indexer = RecordIndexer()
                    result = indexer.process_bulk_queue(es_bulk_kwargs=es_bulk_kwargs)
                assert result[0] == 9  # Number of successes
                assert result[1] == 1   # Number of failures
                assert errors[0]['index']['error'] == "Some string error"

            # ConnectionError (when errors is an empty list)
            errors = []
            es_conn_error = ConnectionError("ConnectionError!", {}, {})
            with patch('invenio_indexer.api.RecordIndexer.reindex_bulk', side_effect=DummyBulkConnectionError(success=10, failed=0, errors=errors, original_exception=es_conn_error)):
                with patch('invenio_indexer.api.RecordIndexer._actionsiter', return_value=[{}]*10):
                    indexer = RecordIndexer()
                    result = indexer.process_bulk_queue(es_bulk_kwargs=es_bulk_kwargs)
                    assert result[0] == 10  # Number of successes
                    assert result[1] == 0   # Number of failures
                    assert errors == []

            # ConnectionTimeout (when errors is an empty list)
            errors = []
            es_conn_error = ConnectionTimeout("ConnectionTimeout!", {}, {})
            def mock_reindex_bulk_ct_empty(client, actions, **kwargs):
                indexer.latest_item_id = 9
                raise DummyBulkConnectionTimeout(success=10, failed=0, errors=errors, original_exception=es_conn_error)
            with patch('invenio_indexer.api.RecordIndexer.reindex_bulk', side_effect=mock_reindex_bulk_ct_empty):
                with patch('invenio_indexer.api.RecordIndexer._actionsiter', return_value=[{}]*10):
                    indexer = RecordIndexer()
                    result = indexer.process_bulk_queue(es_bulk_kwargs=es_bulk_kwargs)
                    assert result[0] == 10  # Number of successes
                    assert result[1] == 0   # Number of failures
                    assert errors == []

            # Exception (when errors is an empty list)
            errors = []
            es_conn_error = Exception("Exception!", {}, {})
            def mock_reindex_bulk_exception_empty(client, actions, **kwargs):
                indexer.latest_item_id = 9
                raise DummyBulkException(success=10, failed=0, errors=errors, original_exception=es_conn_error)
            with patch('invenio_indexer.api.RecordIndexer.reindex_bulk', side_effect=mock_reindex_bulk_exception_empty):
                with patch('invenio_indexer.api.RecordIndexer._actionsiter', return_value=[{}]*10):
                    indexer = RecordIndexer()
                    result = indexer.process_bulk_queue(es_bulk_kwargs=es_bulk_kwargs)
                    assert result[0] == 10  # Number of successes
                    assert result[1] == 0   # Number of failures
                    assert errors == []

            # BulkException (err_info is string)
            errors = [{"index": {"_id": "dummy", "error": "Some string error"}}]
            def mock_reindex_bulk_exception_str(self, client, actions, **kwargs):
                self.count = 10
                raise DummyBulkException(success=0, failed=1, errors=errors, original_exception=Exception("Exception!", {}, {}))
            with patch('invenio_indexer.api.RecordIndexer.reindex_bulk', new=mock_reindex_bulk_exception_str):
                with patch('invenio_indexer.api.RecordIndexer._actionsiter', return_value=[{}]*10):
                    indexer = RecordIndexer()
                    result = indexer.process_bulk_queue(es_bulk_kwargs=es_bulk_kwargs)
                assert result[0] == 0  # Number of successes
                assert result[1] == 1   # Number of failures
                assert errors[0]['index']['error'] == "Some string error"


def test_process_bulk_queue_for_error_loop(app):
    with app.app_context():
        indexer = RecordIndexer()
        es_bulk_kwargs = {"chunk_size": 500}

        # Mock for reindex_bulk: _fail is a list
        def mock_reindex_bulk(*args, **kwargs):
            _success = 2
            _fail = [
                {"index": {"_id": "id1", "error": {"type": "ConnectionError"}}},
                {"index": {"_id": "id2", "error": {"type": "Timeout"}}}
            ]
            return _success, _fail

        with patch('invenio_indexer.api.RecordIndexer.reindex_bulk', side_effect=mock_reindex_bulk), \
             patch('invenio_indexer.api.RecordIndexer._actionsiter', return_value=[{}]*4), \
             patch('weko_deposit.utils.update_pdf_contents_es', lambda ids: None), \
             patch('click.secho') as mock_secho:
            result = indexer.process_bulk_queue(es_bulk_kwargs=es_bulk_kwargs)
            assert result[0] == 2
            assert result[1] == 2
            # click.secho should be called twice in the for error in _fail: loop
            assert any("id1" in str(c) and "ConnectionError" in str(c) for c in mock_secho.call_args_list)
            assert any("id2" in str(c) and "Timeout" in str(c) for c in mock_secho.call_args_list)

class DummyBulkIndexError(BulkIndexError):
    def __init__(self, errors):
        super().__init__(errors)
    @property
    def errors(self):
        return self.args[0]

class DummyBulkConnectionTimeout(BulkConnectionTimeout):
    def __init__(self, success, failed, errors, original_exception):
        super().__init__(success, failed, errors, original_exception)
        self.success = success
        self.failed = failed
        self.errors = errors
        self.original_exception = original_exception

class DummyBulkConnectionError(BulkConnectionError):
    def __init__(self, success, failed, errors, original_exception):
        super().__init__(success, failed, errors, original_exception)
        self.success = success
        self.failed = failed
        self.errors = errors
        self.original_exception = original_exception

class DummyBulkException(BulkException):
    def __init__(self, success, failed, errors, original_exception):
        super().__init__(success, failed, errors, original_exception)
        self.success = success
        self.failed = failed
        self.errors = errors
        self.original_exception = original_exception

# .tox/c1/bin/pytest --cov=invenio_indexer tests/test_api.py::test_reindex_bulk -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_reindex_bulk():
    def dummy_streaming_bulk_success(*args, **kwargs):
        for i in range(10):
            yield True, {'index': {'_id': f'id{i}'}}

    def dummy_streaming_bulk_fail(*args, **kwargs):
        # 2件失敗
        for i in range(10):
            if i == 3 or i == 7:
                yield False, {'index': {'_id': f'id{i}'}}
            else:
                yield True, {'index': {'_id': f'id{i}'}}

    indexer = RecordIndexer()
    indexer.target_chunks = 5
    client = MagicMock()
    actions = [{}] * 10
    with patch('invenio_indexer.api.streaming_bulk', dummy_streaming_bulk_success):
        result = indexer.reindex_bulk(client, actions, stats_only=True, chunk_size=500, ignore_status=[400])
    assert result[0] == 10
    assert result[1] == 0

    actions = [{}] * 10
    with patch('invenio_indexer.api.streaming_bulk', dummy_streaming_bulk_success):
        result = indexer.reindex_bulk(client, actions, stats_only=False, chunk_size=500, span_name='test')
    assert result[0] == 10
    assert isinstance(result[1], list)
    assert len(result[1]) == 0

    actions = [{}] * 10
    with patch('invenio_indexer.api.streaming_bulk', dummy_streaming_bulk_fail):
        result = indexer.reindex_bulk(client, actions, stats_only=True, chunk_size=500)
    assert result[0] == 8
    assert result[1] == 2

    actions = [{}] * 10
    with patch('invenio_indexer.api.streaming_bulk', dummy_streaming_bulk_fail):
        result = indexer.reindex_bulk(client, actions, stats_only=False, chunk_size=500)
    assert result[0] == 8
    assert isinstance(result[1], list)
    assert len(result[1]) == 2

    actions = [{}] * 10
    def streaming_bulk_version_conflict(*args, **kwargs):
        for i in range(10):
            if i == 3 or i == 5:
                yield False, {'index': {'_id': f'id{i}', 'errors': {'type': 'version_conflict'}}}
            else:
                yield True, {'index': {'_id': f'id{i}'}}
        raise BulkIndexError([
            {'index': {'_id': 'id3', 'errors': {'type': 'version_conflict'}}},
            {'index': {'_id': 'id5', 'errors': {'type': 'version_conflict'}}}
        ])

    with patch('invenio_indexer.api.streaming_bulk', streaming_bulk_version_conflict):

        with pytest.raises(BulkIndexError) as be:
            indexer.reindex_bulk(client, actions, stats_only=True, chunk_size=500)
        errors = be.value.args[0]
        assert len(errors) == 2

    with patch('invenio_indexer.api.streaming_bulk', streaming_bulk_version_conflict):
        with pytest.raises(BulkIndexError) as be:
            indexer.reindex_bulk(client, actions, stats_only=False, chunk_size=500)
        errors = be.value.args[0]
        assert len(errors) == 2

    actions = [{}] * 10
    def streaming_bulk_cte_error(*args, **kwargs):
        for i in range(10):
            if i == 5:
                raise ConnectionTimeout("streaming_bulk error", {}, {})
            yield True, {'index': {'_id': f'id{i}'}}

    with patch('invenio_indexer.api.streaming_bulk', streaming_bulk_cte_error):
        with pytest.raises(BulkConnectionTimeout) as cte:
            indexer.reindex_bulk(client, actions, stats_only=True, chunk_size=500)
        assert cte.value.success == 5

    with patch('invenio_indexer.api.streaming_bulk', streaming_bulk_cte_error):
        with pytest.raises(BulkConnectionTimeout) as cte:
            indexer.reindex_bulk(client, actions, stats_only=False, chunk_size=500)
        assert cte.value.success == 5


    actions = [{}] * 10
    def streaming_bulk_ce_error(*args, **kwargs):
        for i in range(10):
            if i == 2:
                raise ConnectionError("streaming_bulk error", {}, {})
            yield True, {'index': {'_id': f'id{i}'}}

    with patch('invenio_indexer.api.streaming_bulk', streaming_bulk_ce_error):
        with pytest.raises(BulkConnectionError) as ce:
            indexer.reindex_bulk(client, actions, stats_only=True, chunk_size=500)
        assert ce.value.success == 2

    with patch('invenio_indexer.api.streaming_bulk', streaming_bulk_ce_error):
        with pytest.raises(BulkConnectionError) as ce:
            indexer.reindex_bulk(client, actions, stats_only=False, chunk_size=500)
        assert ce.value.success == 2

    actions = [{}] * 10
    def streaming_bulk_error(*args, **kwargs):
        for i in range(10):
            if i == 7:
                raise Exception("streaming_bulk error", {}, {})
            yield True, {'index': {'_id': f'id{i}'}}

    with patch('invenio_indexer.api.streaming_bulk', streaming_bulk_error):
        with pytest.raises(Exception) as e:
            indexer.reindex_bulk(client, actions, stats_only=True, chunk_size=500)
        assert e.value.success == 7

    with patch('invenio_indexer.api.streaming_bulk', streaming_bulk_error):
        with pytest.raises(Exception) as e:
            indexer.reindex_bulk(client, actions, stats_only=False, chunk_size=500)
        assert e.value.success == 7

def test_reindex_bulk_chunk_logging():
    # Dummy for streaming_bulk: Assumes chunk logs are output every 2 items
    def dummy_streaming_bulk(*args, **kwargs):
        for i in range(4):
            if i % 2 == 0:
                yield True, {'index': {'_id': f'id{i}'}}
            else:
                yield False, {'index': {'_id': f'id{i}'}}

    indexer = RecordIndexer()
    indexer.target_chunks = 2  # Set chunk size to 2
    client = MagicMock()
    actions = [{}] * 4

    with patch('invenio_indexer.api.streaming_bulk', dummy_streaming_bulk), \
         patch('click.secho') as mock_secho:
        result = indexer.reindex_bulk(client, actions, stats_only=True, chunk_size=2)

    assert mock_secho.call_count == 4
    first_chunk = [
        call(f"[", fg='green'),  # Success
        call(f"[", fg='red'),    # Fail
    ]
    second_chunk = [
        call(f"[", fg='green'),
        call(f"[", fg='red'),
    ]
    calls = mock_secho.call_args_list
    assert any("ID: id0, Status: Success, Chunk: 1/2" in str(c) and "fg='green'" in str(c) for c in calls)
    assert any("ID: id1, Status: Fail, Chunk: 1/2" in str(c) and "fg='red'" in str(c) for c in calls)
    assert any("ID: id2, Status: Success, Chunk: 2/2" in str(c) and "fg='green'" in str(c) for c in calls)
    assert any("ID: id3, Status: Fail, Chunk: 2/2" in str(c) and "fg='red'" in str(c) for c in calls)
    assert result[0] == 2  # Number of successes
    assert result[1] == 2  # Number of failures

def test_process_bulk_queue_brokerurl_parse_fail(monkeypatch):
    """Test process_bulk_queue when BROKER_URL does not match regex (default host/port used)."""
    from invenio_indexer.api import RecordIndexer
    app = types.SimpleNamespace(
        config={
            'BROKER_URL': 'invalid_url',  # Will not match regex, so default host/port used
            'INDEXER_MQ_ROUTING_KEY': 'indexer',
            'INDEXER_MQ_QUEUE': types.SimpleNamespace(name='indexer'),
            'INDEXER_MQ_EXCHANGE': types.SimpleNamespace(name='indexer'),
            'INDEXER_BULK_REQUEST_TIMEOUT': 10,
            'INDEXER_MAX_BODY_SIZE': 10000
        },
        logger=types.SimpleNamespace(debug=lambda *a, **k: None, error=lambda *a, **k: None)
    )
    monkeypatch.setattr('invenio_indexer.api.current_app', app)
    # socket.create_connection always raises
    import socket
    monkeypatch.setattr('socket.create_connection', lambda *a, **k: (_ for _ in ()).throw(Exception('fail')))
    # click.secho mock
    monkeypatch.setattr('invenio_indexer.api.click', types.SimpleNamespace(secho=lambda *a, **k: None))
    indexer = RecordIndexer(search_client=None)
    result = indexer.process_bulk_queue(es_bulk_kwargs={"chunk_size": 1})
    assert result == (0, 0, 0)
    """Test process_bulk_queue returns (0,0,0) if RabbitMQ connection fails."""
    from invenio_indexer.api import RecordIndexer
    app = types.SimpleNamespace(
        config={
            'BROKER_URL': 'amqp://guest:guest@rabbitmq:5672/',
            'INDEXER_MQ_ROUTING_KEY': 'indexer',
            'INDEXER_MQ_QUEUE': types.SimpleNamespace(name='indexer'),
            'INDEXER_MQ_EXCHANGE': types.SimpleNamespace(name='indexer'),
            'INDEXER_BULK_REQUEST_TIMEOUT': 10,
            'INDEXER_MAX_BODY_SIZE': 10000
        },
        logger=types.SimpleNamespace(debug=lambda *a, **k: None, error=lambda *a, **k: None)
    )
    monkeypatch.setattr('invenio_indexer.api.current_app', app)
    # socket.create_connection always raises
    import socket
    monkeypatch.setattr('socket.create_connection', lambda *a, **k: (_ for _ in ()).throw(Exception('fail')))
    # click.secho mock
    monkeypatch.setattr('invenio_indexer.api.click', types.SimpleNamespace(secho=lambda *a, **k: None))
    indexer = RecordIndexer(search_client=None)
    result = indexer.process_bulk_queue(es_bulk_kwargs={"chunk_size": 1})
    assert result == (0, 0, 0)

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
        ({'foo': 'bar', 'content': [{'file': 'abc'}]}, 'abc', True, 5, 3, False, 1000, False)
    ]
)
def test__index_action_cases(monkeypatch, body, expected_file, has_content, version_id, es_version, expect_commit, max_body_size, expect_error):
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
    if has_content:
        result = indexer._index_action(payload)
        assert result['_source']['content'][0]['file'] == expected_file
    else:
        result = indexer._index_action(payload)
        assert result['_source']['file'] == expected_file
        assert 'content' not in result['_source']

def test__actionsiter_exception(monkeypatch):
    """Test that reject and logger.error are called when an exception occurs in _actionsiter."""
    indexer = RecordIndexer(search_client=None)
    # Raise exception in index side (could be _delete_action or _index_action)
    def raise_exc(payload):
        raise Exception('test error')
    monkeypatch.setattr(indexer, '_index_action', raise_exc)
    # Detect logger.error call
    called = {'error': False}
    monkeypatch.setattr('invenio_indexer.api.current_app', types.SimpleNamespace(
        logger=types.SimpleNamespace(error=lambda *a, **k: called.update({'error': True}))
    ))
    msg = DummyMessage({'op': 'index', 'id': 'rid'})
    # Execute
    result = list(indexer._actionsiter([msg]))
    assert msg.rejected is True
    assert msg.acked is False
    assert called['error'] is True

def test__actionsiter_noresultfound(monkeypatch):
    """Test that reject is called when NoResultFound occurs in _actionsiter."""
    indexer = RecordIndexer(search_client=None)
    from sqlalchemy.orm.exc import NoResultFound
    # Make Record.get_record raise NoResultFound
    monkeypatch.setattr('invenio_indexer.api.Record', types.SimpleNamespace(get_record=lambda rid: (_ for _ in ()).throw(NoResultFound('not found'))))
    msg = DummyMessage({'op': 'index', 'id': 'rid'})
    list(indexer._actionsiter([msg]))
    assert msg.rejected is True
    assert msg.acked is False

def test__actionsiter_delete(monkeypatch):
    """Test that _delete_action is called and acked when delete pattern in _actionsiter."""
    indexer = RecordIndexer(search_client=None)
    called = {'delete': False}
    # Detect _delete_action call
    def dummy_delete_action(payload):
        called['delete'] = True
        return {'_op_type': 'delete'}
    monkeypatch.setattr(indexer, '_delete_action', dummy_delete_action)
    msg = DummyMessage({'op': 'delete', 'id': 'rid'})
    list(indexer._actionsiter([msg]))
    assert called['delete'] is True
    assert msg.acked is True
    assert msg.rejected is False


def test__actionsiter_sqlalchemyerror(monkeypatch):
    """Test that rollback, logger.error, and reject are called on SQLAlchemyError in _actionsiter."""
    import sqlalchemy
    indexer = RecordIndexer(search_client=None)
    # Raise SQLAlchemyError in _index_action
    def raise_sqlalchemy(payload):
        raise sqlalchemy.exc.SQLAlchemyError('sqlalchemy error')
    monkeypatch.setattr(indexer, '_index_action', raise_sqlalchemy)
    # Detect rollback and logger.error call
    called = {'rollback': False, 'error': False}
    class DummySession:
        def rollback(self):
            called['rollback'] = True
    monkeypatch.setattr('invenio_indexer.api.db', types.SimpleNamespace(session=DummySession()))
    monkeypatch.setattr('invenio_indexer.api.current_app', types.SimpleNamespace(
        logger=types.SimpleNamespace(error=lambda *a, **k: called.update({'error': True}))
    ))
    msg = DummyMessage({'op': 'index', 'id': 'rid'})
    result = list(indexer._actionsiter([msg]))
    assert msg.rejected is True
    assert msg.acked is False
    assert called['rollback'] is True
    assert called['error'] is True

# .tox/c1/bin/pytest --cov=invenio_indexer tests/test_api.py::test_bulk_base_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_bulk_base_exception():
    exc = BulkBaseException(
        success=2,
        failed=1,
        errors=[{'error': 'test'}],
        original_exception=Exception("original error")
    )
    assert exc.success == 2
    assert exc.failed == 1
    assert exc.errors == [{'error': 'test'}]
    assert isinstance(exc.original_exception, Exception)
    assert str(exc) == "original error"
    with pytest.raises(BulkBaseException):
        raise exc

# .tox/c1/bin/pytest --cov=invenio_indexer tests/test_api.py::test_bulk_connection_timeout -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_bulk_connection_timeout():
    exc = BulkConnectionTimeout(success=1, failed=2, errors=[{'error': 'timeout'}], original_exception=Exception("timeout"))
    assert exc.success == 1
    assert exc.failed == 2
    assert exc.errors == [{'error': 'timeout'}]
    assert isinstance(exc.original_exception, Exception)
    with pytest.raises(BulkConnectionTimeout):
        raise exc

# .tox/c1/bin/pytest --cov=invenio_indexer tests/test_api.py::test_bulk_connection_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_bulk_connection_error():
    exc = BulkConnectionError(success=3, failed=4, errors=[{'error': 'conn'}], original_exception=Exception("conn"))
    assert exc.success == 3
    assert exc.failed == 4
    assert exc.errors == [{'error': 'conn'}]
    assert isinstance(exc.original_exception, Exception)
    with pytest.raises(BulkConnectionError):
        raise exc

# .tox/c1/bin/pytest --cov=invenio_indexer tests/test_api.py::test_bulk_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_bulk_exception():
    exc = BulkException(success=5, failed=6, errors=[{'error': 'other'}], original_exception=Exception("other"))
    assert exc.success == 5
    assert exc.failed == 6
    assert exc.errors == [{'error': 'other'}]
    assert isinstance(exc.original_exception, Exception)
    with pytest.raises(BulkException):
        raise exc
