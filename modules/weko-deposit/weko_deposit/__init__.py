# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of weko-deposit."""

from .ext import WekoDeposit, WekoDepositREST
from .version import __version__

__all__ = ('__version__', 'WekoDeposit', 'WekoDepositREST')
