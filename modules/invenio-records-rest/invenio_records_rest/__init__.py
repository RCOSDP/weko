# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

u"""REST API for Records.

Invenio-Records-REST is a core component of Invenio which provides configurable
REST APIs for searching, retrieving, creating, modifying and deleting records.

The module uses Elasticsearch as the backend search engine and builds on top
a REST API that supports features such as:

- Search with sorting, filtering, aggregations and pagination, which allows the
  full capabilities of Elasticsearch to be used, such as geo-based quering.
- Record serialization and transformation (e.g., JSON, XML, DataCite,
  DublinCore, JSON-LD, MARCXML, Citation Style Language).
- Pluggable query parser.
- Tombstones and record redirection.
- Customizable access control.
- Configurable record namespaces for exposing different classes of records
  (e.g., authors, publications, grants, ...).
- CRUD operations for records with support for persistent identifier minting.
- Super-fast completion suggesters for implementing Google-like instant
  autocomplete suggestions.

The REST API follows best practices and supports, e.g.:

- Content negotiation and links headers.
- Cache control via ETags and Last-Modified headers.
- Optimistic concurrency control via ETags.
- Rate-limiting, Cross-Origin Resource Sharing, and various security headers.

The Search REST API works as **the** central entry point in Invenio for
accessing records. The REST API in combination with, e.g., Invenio-Search-UI/JS
allows to easily display records anywhere in Invenio and still only maintain
one single search endpoint.

For further extending the REST API take a look at the guide in Invenio-REST:
http://invenio-rest.readthedocs.io/en/latest/.

Basics
------

Records
~~~~~~~
A record in Invenio consists of a structured collection of fields and values
(metadata), which provides information about other data. The format of these
records is defined by a schema, which is represented in Invenio as JSONSchema.
Since the format of a record can change over time, it can be associated to
different JSONSchema versions. For more information on records and schemas
visit
`InvenioRecords <http://invenio-records.readthedocs.io/en/latest/index.html>`_.

Elasticsearch
~~~~~~~~~~~~~

Records are represented as JSON documents internally in Elasticsearch and
grouped under an index specified in the configuration, an index represents a
collection of documents with similar characteristics. Because the shape of a
record can change with time, there is the possibility to group indices with
the same meaning but with different versions under an alias. Besides, aliases
can help for grouping and easy filtering purposes. The structure, internal
fields of the documents, along with indexing preferences can be defined by
mappings, applied to specific indices. A mapping is a JSON file, which is
loaded during initialization by Invenio-Search from a path defined by an
entrypoint. The layout of a mapping can highly affect the search and indexing
performance.

Initialization
--------------

First create a Flask application:

>>> from flask import Flask
>>> app = Flask('myapp')
>>> app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
>>> app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Initialize the required dependencies:

>>> from invenio_db import InvenioDB
>>> from invenio_rest import InvenioREST
>>> from invenio_pidstore import InvenioPIDStore
>>> from invenio_records import InvenioRecords
>>> from invenio_records_rest import InvenioRecordsREST
>>> from invenio_search import InvenioSearch
>>> from invenio_indexer import InvenioIndexer
>>> from invenio_records_rest.utils import PIDConverter
>>> ext_db = InvenioDB(app)
>>> ext_rest = InvenioREST(app)
>>> ext_pidstore = InvenioPIDStore(app)
>>> ext_records = InvenioRecords(app)
>>> ext_search = InvenioSearch(app)
>>> ext_indexer = InvenioIndexer(app)
>>> app.url_map.converters['pid'] = PIDConverter

In order for the following examples to work, you need to work within a Flask
application context so let’s push one:

>>> ctx = app.app_context()
>>> ctx.push()

Also, for the examples to work we need to create the database and tables (note
that in this example we use an in-memory SQLite database):

>>> from invenio_db import db
>>> db.create_all()

Configuration
-------------

`Namespaces` are an important concept in Invenio-Records-REST. You can think of
them as a way of grouping related metadata.
Imagine a `namespace` called ``records`` and another ``authors``. You could
use ``records`` to provide bibliographic metadata and ``authors`` for author
metadata. A namespace is mapped one to one to Elasticsearch indices or
aliases.

In Invenio-Records-REST these namespaces are mapped to endpoints (i.e.,
``/records/`` or ``/authors/``). Inside these namespaces you can make
unique reference to specific records thanks to the persistent identifiers.
Going back to our general example, a persistent identifier
for our namespace ``authors`` could be an `ORCID <https://orcid.org/>`_ and a
specific author would be identified by an endpoint like
``/authors/0000-0002-1825-0097``.

The just above mentioned persistent identifiers need ``minters`` and
``fetchers`` so Invenio-Records-REST knows how to create and retrieve them. A
`minter <http://invenio-pidstore.readthedocs.io/en/latest/usage.html#minters>`_
is a small function which makes a record unique under a given schema
(i.e. DOI, ORCID), so this identifier and any other field needed will be added
to the record metadata. A
`fetcher <http://invenio-pidstore.readthedocs.io/en/latest/usage.html#fetchers>`_
on the other hand, is a small function that retrieves records minted
following a certain persistent identifier schema such as DOI.

Among other preferences, routes, PID types, as well as search specific options
are customizable through configuration. The following dictionary shows the
default options in the out of the box minimal configuration.


>>> from invenio_indexer.api import RecordIndexer
>>> from invenio_search import RecordsSearch
>>> app.config.update({'RECORDS_REST_ENDPOINTS': dict(recid=dict(
...     pid_type='recid',
...     pid_minter='recid',
...     pid_fetcher='recid',
...     search_class=RecordsSearch,
...     indexer_class=RecordIndexer,
...     search_index=None,
...     search_type=None,
...     record_serializers={
...         'application/json': ('invenio_records_rest.serializers'
...                              ':json_v1_response'),
...     },
...     search_serializers={
...         'application/json': ('invenio_records_rest.serializers'
...                              ':json_v1_search'),
...     },
...     list_route='/records/',
...     item_route='/records/<pid(recid):pid_value>',
...     default_media_type='application/json',
...     max_result_window=10000,
...     error_handlers=dict(),
...     ))}
... )
>>> ext_records_rest = InvenioRecordsREST(app)

This configuration is not limited to only one endpoint, we could define as
many as we want. This is an idea on how ``/authors/`` would be implemented:

>>> app.config.update({'RECORDS_REST_ENDPOINTS': dict(authors=dict(
...    pid_type='orcid',
...    # ...,
...    list_route='/authors/',
...    item_route='/authors/<pid(orcid):pid_value>',
...    # ...,
... ))})

Demo data
~~~~~~~~~
Once you have this code you can run the application and create some records:

.. code-block:: console

 $ curl -L -H 'Content-Type:application/json' -d '{"title": "Test Record 1"}' -XPOST localhost:5000/records
 $ curl -L -H 'Content-Type:application/json' -d '{"title": "Test Record 2"}' -XPOST localhost:5000/records

Searching
---------
Invenio-Records-REST offers a rich set of fundamental search operations using
query strings, filters, sorting and pagination and also more advanced
operations including aggregations and suggestions.

``/records/?q=&size=10&page=1&sort=bestmatch&type=test``

Faceted Search
~~~~~~~~~~~~~~

Faceted search is enabled through filters and aggregations. It can be used to
obtain subsets of documents which meet certain criteria, group results by
categories, and provide an easy to navigate faceted menu.

``/records/?type=test&type=anotherhvalue/``


Aggregations
++++++++++++
By exposing the Elasticsearch API by default, we can use the advanced
features it provides, such as the `aggregations framework
<https://www.elastic.co/guide/en/elasticsearch/reference/5.6/search-aggregations.html>`_.

These features include:

- `bucketing <https://www.elastic.co/guide/en/elasticsearch/reference/5.6/search-aggregations-bucket.html>`_
  "used to group the documents by a certain criterion".
- `metric <https://www.elastic.co/guide/en/elasticsearch/reference/5.6/search-aggregations-metrics.html>`_
  "used to create different types of metrics from values extracted from the documents
  being aggregated".
- `matrix <https://www.elastic.co/guide/en/elasticsearch/reference/5.6/search-aggregations-matrix.html>`_
  "used to produce a matrix result based on the values extracted from the requested document fields".
- `pipeline <https://www.elastic.co/guide/en/elasticsearch/reference/5.6/search-aggregations-pipeline.html>`_
  "used to aggregate the output of other aggregations and their associated metrics".


Filters
+++++++
Filters can be applied at different points of a query having different effects
for aggregations, but not for search queries.


To set the aggregations and filters you want you can modify the
`RECORDS_REST_FACETS`.

>>> from .facets import terms_filter
>>> app.config['RECORDS_REST_FACETS'] = {
...     'index_name': {
...         'aggs': {
...             'type': {'terms': {'field': 'type'}}
...         },
...         'post_filters': {
...             'type': terms_filter('type'),
...         },
...         'filters': {
...             'typefilter': terms_filter('type'),
...         }
...     }
... }

.. note::

    Unlike the other configurations the ``index_name`` does not refer,
    to the namespace ``recid``, but the actual Elasticsearch index or alias.

Sorting
~~~~~~~
Sorting is based by default on a relevance score, but this can
be configured as well. The following ways are possible:

- `Sorting by field values <https://www.elastic.co/guide/en/elasticsearch/guide/current/_sorting.html#_sorting_by_field_values>`_
- `Multilevel sorting <https://www.elastic.co/guide/en/elasticsearch/guide/current/_sorting.html#_multilevel_sorting>`_
- `Sorting on multilevel fields <https://www.elastic.co/guide/en/elasticsearch/guide/current/_sorting.html#_sorting_on_multivalue_fields>`_

This can be configured through the `RECORDS_REST_SORT_OPTIONS`:

>>> RECORDS_REST_SORT_OPTIONS = dict(
...    records=dict(
...        bestmatch=dict(
...            title='Best match',
...            fields=['_score'],
...        default_order='desc',
...            order=1,
...        ),
...        mostrecent=dict(
...        title='Most recent',
...            fields=['_created'],
...            default_order='asc',
...            order=2,
...        ),
...    )
... )

The default configuration will return the results sorted by the best match when
filtering by a given query, or sorted by their creation date when querying
all results:

>>> RECORDS_REST_DEFAULT_SORT = dict(
...    records=dict(
...        query='bestmatch',
...        noquery='mostrecent',
...    )
... )

Query parser
~~~~~~~~~~~~

The search syntax for the various queries is powered by the query parser used.
Internally the query parser is referred to as the search factory.
This defaults to the `Q() <https://www.elastic.co/guide/en/elasticsearch/reference/2.4/query-dsl-query-string-query.html>`_ parser
from elasticsearch_dsl.

``/records/?q=``

Its features include:

- field names and operators
- exists/missing
- ranges
- wildcards and regular expressions
- fuzziness
- proximity search
- boosting


A custom query parser can also be plugged in by setting the
``search_factory_imp`` option in ``RECORDS_REST_ENDPOINTS`` to point to the
function implementing it:

>>> from invenio_records_rest.query import default_search_factory
>>> from elasticsearch_dsl.query import Q
...
>>> def my_query_parser(qstr=None):
...     if qstr:
...         return Q('query_string', query=qstr)
...     return Q()
...
>>> def my_search_factory(*args, **kwargs):
...     return default_search_factory(*args,
...                                   query_parser=my_query_parser, **kwargs)
...
>>> RECORDS_REST_ENDPOINTS = {
...     'recid': {
...         # ...
...         'search_factory_imp': my_search_factory,
...      }
... }

Suggesters
~~~~~~~~~~
Through the ``/records/_suggest?text=`` entrypoint the suggest feature of
elasticsearch is exposed. The suggest feature suggests similar looking terms
based on a provided text by using a suggester. This endpoint is
configurable and takes a dictionary specifying the suggestion fields and
their url query parameters. The field names are linked to the ones
specified in the elasticsearch schema.

Advanced customization
~~~~~~~~~~~~~~~~~~~~~~

- Invenio-Records-REST can be fine-tuned in terms of search capabilities
  through the ``search_factory`` configuration. As an example, we could:

>>> from invenio_records_rest.query import es_search_factory
>>> def custom_search_factory(*args, **kwargs):
...     print(args)
...     return es_search_factory(*args, **kwargs)
...
>>> RECORDS_REST_ENDPOINTS = dict(
...    recid=dict(
...        search_factory_imp=custom_search_factory
...    )
... )

  Creating a custom search factory can enable full control over Elasticsearch's
  Search API. Some of the features available include rank evaluation, post
  filters, highlighting, index boosting among others. For the full list see
  the full Elasticsearch documentation for the `Search API
  <https://www.elastic.co/guide/en/elasticsearch/reference/current/search.html>`_.

- As the default search behaviour can be adjusted, Invenio-Records-REST
  also offers the possibility to define custom search exceptions.

>>> from invenio_records_rest.errors import InvalidQueryRESTError
>>> def custom_query_parsing_error(error):
...     description = 'There is an error in your query syntax.'
...     return InvalidQueryRESTError(description=description).get_response()
...
>>> RECORDS_REST_ELASTICSEARCH_ERROR_HANDLERS = dict(
...    query_parsing_exception=custom_query_parsing_error
... )

- `Max Results Window`
  In the case where you execute a query and the number of results exceed the
  ``max_results_window`` you will get a 400 error. This limit is passed to
  Elasticsearch and can be configured by the ``RECORDS_REST_ENDPOINTS``, by
  default it is set to 10000.

- `Fetching records from Elasticsearch`
  To retrieve records in the REST API we make use of fetchers. These functions
  take the record unique identifiers and return FetchedPID objects, which
  consist of the Persistent Identifier and the record data.
  The fetcher for each endpoint in Invenio-Records-REST can be configured
  and it is defined by its name, default is ``recid``. To register a new
  fetcher, add the ``invenio_pidstore.fetchers`` entrypoint in the
  ``setup.py`` of a module and point it to the fetcher function. For more
  information on fetchers, see the corresponding paragraph in
  `Invenio-PIDStore <https://invenio-pidstore.readthedocs.io/en/latest/api.html#module-invenio_pidstore.fetchers>`_.

  The fetchers by default will query the database, but this can be redirected
  to Elasticsearch according to the needs of the application. More
  specifically, the fetcher takes as a parameter a provider object,
  which is responsible for the querying. In order to change the behavior of
  the GET one would write a new provider class to
  override the ``get()`` method of the ``BaseProvider`` and query
  Elasticsearch.

Serialization
-------------
A key feature of invenio-records-rest is the ability to transform
records from JSON to other formats. Through this process the content
of records can be enriched, removed of sensitive information when required
or be export in standardized bibliographic formats like DataCite, DublinCore.

Content negotiation
~~~~~~~~~~~~~~~~~~~
The serializer which will be used is chosen by the
MIME type specified in the headers of the request. There can be different
serializers for the multiple results returned by a search query, and the
single result returned when querying for specific records.
This can be configured in the following part of the records rest endpoints:

>>> RECORDS_REST_ENDPOINTS = dict(
...    recid=dict(
...       record_serializers={
...          'application/json':('invenio_records_rest.serializers'
...                              ':json_v1_response'),
...       },
...       search_serializers={
...          'application/json':('invenio_records_rest.serializers'
...                              ':json_v1_search'),
...       }
...    )
... )

With the usage of MIME types it is also possible to specify the
version of a given serialization, as serialization schemas can have
newer versions over time. More specifically, if we have created two
serializers, one for DataCite's version 3.1 metadata schema and one
for version 4.1, we can specify which one we require in the
``Accept`` http header field. For example, if we have
set in the configuration:

>>> record_serializer={
...    'application/datacite.v3.1+xml': ('invenio_records_rest.serializers'
...                                      ':datacite_response_v31'),
...    'application/datacite.v4.1+xml': ('invenio_records_rest.serializers'
...                                      ':datacite_response_v41'),
... }


Then we can send an http request with the http headers containing
``Accept:application/datacite.v3.1+xml`` or
``Accept:application/datacite.v4.1+xml`` and receive the output
in the different formats.

Workflow
~~~~~~~~
The serializers typically will follow a certain number of steps
to process records.
For example, for records returned as results to a search query the format
is dictated from Elasticsearch, while for requests for specific records
the format comes from the database. The output has to be consistent so a
first step is to create the different methods to syncronize the data which
will be returned. The abstract classes with the boilerplate for this workflow
are in `invenio_records_rest.serializers.base`.

Additionally, we can define more steps to anonymize the data, if sensitive
information need to be excluded or enrich it, by adding extra fields.

Citation formatting
~~~~~~~~~~~~~~~~~~~
A common application of serialization is to output a citation from the
record content. For this task the ``CiteprocSerializer``, which in turn is
based on the `citeproc-py <https://github.com/brechtm/citeproc-py>`_
module, is used. To produce the citation text, a schema is required which
defines what fields have to be present. For example the following schemas
will create a citation with the title, abstract and authors of a given record:


>>> from marshmallow import Schema, fields
>>> class AuthorSchema(Schema):
...    family = fields.Method('get_family_name')
...
...    def get_family_name(self, obj):
...        return obj['name']
>>>
>>> class SimpleRecordSchema(Schema):
...    id = fields.Integer(attribute='pid.pid_value')
...    type = fields.Method('get_type')
...    title = fields.Str(attribute='metadata.title')
...    abstract = fields.Str(attribute='metadata.description')
...    author = fields.List(fields.Nested(AuthorSchema),
...                         attribute='metadata.creators')
...
...    def get_type(self, obj):
...        return 'article'


Also, we need to create a serializer to use the serializer
``CiteprocSerializer``:

>>> from invenio_records_rest.serializers.json import JSONSerializer
>>> from invenio_records_rest.serializers.citeproc import CiteprocSerializer
>>> from invenio_records_rest.serializers.response import record_responsify
>>> csl_v1 = JSONSerializer(SimpleRecordSchema, replace_refs=True)
>>> citeproc_v1 = CiteprocSerializer(csl_v1)
>>> citeproc_v1_response = record_responsify(citeproc_v1, 'text/x-bibliography')

and register it in our ``RECORDS_REST_ENDPOINTS``
for ``Accept:text/x-bibliography``:

>>> RECORDS_REST_ENDPOINTS = dict(
...    recid=dict(
...       record_serializers={
...          'application/json':('invenio_records_rest.serializers'
...                              ':json_v1_response'),
...          'text/x-bibliography':('invenio_records_rest.serializers'
...                                 ':citeproc_v1_response'),
...       }
...    )
... )


Then, we can create a record with:

.. code-block:: console

   $ curl -H "Content-Type:application/json" -d '{"title":"Sample Record", "creators":[{"name": "First Name, Last Name"}], "description": "Abstract"}' -XPOST <HOST>/records/


and retrieve the citation for it with:

.. code-block:: console

    $ curl -H "Accept:text/x-bibliography" -XGET <HOST>/records/<PID>
    First Name, Last Name, Sample Record.


In a similar way, schemas can be defined to be used with a serializer,
inheriting from the ``MarshmallowMixin``, and do any type of transformation
to the JSON objects that are exchanged in the REST API.

Data formats
~~~~~~~~~~~~
Typical serialization formats are:

- JSON: JSON-LD, CSL
- XML: DataCite, DublinCore, MARCXML
- Text: Citation formatting

For some examples on the implementation of these serializers you can see
the ones present in different invenio instances such as:

- `CDS-Videos <https://github.com/CERNDocumentServer/cds-videos/tree/cdslabs_qa/cds/modules/records/serializers>`_
- `Zenodo <https://github.com/zenodo/zenodo/tree/master/zenodo/modules/records/serializers>`_


Tombstones and redirection
--------------------------

When it comes to manage changes regarding PIDs such as deletions and
redirections, Invenio-Records-REST offers ways to:

* Customize tombstones:

>>> from invenio_records_rest.errors import PIDDeletedRESTError
>>> def custom_deleted_pid_error_handler(error):
...     record = error.pid_error.record or {}
...     description={
...         'status': 410,
...         'message': error.description,
...         'removal_reason': record.get('removal_reason')}
...     return PIDDeletedRESTError(description=description).get_response()
...
>>> app.config.update({'RECORDS_REST_ENDPOINTS':
...   {'recid':
...      {'error_handlers':
...         {'PIDDeletedRESTError': custom_deleted_pid_error_handler}
...      }
...   }
... })

* Manage redirects:

 (reference with PIDstore, explain how it scans RECORDS_REST_ENDPOINTS to pick
  the target endpoint)

Access control
--------------

Invenio-Records-REST is highly customizable in terms of access control. This
customization can be done by using permission factories. By default two
permission factories are offered within the package, ``allow_all`` and
``deny_all``. For example, if we wanted to allow creation and retrieval
of records by any user, and deny deletion and update for all users, we would
to the following:

>>> from invenio_records_rest.utils import allow_all, deny_all
>>> RECORDS_REST_ENDPOINTS = dict(
...    recid=dict(
...        create_permission_factory_imp=allow_all,
...        delete_permission_factory_imp=deny_all,
...        update_permission_factory_imp=deny_all,
...        read_permission_factory_imp=allow_all,
...    )
... )

Note: In order to have a full setup with access controll you should install
`Invenio-Accounts <https://invenio-accounts.readthedocs.io/en/latest/>`_.

It is also possible to filter search results based on the status of the
requesting user. A simple example is when a normal logged in
user searches for all records and we want to return a list of all records,
excluding the ones that have been set to closed access from their creators.
These records are also referred to as under embargo, and it is a typical
scenario when an author wants to publish an article after a given date.
An indexed record will include list of owners, so this procedure can be
summarized in creating a new search class that includes this permission check.
An example of such a search class is the following:

>>> from flask_login import current_user
>>> def deposits_filter():
...    return Q(
...       'match', **{'_deposit.owners': getattr(current_user, 'id', 0)}
...    )
...
>>> class CustomSearch:
...    class Meta:
...       index = 'deposits'
...       # ...
...       default_filter = deposits_filter

It filters out records that are in a
deposit state. The corresponding endpoint's configuration:

>>> DEPOSIT_REST_ENDPOINTS = {
...    'depid': {
...       # ...,
...       'search_class': 'invenio_records_rest.search:CustomSearch',
...       # ...,
...    }
... }

The following section shows the way to create permission factories, and for
more examples you can directly see the ones used in production in the
Invenio instances:

- `CDS's permission factories <https://github.com/CERNDocumentServer/cds-videos/blob/cdslabs_qa/cds/modules/records/permissions.py>`_
- `Zenodo's permission factories <https://github.com/zenodo/zenodo/blob/master/zenodo/modules/records/permissions.py>`_

Factories
~~~~~~~~~

If the default access control factories are not enough for your use case,
you can always create your own permission factories. Here is an example on how
to quickly configure the instance to allow the creation, deletion, update and
read only on records with the title ``Hello World``.

(for creating records )

>>> def permission_check_factory(record):
...     record = record or {}
...     def can(self):
...         if kwargs.get('record').get('title') == 'Hello World':
...             return True
...     return type('Check', (), {'can': can})()
...
>>> RECORDS_REST_ENDPOINTS=dict(
...    recid=dict(
...        create_permission_factory_imp=permission_check_factory,
...        delete_permission_factory_imp=permission_check_factory,
...        update_permission_factory_imp=permission_check_factory,
...        read_permission_factory_imp=permission_check_factory,
...    )
... )

For more information on access restriction you can read
`Invenio-Access <http://invenio-access.readthedocs.io/en/latest/>`_
documentation.

Deserialization
---------------
Requests carrying out CRUD operations are sent along with data, which need to
be transformed to the internal objects for processing to occur.
This is the job of the loaders. These work in the reverse direction of the
serializers, and are confiurable as well, in the same way.

Following the deserialization of the data passed in the request, a record
or deposit has to be attained so the operation can be performed.
To fectch the corresponding object a fetcher is used, typically provided
by Invenio-PIDStore.
"""

from __future__ import absolute_import, print_function

from .ext import InvenioRecordsREST
from .proxies import current_records_rest
from .version import __version__

__all__ = ('__version__', 'current_records_rest', 'InvenioRecordsREST')
