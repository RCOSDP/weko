# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""System fields provides managed access to the record's dictionary.

**A simple example**

Take the following record subclass:

.. code-block:: python

    class MyRecord(Record, SystemFieldsMixin):
        test = ConstantField('mykey', 'myval')

The class defines a system field named ``test`` of the type ``ConstantField``.
The constant field adds a key (``mykey``) to the record with the value
``myval`` when a record is created:

.. code-block:: python

    record = MyRecord({})

The key ``mykey`` is part of the record's dictionary (i.e. you can do
``record['mykey']`` to acecss the value)::

    record['mykey'] == 'myval'

The key can however also be accessed through the field (i.e. ``record.test``)::

    record.test == 'myval'

System fields is thus a way to manage a subpart of record an allows you the
field to hook into the record API. This is a powerful API that can be used
to create fields which provides integration with related objects.

**A more advanced example**

Imagine the following record subclass using an imaginary ``PIDField``:

.. code-block:: python

    class MyRecord(Record, SystemFieldsMixin):
        pid = PIDField(pid_type='recid', object_type='rec')

You could use this field to set a PID on the record::

    record.pid = PersistentIdentifier(...)

Or, you could access the PID on a record you get from the database:

.. code-block:: python

    record = MyRecord.get_record()
    record.pid  # would return a PersistentIdentifier object.

The simple example only worked with the record itself. The more advanced
example here, the record is integrated with related objects.

**Data access layer**

System fields can do a lot, however you should seen them as part of the data
access layer. This means that they primarily simplifies data access between
records and related objects.
"""

from .base import SystemField, SystemFieldContext, SystemFieldsMeta, SystemFieldsMixin
from .constant import ConstantField
from .dict import DictField
from .model import ModelField
from .relatedmodelfield import RelatedModelField, RelatedModelFieldContext
from .relations import ModelRelation, MultiRelationsField, PKRelation, RelationsField

__all__ = (
    "ConstantField",
    "DictField",
    "ModelField",
    "ModelRelation",
    "MultiRelationsField",
    "PKRelation",
    "RelatedModelField",
    "RelatedModelFieldContext",
    "RelationsField",
    "SystemField",
    "SystemFieldContext",
    "SystemFieldsMeta",
    "SystemFieldsMixin",
)
