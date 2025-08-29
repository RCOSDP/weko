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

from flask import Flask, json, url_for

from weko_items_ui import WekoItemsUI
from weko_items_ui.config import WEKO_ITEMS_UI_BASE_TEMPLATE
from weko_items_ui.proxies import current_weko_items_ui
from weko_theme.config import BASE_PAGE_TEMPLATE
from weko_items_ui.ext import _WekoItemsUIState

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_weko_items_ui.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp

def test_version():
    """Test version import."""
    from weko_items_ui import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoItemsUI(app)
    assert 'weko-items-ui' in app.extensions

    app = Flask('testapp')
    ext = WekoItemsUI()
    assert 'weko-items-ui' not in app.extensions
    ext.init_app(app)
    assert 'weko-items-ui' in app.extensions

    app = Flask('testapp')
    app.config.update(BASE_PAGE_TEMPLATE=BASE_PAGE_TEMPLATE)
    WekoItemsUI(app)
    assert 'weko-items-ui' in app.extensions


    app = Flask('testapp')
    app.config.update(WEKO_ITEMS_UI_BASE_TEMPLATE=WEKO_ITEMS_UI_BASE_TEMPLATE)
    ext = WekoItemsUI(app)
    assert 'weko-items-ui' in app.extensions


    with app.test_request_context():
        assert 'weko-items-ui' in current_weko_items_ui.app.extensions
    
    


def test_view(app,db_sessionlifetime):
    """Test view."""
    WekoItemsUI(app)
    with app.test_client() as client:
        res = client.get("/items/jsonschema/0")
        assert res.status_code == 302
        res = client.get("/items/schemaform/0")
        assert res.status_code == 302


def test_prepare_edit_item(app):
    from weko_items_ui.views import blueprint_api
    app.login_manager._login_disabled = True
    app.register_blueprint(blueprint_api)
    
    with app.test_request_context():
        url = url_for('weko_items_ui_api.prepare_edit_item')
    # WekoItemsUI(app)
    with app.test_client() as client:
        res = client.post(url, json={})
        json_response = json.loads(res.get_data())
        assert json_response.get('code') == -1
        assert json_response.get('msg') == 'An error has occurred.'
