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

"""Warnings capturing tests."""

import logging

from flask import Flask

from weko_logging.ext import WekoLoggingBase


def test_init(pywarnlogger):
    """
    Test extension initialization.

    :param pywarnlogger: Py warn logger object.
    """
    app = Flask("testapp")
    ext = WekoLoggingBase(app)
    assert len(pywarnlogger.handlers) == 0

    # Capture warnings.
    handler = logging.StreamHandler()
    ext.capture_pywarnings(handler)
    assert len(pywarnlogger.handlers) == 1

    # Don't install the same handler twice (i.e. prevent multiple Flask apps
    # to install the same handlers and thus receiving double notifications)
    handler = logging.StreamHandler()
    ext.capture_pywarnings(handler)
    assert len(pywarnlogger.handlers) == 1

    # Different types of handlers are welcome
    handler = logging.NullHandler()
    ext.capture_pywarnings(handler)
    assert len(pywarnlogger.handlers) == 2
