# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""API for indexing of records."""

from __future__ import absolute_import, print_function

import copy
import traceback
from contextlib import contextmanager
import click
import json
import pytz
from celery import current_app as current_celery_app
from invenio_db import db
from sqlalchemy.exc import SQLAlchemyError
from elasticsearch.helpers import bulk, streaming_bulk
from flask import current_app
from invenio_records.api import Record
from invenio_search import current_search_client
from kombu import Producer as KombuProducer
from kombu.compat import Consumer
from sqlalchemy.orm.exc import NoResultFound
from elasticsearch.helpers import BulkIndexError
from elasticsearch.exceptions import ConnectionTimeout,ConnectionError
import datetime
import math

from .proxies import current_record_to_index
from .signals import before_record_index


class Producer(KombuProducer):
    """Producer validating published messages.

    For more information visit :class:`kombu:kombu.Producer`.
    """

    def publish(self, data, **kwargs):
        """Validate operation type."""
        assert data.get('op') in {'index', 'create', 'delete', 'update'}
        return super(Producer, self).publish(data, **kwargs)


class RecordIndexer(object):
    r"""Provide an interface for indexing records in Elasticsearch.

    Bulk indexing works by queuing requests for indexing records and processing
    these requests in bulk.
    """

    def __init__(self, search_client=None, exchange=None, queue=None,
                 routing_key=None, version_type=None, record_to_index=None):
        """Initialize indexer.

        :param search_client: Elasticsearch client.
            (Default: ``current_search_client``)
        :param exchange: A :class:`kombu.Exchange` instance for message queue.
        :param queue: A :class:`kombu.Queue` instance for message queue.
        :param routing_key: Routing key for message queue.
        :param version_type: Elasticsearch version type.
            (Default: ``external_gte``)
        :param record_to_index: Function to extract the index and doc_type
            from the record.
        """
        self.client = search_client or current_search_client
        self._exchange = exchange
        self._queue = queue
        self._record_to_index = record_to_index or current_record_to_index
        self._routing_key = routing_key
        self._version_type = version_type or 'external_gte'

    def record_to_index(self, record):
        """Get index/doc_type given a record.

        :param record: The record where to look for the information.
        :returns: A tuple (index, doc_type).
        """
        return self._record_to_index(record)

    @property
    def mq_queue(self):
        """Message Queue queue.

        :returns: The Message Queue queue.
        """
        return self._queue or current_app.config['INDEXER_MQ_QUEUE']

    @property
    def mq_exchange(self):
        """Message Queue exchange.

        :returns: The Message Queue exchange.
        """
        return self._exchange or current_app.config['INDEXER_MQ_EXCHANGE']

    @property
    def mq_routing_key(self):
        """Message Queue routing key.

        :returns: The Message Queue routing key.
        """
        return (self._routing_key or
                current_app.config['INDEXER_MQ_ROUTING_KEY'])

    #
    # High-level API
    #
    def index(self, record, arguments=None, **kwargs):
        """Index a record.

        The caller is responsible for ensuring that the record has already been
        committed to the database. If a newer version of a record has already
        been indexed then the provided record will not be indexed. This
        behavior can be controlled by providing a different ``version_type``
        when initializing ``RecordIndexer``.

        :param record: Record instance.
        """
        index, doc_type = self.record_to_index(record)
        arguments = arguments or {}
        body = self._prepare_record(
            record, index, doc_type, arguments, **kwargs)

        return self.client.index(
            id=str(record.id),
            version=record.revision_id,
            version_type=self._version_type,
            index=index,
            doc_type=doc_type,
            body=body,
            **arguments
        )

    def index_by_id(self, record_uuid, **kwargs):
        """Index a record by record identifier.

        :param record_uuid: Record identifier.
        :param kwargs: Passed to :meth:`RecordIndexer.index`.
        """
        return self.index(Record.get_record(record_uuid), **kwargs)

    def delete(self, record, **kwargs):
        """Delete a record.

        :param record: Record instance.
        :param kwargs: Passed to
            :meth:`elasticsearch:elasticsearch.Elasticsearch.delete`.
        """
        index, doc_type = self.record_to_index(record)

        return self.client.delete(
            id=str(record.id),
            index=index,
            doc_type=doc_type,
            **kwargs
        )

    def delete_by_id(self, record_uuid, **kwargs):
        """Delete record from index by record identifier.

        :param record_uuid: Record identifier.
        :param kwargs: Passed to :meth:`RecordIndexer.delete`.
        """
        self.delete(Record.get_record(record_uuid), **kwargs)

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, 'index')

    def bulk_delete(self, record_id_iterator):
        """Bulk delete records from index.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, 'delete')

    def process_bulk_queue(self, es_bulk_kwargs=None,with_deleted=False):
        """Process bulk indexing queue.

        :param dict es_bulk_kwargs: Passed to
            :func:`elasticsearch:elasticsearch.helpers.bulk`.
        """
        from weko_deposit.utils import update_pdf_contents_es
        success = 0
        fail = 0
        self.count = 0
        count = (success,fail)
        req_timeout = current_app.config['INDEXER_BULK_REQUEST_TIMEOUT']
        while True:
            with current_celery_app.pool.acquire(block=True) as conn:
                # check
                b4_queues_cnt = 0
                with conn.channel() as chan:
                    name, b4_queues_cnt, consumers = chan.queue_declare(queue=current_app.config['INDEXER_MQ_ROUTING_KEY'], passive=True)
                    current_app.logger.debug("name:{}, queues:{}, consumers:{}".format(name, b4_queues_cnt, consumers))
                    if b4_queues_cnt == 0:
                        break
                consumer = Consumer(
                    connection=conn,
                    queue=self.mq_queue.name,
                    exchange=self.mq_exchange.name,
                    routing_key=self.mq_routing_key,
                )
                es_bulk_kwargs = es_bulk_kwargs or {}
                with consumer:
                    try:
                        messages = list(consumer.iterqueue())
                        ids = [message.decode().get("id") for message in messages]
                        _success,_fail  = bulk(
                            self.client,
                            self._actionsiter(messages,with_deleted=with_deleted),
                            stats_only=True,
                            request_timeout=req_timeout,
                            # raise_on_error=True,
                            # raise_on_exception=True,
                            **es_bulk_kwargs
                        )
                        update_pdf_contents_es(ids)
                        success = success + _success
                        fail = fail + _fail
                    except BulkIndexError as be:
                        with conn.channel() as chan:
                            name, af_queues_cnt, consumers = chan.queue_declare(queue=current_app.config['INDEXER_MQ_ROUTING_KEY'], passive=True)
                            current_app.logger.debug("name:{}, queues:{}, consumers:{}".format(name, af_queues_cnt, consumers))
                            success = success + (b4_queues_cnt-af_queues_cnt-len(be.errors))
                        error_ids = []
                        for error in be.errors:
                            error_ids.append(error['index']['_id'])
                        try:
                            _success,_fail = bulk(
                                self.client,
                                self._actionsiter2(error_ids,with_deleted=with_deleted),
                                stats_only=True,
                                request_timeout=req_timeout,
                                #raise_on_error=False,
                                # raise_on_exception=True,
                                **es_bulk_kwargs
                            )
                            update_pdf_contents_es(error_ids)
                            success = success + _success
                            fail = fail + _fail
                        except BulkIndexError as be2:
                            success_retrys = list(set(error_ids)-set([error['index']['_id'] for error in be2.errors]))
                            update_pdf_contents_es(success_retrys)
                            success = success + (len(error_ids)-len(be2.errors))
                            fail = fail + len(be2.errors)
                            for error in be2.errors:
                                click.secho("{}, {}".format(error['index']['_id'],error['index']['error']['type']),fg='red')
                    except ConnectionError as ce:
                        with conn.channel() as chan:
                            name, af_queues_cnt, consumers = chan.queue_declare(queue=current_app.config['INDEXER_MQ_ROUTING_KEY'], passive=True)
                            current_app.logger.debug("name:{}, queues:{}, consumers:{}".format(name, af_queues_cnt, consumers))
                            success = success + (b4_queues_cnt-af_queues_cnt-self.count)
                        error_ids = []
                        error_ids.append(self.latest_item_id)
                        _success,_fail = bulk(
                                self.client,
                                self._actionsiter2(error_ids),
                                stats_only=True,
                                request_timeout=req_timeout,
                                #raise_on_error=False,
                                # raise_on_exception=True,
                                **es_bulk_kwargs
                        )
                        update_pdf_contents_es(error_ids)
                        success = success + _success
                        fail = fail + _fail
                    except ConnectionTimeout as ce:
                        click.secho("Error: {}".format(ce),fg='red')
                        click.secho("INDEXER_BULK_REQUEST_TIMEOUT: {} sec".format(req_timeout),fg='red')
                        click.secho("Please change value of INDEXER_BULK_REQUEST_TIMEOUT and retry it.",fg='red')
                        click.secho("processing: {}".format(self.count),fg='red')
                        click.secho("latest processing id: {}".format(self.latest_item_id),fg='red')
                        break
                    except Exception as e:
                        current_app.logger.error(e)
                        current_app.logger.error(traceback.format_exc())
                        break

        count = (success,fail)
        click.secho("count(success, error): {}".format(count),fg='green')
        return count

    def process_bulk_queue_reindex(self, es_bulk_kwargs=None, with_deleted=False):
        """
        Process bulk indexing queue.

        Args:
            es_bulk_kwargs (dict, optional): Additional keyword arguments passed to
                elasticsearch.helpers.bulk. Defaults to None.
            with_deleted (bool, optional): If True, include deleted records in the indexing process. Defaults to False.

        Returns:
            tuple: (success, fail) if all processed, or (success, fail, unprocessed) if some remain.

        Raises:
            BulkIndexError: If a bulk indexing error occurs.
            BulkConnectionError: If a connection error occurs during bulk indexing.
            BulkConnectionTimeout: If a connection timeout occurs during bulk indexing.
            BulkException: For other exceptions during bulk indexing.
        """
        from weko_deposit.utils import update_pdf_contents_es_with_index_api # avoid circular import
        import socket
        import re
        broker_url = current_app.config.get('BROKER_URL')
        # Extract host and port from BROKER_URL, fallback to default if not found
        m = re.match(r'.*://.*@(.*):(\d+)', broker_url)
        if m:
            rabbit_host = m.group(1)
            rabbit_port = int(m.group(2))
        else:
            rabbit_host = 'rabbitmq'
            rabbit_port = 5672
        try:
            with socket.create_connection((rabbit_host, rabbit_port), timeout=3):
                rabbitmq_conn = True
        except Exception as e:
            rabbitmq_conn = False
        # Check RabbitMQ connectivity before proceeding
        if not rabbitmq_conn:
            click.secho(f"Cannot connect to RabbitMQ({rabbit_host}:{rabbit_port}) (socket connection failed)", fg='red')
            return (0, 0, 0)

        success = 0
        fail = 0
        unprocessed = 0
        self.count = 0
        self.success_ids = []
        self.target_chunks = 0
        messages_count = 0
        count = (success,fail)
        req_timeout = current_app.config['INDEXER_BULK_REQUEST_TIMEOUT']
        with current_celery_app.pool.acquire(block=True) as conn:
            # check
            b4_queues_cnt = 0
            with conn.channel() as chan:
                name, b4_queues_cnt, consumers = chan.queue_declare(queue=current_app.config['INDEXER_MQ_ROUTING_KEY'], passive=True)
                current_app.logger.debug("name:{}, queues:{}, consumers:{}".format(name, b4_queues_cnt, consumers))
            consumer = Consumer(
                connection=conn,
                queue=self.mq_queue.name,
                exchange=self.mq_exchange.name,
                routing_key=self.mq_routing_key,
            )
            es_bulk_kwargs = es_bulk_kwargs or {}
            with consumer:
                try:
                    messages = list(consumer.iterqueue())
                    messages_count = len(messages)
                    self.target_chunks = math.ceil(messages_count / es_bulk_kwargs["chunk_size"])
                    click.secho("messages count:{}, target chunks:{}".format(messages_count, self.target_chunks),fg='green')
                    _success,_fail  = self.reindex_bulk(
                        self.client,
                        self._actionsiter_sync_version(messages),
                        request_timeout=req_timeout,
                        # raise_on_error=True,
                        # raise_on_exception=True,
                        **es_bulk_kwargs
                    )
                    update_pdf_contents_es_with_index_api(self.success_ids)
                    success = _success
                    if isinstance(_fail, list):
                        fail = len(_fail)
                        for error in _fail:
                            click.secho("{}, {}".format(error['index']['_id'],error['index']['error']['type']),fg='red')
                    else:
                        fail = _fail
                    unprocessed = messages_count - (success + fail) if messages_count > (success + fail) else 0
                except BulkIndexError as be:
                    with conn.channel() as chan:
                        name, af_queues_cnt, consumers = chan.queue_declare(queue=current_app.config['INDEXER_MQ_ROUTING_KEY'], passive=True)
                        current_app.logger.debug("name:{}, queues:{}, consumers:{}".format(name, af_queues_cnt, consumers))
                    fail = len(be.errors)
                    success = self.count - fail
                    unprocessed = messages_count - self.count
                    update_pdf_contents_es_with_index_api(self.success_ids)
                    for error in be.errors:
                        err = error['index']
                        err_info = err.get('error')
                        if isinstance(err_info, dict):
                            error_type = err_info.get('type', 'unknown')
                        else:
                            error_type = str(err_info)
                        click.secho("{}, {}".format(err.get('_id', ''), error_type), fg='red')
                except (BulkConnectionTimeout, ConnectionTimeout) as ce:
                    click.secho("Error: {}".format(ce.errors),fg='red')
                    click.secho("INDEXER_BULK_REQUEST_TIMEOUT: {} sec".format(req_timeout),fg='red')
                    click.secho("Please change value of INDEXER_BULK_REQUEST_TIMEOUT and retry it.",fg='red')
                    click.secho("processing: {}".format(self.count),fg='red')
                    click.secho("latest processing id: {}".format(self.latest_item_id),fg='red')
                    if '_success' in locals() or '_fail' in locals():
                        success = _success
                        fail = _fail
                        errors = []
                        if isinstance(fail, list):
                            errors = fail
                    else:
                        success = ce.success if hasattr(ce, 'success') else 0
                        fail = ce.failed if hasattr(ce, 'failed') else 0
                        errors = ce.errors if hasattr(ce, 'errors') else []
                    if len(errors) > 0:
                        for error in errors:
                            click.secho("{}, {}".format(error['index']['_id'],error['index']['error']['type']),fg='red')
                        fail = len(errors)
                    unprocessed = messages_count - (success + fail) if messages_count > (success + fail) else 0
                    update_pdf_contents_es_with_index_api(self.success_ids)
                except (BulkConnectionError, ConnectionError) as ce:
                    with conn.channel() as chan:
                        name, af_queues_cnt, consumers = chan.queue_declare(queue=current_app.config['INDEXER_MQ_ROUTING_KEY'], passive=True)
                        current_app.logger.debug("name:{}, queues:{}, consumers:{}".format(name, af_queues_cnt, consumers))
                        if '_success' in locals() or '_fail' in locals():
                            success = _success
                            fail = _fail
                            errors = []
                            if isinstance(fail, list):
                                errors = fail
                        else:
                            success = ce.success if hasattr(ce, 'success') else 0
                            fail = ce.failed if hasattr(ce, 'failed') else 0
                            errors = ce.errors if hasattr(ce, 'errors') else []
                        if len(errors) > 0:
                            for error in errors:
                                click.secho("{}, {}".format(error['index']['_id'],error['index']['error']['type']),fg='red')
                            fail = len(errors)
                        unprocessed = messages_count - (success + fail) if messages_count > (success + fail) else 0
                        update_pdf_contents_es_with_index_api(self.success_ids)
                except (BulkException, Exception) as e:
                    current_app.logger.error(e)
                    current_app.logger.error(traceback.format_exc())
                    if '_success'  in locals() or '_fail' in locals():
                        success = _success
                        fail = _fail
                        errors = []
                        if isinstance(fail, list):
                            errors = fail
                    else:
                        success = e.success if hasattr(e, 'success') else 0
                        fail = e.failed if hasattr(e, 'failed') else 0
                        errors = e.errors if hasattr(e, 'errors') else []
                    if len(errors) > 0:
                        for error in errors:
                            err = error['index']
                            err_info = err.get('error')
                            if isinstance(err_info, dict):
                                error_type = err_info.get('type', 'unknown')
                            else:
                                error_type = str(err_info)
                            click.secho("{}, {}".format(err.get('_id', ''), error_type), fg='red')
                        fail = len(errors)
                    unprocessed = messages_count - (success + fail) if messages_count > (success + fail) else 0
                    update_pdf_contents_es_with_index_api(self.success_ids)
        if unprocessed == 0:
            count = (success,fail)
            click.secho("count(success, error): {}".format(count),fg='green')
        else:
            count = (success,fail,unprocessed)
            click.secho("count(success, error, unprocessed): {}".format(count),fg='green')
        return count

    @contextmanager
    def create_producer(self):
        """Context manager that yields an instance of ``Producer``."""
        with current_celery_app.pool.acquire(block=True) as conn:
            yield Producer(
                conn,
                exchange=self.mq_exchange,
                routing_key=self.mq_routing_key,
                auto_declare=True,
            )

    #
    # Low-level implementation
    #
    def _bulk_op(self, record_id_iterator, op_type, index=None, doc_type=None):
        """Index record in Elasticsearch asynchronously.

        :param record_id_iterator: Iterator that yields record UUIDs.
        :param op_type: Indexing operation (one of ``index``, ``create``,
            ``delete`` or ``update``).
        :param index: The Elasticsearch index. (Default: ``None``)
        :param doc_type: The Elasticsearch doc_type. (Default: ``None``)
        """
        with self.create_producer() as producer:
            for rec in record_id_iterator:
                producer.publish(dict(
                    id=str(rec),
                    op=op_type,
                    index=index,
                    doc_type=doc_type
                ))

    def _actionsiter(self, message_iterator, with_deleted=False):
        """Iterate bulk actions.

        :param message_iterator: Iterator yielding messages from a queue.
        """
        for message in message_iterator:
            payload = message.decode()
            try:
                if payload['op'] == 'delete':
                    yield self._delete_action(payload)
                else:
                    yield self._index_action(payload, with_deleted=with_deleted)
                message.ack()
            except NoResultFound:
                message.reject()
            except Exception:
                message.reject()
                current_app.logger.error(
                    "Failed to index record {0}".format(payload.get('id')),
                    exc_info=True)

    def _actionsiter2(self, ids, with_deleted=False):
        """Iterate bulk actions.

        :param message_iterator: Iterator yielding messages from a queue.
        """
        for id in ids:
            yield self._index_action2(id, True, with_deleted=with_deleted)

    def _actionsiter_sync_version(self, message_iterator):
        """
        Iterate bulk actions with sync version.

        Args:
            message_iterator (iterator): Iterator yielding messages from a queue.

        Returns:
            iterator: Yields bulk action dictionaries for Elasticsearch.

        Raises:
            NoResultFound: If the record is not found in the database.
            Exception: For other errors during action generation.
        """
        for message in message_iterator:
            payload = message.decode()
            try:
                if payload['op'] == 'delete':
                    yield self._delete_action(payload)
                else:
                    yield self._index_action_sync_version(payload)
                message.ack()
            except NoResultFound:
                message.reject()
            except Exception:
                message.reject()
                current_app.logger.error(
                    f"Failed to index record {0}".format(payload.get('id')),
                    exc_info=True)

    def _delete_action(self, payload):
        """Bulk delete action.

        :param payload: Decoded message body.
        :returns: Dictionary defining an Elasticsearch bulk 'delete' action.
        """
        index, doc_type = payload.get('index'), payload.get('doc_type')
        if not (index and doc_type):
            record = Record.get_record(payload['id'])
            index, doc_type = self.record_to_index(record)

        return {
            '_op_type': 'delete',
            '_index': index,
            '_type': doc_type,
            '_id': payload['id'],
        }

    def _index_action(self, payload, with_deleted=False):
        """Bulk index action.

        :param payload: Decoded message body.
        :returns: Dictionary defining an Elasticsearch bulk 'index' action.
        """

        return self._index_action2(payload['id'], with_deleted=with_deleted)

    def _index_action2(self, id,deleteFile=False,with_deleted=False):
        """Bulk index action.

        :param payload: Decoded message body.
        :returns: Dictionary defining an Elasticsearch bulk 'index' action.
        """
        record = Record.get_record(id)
        self.count = self.count + 1
        click.secho("Indexing ID:{}, Count:{}".format(id,self.count),fg='green')

        self.latest_item_id = id
        index, doc_type = self.record_to_index(record)

        arguments = {}
        body = self._prepare_record(record, index, doc_type, arguments)
        body_size = len(json.dumps(body))
        max_body_size = current_app.config['INDEXER_MAX_BODY_SIZE']


        if deleteFile or (body_size>max_body_size):
            if 'content' in body:
                for i in range(len(body['content'])):
                    body['content'][i]['file'] = ""

        action = {
            '_op_type': 'index',
            '_index': index,
            '_type': doc_type,
            '_id': str(record.id),
            '_version': record.revision_id,
            '_version_type': self._version_type,
            '_source': body
        }
        action.update(arguments)

        return action

    def _index_action_sync_version(self, payload):
        """
        Create a bulk index action for Elasticsearch.

        Args:
            id (str): Record identifier.
            deleteFile (bool, optional): If True, remove file information from the content. Default is False.
            with_deleted (bool, optional): If True, include deleted records in the indexing process. Default is False.

        Returns:
            dict: Dictionary defining an Elasticsearch bulk 'index' action.

        Raises:
            Exception: If the record cannot be retrieved or processed.
        """
        from weko_deposit.api import WekoIndexer # avoid circular import
        record_id = payload['id']
        record = Record.get_record(record_id)

        indexer = WekoIndexer()
        indexer.get_es_index()
        res = indexer.get_metadata_by_item_id(record_id)
        es_version = res.get('_version')

        try:
            if record.model.version_id < es_version:
                record.model.version_id = es_version
                db.session.commit()

        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.error(
                f'SQLAlchemy error occurred while updating the version_id in records_metadata for id: {record_id}.')
            traceback.print_exc()
            raise

        self.count = self.count + 1
        click.secho(f"Indexing ID:{record_id}, Count:{self.count}", fg='green')

        self.latest_item_id = record_id
        index, doc_type = self.record_to_index(record)

        arguments = {}
        body = self._prepare_record(record, index, doc_type, arguments)

        body_size = len(json.dumps(body))
        max_body_size = current_app.config['INDEXER_MAX_BODY_SIZE']

        if body_size>max_body_size:
            if 'content' in body:
                for i in range(len(body['content'])):
                    body['content'][i]['file'] = ""

        action = {
            '_op_type': 'index',
            '_index': index,
            '_type': doc_type,
            '_id': str(record.id),
            '_version': record.model.version_id,
            '_version_type': self._version_type,
            '_source': body
        }
        action.update(arguments)
        return action

    @staticmethod
    def _prepare_record(record, index, doc_type, arguments=None, **kwargs):
        """Prepare record data for indexing.

        :param record: The record to prepare.
        :param index: The Elasticsearch index.
        :param doc_type: The Elasticsearch document type.
        :param arguments: The arguments to send to Elasticsearch upon indexing.
        :param **kwargs: Extra parameters.
        :returns: The record metadata.
        """
        if current_app.config['INDEXER_REPLACE_REFS']:
            data = copy.deepcopy(record.replace_refs())
        else:
            data = record.dumps()

        data['_created'] = pytz.utc.localize(record.created).isoformat() \
            if record.created else None
        data['_updated'] = pytz.utc.localize(record.updated).isoformat() \
            if record.updated else None

        # Allow modification of data prior to sending to Elasticsearch.
        before_record_index.send(
            current_app._get_current_object(),
            json=data,
            record=record,
            index=index,
            doc_type=doc_type,
            arguments={} if arguments is None else arguments,
            **kwargs
        )

        return data

    def reindex_bulk(self, client, actions, stats_only=False, *args, **kwargs):
        """
        Wrapper function for streaming_bulk, providing the same behavior as bulk.

        Args:
            client (Elasticsearch): Elasticsearch client instance.
            actions (iterator): Iterator containing bulk actions to be processed.
            stats_only (bool, optional): If True, returns only the number of successful and failed operations. If False, returns the number of successful operations and a list of error responses. Default is False.
            *args: Additional arguments to pass to Elasticsearch.
            **kwargs: Extra parameters.

        Returns:
            tuple: If stats_only=True, returns (success, failed). If stats_only=False, returns (success, errors).

        Raises:
            BulkIndexError: Raised when a bulk-specific error occurs during processing.
            BulkConnectionError: Raised when a connection error occurs.
            BulkConnectionTimeout: Raised when a connection timeout occurs.
            BulkException: Raised for any other exceptions during bulk processing.
        """
    # ...existing
        success, failed = 0, 0
        errors = []
        success_ids = []
        current_chunk = 1
        chunk_progress = f"{current_chunk}/{self.target_chunks}"
        ignore_status = kwargs.pop('ignore_status', None)
        span_name = kwargs.pop('span_name', None)
        kwargs.pop('yield_ok', None)
        try:
            streaming_bulk_kwargs = {"yield_ok": True}
            if span_name is not None:
                streaming_bulk_kwargs["span_name"] = span_name
            if ignore_status is not None:
                streaming_bulk_kwargs["ignore_status"] = ignore_status
            item_count = 0
            log_list = []
            for ok, item in streaming_bulk(
                client,
                actions,
                *args,
                **streaming_bulk_kwargs,
                **kwargs
            ):
                item_count += 1
                if not ok:
                    if not stats_only:
                        errors.append(item)
                    failed += 1
                    log_list.append({"id": item['index']['_id'], "Status": "Fail"})
                else:
                    success += 1
                    success_ids.append(item['index']['_id'])
                    log_list.append({"id": item['index']['_id'], "Status": "Success"})
                if item_count % kwargs["chunk_size"] == 0:
                    date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                    for log in log_list:
                        if log["Status"] == "Success":
                            click.secho("[{}] ID: {}, Status: {}, Chunk: {}".format(date, log["id"], log["Status"], chunk_progress), fg='green')
                        else:
                            click.secho("[{}] ID: {}, Status: {}, Chunk: {}".format(date, log["id"], log["Status"], chunk_progress), fg='red')
                    current_chunk += 1
                    chunk_progress = f"{current_chunk}/{self.target_chunks}"
                    log_list = []
            date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            for log in log_list:
                if log["Status"] == "Success":
                    click.secho("[{}] ID: {}, Status: {}, Chunk: {}".format(date, log["id"], log["Status"], chunk_progress), fg='green')
                else:
                    click.secho("[{}] ID: {}, Status: {}, Chunk: {}".format(date, log["id"], log["Status"], chunk_progress), fg='red')
            self.success_ids = success_ids
            return (success, failed) if stats_only else (success, errors)
        except BulkIndexError:
            self.success_ids = success_ids
            raise
        except ConnectionTimeout as cte:
            self.success_ids = success_ids
            raise BulkConnectionTimeout(success, failed, errors, cte) from cte
        except ConnectionError as ce:
            self.success_ids = success_ids
            raise BulkConnectionError(success, failed, errors, ce) from ce
        except Exception as e:
            self.success_ids = success_ids
            raise BulkException(success, failed, errors, e) from e

class BulkRecordIndexer(RecordIndexer):
    r"""Provide an interface for indexing records in Elasticsearch.

    Uses bulk indexing by default.
    """

    def index(self, record):
        """Index a record.

        The caller is responsible for ensuring that the record has already been
        committed to the database. If a newer version of a record has already
        been indexed then the provided record will not be indexed. This
        behavior can be controlled by providing a different ``version_type``
        when initializing ``RecordIndexer``.

        :param record: Record instance.
        """
        self.bulk_index([record.id])

    def index_by_id(self, record_uuid):
        """Index a record by record identifier.

        :param record_uuid: Record identifier.
        """
        self.bulk_index([record_uuid])

    def delete(self, record):
        """Delete a record.

        :param record: Record instance.
        """
        self.bulk_delete([record.id])

    def delete_by_id(self, record_uuid):
        """Delete record from index by record identifier."""
        self.bulk_delete([record_uuid])

class BulkBaseException(Exception):
    """
    Base exception for bulk indexing errors.

    Args:
        success (int): Number of successful operations before the exception.
        failed (int): Number of failed operations before the exception.
        errors (list): List of error details.
        original_exception (Exception): The original exception that was raised.

    Attributes:
        success (int): Number of successful operations.
        failed (int): Number of failed operations.
        errors (list): List of error details.
        original_exception (Exception): The original exception.
    """
    def __init__(self, success, failed, errors, original_exception):
        super().__init__(str(original_exception))
        self.success = success
        self.failed = failed
        self.errors = errors
        self.original_exception = original_exception


class BulkConnectionError(BulkBaseException, ConnectionError):
    """
    Exception raised when a connection error occurs during bulk indexing.

    Args:
        success (int): Number of successful operations before the exception.
        failed (int): Number of failed operations before the exception.
        errors (list): List of error details.
        original_exception (Exception): The original connection error that was raised.

    Attributes:
        success (int): Number of successful operations.
        failed (int): Number of failed operations.
        errors (list): List of error details.
        original_exception (Exception): The original connection error.
    """
    pass

class BulkConnectionTimeout(BulkBaseException, ConnectionTimeout):
    """
    Exception raised when a connection timeout occurs during bulk indexing.

    Args:
        success (int): Number of successful operations before the exception.
        failed (int): Number of failed operations before the exception.
        errors (list): List of error details.
        original_exception (Exception): The original timeout exception that was raised.

    Attributes:
        success (int): Number of successful operations.
        failed (int): Number of failed operations.
        errors (list): List of error details.
        original_exception (Exception): The original timeout exception.
    """
    pass

class BulkException(BulkBaseException):
    """
    General exception for errors during bulk indexing.

    Args:
        success (int): Number of successful operations before the exception.
        failed (int): Number of failed operations before the exception.
        errors (list): List of error details.
        original_exception (Exception): The original exception that was raised.

    Attributes:
        success (int): Number of successful operations.
        failed (int): Number of failed operations.
        errors (list): List of error details.
        original_exception (Exception): The original exception.
    """
    pass
