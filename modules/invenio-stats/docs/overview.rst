..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Overview
--------

Invenio-Stats enables an Invenio instance to generate statistics and
access them via a REST API.

Invenio-Stats is based on the requirements gathered from different Invenio
based services. A summary can of those requirements can be found here:
`Invenio-Stats requirements <https://github.com/inveniosoftware/invenio-stats/wiki/Requirements>`_

This module is composed of many different parts, all of them being optional.
The main parts are:

* **the generation of events** which can be later processed.

* **the processing of events**. *Example: filtering out downloads made by bots,
  and then indexing remaining events in Elasticsearch.*

* **the compression of events**. Querying too many events in an Elasticsearch
  cluster can put a big strain on it. Thus doing a compression of events makes
  later queries faster. *Example: aggregating the number of downloads per day*.

* **the querying of statistics via a REST API**. This enables a standardized
  way of querying statistics.

1. Event generation and processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Statistics can measure the occurence of an event within the application (e.g.
file downloads, record views) by plugging multiple components like this:

.. graphviz::

    digraph G {
    rankdir=LR;

    Module [
        label="Other Module",
        width=1.5,
        height=3,
        fixedsize=true, // don't allow nodes to change sizes dynamically
        shape=rectangle
        color=grey,
        style=filled,
    ];
    Module -> Emitter [label="(1) signals"];

    subgraph cluster_invenio_stats {
        rank=same;
        fontsize = 20;
        label = "Invenio Stats";
        style = "solid";
        Emitter [label="Event\nEmitter", shape="parallelogram"];

        subgraph cluster_celery {
            label="Celery Tasks"
            style="dashed"
            fontsize = 15;
            Processor [label=<Events<BR/>Indexer<BR/><FONT POINT-SIZE="10">Event Processor</FONT>>, shape=Mcircle]
            Aggregator [label="Event\nAggregator", shape=Mcircle]
        }
    }
    Queue [label="Message Queue\n(RabbitMQ)", margin=0.2, shape="cds"];
    Elasticsearch [label="Elasticsearch", shape="cylinder", height=2];

    Emitter -> Queue [label="(2) events"];

    Queue -> Processor [label="(3) events"];

    Processor -> Elasticsearch [label="(4) processed events"];

    Aggregator -> Elasticsearch [label="(5) processed events" dir=back];
    Aggregator -> Elasticsearch [label="(6) aggregated statistics"];
    }

Invenio-Stats provides an easy way to generate events whenever a signal is
sent. However, it is possible to generate your own events.

EventsIndexer is just one example of events processor. As other components it
can be replaced.

2. Querying
~~~~~~~~~~~

The statistics are accessible via REST API.

.. graphviz::

    digraph G {
    rankdir=LR;
    WEB [
        label="WEB",
        shape=rectangle,
        color=grey,
        style=filled,
        width=1.5,
        height=3,
    ]
    WEB -> REST [label="(1) HTTP request"];
    REST -> WEB [label="(6) HTTP response"];


    subgraph cluster_invenio_stats {
        fontsize = 20;
        label = "Invenio Stats";
        style = "solid";
        REST [
            label="Statistics\nREST API\n/api/stats/",
            shape=rectangle,
            width=1.5,
            height=3,
        ]
        Query [label="Aggregation\nQuery", shape="Msquare"]
        REST -> Query [label="(2) query"];
        Query -> REST [label="(5) statistics"];
    }
    Elasticsearch [label="Elasticsearch", shape="cylinder", height=2];
    Query -> Elasticsearch [label="(3) query"];
    Elasticsearch -> Query [label="(4) stats"];
    }

Not every statistic of interest has to be derived from Elasticsearch. It is
possible to retrieve statistics by just running and SQL query on the database.
Examples:

* number of users per community.

* number of records per collection.

* number of records under embargo.

* number of new files per month.

Elasticsearch is mainly used for events which happen very often and thus
generate a big volume of data. Invenio-Stats provide components to easily
generate statistics out of events previously aggregated in Elasticsearch.
