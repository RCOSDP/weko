# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Models for Invenio-Files-REST."""

from __future__ import absolute_import, print_function

from blinker import Namespace

_signals = Namespace()

file_downloaded = _signals.signal('file-downloaded')
file_previewed = _signals.signal('file-previewed')
"""File downloaded signal.

Sent when a file is downloaded.
"""
