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


"""Test CLI."""

from __future__ import absolute_import, print_function

import os

from click.testing import CliRunner
from flask.cli import ScriptInfo

from invenio_files_rest.cli import files as cmd


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
