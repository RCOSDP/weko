# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Proxy to the current queues module."""

from flask import current_app
from werkzeug.local import LocalProxy

current_queues = LocalProxy(lambda: current_app.extensions["invenio-queues"])
