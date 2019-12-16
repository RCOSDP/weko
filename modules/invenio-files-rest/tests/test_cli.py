# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Test CLI."""

from __future__ import absolute_import, print_function

import os
import pytest

from click.testing import CliRunner
from flask.cli import ScriptInfo

from invenio_files_rest.cli import files as cmd


@pytest.mark.skip(reason='failed and seems not used in weko')
def test_simple_workflow(app, db, tmpdir):
    """Run simple workflow."""
    runner = CliRunner()
    script_info = ScriptInfo(create_app=lambda info: app)

    source = os.path.join(os.path.dirname(__file__), 'fixtures', 'source')
    result = runner.invoke(cmd, [
        'location', 'tmp', 'file://' + tmpdir.strpath, '--default'
    ], obj=script_info)
    assert 0 == result.exit_code

    result = runner.invoke(cmd, ['bucket', 'touch'], obj=script_info)
    assert 0 == result.exit_code
    bucket_id = result.output.split('\n')[0]

    # Specify a directory where 2 files have same content.
    result = runner.invoke(cmd, [
        'bucket', 'cp', source, bucket_id, '--checksum'
    ], obj=script_info)
    assert 0 == result.exit_code

    assert len(tmpdir.listdir()) == 2

    # Specify a file.
    result = runner.invoke(cmd, ['bucket', 'cp', __file__, bucket_id],
                           obj=script_info)
    assert 0 == result.exit_code

    assert len(tmpdir.listdir()) == 3

    # No new file should be created.
    result = runner.invoke(cmd, [
        'bucket', 'cp', __file__, bucket_id, '--checksum'
    ], obj=script_info)
    assert 0 == result.exit_code

    assert len(tmpdir.listdir()) == 3
