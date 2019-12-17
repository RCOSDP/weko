# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Extension initialization tests."""

from __future__ import absolute_import, print_function

from flask import Flask

from invenio_records_rest import InvenioRecordsREST
from invenio_records_rest.utils import PIDConverter


def test_version():
    """Test version import."""
    from invenio_records_rest import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    app.url_map.converters['pid'] = PIDConverter
    ext = InvenioRecordsREST()
    assert 'invenio-records-rest' not in app.extensions
    ext.init_app(app)
    assert 'invenio-records-rest' in app.extensions
