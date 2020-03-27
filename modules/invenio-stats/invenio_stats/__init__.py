# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

r"""Invenio module for collecting statistics.

1. Event processing
~~~~~~~~~~~~~~~~~~~

Invenio-Stats enables to generate **statistics based on Events**. Events
are just pieces of data sent to Invenio-Stats which are then aggregated
and queried.

1.1. Registering an Event type
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each event has a type. Example of event types:

    * ``file-download``: a file has been downloaded.
    * ``record-view``: a record has been read by a user.

A module needs to declare all the event types it provides.

First create a function which will list all the events provided by your Invenio
module as well as their default configuration.

.. code-block:: python

    # in your_module/registrations.py
    def register_events():
       return [dict(event_type='file-download',
                    templates='contrib/file-download',
                    processor_class=EventsIndexer,
                    processor_config=dict(
                       preprocessors=[
                           flag_robots,
                           anonymize_user,
                           build_file_unique_id
                       ]
                    )),
               ...

The ``templates`` attribute defines the Elasticsearch templates that will be
used for indexing the events. The processor related attributes will be
explained later.

Once you've created the function you need to declare it in the ``setup.py``
under the entrypoint ``invenio_stats.events``.

.. code-block:: python

    # in setup.py
    ...
    entry_points={
        'invenio_stats.events': [
            'invenio_stats = '
            'invenio_stats.contrib.registrations:register_events'
        ]
    }
    ...

The function enables to dynamically add new events using for example
information from the database.

1.2. Enabling an Event type
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Only enabled events will be processed by your Invenio instance. Disabled events
will just be discarded. This enables to have many events provided by different
modules and to enable only required events in your Invenio overlay.

Events are enabled in the configuration like this:

.. code-block:: python

    # in config.py
    STATS_EVENTS = {
        'file-download': {},
    }

An Invenio overlay should list all the events it wants to process.

**Once an event is enabled, a queue is registered in Invenio-Queues.** This
queue will store all events before they are processed.

1.3. Overriding an event's default configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is possible to override the default configuration of an event by specifying
different ``templates``, ``processor_class``, ``event_builders``, or
``processor_config`` in the ``STATS_EVENTS`` config variable:

.. code-block:: python

    STATS_EVENTS = {
        'file-download': dict(
            templates: 'your_module.mappings.stats.file_download',
            event_builders=[
                'invenio_stats.contrib.event_builders.file_download_event_builder'
            ],
            processor_class: your_module.processors.CustomEventsIndexer,
            processor_config=dict(
                preprocessors=[
                    'invenio_stats.processors:flag_robots',
                    'invenio_stats.processors:anonymize_user',
                    'invenio_stats.contrib.event_builders:build_file_unique_id',
                ],
                # Keep only 1 file download for each file and user every
                # 30 sec.
                double_click_window=30,
                # Create one index per month which will store file download
                # events.
                suffix='%Y-%m'
            ))
    }

This is useful when you want to change how an event is created or processed.

Examples of customization:
    * add more fields in the event so that you can later aggregate by those
      fields.
    * store the events in a different database.
    * filter out some events.

1.4. Emitting Events
^^^^^^^^^^^^^^^^^^^^

Events can be generated either from signals or directly in any module.

In order to automatically generate events when a signal is sent, add ``signal``
to the ``STATS_EVENTS`` configuration. The following configuration shows how to
generate a ``file-download`` event when the ``file_downloaded`` signal is
emitted:

.. code-block:: python

    # in config.py
    STATS_EVENTS = {
        'file-download': {
            'signal': 'invenio_files_rest.signals.file_downloaded',
            'event_builders': [
                'invenio_stats.contrib.event_builders.file_download_event_builder'
            ]
        },
    }

The ``event_builders`` parameter is a list of functions which will be used to
create and enrich the event using the signal information. You can also
completely skip sending an event by returning ``None`` from any of the
functions.

If you prefer to generate your event directly, here is an example:

.. code-block:: python

    from .proxies import current_stats

    event = dict(
        timestamp=datetime.datetime.utcnow().isoformat(),
        mydata='somedata'
    )

    current_stats.publish('my-event-name', [event])

1.5. Emitting Signals
^^^^^^^^^^^^^^^^^^^^^

There are different ways of emitting events. One of them is to emit an event
every time a signal is triggered. Invenio modules already send many different
signals. If no signal exists it is possible to emit your own signals.

.. code-block:: python

    # in signals.py
    from blinker import Namespace

    _signals = Namespace()
    file_downloaded = _signals.signal('file-downloaded')

    # at the point where the event happens
    file_downloaded.send(current_app._get_current_object(), obj=obj)

Note that this is optional. It is also possible to directly emit your own
events without using signals.

It is possible to completely disable the signal handling by setting
``STATS_REGISTER_RECEIVERS = False`` in the configuration.

1.6. Event Processing
^^^^^^^^^^^^^^^^^^^^^

Events are queued in AMQP queues, which are by default RabbitMQ queues. These
queues are handled by Invenio-Queues.

Invenio-Stats provides the task :py:func:`~invenio_stats.tasks.process_events`
which will process every event from the queues. It will instantiate a
**Processor** using the ``processor_class`` value from the event configuration
and pass the ``processor_config`` as parameters.

A processor is just a class which takes a *"queue"* as constructor parameter
and has a ``run()`` method.

Invenio-Stats provides the processor
:py:class:`~invenio_stats.processors.EventsIndexer` which reads events from
the queue and indexes them in Elasticsearch. This processor also accepts a list
of preprocessors which are run on every event. These preprocessors are used
to filter out or transform events before they are indexed.

It is possible to pass as a parameter a time window in seconds (10s by
default) within which, multiple events from the same user to the resource will
count as 1, allowing for more accurate statistics.

After the processing has taken place the event is indexed in Elasticsearch,
according to the template provided in the event registration. The index is
under the alias **events-stats-file-download**. It is also possible to index
events over different intervals (day, month or other).

Having multiple Elasticsearch indices enables the system administrator to
delete or archive old indices.

2. Aggregating
^^^^^^^^^^^^^^

The :py:class:`~invenio_stats.processors.EventsIndexer` processor indexes raw
events. Querying those events can put a big strain on the Elasticsearch
cluster. Thus Invenio-Stats provides a way to *compress* those events by
pre-aggregating them into meaningful statistics.

*Example: individual file downoalds events can be aggregated into the number of
file download per day and per file.*

Aggregations are registered in the same way as events, under the entrypoint
``invenio_stats.aggregations``.

.. code-block:: python

    # in setup.py
    ...
    entry_points={
        ...
        'invenio_stats.aggregations': [
            'invenio_stats = '
            'invenio_stats.contrib.registrations:register_aggregations'
        ],
    }

The function returns a dictionary with the configuration for the aggregations.

.. code-block:: python

    def register_aggregations():
        return [dict(aggregation_name='file-download-agg',
                     templates='contrib/aggregations/aggr-file-download',
                     aggregator_class=StatAggregator,
                     aggregator_config=dict(
                         client=current_search_client,
                         event='file-download',
                         aggregation_field='unique_id',
                         aggregation_interval='day',
                         copy_fields=dict(
                             file_key='file_key',
                             bucket_id='bucket_id',
                             file_id='file_id',
                         )
                     ))
                ]

An aggregator class must be specified. The dictionary ``aggregator_config``
contains all the arguments given to its construtor. An Aggregator class is
just required to have a ``run()`` method.

The default one is :py:class:`~invenio_stats.aggregations.StatAggregator`
and it aggregates events based on their ``timestamp`` field. It can aggregate
using different time windows and calculate different kinds of metrics using
`Elasticsearch Metric Aggregations <https://www.elastic.co/guide/en/elasticsearch/reference/5.6/search-aggregations-metrics.html>`_.
The events are retrieved from Elasticsearch and the resulting aggregations are
indexed in different Elasticsearch indices.

3. Querying
~~~~~~~~~~~

The statistics are accessible via REST API.

The queries are predefined and they are registered in the same way as events
and aggregations, under the entrypoint ``invenio_stats.queries``:

.. code-block:: python

    # in setup.py
    ...
    entry_points={
        ...
        'invenio_stats.queries': [
            'invenio_stats = '
            'invenio_stats.contrib.registrations:register_queries'
        ]
    }

Again the registering function returns the configuraton for the query:

.. code-block:: python

 def register_queries():
    return [
        dict(
            query_name='bucket-file-download-histogram',
            query_class=ESDateHistogramQuery,
            query_config=dict(
                index='stats-file-download',
                doc_type='file-download-day-aggregation',
                copy_fields=dict(
                    bucket_id='bucket_id',
                    file_key='file_key',
                ),
                metric_fields=dict(
                    count=('sum', 'count', {}),
                    avg_size=('avg', 'size', {}),
                ),
                required_filters=dict(
                    bucket_id='bucket_id',
                    file_key='file_key',
                )
            )
        )
   ...

The logic is identical, we specify the query class, each for a given statistic
and the parameters given to its constructor.

An example request fetching statistics is the following:

.. code-block:: bash

    $ curl -XPOST localhost:5000/stats \
        -H "Content-Type: application/json" \
        -d '{
               "mystat": {
                   "stat": "bucket-file-download-histogram",
                   "params": {
                       "start_date":"2016-12-18",
                       "end_date":"2016-12-19",
                       "interval": "day",
                       "bucket_id": 20,
                       "file_key": "file1.txt"}
                   }
           }'

The query format is the following:

.. code-block:: json

    {
        "<CUSTOM-QUERY-NAME1>": {
            "stat": "<STATISTIC-NAME-AS-DECLARED-IN-THE-CONFIGURATION>",
            "params": {
                "<PARAMETER-NAME1>": "PARAMETER-VALUE1",
                "<PARAMETER-NAME2>": "PARAMETER-VALUE2",
            }
        },
        "<CUSTOM-QUERY-NAME2>": {
            "stat": "<STATISTIC-NAME-AS-DECLARED-IN-THE-CONFIGURATION>",
            "params": {
                "<PARAMETER-NAME1>": "PARAMETER-VALUE1",
                "<PARAMETER-NAME2>": "PARAMETER-VALUE2"
            }
        }
    }

The response will have the format:

.. code-block:: json

    {
        "<CUSTOM-QUERY-NAME1>": {
            "<SOME-STATISTIC-KEY1>": "<SOME-STATISTIC-VALUE1>",
            "<SOME-STATISTIC-KEY2>": "<SOME-STATISTIC-VALUE2>"
        },
        "<CUSTOM-QUERY-NAME2>": {
            "..."
        }
    }

Each Query class is entitled to return custom key-values. However provided
Query classes already return a common pattern of fields.

The provided query classes are:

* :py:class:`~invenio_stats.queries.ESDateHistogramQuery`: histogram style
  aggregations.

* :py:class:`~invenio_stats.queries.ESTermsQuery`: aggregation by terms
  (unique field values).

Those two query classes have a common format for their results:

.. code-block:: json

    {
        "<CUSTOM-QUERY-NAME1>": {
            "type": "<STATISTIC-TYPE>",
            "key_type": "<AGGREGATION-TYPE (date, terms, ...)>",
            "SOME-OTHER-KEY": "<SOME-OTHER-VALUE>",
        }
    }

The field ``type`` is ``bucket`` for both as these are bucket aggregations (
see Elasticsearch documentation). The ``key-type`` field is used as a helper
for UI widgets so that they know how they can display the statistic
automatically.

Not every statistic of interest has to be derived from Elasticsearch. It is
possible to return statistics by just running an SQL query on the database.

4. Provided statistics
~~~~~~~~~~~~~~~~~~~~~~

Invenio-Stats provides some default statistics which can be found in
:py:mod:`invenio_stats.contrib.event_builders`.
"""

from __future__ import absolute_import, print_function

from .ext import InvenioStats
from .proxies import current_stats
from .version import __version__

__all__ = (
    '__version__',
    'current_stats',
    'InvenioStats',
)
