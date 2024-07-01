# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
# Copyright (C)      2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Proxy to the current stats module."""

import os

from flask_babelex import get_timezone
from kombu import Exchange

from .utils import default_permission_factory, weko_permission_factory

STATS_REGISTER_RECEIVERS = True
"""Enable the registration of signal receivers.

Default is ``True``.
The signal receivers are functions which will listen to the signals listed in
by the ``STATS_EVENTS`` config variable. An event will be generated for each
signal sent.
"""

PROVIDE_PERIOD_YEAR = 5

REPORTS_PER_PAGE = 10

STATS_EVENTS = {}
"""Enabled Events.

Each key is the name of an event. A queue will be created for each event.

If the dict of an event contains the ``signal`` key, and the config variable
``STATS_REGISTER_RECEIVERS`` is ``True``, a signal receiver will be registered.
Receiver function which will be connected on a signal and emit events. The key
is the name of the emitted event.

``signal``: Signal to which the receiver will be connected to.

``event_builders``: list of functions which will create and enhance the event.
    Each function will receive the event created by the previous function and
    can update it. Keep in mind that these functions will run synchronously
    during the creation of the event, meaning that if the signal is sent during
    a request they will increase the response time.

You can find a sampe of STATS_EVENT configuration in the `registrations.py`
"""

STATS_EXCLUDED_ADDRS = []
"""Fill IP Addresses which will be excluded from stats in `[]`"""

STATS_AGGREGATIONS = {}


STATS_QUERIES = {}


STATS_PERMISSION_FACTORY = weko_permission_factory
"""Permission factory used by the statistics REST API.

This is a function which returns a permission granting or forbidding access
to a request. It is of the form ``permission_factory(query_name, params)``
where ``query_name`` is the name of the statistic requested by the user and
``params`` is a dict of parameters for this statistic. The result of the
function is a Permission.

See Invenio-access and Flask-principal for a better understanding of the
access control mechanisms.
"""


STATS_MQ_EXCHANGE = Exchange(
    "events",
    type="direct",
    delivery_mode="transient",  # in-memory queue
)
"""Default exchange used for the message queues."""

TARGET_REPORTS = {
    'Item Registration': '1',
    'Item Detail': '2',
    'Contents Download': '3',
}

STATS_ES_INTEGER_MAX_VALUE = 6000
"""Since ES2 using size=0 has been prohibited, so in order to accomplish
the same thing, Integer.MAX_VALUE is used to retrieve agg buckets.
In ES2, size=0 was internally replaced by this value, so we have effectively
mimicked the same functonality.

Changed from 2147483647 to 6000. (refs. weko#23741)
"""

SEARCH_INDEX_PREFIX = os.environ.get('SEARCH_INDEX_PREFIX', '')
"""Search index prefix which is set in weko config."""

WEKO_STATS_UNKNOWN_LABEL = 'UNKNOWN'
"""Label using for missing of view or file-download stats."""

STATS_EVENT_STRING = 'events'
"""Stats event string."""

STATS_AGGREGATION_INDEXES = []
"""Stats aggregation indexes."""


STATS_WEKO_DEFAULT_TIMEZONE = get_timezone
"""Bucketing should use a different time zone."""

STATS_WEKO_DB_BACKUP_EVENTS = True
"""Enable DB backup of events."""

STATS_WEKO_DB_BACKUP_AGGREGATION = False
"""Enable DB backup of aggregation."""

STATS_WEKO_DB_BACKUP_BOOKMARK = False
"""Enable DB backup of bookmark."""

