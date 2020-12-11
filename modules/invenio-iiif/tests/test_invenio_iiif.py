# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function


def test_version():
    """Test version import."""
    from invenio_iiif import __version__
    assert __version__


def test_init(base_app):
    """Test extension initialization."""
    assert 'invenio-iiif' in base_app.extensions
    assert 'iiif' in base_app.extensions
