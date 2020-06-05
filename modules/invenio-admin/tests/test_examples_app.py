# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test example app."""

import os
import signal
import subprocess
import time
from os.path import abspath, dirname, join

import pytest


@pytest.yield_fixture
def example_app():
    """Example app fixture."""
    current_dir = os.getcwd()

    # Go to example directory
    project_dir = dirname(dirname(abspath(__file__)))
    exampleapp_dir = join(project_dir, 'examples')
    os.chdir(exampleapp_dir)

    # Setup application
    assert subprocess.call('./app-setup.sh', shell=True) == 0

    # Setup fixtures
    assert subprocess.call('./app-fixtures.sh', shell=True) == 0

    # Start example app
    webapp = subprocess.Popen(
        'FLASK_APP=app.py flask run --debugger -p 5000',
        stdout=subprocess.PIPE, preexec_fn=os.setsid, shell=True)
    time.sleep(10)
    yield webapp

    # Stop server
    os.killpg(webapp.pid, signal.SIGTERM)

    # Tear down example app
    subprocess.call('./app-teardown.sh', shell=True)

    # Return to the original directory
    os.chdir(current_dir)


def test_example_app(example_app, tmpdir):
    """Test example app."""
    # Index redirects to `/admin`
    cmd = 'curl -L http://localhost:5000/'
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    assert 'Test Model' not in output

    # Login and then access the custom admin page
    cookie_jar = str((tmpdir.join('cookies')))
    cmd = (
        "curl -L -c {cookie_jar} http://localhost:5000/login/ "
        "-d 'csrf_token=None&email=info@inveniosoftware.org&password=123456' "
        "&& curl -L -b {cookie_jar} http://localhost:5000/admin/testmodel"
        .format(cookie_jar=cookie_jar))
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    # Ensure that the view is visible for the logged-in user
    assert 'Test Model' in output

    # User admin page
    cmd = 'curl -L -b {cookie_jar} http://localhost:5000/admin/user/'.format(
        cookie_jar=cookie_jar)
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    assert 'info@inveniosoftware.org' in output
