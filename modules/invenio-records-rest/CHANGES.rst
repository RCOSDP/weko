..
    This file is part of Invenio.
    Copyright (C) 2015-2023 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version 2.4.1 (2024-05-08)

- marhsmallow: remove deprecation warning

Version 2.4.0 (2023-12-08)

- facet: Allow more than one possibility on range facets
- search: possibility to specify a different query_parser
- facets: New parameter, RECORDS_REST_FACETS_FILTER, to filter the facets based on a category based on all the other categories
- i18n-global: add compile-catalog fuzzy (#323)

Version 2.3.1 (2023-11-10)

- facets: apply some fixes on nested filter

Version 2.3.0 (2023-11-07)

- facets: add a new filter for nested filters

Version 2.2.0 (2023-03-03)

- remove deprecated flask-babelex dependency and imports
- upgrade invenio-i18n

Version 2.1.0 (2022-10-03)

- Add support to OpenSearch v2
- Remove `search_type` param

Version 2.0.2 (2022-09-28)

- Bump invenio-indexer

Version 2.0.1 (2022-09-27)

- Bump invenio-records

Version 2.0.0 (2022-09-24)

- Add support for OpenSearch
- Drop support for Elasticsearch < 7
- Upper pin Invenio dependencies
- Rename all occurrences of Elasticsearch to `search`
- Remove iterator from `MarshmallowErrors` class
- Breaking: rename func `check_elasticsearch` to `check_search`,
  conf `RECORDS_REST_ELASTICSEARCH_ERROR_HANDLERS` to
  `RECORDS_REST_SEARCH_ERROR_HANDLERS`
- Fix CI tests

Version 1.9.0 (2021-11-29)

- Fixes `MarshmallowErrors.get_body` due to Werkzeug 2.0.x changes
- Upgrade invenio packages
- Upgrade cite-proc

Version 1.8.0 (2020-12-09)

- Adds Cache-Control: 'no-cache' header to 200 responses to
  ensure that browsers will not cache responses client side.

- Unpins the ftfy library.

Version 1.7.2 (2020-08-28)

- Fixes an issue with record PID resolution error handling.
- URL PID converter is now "lazier" and initializes its internal resolver via a
  property.
- Fixes classifiers to reflect Python verisons

Version 1.7.1 (released 2020-05-07)

- Sphinx set to ``<3`` because of errors related to application context
- Stop using example app

Version 1.7.0 (released 2020-03-13)

- Removes support for python 2.7
- Centralises management of Flask dependency by invenio-base

Version 1.6.4 (released 2019-12-11)

- Fixes loaders error payload to add support for nested fields

Version 1.6.3 (released 2019-11-19)

- Upgrades `six` package minimal version

Version 1.6.2 (released 2019-10-02)

- Changes PID field in Marshmallow Schema to String instead of Integer.

Version 1.6.1 (released 2019-09-23)

- Fixes wrong `size` url arg upper limit
- Upgrades `invenio-rest` dependency

Version 1.6.0 (released 2019-09-11)

- Adds support to serialization using Marshmallow with versions 2 and 3
- Enables to choose response search serializer via url argument

Version 1.5.0 (released 2019-08-02)

- Adds improved support for infinite scroll
- Adds ES7 support
- Adds CSV serializer
- Adds ``record`` to marshmallow context
- Uses html allowed tags and attributes for bleach from config

Version 1.4.2 (released 2019-05-07)

- Marshmallow JSON schema: add getter method to customize and retrieve the PID
  field name per schema.

Version 1.4.1 (released 2019-04-02)

- Added ``RECORDS_REST_DEFAULT_RESULTS_SIZE`` variable to change the default
  ``size`` of the search results. The default value remains ``10``.

Version 1.4.0 (released 2019-02-22)

- Removed unused resolver parameter from views classes.
- Improved documentation of record_class in URL patterns.

Version 1.3.0 (released 2018-12-14)

- Enhance Elasticsearch error handling.
- Refactor Marshmallow schemas to allow PID injection.

Version 1.2.2 (released 2018-11-16)

- Changes ``str`` to ``text_type`` on filter dsl.

Version 1.2.1 (released 2018-09-17)

- Adds source filtering support for ES 5.

Version 1.2.0 (released 2018-08-24)

- Adds PersistentIdentifier field to handle record PIDs.
- Adds Nested class to improve reporting of validation errors.

Version 1.1.2 (released 2018-06-26)

- Rename authentication of GET operation over
  RecordsListResource from 'read_list' to 'list'.

Version 1.1.1 (released 2018-06-25)

- Adds authentication to GET operation over
  RecordsListResource.
- Bumps invenio-db version (min v1.0.2).

Version 1.1.0 (released 2018-05-26)

- Moves RecordSchemaJSONV1 marshmallow schema from
  invenio_records_rest.serializers.schemas to
  invenio_records_rest.schemas.
- Fixes missing API documentation.
- Adds blueprint factory (requires Invenio-Base v1.0.1+).
- Adds marshmallow loaders, fields and schemas.

Version 1.0.1 (released 2018-03-27)

- Fixes unicode query handling
- Fixes Datacite v4.1 serialization

Version 1.0.0 (released 2018-03-23)

- Initial public release.
