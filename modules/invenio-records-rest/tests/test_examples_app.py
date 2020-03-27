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

    # Start example app
    webapp = subprocess.Popen(
        'FLASK_APP=app.py flask run --debugger -p 5000',
        stdout=subprocess.PIPE, preexec_fn=os.setsid, shell=True)
    time.sleep(20)
    yield webapp

    # Stop server
    os.killpg(webapp.pid, signal.SIGTERM)

    # Tear down example app
    subprocess.call('./app-teardown.sh', shell=True)

    # Return to the original directory
    os.chdir(current_dir)


def test_example_app(example_app):
    """Test example app."""
    # load fixtures
    cmd = 'FLASK_APP=app.py flask fixtures records'
    exit_status = subprocess.call(cmd, shell=True)
    assert exit_status == 0
    time.sleep(7)
    # Testing record retrieval via web
    cmd = 'curl http://127.0.0.1:5000/records/1'
    output = json.loads(
        subprocess.check_output(cmd, shell=True).decode("utf-8")
    )
    assert output['id'] == 1
    assert output['metadata']['control_number'] == '1'
    assert output['metadata']['description'] == \
        "This is an awesome description"
    assert output['metadata']['title'] == "Registered"

    # Testing record retrieval via web with query
    cmd = ('curl http://127.0.0.1:5000/records/'
           '?size=3&page=3&q=awesome&sort=-control_number')
    output = json.loads(
        subprocess.check_output(cmd, shell=True).decode("utf-8")
    )
    assert len(output['hits']['hits']) == 3

    # Testing view options retrieval via web
    cmd = 'curl http://127.0.0.1:5000/records/_options'
    output = json.loads(
        subprocess.check_output(cmd, shell=True).decode("utf-8")
    )
    assert len(output['sort_fields']) == 2
    for sort_field in output['sort_fields']:
        if 'title' in sort_field:
            assert sort_field['title']['default_order'] == 'asc'
            assert sort_field['title']['title'] == 'Title'
        if 'control_number' in sort_field:
            assert sort_field['control_number']['default_order'] == 'asc'
            assert sort_field['control_number']['title'] == 'Record identifier'

    # Testing suggest retrieval via web
    cmd = 'curl http://127.0.0.1:5000/records/_suggest?title-complete=Reg'
    output = json.loads(
        subprocess.check_output(cmd, shell=True).decode("utf-8")
    )
    assert output['title-complete'][0]['text'] == 'Reg'
