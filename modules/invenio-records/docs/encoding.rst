..
    This file is part of Invenio.
    Copyright (C) 2020 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

JSON Encoding/Decoding
======================

A record is a Python dictionary which can be persisted as a JSON document in
a database. Because the record is persisted as a JSON document, the Python
dictionary can by default only hold valid JSON data types (string, number,
object, array, boolean and null). Most notably, the Python dictionary cannot
hold for instance a Python datetime object like this::

    Record.create({"date": date(2020, 9, 7)})

Above will raise an error.

Custom encoder/decoder
----------------------
Invenio-Records supports customizing the JSON encoder/decoder which is
responsible for converting the dictionary to a JSON document and vice versa.
This allows you to support non-JSON data types like for instance a Python
date object.

First, let's look at the encoder/decoder. An encoder is a simple class with
two methods: ``encode()`` and ``decode()``:

.. code-block:: python

    class DateEncoder:
        def __init__(self, *keys):
            self.keys = keys

        def encode(self, data):
            for k in self.keys:
                if k in data:
                    data[k] = data[k].isoformat()

        def decode(self, data):
            for k in self.keys:
                if k in data:
                    s = data[k]
                    year, month, day = int(s[0:4]), int(s[5:7]), int(s[8:10])
                    data[k] = date(year, month, date)

- The ``encode()`` method iterate over keys, and converts a Python date object
  into a string (a valid JSON data type) using the ``isoformat()`` method of a
  date.
- The ``decode()`` method does the reverse. It parses a string and converts it
  into a date object.

Using the encoder
~~~~~~~~~~~~~~~~~
Next, you can use the encoder by assigning it to a custom model class and using
that model class in your custom record. This could look like below:

.. code-block:: python

    class MyRecordMetadata(db.Model, RecordMetadataBase):
        __tablename__ = 'myrecord_metadata'

        encoder = DatetimeEncoder('pubdate')

    class MyRecord(Record):
        model_cls = MyRecordMetadata

You can now create and get records with a Python date object, which will be
properly encoded/decoded on the way to/from the database

.. code-block:: python

    record = MyRecord.create({'pubdate': date(2020, 9, 3)})
    record = MyRecord.get_record(record.id)
    record['pubdate'] == date(2020, 9, 3)

JSONSchema validation
---------------------
JSONSchema validation is done on the JSON encoded version of the record. This
ensures that the schema validation is actually applied to the JSON document and
not the Python dict representation of it, which would involve validating
non-JSON data types.

Internals
---------
It is important to realize that there exists two distinct representations of a
record:

- The Python dictionary - possibly holding complex Python data types.
- The JSON encoded version of the Python dictionary - holding only JSON data
  types.

The Python dictionary is encoded to the JSON version **only** when we persist
the record to the database. Similarly, we only decode the JSON version when we
read the record from the database. **This means that the two representations
are not kept in sync**.

You should only ever modify the Python dictionary.  In simple terms that means:

.. code-block:: python

    # DON'T:
    record.model.json['mykey']
    record.model.json['mykey'] = ...
    record.model.json = record
    # DO:
    record['mykey]
    record['mykey] = ...

If you touch ``record.model.json`` you risk creating a binding between the
Python dictionary and the JSON encoded version of it because of Python's data
model (e.g. you modify a nested object on the Python dictionary will cause
the JSON version to also be updated because both holds a reference to the
nested dict).



