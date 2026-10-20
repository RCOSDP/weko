# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test app."""

from __future__ import absolute_import

import pytest
from flask import Flask

from invenio_oaiserver import InvenioOAIServer


def test_version():
    """Test version import."""
    from invenio_oaiserver import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    with pytest.warns(None):
        InvenioOAIServer(app)


def test_resumption_token_expire_time_default():
    """Scroll keep-alive defaults to 1 hour, not 24 hours."""
    app = Flask('testapp')
    InvenioOAIServer(app)
    assert app.config['OAISERVER_RESUMPTION_TOKEN_EXPIRE_TIME'] == 3600


def test_resumption_token_expire_time_override():
    """A value set by the instance config is kept."""
    app = Flask('testapp')
    app.config['OAISERVER_RESUMPTION_TOKEN_EXPIRE_TIME'] = 600
    InvenioOAIServer(app)
    assert app.config['OAISERVER_RESUMPTION_TOKEN_EXPIRE_TIME'] == 600
