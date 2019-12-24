..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.


===============
 Invenio-Stats
===============

.. image:: https://img.shields.io/github/license/inveniosoftware/invenio-stats.svg
        :target: https://github.com/inveniosoftware/invenio-stats/blob/master/LICENSE

.. image:: https://img.shields.io/travis/inveniosoftware/invenio-stats.svg
        :target: https://travis-ci.org/inveniosoftware/invenio-stats

.. image:: https://img.shields.io/coveralls/inveniosoftware/invenio-stats.svg
        :target: https://coveralls.io/r/inveniosoftware/invenio-stats

.. image:: https://img.shields.io/pypi/v/invenio-stats.svg
        :target: https://pypi.org/pypi/invenio-stats

Invenio module for collecting statistics.

This module provides the components for **statistical data processing and
querying**.

The most common statistics measure the occurence of events in an invenio
application, e.g. file downloads, record views and others. Invenio-stats
provides the tools to transform, register, compress and query those events.
However, statistics can be fully customized and directly query the database.

The services it uses are:

- RabbitMQ for buffering incoming events.
- Elasticsearch for aggregating and searching events.

Further documentation is available on: https://invenio-stats.readthedocs.io/
