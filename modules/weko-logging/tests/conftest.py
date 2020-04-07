# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pytest for weko-logging configuration."""

import logging
import shutil
import tempfile

import pytest


@pytest.yield_fixture()
def tmppath():
    """Make a temporary directory."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.yield_fixture()
def pywarnlogger():
    """Rest the py.warnings logger."""
    logger = logging.getLogger('py.warnings')
    yield logger
    logger.handlers = []
