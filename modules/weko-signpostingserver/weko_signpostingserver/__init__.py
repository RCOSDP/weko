# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Signpostingserver is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of weko-signpostingserver."""

from __future__ import absolute_import, print_function

from .ext import WekoSignpostingserver
from .version import __version__

__all__ = ('__version__', 'WekoSignpostingserver')
