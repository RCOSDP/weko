# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record indexer for Invenio.

Invenio-Indexer is responsible for sending records for indexing in
Elasticsearch so that the records can be searched. Invenio-Indexer can either
send the records in bulk or individually. Bulk indexing is far superior in
performance if multiple records needs to be indexed at the price of delay. Bulk
indexing works by queuing records in a message queue, which is then consumed
and sent to Elasticsearch.

Initialization
--------------
First create a Flask application:

>>> from flask import Flask
>>> app = Flask('myapp')
>>> app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

You initialize Indexer like a normal Flask extension, however
Invenio-Indexer is dependent on Invenio-Records and Invenio-Search so you
need to initialize these extensions first:

>>> from invenio_db import InvenioDB
>>> ext_db = InvenioDB(app)
>>> from invenio_search import InvenioSearch
>>> ext_search = InvenioSearch(app)
>>> from invenio_records import InvenioRecords
>>> ext_records = InvenioRecords(app)

We now initialize Invenio-Indexer:

>>> from invenio_indexer import InvenioIndexer
>>> ext_indexer = InvenioIndexer(app)

In order for the following examples to work, you need to work within an
Flask application context so let's push one:

>>> ctx = app.app_context()
>>> ctx.push()

Also, for the examples to work we need to create the database tables and
Elasticsearch indexes (note, in this example we use an in-memory SQLite
database):

>>> from invenio_db import db
>>> db.create_all()

Indexing a record
-----------------
Let's start by creating a record that we would like to index:

>>> from invenio_db import db
>>> from invenio_records.api import Record
>>> record = Record.create({'title': 'A test'})
>>> db.session.commit()

Note, that you are responsible for ensuring that the record is committed to
the  database, prior to sending it for indexing.

Now, let's index the record:

>>> from invenio_indexer.api import RecordIndexer
>>> indexer = RecordIndexer()
>>> res = indexer.index(record)

By default, records are sent to the Elasticsearch index defined by the
configuration variable ``INDEXER_DEFAULT_INDEX``. If the record however
has a ``$schema`` attribute, the index is automatically determined from this.
E.g. the following record:

>>> r = Record({
...     '$schema': 'http://example.org/records/record-v1.0.0.json'})

Would be indexed in the following Elasticsearch index/doctype:

>>> print(indexer.record_to_index(record))
('records-record-v1.0.0', 'record-v1.0.0')

Bulk indexing
-------------
If you have many records to index, bulk indexing is far superior in speed to
single record indexing. Bulk indexing requires the existence of a queue on your
broker, so since this is the very first time we send any records for bulk
indexing, we will have to create this queue:

>>> from celery.messaging import establish_connection
>>> queue = app.config['INDEXER_MQ_QUEUE']
>>> with establish_connection() as conn:
...     queue(conn).declare()
'indexer'


We can now send a record for bulk indexing:

>>> indexer.bulk_index([str(r.id)])

Above will send the record id to the queue on your broker and wait for the bulk
indexer to execute. This is normally done in the background by a Celery task
which can be started from the command line like e.g.:

.. code-block:: console

   $ <instance cmd> index run

Note, you can achieve much higher indexing speeds, by having multiple processes
running the ``process_bulk_queue`` concurrently. This can be achieved with
e.g.:

.. code-block:: console

   $ <instance cmd> index run -d -c 8


Customizing record indexing
---------------------------
Record indexing can easily be customized using either:

* **JSONRef:** By default, all JSONRefs for each record is resolved prior to
  indexing.
* **Signals:** Before each record is indexed the signal ``before_record_index``
  is sent, in order to allow modification of the record. The signal can be used
  to e.g. remove sensitive data and/or add extra data to the record.

JSONRef
~~~~~~~
JSONRefs inside the record are by default resolved prior to indexing the
record. For instance the value for the ``rel`` key will be replaced with the
referenced JSON object:

>>> r = Record.create({
...     'title': 'A ref',
...     'rel': {'$ref': 'http://dx.doi.org/10.1234/foo'}})

See Invenio-Records documentation for how to customize the JSONRef resolver
to resolve references locally. The JSONRefs resolving works on all indexed
records, and can be switched off using the configuration::

>>> app.config['INDEXER_REPLACE_REFS'] = False

Signal
~~~~~~
First write a signal receiver. In the example below, we remove the attribute
``_internal`` if it exists in the record:

>>> def indexer_receiver(sender, json=None, record=None,
...                      index=None, doc_type=None):
...     if '_internal' in json:
...         del json['_internal']

The receiver takes four parameters besides the sender (which is the Flask
application)

* ``json``:  JSON is a Python dictionary dump of the record, and the actual
  data that will be sent to the index. Modify this dictionary in order to
  change the document.
* ``record``: The record from which the JSON was dumped.
* ``index``: The Elasticsearch index in which the record will be indexed.
* ``doc_type``: The Elasticsearch document type for the record.

Connecting the receiver to the signal is as simple as (do this e.g. in your
extension's ``init_app`` method):

>>> from invenio_indexer.signals import before_record_index
>>> res = before_record_index.connect(indexer_receiver, sender=app)
"""

from __future__ import absolute_import, print_function

from .ext import InvenioIndexer
from .proxies import current_record_to_index
from .version import __version__

__all__ = ('__version__', 'InvenioIndexer', 'current_record_to_index')
