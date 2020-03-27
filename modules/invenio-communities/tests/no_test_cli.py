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


"""Module tests."""

from __future__ import absolute_import, print_function

from click.testing import CliRunner

from invenio_communities.cli import addlogo, init


def test_cli_init(script_info):
    """Test create user CLI."""
    runner = CliRunner()

    # Init a community first time.
    result = runner.invoke(init, obj=script_info)
    assert result.exit_code == 0

    # Init a community when it is already created.
    result = runner.invoke(init, obj=script_info)
    assert 'Bucket with UUID' in result.output_bytes
    assert 'already exists.\n' in result.output_bytes


def test_cli_init(script_info):
    """Test create user CLI."""
    runner = CliRunner()

    # Add logo to an unexisting community.
    result = runner.invoke(addlogo, [
        '00000000-0000-0000-0000-000000000000',
        '',
    ], obj=script_info)
    assert result.exit_code == 0

    # Add logo to an existing community.
