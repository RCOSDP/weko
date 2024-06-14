# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test example app."""

import os
import subprocess

import pytest


@pytest.yield_fixture
def example_app():
    """Example app fixture."""
    current_dir = os.getcwd()

    # Go to example directory
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exampleappdir = os.path.join(project_dir, 'examples')
    os.chdir(exampleappdir)

    # Return current dir
    yield exampleappdir

    # Return to the original directory
    os.chdir(current_dir)


def test_example_app(example_app):
    """Test example app."""
    # Testing database creation
    for cmd in ['FLASK_APP=app.py flask db init',
                'FLASK_APP=app.py flask db create',
                'FLASK_APP=app.py flask db drop --yes-i-know']:
        exit_status = subprocess.call(cmd, shell=True)
        assert exit_status == 0
