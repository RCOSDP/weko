# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Signals for indexer."""

from __future__ import absolute_import, print_function

from blinker import Namespace

_signals = Namespace()

before_record_index = _signals.signal('before-record-index')
"""Signal sent before a record is indexed.

The sender is the current Flask application, and two keyword arguments are
provided:

- ``json``: The dumped record dictionary which can be modified.
- ``record``: The record being indexed.
- ``index``: The index in which the record will be indexed.
- ``doc_type``: The doc_type for the record.
- ``arguments``: The arguments to pass to Elasticsearch for indexing.
- ``**kwargs``: Extra arguments.
"""
