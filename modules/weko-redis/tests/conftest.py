# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Pytest configuration for weko-redis."""

import os

import pytest
from flask import Flask


@pytest.fixture()
def base_app():
    """Flask application carrying only the config weko-redis reads."""
    app_ = Flask("testapp")
    app_.config.update(
        TESTING=True,
        CACHE_TYPE="redis",
        CACHE_REDIS_HOST=os.environ.get("CACHE_REDIS_HOST", "redis"),
        REDIS_PORT=os.environ.get("REDIS_PORT", "6379"),
        CACHE_REDIS_SENTINELS=[("sentinel", 26379)],
        CACHE_REDIS_SENTINEL_MASTER="mymaster",
    )
    return app_


@pytest.fixture()
def app(base_app):
    """Flask application with an application context pushed."""
    with base_app.app_context():
        yield base_app
