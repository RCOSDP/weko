# -*- coding: utf-8 -*-
"""Pytest for weko-logging configuration."""

import logging
import shutil
import tempfile

import pytest


@pytest.fixture()
def tmppath():
    """Make a temporary directory."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture()
def pywarnlogger():
    """Rest the py.warnings logger."""
    logger = logging.getLogger("py.warnings")
    yield logger
    logger.handlers = []
