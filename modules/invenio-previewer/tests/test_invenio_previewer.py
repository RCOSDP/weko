# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Module tests."""

from __future__ import absolute_import, print_function

import importlib

from flask import Flask
from mock import patch
from pkg_resources import EntryPoint

from invenio_previewer import InvenioPreviewer


class MockEntryPoint(EntryPoint):
    """Mocking of entrypoint."""

    def load(self):
        """Mock load entry point."""
        return importlib.import_module(self.module_name)


def _mock_entry_points(group=None):
    """Mocking funtion of entrypoints."""
    data = {
        'invenio_previewer.previewers': [
            MockEntryPoint(
                'default',
                'invenio_previewer.extensions.default',
            ),
            MockEntryPoint(
                'zip',
                'invenio_previewer.extensions.zip',
            ),
        ],
    }
    names = data.keys() if group is None else [group]
    for key in names:
        for entry_point in data[key]:
            yield entry_point


def test_version():
    """Test version import."""
    from invenio_previewer import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    InvenioPreviewer(app)
    assert 'invenio-previewer' in app.extensions


@patch('pkg_resources.iter_entry_points', _mock_entry_points)
def test_entrypoint_previewer():
    """Test the entry points."""
    app = Flask('testapp')
    ext = InvenioPreviewer(app)
    ext.load_entry_point_group('invenio_previewer.previewers')
    assert len(ext.previewers) == 2
