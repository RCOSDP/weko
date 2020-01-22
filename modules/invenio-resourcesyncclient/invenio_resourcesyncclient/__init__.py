# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# INVENIO-ResourceSyncClient is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of invenio-resourcesyncclient."""

from __future__ import absolute_import, print_function

from .ext import INVENIOResourceSyncClient
from .version import __version__

__all__ = ('__version__', 'INVENIOResourceSyncClient')
