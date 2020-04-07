# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Proxy definitions."""

from flask import current_app
from werkzeug.local import LocalProxy

current_weko_items_ui = LocalProxy(
    lambda: current_app.extensions['weko-items-ui'])
"""Helper proxy to access files rest state object."""
