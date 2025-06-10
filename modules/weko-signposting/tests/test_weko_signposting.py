# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Signposting is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

import pytest

from weko_signposting import WekoSignposting

def test_version():
    """Test version import."""
    from weko_signposting import __version__

    assert __version__

def test_init(base_app):
    """Test extension initialization."""
    assert 'weko-signposting' not in base_app.extensions
    WekoSignposting(base_app)
    assert "weko-signposting" in base_app.extensions

def test_init_no_app(base_app):
    """Test extension initialization without app."""
    ext = WekoSignposting()
    assert 'weko-signposting' not in base_app.extensions

    ext.init_app(base_app)
    assert 'weko-signposting' in base_app.extensions
