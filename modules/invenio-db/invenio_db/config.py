# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Default configuration for Invenio-DB."""

from os import environ

DB_POOL_CLASS = 'QueuePool'
"""Database connection pool"""

DB_SQLALCHEMY_POOL_PACKAGE = 'sqlalchemy.pool'
"""SQLAlchemy pool package"""
