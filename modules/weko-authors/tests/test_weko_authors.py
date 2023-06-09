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

from weko_authors import WekoAuthors
from weko_theme import WekoTheme

# .tox/c1/bin/pytest --cov=weko_authors tests/test_weko_authors.py -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp

def test_version():
    """Test version import."""
    from weko_authors import __version__
    assert __version__

# .tox/c1/bin/pytest --cov=weko_authors tests/test_weko_authors.py::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoAuthors(app)
    assert 'weko-authors' in app.extensions

    app = Flask('testapp')
    ext = WekoAuthors()
    assert 'weko-authors' not in app.extensions
    ext.init_app(app)
    assert 'weko-authors' in app.extensions
