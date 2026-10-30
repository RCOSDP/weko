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

from weko_search_ui import WekoSearchUI


def test_version():
    """Test version import."""
    from weko_search_ui import __version__

    assert __version__


def test_init(app):
    """Test extension initialization."""
    # app = Flask('testapp')
    ext = WekoSearchUI(app)
    assert "weko-search-ui" in app.extensions

    # app = Flask('testapp')
    # ext = WekoSearchUI()
    # assert 'weko-search-ui' not in app.extensions
    # ext.init_app(app)
    # assert 'weko-search-ui' in app.extensions


def test_records_rest_endpoints_permission_factories():
    """Test permission factories of the records REST endpoints."""
    from weko_search_ui.config import RECORDS_REST_ENDPOINTS

    for endpoint in ("recid", "opensearch", "worksapce"):
        options = RECORDS_REST_ENDPOINTS[endpoint]
        for key in (
            "create_permission_factory_imp",
            "update_permission_factory_imp",
            "delete_permission_factory_imp",
        ):
            assert options[key] == "invenio_records_rest.utils:deny_all"
