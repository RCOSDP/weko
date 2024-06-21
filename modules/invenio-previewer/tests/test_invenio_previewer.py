# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

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
        "invenio_previewer.previewers": [
            MockEntryPoint(
                "default",
                "invenio_previewer.extensions.default",
            ),
            MockEntryPoint(
                "zip",
                "invenio_previewer.extensions.zip",
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
    app = Flask("testapp")
    InvenioPreviewer(app)
    assert "invenio-previewer" in app.extensions


@patch("pkg_resources.iter_entry_points", _mock_entry_points)
def test_entrypoint_previewer():
    """Test the entry points."""
    app = Flask("testapp")
    ext = InvenioPreviewer(app)
    ext.load_entry_point_group("invenio_previewer.previewers")
    assert len(ext.previewers) == 2
