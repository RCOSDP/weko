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

"""Module tests."""

from flask import Flask

from weko_schema_ui import WekoSchemaUI


def test_version():
    """Test version import."""
    from weko_schema_ui import __version__
    assert __version__


def test_init(app):
    """Test extension initialization."""
    app_1 = Flask('testapp')
    ext = WekoSchemaUI(app_1)
    assert 'weko-schema-ui' in app_1.extensions

    app_2 = Flask('testapp')
    ext = WekoSchemaUI()
    assert 'weko-schema-ui' not in app_2.extensions
    ext.init_app(app_2)
    assert 'weko-schema-ui' in app_2.extensions
