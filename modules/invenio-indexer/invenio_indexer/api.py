# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""API for indexing of records."""

import copy
import traceback
import click
import json
import warnings
from contextlib import contextmanager
import pytz
from celery import current_app as current_celery_app
from flask import current_app
from invenio_records.api import Record
from invenio_search import current_search_client
from invenio_search.engine import dsl, search
from invenio_search.utils import build_alias_name
from kombu import Producer as KombuProducer
from kombu.compat import Consumer
from sqlalchemy.orm.exc import NoResultFound

from .proxies import current_record_to_index
from .signals import before_record_index

# the tests expect this to be present
bulk = search.helpers.bulk
BulkIndexError = search.helpers.BulkIndexError
ConnectionTimeout = search.ConnectionTimeout
ConnectionError = search.ConnectionError

class Producer(KombuProducer):
    """Producer validating published messages.

    For more information visit :class:`kombu:kombu.Producer`.
    """

    def publish(self, data, **kwargs):
        """Validate operation type."""
        assert data.get("op") in {"index", "create", "delete", "update"}
        return super(Producer, self).publish(data, **kwargs)


class RecordIndexer(object):
    r"""Provide an interface for indexing records in the search engine.

    Bulk indexing works by queuing requests for indexing records and processing
    these requests in bulk.
    """

    record_cls = Record
    """Record class used for retrieving and dumping records.

    You can either subclass and overwrite this attribute, or provide the record
    class to the constructor.
    """

    record_dumper = None
    """Dumper instance to use with this record indexer."""

    def __init__(
        self,
        search_client=None,
        exchange=None,
        queue=None,
        routing_key=None,
        version_type=None,
        record_to_index=None,
        record_cls=None,
        record_dumper=None,
        publish_kwargs=None,
        bulk_index_max_items=10_000,
    ):
        """Initialize indexer.

        :param search_client: search engine client.
            (Default: ``current_search_client``)
        :param exchange: A :class:`kombu.Exchange` instance for message queue.
        :param queue: A :class:`kombu.Queue` instance for message queue.
        :param routing_key: Routing key for message queue.
        :param version_type: search engine version type.
            (Default: ``external_gte``)
        :param record_to_index: Function to extract the index from the record.
        :param record_cls: Record class used for retriving and dumping records.
            If the ``Record.enable_jsonref`` flag is False, new-style record
            dumping will be used for creating the search engine source
            document.
        :param record_dumper: Dumper instance to use for dumping the record.
            Only has an effect for new-style record dumping.
        :param bulk_index_max_items: max number of records to consume per task, when
            bulk indexing.
        """
        self.client = search_client or current_search_client
        self._exchange = exchange
        self._queue = queue
        self._record_to_index = record_to_index or current_record_to_index
        self._routing_key = routing_key
        self._version_type = version_type or "external_gte"
        self._publish_kwargs = publish_kwargs
        self._bulk_index_max_items = bulk_index_max_items

        if record_cls:
            self.record_cls = record_cls
        if record_dumper:
            self.record_dumper = record_dumper

    def record_to_index(self, record):
        """Get the index, given a record.

        :param record: The record where to look for the information.
        :returns: The index.
        """
        result = self._record_to_index(record)
        if isinstance(result, tuple):
            warnings.warn(
                (
                    "The 'record_to_index' function is no longer expected to return "
                    "a tuple (index, doc_type), instead it should only return the "
                    "index. Support for the tuple will be removed in a future version "
                    "of 'invenio-indexer'."
                ),
                DeprecationWarning,
            )
            result, _ = result

        return result

    @property
    def mq_queue(self):
        """Message Queue queue.

        :returns: The Message Queue queue.
        """
        return self._queue or current_app.config["INDEXER_MQ_QUEUE"]

    @property
    def mq_exchange(self):
        """Message Queue exchange.

        :returns: The Message Queue exchange.
        """
        return self._exchange or current_app.config["INDEXER_MQ_EXCHANGE"]

    @property
    def mq_routing_key(self):
        """Message Queue routing key.

        :returns: The Message Queue routing key.
        """
        return self._routing_key or current_app.config["INDEXER_MQ_ROUTING_KEY"]

    @property
    def mq_publish_kwargs(self):
        """Message Queue producer publish kwargs."""
        if self._publish_kwargs is not None:  # this allows overriding to {}
            return self._publish_kwargs
        return current_app.config["INDEXER_MQ_PUBLISH_KWARGS"]

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
        index = self.record_to_index(record)
        arguments = arguments or {}
        body = self._prepare_record(record, index, arguments, **kwargs)
        index = self._prepare_index(index)

        return self.client.index(
            id=str(record.id),
            version=record.revision_id,
            version_type=self._version_type,
            index=index,
            body=body,
            **arguments,
        )

    def index_by_id(self, record_uuid, **kwargs):
        """Index a record by record identifier.

        :param record_uuid: Record identifier.
        :param kwargs: Passed to :meth:`RecordIndexer.index`.
        """
        return self.index(self.record_cls.get_record(record_uuid), **kwargs)

    def refresh(self, index=None, **kwargs):
        """Refresh an index.

        :param index: the index or index name to refresh. if not given the
                      indexer record class index will be used.
        """
        if not index:
            index_name = self.record_cls.index._name
        elif isinstance(index, dsl.Index):
            index_name = index._name
        else:
            index_name = index

        index_name = build_alias_name(index_name)

        return self.client.indices.refresh(index=index_name, **kwargs)

    def exists(self, index=None, **kwargs):
        """Check if an index exists.

        :param index: the index or index name to refresh. if not given the
                      indexer record class index will be used.
        """
        if not index:
            index_name = self.record_cls.index._name
        elif isinstance(index, dsl.Index):
            index_name = index._name
        else:
            index_name = index

        index_name = build_alias_name(index_name)

        return self.client.indices.exists(index=index_name, **kwargs)

    def delete(self, record, **kwargs):
        """Delete a record.

        :param record: Record instance.
        :param kwargs: Passed to `search.delete`.
        """
        index = self.record_to_index(record)
        index = self._prepare_index(index)

        # Pop version arguments for backward compatibility if they were
        # explicit set to None in the function call.
        if "version" in kwargs and kwargs["version"] is None:
            kwargs.pop("version", None)
            kwargs.pop("version_type", None)
        else:
            kwargs.setdefault("version", record.revision_id)
            kwargs.setdefault("version_type", self._version_type)

        return self.client.delete(id=str(record.id), index=index, **kwargs)

    def delete_by_id(self, record_uuid, **kwargs):
        """Delete record from index by record identifier.

        :param record_uuid: Record identifier.
        :param kwargs: Passed to :meth:`RecordIndexer.delete`.
        """
        self.delete(self.record_cls.get_record(record_uuid), **kwargs)

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, "index")

    def bulk_delete(self, record_id_iterator):
        """Bulk delete records from index.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, "delete")

    def process_bulk_queue(self, search_bulk_kwargs=None, bulk_index_max_items=None ,with_deleted=False):
        """Process bulk indexing queue.

        :param dict search_bulk_kwargs: Passed to `search.helpers.bulk`.
        :param int bulk_index_max_items: max number of records to consume per task,
            when bulk indexing. If None, the default from the class attribute will
            be used instead.
        :param bool with_deleted: If True, include deleted records in the bulk
        """

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

                req_timeout = current_app.config["INDEXER_BULK_REQUEST_TIMEOUT"]
                search_bulk_kwargs = search_bulk_kwargs or {}
                bulk_index_max_items = bulk_index_max_items or self._bulk_index_max_items

                with consumer:
                    try:
                        _success,_fail  = bulk(
                            self.client,
                            self._actionsiter(consumer.iterqueue(limit=bulk_index_max_items),with_deleted=with_deleted),
                            stats_only=True,
                            request_timeout=req_timeout,
                            expand_action_callback=search.helpers.expand_action,
                            **search_bulk_kwargs,
                        )
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
                                **search_bulk_kwargs
                            )
                            success = success + _success
                            fail = fail + _fail
                        except BulkIndexError as be2:
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
                                **search_bulk_kwargs
                        )
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


                consumer.close()

        count = (success,fail)
        click.secho("count(success, error): {}".format(count),fg='green')
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
    def _bulk_op(self, record_id_iterator, op_type, index=None):
        """Index record in the search engine asynchronously.

        :param record_id_iterator: dIterator that yields record UUIDs.
        :param op_type: Indexing operation (one of ``index``, ``create``,
            ``delete`` or ``update``).
        :param index: The search engine index. (Default: ``None``)
        """
        with self.create_producer() as producer:
            for rec in record_id_iterator:
                data = dict(
                    id=str(rec),
                    op=op_type,
                    index=index,
                )
                producer.publish(
                    data,
                    declare=[self.mq_queue],
                    **self.mq_publish_kwargs,
                )

    def _actionsiter(self, message_iterator, with_deleted=False):
        """Iterate bulk actions.

        :param message_iterator: Iterator yielding messages from a queue.
        """
        for message in message_iterator:
            payload = message.decode()
            try:
                if payload["op"] == "delete":
                    yield self._delete_action(payload)
                else:
                    yield self._index_action(payload, with_deleted=with_deleted)
                message.ack()
            except NoResultFound:
                message.reject()
            except Exception:
                message.reject()
                current_app.logger.error(
                    "Failed to index record {0}".format(payload.get("id")),
                    exc_info=True,
                )

    def _actionsiter2(self, ids, with_deleted=False):
        """Iterate bulk actions.

        :param message_iterator: Iterator yielding messages from a queue.
        """
        for id in ids:
            yield self._index_action2(id, True, with_deleted=with_deleted)


    def _delete_action(self, payload):
        """Bulk delete action.

        :param payload: Decoded message body.
        :returns: Dictionary defining the search engine bulk 'delete' action.
        """
        kwargs = {}
        index = payload.get("index")
        if not index:
            record = self.record_cls.get_record(payload["id"], with_deleted=True)
            index = self.record_to_index(record)
            kwargs["_version"] = record.revision_id
            kwargs["_version_type"] = self._version_type
        else:
            # Allow version to be sent in the payload (but only use if we
            # haven't loaded the record.
            if "version" in payload:
                kwargs["_version"] = payload["version"]
                kwargs["_version_type"] = self._version_type
        index = self._prepare_index(index)

        return {
            "_op_type": "delete",
            "_index": index,
            "_id": payload["id"],
            **kwargs,
        }

    def _index_action(self, payload, with_deleted=False):
        """Bulk index action.

        :param payload: Decoded message body.
        :returns: Dictionary defining the search engine bulk 'index' action.
        """

        return self._index_action2(payload['id'], with_deleted=with_deleted)

    def _index_action2(self, id,deleteFile=False,with_deleted=False):
        """Bulk index action.

        :param payload: Decoded message body.
        :returns: Dictionary defining an the search engine bulk 'index' action.
        """
        record = self.record_cls.get_record(id)
        self.count = self.count + 1
        click.secho("Indexing ID:{}, Count:{}".format(id,self.count),fg='green')

        self.latest_item_id = id
        index = self.record_to_index(record)

        arguments = {}
        body = self._prepare_record(record, index, arguments)
        index = self._prepare_index(index)
        body_size = len(json.dumps(body))
        max_body_size = current_app.config['INDEXER_MAX_BODY_SIZE']


        if deleteFile or (body_size>max_body_size):
            if 'content' in body:
                for i in range(len(body['content'])):
                    body['content'][i]['file'] = ""

        action = {
            "_op_type": "index",
            "_index": index,
            "_id": str(record.id),
            "_version": record.revision_id,
            "_version_type": self._version_type,
            "_source": body,
        }
        action.update(arguments)

        return action

    def _prepare_index(self, index):
        """Prepare the index before an operation."""
        return build_alias_name(index)

    def _prepare_record(self, record, index, arguments=None, **kwargs):
        """Prepare record data for indexing.

        Invenio-Records is evolving and preparing the search engine source
        document is now a responsibility of the Record class. For backward
        compatibility, we use the ``Record.enable_jsonref`` flag to control
        if we use the new record dumpers feature from Invenio-Records. Set the
        flag to ``False`` (disabling JSONRef replacement) to use the new
        style record dumping.

        :param record: The record to prepare.
        :param index: The search engine index.
        :param arguments: The arguments to send to the search engine upon indexing.
        :param **kwargs: Extra parameters.
        :returns: The search engine source document.
        """
        # New-style record dumping - we use the Record.enable_jsonref flag on
        # the Record to control if we use the new simplified dumping.
        if not getattr(record, "enable_jsonref", True):
            # If dumper is None, dumps() will use the default configured dumper
            # on the Record class.
            return record.dumps(dumper=self.record_dumper)

        # Old-style dumping - the old style will still if INDEXER_REPLACE_REFS
        # is False use the Record.dumps(), however the default implementation
        # is backward compatible for new-style records. Also, we're adding
        # extra information into the record like _created and _updated
        # afterwards, which the Record.dumps() have no control over.
        if current_app.config["INDEXER_REPLACE_REFS"]:
            data = copy.deepcopy(record.replace_refs())
        else:
            data = record.dumps()

        data["_created"] = (
            pytz.utc.localize(record.created).isoformat() if record.created else None
        )
        data["_updated"] = (
            pytz.utc.localize(record.updated).isoformat() if record.updated else None
        )

        # Allow modification of data prior to sending to the search engine.
        before_record_index.send(
            current_app._get_current_object(),
            json=data,
            record=record,
            index=index,
            arguments={} if arguments is None else arguments,
            **kwargs,
        )

        return data


class BulkRecordIndexer(RecordIndexer):
    r"""Provide an interface for indexing records in the search engine.

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
