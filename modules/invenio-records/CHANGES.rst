..
    This file is part of Invenio.
    Copyright (C) 2015-2024 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version 2.3.0 (released 2024-02-19)

- tests: add tests for filter_dict_keys
- dictutils: add filter_dict_keys

Version 2.2.2 (released 2023-09-12)

- search: prevent flush on search queries

Version 2.2.1 (released 2023-09-12)

- revert dumper: merge record to working data instead of replacing

Version 2.2.0 (released 2023-09-05)

- dumper: merge record to working data instead of replacing

Version 2.1.0 (released 2023-03-02)

- remove deprecated flask-babelex dependency and imports
- upgrade invenio-i18n
- upgrade invenio-admin

Version 2.0.1 (released 2022-11-18)

- Adds translations
- Upgrades pytest-invenio

Version 2.0.0 (released 2022-09-07)

- Renames SearchDumper classes to remove Elasticsearch naming.

Version 1.7.6 (released 2022-09-07)

- Moves the _fields attribute of RelationFields into a cached property.
  This allows delayed calculation of its values.

Version 1.7.5 (released 2022-09-06)

- Fixes a bug on MultiRelationsField where fields would be calculated multiple
  times. Now they are calculated only once, and cached.

Version 1.7.4 (released 2022-08-23)

- Adds support for nested RelationFields via MultiRelationsField
- Migrates to declarative module (setup.cfg)
- Migrates code to Black formatter
- Adds german translations
- Removes babel extensions for Jinja

Version 1.7.3 (released 2022-05-04)

- Adds utility to merge Python dicts

Version 1.7.2 (released 2022-05-03)

- Fixes regression in 1.7.1.

Version 1.7.1 (released 2022-04-26)

- Fixes dictionary lookup during dereferencing for optional/non-existing keys.

Version 1.7.0 (released 2022-04-13)

- Adds support for relations defined via database-level foreign keys.

- Backwards incompatible: Changes the relations definitions to support both
  dictionary keys and object attributes instead of only dictionary keys. Change
  existing code from::

    Relation(
        # ...
        attrs=['title'],
    ),

  to::

    Relation(
        # ...
        keys=['title'],
    ),

- Move from setup.py to setup.cfg for purely declarative package definitions.

Version 1.6.2 (released 2022-04-06)

- Removes python 3.6 from test suite.
- Initializes parent class of ModelField.
- Bumps several dependencies (invenio-db, invenio-base, etc.) to
  support Flask 2.1.

Version 1.6.1 (released 2021-12-04)

- Adds support for the post commit life-cycle hook.

Version 1.6.0 (released 2021-10-20)

- Adds a new relations system field for managing relations between records.
  Part of RFC #40.

- Adds a new related model system field to serialize/dump a related object into
  the record JSON.

- Adds new configuration variables to allow injecting a custom JSONSchema
  RefResolver together with a custom JSONSchema store. Part of RFC #42 to
  simplify JSON Schema resolution and registry management and more easily build
  composable JSONSchemas.

- Deprecated the Record.patch() method.

Version 1.5.0

- Not released to avoid polluting Invenio v3.4.

Version 1.4.0 (released 2020-12-09)

- Backwards incompatible: By default the versioning table is now disabled in
  the ``RecordMetadataBase`` (the ``RecordMetadata`` is still versioned). If
  you subclasses ``RecordMetadataBase`` and needs versioning, you need to add
  the following line in your class:

  .. code-block:: python

        class MyRecordMetadata(db.Model, RecordMetadataBase):
            __versioned__ = {}

- Backwards incompatible: The ``Record.validate()`` method is now split in
  two methods ``validate()`` and ``_validate()``. If you overwrote the
  ``validate()`` method in a subclass, you may need to overwrite instead
  ``_validate()``.

- Backwards incompatible: Due to the JSON encoding/decoding support, the
  Python dictionary representing the record and the SQLAlchemy models are
  separate objects and updating one, won't automatically update the other.
  Normally, you should not have accessed ``record.model.json`` in your code,
  however if you did, you need to rewrite it and rely on the ``create()`` and
  ``commit()`` methods to update the model's ``json`` column.

- Adds a new is_deleted property to the Records API.

- Removes the @ prefix that was used to separate metadata fields from other
  fields.

- Adds a SystemFieldContext which allows knowing the record class when
  accessing the attribute through the class instead of object instance.

- Adds helpers for caching related objects on the record.

- Adds support for JSON encoding/decoding to/from the database. This allows
  e.g. have records with complex data types such as datetime objects.
  JSONSchema validation happens on the JSON encoded version of the record.

- Adds dumpers to support dumping and loading records from secondary copies
  (e.g. records stored in an Elasticsearch index).

- Adds support record extensions as a more strict replacement of signals.
  Allows writing extensions (like the system fields), that integrate into the
  Records API.

- Adds support for system fields that are Python data descriptors on the Record
  which allows for managed access to the Record's dictionary.

- Adds support for disabling signals.

- Adds support for disabling JSONRef replacement.

- Adds support for specifying JSONSchema format checkers and validator class at
  a class-level instead of per validate call.

- Adds support for specifying class-wide JSONSchema format checkers

- Adds a cleaner definition of a what a soft-deleted record using the
  is_deleted hybrid property on the database model.

- Adds support for undeleting a soft-deleted record.

Version 1.3.2 (released 2020-05-27)

- Fixes a bug causing incorrect revisions to be fetched. If ``record.commit()``
  was called multiple times prior to a ``db.session.commit()``, there would be
  gaps in the version ids persisted in the database. This meant that if you
  used ``record.revisions[revision_id]`` to access a revision, it was not
  guaranteed to return that specific revision id. See #221

Version 1.3.1 (released 2020-05-07)

- Deprecated Python versions lower than 3.6.0. Now supporting 3.6.0 and 3.7.0.
- Removed dependency on Invenio-PIDStore and releated documentation.
  Functionality was removed in v1.3.0.

Version 1.3.0 (released 2019-08-01)

- Removed deprecated CLI.

Version 1.2.2 (released 2019-07-11)

- Fix XSS vulnerability in admin interface.

Version 1.2.1 (released 2019-05-14)

- Relax Flask dependency to v0.11.1.

Version 1.2.0 (released 2019-05-08)

- Allow to store RecordMetadata in a custom db table.

Version 1.1.1 (released 2019-07-11)

- Fix XSS vulnerability in admin interface.

Version 1.1.0 (released 2019-02-22)

- Removed deprecated Celery task.
- Deprecated CLI

Version 1.0.2 (released 2019-07-11)

- Fix XSS vulnerability in admin interface.

Version 1.0.1 (released 2018-12-14)

- Fix CliRunner exceptions.
- Fix JSON Schema URL.

Version 1.0.0 (released 2018-03-23)

- Initial public release.
