# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-sitemap is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Sitemap signals."""

from blinker import Namespace

_signals = Namespace()

sitemap_finished = _signals.signal('sitemap-finished')
"""
This signal is sent when  sitemap is updated.
"""
