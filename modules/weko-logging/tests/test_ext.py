# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Warnings capturing tests."""

import logging

from flask import Flask

from weko_logging.ext import WekoLoggingBase


def test_init(pywarnlogger):
    """
    Test extension initialization.

    :param pywarnlogger: Py warn logger object.
    """
    app = Flask('testapp')
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
