# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test example app."""

import json
import os
import signal
import subprocess
import time

import pytest


@pytest.yield_fixture
def example_app():
    """Example app fixture."""
    current_dir = os.getcwd()

    # Go to example directory
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exampleappdir = os.path.join(project_dir, 'examples')
    os.chdir(exampleappdir)

    # Setup example
    cmd = './app-setup.sh'
    exit_status = subprocess.call(cmd, shell=True)
    assert exit_status == 0

    # Setup example
    cmd = './app-fixtures.sh'
    exit_status = subprocess.call(cmd, shell=True)
    assert exit_status == 0
    time.sleep(10)
    # Return webapp
    yield exit_status

    # Tear down example app
    cmd = './app-teardown.sh'
    subprocess.call(cmd, shell=True)

    # Return to the original directory
    os.chdir(current_dir)


def test_example_app(example_app):
    """Test example app."""
    cmd = 'curl -X GET localhost:9200/_cat/indices?v'
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    assert 'testrecords-testrecord-v1.0.0' in output
    cmd = 'curl -X GET localhost:9200/testrecords-testrecord-v1.0.0/_search'
    output = json.loads(
        subprocess.check_output(cmd, shell=True).decode('utf-8'))
    assert len(output['hits']['hits']) == 10
