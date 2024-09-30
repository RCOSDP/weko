..
    This file is part of Invenio.
    Copyright (C) 2017-2023 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.


Changes
=======

Version 4.0.2 (release 2024-03-04)
----------------------------------

- aggregations: consider updated_timestamp field optional (ensure backwards compatibility)

Version 4.0.1 (release 2023-10-09)
----------------------------------

- aggregations: ensure events are aggregated only once

Version 4.0.0 (release 2023-10-03)
----------------------------------

- introduce new field `updated_timestamp`` in the events and stats templates
  and mappings
- improved calculation of aggregations skipping already aggregated events
- changed `refresh_interval` from 1m to 5s
- changed default events index name from daily to monthly
- moved BookmarkAPI to a new module

Version 3.1.0 (release 2023-04-20)
----------------------------------

- add extension method for building and caching queries

Version 3.0.0 (release 2023-03-01)
-------------------------------------

- Upgrade to ``invenio-search`` 2.x
- Drop support for Elasticsearch 2, 5, and 6
- Add support for OpenSearch 1 and 2
- Drop support for Python 2.7 and 3.6
- Remove function ``invenio_stats.utils:get_doctype``
- Fix ``validate_arguments`` for query classes
- Add ``build_event_emitter`` function for creating an ``EventEmitter`` but not registering it as a signal handler
- Add ``ext.get_event_emitter(name)``` function for caching built ``EventEmitter`` objects per name
- Replace elasticsearch-specific terminology

Version 2.0.0 (release 2023-02-23)
-------------------------------------

- add opensearch2 compatibility

Version 1.0.0a18 (release 2020-09-01)
-------------------------------------

- Fix isort arguments
- Filter pytest deprecation warnings
- Set default values for metrics instead of None, when no index found

Version 1.0.0a17 (release 2020-03-19)
-------------------------------------

- Removes Python 2.7 support.
- Centralizes Flask dependency via ``invenio-base``.

Version 1.0.0a16 (release 2020-02-24)
-------------------------------------

- bump celery dependency
- pin Werkzeug version

Version 1.0.0a15 (release 2019-11-27)
-------------------------------------

- Pin celery dependency

Version 1.0.0a14 (release 2019-11-27)
-------------------------------------

- Fix `get_bucket_size` method

Version 1.0.0a13 (release 2019-11-08)
-------------------------------------

- Bump invenio-queues

Version 1.0.0a12 (release 2019-11-08)
-------------------------------------

- Fixes templates for ElasticSearch 7
- Updates dependency of invenio-search

Version 1.0.0a11 (release 2019-10-02)
-------------------------------------

- Initial public release.
