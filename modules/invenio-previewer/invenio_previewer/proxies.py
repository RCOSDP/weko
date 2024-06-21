# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Proxy for current previewer."""

from flask import current_app
from werkzeug.local import LocalProxy

current_previewer = LocalProxy(lambda: current_app.extensions["invenio-previewer"])
"""Proxy object to the current previewer extension."""
