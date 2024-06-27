# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
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
    # go to example directory
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exampleappdir = os.path.join(project_dir, 'examples')
    os.chdir(exampleappdir)
    # setup example
    cmd = './app-setup.sh'
    exit_status = subprocess.call(cmd, shell=True)
    assert exit_status == 0
    # load fixtures
    cmd = './app-fixtures.sh'
    exit_status = subprocess.call(cmd, shell=True)
    assert exit_status == 0
    # Starting example web app
    cmd = 'FLASK_APP=app.py flask run --debugger -p 5000'
    webapp = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                              preexec_fn=os.setsid, shell=True)
    time.sleep(20)
    # return webapp
    yield webapp
    # stop server
    os.killpg(webapp.pid, signal.SIGTERM)
    # tear down example app
    cmd = './app-teardown.sh'
    subprocess.call(cmd, shell=True)
    # return to the original directory
    os.chdir(current_dir)


def test_example_app(example_app):
    """Test example app."""
    cmd = 'FLASK_APP=app.py flask tokens create --name test_token' \
          ' --user info@inveniosoftware.org'
    token = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
    # search page
    cmd = 'curl http://localhost:5000/search'
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    assert 'invenio-search-results' in output
    # search API
    cmd = 'curl http://localhost:5000/deposits/?access_token={0}'.format(token)
    output = json.loads(
        subprocess.check_output(cmd, shell=True).decode('utf-8')
    )
    assert len(output['hits']['hits']) > 0
