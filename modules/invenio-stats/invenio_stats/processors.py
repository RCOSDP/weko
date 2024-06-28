# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2019 CERN.
# Copyright (C)      2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Events indexer."""

import hashlib
from datetime import datetime
from time import mktime

from counter_robots import is_machine, is_robot
from dateutil import parser
from flask import current_app
from invenio_base.utils import obj_or_import_string
from invenio_search import current_search_client
from invenio_search.engine import search
from invenio_search.utils import prefix_index
from pytz import utc

from .utils import get_anonymization_salt, get_geoip


def anonymize_user(doc):
    """Preprocess an event by anonymizing user information.

    The anonymization is done by removing fields that can uniquely identify a
    user, such as the user's ID, session ID, IP address and User Agent, and
    hashing them to produce a ``visitor_id`` and ``unique_session_id``. To
    further secure the method, a randomly generated 32-byte salt is used, that
    expires after 24 hours and is discarded. The salt values are stored in
    Redis (or whichever backend Invenio-Cache uses). The ``unique_session_id``
    is calculated in the same way as the ``visitor_id``, with the only
    difference that it also takes into account the hour of the event . All of
    these rules effectively mean that a user can have a unique ``visitor_id``
    for each day and unique ``unique_session_id`` for each hour of a day.

    This session ID generation process was designed according to the `Project
    COUNTER Code of Practice <https://www.projectcounter.org/code-of-
    practice-sections/general-information/>`_.

    In addition to that the country of the user is extracted from the IP
    address as a ISO 3166-1 alpha-2 two-letter country code (e.g. "CH" for
    Switzerland).
    """
    ip = doc.pop("ip_address", None)
    if ip:
        doc.update({"country": get_geoip(ip)})

    user_id = doc.pop("user_id", "")
    session_id = doc.pop("session_id", "")
    user_agent = doc.pop("user_agent", "")

    # A 'User Session' is defined as activity by a user in a period of
    # one hour. timeslice represents the hour of the day in which
    # the event has been generated and together with user info it determines
    # the 'User Session'
    timestamp = parser.parse(doc.get("timestamp"))
    timeslice = timestamp.strftime("%Y%m%d%H")
    salt = get_anonymization_salt(timestamp)

    visitor_id = hashlib.sha224(salt.encode("utf-8"))
    unique_session_id = hashlib.sha224(salt.encode("utf-8"))

    if user_id:
        visitor_id.update(user_id.encode("utf-8"))
        sid = "{}|{}".format(user_id, timeslice)
        unique_session_id.update(sid.encode("utf-8"))
    elif session_id:
        visitor_id.update(session_id.encode("utf-8"))
        sid = "{}|{}".format(session_id, timeslice)
        unique_session_id.update(sid.encode("utf-8"))
    elif ip and user_agent:
        vsid = "{}|{}|{}".format(ip, user_agent, timeslice)
        visitor_id.update(vsid.encode("utf-8"))
        unique_session_id.update(vsid.encode("utf-8"))

    doc.update(
        {
            "visitor_id": visitor_id.hexdigest(),
            "unique_session_id": unique_session_id.hexdigest(),
        }
    )
    return doc


def flag_robots(doc):
    """Flag events which are created by robots.

    The list of robots is defined by the `COUNTER-robots Python package
    <https://github.com/inveniosoftware/counter-robots>`_ , which follows the
    `list defined by Project COUNTER
    <https://www.projectcounter.org/appendices/850-2/>`_ that was later split
    into robots and machines by `the Make Data Count project
    <https://github.com/CDLUC3/Make-Data-Count/tree/master/user-agents>`_.
    """
    doc["is_robot"] = "user_agent" in doc and is_robot(doc["user_agent"])
    return doc


def flag_machines(doc):
    """Flag events which are created by machines.

    The list of machines is defined by the `COUNTER-robots Python package
    <https://github.com/inveniosoftware/counter-robots>`_ , which follows the
    `list defined by Project COUNTER
    <https://www.projectcounter.org/appendices/850-2/>`_ that was later split
    into robots and machines by `the Make Data Count project
    <https://github.com/CDLUC3/Make-Data-Count/tree/master/user-agents>`_.

    """
    doc["is_machine"] = "user_agent" in doc and is_machine(doc["user_agent"])
    return doc


def hash_id(iso_timestamp, msg):
    """Generate event id, optimized for the search engine."""
    return "{0}-{1}".format(
        iso_timestamp,
        hashlib.sha1(
            msg.get("unique_id").encode("utf-8")
            + str(msg.get("visitor_id")).encode("utf-8")
        ).hexdigest(),
    )


class EventsIndexer(object):
    """Simple events indexer.

    Subclass this class in order to provide custom indexing behaviour.
    """

    default_preprocessors = [flag_robots, anonymize_user]
    """Default preprocessors ran on every event."""

    def __init__(
        self,
        queue,
        prefix="events",
        suffix="%Y-%m",
        client=None,
        preprocessors=None,
        double_click_window=10,
    ):
        """Initialize indexer.

        :param prefix: prefix appended to search indices' name.
        :param suffix: suffix appended to search indices' name.
        :param double_click_window: time window during which similar events are
            deduplicated (counted as one occurence).
        :param client: search client.
        :param preprocessors: a list of functions which are called on every
            event before it is indexed. Each function should return the
            processed event. If it returns None, the event is filtered and
            won't be indexed.
        """
        self.queue = queue
        self.client = client or current_search_client
        self.index = prefix_index("{0}-{1}".format(prefix, self.queue.routing_key))
        self.suffix = suffix

        # load the preprocessors
        self.preprocessors = (
            [obj_or_import_string(preproc) for preproc in preprocessors]
            if preprocessors is not None
            else self.default_preprocessors
        )
        self.double_click_window = double_click_window

    def actionsiter(self):
        """Iterator."""
        for msg in self.queue.consume():
            try:
                for preproc in self.preprocessors:
                    msg = preproc(msg)
                    if msg is None:
                        break
                if msg is None:
                    continue

                ts = parser.parse(msg.get("timestamp"))
                suffix = ts.strftime(self.suffix)

                # Truncate timestamp to keep only seconds.
                # This is to improve search engine performances.
                ts = ts.replace(microsecond=0)
                msg["timestamp"] = ts.isoformat()
                msg["updated_timestamp"] = datetime.utcnow().isoformat()
                # apply timestamp windowing in order to group events too close in time
                if self.double_click_window > 0:
                    timestamp = mktime(utc.localize(ts).utctimetuple())
                    ts = ts.fromtimestamp(
                        timestamp // self.double_click_window * self.double_click_window
                    )
                yield {
                    "_id": hash_id(ts.isoformat(), msg),
                    "_op_type": "index",
                    "_index": "{0}-{1}".format(self.index, suffix),
                    "_source": msg,
                }
            except Exception:
                current_app.logger.exception("Error while processing event")

    def run(self):
        """Process events queue."""
        return search.helpers.bulk(
            self.client, self.actionsiter(), stats_only=True, chunk_size=50
        )
