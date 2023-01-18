# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test example app."""

import os
import signal
import subprocess
import time
from os.path import abspath, dirname, join

import pytest


#@pytest.yield_fixture
#def example_app():
#    """Example app fixture."""
#    current_dir = os.getcwd()
#
#    # Go to example directory
#    project_dir = dirname(dirname(abspath(__file__)))
#    exampleapp_dir = join(project_dir, 'examples')
#    os.chdir(exampleapp_dir)
#
#    # Setup application
#    assert subprocess.call('./app-setup.sh', shell=True) == 0
#
#    # Setup fixtures
#    assert subprocess.call('./app-fixtures.sh', shell=True) == 0
#
#    # Start example app
#    webapp = subprocess.Popen(
#        'FLASK_APP=app.py flask run --debugger -p 5000',
#        stdout=subprocess.PIPE, preexec_fn=os.setsid, shell=True)
#    time.sleep(10)
#    yield webapp
#
#    # Stop server
#    os.killpg(webapp.pid, signal.SIGTERM)
#
#    # Tear down example app
#    subprocess.call('./app-teardown.sh', shell=True)
#
#    # Return to the original directory
#    os.chdir(current_dir)
#
#
#def test_example_app_role_admin(example_app):
#    """Test example app."""
#    cmd = 'curl http://0.0.0.0:5000/'
#    output = subprocess.check_output(cmd, shell=True)
#    assert b'Welcome to WEKO-SWORDServer' in output
