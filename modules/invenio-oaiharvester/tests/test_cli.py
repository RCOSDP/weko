# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Test for utilities used by OAI harvester."""

from __future__ import absolute_import, print_function

import re

import responses
from click.testing import CliRunner

from invenio_oaiharvester.cli import harvest

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_cli.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_cli.py::test_cli_harvest_idents -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
@responses.activate
def test_cli_harvest_idents(script_info, sample_record_xml, tmpdir):
    """Test create user CLI."""
    responses.add(
        responses.GET,
        'http://export.arxiv.org/oai2',
        body=sample_record_xml,
        content_type='text/xml'
    )

    runner = CliRunner()
    result = runner.invoke(
        harvest,
        ['-u', 'http://export.arxiv.org/oai2',
         '-m', 'arXiv',
         '-i', 'oai:arXiv.org:1507.03011'],
        obj=script_info
    )
    assert result.exit_code == 0

    # not send signal, quiet is true
    result = runner.invoke(
        harvest,
        ['-u', 'http://export.arxiv.org/oai2',
         '-m', 'arXiv',
         '-i', 'oai:arXiv.org:1507.03011',
         '--quiet',
         '--no-signals'],
        obj=script_info
    )
    assert result.exit_code == 0

    # Cannot use dates and identifiers
    result = runner.invoke(
        harvest,
        ['-u', 'http://export.arxiv.org/oai2',
         '-m', 'arXiv',
         '-f', '2015-01-17',
         '-i', 'oai:arXiv.org:1507.03011'],
        obj=script_info
    )
    assert result.exit_code != 0

    # Queue it
    result = runner.invoke(
        harvest,
        ['-u', 'http://export.arxiv.org/oai2',
         '-m', 'arXiv',
         '-i', 'oai:arXiv.org:1507.03011',
         '--enqueue'],
        obj=script_info
    )
    assert result.exit_code == 0

    # Save it directory
    result = runner.invoke(
        harvest,
        ['-u', 'http://export.arxiv.org/oai2',
         '-m', 'arXiv',
         '-i', 'oai:arXiv.org:1507.03011',
         '-d', tmpdir.dirname],
        obj=script_info
    )
    assert result.exit_code == 0

    # Missing URL
    result = runner.invoke(
        harvest,
        ['-m', 'arXiv',
         '-i', 'oai:arXiv.org:1507.03011'],
        obj=script_info
    )
    assert result.exit_code != 0

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_cli.py::test_cli_harvest_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
@responses.activate
def test_cli_harvest_list(script_info, sample_empty_set):
    """Test create user CLI."""
    responses.add(
        responses.GET,
        re.compile(r'http?://export.arxiv.org/oai2.*set=physics.*'),
        body=sample_empty_set,
        content_type='text/xml'
    )

    runner = CliRunner()
    result = runner.invoke(
        harvest,
        ['-u', 'http://export.arxiv.org/oai2',
         '-m', 'arXiv',
         '-s', 'physics',
         '-f', '2015-01-17',
         '-t', '2015-01-17',
         '-e', 'utf-8'],
        obj=script_info
    )
    assert result.exit_code == 0

    # Queue it
    result = runner.invoke(
        harvest,
        ['-u', 'http://export.arxiv.org/oai2',
         '-m', 'arXiv',
         '-s', 'physics',
         '-f', '2015-01-17',
         '-t', '2015-01-17',
         '--enqueue'],
        obj=script_info
    )
    assert result.exit_code == 0
