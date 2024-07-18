# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Signals for indexer."""

from types import MethodType

from blinker import ANY, Namespace


def _with_dynamic_connect(signal):
    """Adds a `dynamic_connect()` method to blinker signals."""

    def _dynamic_connect(
        self, receiver, sender=ANY, weak=True, condition_func=None, **connect_kwargs
    ):
        """Dynamically connect a receiver to a signal based on a condition."""

        def _default_condition_func(sender, connect_kwargs, **signal_kwargs):
            return all(signal_kwargs.get(k) == v for k, v in connect_kwargs.items())

        condition_func = condition_func or _default_condition_func

        def _conditional_receiver(sender, **kwargs):
            if condition_func(sender, connect_kwargs, **kwargs):
                receiver(sender, **kwargs)

        return self.connect(_conditional_receiver, sender=sender, weak=weak)

    signal.dynamic_connect = MethodType(_dynamic_connect, signal)
    return signal


_signals = Namespace()

before_record_index = _with_dynamic_connect(_signals.signal("before-record-index"))
"""Signal sent before a record is indexed.

The sender is the current Flask application, and two keyword arguments are
provided:

- ``json``: The dumped record dictionary which can be modified.
- ``record``: The record being indexed.
- ``index``: The index in which the record will be indexed.
- ``arguments``: The arguments to pass to the search engine for indexing.
- ``**kwargs``: Extra arguments.

This signal also has a ``.dynamic_connect()`` method which allows some more
flexible ways to connect receivers to it. The most common use case is that you
want to apply a receiver only to a specific index. In that case you can call:

.. code-block: python

    # Will only run "my_receiver" if the "index" parameter is "authors-v1.0.0"
    before_record_index.dynamic_connect(
        some_receiver, sender=app, index="authors-v1.0.0")

For more complex conditions you can provide a function via the
``condition_func`` parameter like so:

.. code-block: python

    def famous_author_condition(sender, connect_kwargs, **signal_kwargs):
        # "connect_kwargs" are keyword arguments passed to ".dynamic_connect()
        # "signal_kwargs" are keyword arguemtns passed by the
        # "before_record_index.send()" call
        return signal_args['index'] == 'authors-v1.0.0' \
            and len(signal_args['json']['awards']) > 5

    before_record_index.dynamic_connect(
        some_receiver, sender=app, condition_func=author_condition)
"""
