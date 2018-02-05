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

from weko_index_tree import WekoIndexTree


def test_version():
    """Test version import."""
    from weko_index_tree import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoIndexTree(app)
    assert 'weko-index-tree' in app.extensions

    app = Flask('testapp')
    ext = WekoIndexTree()
    assert 'weko-index-tree' not in app.extensions
    ext.init_app(app)
    assert 'weko-index-tree' in app.extensions


def test_view(app):
    """Test view."""
    WekoIndexTree(app)
    with app.test_client() as client:
        res = client.get("/")
        assert res.status_code == 200
        assert 'Welcome to weko-index-tree' in str(res.data)
