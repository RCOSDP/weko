# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test app."""

import pytest
from flask import Flask

from invenio_oaiserver import InvenioOAIServer


def test_version():
    """Test version import."""
    from invenio_oaiserver import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    with pytest.warns(None):
        InvenioOAIServer(app)
