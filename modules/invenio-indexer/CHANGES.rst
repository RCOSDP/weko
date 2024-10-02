..
    This file is part of Invenio.
    Copyright (C) 2016-2024 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version 2.3.0 (released 2024-03-04)

- indexer: Allow the definition of indices in index_templates, instead of mappings

Version 2.2.1 (released 2023-09-28)

- bulk: make configurable the number of records to be bulk indexed per task

Version 2.2.0 (released 2023-05-25)

- cli: add queue selection options
- tests: remove redis as message backend

Version 2.1.2 (released 2023-05-05)

- Allow passing message queue producer publish arguments via the ``RecordIndexer``
  constructor and the ``INDEXER_MQ_PUBLISH_KWARGS`` config.

Version 2.1.1 (released 2022-10-07)

- Change `schema_to_index` to return only the index and not a tuple with index and
  doc type.

Version 2.1.0 (released 2022-10-03)

- Add support to OpenSearch v2
- Remove `doc_type` param
- Change `record_to_index` to return only the index and not a tuple with index and
  doc type.
- Remove the config var `INDEXER_DEFAULT_DOC_TYPE`

Version 2.0.1 (released 2022-09-26)

- Bump upper pin of invenio-records

Version 2.0.0 (released 2022-09-23)

- Integrate invenio-search v2, add support to OpenSearch
- Require Elasticsearch >= 7.5
- Remove old versions of Elasticsearch mappings
- Breaking: rename kwarg param `es_bulk_kwargs` to `search_bulk_kwargs`

Version 1.2.7 (released 2022-05-17)

- Add exists method to RecordIndexer API class.

Version 1.2.6 (released 2022-05-13)

- Add refresh method to RecordIndexer API class.

Version 1.2.5 (released 2022-05-05)

- Add a config to defined the max number of concurrent consumers
  when bulk indexing.
- Allows to retrieve all registered indexers.

Version 1.2.4 (released 2022-04-26)

- Aligns with best practice from Kombu that producers should also declare
  queues.

Version 1.2.3 (released 2022-04-06)

- Add indexer registry and use it in celery tasks.

Version 1.2.2 (released 2022-03-30)

- Add support for Click v8.1+ and Flask v2.1+.

Version 1.2.1 (released 2021-03-05)

- Remove pytest runner from setup dependencies

Version 1.2.0 (released 2020-09-16)

- Changes delete requests to optimistic concurrency control by providing the
  the version and version_type in delete requests. The previous behavior can
  restored by calling
  ``RecordIndexer().delete(record, version=None, version_type=None)`` instead.

- Adds support for using new-style record dumping controlled via the
  ``Record.enable_jsonref`` flag.

Version 1.1.2 (released 2020-04-28)

- Introduces ``RecordIndexer.record_cls`` for customizing the record class.
- Removes Python 2 support.

Version 1.1.1 (released 2019-11-21)

- Fix bulk action parameters compatibility for Elasticsearch v7.

Version 1.1.0 (released 2019-07-19)

- Add support for Elasticsearch v7.
- Integrate index prefixing.
- Add ``before_record_index.dynamic_connect()`` signal utility for more
  flexible indexer receivers.
- Add ``schema_to_index`` utility from ``invenio-search`` (will be removed in
  next minor version of ``invenio-search``).

Version 1.0.2 (released 2019-05-27)

- Allow Elasticsearch indexing arguments to be modified by subscribing to
  ``before_record_index`` signal.

Version 1.0.1 (released 2018-10-11)

- Allow forwarding arguments from ``RecordIndexer.process_bulk_queue`` to
  ``elasticsearch.helpers.bulk`` calls via the ``es_bulk_kwargs`` parameter.

Version 1.0.0 (released 2018-03-23)

- Initial public release.
