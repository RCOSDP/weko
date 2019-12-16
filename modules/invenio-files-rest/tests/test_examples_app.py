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

    # tear down example app
    cmd = './app-teardown.sh'
    subprocess.call(cmd, shell=True)

    # setup example
    cmd = './app-setup.sh'
    exit_status = subprocess.call(cmd, shell=True)
    assert exit_status == 0
    # Starting example web app
    cmd = 'FLASK_APP=app.py flask run --debugger -p 5000'
    webapp = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                              preexec_fn=os.setsid, shell=True)

    time.sleep(10)
    # return webapp
    yield webapp
    # stop server
    os.killpg(webapp.pid, signal.SIGTERM)
    # tear down example app
    cmd = './app-teardown.sh'
    subprocess.call(cmd, shell=True)
    # return to the original directory
    os.chdir(current_dir)


@pytest.mark.skip(reason='not use in weko and cause others test cases failed.')
def test_example_app(example_app):
    """Test example app."""
    file_1 = '11111111-1111-1111-1111-111111111111'
    # load fixtures
    cmd = './app-fixtures.sh'
    exit_status = subprocess.call(cmd, shell=True)
    assert exit_status == 0
    # get file_1
    cmd = 'curl http://localhost:5000/files/{0}'.format(file_1)
    output = json.loads(
        subprocess.check_output(cmd, shell=True).decode('utf-8'))
    assert output['id'] == file_1
    assert len(output['contents']) == 1
