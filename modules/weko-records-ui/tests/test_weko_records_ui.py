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

from weko_records_ui import WekoRecordsUI,WekoRecordsCitesREST
from weko_records_ui.config import WEKO_RECORDS_UI_BASE_TEMPLATE,WEKO_RECORDS_UI_CITES_REST_ENDPOINTS
from weko_theme.config import BASE_PAGE_TEMPLATE

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_weko_records_ui.py::test_version -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_version():
    """Test version import."""
    from weko_records_ui import __version__
    assert __version__

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_weko_records_ui.py::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoRecordsUI(app)
    assert 'weko-records-ui' in app.extensions

    app = Flask('testapp')
    ext = WekoRecordsUI()
    assert 'weko-records-ui' not in app.extensions
    ext.init_app(app)
    assert 'weko-records-ui' in app.extensions


    app = Flask('testapp')
    app.config["BASE_PAGE_TEMPLATE"] = BASE_PAGE_TEMPLATE
    ext = WekoRecordsUI()
    assert 'weko-records-ui' not in app.extensions
    ext.init_app(app)
    assert 'weko-records-ui' in app.extensions


    app = Flask('testapp')
    app.config["BASE_PAGE_TEMPLATE"] = BASE_PAGE_TEMPLATE
    assert "BASE_PAGE_TEMPLATE" in app.config
    ext = WekoRecordsUI()
    ext.init_app(app)
    assert 'weko-records-ui' in app.extensions
    
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_weko_records_ui.py::test_wekorecordsCitesREST -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_wekorecordsCitesREST():
    app = Flask('testapp')
    app.config["WEKO_RECORDS_UI_CITES_REST_ENDPOINTS"]=WEKO_RECORDS_UI_CITES_REST_ENDPOINTS
    ext = WekoRecordsCitesREST(app)
    assert 'weko-records-ui-cites-rest' in app.extensions
    
