# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""UI for creating items."""

from .ext import WekoItemsUI
from .proxies import current_weko_items_ui
from .version import __version__

__all__ = ('__version__', 'WekoItemsUI', 'current_weko_items_ui')
