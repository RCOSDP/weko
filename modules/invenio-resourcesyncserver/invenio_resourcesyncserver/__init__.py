# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# INVENIO-ResourceSyncServer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of invenio-resourcesyncserver."""

from __future__ import absolute_import, print_function

from .ext import InvenioResourceSyncServer
from .version import __version__

__all__ = ('__version__', 'InvenioResourceSyncServer')
