# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

r"""Invenio-Records is a metadata storage module.

In a few words, a `record`_ is basically a structured collection of fields and
values (metadata) which provides information about other data.

.. _record: https://en.wikipedia.org/wiki/Record_(computer_science)

A record (and each revision) is identified by a unique `UUID`_, as most of the
others entities in Invenio.

.. _UUID: https://en.wikipedia.org/wiki/Universally_unique_identifier

Invenio-Records is a core component of Invenio and it provides a way to create,
update and delete records. Records are versioned, to keep track of
modifications and to be able to revert back to a specific revision.

When creating or updating a record, if the record contains a schema definition,
the record data will be validated against its schema. Moreover, data format can
for each field be also validated.

When deleting a record, two options are available:

* **soft deletion**: record will be deletes but keeping its identifier and
  history, to ensure that the same record's identifier cannot be reused, and
  that older revisions can be retrieved.
* **hard deletion**: record will be completely deleted with its history.

Records creation and update can be validated if the schema is provided.

Records CRUD operations are available using the administration interface and
the CLI, which also allows batch operations.

If `InvenioPIDStore`_ is installed, it also enables to
mint PIDs in a record using the CLI.

Further documentation available Documentation:
https://invenio-records.readthedocs.io/

.. _InvenioPIDStore: https://invenio-pidstore.readthedocs.io/

Initialization
--------------

Create a Flask application:

>>> import os
>>> db_url = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite://')
>>> from flask import Flask
>>> app = Flask('myapp')
>>> app.config.update({
...     'SQLALCHEMY_DATABASE_URI': db_url,
...     'SQLALCHEMY_TRACK_MODIFICATIONS': False,
... })

Initialize Invenio-Records dependencies and Invenio-Records itself:

>>> from invenio_db import InvenioDB
>>> ext_db = InvenioDB(app)
>>> from invenio_records import InvenioRecords
>>> ext_records = InvenioRecords(app)

The following examples needs to run in a Flask application context, so
let's push one:

>>> app.app_context().push()

Also, for the examples to work we need to create the database and tables (note,
in this example we use an in-memory SQLite database by default):

>>> from invenio_db import db
>>> db.create_all()

CRUD operations
---------------

Creation
~~~~~~~~

Let's **create** a very simple record:

>>> from invenio_records import Record
>>> record = Record.create({"title": "The title of the record"})
>>> db.session.commit()
>>> assert record.revision_id == 0

A new row has been added to the database, in the table ``records_metadata``:
this corresponds to the record metadata, first version (version 1).

Update
~~~~~~

Let's try to **update** the previously created record with new data. This will
create a new version of the previous with the same ``uuid`` but incremented
version/revision id.
Update the record and **commit** the changes to apply them to the record:

>>> record['title'] = 'The title of the 2nd version of the record'
>>> record = record.commit()  # validate new data and store changes
>>> db.session.commit()
>>> assert record.revision_id == 1

A second row has been added, version 2. You can access to the different
versions by doing:

>>> rec_v1 = record.revisions[0]
>>> rec_v2 = record.revisions[1]

Reverting
~~~~~~~~~

To **restore** the first version of the record, just:

>>> record = record.revert(0)
>>> db.session.commit()
>>> assert record.revision_id == 2

Patch
~~~~~

It is also possible to **patch** a record to perform multiple operations in one
shot:

>>> record = Record.create({"title": "First title"})
>>> db.session.commit()
>>> assert len(record.revisions) == 1

>>> ops = [
...     {"op": "replace", "path": "/title", "value": "Title first record"},
...     {"op": "add", "path": "/description", "value": "Record description"}
... ]

>>> record = record.patch(ops)
>>> record = record.commit()
>>> db.session.commit()
>>> assert len(record.revisions) == 2

See `JSON Patch <http://jsonpatch.com/>`_ documentation to have nice examples.

Deletion
~~~~~~~~

Let's create another record and then **soft delete** it:

>>> record = Record.create({"title": "Record to be deleted"})
>>> db.session.commit()
>>> record['title'] = 'Record to be deleted version 2'
>>> record = record.commit()
>>> db.session.commit()

>>> deleted = record.delete()

There is only one row left in the database corresponding to this record. Notice
that the ``json`` column is empty, but the ``uuid`` is still there. This
ensures uniqueness.
The record can be retrieved by doing:

>>> deleted = Record.get_record(record.id, with_deleted=True)
>>> assert deleted.id == record.id

Let's **hard delete** it, completely:

>>> deleted = record.delete(force=True)

Now, try to retrieve it, it will throw an exception.

>>> Record.get_record(record.id,
...                   with_deleted=True)  # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
  ...
NoResultFound: No row was found for one()

Record validation
-----------------

When creating or updating a record, the input data can be validated to ensure
that it is conform to a specified schema and values formats are respected.
The validation is provided by the
`jsonschema <https://python-jsonschema.readthedocs.io>`_ library.

How ``jsonschema`` works
~~~~~~~~~~~~~~~~~~~~~~~~

* **Format checker:** create a custom format checker (or use one of the
  available), for example to  validate if the first letter of a string is
  uppercase:

  >>> from jsonschema import FormatChecker
  >>> from jsonschema.validators import Draft4Validator
  >>> checker = FormatChecker()
  >>> f = checker.checks("uppercaseFirstLetter")(lambda value: value[0]
  ...                                             .isupper())
  >>> validator = Draft4Validator({"format": "uppercaseFirstLetter"},
  ...                             format_checker=checker)

  Now, let's try it out:

  >>> validator.validate("Title of the record")

  Does not throw any exception, because the data is valid, the first letter is
  uppercase.

  >>> validator.validate(
  ...               "title of the record")  # doctest: +IGNORE_EXCEPTION_DETAIL
  Traceback (most recent call last):
    ...
  ValidationError: 'title of the record' is not a 'uppercaseFirstLetter'
    ...

  This raises a ValidationError error exception, because the first letter is
  lowercase.

* **Schema validator:** create a validator to ensure that the input data
  structure, fields and types conform to a specific schema.

  >>> schema = {
  ...     'type': 'object',
  ...     'properties': {
  ...         'title': { 'type': 'string' },
  ...         'description': { 'type': 'string' }
  ...     },
  ...     'required': ['title']
  ... }

  Try to validate a record without the field `title`, which is required.

  >>> from jsonschema.validators import validate
  >>> record = {"description": "Description but no title"}
  >>> validate(record, schema)  # doctest: +IGNORE_EXCEPTION_DETAIL
  Traceback (most recent call last):
    ...
  ValidationError: 'title' is a required property
    ...

If the JSON schema is not defined inside the JSON itself, like in the example,
but it is defined somewhere else (e.g. any schema provider service), the record
should contain the ``$ref`` field with the URI link to the schema definition.
Record provides a method :py:meth:`api.RecordBase.replace_refs` that
will resolve the URI in the ``$ref`` field and return a new Record with the
schema definition injected.

Invenio-Records validation
~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's put everything together and create a record with validation and format
checking: define a schema with a mandatory ``title`` field and a validation
format for the ``title`` field.

>>> from jsonschema import FormatChecker
>>> checker = FormatChecker()
>>> f = checker.checks("uppercaseFirstLetter")(lambda value: value[0]
...                                             .isupper())
>>> schema = {
...     'type':'object',
...     'properties': {
...         'title': {
...             'type':'string',
...             'format': 'uppercaseFirstLetter'
...         },
...         'description': {
...             'type':'string'
...         }
...     },
...     'required': ['title']
... }

Create a new record with an invalid value format for the ``title`` field.
Notice that the ``schema`` must be defined in the record with the field
``$schema`` and the format checker must be passed as ``kwarg`` argument with
the key ``format_checker``, to be taken into account by the `jsonschema`
library.

>>> record = {
...     "$schema": schema,
...     "title": "title of this record",  # first letter is lowercase
...     "description": "Description of this record"
... }
>>> rec = Record.create(record,
...                format_checker=checker)  # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
  ...
ValidationError: 'title of this record' is not a 'uppercaseFirstLetter'
  ...

Create a new record without the ``title`` field:

>>> record = {
...     "$schema": schema,
...     "description": "Description of this record without a title"
... }
>>> rec = Record.create(record,
...                format_checker=checker)  # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
  ...
ValidationError: 'title' is a required property
  ...

CLI
---

The CLI provides a way of creating, patching or deleting records.
Batch operations should be performed using the CLI.

Create a new record:

.. code-block:: console

    $ echo '{"title": "New record"}' | flask records create

Create multiple records:

.. code-block:: console

    $ echo '[{"title": "1st"},{"title":"2nd"}]' | flask records create

A file with a list of records can be specified as parameter to create multiple
records in one shot. It is also possible to specify a list of ``ids``, where
each ``id`` corresponds to an input record, respecting the ordering.

In case of already existing ``id``, the ``force`` parameter will create a new
revision of the record:

.. code-block:: console

    $ echo '{"title": "New record"}' | flask records create \
       -i deadbeef-9fe4-43d3-a08f-38c2b309afba
    $ echo '{"title": "Same new record"}' | flask records create --force \
       -i deadbeef-9fe4-43d3-a08f-38c2b309afba

Patch an existing record:

.. code-block:: console

    $ echo '{"title": "New record"}' | flask records create \
       -i deadbeef-9fe4-43d3-a08f-38c2b309afbe
    $ echo '[{"op": "replace", "path": "/title", "value": "Patched"}]' | \
       flask records patch -i deadbeef-9fe4-43d3-a08f-38c2b309afbe

Soft and hard delete a record:

.. code-block:: console

    $ echo '{"title": "New record"}' | flask records create \
       -i 28c18220-f22e-480c-88ea-cd414aef035b
    $ flask records delete -i 28c18220-f22e-480c-88ea-cd414aef035b
    $ flask records delete --force -i 28c18220-f22e-480c-88ea-cd414aef035b

Minting PIDs
------------

If the module `InvenioPIDStore`_ is installed and loaded, the CLI option
``--pid-minter`` allows minting PIDs in records.

To use ``InvenioPIDStore``, initialize your app with:

>>> from invenio_pidstore import InvenioPIDStore
>>> ext_pid = InvenioPIDStore(app)

Then, when creating a record/records using the CLI, the name of an existing PID
minter can be specified as parameter:

.. code-block:: console

    $ echo '{"title": "New record with PID"}' | flask records create \
       -i deadbeef-9fe4-43d3-a08f-38c2b309afbc --pid-minter recid
    $ flask run
    $ curl http://127.0.0.1:5000/deadbeef-9fe4-43d3-a08f-38c2b309afbc

        {
          "control_number": "1",
          "title": "New record with PID"
        }

See `InvenioPIDStore`_ documentation for more information.

Signals
-------
Invenio-Records provides several types of signals and they can be used to react
to events to read or modify data before or after an operation.

Events are sent in case of:

* record creation, before and after
* record update, before and after
* record deletion, before and after
* record revert, before and after

Let's modify the record before creation and verify, after creation, that the
record has been correctly modified:

>>> from invenio_records.signals import (before_record_insert, \
...                                      after_record_insert)
>>> def before_record_creation_add_flag(sender, *args, **kwargs):
...     record = kwargs['record']
...     record['created_with'] = 'Invenio'
...
>>> listener = before_record_insert.connect(before_record_creation_add_flag)
>>> def after_record_creation(sender, *args, **kwargs):
...     record = kwargs['record']
...     assert 'created_with' in record
...
>>> listener = after_record_insert.connect(after_record_creation)
>>> rec_events = Record.create({"title": "My new record"})
>>> db.session.commit()

See :doc:`api` for extensive API documentation.
"""

from __future__ import absolute_import, print_function

from .api import Record
from .ext import InvenioRecords
from .version import __version__

__all__ = (
    'InvenioRecords',
    'Record',
    '__version__',
)
